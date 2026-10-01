# -*- coding: utf-8 -*-
"""
profe/simular_notebook.py — Ejecuta el cuaderno del alumno sin abrir Colab.

    python profe/simular_notebook.py --experto
    python profe/simular_notebook.py --experto --ofuscado

Recorre las celdas de código del cuaderno en un mismo espacio de nombres (como
si el alumno las ejecutara en orden) y después hace lo que haría un alumno
perfecto: escribe la función del método, contesta los widgets con las
respuestas correctas y llama a `enviar(debug=True)`. Comprueba:

  1. que TODAS las celdas de código compilan y corren sin excepciones;
  2. que un alumno perfecto saca 100 / 100;
  3. que el cuerpo del POST lleva `respuestas`, `pesos` y `maxPuntos`.

Con `--ofuscado` se fuerza el cuaderno a cargar `grader_ofuscado.txt` en lugar
del bundle legible, para verificar que el blob está al día.
"""
import argparse
import contextlib
import io
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

CUADERNO = os.path.join(RAIZ, 'U2_T3A.ipynb')
# Magia de IPython (`%matplotlib inline`, `!pip install ...`). Solo se quita si
# tras el signo viene un nombre: si no, se llevaría por delante las líneas de
# continuación de un `print(...)`, que empiezan con el operador `%`.
MAGIC = re.compile(r'^\s*[%!][A-Za-z]')
NC_EJEMPLO = 'm16330887@hermosillo.tecnm.mx'


class MarcoFalso(object):
    """Lo que `inspect.currentframe().f_back` da dentro de un cuaderno real."""

    def __init__(self, globs):
        self.f_globals = globs


def horner_experto(a, x0):
    """La función que escribiría un alumno que domina el algoritmo."""
    n = len(a) - 1
    b = [0.0] * (n + 1)
    b[0] = a[0]
    for k in range(1, n + 1):
        b[k] = a[k] + b[k - 1] * x0
    c = [None] * (n + 1)
    c[0] = b[0]
    for k in range(1, n):
        c[k] = b[k] + c[k - 1] * x0
    return b[n], (c[n - 1] if n >= 1 else 0.0), b[:-1]


def celdas_de_codigo(ruta):
    with io.open(ruta, encoding='utf-8') as f:
        nb = json.load(f)
    salida = []
    for celda in nb.get('cells', []):
        if celda.get('cell_type') != 'code':
            continue
        fuente = celda.get('source', '')
        if isinstance(fuente, list):
            fuente = ''.join(fuente)
        lineas = [l for l in fuente.splitlines() if not MAGIC.match(l)]
        salida.append('\n'.join(lineas))
    return salida


def ejecutar(ofuscado=False, verboso=False):
    if not os.path.exists(CUADERNO):
        raise SystemExit('No encuentro %s' % CUADERNO)
    celdas = celdas_de_codigo(CUADERNO)
    print('Cuaderno : %s  (%d celdas de código)'
          % (os.path.basename(CUADERNO), len(celdas)))
    print('Motor    : %s' % ('OFUSCADO (grader_ofuscado.txt)' if ofuscado
                             else 'bundle legible (grader_local.py)'))

    ns = {'__name__': '__main__', 'alumno_id': NC_EJEMPLO}
    fallos, salidas = [], {}
    for i, codigo in enumerate(celdas, start=1):
        if ofuscado and 'DEBUG_SIN_OFUSCAR = True' in codigo:
            codigo = codigo.replace('DEBUG_SIN_OFUSCAR = True',
                                    'DEBUG_SIN_OFUSCAR = False')
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(codigo, '<celda %d>' % i, 'exec'), ns)
            salidas[i] = buf.getvalue()
        except BaseException as exc:                       # noqa: BLE001
            fallos.append((i, exc, buf.getvalue().strip().splitlines()[-3:]))
        if verboso:
            print('   celda %2d %s' % (i, 'FALLA' if any(f[0] == i for f in fallos)
                                       else 'OK'))

    for i in sorted(salidas):
        for linea in salidas[i].splitlines():
            if linea.startswith(('Modo', 'Motor', 'Carpeta', '✅', '⛔', 'Listo')):
                print('   [celda %d] %s' % (i, linea))

    if fallos:
        print('\n❌ Celdas que fallaron:')
        for i, exc, cola in fallos:
            print('   celda %d: %r' % (i, exc))
            for linea in cola:
                print('       %s' % linea)
        return 1
    print('   todas las celdas corrieron sin excepciones')

    # ---- Un alumno perfecto contesta todo -----------------------------
    ex = ns.get('MI_TAREA')
    if ex is None:
        print('❌ El cuaderno no creó MI_TAREA.')
        return 1

    ns['horner'] = horner_experto
    sin_widget = []
    for i, p in enumerate(ex.preguntas, start=1):
        if p['tipo'] == 'funcion':
            continue
        w = ns.get('resp_%d' % i)
        sol = ex.soluciones[i - 1]
        if w is None:
            sin_widget.append(i)
            continue
        if p['tipo'] == 'vector':
            for caja, valor in zip(w.casillas, sol):
                caja.value = float(valor)
        else:
            w.value = float(sol)

    marco = MarcoFalso(ns)
    res = ns['enviar'](marco=marco, debug=True)
    cuerpo = res.get('cuerpo', {})
    calif = res.get('calificacion', 0.0)
    print('\nAlumno perfecto: %.1f / 100  (máximo %g, mínimo para enviar %g %%)'
          % (calif, res.get('maximo', 0), res.get('minimo', 0)))
    print('   respuestas = %s' % (cuerpo.get('respuestas'),))
    print('   pesos      = %s' % (cuerpo.get('pesos'),))

    problemas = []
    if sin_widget:
        problemas.append('sin widget las preguntas %s' % sin_widget)
    if abs(calif - 100.0) > 1e-9:
        problemas.append('un alumno perfecto no saca 100 (saca %.1f)' % calif)
    if not cuerpo.get('respuestas'):
        problemas.append('el POST no lleva `respuestas` (la hoja no guardaría nada)')
    if res.get('maximo') != ex.maximo:
        problemas.append('maximo del envío (%s) != maximo de la tarea (%s)'
                         % (res.get('maximo'), ex.maximo))

    print()
    if problemas:
        for p in problemas:
            print('❌ %s' % p)
        return 1
    print('=' * 74)
    print(' RESULTADO: TODO OK')
    print('=' * 74)
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Ejecuta el cuaderno como si fuera el alumno.')
    ap.add_argument('--experto', action='store_true',
                    help='contesta todo bien y comprueba el 100 / 100')
    ap.add_argument('--ofuscado', action='store_true',
                    help='usa grader_ofuscado.txt (el blob de Colab)')
    ap.add_argument('--verboso', action='store_true', help='lista cada celda')
    args = ap.parse_args()
    sys.exit(ejecutar(ofuscado=args.ofuscado, verboso=args.verboso))

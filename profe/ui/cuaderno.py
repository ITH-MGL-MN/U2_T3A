# -*- coding: utf-8 -*-
"""
profe/ui/cuaderno.py — API que usa el cuaderno del alumno.

El cuaderno NO habla con los módulos internos: llama a estas funciones, que
son las mismas del motor anterior, así que las celdas y las explicaciones no
cambian cuando se reordena el código por dentro.

    generar_tarea(alumno_id)      crea MI_TAREA y muestra el encabezado
    pregunta(n)                   muestra la pregunta n y su widget resp_n
    mano_enunciado(metodo)        enunciado + tabla en blanco de la actividad
    mano_ecuacion(metodo, ...)    revisa las lambdas que escribió el alumno
    mano_comprueba(metodo, lista) realimentación de la tabla a mano
    mano_solucion(metodo)         valores de referencia de la actividad
    hoja_manual()                 resumen para calificar las 2 rúbricas
    calificar / enviar

Los mensajes al alumno se imprimen aquí (es la capa de presentación); el
motor de `profe.core` solo devuelve datos.
"""
import builtins
import inspect
import json

import numpy as np

from profe.config import buscar, obtener_configuracion
from profe.core import (
    MANO_REPORTE,
    METODOS_MANO,
    NOMBRE_FUNCION,
    NOMBRE_METODO,
    NOMBRE_REDUCIDO,
    elegir_mano,
)
from profe.core.evaluator import Tarea
from profe.core.helpers import _fmt
from profe.core.seed import extraer_nc, generar_semilla, obtener_rng
from profe.core.solvers import ES_DEFECTO, MAX_ITER, iteraciones, resolver

# ---------------------------------------------------------------------
#  Estado del cuaderno
# ---------------------------------------------------------------------
_EXAMEN = None             # la tarea que se está resolviendo
_MANO = {}                 # metodo -> valores que reportó el alumno
_MANO_EJ = {}              # metodo -> ejercicio de la actividad a mano
_MANO_RES = {}             # metodo -> True si acertó TODOS los valores
_MANO_EC = {}              # metodo -> True si SUS lambdas coinciden

# Columnas de la tabla del método, en el orden en que se imprimen. Cada fila
# es un coeficiente: `grado` es la potencia que lo acompaña y `a_k` el
# coeficiente del polinomio original.
ORDEN_COLUMNAS = {
    'HORNER': ['grado', 'a_k', 'b_k', 'c_k'],
    'DEFLACION': ['grado', 'a_k', 'b_k'],
}

# Columnas que el enunciado YA da (las demás las llena el alumno).
COLUMNAS_DADAS = {
    'HORNER': ('grado', 'a_k'),
    'DEFLACION': ('grado', 'a_k'),
}

ENCABEZADOS = {
    'grado': 'grado',
    'a_k': 'a_k',
    'b_k': 'b_k',
    'c_k': 'c_k',
}

# Qué es cada columna (se imprime junto a la tabla en blanco).
COLUMNAS_EXPL = {
    'HORNER': ('`grado` = la potencia que acompaña al coeficiente (de mayor a menor)  ·  '
               '`a_k` = los coeficientes del polinomio, que ya te da el enunciado  ·  '
               '`b_k` = la **primera corrida**: cada $b$ se calcula con el $b$ anterior  ·  '
               '`c_k` = la **segunda corrida**, que va sobre los $b$ (no sobre los $a$).'),
    'DEFLACION': ('`grado` = la potencia del coeficiente  ·  `a_k` = los coeficientes del '
                  'polinomio original  ·  `b_k` = el cociente de dividir entre $(x-r)$; '
                  'el **último** valor que obtengas es el residuo.'),
}

# Parámetros de arranque por método y su nombre en LaTeX.
_PARAMS_TEXTO = {
    'HORNER': (('x0', 'x_0'),),
    'DEFLACION': (('x0', 'r'),),
}


def _display(*objetos):
    """`display` de IPython, importado solo cuando se usa."""
    from IPython.display import display
    return display(*objetos)


def _markdown(texto):
    from IPython.display import Markdown
    return Markdown(texto)


def _obtener_examen(nc=None, marco=None):
    """
    La tarea del alumno. Si todavía no existe, la crea usando el `alumno_id`
    que esté en el cuaderno; si no hay ninguno, avisa.
    """
    global _EXAMEN
    if _EXAMEN is None:
        if marco is None:
            marco = inspect.currentframe().f_back
        glob = getattr(marco, 'f_globals', {}) or {}
        alumno = nc
        for clave in ('alumno_id', 'ALUMNO_ID', 'MI_CORREO', 'correo'):
            if alumno:
                break
            alumno = glob.get(clave)
        if alumno is None:
            raise RuntimeError('Primero ejecuta generar_tarea(alumno_id).')
        _EXAMEN = Tarea(alumno)
    return _EXAMEN


# =====================================================================
#  TABLAS DE LA DIVISIÓN SINTÉTICA
# =====================================================================
def _filas_tabla(metodo, ej, filas_n=None):
    filas = ej.get('_filas')
    if not filas:
        filas = iteraciones(metodo, ej)[1]
    return filas if filas_n is None else filas[:filas_n]


def _texto_tabla(filas, orden):
    """Impresión en texto plano (sin pandas)."""
    if not filas:
        return '(tabla vacía)'
    cols = [c for c in orden if c in filas[0]]
    enc = [ENCABEZADOS.get(c, c)[:13] for c in cols]
    lineas = ['  '.join('%-13s' % c for c in enc), '-' * (15 * len(cols))]
    for fila in filas:
        celdas = []
        for c in cols:
            v = fila.get(c)
            if isinstance(v, float):
                celdas.append('%-13.8g' % v)
            elif isinstance(v, (int, np.integer)):
                celdas.append('%-13s' % v)
            else:
                celdas.append('%-13s' % ('' if v is None else v))
        lineas.append('  '.join(celdas))
    return '\n'.join(lineas)


def tabla_en_blanco(metodo, ej, n=None):
    """
    Tabla con los resultados OCULTOS, para que el alumno la llene a mano:
    se dejan a la vista las columnas que el enunciado ya da (el grado y los
    coeficientes del polinomio) y se borra todo lo demás.
    """
    dadas = COLUMNAS_DADAS[metodo]
    filas = _filas_tabla(metodo, ej)
    if n is not None:
        filas = filas[:n]
    salida = []
    for fila in filas:
        salida.append({c: (fila.get(c) if c in dadas else '')
                       for c in ORDEN_COLUMNAS[metodo]})
    return salida


def tabla_df(metodo, ej, filas_n=None):
    """
    Tabla de referencia como DataFrame de pandas.
    Si pandas no está disponible, devuelve una lista de diccionarios.
    """
    datos = _filas_tabla(metodo, ej, filas_n)
    orden = ORDEN_COLUMNAS[metodo]
    try:
        import pandas as pd
    except ImportError:
        return [{k: fila.get(k) for k in orden} for fila in datos]
    df = pd.DataFrame(datos)
    df = df[[c for c in orden if c in df.columns]]
    return df


def tabla(metodo, ej, filas_n=None):
    """Muestra la tabla de referencia (la solución de la división sintética)."""
    datos = _filas_tabla(metodo, ej, filas_n)
    df = tabla_df(metodo, ej, filas_n)
    if df is not None and not isinstance(df, list):
        _display(_markdown('**Tabla de la división sintética (referencia)**'))
        _display(df)
    else:
        print('Tabla de la división sintética (referencia)')
        print(_texto_tabla(datos, ORDEN_COLUMNAS[metodo]))
    return df


# =====================================================================
#  TAREA Y PREGUNTAS
# =====================================================================
def generar_tarea(alumno_id):
    """Crea la tarea del alumno y muestra el encabezado."""
    global _EXAMEN
    _EXAMEN = Tarea(alumno_id)
    _display(_markdown('# Tarea · %s' % _EXAMEN.nombre_tarea))
    _display(_markdown('**Alumno:** `%s`  ·  **NC:** `%s`  ·  **Puntos automáticos:** %g'
                       % (_EXAMEN.alumno_id, _EXAMEN.nc, _EXAMEN.maximo)))
    _display(_markdown('Esta tarea tiene **%d** preguntas automáticas (%g puntos) y **%d** '
                       'actividades a mano que revisa tu profesor (%g%% de la calificación).'
                       % (builtins.len(_EXAMEN.preguntas), _EXAMEN.maximo,
                          builtins.len(METODOS_MANO),
                          100.0 * _EXAMEN.peso_mano)))
    return _EXAMEN


# Compatibilidad: la función se llamaba `generar_examen` antes de renombrarla.
def generar_examen(alumno_id):
    return generar_tarea(alumno_id)


def _render_pregunta(i, p, peso=None, total=None):
    _display(_markdown('#### Pregunta %d: %s' % (i, p['titulo'])))
    if peso is not None and total:
        _display(_markdown('**Valor:** $\\frac{%g}{%g}$ puntos' % (peso, total)))
    # Las preguntas de la tabla se refieren al ejercicio de la sección, que el
    # alumno ya tiene delante: se recuerda el TÍTULO nada más, sin repetir
    # entero el enunciado (es el mismo de su actividad a mano).
    if p.get('_mostrar_ejercicio') and p.get('_ej'):
        _display(_markdown('**Ejercicio:** %s' % p['_ej']['titulo']))
    _display(_markdown(p['texto']))
    if p['tipo'] == 'funcion':
        _display(_markdown(
            'Define la función con **exactamente** la firma `%s` en una celda aparte '
            'y ejecútala (no la definas dentro de esta celda).' % p.get('firma', '?')))


class _Vectores(object):
    """
    Envuelve N casillas para que se comporten como UN solo widget: `.value`
    devuelve la lista de lo que escribió el alumno. Así el resto del motor
    (que lee `resp_i.value`) no necesita saber que son varias casillas.
    """

    def __init__(self, casillas, etiquetas):
        self.casillas = list(casillas)
        self.etiquetas = list(etiquetas)

    @property
    def value(self):
        return [c.value for c in self.casillas]


def _crear_widget_respuesta(i, p, marco):
    """
    Crea y muestra el widget de la pregunta y lo guarda como `resp_i` en el
    cuaderno. En las de tipo `opcion` el valor es el ÍNDICE de la opción.
    """
    import ipywidgets as widgets
    from ipywidgets import Layout

    t = p['tipo']
    if t == 'opcion':
        for op in p['opciones']:
            _display(_markdown(op))
        letras = [chr(97 + j) + ')' for j in range(len(p['opciones']))]
        w = widgets.RadioButtons(
            options=[(letra, j) for j, letra in enumerate(letras)],
            value=None, disabled=False, layout=Layout(width='170px'))
        _display(w)
        marco.f_globals['resp_%d' % i] = w
        return w
    if t == 'simple':
        w = widgets.FloatText(value=0.0, description='Respuesta:',
                              layout=Layout(width='260px'))
        _display(w)
        marco.f_globals['resp_%d' % i] = w
        return w
    if t == 'vector':
        _display(_markdown('Escribe **un número en cada casilla**, en el orden '
                           'del enunciado:'))
        casillas = []
        etiquetas = p.get('etiquetas') or []
        for j, etiqueta in enumerate(etiquetas):
            caja = widgets.FloatText(value=0.0, description='%s =' % etiqueta,
                                     layout=Layout(width='230px'))
            _display(caja)
            casillas.append(caja)
        w = _Vectores(casillas, etiquetas)
        marco.f_globals['resp_%d' % i] = w
        return w
    # tipo 'funcion': no hay widget, la función se lee del cuaderno
    marco.f_globals['resp_%d' % i] = None
    return None


def pregunta(numero):
    """Muestra la pregunta `numero` y su widget."""
    marco = inspect.currentframe().f_back
    ex = _obtener_examen(marco=marco)
    i = int(numero)
    if not 1 <= i <= builtins.len(ex.preguntas):
        raise ValueError('Esta tarea tiene %d preguntas.' % builtins.len(ex.preguntas))
    p = ex.preguntas[i - 1]
    _render_pregunta(i, p, peso=ex.pesos[i - 1], total=ex.maximo)
    _crear_widget_respuesta(i, p, marco)
    # Devuelve None a propósito: si regresara el diccionario, Jupyter lo
    # imprimiría debajo del widget. Para inspeccionarlo usa
    # MI_TAREA.preguntas[i-1] o MI_TAREA.soluciones[i-1].
    return None


def _leer_valor(marco, i):
    for clave in ('resp_%d' % i, 'r%d' % i):
        w = marco.f_globals.get(clave)
        if w is None:
            continue
        try:
            return w.value
        except AttributeError:
            return w
    return None


def _respuestas_del_cuaderno(marco):
    ex = _EXAMEN
    res = {}
    for i in range(1, builtins.len(ex.preguntas) + 1):
        if ex.preguntas[i - 1]['tipo'] == 'funcion':
            continue
        res[i] = _leer_valor(marco, i)
    return res


# Casos de prueba con solución conocida: sirven para comprobar la función del
# alumno cuando la quiere probar con un polinomio que no es el suyo.
CASOS_PRUEBA = {
    'HORNER': ('horner([1, -4, 5, -3, 2], 3.0)',
               '(11.0, 27.0, [1.0, -1.0, 2.0, 3.0])'),
}

TOL_PRACTICA = 1e-6      # relativa, para decir si su función está bien
TOL_MANO = 1e-3          # relativa, para la realimentación de la tabla a mano


def _lista_txt(valores):
    """[1.0, -4.0, 7.0, 1.0] -> '[1, -4, 7, 1]'."""
    return '[%s]' % ', '.join(_fmt(v, 6) for v in valores)


def _num_o_none(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def comparar_practica(metodo, ej, resultado):
    """
    Compara lo que devolvió la función del alumno con la referencia del
    ejercicio y le dice con claridad QUÉ parte está mal: el valor, la
    derivada o el polinomio reducido.

    En Horner, `resultado` = (p_val, dp_val, Q).
    """
    nombre = NOMBRE_FUNCION.get(metodo, metodo)
    try:
        if (not isinstance(resultado, (tuple, list, np.ndarray))
                or builtins.len(resultado) != 3):
            raise TypeError
        p_val, dp_val, Q = resultado
        Q = list(Q)
    except (TypeError, ValueError):
        print('\u26a0\ufe0f Tu %s debe devolver TRES cosas: '
              '(p_val, dp_val, Q). Devolvió: %r' % (nombre, resultado))
        return

    print('tu %-8s: P(x_0) = %s   P\'(x_0) = %s   Q = %s'
          % (nombre, _fmt(p_val, 8), _fmt(dp_val, 8), _lista_txt(Q)))
    print('referencia: P(x_0) = %s   P\'(x_0) = %s   Q = %s'
          % (_fmt(ej['p_val'], 8), _fmt(ej['dp_val'], 8), _lista_txt(ej['Q'])))
    if not ej.get('_conv'):
        print('⚠️ Este ejercicio no tiene tabla de referencia.')

    ok_p = builtins.abs(_num_o_none(p_val) - ej['p_val']) <= \
        TOL_PRACTICA * builtins.max(1.0, builtins.abs(ej['p_val'])) \
        if _num_o_none(p_val) is not None else False
    ok_d = builtins.abs(_num_o_none(dp_val) - ej['dp_val']) <= \
        TOL_PRACTICA * builtins.max(1.0, builtins.abs(ej['dp_val'])) \
        if _num_o_none(dp_val) is not None else False
    ok_q = (builtins.len(Q) == builtins.len(ej['Q'])
            and builtins.all(builtins.abs(a - b) <=
                             TOL_PRACTICA * builtins.max(1.0, builtins.abs(b))
                             for a, b in zip(Q, ej['Q'])))

    if ok_p and ok_d and ok_q:
        print('\u2705 Las tres cosas coinciden con la referencia.')
        return

    if not ok_p:
        print('\u274c P(x_0) no coincide: revisa que la primera corrida empiece con '
              'b = a_n y que cada paso use el b anterior.')
    if ok_p and not ok_d:
        print('\u274c P\'(x_0) no coincide: la segunda corrida va sobre los '
              '**b_k** (los que acabas de obtener), no sobre los a_k. El resultado '
              'es el PENÚLTIMO valor de esa segunda fila.')
    if not ok_q:
        if builtins.len(Q) == builtins.len(ej['Q']):
            print('\u274c Q no coincide: son los b_k SIN el último (ese último es '
                  'P(x_0)). Cuidado si el polinomio no es mónico: Q conserva el '
                  'coeficiente líder.')
        else:
            print('\u274c Q tiene %d coeficientes y debe tener %d (grado %d): '
                  'esa lista NO incluye el residuo.'
                  % (builtins.len(Q), builtins.len(ej['Q']), builtins.len(ej['Q']) - 1))
    cmd, valor = CASOS_PRUEBA.get(metodo, ('', ''))
    if cmd:
        print('   Compruébala con un caso que ya conoces:')
        print('       %s   ->   %s' % (cmd, valor))


def _mostrar_resultados(filas):
    """Tabla de resultados de la calificación (la usa `calificar`)."""
    iconos = {'correcta': '\u2705', 'parcial': '\U0001f7e1',
              'incorrecta': '\u274c', 'sin respuesta': '\u26a0\ufe0f'}
    print('%-4s %-12s %-11s %s' % ('#', 'estado', 'puntos', 'respuesta'))
    print('-' * 62)
    for fila in filas:
        val = fila['val']
        if isinstance(val, (tuple, list)) and val and isinstance(val[0], tuple):
            val = 'programa (%d casos)' % builtins.len(val)
        elif isinstance(val, list):
            val = _lista_txt(val)
        print('%-4d %-12s %-11s %s' % (fila['i'], iconos[fila['estado']],
                                       '%g/%g' % (fila['puntos'], fila['peso']), val))
    print('-' * 62)


def calificar(marco=None):
    """Califica las preguntas automáticas y muestra el detalle."""
    ex = _EXAMEN
    if ex is None:
        raise RuntimeError('Primero ejecuta generar_tarea(alumno_id).')
    if marco is None:
        marco = inspect.currentframe().f_back

    respuestas = _respuestas_del_cuaderno(marco)
    filas = ex.calificar(respuestas, marco)

    puntos = 0.0
    maximo = 0.0
    for fila in filas:
        puntos += fila['puntos']
        maximo += fila['peso']
    _mostrar_resultados(filas)
    print('AUTOMÁTICO: %.1f / %g  =  %.1f %%' % (puntos, maximo, 100.0 * puntos / maximo))
    return puntos, maximo


def enviar(correo=None, marco=None, debug=False):
    """Envía el resultado automático al Apps Script (exige ≥ MIN_APROBACION)."""
    ex = _EXAMEN
    if ex is None:
        raise RuntimeError('Primero ejecuta generar_tarea(alumno_id).')
    if marco is None:
        marco = inspect.currentframe().f_back

    puntos, maximo = calificar(marco)
    correo = correo or marco.f_globals.get('alumno_id', '') or ex.alumno_id
    res = ex.enviar(_respuestas_del_cuaderno(marco), marco, debug=debug, correo=correo)

    if debug:
        print('POST', ex.url)
        print(json.dumps(res['cuerpo'], indent=2, ensure_ascii=False))
        return res

    if res.get('motivo') == 'minimo':
        print('⛔ Aún no puedes enviar: necesitas al menos %g %% (%g puntos de %g). '
              'Corrige y vuelve a intentarlo.'
              % (res['minimo'], ex.min_aprobacion * res['maximo'], res['maximo']))
        return res

    if res['enviado']:
        detalle = ''
        aviso = res.get('aviso')
        if isinstance(aviso, dict) and isinstance(aviso.get('data'), dict):
            d = aviso['data']
            detalle = ' Intento %s, total %.1f %%.' % (d.get('intento', '?'),
                                                       d.get('total', 0.0))
        print('\u2705 Enviado.%s Respuesta del servidor: %s'
              % (detalle, res['respuesta'][:300]))
    else:
        print('\u26a0\ufe0f No se pudo enviar a la hoja de cálculo: %s'
              % res.get('error'))
    return res


# =====================================================================
#  ACTIVIDADES A MANO (con realimentación automática)
# =====================================================================
def _num_txt(valor):
    """Número corto para el enunciado: 69.0 -> 69, 1e-05 -> 1e-05."""
    try:
        return '%g' % float(valor)
    except (TypeError, ValueError):
        return str(valor)


def _datos_texto(metodo, ej):
    """
    Línea con los datos del ejercicio y los parámetros de arranque.

    Además del punto del método, se imprime la lista de coeficientes tal como
    la espera la función del alumno: así no hay que copiarla a mano del
    enunciado (y no se cuelan errores de signo).
    """
    piezas = []
    for nombre, valor, unidad in (ej.get('datos') or []):
        sufijo = '' if not unidad or unidad == '-' else ' %s' % unidad
        piezas.append('%s = %s%s' % (nombre, _num_txt(valor), sufijo))

    for clave, etiqueta in _PARAMS_TEXTO.get(metodo, ()):
        valor = ej.get(clave)
        if valor is not None:
            piezas.append('$%s = %s$' % (etiqueta, _num_txt(valor)))

    if ej.get('a'):
        piezas.append('coeficientes `a = %s`' % _lista_txt(ej['a']))

    if not piezas:
        return None
    return '**Datos y arranque:** ' + '  ·  '.join(piezas)


def _reporte_txt(metodo):
    """'[P(x_0), P\'(x_0)]' — lo que el alumno tiene que reportar."""
    return '[%s]' % ', '.join(etq for etq, _fn in MANO_REPORTE[metodo])


def _marco_mano(metodo, ej):
    """
    Enunciado de la actividad a mano (sin revelar los resultados).

    El texto va con display(Markdown(...)) para que el LaTeX del enunciado se
    renderice; la tabla va con print() porque es texto monoespaciado y así las
    columnas quedan alineadas.
    """
    _display(_markdown('### ✏️ Actividad a mano: %s' % NOMBRE_METODO[metodo]))
    _display(_markdown('**%s**' % ej['titulo']))
    _display(_markdown(ej['contexto'].strip()))
    linea_datos = _datos_texto(metodo, ej)
    if linea_datos:
        _display(_markdown(linea_datos))
    _display(_markdown('**Tu tabla para llenar a mano** (no redondees los pasos '
                       'intermedios):'))
    print(_texto_tabla(tabla_en_blanco(metodo, ej), ORDEN_COLUMNAS[metodo]))
    _display(_markdown(COLUMNAS_EXPL[metodo]))
    _display(_markdown('Reporta en la celda siguiente la lista `%s`, con al menos '
                       '4 decimales. **Se comprueban todos los valores** para que '
                       'verifiques tu tabla.' % _reporte_txt(metodo)))
    return ej


def mano_enunciado(metodo, nc=None):
    """
    Imprime el enunciado de la actividad a mano del método y guarda el
    ejercicio en `_MANO_EJ[metodo]` para la realimentación.

    El ejercicio se sortea con el número de control del alumno, así que no
    coincide con el de sus compañeros.
    """
    marco = inspect.currentframe().f_back
    ex = _obtener_examen(nc=nc, marco=marco)
    rng = obtener_rng(nc or ex.nc, ex.id_tarea, 'mano', metodo)
    ej = elegir_mano(metodo, rng)
    _MANO_EJ[metodo] = ej
    _marco_mano(metodo, ej)
    return ej


def _referencia_mano(metodo):
    """[(etiqueta, valor de referencia)] de la actividad a mano."""
    ej = _MANO_EJ[metodo]
    return [(etq, float(fn(ej))) for etq, fn in MANO_REPORTE[metodo]]


def mano_comprueba(metodo, valores):
    """
    Realimentación de la actividad a mano: compara TODOS los valores que
    reporta el alumno contra la referencia.
    """
    ej = (_MANO_EJ or {}).get(metodo)
    if ej is None:
        print('Primero ejecuta mano_enunciado(%r).' % metodo)
        return None

    try:
        vals = [float(v) for v in valores]
    except (TypeError, ValueError):
        print('\u26a0\ufe0f Reporta una lista de números, por ejemplo %s.'
              % _reporte_txt(metodo))
        return None

    _MANO[metodo] = vals
    ref = _referencia_mano(metodo)
    print('Tus valores reportados: %s'
          % ', '.join('%s = %.8g' % (etq, v) for (etq, _r), v in zip(ref, vals)))

    todo, faltan = True, builtins.len(ref) - builtins.len(vals)
    print('')
    print('   %-10s %-16s %-16s %s' % ('valor', 'tu resultado', 'referencia', 'estado'))
    print('   ' + '-' * 58)
    for (etq, r), v in zip(ref, vals):
        err = builtins.abs(v - r) / builtins.max(builtins.abs(r), 1e-12)
        bien = err <= TOL_MANO
        todo = todo and bien
        print('   %-10s %-16.8g %-16.8g %s (error %.1e)'
              % (etq, v, r, '\u2705' if bien else '\u274c', err))

    _MANO_RES[metodo] = bool(todo and builtins.len(vals) == builtins.len(ref))
    print('')
    if _MANO_RES[metodo]:
        print('\u2705 Todos los valores son correctos.')
    else:
        if builtins.len(vals) < builtins.len(ref):
            print('\u26a0\ufe0f Reportaste %d valores y hacen falta %d: %s.'
                  % (builtins.len(vals), builtins.len(ref), _reporte_txt(metodo)))
        print('   Sugerencias: arrastra TODOS los decimales del paso anterior y no')
        print('   redondees a la mitad del cálculo.')
        if metodo == 'HORNER':
            print('   En la derivada, recuerda que la segunda corrida va sobre los')
            print('   b_k, y que P\'(x_0) es el PENÚLTIMO valor de esa segunda fila.')
        else:
            print('   En la deflación, el cociente conserva el coeficiente líder del')
            print('   polinomio original (y el último valor que obtienes es el residuo).')
    # None a propósito: evita que Jupyter imprima el diccionario del ejercicio.
    return None


def mano_solucion(metodo):
    """
    Da SOLO los valores de referencia de la actividad (el valor y la derivada,
    o los coeficientes del polinomio reducido). La tabla completa queda para la
    revisión del profesor en hoja_manual().
    """
    ej = (_MANO_EJ or {}).get(metodo)
    if ej is None:
        print('Primero ejecuta mano_enunciado(%r).' % metodo)
        return None
    print('Valores de referencia:')
    for etq, r in _referencia_mano(metodo):
        print('   %-10s = %.8f' % (etq, r))
    print('(La tabla completa la revisa tu profesor en la HOJA DE TRABAJO MANUAL.)')
    # None a propósito: evita que Jupyter imprima el diccionario del ejercicio.
    return None


# Nombre alterno, más descriptivo que "solución".
def mano_referencia(metodo):
    return mano_solucion(metodo)


def mano_ecuacion(metodo, f=None, df=None):
    """
    Revisa la ECUACIÓN que escribió el alumno (como funciones lambda) contra
    la del enunciado, evaluándola en puntos OCULTOS.

    Cada método pide lo que usa:
        HORNER    ->  P y P'
        DEFLACION ->  P
    El resultado queda en `_MANO_EC[metodo]` y se imprime en hoja_manual().
    """
    ej = (_MANO_EJ or {}).get(metodo)
    if ej is None:
        print('Primero ejecuta mano_enunciado(%r).' % metodo)
        return None

    necesarias = {
        'HORNER': (('P', f), ("P'", df)),
        'DEFLACION': (('P', f),),
    }[metodo]
    referencia = {'P': ej.get('f'), "P'": ej.get('df')}

    # --- puntos ocultos: el punto del método y dos más, sin repetir ---------
    x0 = float(ej.get('x0'))
    xs = []
    for cand in (x0, x0 + 1.0, x0 - 1.7, 0.0, x0 + 0.35):
        cand = float(cand)
        if not np.isfinite(cand):
            continue
        if builtins.all(builtins.abs(cand - v) > 1e-6 * builtins.max(1.0, builtins.abs(v))
                        for v in xs):
            xs.append(cand)
        if builtins.len(xs) == 3:
            break

    print('Revisión de TU ecuación (en %d valores que no ves):' % builtins.len(xs))
    todo_ok, faltan, malas = True, [], []
    for nombre, fn_alumno in necesarias:
        fn_ref = referencia.get(nombre)
        if fn_alumno is None:
            faltan.append(nombre)
            todo_ok = False
            print('   %-4s : todavía no la escribiste' % nombre)
            continue
        if fn_ref is None:
            print('   %-4s : (este enunciado no la pide)' % nombre)
            continue
        peor, falla = 0.0, None
        for x in xs:
            try:
                a, b = float(fn_alumno(x)), float(fn_ref(x))
            except Exception as exc:                       # noqa: BLE001
                falla = 'tu lambda falló en x=%.6g (%r)' % (x, exc)
                break
            if not (np.isfinite(a) and np.isfinite(b)):
                continue
            peor = builtins.max(peor, builtins.abs(a - b) /
                                builtins.max(1.0, builtins.abs(b)))
        if falla:
            todo_ok = False
            malas.append(nombre)
            print('   %-4s : NO  -> %s' % (nombre, falla))
        elif peor <= 1e-9:
            print('   %-4s : OK  (diferencia relativa máxima %.2e)' % (nombre, peor))
        else:
            todo_ok = False
            malas.append(nombre)
            print('   %-4s : NO coincide (diferencia relativa máxima %.2e)' % (nombre, peor))

    _MANO_EC[metodo] = bool(todo_ok)
    if todo_ok:
        print('✅ Tu ecuación coincide con la del enunciado.')
    elif faltan:
        print('⚠️ Falta escribir: %s' % ', '.join(faltan))
    else:
        print('❌ Revisa %s: compárala con la fórmula del enunciado (paréntesis, '
              'signos, potencias).' % ', '.join(malas))
    return None


def hoja_manual(metodo=None):
    """
    Resumen para calificar a mano (lo que ve el profesor).
    Con `metodo` muestra solo esa actividad; sin argumentos, todas.
    """
    ex = _EXAMEN
    nombre = ex.id_tarea if ex is not None else 'U2_T3A'
    metodos = (metodo,) if metodo else METODOS_MANO

    print('=' * 72)
    print('HOJA DE TRABAJO MANUAL · %s' % nombre)
    print('=' * 72)
    for met in metodos:
        ej = (_MANO_EJ or {}).get(met)
        if ej is None:
            continue
        alumno = _MANO.get(met, [])
        print('\n%s · %s' % (NOMBRE_METODO[met], ej['titulo']))
        print('  polinomio  : %s' % _lista_txt(ej['a']))
        print('  %-11s: %s' % ('punto', _num_txt(ej['x0'])))
        print('  %-11s: %s' % ('referencia',
                                ', '.join('%s = %.6g' % (etq, r)
                                          for etq, r in _referencia_mano(met))))
        print('  %-11s: %s' % ('alumno',
                                (', '.join('%.6g' % v for v in alumno)
                                 if alumno else '(sin reportar)')))
        _ec = _MANO_EC.get(met)
        print('  ecuación   : %s' % ('OK' if _ec else ('NO' if _ec is False
                                                      else '(sin escribir)')))
        print('  tabla      : %s' % ('acertada' if _MANO_RES.get(met)
                                     else ('revisar' if met in _MANO_RES
                                           else '(sin comprobar)')))
    if ex is not None:
        print('\nCalifica cada rúbrica de 0 a 10 en la hoja %s_Manual.' % nombre)
        print('Nota final = %.2f*automático + %.2f*manual'
              % (ex.peso_auto, ex.peso_mano))


# =====================================================================
#  Utilidades sueltas que el cuaderno (o el profesor) puede usar
# =====================================================================
def raices_de(a):
    """
    Todas las raíces del polinomio (reales y complejas) con `numpy.roots`.

    Sirve para el laboratorio de deflación progresiva: después de extraer una
    raíz con deflación, las raíces que faltan salen del polinomio reducido.
    """
    return np.roots([float(c) for c in a])


def semilla_de(alumno_id):
    """Semilla entera del alumno (útil para reproducir su tarea)."""
    cfg, _ = obtener_configuracion()
    id_tarea = buscar(cfg, 'tarea.id', 'U2_T3A')
    return generar_semilla(extraer_nc(alumno_id), id_tarea)


__all__ = [
    'CASOS_PRUEBA', 'COLUMNAS_DADAS', 'COLUMNAS_EXPL', 'ENCABEZADOS',
    'ORDEN_COLUMNAS', 'calificar', 'comparar_practica', 'enviar',
    'generar_examen', 'generar_tarea', 'hoja_manual', 'iteraciones',
    'mano_comprueba', 'mano_ecuacion', 'mano_enunciado', 'mano_referencia',
    'mano_solucion', 'pregunta', 'raices_de', 'resolver', 'semilla_de',
    'tabla', 'tabla_df', 'tabla_en_blanco'
]

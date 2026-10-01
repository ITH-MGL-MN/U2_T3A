# -*- coding: utf-8 -*-
"""
profe/verificar_simbolico.py — Verificación matemática de la Tarea 3A.

Comprueba, con sympy y numpy, que:

  1. `solvers.horner` devuelve el valor, la derivada y el cociente correctos
     (contra la derivada simbólica y contra la división exacta de polinomios);
  2. `solvers.deflactar` cumple P(x) = (x - r) Q(x) + residuo;
  3. el POLINOMIO QUE MUESTRA EL ENUNCIADO es el mismo con el que se calcula
     (se re-parsea el LaTeX renderizado y se compara con los coeficientes);
  4. la identidad de la derivada por doble división sintética (P'(x0) = c_1).

Uso:  python profe/verificar_simbolico.py
"""
import os
import re
import sys

import numpy as np
import sympy as sp

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from profe.core import elegir, elegir_mano, obtener_rng    # noqa: E402
from profe.core.helpers import _poly_latex           # noqa: E402
from profe.core.solvers import deflactar, horner     # noqa: E402

X = sp.Symbol('x')
CASOS = 120
POLINOMIO_EN_EL_TEXTO = re.compile(r'\$\$P\(x\) = (.+?)\$\$', re.S)


def latex_a_sympy(texto):
    """
    `x^{3} - 4x^{2} + 7x + 1` -> polinomio de sympy.

    Se convierte `^{n}` en `**n` y se meten los productos implícitos
    (`4x` -> `4*x`), que es justo lo que un humano sobreentiende y una
    computadora no.
    """
    texto = texto.strip().replace('\\,', '')
    texto = re.sub(r'\^\{(\d+)\}', r'**\1', texto)
    texto = re.sub(r'(\d)\s*([a-zA-Z])', r'\1*\2', texto)
    return sp.expand(sp.sympify(texto))


def poly_sympy(a):
    """Polinomio de sympy con los coeficientes [a_n, ..., a_0]."""
    n = len(a) - 1
    return sp.expand(sum(sp.Rational(c) * X ** (n - i) for i, c in enumerate(a)))


def main():
    avisos = []
    peor_p, peor_d, peor_q = 0.0, 0.0, 0.0

    for s in range(CASOS):
        rng = np.random.default_rng(s)
        n = int(rng.integers(1, 7))
        a = [int(rng.integers(-6, 7)) for _ in range(n + 1)]
        if a[0] == 0:
            a[0] = int(rng.integers(1, 4))
        x0 = float(rng.uniform(-3.0, 3.0))

        P = poly_sympy(a)
        dP = sp.diff(P, X)
        p_exacta = sp.N(P.subs(X, x0))
        d_exacta = sp.N(dP.subs(X, x0))

        p_val, dp_val, Q = horner([float(c) for c in a], x0)
        peor_p = max(peor_p, abs(float(p_exacta) - p_val) /
                     max(1.0, abs(float(p_exacta))))
        peor_d = max(peor_d, abs(float(d_exacta) - dp_val) /
                     max(1.0, abs(float(d_exacta))))

        # 2) identidad de la división: P(x) = (x - x0) Q(x) + b_0
        Qs = poly_sympy(Q) if len(Q) > 0 else sp.Integer(0)
        identidad = sp.expand((X - sp.Rational(x0)) * Qs +
                              sp.Rational(p_val) - P)
        resto = sp.simplify(identidad)
        if resto != 0 and abs(float(sp.N(resto.subs(X, 1.0)))) > 1e-6:
            avisos.append('división de Horner inconsistente con a=%s x0=%g' % (a, x0))

        # 3) deflación con una raíz exacta: P = (x-r)Q + residuo, residuo = 0
        r = float(rng.integers(-4, 5))
        Qr = [int(rng.integers(-5, 6)) for _ in range(3)]
        if Qr[0] == 0:
            Qr[0] = 1
        ar = [int(v) for v in np.polymul([1.0, -r], [float(v) for v in Qr])]
        Qd, residuo = deflactar([float(v) for v in ar], r)
        Poly = poly_sympy(ar)
        if abs(residuo) > 1e-9:
            avisos.append('residuo != 0 con raíz exacta: a=%s r=%g' % (ar, r))
        if sp.expand((X - sp.Rational(r)) * poly_sympy(Qd) - Poly) != 0:
            avisos.append('deflación inconsistente: a=%s r=%g' % (ar, r))

    print('Horner contra sympy: %d polígonos de grado 1 a 6' % CASOS)
    print('   peor error relativo en P(x0)  = %.2e' % peor_p)
    print('   peor error relativo en P\'(x0) = %.2e' % peor_d)
    if peor_p > 1e-9 or peor_d > 1e-9:
        avisos.append('error numérico demasiado grande en Horner')

    # 4) el polinomio del ENUNCIADO tiene que ser el mismo que se calcula ---
    revisados = 0
    for metodo in ('HORNER', 'DEFLACION'):
        for nc in ('16330887', '21150001', '19999999', '18000001', '20060042'):
            for etiqueta, mano in (('automático', False), ('a mano', True)):
                rng = obtener_rng(nc, 'U2_T3A', 'mano', metodo) if mano \
                    else obtener_rng(nc, 'U2_T3A', metodo)
                ej = elegir_mano(metodo, rng) if mano else elegir(metodo, rng)
                revisados += 1
                m = POLINOMIO_EN_EL_TEXTO.search(ej['contexto'])
                if not m:
                    avisos.append('%s/%s: el enunciado no muestra $$P(x) = ...$$'
                                  % (metodo, nc))
                    continue
                try:
                    del_texto = latex_a_sympy(m.group(1))
                except Exception as exc:                    # noqa: BLE001
                    avisos.append('%s/%s: no pude leer el polinomio %r (%r)'
                                  % (metodo, nc, m.group(1), exc))
                    continue
                if sp.expand(del_texto - poly_sympy(ej['a'])) != 0:
                    avisos.append('%s/%s: el enunciado dice %s y los coeficientes '
                                  'son %s' % (metodo, nc, m.group(1), ej['a']))

    print('Polinomios del enunciado re-parseados: %d' % revisados)

    print()
    print('=' * 74)
    if avisos:
        for aviso in avisos:
            print('AVISO: %s' % aviso)
        print(' RESULTADO: %d AVISOS' % len(avisos))
        print('=' * 74)
        return 1
    print(' RESULTADO: TODO OK  (0 avisos)')
    print('=' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())

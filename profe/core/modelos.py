# -*- coding: utf-8 -*-
"""
profe/core/modelos.py — Fábricas de polinomios de la Tarea 3A.

Cada fábrica sortea sus datos con el RNG del alumno (a través de los rangos
declarados en `profe/ejercicios/<nombre>.md`) y devuelve un diccionario con

  * `a`       coeficientes del polinomio, de mayor a menor grado
              (`a = [a_n, a_{n-1}, ..., a_0]`)
  * `x0`      el punto que usa el método: dónde se evalúa (Horner) o la
              raíz conocida que se extrae (deflación)
  * `f`, `df` el polinomio y su derivada analítica, versiones "ingenuas"
              (término a término). NO se usan para calcular la respuesta:
              sirven para revisar las lambdas que escribe el alumno y para
              que el cuaderno pueda graficar o comparar.
  * el texto del enunciado ya formateado

Los coeficientes son ENTEROS y `x0` trae a lo más un decimal: la actividad es
a mano y con calculadora, así que los números tienen que ser amables. Los
resultados (tabla, valor, derivada y cociente) los agrega
`profe.core.solvers.resolver()` al seleccionar el ejercicio.
"""
import builtins

from profe.core.helpers import _fmt, _poly_latex
from profe.core.markdown_loader import cargar_ejercicio_md, sustituir


def _poly_funcs(a):
    """(P, P') a partir de los coeficientes [a_n, ..., a_0], término a término."""
    n = builtins.len(a) - 1

    def P(x):
        total = 0.0
        for i, c in enumerate(a):
            total += c * x ** (n - i)
        return total

    def dP(x):
        total = 0.0
        for i, c in enumerate(a):
            g = n - i
            if g >= 1:
                total += c * g * x ** (g - 1)
        return total

    return P, dP


def _base(meta, ctx, a, x0, datos=None):
    """Diccionario común a todos los ejercicios de polinomios."""
    P, dP = _poly_funcs(a)
    return {
        **meta,
        'contexto': ctx,
        'a': [float(c) for c in a],
        'grado': builtins.len(a) - 1,
        'x0': float(x0),
        'x1': None, 'lam': None, 'delta': None,
        'f': P, 'df': dP, 'ddf': None, 'g': None, 'dg': None,
        'datos': datos or [],
    }


# ---------------------------------------------------------------------
#  HORNER: forma anidada + derivada
# ---------------------------------------------------------------------
def _ej_horner_calibracion(rng):
    """Polinomio de calibración de grado 4 (sensor piezoeléctrico)."""
    meta, ctx, d = cargar_ejercicio_md('horner_calibracion.md', rng)
    a = [int(d['a4']), int(d['a3']), int(d['a2']), int(d['a1']), int(d['a0'])]
    x0 = d['x_eval']
    ctx = sustituir(ctx, polinomio=_poly_latex(a), x_eval=_fmt(x0, 1))
    return _base(meta, ctx, a, x0)


def _ej_horner_motor(rng):
    """Curva de par/velocidad de un motor de CD, grado 3."""
    meta, ctx, d = cargar_ejercicio_md('horner_motor.md', rng)
    a = [int(d['a3']), int(d['a2']), int(d['a1']), int(d['a0'])]
    x0 = d['x_eval']
    ctx = sustituir(ctx, polinomio=_poly_latex(a), x_eval=_fmt(x0, 1))
    return _base(meta, ctx, a, x0)


# ---------------------------------------------------------------------
#  DEFLACIÓN: extraer una raíz exacta conocida
# ---------------------------------------------------------------------
def _ej_deflacion_leva(rng):
    """
    Cúbica mónica construida para que x = r1 sea raíz EXACTA:

        P(x) = x^3 - (r1+b) x^2 + (r1*b - c) x + c*r1
        P(r1) = 0        y el cociente es   x^2 - b x - c

    El cociente tiene coeficientes enteros y sus raíces son reales, así que la
    deflación progresiva del laboratorio llega hasta el final.
    """
    meta, ctx, d = cargar_ejercicio_md('deflacion_leva.md', rng)
    r1, b, c = int(d['r1']), int(d['b']), int(d['c'])
    a = [1, -(r1 + b), r1 * b - c, c * r1]
    ctx = sustituir(ctx, polinomio=_poly_latex(a), r1=_fmt(r1, 0))
    return _base(meta, ctx, a, float(r1))


def _ej_deflacion_engranes(rng):
    """
    Cúbica con coeficiente líder A y un factor cuadrático aleatorio:

        P(x) = A (x - r)(x^2 + p x + q)   ->   cociente  A (x^2 + p x + q)

    Es la misma operación que la leva, pero con coeficiente líder distinto de
    1 (el error clásico al deflactar a mano es olvidarlo).
    """
    meta, ctx, d = cargar_ejercicio_md('deflacion_engranes.md', rng)
    r, p, q, A = int(d['r']), int(d['p']), int(d['q']), int(d['A'])
    a = [A * v for v in (1, p - r, q - p * r, -q * r)]
    ctx = sustituir(ctx, polinomio=_poly_latex(a), r=_fmt(r, 0))
    return _base(meta, ctx, a, float(r))

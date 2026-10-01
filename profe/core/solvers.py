# -*- coding: utf-8 -*-
"""
profe/core/solvers.py — Algoritmos de referencia de la Tarea 3A.

Dos operaciones, las dos por división sintética (regla de Horner):

  HORNER     evalúa P(x0) y P'(x0) y devuelve los coeficientes del cociente
             de dividir P(x) entre (x - x0).
  DEFLACION  divide P(x) entre (x - r) para una raíz r CONOCIDA y devuelve el
             polinomio reducido.

Ninguno de los dos itera: son algoritmos directos. Aun así `iteraciones()`
devuelve la "tabla del método" (una fila por coeficiente, como en los métodos
iterativos) porque es lo que imprimen el cuaderno y los verificadores.
"""
import builtins

import numpy as np

MAX_ITER = 60
ES_DEFECTO = 0.01  # %


# =====================================================================
#  DIVISIÓN SINTÉTICA
# =====================================================================
def _division_sintetica(a, x0):
    """
    Primera corrida: b_n = a_n ; b_k = a_k + b_{k+1} x0.

    Devuelve `b` con los coeficientes en el MISMO orden que `a`, es decir
    `b[0] = b_n` ... `b[n] = b_0`. El valor del polinomio es `b[n]` y los
    coeficientes de `b[0..n-1]` son el cociente de dividir entre (x - x0).
    """
    n = builtins.len(a) - 1
    b = [0.0] * (n + 1)
    b[0] = a[0]
    for k in range(1, n + 1):
        b[k] = a[k] + b[k - 1] * x0
    return b


def _division_sintetica_2(b, x0):
    """
    Segunda corrida, sobre los `b`: c_n = b_n ; c_k = b_k + c_{k+1} x0.

    El resultados es `P'(x0) = c_1`. En el orden de la lista eso es
    `c[n-1]` (y por eso el último hueco queda en None).
    """
    n = builtins.len(b) - 1
    c = [None] * (n + 1)
    if n == 0:
        return c
    c[0] = b[0]
    for k in range(1, n):
        c[k] = b[k] + c[k - 1] * x0
    return c


def horner(a, x0):
    """
    Horner:  (P(x0), P'(x0), Q)

    `Q` son los coeficientes del cociente de `P(x)/(x - x0)`, de mayor a
    menor grado (grado n-1). Es la MISMA función que programa el alumno, así
    que aquí queda como referencia de lo que debe devolver.
    """
    b = _division_sintetica(a, x0)
    n = builtins.len(a) - 1
    c = _division_sintetica_2(b, x0)
    p_val = b[n]
    dp_val = c[n - 1] if n >= 1 else 0.0
    return p_val, dp_val, list(b[:-1])


def deflactar(a, r):
    """
    Deflación con una raíz conocida:  (Q, residuo)

    `Q` = coeficientes del cociente `P(x)/(x - r)` (grado n-1). El residuo es
    `P(r)`: si r es raíz exacta vale 0, y si no, es justo el error que se
    comete al suponerla.
    """
    b = _division_sintetica(a, r)
    n = builtins.len(a) - 1
    return list(b[:-1]), b[n]


def evaluar(a, x):
    """P(x) término a término (la forma "ingenua", para comparar)."""
    n = builtins.len(a) - 1
    total = 0.0
    for i, c in enumerate(a):
        total += c * x ** (n - i)
    return total


# =====================================================================
#  TABLA DEL MÉTODO (lo que imprimen el cuaderno y los verificadores)
# =====================================================================
def iteraciones(metodo, ej, es=None, max_iter=MAX_ITER):
    """
    Tabla de referencia del método: `(llego_al_final, filas)`.

    En Horner y en la deflación no hay iteraciones: hay una división
    sintética, y cada fila es un coeficiente. Se devuelve `True` siempre
    porque el algoritmo es directo (no puede "no converger").
    """
    filas = []
    a, x0 = ej.get('a'), ej.get('x0')
    if not a or x0 is None:
        return False, filas

    n = builtins.len(a) - 1

    if metodo == 'HORNER':
        b = _division_sintetica(a, x0)
        c = _division_sintetica_2(b, x0)
        for j in range(n + 1):
            filas.append({
                'grado': n - j,
                'a_k': a[j],
                'b_k': b[j],
                'c_k': c[j],
            })
        return True, filas

    if metodo == 'DEFLACION':
        b = _division_sintetica(a, x0)
        for j in range(n + 1):
            filas.append({
                'grado': n - j,
                'a_k': a[j],
                'b_k': b[j],
                'c_k': None,
            })
        return True, filas

    raise ValueError('Método desconocido: %s' % (metodo,))


def iteracion_objetivo(filas, es):
    """
    Compatibilidad con el motor de los métodos iterativos (allí buscaba la
    primera iteración con ea <= es). Aquí no aplica: la tabla es una división
    sintética, así que su "objetivo" es la última fila.
    """
    return builtins.len(filas) if filas else None


def resolver(metodo, ej, es=None):
    """
    Calcula la tabla de referencia del ejercicio y deja el RESULTADO dentro
    del propio diccionario:

        ej['_filas']  -> la tabla (una fila por coeficiente)
        ej['Q']       -> coeficientes del polinomio reducido
        HORNER        -> además ej['p_val'] y ej['dp_val']
        DEFLACION     -> además ej['resto']
        ej['_conv']   -> True (los dos son algoritmos directos)
        ej['_es']     -> se conserva por compatibilidad
    """
    conv, filas = iteraciones(metodo, ej, es=es)
    ej['_conv'] = conv
    ej['_filas'] = filas
    ej['_es'] = ES_DEFECTO if es is None else es
    ej['raiz'] = None

    a, x0 = ej.get('a'), ej.get('x0')
    if metodo == 'HORNER':
        p_val, dp_val, Q = horner(a, x0)
        ej['p_val'], ej['dp_val'], ej['Q'] = p_val, dp_val, Q
    elif metodo == 'DEFLACION':
        Q, resto = deflactar(a, x0)
        ej['Q'], ej['resto'] = Q, resto
    else:
        raise ValueError('Método desconocido: %s' % (metodo,))
    return ej


# `np` se conserva importado porque los verificadores del profesor lo usan
# sobre las tablas; aquí no se necesita para nada más.
_ = np

# -*- coding: utf-8 -*-
"""
profe/core/helpers.py — Utilidades base de formateo y generación aleatoria.
"""
import builtins

def _r(rng, lo, hi, dec=4) -> float:
    """Genera un número flotante aleatorio entre [lo, hi] redondeado a 'dec' decimales."""
    return builtins.round(float(rng.uniform(lo, hi)), dec)

def _fmt(v, dec=4) -> str:
    """Convierte un número a un texto LaTeX compacto."""
    if v == int(v) and builtins.abs(v) < 1e6:
        return str(int(v))
    return ('%.' + str(dec) + 'f') % v

def _poly_latex(coefs, var='x', dec=4) -> str:
    """
    Coeficientes ordenados de mayor a menor grado -> polinomio en LaTeX.

    `[1, -4, 0, 5, -2]` -> 'x^{4} - 4x^{3} + 5x - 2'

    Lo usan las fábricas (`modelos.py`) para inyectar el polinomio YA
    formateado en el enunciado, con el marcador `{polinomio}`. Así el .md no
    tiene que adivinar los signos: escribir los coeficientes a mano producía
    `+ -4x^3` cuando el coeficiente era negativo, y `{r1}{b}` se imprimía
    como `24`, que es ambiguo (¿2·4 o veinticuatro?).
    """
    n = builtins.len(coefs) - 1
    piezas = []
    for i, c in enumerate(coefs):
        grado = n - i
        if c == 0:
            continue
        mag = builtins.abs(c)
        if grado == 0:
            cuerpo = _fmt(mag, dec)
        elif grado == 1:
            cuerpo = var if mag == 1 else '%s%s' % (_fmt(mag, dec), var)
        else:
            pot = '%s^{%d}' % (var, grado)
            cuerpo = pot if mag == 1 else '%s%s' % (_fmt(mag, dec), pot)
        piezas.append(('-' if c < 0 else '+', cuerpo))

    if not piezas:
        return '0'
    texto = (piezas[0][1] if piezas[0][0] == '+' else '-' + piezas[0][1])
    for signo, cuerpo in piezas[1:]:
        texto += ' %s %s' % (signo, cuerpo)
    return texto

def _igual_num(a, b, tol) -> bool:
    """
    ¿Son iguales dos números (reales o complejos) con tolerancia RELATIVA?

    `tol` es una fracción: 1e-6 = seis dígitos.
    """
    try:
        a = complex(a)
        b = complex(b)
    except (TypeError, ValueError):
        return False
    if not (a == a and b == b):        # descarta nan
        return False
    return builtins.abs(a - b) <= tol * builtins.max(1.0, builtins.abs(b))

def _igual(a, b, tol) -> bool:
    """
    Compara recursivamente números, listas y tuplas con tolerancia relativa.

    Es lo que permite calificar funciones que devuelven VARIOS valores
    (`horner` devuelve `(p_val, dp_val, Q)`) o una lista de raíces (Bairstow),
    incluidas las complejas.
    """
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        try:
            if builtins.len(a) != builtins.len(b):
                return False
        except TypeError:
            return False
        return builtins.all(_igual(x, y, tol) for x, y in zip(a, b))
    return _igual_num(a, b, tol)

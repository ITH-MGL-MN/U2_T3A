# -*- coding: utf-8 -*-
"""
profe/core/registry.py — Catálogo de ejercicios y selección sembrada.

Cada método recibe SOLO las variantes que puede resolver: Horner necesita un
polinomio y un punto de evaluación; la deflación, un polinomio y una raíz
conocida. La selección usa el RNG del alumno, así que el ejercicio es
reproducible.
"""
from .modelos import (
    _ej_deflacion_engranes,
    _ej_deflacion_leva,
    _ej_horner_calibracion,
    _ej_horner_motor,
)
from .solvers import resolver

# Ejercicios disponibles por método (preguntas automáticas)
EJERCICIOS = {
    'HORNER': [_ej_horner_calibracion, _ej_horner_motor],
    'DEFLACION': [_ej_deflacion_leva, _ej_deflacion_engranes],
}

# Ejercicios específicos para la actividad realizada a mano
MANO_FABRICA = {
    'HORNER': [_ej_horner_calibracion, _ej_horner_motor],
    'DEFLACION': [_ej_deflacion_leva, _ej_deflacion_engranes],
}

NOMBRE_METODO = {
    'HORNER': 'Forma anidada de Horner',
    'DEFLACION': 'Deflación polinomial',
}

# Nombre EXACTO de la función que debe programar el alumno. Tiene que
# coincidir con la firma que anuncia su ficha de `profe/evaluador/`, porque el
# cuaderno declara esa función y la tarea la busca por nombre.
# La deflación no se programa en esta entrega: es actividad a mano.
NOMBRE_FUNCION = {
    'HORNER': 'horner',
    'DEFLACION': None,
}

METODOS_MANO = ('HORNER', 'DEFLACION')

# Qué se reporta en cada actividad a mano: una tupla (etiqueta, de dónde sale
# el valor de referencia). En Horner son el valor y la derivada; en la
# deflación, los tres coeficientes del polinomio reducido. `cuaderno.py`
# imprime la lista y compara componente a componente.
MANO_REPORTE = {
    'HORNER': (
        ('P(x_0)', lambda ej: ej['p_val']),
        ("P'(x_0)", lambda ej: ej['dp_val']),
    ),
    'DEFLACION': (
        ('A', lambda ej: ej['Q'][0]),
        ('B', lambda ej: ej['Q'][1]),
        ('C', lambda ej: ej['Q'][2]),
    ),
}

# Encabezado LaTeX del polinomio reducido, para los mensajes.
NOMBRE_REDUCIDO = {
    'DEFLACION': 'Q(x)',
}


def _sortear(fabricas, metodo, rng, es=None):
    """Sortea una variante con el RNG del alumno y la deja resuelta."""
    idx = int(rng.integers(0, len(fabricas)))
    return resolver(metodo, fabricas[idx](rng), es=es)


def elegir(metodo: str, rng, es=None):
    """Selecciona un ejercicio aleatorio del catálogo según el método y el RNG del alumno."""
    return _sortear(EJERCICIOS[metodo], metodo, rng, es=es)


def elegir_mano(metodo: str, rng, es=None):
    """Selecciona un ejercicio para la actividad manual según el método y el RNG del alumno."""
    return _sortear(MANO_FABRICA[metodo], metodo, rng, es=es)

# -*- coding: utf-8 -*-
# profe/core/__init__.py
from .seed import (
    extraer_nc,
    generar_semilla,
    obtener_rng
)

from .solvers import (
    ES_DEFECTO,
    MAX_ITER,
    deflactar,
    horner,
    iteracion_objetivo,
    iteraciones,
    resolver
)

from .registry import (
    EJERCICIOS,
    MANO_FABRICA,
    MANO_REPORTE,
    METODOS_MANO,
    NOMBRE_FUNCION,
    NOMBRE_METODO,
    NOMBRE_REDUCIDO,
    elegir,
    elegir_mano
)

__all__ = [
    'extraer_nc',
    'generar_semilla',
    'obtener_rng',
    'ES_DEFECTO',
    'MAX_ITER',
    'deflactar',
    'horner',
    'iteracion_objetivo',
    'iteraciones',
    'resolver',
    'EJERCICIOS',
    'MANO_FABRICA',
    'MANO_REPORTE',
    'METODOS_MANO',
    'NOMBRE_FUNCION',
    'NOMBRE_METODO',
    'NOMBRE_REDUCIDO',
    'elegir',
    'elegir_mano'
]

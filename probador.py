# -*- coding: utf-8 -*-
"""
probador.py — Herramienta local para inspeccionar un ejercicio por NC.

    python probador.py                       # NC y método por omisión
    python probador.py 16330887 HORNER       # número de control y método
    python probador.py 16330887 DEFLACION mano   # el de la actividad a mano

Muestra el enunciado tal como lo ve el alumno y la tabla de referencia (la
división sintética) que usa el motor para calificar.
"""
import sys

from profe.config import buscar, obtener_configuracion
from profe.core import MANO_REPORTE, METODOS_MANO, NOMBRE_METODO, elegir, elegir_mano, obtener_rng
from profe.ui.cuaderno import ORDEN_COLUMNAS, _lista_txt, _texto_tabla

NC_POR_OMISION = '16330887'
METODO_POR_OMISION = 'HORNER'


def id_tarea():
    """Nombre de la hoja / parte de la semilla, tal como está en config.yaml."""
    cfg, _ = obtener_configuracion()
    return buscar(cfg, 'tarea.id', 'U2_T3A')


def probar_ejercicio(nc=NC_POR_OMISION, metodo=METODO_POR_OMISION, mano=False):
    if metodo not in METODOS_MANO:
        print('Método desconocido: %r (usa uno de %s)'
              % (metodo, ', '.join(METODOS_MANO)))
        return 1

    tarea = id_tarea()
    partes = (nc, tarea, 'mano', metodo) if mano else (nc, tarea, metodo)
    rng = obtener_rng(*partes)
    ej = elegir_mano(metodo, rng) if mano else elegir(metodo, rng)

    print('=' * 68)
    print(' %s | NC: %s | %s' % (NOMBRE_METODO[metodo], nc,
                                 'actividad a mano' if mano else 'preguntas automáticas'))
    print('=' * 68)
    print('\nTÍTULO   : %s' % ej['titulo'])
    print('INCÓGNITA: %s [%s]' % (ej.get('incognita', '-'), ej.get('unidad', '-')))
    print('GRADO    : %d' % ej['grado'])
    print('POLINOMIO: a = %s' % _lista_txt(ej['a']))
    print('PUNTO    : x0 = %g' % ej['x0'])

    print('\n--- ENUNCIADO QUE VE EL ALUMNO ---')
    print(ej['contexto'].strip())
    print('----------------------------------')

    print('\nRespuestas de referencia (lo que se califica):')
    for etq, fn in MANO_REPORTE[metodo]:
        print('   %-10s = %.10g' % (etq, float(fn(ej))))
    if metodo == 'DEFLACION':
        print('   %-10s = %.10g   (debe ser 0 si la raíz es exacta)'
              % ('residuo', ej['resto']))

    print('\nTabla de referencia (división sintética):')
    print(_texto_tabla(ej['_filas'], ORDEN_COLUMNAS[metodo]))
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    nc = args[0] if args else NC_POR_OMISION
    metodo = args[1].upper() if len(args) > 1 else METODO_POR_OMISION
    mano = len(args) > 2 and args[2].lower().startswith('mano')
    sys.exit(probar_ejercicio(nc, metodo, mano))

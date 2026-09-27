"""
search/astar.py  -  Búsqueda A*
===============================
INTEGRANTE 3  |  Base teórica: Capítulo 9        *** PENDIENTE ***

    buscar(mapa, origen, destino) -> (camino, costo_total) o (None, None)

    g(n) = minutos acumulados (ya incluyen transbordos, vienen del mapa del Integrante 2)
    h(n) = kb.estaciones.distancia_km(n, destino) / kb.conexiones.VELOCIDAD_MAXIMA_KMH * 60

    Nota: origen y destino son estaciones, pero los nodos del mapa son
    (estacion, ruta). Se puede arrancar desde todos los nodos de la estación
    de origen y terminar al llegar a cualquier nodo de la estación destino.
"""


def buscar(mapa, origen, destino):
    raise NotImplementedError("Lo implementa el Integrante 3")

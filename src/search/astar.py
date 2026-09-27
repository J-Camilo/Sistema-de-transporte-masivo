import heapq

from kb.conexiones import VELOCIDAD_MAXIMA_KMH
from kb.estaciones import distancia_km


def heuristica(estacion, destino):
    """h(n): minutos que tardaría el bus en línea recta y a velocidad máxima."""
    return distancia_km(estacion, destino) / VELOCIDAD_MAXIMA_KMH * 60


def _reconstruir(padres, nodo):
    """Recorre los padres hacia atrás, desde el destino hasta el origen."""
    camino = [nodo]
    while padres[nodo] is not None:
        nodo = padres[nodo]
        camino.append(nodo)
    return list(reversed(camino))


def _a_estrella(mapa, origen, destino, usar_heuristica=True):
    """
    Núcleo de la búsqueda. Devuelve (camino, costo, nodos_expandidos).
    Con usar_heuristica=False, h(n) = 0 y el algoritmo es Dijkstra.
    """
    if origen == destino:
        return [], 0, 0

    h = heuristica if usar_heuristica else (lambda estacion, destino: 0)

    # Frontera: cola de prioridad ordenada por f = g + h.
    # El contador desempata sin tener que comparar nodos entre sí.
    frontera = []
    contador = 0
    g = {}        # mejor costo conocido para llegar a cada nodo
    padres = {}   # de qué nodo venimos, para reconstruir el camino

    for nodo in mapa:
        if nodo[0] == origen:
            g[nodo] = 0
            padres[nodo] = None
            heapq.heappush(frontera, (h(origen, destino), contador, nodo))
            contador += 1

    expandidos = 0
    while frontera:
        f, _, nodo = heapq.heappop(frontera)
        estacion = nodo[0]

        # Entrada vieja: ya encontramos un camino mejor a este nodo.
        if f > g[nodo] + h(estacion, destino):
            continue

        expandidos += 1
        if estacion == destino:
            return _reconstruir(padres, nodo), g[nodo], expandidos

        for vecino, minutos in mapa.get(nodo, []):
            nuevo_g = g[nodo] + minutos
            if vecino not in g or nuevo_g < g[vecino]:
                g[vecino] = nuevo_g
                padres[vecino] = nodo
                heapq.heappush(frontera, (nuevo_g + h(vecino[0], destino), contador, vecino))
                contador += 1

    return None, None, expandidos


def buscar(mapa, origen, destino):
    """Ruta de menor tiempo entre dos estaciones: (camino, costo) o (None, None)."""
    camino, costo, _ = _a_estrella(mapa, origen, destino)
    return camino, costo


def comparar(mapa, origen, destino):
    """
    Ejecuta A* y Dijkstra sobre el mismo mapa para demostrar que la heurística
    sirve: ambos encuentran el mismo costo, pero A* revisa menos nodos.
    """
    resultado = {}
    for nombre, usar_h in (("astar", True), ("dijkstra", False)):
        _, costo, expandidos = _a_estrella(mapa, origen, destino, usar_heuristica=usar_h)
        resultado[nombre] = {"costo": costo, "expandidos": expandidos}
    return resultado

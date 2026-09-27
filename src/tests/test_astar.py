"""Pruebas de la búsqueda A* con un mapa falso hecho a mano (Integrante 3).
Ejecutar desde la raíz del proyecto:  python -m unittest discover tests

El mapa falso tiene el mismo formato que devuelve engine.inferencia.construir_mapa,
así A* se prueba sin depender del motor de inferencia.
Las estaciones son reales (la heurística necesita sus coordenadas),
pero los minutos son inventados:

    cuba(R1) --20--> maraya(R1) --2--> el_jardin(R1)
                        ^  |
                      5 |  | 5     (transbordo dentro de Maraya)
                        |  v
    cuba(R2) --10--> maraya(R2) --6--> el_lago(R2)

    libertad(R3) está aislada: no se llega a ella desde ningún lado.
"""
import unittest

from search.astar import buscar, heuristica, comparar

MAPA_FALSO = {
    ("cuba", "R1"):      [(("maraya", "R1"), 20)],
    ("cuba", "R2"):      [(("maraya", "R2"), 10)],
    ("maraya", "R1"):    [(("el_jardin", "R1"), 2), (("maraya", "R2"), 5)],
    ("maraya", "R2"):    [(("maraya", "R1"), 5), (("el_lago", "R2"), 6)],
    ("el_jardin", "R1"): [],
    ("el_lago", "R2"):   [],
    ("libertad", "R3"):  [],
}


class TestAEstrella(unittest.TestCase):

    def test_misma_ruta_sin_transbordo(self):
        camino, costo = buscar(MAPA_FALSO, "cuba", "el_lago")
        self.assertEqual(camino, [("cuba", "R2"), ("maraya", "R2"), ("el_lago", "R2")])
        self.assertEqual(costo, 16)

    def test_con_transbordo_si_sale_mas_barato(self):
        # Directo por R1: 20 + 2 = 22.  Por R2 y transbordo en Maraya: 10 + 5 + 2 = 17.
        camino, costo = buscar(MAPA_FALSO, "cuba", "el_jardin")
        self.assertEqual(camino, [("cuba", "R2"), ("maraya", "R2"),
                                  ("maraya", "R1"), ("el_jardin", "R1")])
        self.assertEqual(costo, 17)

    def test_origen_igual_a_destino(self):
        camino, costo = buscar(MAPA_FALSO, "maraya", "maraya")
        self.assertEqual(costo, 0)
        self.assertEqual(camino, [])

    def test_ruta_imposible(self):
        self.assertEqual(buscar(MAPA_FALSO, "cuba", "libertad"), (None, None))

    def test_mapa_vacio_sistema_cerrado(self):
        # Si todas las reglas bloquean los arcos, el mapa llega vacío.
        self.assertEqual(buscar({}, "cuba", "maraya"), (None, None))

    def test_heuristica_cero_en_el_destino(self):
        self.assertEqual(heuristica("cuba", "cuba"), 0)

    def test_heuristica_nunca_supera_el_costo_real(self):
        # Admisibilidad: h(origen) <= costo óptimo real, para todos los pares posibles.
        estaciones = {est for est, _ in MAPA_FALSO}
        for origen in estaciones:
            for destino in estaciones:
                _, costo = buscar(MAPA_FALSO, origen, destino)
                if costo is not None:
                    self.assertLessEqual(heuristica(origen, destino), costo)

    def test_dijkstra_da_el_mismo_costo_y_revisa_mas_o_igual_nodos(self):
        resultado = comparar(MAPA_FALSO, "cuba", "el_jardin")
        self.assertEqual(resultado["astar"]["costo"], resultado["dijkstra"]["costo"])
        self.assertLessEqual(resultado["astar"]["expandidos"],
                             resultado["dijkstra"]["expandidos"])


if __name__ == "__main__":
    unittest.main()

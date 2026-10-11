"""
Pruebas de ml/reporte.py: las páginas HTML de la evaluación y de la integración.
Solo usan la biblioteca estándar.
"""
import unittest

from engine.inferencia import construir_mapa
from ml.integracion import a_regla_motor, hechos_de_viaje, inferir_demora, leer_reglas
from ml.reporte import condiciones_marcadas, html_evaluacion, html_integracion
from search.astar import buscar

ARBOL = """\
|--- tiempo_base_min <= 7.98
|   |--- class: media
|--- tiempo_base_min >  7.98
|   |--- hora <= 16.50
|   |   |--- class: baja
|   |--- hora >  16.50
|   |   |--- clima_lluvia <= 0.50
|   |   |   |--- class: alta
|   |   |--- clima_lluvia >  0.50
|   |   |   |--- class: alta
"""

RESULTADOS = {
    "profundidad": 7, "viajes_prueba": 1200, "accuracy": 0.803,
    "por_clase": [("baja", 0.845, 0.859, 0.852, 512), ("media", 0.754, 0.815, 0.783, 417),
                  ("alta", 0.807, 0.679, 0.737, 271)],
    "matriz": [[440, 56, 16], [49, 340, 28], [32, 55, 184]],
    "modelos": [{"nombre": "Línea base (DummyClassifier)", "prueba": 0.427, "cv": [0.427] * 5},
                {"nombre": "Árbol de decisión (profundidad 7)", "prueba": 0.803,
                 "cv": [0.801, 0.781, 0.819, 0.816, 0.791]}],
    "curva": [(3, 0.621), (7, 0.802), (12, 0.796)],
    "fidelidad": {"reglas": 93, "iguales": 1200, "viajes": 1200},
    "por_regla": [("ML1", "tiempo base min >= 7.98 -> demora alta", 105, 0.848)],
}


class TestReporteEvaluacion(unittest.TestCase):

    def setUp(self):
        self.html = html_evaluacion(RESULTADOS)

    def test_es_una_pagina_completa(self):
        self.assertTrue(self.html.startswith("<!doctype html>"))
        self.assertIn("prefers-color-scheme: dark", self.html)

    def test_muestra_el_acierto_y_la_linea_base(self):
        self.assertIn("80,3 %", self.html)
        self.assertIn("42,7 %", self.html)

    def test_la_matriz_tiene_las_nueve_celdas(self):
        for valor in (440, 56, 16, 49, 340, 28, 32, 55, 184):
            self.assertIn(f">{valor}<", self.html)

    def test_muestra_la_fidelidad_del_motor(self):
        self.assertIn("1200 de 1200", self.html)


class TestReporteIntegracion(unittest.TestCase):

    def setUp(self):
        self.reglas = [a_regla_motor(r, f"ML{i}") for i, r in enumerate(leer_reglas(ARBOL), 1)]
        mapa, _ = construir_mapa("18:00")
        self.camino, self.costo = buscar(mapa, "cuba", "dosquebradas")
        self.mapa = mapa
        self.hechos = hechos_de_viaje(self.camino, "cuba", "dosquebradas", "18:00",
                                      "miercoles", "despejado", False)
        self.nivel, self.traza = inferir_demora(self.hechos, self.reglas)

    def generar(self):
        return html_integracion(self.mapa, self.camino, self.costo, "cuba", "dosquebradas",
                                "18:00", self.hechos, self.traza, self.reglas, self.nivel)

    def test_condiciones_marcadas_con_el_valor_del_viaje(self):
        disparada = next(r for r in self.reglas if r["id"] == "ML3")
        marcadas = condiciones_marcadas(disparada, self.hechos)
        self.assertTrue(all(ok for _, _, ok in marcadas))
        self.assertIn(("hora >= 17:00", "18:00", True), marcadas)
        self.assertIn(("clima != lluvia", "despejado", True), marcadas)

    def test_condicion_que_falla_queda_marcada(self):
        marcadas = condiciones_marcadas(self.reglas[0], self.hechos)   # tiempo base < 7.98
        self.assertFalse(marcadas[0][2])

    def test_muestra_la_demora_y_la_ruta(self):
        html = self.generar()
        self.assertIn("ALTA", html)
        self.assertIn("Intercambiador Dosquebradas", html)

    def test_separa_reglas_a_mano_y_aprendidas(self):
        html = self.generar()
        self.assertIn("D2", html)
        self.assertIn("ML3", html)
        self.assertIn("Escrita a mano", html)
        self.assertIn("Aprendida por el árbol", html)

    def test_sin_regla_que_aplique(self):
        html = html_integracion(self.mapa, self.camino, self.costo, "cuba", "dosquebradas",
                                "18:00", self.hechos, [], self.reglas, None)
        self.assertIn("Ninguna de las reglas cargadas aplica", html)


if __name__ == "__main__":
    unittest.main()

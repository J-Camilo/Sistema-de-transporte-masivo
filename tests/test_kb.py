"""Pruebas de la base de conocimiento (Integrante 1).
Ejecutar desde la raíz del proyecto:  python -m unittest discover tests
"""
import unittest

from kb.estaciones import ESTACIONES, buscar_por_nombre, distancia_km
from kb.conexiones import CONEXIONES, validar, rutas_de_estacion
from kb.reglas import REGLAS, hora_a_minutos


class TestBaseConocimiento(unittest.TestCase):

    def test_base_coherente(self):
        self.assertEqual(validar(), [])

    def test_buscar_estacion_con_y_sin_tildes(self):
        self.assertEqual(buscar_por_nombre("Egoyá"), "egoya")
        self.assertEqual(buscar_por_nombre("egoya"), "egoya")
        self.assertEqual(buscar_por_nombre("intercambiador cuba"), "cuba")

    def test_estacion_inexistente(self):
        self.assertIsNone(buscar_por_nombre("Estación Marte"))

    def test_maraya_es_punto_de_transbordo(self):
        self.assertEqual(rutas_de_estacion("maraya"), {"R1", "R2", "R3"})

    def test_ruta3_no_llega_a_dosquebradas(self):
        self.assertNotIn("R3", rutas_de_estacion("dosquebradas"))

    def test_distancia_cero_a_si_misma(self):
        self.assertAlmostEqual(distancia_km("cuba", "cuba"), 0.0)

    def test_hora_a_minutos(self):
        self.assertEqual(hora_a_minutos("07:30"), 450)
        with self.assertRaises(ValueError):
            hora_a_minutos("25:00")

    def test_reglas_bien_formadas(self):
        ids = [r["id"] for r in REGLAS]
        self.assertEqual(len(ids), len(set(ids)), "Hay ids de reglas repetidos")
        for r in REGLAS:
            self.assertIn(r["tipo"], ("deduccion", "ajuste"))
            self.assertTrue(r["si"] and r["entonces"] and r["descripcion"])


if __name__ == "__main__":
    unittest.main()

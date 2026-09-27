"""Pruebas de integración: base de conocimiento + motor + A* + consola (Integrante 3).
Ejecutar desde la raíz del proyecto:  python -m unittest discover tests
"""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from engine.inferencia import construir_mapa
from main import main, resumir_camino, reglas_del_camino
from search.astar import buscar, heuristica


def ejecutar(*argumentos):
    """Corre main() capturando lo que imprime. Devuelve (codigo, salida)."""
    salida = io.StringIO()
    with redirect_stdout(salida):
        codigo = main(list(argumentos))
    return codigo, salida.getvalue()


class TestConsola(unittest.TestCase):

    def test_consulta_valida(self):
        codigo, salida = ejecutar("--origen", "Cuba", "--destino", "Dosquebradas", "--hora", "10:00")
        self.assertEqual(codigo, 0)
        self.assertIn("RUTA RECOMENDADA", salida)
        self.assertIn("TIEMPO TOTAL", salida)

    def test_acepta_nombres_con_tildes_y_mayusculas(self):
        codigo, _ = ejecutar("--origen", "EGOYÁ", "--destino", "el lago", "--hora", "10:00")
        self.assertEqual(codigo, 0)

    def test_estacion_que_no_existe(self):
        codigo, salida = ejecutar("--origen", "Estación Marte", "--destino", "Cuba", "--hora", "10:00")
        self.assertEqual(codigo, 1)
        self.assertIn("no existe", salida)

    def test_hora_invalida(self):
        codigo, _ = ejecutar("--origen", "Cuba", "--destino", "Maraya", "--hora", "25:00")
        self.assertEqual(codigo, 1)

    def test_origen_igual_a_destino(self):
        codigo, salida = ejecutar("--origen", "Maraya", "--destino", "Maraya", "--hora", "10:00")
        self.assertEqual(codigo, 0)
        self.assertIn("Ya estás", salida)

    def test_sistema_cerrado_ruta_imposible(self):
        codigo, salida = ejecutar("--origen", "Cuba", "--destino", "Dosquebradas", "--hora", "03:00")
        self.assertEqual(codigo, 2)
        self.assertIn("A1", salida)


class TestReporteHtml(unittest.TestCase):

    def test_html_se_genera_y_se_abre_en_el_navegador(self):
        carpeta_original = os.getcwd()
        with tempfile.TemporaryDirectory() as carpeta, \
                mock.patch("main.webbrowser.open") as abrir:
            os.chdir(carpeta)
            try:
                codigo, _ = ejecutar("--origen", "Parque Olaya", "--destino", "Egoyá",
                                     "--hora", "07:30", "--html")
                html = open("resultado.html", encoding="utf-8").read()
            finally:
                os.chdir(carpeta_original)
        self.assertEqual(codigo, 0)
        abrir.assert_called_once()
        self.assertIn("Transbordo en Maraya", html)
        self.assertIn("Hora pico aplicada", html)
        self.assertIn("<svg", html)


class TestConMotorReal(unittest.TestCase):

    def test_hora_pico_tarda_mas_que_hora_valle(self):
        _, costo_valle = buscar(construir_mapa("10:00")[0], "cuba", "dosquebradas")
        _, costo_pico = buscar(construir_mapa("07:30")[0], "cuba", "dosquebradas")
        self.assertGreater(costo_pico, costo_valle)

    def test_heuristica_consistente_en_el_mapa_real(self):
        # Para todo arco a->b: h(a) <= costo(a,b) + h(b). Si se cumple, A* es óptimo.
        for hora in ("07:30", "10:00", "17:30", "22:00"):
            mapa, _ = construir_mapa(hora)
            for destino in ("cuba", "dosquebradas", "el_lago"):
                for (a, _), vecinos in mapa.items():
                    for (b, _), minutos in vecinos:
                        self.assertLessEqual(heuristica(a, destino),
                                             minutos + heuristica(b, destino) + 1e-9)

    def test_resumen_marca_los_transbordos(self):
        mapa = {("cuba", "R2"): [(("maraya", "R2"), 10)],
                ("maraya", "R2"): [(("maraya", "R1"), 5)],
                ("maraya", "R1"): [(("el_jardin", "R1"), 2)]}
        pasos = resumir_camino(mapa, [("cuba", "R2"), ("maraya", "R2"),
                                      ("maraya", "R1"), ("el_jardin", "R1")])
        self.assertEqual([p["tipo"] for p in pasos], ["tramo", "transbordo", "tramo"])
        self.assertEqual(pasos[1]["minutos"], 5)
        self.assertEqual(pasos[0]["paradas"], 1)

    def test_reglas_del_camino_solo_incluye_arcos_usados(self):
        mapa, traza = construir_mapa("07:30")
        camino, _ = buscar(mapa, "cuba", "maraya")
        ids = [r["id"] for r in reglas_del_camino(camino, traza)]
        self.assertIn("D1", ids)       # es hora pico
        self.assertIn("A2", ids)       # los tramos tardan 40 % más
        self.assertNotIn("A3", ids)    # Cuba -> Maraya no pasa por el centro


if __name__ == "__main__":
    unittest.main()

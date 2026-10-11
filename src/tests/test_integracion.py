"""
Pruebas de ml/integracion.py: las reglas que aprendió el árbol se traducen al
formato de kb/reglas.py y el motor de inferencia de la Actividad 1 las ejecuta.

Solo usan la biblioteca estándar: no necesitan scikit-learn ni el modelo entrenado.
"""
import unittest

from kb import reglas as kb_reglas
from ml.integracion import (a_condicion_motor, a_regla_motor, hechos_de_fila,
                            inferir_demora, leer_reglas, medir, seleccionar)

# Árbol pequeño escrito con el mismo formato de export_text().
TEXTO_ARBOL = """\
|--- tiempo_base_min <= 7.11
|   |--- hora <= 16.50
|   |   |--- class: baja
|   |--- hora >  16.50
|   |   |--- clima_lluvia <= 0.50
|   |   |   |--- class: media
|   |   |--- clima_lluvia >  0.50
|   |   |   |--- class: alta
|--- tiempo_base_min >  7.11
|   |--- estacion_destino_San Fernando <= 0.50
|   |   |--- class: alta
|   |--- estacion_destino_San Fernando >  0.50
|   |   |--- class: media
"""

FILA = {"id_viaje": "1", "estacion_origen": "Maraya", "estacion_destino": "Egoyá",
        "ruta": "Ruta 2", "num_transbordos": "0", "distancia_km": "0.5", "hora": "18",
        "dia_semana": "lunes", "es_festivo": "0", "clima": "lluvia",
        "tiempo_base_min": "4.2", "tiempo_real_min": "7.9", "nivel_demora": "alta"}


class TestLeerReglas(unittest.TestCase):

    def test_cada_hoja_es_una_regla(self):
        reglas = leer_reglas(TEXTO_ARBOL)
        self.assertEqual([r["clase"] for r in reglas], ["baja", "media", "alta", "alta", "media"])

    def test_la_regla_guarda_el_camino_desde_la_raiz(self):
        tercera = leer_reglas(TEXTO_ARBOL)[2]
        self.assertEqual(tercera["condiciones"], [("tiempo_base_min", "<=", 7.11),
                                                  ("hora", ">", 16.5),
                                                  ("clima_lluvia", ">", 0.5)])

    def test_nombres_de_columna_con_espacios(self):
        ultima = leer_reglas(TEXTO_ARBOL)[-1]
        self.assertEqual(ultima["condiciones"][-1], ("estacion_destino_San Fernando", ">", 0.5))


class TestTraduccion(unittest.TestCase):

    def test_columna_dummy_mayor_es_igual(self):
        self.assertEqual(a_condicion_motor("clima_lluvia", ">", 0.5), ("clima", "==", "lluvia"))

    def test_columna_dummy_menor_es_distinto(self):
        self.assertEqual(a_condicion_motor("estacion_destino_San Fernando", "<=", 0.5),
                         ("estacion_destino", "!=", "San Fernando"))

    def test_hora_usa_el_formato_hh_mm_del_motor(self):
        # hora <= 16.5 significa "salió a las 16:xx o antes", o sea antes de las 17:00.
        self.assertEqual(a_condicion_motor("hora", "<=", 16.5), ("hora", "<", "17:00"))
        self.assertEqual(a_condicion_motor("hora", ">", 16.5), ("hora", ">=", "17:00"))

    def test_es_festivo_es_si_o_no(self):
        self.assertEqual(a_condicion_motor("es_festivo", "<=", 0.5), ("es_festivo", "==", 0))
        self.assertEqual(a_condicion_motor("es_festivo", ">", 0.5), ("es_festivo", "==", 1))

    def test_columna_numerica(self):
        self.assertEqual(a_condicion_motor("tiempo_base_min", "<=", 7.11),
                         ("tiempo_base_min", "<", 7.11))
        self.assertEqual(a_condicion_motor("tiempo_base_min", ">", 7.11),
                         ("tiempo_base_min", ">=", 7.11))

    def test_simplifica_condiciones_repetidas_en_un_rango(self):
        regla = {"clase": "media", "condiciones": [
            ("hora", ">", 8.5), ("hora", "<=", 16.5), ("hora", "<=", 13.5), ("hora", ">", 10.5),
            ("tiempo_base_min", ">", 7.11), ("tiempo_base_min", ">", 9.0),
            ("clima_lluvia", "<=", 0.5), ("clima_nublado", "<=", 0.5)]}
        self.assertEqual(a_regla_motor(regla, "ML1")["si"], [
            ("hora", "entre", ("11:00", "14:00")),
            ("tiempo_base_min", ">=", 9.0),
            ("clima", "!=", "lluvia"),
            ("clima", "!=", "nublado")])

    def test_un_igual_hace_sobrar_los_distintos(self):
        regla = {"clase": "alta", "condiciones": [("clima_nublado", "<=", 0.5),
                                                  ("clima_lluvia", ">", 0.5)]}
        self.assertEqual(a_regla_motor(regla, "ML1")["si"], [("clima", "==", "lluvia")])

    def test_regla_con_el_formato_de_kb_reglas(self):
        regla = a_regla_motor(leer_reglas(TEXTO_ARBOL)[2], "ML1")
        self.assertEqual(regla["id"], "ML1")
        self.assertEqual(regla["tipo"], "deduccion")
        self.assertEqual(regla["entonces"], ("agregar_hecho", "nivel_demora", "alta"))
        self.assertIn(("clima", "==", "lluvia"), regla["si"])
        self.assertTrue(regla["descripcion"])


class TestMotorConReglasAprendidas(unittest.TestCase):

    def setUp(self):
        self.reglas = [a_regla_motor(r, f"ML{i}")
                       for i, r in enumerate(leer_reglas(TEXTO_ARBOL), start=1)]

    def test_hechos_de_una_fila_del_csv(self):
        hechos = hechos_de_fila(FILA)
        self.assertEqual(hechos["hora"], 18 * 60)
        self.assertEqual(hechos["tiempo_base_min"], 4.2)
        self.assertEqual(hechos["es_festivo"], 0)
        self.assertNotIn("nivel_demora", hechos)
        self.assertNotIn("tiempo_real_min", hechos)

    def test_el_motor_deduce_la_demora(self):
        nivel, traza = inferir_demora(hechos_de_fila(FILA), self.reglas)
        self.assertEqual(nivel, "alta")
        self.assertIn("ML3", [t["regla"] for t in traza])

    def test_las_reglas_de_la_actividad_1_siguen_activas(self):
        # 18:00 es hora pico: D2 (escrita a mano) se dispara junto a la aprendida.
        _, traza = inferir_demora(hechos_de_fila(FILA), self.reglas)
        self.assertIn("D2", [t["regla"] for t in traza])

    def test_sin_regla_que_aplique_no_hay_conclusion(self):
        nivel, _ = inferir_demora(hechos_de_fila(FILA), self.reglas[:1])
        self.assertIsNone(nivel)

    def test_la_base_de_conocimiento_queda_intacta(self):
        antes = list(kb_reglas.REGLAS)
        inferir_demora(hechos_de_fila(FILA), self.reglas)
        self.assertEqual(kb_reglas.REGLAS, antes)


class TestSeleccion(unittest.TestCase):

    def setUp(self):
        self.reglas = leer_reglas(TEXTO_ARBOL)
        self.filas = [FILA, dict(FILA, clima="despejado", nivel_demora="media"),
                      dict(FILA, hora="9", nivel_demora="baja"),
                      dict(FILA, hora="10", nivel_demora="media")]

    def test_medir_soporte_y_acierto(self):
        soporte, acierto = medir(self.reglas[0], self.filas)   # hora < 17 -> baja
        self.assertEqual(soporte, 2)
        self.assertEqual(acierto, 0.5)

    def test_seleccionar_prefiere_reglas_sin_estaciones(self):
        elegidas = seleccionar(self.reglas, self.filas, cantidad=10)
        columnas = [c for r in elegidas for c, _, _ in r["condiciones"]]
        self.assertFalse(any(c.startswith("estacion_") for c in columnas))

    def test_seleccionar_ordena_por_soporte(self):
        elegidas = seleccionar(self.reglas, self.filas, cantidad=2, acierto_minimo=0)
        self.assertEqual(elegidas[0]["soporte"], 2)


if __name__ == "__main__":
    unittest.main()

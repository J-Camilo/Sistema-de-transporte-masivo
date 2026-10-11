"""
Pruebas del Rol C de la Actividad 3: jerarquico.py y validacion.py.

Usan curvas pequeñas inventadas para saber de antemano la respuesta correcta.
Necesitan scikit-learn y scipy (py -m pip install -r requirements.txt).
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Los módulos de cluster se importan como "src.cluster...", igual que en el Rol A y el Rol B.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cluster.jerarquico import agrupar_ward, matriz_enlace  # noqa: E402
from src.cluster.validacion import (barrido_dbscan, comparar_particiones,  # noqa: E402
                                    describir_grupos, nombrar_grupos, validar_contra_reales)

HORAS = list(range(5, 23))


def curva(abordajes, descensos):
    """Una fila de la matriz 20 x 36: 18 horas de abordajes + 18 de descensos, normalizada."""
    fila = np.array(abordajes + descensos, dtype=float)
    return fila / fila.sum()


def pico(hora_inicio, hora_fin, alto=10.0, bajo=1.0):
    return [alto if hora_inicio <= h <= hora_fin else bajo for h in HORAS]


PLANO = [5.0] * 18
# Cuatro arquetipos claros, tres estaciones de cada uno.
ARQUETIPOS = {
    "residencial": curva(pico(6, 8), pico(17, 19)),   # sale en la mañana, vuelve en la tarde
    "laboral": curva(pico(17, 19), pico(6, 8)),       # el espejo
    "mixta": curva(pico(11, 13), pico(11, 13)),       # repunte al mediodía
    "intercambio": curva(PLANO, PLANO),               # parejo todo el día
}


def matriz_de_prueba(ruido=0.002, semilla=1):
    generador = np.random.default_rng(semilla)
    filas, nombres, reales = [], [], []
    for tipo, base in ARQUETIPOS.items():
        for i in range(3):
            fila = np.clip(base + generador.normal(0, ruido, base.size), 1e-6, None)
            filas.append(fila / fila.sum())
            nombres.append(f"{tipo}_{i}")
            reales.append(tipo)
    columnas = [f"ab_{h:02d}" for h in HORAS] + [f"de_{h:02d}" for h in HORAS]
    return pd.DataFrame(filas, index=nombres, columns=columnas), pd.Series(reales, index=nombres)


class TestJerarquico(unittest.TestCase):

    def setUp(self):
        self.matriz, self.reales = matriz_de_prueba()

    def test_ward_separa_los_cuatro_tipos(self):
        grupos = agrupar_ward(self.matriz.to_numpy(), k=4)
        self.assertEqual(len(set(grupos)), 4)
        self.assertAlmostEqual(comparar_particiones(grupos, self.reales)["ari"], 1.0)

    def test_matriz_de_enlace_para_el_dendrograma(self):
        enlace = matriz_enlace(self.matriz.to_numpy())
        self.assertEqual(enlace.shape, (len(self.matriz) - 1, 4))


class TestComparacion(unittest.TestCase):

    def test_mismos_grupos_con_otros_numeros_dan_ari_1(self):
        # El número de cada grupo es arbitrario: lo que importa es quién queda con quién.
        resultado = comparar_particiones([0, 0, 1, 1, 2, 2], [5, 5, 3, 3, 9, 9])
        self.assertAlmostEqual(resultado["ari"], 1.0)

    def test_tabla_cruzada(self):
        resultado = comparar_particiones([0, 0, 1, 1], ["a", "b", "b", "b"])
        self.assertEqual(resultado["tabla"].loc[1, "b"], 2)
        self.assertLess(resultado["ari"], 1.0)


class TestDbscan(unittest.TestCase):

    def test_barrido_cuenta_grupos_y_atipicas(self):
        matriz, _ = matriz_de_prueba()
        tabla = barrido_dbscan(matriz, [0.0001, 1000])
        muy_chico, muy_grande = tabla.iloc[0], tabla.iloc[1]
        self.assertEqual(muy_chico["atipicas"], len(matriz))     # nadie tiene vecinos
        self.assertEqual(muy_grande["grupos"], 1)                # todo es un solo grupo
        self.assertEqual(muy_grande["atipicas"], 0)


class TestInterpretacion(unittest.TestCase):

    def setUp(self):
        self.matriz, self.reales = matriz_de_prueba()
        # Números de grupo arbitrarios, como los que pone K-means.
        numero = {"residencial": 2, "laboral": 0, "mixta": 3, "intercambio": 1}
        self.grupos = pd.Series([numero[t] for t in self.reales], index=self.matriz.index)

    def test_describir_grupos(self):
        resumen = describir_grupos(self.matriz, self.grupos)
        residencial = resumen.loc[2]
        self.assertGreater(residencial["sube_manana"], residencial["baja_manana"])
        self.assertLess(resumen.loc[1]["variacion"], resumen.loc[3]["variacion"])

    def test_nombra_cada_grupo_por_la_forma_de_su_curva(self):
        nombres = nombrar_grupos(self.matriz, self.grupos)
        self.assertEqual(nombres, {2: "residencial", 0: "laboral", 3: "mixta", 1: "intercambio"})

    def test_validar_contra_los_tipos_reales(self):
        nombres = nombrar_grupos(self.matriz, self.grupos)
        resultado = validar_contra_reales(self.grupos.map(nombres), self.reales)
        self.assertEqual(resultado["aciertos"], 12)
        self.assertAlmostEqual(resultado["ari"], 1.0)
        self.assertEqual(resultado["errores"], [])


if __name__ == "__main__":
    unittest.main()

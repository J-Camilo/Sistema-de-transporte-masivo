# -*- coding: utf-8 -*-
"""Rol B: estandarización y agrupamiento K-means de estaciones del Megabús.

Ejecutar desde la raíz del repositorio:
    py -m src.cluster.kmeans_modelo
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.cluster.preparacion import preparar_datos, CARPETA_RESULTADOS

RUTA_MODELO = Path(CARPETA_RESULTADOS) / "modelo_kmeans.joblib"


def estandarizar_datos(matriz_normalizada):
    """Ajusta StandardScaler sobre la matriz de 20 x 36 y la transforma."""
    if not isinstance(matriz_normalizada, pd.DataFrame):
        raise TypeError("Se esperaba un DataFrame con las estaciones como índice.")
    if matriz_normalizada.empty or matriz_normalizada.isna().any().any():
        raise ValueError("La matriz está vacía o contiene valores nulos.")
    if not np.isfinite(matriz_normalizada.to_numpy(dtype=float)).all():
        raise ValueError("La matriz contiene valores no finitos.")

    escalador = StandardScaler()
    datos_escalados = escalador.fit_transform(matriz_normalizada)
    return datos_escalados, escalador


def entrenar_kmeans(datos_escalados, k=4):
    """Entrena K-means con k grupos y devuelve el modelo ajustado."""
    if not 2 <= k <= len(datos_escalados):
        raise ValueError("k debe ser al menos 2 y no superar el número de estaciones.")
    modelo = KMeans(n_clusters=k, random_state=42, n_init=20)
    modelo.fit(datos_escalados)
    return modelo


def guardar_modelo(modelo, escalador, columnas, estaciones, ruta=RUTA_MODELO):
    """Guarda modelo, escalador y metadatos para reutilizarlos en otros módulos."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "escalador": escalador,
            "columnas": list(columnas),
            "estaciones": list(estaciones),
        },
        ruta,
    )
    return ruta


def main():
    print("\n--- AGRUPAMIENTO K-MEANS: MEGABÚS ---")
    matriz, matriz_normalizada = preparar_datos()
    datos_escalados, escalador = estandarizar_datos(matriz_normalizada)
    modelo = entrenar_kmeans(datos_escalados, k=4)

    print(f"Estaciones: {matriz.shape[0]}")
    print(f"Características por estación: {matriz.shape[1]}")
    print(f"Grupos solicitados: {modelo.n_clusters}")
    print(f"Inercia: {modelo.inertia_:.4f}")

    asignaciones = pd.DataFrame({
        "estacion": matriz_normalizada.index,
        "grupo": modelo.labels_,
    })
    for grupo, filas in asignaciones.groupby("grupo"):
        print(f"\nGrupo {grupo} ({len(filas)} estaciones):")
        for estacion in filas["estacion"]:
            print(f"  - {estacion}")

    ruta = guardar_modelo(
        modelo, escalador, matriz_normalizada.columns, matriz_normalizada.index
    )
    print(f"\nModelo guardado en: {ruta}")
    print("Entrenamiento completado correctamente.")


if __name__ == "__main__":
    main()

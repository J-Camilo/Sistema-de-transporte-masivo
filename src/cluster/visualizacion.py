# -*- coding: utf-8 -*-
"""Rol B: visualización PCA de los grupos K-means de Megabús.

Ejecutar desde la raíz del proyecto:
    py -m src.cluster.visualizacion

Requiere haber ejecutado previamente:
    py -m src.cluster.kmeans_modelo
"""
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.cluster.preparacion import preparar_datos, CARPETA_RESULTADOS, CARPETA_SALIDA
from src.cluster.kmeans_modelo import RUTA_MODELO

RUTA_GRAFICA = Path(CARPETA_RESULTADOS) / "grafica_pca.png"
RUTA_GRUPOS = Path(CARPETA_SALIDA) / "grupos_encontrados.csv"


def cargar_modelo_y_datos(ruta_modelo=RUTA_MODELO):
    """Carga el modelo ya entrenado y verifica que corresponda a los datos."""
    ruta_modelo = Path(ruta_modelo)
    if not ruta_modelo.is_file():
        raise FileNotFoundError(
            f"No se encontró el modelo: {ruta_modelo}\n"
            "Primero ejecuta: py -m src.cluster.kmeans_modelo"
        )

    paquete = joblib.load(ruta_modelo)  # Usar solo archivos generados por este proyecto.
    _, matriz_normalizada = preparar_datos()

    if list(matriz_normalizada.columns) != paquete["columnas"]:
        raise ValueError("Las columnas no coinciden con las del entrenamiento.")
    if list(matriz_normalizada.index) != paquete["estaciones"]:
        raise ValueError("El orden de las estaciones cambió desde el entrenamiento.")

    datos_escalados = paquete["escalador"].transform(matriz_normalizada)
    modelo = paquete["modelo"]
    grupos = modelo.predict(datos_escalados)
    if not np.array_equal(grupos, modelo.labels_):
        raise ValueError("Los grupos predichos difieren de los guardados en el modelo.")
    return matriz_normalizada.index, datos_escalados, grupos


def calcular_pca(datos_escalados):
    """Reduce las 36 características estandarizadas a dos componentes PCA."""
    pca = PCA(n_components=2)
    coordenadas = pca.fit_transform(datos_escalados)
    return coordenadas, pca


def guardar_grupos(estaciones, grupos, ruta=RUTA_GRUPOS):
    """Exporta una fila por estación con el grupo asignado por K-means."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla = pd.DataFrame({"estacion": list(estaciones), "grupo": grupos})
    tabla.to_csv(ruta, index=False, encoding="utf-8-sig")
    return tabla, ruta


def graficar_pca(estaciones, grupos, coordenadas, pca, ruta=RUTA_GRAFICA):
    """Genera una gráfica PCA con nombres y colores según los grupos."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 8))
    colores = plt.get_cmap("tab10")
    for grupo in sorted(set(grupos)):
        indices = np.flatnonzero(grupos == grupo)
        ax.scatter(
            coordenadas[indices, 0], coordenadas[indices, 1],
            color=colores(int(grupo)), s=100, alpha=0.85,
            edgecolors="white", linewidths=0.8,
            label=f"Grupo {grupo} ({len(indices)} estaciones)",
        )

    for i, estacion in enumerate(estaciones):
        ax.annotate(str(estacion), (coordenadas[i, 0], coordenadas[i, 1]),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)

    varianza = pca.explained_variance_ratio_ * 100
    ax.set_xlabel(f"Componente principal 1 ({varianza[0]:.1f}% de varianza)")
    ax.set_ylabel(f"Componente principal 2 ({varianza[1]:.1f}% de varianza)")
    ax.set_title("Estaciones Megabús agrupadas por K-means (PCA)")
    ax.axhline(0, color="gray", linewidth=0.6, alpha=0.4)
    ax.axvline(0, color="gray", linewidth=0.6, alpha=0.4)
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return ruta


def main():
    print("\n--- VISUALIZACIÓN PCA: MEGABÚS ---")
    estaciones, datos_escalados, grupos = cargar_modelo_y_datos()
    coordenadas, pca = calcular_pca(datos_escalados)
    tabla, ruta_csv = guardar_grupos(estaciones, grupos)
    ruta_png = graficar_pca(estaciones, grupos, coordenadas, pca)

    print(f"Estaciones: {len(estaciones)}")
    print(f"Características originales: {datos_escalados.shape[1]}")
    print("Componentes PCA: 2")
    print(f"Varianza explicada por PCA: {pca.explained_variance_ratio_.sum() * 100:.2f}%")
    for grupo, filas in tabla.groupby("grupo"):
        print(f"Grupo {grupo}: {len(filas)} estaciones")
    print(f"CSV de grupos: {ruta_csv}")
    print(f"Gráfica PCA: {ruta_png}")
    print("Visualización finalizada correctamente.")


if __name__ == "__main__":
    main()

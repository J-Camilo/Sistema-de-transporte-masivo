# -*- coding: utf-8 -*-
"""Rol B: selección del número de grupos mediante codo y silueta.

Ejecutar desde la raíz del repositorio:
    py -m src.cluster.seleccion_k
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import silhouette_score

from src.cluster.preparacion import preparar_datos, CARPETA_RESULTADOS
from src.cluster.kmeans_modelo import estandarizar_datos, entrenar_kmeans

CARPETA_SALIDA = Path(CARPETA_RESULTADOS)


def evaluar_valores_k(datos_escalados, minimo=2, maximo=8):
    """Calcula inercia y silueta para cada k usando los mismos datos."""
    n = len(datos_escalados)
    if minimo < 2 or maximo >= n or minimo > maximo:
        raise ValueError("Se requiere 2 <= minimo <= maximo < número de estaciones.")

    resultados = []
    for k in range(minimo, maximo + 1):
        modelo = entrenar_kmeans(datos_escalados, k=k)
        silueta = silhouette_score(datos_escalados, modelo.labels_)
        resultados.append({
            "k": k,
            "inercia": modelo.inertia_,
            "silueta": silueta,
        })
    return pd.DataFrame(resultados)


def generar_graficas(resultados, carpeta_salida=CARPETA_SALIDA):
    """Guarda las gráficas del codo y de la silueta."""
    carpeta_salida = Path(carpeta_salida)
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(resultados["k"], resultados["inercia"], marker="o")
    ax.set_title("Método del codo — K-means Megabús")
    ax.set_xlabel("Número de grupos (k)")
    ax.set_ylabel("Inercia")
    ax.set_xticks(resultados["k"])
    ax.grid(alpha=0.3)
    fig.tight_layout()
    ruta_codo = carpeta_salida / "grafica_codo.png"
    fig.savefig(ruta_codo, dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(resultados["k"], resultados["silueta"], marker="o")
    ax.set_title("Coeficiente de silueta — K-means Megabús")
    ax.set_xlabel("Número de grupos (k)")
    ax.set_ylabel("Silueta media")
    ax.set_xticks(resultados["k"])
    ax.grid(alpha=0.3)
    fig.tight_layout()
    ruta_silueta = carpeta_salida / "grafica_silueta.png"
    fig.savefig(ruta_silueta, dpi=160)
    plt.close(fig)
    return ruta_codo, ruta_silueta


def main():
    print("\n--- SELECCIÓN DE K: MEGABÚS ---")
    _, matriz_normalizada = preparar_datos()
    datos_escalados, _ = estandarizar_datos(matriz_normalizada)
    resultados = evaluar_valores_k(datos_escalados)

    print("\n  k       Inercia       Silueta")
    for fila in resultados.itertuples(index=False):
        print(f"  {fila.k:<3}     {fila.inercia:>8.4f}       {fila.silueta:.4f}")

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_csv = CARPETA_SALIDA / "comparacion_k.csv"
    resultados.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    ruta_codo, ruta_silueta = generar_graficas(resultados)

    mejor_silueta = resultados.loc[resultados["silueta"].idxmax()]
    print(f"\nMayor silueta: k={int(mejor_silueta['k'])} ({mejor_silueta['silueta']:.4f})")
    print("Nota: la mayor silueta no determina por sí sola el k elegido.")
    print("El plan propone k=4 por interpretación y comparación con otros métodos.")
    print(f"Resultados CSV: {ruta_csv}")
    print(f"Gráfica del codo: {ruta_codo}")
    print(f"Gráfica de silueta: {ruta_silueta}")
    print("Evaluación finalizada correctamente.")


if __name__ == "__main__":
    main()

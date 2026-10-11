# -*- coding: utf-8 -*-
"""
src/cluster/jerarquico.py  -  Rol C: agrupamiento jerárquico (Ward) y dendrograma
==============================================================================

Segundo método para confirmar los grupos de K-means (Rol B).

Cómo funciona el agrupamiento jerárquico aglomerativo:
    1. Cada estación empieza siendo su propio grupo (20 grupos).
    2. En cada paso se unen los dos grupos que, al juntarse, aumentan MENOS
       la varianza interna (criterio de Ward, el mismo objetivo que K-means).
    3. Se repite hasta que queda un solo grupo. El dendrograma dibuja esas
       uniones: la altura de cada unión es qué tan distintos eran los grupos.
    4. Cortar el árbol a cierta altura da k grupos. Aquí se corta en k = 4.

Usa los mismos datos que K-means: la matriz 20 x 36 normalizada por fila y
estandarizada con StandardScaler (kmeans_modelo.estandarizar_datos).

Uso (desde la raíz del repositorio):
    py -m src.cluster.jerarquico
Genera docs/actividad3/figuras/c1_dendrograma.png
"""

import os

import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, set_link_color_palette
from sklearn.cluster import AgglomerativeClustering

from src.cluster import estilo
from src.cluster.kmeans_modelo import estandarizar_datos
from src.cluster.preparacion import CARPETA_FIGURAS, preparar_datos

K = 4
RUTA_DENDROGRAMA = os.path.join(CARPETA_FIGURAS, "c1_dendrograma.png")


def agrupar_ward(datos_escalados, k=K):
    """Grupo de cada estación (0 a k-1) con enlace de Ward."""
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(datos_escalados)


def matriz_enlace(datos_escalados):
    """Historial de uniones que dibuja el dendrograma: una fila por cada unión."""
    return linkage(datos_escalados, method="ward")


def altura_de_corte(enlace, k=K):
    """Altura entre la unión que deja k grupos y la siguiente: cortar ahí da k grupos."""
    return (enlace[-k, 2] + enlace[-(k - 1), 2]) / 2


def graficar_dendrograma(enlace, estaciones, ruta=RUTA_DENDROGRAMA, k=K):
    corte = altura_de_corte(enlace, k)
    set_link_color_palette(estilo.COLORES_GRUPO)
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=estilo.FONDO)
    dendrogram(enlace, labels=list(estaciones), color_threshold=corte,
               above_threshold_color=estilo.TEXTO_2, leaf_rotation=60, leaf_font_size=10, ax=ax)
    ax.axhline(corte, color=estilo.TEXTO_2, linestyle="--", linewidth=1)
    ax.text(ax.get_xlim()[1], corte, f"  corte: {k} grupos", va="center", color=estilo.TEXTO_2)
    estilo.preparar_ejes(ax, "Dendrograma (enlace de Ward) de las 20 estaciones",
                         "", "Distancia entre grupos al unirse", rejilla="y")
    set_link_color_palette(None)
    return estilo.guardar(fig, ruta)


def main():
    print("\n--- AGRUPAMIENTO JERÁRQUICO (WARD) ---")
    _, matriz_normalizada = preparar_datos()
    datos_escalados, _ = estandarizar_datos(matriz_normalizada)
    estaciones = matriz_normalizada.index

    grupos = agrupar_ward(datos_escalados)
    for grupo in sorted(set(grupos)):
        miembros = [e for e, g in zip(estaciones, grupos) if g == grupo]
        print(f"\nGrupo {grupo} ({len(miembros)} estaciones): {', '.join(miembros)}")

    enlace = matriz_enlace(datos_escalados)
    ruta = graficar_dendrograma(enlace, estaciones)
    print(f"\nAltura de corte para {K} grupos: {altura_de_corte(enlace):.2f}")
    print(f"Dendrograma guardado en: {ruta}")


if __name__ == "__main__":
    main()

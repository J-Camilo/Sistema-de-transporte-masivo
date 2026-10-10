# -*- coding: utf-8 -*-
"""
src/cluster/estilo.py  -  Colores y formato comunes a todas las gráficas.

Los cuatro colores de grupo se validaron para que se distingan entre sí
también con daltonismo; además cada grupo usa una forma de marcador distinta
y su nombre escrito, para que el color nunca sea la única pista.
"""

import matplotlib
matplotlib.use("Agg")          # guarda imágenes sin abrir ventanas
import matplotlib.pyplot as plt

FONDO = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
REJILLA = "#e4e3df"

AZUL = "#2a78d6"               # abordajes / serie única
NARANJA = "#eb6834"            # descensos
COLORES_GRUPO = ["#2a78d6", "#eb6834", "#1baf7a", "#9c2f6b"]
MARCADORES_GRUPO = ["o", "s", "^", "D"]


def preparar_ejes(ax, titulo, xlabel, ylabel, rejilla="y"):
    ax.set_facecolor(FONDO)
    ax.set_title(titulo, color=TEXTO, fontsize=12, loc="left", pad=10)
    ax.set_xlabel(xlabel, color=TEXTO_2)
    ax.set_ylabel(ylabel, color=TEXTO_2)
    ax.tick_params(colors=TEXTO_2, labelsize=9)
    if rejilla:
        ax.grid(axis=rejilla, color=REJILLA, linewidth=0.8)
        ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(REJILLA)


def guardar(fig, ruta):
    import os
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fig.savefig(ruta, dpi=150, facecolor=FONDO, bbox_inches="tight")
    plt.close(fig)
    return ruta

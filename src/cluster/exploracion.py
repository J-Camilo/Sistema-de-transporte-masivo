# -*- coding: utf-8 -*-
"""
src/cluster/exploracion.py  -  Rol A: gráficas de exploración
=============================================================

Tres gráficas que se hacen ANTES de agrupar, solo con afluencia_megabus.csv:
  1. Curva promedio de abordajes y descensos por hora (todas las estaciones).
  2. Curvas de 4 estaciones distintas, una por panel.
  3. Mapa de calor estación x hora.

Uso (desde la raíz del repositorio):
    py -m src.cluster.exploracion
"""

import os

import matplotlib.pyplot as plt
import numpy as np

from src.cluster import estilo
from src.cluster.preparacion import (CARPETA_FIGURAS, HORAS, cargar_afluencia,
                                     filtrar_dias_habiles, preparar_datos)

# Estaciones elegidas para comparar: están en zonas distintas de la ciudad.
# Se eligen solo para mostrar formas diferentes; el algoritmo no recibe esta lista.
ESTACIONES_EJEMPLO = ["Cuba", "Centro", "Universidad", "Terminal"]

ETIQUETAS_HORA = [f"{h}" for h in HORAS]


def grafica_curva_promedio(df_habiles):
    prom = df_habiles.groupby("hora")[["abordajes", "descensos"]].mean()
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=estilo.FONDO)
    ax.plot(prom.index, prom["abordajes"], color=estilo.AZUL, lw=2, marker="o", ms=5)
    ax.plot(prom.index, prom["descensos"], color=estilo.NARANJA, lw=2, marker="s", ms=5)
    # Etiquetas directas al final de cada línea (en lugar de una leyenda lejana)
    ax.text(22.3, prom["abordajes"].iloc[-1], "abordajes", color=estilo.TEXTO, va="center", fontsize=9)
    ax.text(22.3, prom["descensos"].iloc[-1], "descensos", color=estilo.TEXTO, va="bottom", fontsize=9)
    estilo.preparar_ejes(ax, "Afluencia promedio por hora — 20 estaciones, días hábiles sin festivo",
                         "Hora del día", "Pasajeros por estación y hora (promedio)")
    ax.set_xticks(HORAS)
    ax.set_xlim(4.5, 23.8)
    ax.set_ylim(0, None)
    return estilo.guardar(fig, os.path.join(CARPETA_FIGURAS, "a1_curva_promedio_por_hora.png")), prom


def grafica_estaciones_ejemplo(matriz_norm):
    fig, ejes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey=True,
                             facecolor=estilo.FONDO)
    for ax, est in zip(ejes.ravel(), ESTACIONES_EJEMPLO):
        ab = matriz_norm.loc[est, [f"ab_{h:02d}" for h in HORAS]].values * 100
        de = matriz_norm.loc[est, [f"de_{h:02d}" for h in HORAS]].values * 100
        ax.plot(HORAS, ab, color=estilo.AZUL, lw=2, label="abordajes")
        ax.plot(HORAS, de, color=estilo.NARANJA, lw=2, ls="--", label="descensos")
        estilo.preparar_ejes(ax, est, "", "")
        ax.set_xticks(range(5, 23, 2))
    ejes[1, 0].set_xlabel("Hora del día", color=estilo.TEXTO_2)
    ejes[1, 1].set_xlabel("Hora del día", color=estilo.TEXTO_2)
    ejes[0, 0].set_ylabel("% del movimiento diario", color=estilo.TEXTO_2)
    ejes[1, 0].set_ylabel("% del movimiento diario", color=estilo.TEXTO_2)
    ejes[0, 0].legend(frameon=False, fontsize=9, loc="upper right")
    fig.suptitle("Cuatro estaciones, cuatro formas de curva (datos normalizados por estación)",
                 x=0.01, ha="left", color=estilo.TEXTO, fontsize=12)
    fig.tight_layout()
    return estilo.guardar(fig, os.path.join(CARPETA_FIGURAS, "a2_curvas_cuatro_estaciones.png"))


def grafica_mapa_calor(matriz_norm):
    """Dos mapas de calor (abordajes y descensos). Filas ordenadas por la hora del
    pico de abordajes, para que el patrón se vea sin usar ninguna etiqueta."""
    ab = matriz_norm[[f"ab_{h:02d}" for h in HORAS]] * 100
    de = matriz_norm[[f"de_{h:02d}" for h in HORAS]] * 100
    hora_pico = ab.values.argmax(axis=1)
    orden = ab.index[np.lexsort((ab.index, hora_pico))]
    ab, de = ab.loc[orden], de.loc[orden]
    vmax = max(ab.values.max(), de.values.max())

    fig, ejes = plt.subplots(1, 2, figsize=(12, 7), sharey=True, facecolor=estilo.FONDO)
    for ax, datos, titulo in ((ejes[0], ab, "Abordajes"), (ejes[1], de, "Descensos")):
        im = ax.imshow(datos.values, aspect="auto", cmap="Blues", vmin=0, vmax=vmax)
        ax.set_title(titulo, color=estilo.TEXTO, loc="left", fontsize=11)
        ax.set_xticks(range(len(HORAS)))
        ax.set_xticklabels(ETIQUETAS_HORA, fontsize=8, color=estilo.TEXTO_2)
        ax.set_xlabel("Hora del día", color=estilo.TEXTO_2)
        ax.set_yticks(range(len(orden)))
        ax.set_yticklabels(orden, fontsize=9, color=estilo.TEXTO)
        for lado in ax.spines.values():
            lado.set_visible(False)
    barra = fig.colorbar(im, ax=ejes, shrink=0.8, pad=0.02)
    barra.set_label("% del movimiento diario de la estación", color=estilo.TEXTO_2)
    barra.outline.set_visible(False)
    fig.suptitle("Mapa de calor estación × hora (filas ordenadas por la hora de su pico de abordajes)",
                 x=0.01, ha="left", color=estilo.TEXTO, fontsize=12)
    return estilo.guardar(fig, os.path.join(CARPETA_FIGURAS, "a3_mapa_calor_estacion_hora.png"))


def ejecutar():
    df = cargar_afluencia()
    habiles = filtrar_dias_habiles(df)
    _, matriz_norm = preparar_datos()
    r1, prom = grafica_curva_promedio(habiles)
    r2 = grafica_estaciones_ejemplo(matriz_norm)
    r3 = grafica_mapa_calor(matriz_norm)
    for r in (r1, r2, r3):
        print(f"Guardada: {os.path.relpath(r)}")
    pico_ab = prom["abordajes"].idxmax()
    pico_de = prom["descensos"].idxmax()
    print(f"Curva promedio: pico de abordajes a las {pico_ab}:00 "
          f"({prom['abordajes'].max():.1f}), pico de descensos a las {pico_de}:00 "
          f"({prom['descensos'].max():.1f}); mínimo a las "
          f"{prom['abordajes'].idxmin()}:00 ({prom['abordajes'].min():.1f} abordajes)")
    return prom


if __name__ == "__main__":
    ejecutar()

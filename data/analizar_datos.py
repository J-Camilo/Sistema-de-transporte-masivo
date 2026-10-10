# -*- coding: utf-8 -*-
"""
Análisis exploratorio de data/viajes_megabus.csv  (Rol A - Los datos)

Hace cuatro cosas:
  1. Revisa la calidad del CSV (filas, columnas, tipos, nulos, duplicados, valores).
  2. Verifica que las estaciones coincidan con la Actividad 1 (kb/estaciones.py).
  3. Comprueba que nivel_demora sea coherente con los tiempos.
  4. Genera las 3 gráficas en docs/figuras/.

Uso (desde la raíz del repositorio):
    py data/analizar_datos.py

Solo LEE el CSV: no lo modifica.
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")            # guarda imágenes sin abrir ventanas
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CSV = os.path.join(RAIZ, "data", "viajes_megabus.csv")
CARPETA_FIG = os.path.join(RAIZ, "docs", "figuras")

ORDEN_NIVEL = ["baja", "media", "alta"]
ORDEN_CLIMA = ["despejado", "nublado", "lluvia"]

# Estilo de las gráficas: un solo color, fondo claro, texto en gris oscuro
AZUL = "#2a78d6"
FONDO = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
REJILLA = "#e4e3df"


def titulo(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ----------------------------------------------------------------------------
# 1. Calidad del CSV
# ----------------------------------------------------------------------------
def revisar_calidad(df):
    titulo("1. CALIDAD DEL CSV")
    print(f"Filas: {len(df)}   Columnas: {df.shape[1]}")
    print(f"Filas completamente duplicadas: {df.duplicated().sum()}")
    print(f"id_viaje repetidos: {df['id_viaje'].duplicated().sum()}")
    sin_id = df.drop(columns="id_viaje")
    print(f"Viajes idénticos en todo excepto id_viaje: {sin_id.duplicated().sum()} "
          "(no se eliminan: dos viajes pueden coincidir legítimamente)")
    print(f"Viajes con origen igual al destino: {(df.estacion_origen == df.estacion_destino).sum()}")

    print("\nColumna             Tipo      Nulos  Distintos  Ejemplo")
    for c in df.columns:
        print(f"{c:18s}  {str(df[c].dtype):8s}  {df[c].isna().sum():5d}  {df[c].nunique():9d}  {df[c].iloc[0]}")

    print("\nVariables categóricas (valor: cantidad)")
    for c in ["ruta", "num_transbordos", "dia_semana", "es_festivo", "clima", "nivel_demora"]:
        print(f"  {c}: {df[c].value_counts().sort_index().to_dict()}")

    print("\nVariables numéricas")
    print(df[["distancia_km", "hora", "tiempo_base_min", "tiempo_real_min"]]
          .describe().round(2).to_string())

    print("\nValores inválidos")
    print(f"  distancia_km <= 0: {(df.distancia_km <= 0).sum()}")
    print(f"  hora fuera de 0-23: {(~df.hora.between(0, 23)).sum()}")
    print(f"  tiempo_base_min < 3 (mínimo del generador): {(df.tiempo_base_min < 3).sum()}")
    print(f"  tiempo_real_min <= 0: {(df.tiempo_real_min <= 0).sum()}")


# ----------------------------------------------------------------------------
# 2. Estaciones contra la Actividad 1
# ----------------------------------------------------------------------------
def revisar_estaciones(df):
    titulo("2. ESTACIONES CONTRA LA ACTIVIDAD 1 (kb/estaciones.py)")
    usadas = set(df.estacion_origen) | set(df.estacion_destino)
    print(f"Estaciones distintas en el CSV: {len(usadas)}")
    sys.path.insert(0, RAIZ)
    try:
        from kb.estaciones import ESTACIONES as KB
    except ImportError:
        print("No se encontró kb/estaciones.py en el repositorio: se omite la comparación.")
        return
    oficiales = {v["nombre"] for v in KB.values()}
    faltan = sorted(usadas - oficiales)
    no_usadas = sorted(oficiales - usadas)
    print(f"Estaciones en kb/estaciones.py: {len(oficiales)}")
    print(f"Estaciones del CSV que NO están en la Actividad 1: {faltan if faltan else 'ninguna'}")
    print(f"Estaciones de la Actividad 1 que no aparecen en el CSV: {no_usadas if no_usadas else 'ninguna'}")

    # Coordenadas: las del generador deben ser las mismas de kb/
    sys.path.insert(0, os.path.join(RAIZ, "data"))
    from generar_dataset import ESTACIONES as GEN
    por_nombre = {v["nombre"]: (v["lat"], v["lon"]) for v in KB.values()}
    distintas = [n for n, (lat, lon, _) in GEN.items() if por_nombre.get(n) != (lat, lon)]
    print(f"Coordenadas distintas entre generador y kb/: {distintas if distintas else 'ninguna'}")


# ----------------------------------------------------------------------------
# 3. Coherencia entre tiempos y nivel_demora
# ----------------------------------------------------------------------------
def nivel_por_regla(demora):
    if demora < 0.8:
        return "baja"
    if demora < 3.2:
        return "media"
    return "alta"


def revisar_coherencia(df):
    titulo("3. COHERENCIA ENTRE TIEMPOS Y nivel_demora")
    demora = df.tiempo_real_min - df.tiempo_base_min
    esperado = demora.apply(nivel_por_regla)
    coinciden = (esperado == df.nivel_demora)
    print("demora_min = tiempo_real_min - tiempo_base_min")
    print(f"Filas donde la regla del generador reproduce nivel_demora: "
          f"{coinciden.sum()} de {len(df)} ({coinciden.mean() * 100:.1f} %)")
    print(f"Filas que no coinciden: {(~coinciden).sum()} ({(~coinciden).mean() * 100:.1f} %) "
          "-> corresponden al ruido intencional (y a redondeos en el límite)")
    print("\nDemora (min) por nivel_demora:")
    print(demora.groupby(df.nivel_demora).agg(["count", "min", "mean", "max"])
          .reindex(ORDEN_NIVEL).round(2).to_string())


# ----------------------------------------------------------------------------
# 4. Gráficas
# ----------------------------------------------------------------------------
def preparar_ejes(ax, titulo_txt, xlabel, ylabel):
    ax.set_facecolor(FONDO)
    ax.set_title(titulo_txt, color=TEXTO, fontsize=13, pad=12, loc="left")
    ax.set_xlabel(xlabel, color=TEXTO_2)
    ax.set_ylabel(ylabel, color=TEXTO_2)
    ax.tick_params(colors=TEXTO_2)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(TEXTO_2)


def guardar(fig, nombre):
    os.makedirs(CARPETA_FIG, exist_ok=True)
    ruta = os.path.join(CARPETA_FIG, nombre)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, facecolor=FONDO)
    plt.close(fig)
    print(f"Guardada: docs/figuras/{nombre}")


def grafica_nivel_demora(df):
    conteo = df.nivel_demora.value_counts().reindex(ORDEN_NIVEL)
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=FONDO)
    barras = ax.bar(conteo.index, conteo.values, color=AZUL, width=0.6)
    for b, n in zip(barras, conteo.values):
        ax.text(b.get_x() + b.get_width() / 2, n, f"{n}  ({n / len(df) * 100:.1f} %)",
                ha="center", va="bottom", color=TEXTO, fontsize=10)
    preparar_ejes(ax, "Distribución de nivel_demora (4.000 viajes sintéticos)",
                  "Nivel de demora", "Cantidad de viajes")
    ax.set_ylim(0, conteo.max() * 1.15)
    guardar(fig, "01_distribucion_nivel_demora.png")
    return conteo


def grafica_viajes_por_hora(df):
    conteo = df.hora.value_counts().sort_index()          # hora es un entero (5..22)
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=FONDO)
    ax.bar(conteo.index, conteo.values, color=AZUL, width=0.75)
    for h in (conteo.idxmax(), conteo.idxmin()):           # solo se rotulan máximo y mínimo
        ax.text(h, conteo[h], str(conteo[h]), ha="center", va="bottom", color=TEXTO, fontsize=10)
    preparar_ejes(ax, "Viajes registrados por hora de salida",
                  "Hora del día (formato 24 h)", "Cantidad de viajes")
    ax.set_xticks(conteo.index)
    ax.set_xticklabels([f"{h}:00" for h in conteo.index], rotation=45)
    ax.set_ylim(0, conteo.max() * 1.15)
    guardar(fig, "02_viajes_por_hora.png")
    return conteo


def grafica_demora_por_clima(df):
    demora = df.tiempo_real_min - df.tiempo_base_min
    resumen = demora.groupby(df.clima).agg(["count", "mean"]).reindex(ORDEN_CLIMA)
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=FONDO)
    barras = ax.bar(resumen.index, resumen["mean"], color=AZUL, width=0.6)
    for b, (n, m) in zip(barras, resumen.values):
        ax.text(b.get_x() + b.get_width() / 2, m, f"{m:.2f} min\n(n = {int(n)})",
                ha="center", va="bottom", color=TEXTO, fontsize=10)
    preparar_ejes(ax, "Demora promedio por clima (tiempo real − tiempo base)",
                  "Clima", "Demora promedio (minutos)")
    ax.set_ylim(0, resumen["mean"].max() * 1.3)
    guardar(fig, "03_demora_promedio_por_clima.png")
    return resumen


def main():
    df = pd.read_csv(RUTA_CSV, encoding="utf-8")
    revisar_calidad(df)
    revisar_estaciones(df)
    revisar_coherencia(df)

    titulo("4. GRÁFICAS")
    c1 = grafica_nivel_demora(df)
    c2 = grafica_viajes_por_hora(df)
    c3 = grafica_demora_por_clima(df)
    print(f"\nnivel_demora: {c1.to_dict()}")
    print(f"Hora con más viajes: {c2.idxmax()}:00 ({c2.max()})  |  "
          f"con menos: {c2.idxmin()}:00 ({c2.min()})")
    print(f"Viajes por hora: {c2.to_dict()}")
    print("Demora promedio por clima (min):")
    print(c3.round(2).to_string())


if __name__ == "__main__":
    main()

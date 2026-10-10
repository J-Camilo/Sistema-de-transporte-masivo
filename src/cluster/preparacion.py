# -*- coding: utf-8 -*-
"""
src/cluster/preparacion.py  -  Rol A: datos y preparación
=========================================================

Convierte los 10.800 registros de data/afluencia_megabus.csv en la matriz
que usan todos los algoritmos de agrupamiento:

    10.800 registros
      -> se dejan solo los días hábiles (lunes a viernes) que NO son festivos
      -> se promedian abordajes y descensos por estación y hora
      -> matriz de 20 filas (estaciones) x 36 columnas (18 horas de abordajes + 18 de descensos)
      -> cada fila se divide por su propio total (normalización por fila)

Por qué se normaliza cada fila:
    Sin este paso el algoritmo agruparía por TAMAÑO (estaciones grandes contra
    pequeñas). Al dividir por el total, cada fila pasa a decir "qué parte del
    movimiento diario ocurre en cada hora", es decir, la FORMA de la curva.

IMPORTANTE: data/perfiles_reales.csv NO se lee en este módulo. Contiene la
respuesta (el tipo real de cada estación) y usarlo como entrada convertiría
el ejercicio en aprendizaje supervisado. Solo se usa al final, en validacion.py.

Uso rápido (desde la raíz del repositorio):
    py -m src.cluster.preparacion
"""

import os

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas del proyecto (todas relativas a la raíz del repositorio)
# ---------------------------------------------------------------------------
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_AFLUENCIA = os.path.join(RAIZ, "data", "afluencia_megabus.csv")
RUTA_PERFILES = os.path.join(RAIZ, "data", "perfiles_reales.csv")   # solo validacion.py

# Carpeta donde se guardan los resultados de la Actividad 3. Se usa una
# subcarpeta para no reemplazar docs/descripcion_datos.md de la Actividad 2.
CARPETA_SALIDA = os.path.join(RAIZ, "docs", "actividad3")
CARPETA_FIGURAS = os.path.join(CARPETA_SALIDA, "figuras")
CARPETA_RESULTADOS = os.path.join(CARPETA_SALIDA, "resultados")

COLUMNAS_ESPERADAS = ["fecha_dia", "dia_semana", "es_festivo", "clima",
                      "estacion", "hora", "abordajes", "descensos"]
DIAS_HABILES = ["lunes", "martes", "miercoles", "jueves", "viernes"]
HORAS = list(range(5, 23))            # 18 franjas: 5:00 a 22:00
N_ESTACIONES_ESPERADAS = 20


def cargar_afluencia(ruta=RUTA_AFLUENCIA):
    """Lee el CSV y comprueba que tenga las columnas y valores esperados."""
    df = pd.read_csv(ruta, encoding="utf-8")

    faltan = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if faltan:
        raise ValueError(f"Al CSV le faltan las columnas: {faltan}")
    if df[COLUMNAS_ESPERADAS].isna().any().any():
        raise ValueError("El CSV tiene valores vacíos; revisar antes de continuar.")
    if (df[["abordajes", "descensos"]] < 0).any().any():
        raise ValueError("Hay abordajes o descensos negativos.")
    if df.duplicated(["fecha_dia", "estacion", "hora"]).any():
        raise ValueError("Hay registros repetidos para la misma estación, día y hora.")
    return df


def filtrar_dias_habiles(df):
    """Deja solo lunes a viernes que no sean festivos."""
    return df[df["dia_semana"].isin(DIAS_HABILES) & (df["es_festivo"] == 0)].copy()


def construir_matriz(df_habiles):
    """
    Promedia abordajes y descensos por estación y hora, y los pone en una fila
    por estación. Columnas: ab_05 ... ab_22, de_05 ... de_22 (en ese orden).
    """
    promedio = (df_habiles
                .groupby(["estacion", "hora"])[["abordajes", "descensos"]]
                .mean())
    abordajes = promedio["abordajes"].unstack("hora").reindex(columns=HORAS)
    descensos = promedio["descensos"].unstack("hora").reindex(columns=HORAS)
    abordajes.columns = [f"ab_{h:02d}" for h in HORAS]
    descensos.columns = [f"de_{h:02d}" for h in HORAS]
    matriz = pd.concat([abordajes, descensos], axis=1).sort_index()
    matriz.index.name = "estacion"

    if matriz.isna().any().any():
        raise ValueError("Alguna estación no tiene datos en todas las horas.")
    return matriz


def normalizar_filas(matriz):
    """
    Divide cada fila por su total, de modo que cada fila sume 1.
    Si una estación tuviera total 0 (nunca pasa con estos datos) se detiene
    con un error claro en lugar de dividir por cero.
    """
    totales = matriz.sum(axis=1)
    sin_movimiento = totales[totales == 0]
    if len(sin_movimiento) > 0:
        raise ValueError(f"Estaciones sin pasajeros, no se pueden normalizar: "
                         f"{list(sin_movimiento.index)}")
    return matriz.div(totales, axis=0)


def preparar_datos(ruta=RUTA_AFLUENCIA, verbose=False):
    """
    Función principal que usan los demás módulos.
    Devuelve (matriz_promedios, matriz_normalizada), ambas de 20 x 36.
    """
    df = cargar_afluencia(ruta)
    habiles = filtrar_dias_habiles(df)
    matriz = construir_matriz(habiles)
    normalizada = normalizar_filas(matriz)

    if matriz.shape != (N_ESTACIONES_ESPERADAS, 2 * len(HORAS)):
        raise ValueError(f"Se esperaba una matriz 20 x 36 y salió {matriz.shape}.")
    if not np.allclose(normalizada.sum(axis=1), 1.0):
        raise ValueError("La normalización falló: alguna fila no suma 1.")

    if verbose:
        print(f"Registros leídos:                 {len(df):,}")
        print(f"Días hábiles sin festivo:         {habiles['fecha_dia'].nunique()} "
              f"de {df['fecha_dia'].nunique()}  ({len(habiles):,} registros)")
        print(f"Matriz de características:        {matriz.shape[0]} estaciones x "
              f"{matriz.shape[1]} columnas")
        print(f"Cada fila normalizada suma:       "
              f"{normalizada.sum(axis=1).min():.6f} a {normalizada.sum(axis=1).max():.6f}")
    return matriz, normalizada


def comparar_con_actividad_1(estaciones):
    """
    Compara los nombres de estación del CSV con kb/estaciones.py (Actividad 1).
    No cambia nada: solo informa. Devuelve (coinciden, no_coinciden) o None
    si kb/ no está en el repositorio.
    """
    import sys
    import unicodedata
    sys.path.insert(0, RAIZ)
    try:
        from kb.estaciones import ESTACIONES as KB
    except ImportError:
        return None

    def sin_tildes(t):
        t = unicodedata.normalize("NFD", t.lower())
        return "".join(c for c in t if unicodedata.category(c) != "Mn")

    oficiales = {sin_tildes(v["nombre"]): v["nombre"] for v in KB.values()}
    for v in KB.values():                     # "Intercambiador Cuba" también como "cuba"
        oficiales.setdefault(sin_tildes(v["nombre"].replace("Intercambiador ", "")), v["nombre"])
        oficiales.setdefault(sin_tildes(v["nombre"].replace("El ", "")), v["nombre"])
    coinciden, no_coinciden = {}, []
    for est in estaciones:
        if sin_tildes(est) in oficiales:
            coinciden[est] = oficiales[sin_tildes(est)]
        else:
            no_coinciden.append(est)
    return coinciden, no_coinciden


def resumen_calidad(df):
    """Imprime el diccionario básico y la calidad del CSV (para descripcion_datos.md)."""
    print(f"Filas: {len(df):,}   Columnas: {df.shape[1]}")
    print(f"Valores nulos en total: {int(df.isna().sum().sum())}")
    print(f"Filas duplicadas completas: {int(df.duplicated().sum())}")
    print(f"Registros repetidos (día, estación, hora): "
          f"{int(df.duplicated(['fecha_dia', 'estacion', 'hora']).sum())}")
    print(f"Estaciones: {df['estacion'].nunique()}   Días: {df['fecha_dia'].nunique()}   "
          f"Horas: {df['hora'].nunique()} ({df['hora'].min()} a {df['hora'].max()})")
    por_est = df.groupby("estacion").size()
    print(f"Registros por estación: mínimo {por_est.min()}, máximo {por_est.max()}")
    print("\nColumna       Tipo     Distintos  Mínimo   Máximo")
    for c in df.columns:
        es_numero = pd.api.types.is_numeric_dtype(df[c])
        mn, mx = (df[c].min(), df[c].max()) if es_numero else ("-", "-")
        print(f"{c:12s}  {str(df[c].dtype):7s}  {df[c].nunique():9d}  {str(mn):7s}  {str(mx):7s}")
    dias = df.drop_duplicates("fecha_dia")
    print(f"\nDías por tipo: {dias['dia_semana'].value_counts().to_dict()}")
    print(f"Festivos: {dias.loc[dias['es_festivo'] == 1, ['fecha_dia', 'dia_semana']].values.tolist()}")
    print(f"Clima (días): {dias['clima'].value_counts().to_dict()}")


if __name__ == "__main__":
    datos = cargar_afluencia()
    resumen_calidad(datos)
    print()
    m, mn = preparar_datos(verbose=True)
    print("\nPrimeras columnas de la matriz normalizada:")
    print(mn.iloc[:5, :6].round(4).to_string())

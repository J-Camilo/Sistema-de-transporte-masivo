# -*- coding: utf-8 -*-
"""
src/cluster/validacion.py  -  Rol C: comparación, DBSCAN, interpretación y validación
====================================================================================

Confirma que los grupos de K-means (Rol B) son reales y les pone nombre:

    1. K-means contra Ward: tabla cruzada + adjusted_rand_score (ARI).
       ARI = 1 significa que los dos métodos formaron exactamente los mismos grupos,
       aunque les hayan puesto otro número.
    2. DBSCAN variando eps: tercer método, que además marca estaciones atípicas
       (las que no tienen vecinos cerca).
    3. Interpretación: la curva promedio de cada grupo decide su nombre
       (residencial, laboral, mixta o intercambio).
    4. Recién al final, comparación contra data/perfiles_reales.csv.
       Ese archivo NO se usa en ningún paso anterior: el agrupamiento no ve etiquetas.

Uso (desde la raíz del repositorio, después de py -m src.cluster.kmeans_modelo):
    py -m src.cluster.validacion
Genera en docs/actividad3/:
    figuras/c2_curvas_por_grupo.png, figuras/c3_dbscan_eps.png
    resultados/comparacion_kmeans_ward.csv, resultados/dbscan_eps.csv,
    resultados/ari_por_k.csv, resultados/validacion_perfiles.csv
    grupos_interpretados.csv
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import adjusted_rand_score

from src.cluster import estilo
from src.cluster.jerarquico import agrupar_ward
from src.cluster.kmeans_modelo import entrenar_kmeans
from src.cluster.preparacion import (CARPETA_FIGURAS, CARPETA_RESULTADOS, CARPETA_SALIDA, HORAS,
                                     RUTA_PERFILES)
from src.cluster.visualizacion import cargar_modelo_y_datos

VALORES_EPS = [round(e, 2) for e in np.arange(3.0, 6.01, 0.25)]
MIN_VECINOS = 2              # con 20 estaciones, 2 basta para formar un grupo
EPS_ATIPICAS = 4.0           # el plan pide revisar qué estación queda sola con eps = 4,0
MANANA, MEDIODIA, TARDE = (6, 8), (11, 13), (17, 19)
ORDEN_NOMBRES = ["residencial", "laboral", "mixta", "intercambio"]


# ---------------------------------------------------------------------------
# 1. Comparar dos agrupamientos
# ---------------------------------------------------------------------------
def comparar_particiones(grupos_a, grupos_b, nombre_a="a", nombre_b="b"):
    """ARI y tabla cruzada. El ARI no depende de qué número le tocó a cada grupo."""
    a = pd.Series(list(grupos_a), name=nombre_a)
    b = pd.Series(list(grupos_b), name=nombre_b)
    return {"ari": adjusted_rand_score(a, b), "tabla": pd.crosstab(a, b)}


# ---------------------------------------------------------------------------
# 2. DBSCAN
# ---------------------------------------------------------------------------
def barrido_dbscan(datos, valores_eps=VALORES_EPS, min_vecinos=MIN_VECINOS):
    """
    Para cada eps: cuántos grupos forma DBSCAN y qué estaciones quedan como atípicas.
    eps es el radio del vecindario: dos estaciones a menos de eps son vecinas.
    """
    datos = pd.DataFrame(datos)
    filas = []
    for eps in valores_eps:
        etiquetas = DBSCAN(eps=eps, min_samples=min_vecinos).fit_predict(datos.to_numpy())
        atipicas = list(datos.index[etiquetas == -1])
        filas.append({"eps": eps, "grupos": len(set(etiquetas) - {-1}),
                      "atipicas": len(atipicas), "estaciones_atipicas": ", ".join(map(str, atipicas))})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 3. Interpretar y bautizar los grupos
# ---------------------------------------------------------------------------
def _suma_franja(curva, prefijo, franja):
    return sum(curva[f"{prefijo}_{h:02d}"] for h in range(franja[0], franja[1] + 1))


def describir_grupos(matriz_normalizada, grupos):
    """
    Resume la curva promedio de cada grupo:
        sube_manana / baja_manana   parte del movimiento diario entre 6:00 y 8:59
        sube_tarde  / baja_tarde    lo mismo entre 17:00 y 19:59
        mediodia                    abordajes + descensos entre 11:00 y 13:59
        variacion                   qué tan desigual es el movimiento hora a hora
                                    (coeficiente de variación: 0 = perfectamente parejo)
    """
    grupos = pd.Series(list(grupos), index=matriz_normalizada.index)
    filas = {}
    for grupo, miembros in grupos.groupby(grupos):
        curva = matriz_normalizada.loc[miembros.index].mean()
        por_hora = np.array([curva[f"ab_{h:02d}"] + curva[f"de_{h:02d}"] for h in HORAS])
        filas[grupo] = {
            "estaciones": len(miembros),
            "sube_manana": _suma_franja(curva, "ab", MANANA),
            "baja_manana": _suma_franja(curva, "de", MANANA),
            "sube_tarde": _suma_franja(curva, "ab", TARDE),
            "baja_tarde": _suma_franja(curva, "de", TARDE),
            "mediodia": _suma_franja(curva, "ab", MEDIODIA) + _suma_franja(curva, "de", MEDIODIA),
            "variacion": por_hora.std() / por_hora.mean(),
        }
    return pd.DataFrame(filas).T


def nombrar_grupos(matriz_normalizada, grupos):
    """
    Regla para ponerle nombre a cada grupo, mirando solo su curva:
        residencial  el que más SUBE de lo que BAJA en la mañana (la gente sale de su casa)
        laboral      el contrario: el que más BAJA de lo que SUBE en la mañana (llega al trabajo)
        intercambio  de los que quedan, el de movimiento más parejo durante el día
        mixta        el resto: flujo en ambos sentidos con repunte al mediodía
    """
    resumen = describir_grupos(matriz_normalizada, grupos)
    salida_manana = resumen["sube_manana"] - resumen["baja_manana"]
    nombres = {salida_manana.idxmax(): "residencial", salida_manana.idxmin(): "laboral"}
    restantes = resumen.drop(index=list(nombres))
    if len(restantes):
        nombres[restantes["variacion"].idxmin()] = "intercambio"
    for grupo in restantes.index:
        nombres.setdefault(grupo, "mixta")
    return {int(g) if isinstance(g, (np.integer, int)) else g: n for g, n in nombres.items()}


# ---------------------------------------------------------------------------
# 4. Validación final contra los tipos reales
# ---------------------------------------------------------------------------
def cargar_perfiles_reales(ruta=RUTA_PERFILES):
    """Tipo real de cada estación. SOLO se usa aquí, al final."""
    return pd.read_csv(ruta, encoding="utf-8-sig").set_index("estacion")


def validar_contra_reales(nombres_por_estacion, tipos_reales):
    nombres = pd.Series(nombres_por_estacion)
    reales = pd.Series(tipos_reales).reindex(nombres.index)
    errores = [(e, p, r) for e, p, r in zip(nombres.index, nombres, reales) if p != r]
    return {
        "aciertos": int((nombres == reales).sum()),
        "total": len(nombres),
        "ari": adjusted_rand_score(reales, nombres),
        "errores": errores,
        "tabla": pd.crosstab(reales.rename("tipo real"), nombres.rename("nombre del grupo")),
    }


def ari_por_k(datos_escalados, tipos_reales, valores_k=range(2, 9)):
    """La trampa de la silueta: ¿con qué k los grupos coinciden con los tipos reales?"""
    return pd.DataFrame([{"k": k, "ari_tipos_reales":
                          adjusted_rand_score(tipos_reales, entrenar_kmeans(datos_escalados, k).labels_)}
                         for k in valores_k])


# ---------------------------------------------------------------------------
# Gráficas
# ---------------------------------------------------------------------------
def graficar_curvas_por_grupo(matriz_normalizada, grupos, nombres, ruta):
    grupos = pd.Series(list(grupos), index=matriz_normalizada.index)
    orden = sorted(nombres, key=lambda g: ORDEN_NOMBRES.index(nombres[g]))
    fig, ejes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True, facecolor=estilo.FONDO)
    for ax, grupo in zip(ejes.flat, orden):
        miembros = grupos[grupos == grupo].index
        curva = matriz_normalizada.loc[miembros].mean()
        ax.plot(HORAS, [curva[f"ab_{h:02d}"] * 100 for h in HORAS], color=estilo.AZUL,
                marker="o", markersize=3, label="Suben (abordajes)")
        ax.plot(HORAS, [curva[f"de_{h:02d}"] * 100 for h in HORAS], color=estilo.NARANJA,
                marker="s", markersize=3, label="Bajan (descensos)")
        titulo = f"{nombres[grupo].capitalize()} ({len(miembros)} estaciones)"
        estilo.preparar_ejes(ax, titulo, "Hora del día", "% del movimiento diario")
        ax.set_xticks(range(5, 23, 2))
        ax.text(0.01, 0.97, "\n".join(miembros), transform=ax.transAxes, va="top",
                fontsize=8, color=estilo.TEXTO_2)
    ejes.flat[0].legend(loc="upper right", fontsize=8, frameon=False)
    fig.suptitle("Curva promedio de cada grupo de K-means", x=0.01, ha="left", color=estilo.TEXTO)
    fig.tight_layout()
    return estilo.guardar(fig, ruta)


def graficar_dbscan(tabla, ruta):
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor=estilo.FONDO)
    ax.plot(tabla["eps"], tabla["grupos"], color=estilo.AZUL, marker="o", label="Grupos encontrados")
    ax.plot(tabla["eps"], tabla["atipicas"], color=estilo.NARANJA, marker="s", label="Estaciones atípicas")
    ax.axhline(4, color=estilo.REJILLA, linestyle="--")
    estilo.preparar_ejes(ax, "DBSCAN: grupos y estaciones atípicas según eps", "eps (radio del vecindario)",
                         "Cantidad")
    ax.legend(frameon=False)
    return estilo.guardar(fig, ruta)


def _guardar_csv(tabla, nombre, index=False):
    ruta = os.path.join(CARPETA_RESULTADOS, nombre)
    os.makedirs(CARPETA_RESULTADOS, exist_ok=True)
    tabla.to_csv(ruta, index=index, encoding="utf-8-sig")
    return ruta


def main():
    from src.cluster.preparacion import preparar_datos

    print("\n--- VALIDACIÓN E INTERPRETACIÓN (ROL C) ---")
    estaciones, datos_escalados, grupos_kmeans = cargar_modelo_y_datos()
    _, matriz_normalizada = preparar_datos()

    # 1. K-means contra Ward
    grupos_ward = agrupar_ward(datos_escalados)
    comparacion = comparar_particiones(grupos_kmeans, grupos_ward, "kmeans", "ward")
    _guardar_csv(comparacion["tabla"], "comparacion_kmeans_ward.csv", index=True)
    print("\n1. K-means contra Ward (tabla cruzada):")
    print(comparacion["tabla"].to_string())
    print(f"   ARI = {comparacion['ari']:.3f}")

    # 2. DBSCAN
    escalados = pd.DataFrame(datos_escalados, index=estaciones)
    dbscan = barrido_dbscan(escalados)
    _guardar_csv(dbscan, "dbscan_eps.csv")
    graficar_dbscan(dbscan, os.path.join(CARPETA_FIGURAS, "c3_dbscan_eps.png"))
    print(f"\n2. DBSCAN (min_samples = {MIN_VECINOS}):")
    print(dbscan.to_string(index=False))

    # 3. Interpretación (todavía sin mirar perfiles_reales.csv)
    nombres = nombrar_grupos(matriz_normalizada, grupos_kmeans)
    resumen = describir_grupos(matriz_normalizada, grupos_kmeans)
    resumen.insert(0, "nombre", [nombres[g] for g in resumen.index])
    print("\n3. Curva promedio de cada grupo y nombre asignado:")
    print(resumen.round(3).to_string())
    graficar_curvas_por_grupo(matriz_normalizada, grupos_kmeans, nombres,
                              os.path.join(CARPETA_FIGURAS, "c2_curvas_por_grupo.png"))
    interpretados = pd.DataFrame({"estacion": estaciones, "grupo_kmeans": grupos_kmeans,
                                  "grupo_ward": grupos_ward,
                                  "nombre": [nombres[g] for g in grupos_kmeans]})
    interpretados.to_csv(os.path.join(CARPETA_SALIDA, "grupos_interpretados.csv"),
                         index=False, encoding="utf-8-sig")

    # 4. Recién ahora: los tipos reales
    reales = cargar_perfiles_reales()["arquetipo_real"]
    validacion = validar_contra_reales(interpretados.set_index("estacion")["nombre"], reales)
    _guardar_csv(validacion["tabla"], "validacion_perfiles.csv", index=True)
    por_k = ari_por_k(datos_escalados, reales.reindex(estaciones))
    _guardar_csv(por_k, "ari_por_k.csv")
    print("\n4. Validación contra data/perfiles_reales.csv:")
    print(validacion["tabla"].to_string())
    print(f"   Aciertos: {validacion['aciertos']} de {validacion['total']} | ARI = {validacion['ari']:.3f}")
    for estacion, nombre, real in validacion["errores"]:
        print(f"   - {estacion}: el grupo dice {nombre}, el tipo real es {real}")
    print("\n   ARI contra los tipos reales según k:")
    print(por_k.round(3).to_string(index=False))
    print("\nValidación completada correctamente.")


if __name__ == "__main__":
    main()

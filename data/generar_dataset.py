# -*- coding: utf-8 -*-
"""
Generador del dataset de viajes del sistema Megabus (Pereira - Dosquebradas).

No existe una fuente de datos publica con tiempos de viaje por trayecto para el
sistema Megabus, por lo que se construye una muestra sintetica a partir del grafo
de estaciones utilizado en la actividad anterior. La etiqueta nivel_demora se
genera mediante reglas latentes mas un porcentaje de ruido, de modo que el modelo
de aprendizaje supervisado deba inferirlas y no se limite a reproducir una formula
deterministica.

Uso:
    python generar_dataset.py [--filas 4000] [--semilla 42] [--salida viajes_megabus.csv]
"""

import argparse
import csv
import math
import random

# --------------------------------------------------------------------------
# Grafo de estaciones. Sustituir por el modulo kb/estaciones.py del repositorio
# si los nombres o coordenadas difieren.
# troncal: 1 = Av. 30 de Agosto (Cuba-Centro)
#          2 = Av. Simon Bolivar (Centro-Dosquebradas)
#          0 = estacion de intercambio entre ambas troncales
# --------------------------------------------------------------------------
ESTACIONES = {
    "Cuba":              {"lat": 4.7920, "lon": -75.7215, "troncal": 1},
    "Perla del Otun":    {"lat": 4.7965, "lon": -75.7168, "troncal": 1},
    "Travesuras":        {"lat": 4.8003, "lon": -75.7129, "troncal": 1},
    "Insuperables":      {"lat": 4.8041, "lon": -75.7091, "troncal": 1},
    "Corales":           {"lat": 4.8078, "lon": -75.7054, "troncal": 1},
    "San Fernando":      {"lat": 4.8112, "lon": -75.7018, "troncal": 1},
    "Universidad":       {"lat": 4.8146, "lon": -75.6982, "troncal": 1},
    "Parque Olaya":      {"lat": 4.8158, "lon": -75.6948, "troncal": 1},
    "Jardin":            {"lat": 4.8142, "lon": -75.6921, "troncal": 1},
    "Egoya":             {"lat": 4.8131, "lon": -75.6903, "troncal": 0},
    "Centro":            {"lat": 4.8143, "lon": -75.6946, "troncal": 0},
    "Victoria":          {"lat": 4.8167, "lon": -75.6948, "troncal": 2},
    "Viaducto":          {"lat": 4.8215, "lon": -75.6921, "troncal": 2},
    "Postobon":          {"lat": 4.8263, "lon": -75.6890, "troncal": 2},
    "La Macarena":       {"lat": 4.8301, "lon": -75.6862, "troncal": 2},
    "Dosquebradas":      {"lat": 4.8338, "lon": -75.6835, "troncal": 2},
    "La Romelia":        {"lat": 4.8392, "lon": -75.6798, "troncal": 2},
    "Los Molinos":       {"lat": 4.8427, "lon": -75.6771, "troncal": 2},
    "Guadalupe":         {"lat": 4.8461, "lon": -75.6744, "troncal": 2},
    "Terminal":          {"lat": 4.8055, "lon": -75.6938, "troncal": 0},
}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
CLIMAS = ["despejado", "nublado", "lluvia"]
PESOS_CLIMA = [0.58, 0.27, 0.15]

VELOCIDAD_KMH = 21.0        # velocidad comercial promedio del sistema
PENALIZACION_TRANSBORDO = 5  # minutos


def haversine(a, b):
    """Distancia en kilometros entre dos estaciones."""
    r = 6371.0
    la1, lo1 = math.radians(a["lat"]), math.radians(a["lon"])
    la2, lo2 = math.radians(b["lat"]), math.radians(b["lon"])
    dla, dlo = la2 - la1, lo2 - lo1
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def ruta_de(origen, destino):
    """Ruta asignada y numero de transbordos segun las troncales implicadas."""
    t_o = ESTACIONES[origen]["troncal"]
    t_d = ESTACIONES[destino]["troncal"]
    if t_o == 0 and t_d == 0:
        return "Ruta 1", 0
    if t_o in (1, 0) and t_d in (1, 0):
        return "Ruta 1", 0
    if t_o in (2, 0) and t_d in (2, 0):
        return "Ruta 2", 0
    # Cambio de troncal: la ruta 3 es directa, en caso contrario hay transbordo
    if random.random() < 0.35:
        return "Ruta 3", 0
    return random.choice(["Ruta 1", "Ruta 2"]), 1


def factor_hora(hora):
    """Factor de congestion segun la franja horaria."""
    if 6 <= hora <= 8:
        return 1.45          # pico de la manana
    if 17 <= hora <= 19:
        return 1.40          # pico de la tarde
    if 11 <= hora <= 13:
        return 1.15          # franja intermedia
    if hora <= 6 or hora >= 21:
        return 0.90          # servicio nocturno o madrugada
    return 1.00


def factor_dia(dia, festivo):
    if festivo:
        return 0.82
    if dia == "domingo":
        return 0.78
    if dia == "sabado":
        return 0.90
    return 1.00


def factor_clima(clima):
    return {"despejado": 1.00, "nublado": 1.04, "lluvia": 1.22}[clima]


def etiquetar(minutos_base, factor_total):
    """
    Regla latente que el arbol de decision debe descubrir.
    Se compara el tiempo estimado contra el tiempo base del trayecto.
    """
    exceso = (minutos_base * factor_total) - minutos_base
    if exceso < 0.8:
        return "baja"
    if exceso < 3.2:
        return "media"
    return "alta"


def generar(filas, semilla):
    random.seed(semilla)
    nombres = list(ESTACIONES.keys())
    registros = []
    ruido_aplicado = 0
    niveles = ["baja", "media", "alta"]

    for i in range(filas):
        origen = random.choice(nombres)
        destino = random.choice([n for n in nombres if n != origen])

        dist = haversine(ESTACIONES[origen], ESTACIONES[destino])
        ruta, transbordos = ruta_de(origen, destino)

        hora = random.choices(
            population=list(range(5, 23)),
            weights=[1, 4, 9, 10, 7, 5, 5, 6, 7, 6, 5, 6, 8, 10, 9, 6, 3, 2],
            k=1)[0]
        dia = random.choice(DIAS)
        festivo = 1 if random.random() < 0.07 else 0
        clima = random.choices(CLIMAS, weights=PESOS_CLIMA, k=1)[0]

        minutos_base = (dist / VELOCIDAD_KMH) * 60 + transbordos * PENALIZACION_TRANSBORDO
        minutos_base = max(minutos_base, 3.0)

        factor = factor_hora(hora) * factor_dia(dia, festivo) * factor_clima(clima)
        minutos_reales = minutos_base * factor
        nivel = etiquetar(minutos_base, factor)

        # Ruido del 12 %: refleja incidentes no modelados (averias, desvios, eventos)
        if random.random() < 0.12:
            nivel = random.choice([n for n in niveles if n != nivel])
            ruido_aplicado += 1

        registros.append({
            "id_viaje": i + 1,
            "estacion_origen": origen,
            "estacion_destino": destino,
            "ruta": ruta,
            "num_transbordos": transbordos,
            "distancia_km": round(dist, 3),
            "hora": hora,
            "dia_semana": dia,
            "es_festivo": festivo,
            "clima": clima,
            "tiempo_base_min": round(minutos_base, 2),
            "tiempo_real_min": round(minutos_reales, 2),
            "nivel_demora": nivel,
        })

    return registros, ruido_aplicado


def main():
    ap = argparse.ArgumentParser(description="Genera el dataset de viajes del Megabus.")
    ap.add_argument("--filas", type=int, default=4000)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--salida", default="viajes_megabus.csv")
    args = ap.parse_args()

    registros, ruido = generar(args.filas, args.semilla)
    campos = list(registros[0].keys())

    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(registros)

    conteo = {}
    for r in registros:
        conteo[r["nivel_demora"]] = conteo.get(r["nivel_demora"], 0) + 1

    print(f"Archivo generado: {args.salida}")
    print(f"Registros: {len(registros)}  |  Columnas: {len(campos)}")
    print(f"Ruido aplicado: {ruido} registros ({ruido / len(registros) * 100:.1f} %)")
    print("Distribucion de la clase objetivo:")
    for k in ("baja", "media", "alta"):
        n = conteo.get(k, 0)
        print(f"  {k:6s} {n:5d}  ({n / len(registros) * 100:5.1f} %)")


if __name__ == "__main__":
    main()

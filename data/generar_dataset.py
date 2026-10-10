# -*- coding: utf-8 -*-
"""
Generador del dataset de viajes del sistema Megabús (Pereira - Dosquebradas).

No existe una fuente de datos pública con tiempos de viaje por trayecto para el
sistema Megabús, por lo que se construye una muestra SINTÉTICA a partir del grafo
de estaciones de la Actividad 1 (kb/estaciones.py y kb/conexiones.py). La etiqueta
nivel_demora se genera mediante reglas latentes más un porcentaje de ruido, de modo
que el modelo de aprendizaje supervisado deba inferirlas y no se limite a reproducir
una fórmula determinística.

Versión 2 (Rol A, revisión de datos):
  - Las 20 estaciones de la versión 1 se reemplazaron por las 37 estaciones de la
    Actividad 1 (13 nombres de la v1 no existían en la base de conocimiento).
  - La ruta y los transbordos se asignan según las rutas R1, R2 y R3 de la
    Actividad 1 (en la v1 la "Ruta 3" llegaba a Dosquebradas, lo que no ocurre).
  - La regla que define nivel_demora NO se modificó.
  - El CSV se guarda por defecto en la carpeta data/ y no se sobrescribe
    sin la opción --sobrescribir.

Uso (desde la raíz del repositorio):
    py data/generar_dataset.py                       # crea data/viajes_megabus.csv si no existe
    py data/generar_dataset.py --sobrescribir        # lo regenera (mismo resultado con la misma semilla)
    py data/generar_dataset.py --salida data/prueba.csv   # genera una copia sin tocar el oficial
"""

import argparse
import csv
import math
import os
import random

# --------------------------------------------------------------------------
# Estaciones de la Actividad 1 (copia de kb/estaciones.py y de las rutas de
# kb/conexiones.py). Se copian aquí para que el generador funcione solo; el
# script data/analizar_datos.py verifica que coincidan con kb/ si está presente.
#   nombre : (latitud, longitud, rutas que pasan por la estación)
# --------------------------------------------------------------------------
TODAS = ("R1", "R2", "R3")
ESTACIONES = {
    # Occidente (las tres rutas, salvo El Viajero)
    "Intercambiador Cuba":         (4.7960, -75.7380, TODAS),
    "San Fernando":                (4.8015, -75.7440, TODAS),
    "El Viajero":                  (4.8050, -75.7390, ("R1", "R3")),
    "Aeropuerto":                  (4.8090, -75.7320, TODAS),
    "Batallón":                    (4.8065, -75.7220, TODAS),
    "Maraya":                      (4.8045, -75.7120, TODAS),
    # Avenida 30 de Agosto (solo Ruta 1)
    "El Jardín":                   (4.8085, -75.7110, ("R1",)),
    "Ucumarí":                     (4.8100, -75.7100, ("R1",)),
    "Consota":                     (4.8120, -75.7085, ("R1",)),
    "El Cafetero":                 (4.8130, -75.7070, ("R1",)),
    "Francisco Pereira":           (4.8150, -75.7045, ("R1",)),
    "Parque Olaya":                (4.8175, -75.7010, ("R1",)),
    "Condina":                     (4.8200, -75.6970, ("R1",)),
    # Centro (Rutas 2 y 3; Libertad solo Ruta 3)
    "Turín":                       (4.8055, -75.7085, ("R2", "R3")),
    "Egoyá":                       (4.8065, -75.7070, ("R2", "R3")),
    "Coliseo":                     (4.8075, -75.7055, ("R2", "R3")),
    "Ormaza":                      (4.8088, -75.7030, ("R2", "R3")),
    "Mercados":                    (4.8100, -75.7010, ("R2", "R3")),
    "El Lago":                     (4.8112, -75.6990, ("R2", "R3")),
    "Otún":                        (4.8128, -75.6975, ("R2", "R3")),
    "Victoria":                    (4.8140, -75.6960, ("R2", "R3")),
    "Del Café":                    (4.8155, -75.6940, ("R2", "R3")),
    "Libertad":                    (4.8165, -75.6930, ("R3",)),
    "Viaducto":                    (4.8175, -75.6915, ("R2", "R3")),
    "Central":                     (4.8150, -75.6950, ("R2", "R3")),
    "Claret":                      (4.8130, -75.6975, ("R2", "R3")),
    "Cañarte":                     (4.8115, -75.6995, ("R2", "R3")),
    "Las Flores":                  (4.8100, -75.7015, ("R2", "R3")),
    "Banderas":                    (4.8085, -75.7040, ("R2", "R3")),
    "Palacio de Justicia":         (4.8072, -75.7060, ("R2", "R3")),
    "La Ruana":                    (4.8062, -75.7080, ("R2", "R3")),
    # Dosquebradas (Rutas 1 y 2)
    "La Popa":                     (4.8230, -75.6880, ("R1", "R2")),
    "Santa Mónica":                (4.8270, -75.6860, ("R1", "R2")),
    "Milán":                       (4.8310, -75.6840, ("R1", "R2")),
    "Fundadores":                  (4.8345, -75.6820, ("R1", "R2")),
    "CAM":                         (4.8380, -75.6800, ("R1", "R2")),
    "Intercambiador Dosquebradas": (4.8420, -75.6780, ("R1", "R2")),
}

NOMBRE_RUTA = {"R1": "Ruta 1", "R2": "Ruta 2", "R3": "Ruta 3"}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
CLIMAS = ["despejado", "nublado", "lluvia"]
PESOS_CLIMA = [0.58, 0.27, 0.15]

VELOCIDAD_KMH = 21.0         # velocidad comercial promedio supuesta
PENALIZACION_TRANSBORDO = 5  # minutos (mismo valor que la regla de la Actividad 1)
PROB_RUIDO = 0.12            # probabilidad de cambiar la etiqueta (ruido)

CARPETA_DATA = os.path.dirname(os.path.abspath(__file__))
SALIDA_POR_DEFECTO = os.path.join(CARPETA_DATA, "viajes_megabus.csv")


def haversine(origen, destino):
    """Distancia en línea recta, en kilómetros, entre dos estaciones."""
    lat1, lon1, _ = ESTACIONES[origen]
    lat2, lon2, _ = ESTACIONES[destino]
    r = 6371.0
    la1, la2 = math.radians(lat1), math.radians(lat2)
    dla, dlo = la2 - la1, math.radians(lon2 - lon1)
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def ruta_de(origen, destino):
    """
    Ruta asignada y número de transbordos según las rutas de la Actividad 1.
      - Si alguna ruta pasa por las dos estaciones: viaje directo (0 transbordos),
        se escoge al azar una de esas rutas comunes.
      - Si no hay ruta común: se sale por una ruta del origen y se hace 1 transbordo.
        (En el grafo de la Actividad 1 todas las rutas comparten el occidente,
        así que nunca se necesitan 2 transbordos.)
    Las listas se ordenan para que el resultado sea reproducible.
    """
    rutas_o = set(ESTACIONES[origen][2])
    rutas_d = set(ESTACIONES[destino][2])
    comunes = sorted(rutas_o & rutas_d)
    if comunes:
        return NOMBRE_RUTA[random.choice(comunes)], 0
    return NOMBRE_RUTA[random.choice(sorted(rutas_o))], 1


def factor_hora(hora):
    """Factor de congestión según la franja horaria."""
    if 6 <= hora <= 8:
        return 1.45          # pico de la mañana
    if 17 <= hora <= 19:
        return 1.40          # pico de la tarde
    if 11 <= hora <= 13:
        return 1.15          # franja intermedia (mediodía)
    if hora <= 6 or hora >= 21:
        return 0.90          # madrugada (5 h) o noche (21-22 h)
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
    Regla latente que el árbol de decisión debe descubrir (sin cambios desde la v1).
    exceso = minutos de más respecto al tiempo base = tiempo_real - tiempo_base.
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

        dist = haversine(origen, destino)
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

        # Ruido: con probabilidad 12 % la etiqueta se cambia por otra al azar.
        # Simula incidentes no modelados (averías, desvíos, eventos).
        if random.random() < PROB_RUIDO:
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
    ap = argparse.ArgumentParser(description="Genera el dataset sintético de viajes del Megabús.")
    ap.add_argument("--filas", type=int, default=4000)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--salida", default=SALIDA_POR_DEFECTO)
    ap.add_argument("--sobrescribir", action="store_true",
                    help="Permite reemplazar el archivo de salida si ya existe.")
    args = ap.parse_args()

    if os.path.exists(args.salida) and not args.sobrescribir:
        print(f"El archivo {args.salida} ya existe y NO se modificó.")
        print("Use --sobrescribir para regenerarlo o --salida otro_archivo.csv para una copia.")
        return

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
    print(f"Registros: {len(registros)}  |  Columnas: {len(campos)}  |  Semilla: {args.semilla}")
    print(f"Ruido aplicado: {ruido} registros ({ruido / len(registros) * 100:.1f} %)")
    print("Distribución de la clase objetivo:")
    for k in ("baja", "media", "alta"):
        n = conteo.get(k, 0)
        print(f"  {k:6s} {n:5d}  ({n / len(registros) * 100:5.1f} %)")


if __name__ == "__main__":
    main()

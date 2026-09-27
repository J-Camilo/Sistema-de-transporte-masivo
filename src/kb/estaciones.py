"""
kb/estaciones.py  -  Base de conocimiento: ESTACIONES (hechos del mundo)
=========================================================================
Integrante 1  |  Base teórica: Capítulos 2 y 3

Cada estación es un HECHO de la base de conocimiento. Se guarda con:
    - nombre  : nombre oficial de la estación
    - lat/lon : coordenadas (grados decimales). Las usa el Integrante 3
                para la heurística h(n) de A* (distancia en línea recta).
    - tipo    : "intercambiador" (terminal de transbordo) o "estacion"
    - zona    : sector de la ciudad. Lo usan las reglas (ej. congestión
                en el centro en hora pico).

Fuente de nombres y orden: megabus.gov.co y Moovit (troncales 1, 2 y 3).
IMPORTANTE: las coordenadas son APROXIMADAS. Antes de entregar, verificar
cada una en Google Maps (clic derecho sobre la estación -> copiar coordenadas).
"""

import math
import unicodedata

ESTACIONES = {
    # ---------------- Occidente (Cuba - Maraya) ----------------
    "cuba":              {"nombre": "Intercambiador Cuba",         "lat": 4.7960, "lon": -75.7380, "tipo": "intercambiador", "zona": "occidente"},
    "san_fernando":      {"nombre": "San Fernando",                "lat": 4.8015, "lon": -75.7440, "tipo": "estacion",       "zona": "occidente"},
    "el_viajero":        {"nombre": "El Viajero",                  "lat": 4.8050, "lon": -75.7390, "tipo": "estacion",       "zona": "occidente"},
    "aeropuerto":        {"nombre": "Aeropuerto",                  "lat": 4.8090, "lon": -75.7320, "tipo": "estacion",       "zona": "occidente"},
    "batallon":          {"nombre": "Batallón",                    "lat": 4.8065, "lon": -75.7220, "tipo": "estacion",       "zona": "occidente"},
    "maraya":            {"nombre": "Maraya",                      "lat": 4.8045, "lon": -75.7120, "tipo": "estacion",       "zona": "occidente"},

    # ---------------- Avenida 30 de Agosto (Ruta 1) ----------------
    "el_jardin":         {"nombre": "El Jardín",                   "lat": 4.8085, "lon": -75.7110, "tipo": "estacion",       "zona": "av30"},
    "ucumari":           {"nombre": "Ucumarí",                     "lat": 4.8100, "lon": -75.7100, "tipo": "estacion",       "zona": "av30"},
    "consota":           {"nombre": "Consota",                     "lat": 4.8120, "lon": -75.7085, "tipo": "estacion",       "zona": "av30"},
    "el_cafetero":       {"nombre": "El Cafetero",                 "lat": 4.8130, "lon": -75.7070, "tipo": "estacion",       "zona": "av30"},
    "francisco_pereira": {"nombre": "Francisco Pereira",           "lat": 4.8150, "lon": -75.7045, "tipo": "estacion",       "zona": "av30"},
    "parque_olaya":      {"nombre": "Parque Olaya",                "lat": 4.8175, "lon": -75.7010, "tipo": "estacion",       "zona": "av30"},
    "condina":           {"nombre": "Condina",                     "lat": 4.8200, "lon": -75.6970, "tipo": "estacion",       "zona": "av30"},

    # ---------------- Centro por carreras 8 y 10 (sentido hacia el centro) ----------------
    "turin":             {"nombre": "Turín",                       "lat": 4.8055, "lon": -75.7085, "tipo": "estacion",       "zona": "centro"},
    "egoya":             {"nombre": "Egoyá",                       "lat": 4.8065, "lon": -75.7070, "tipo": "estacion",       "zona": "centro"},
    "coliseo":           {"nombre": "Coliseo",                     "lat": 4.8075, "lon": -75.7055, "tipo": "estacion",       "zona": "centro"},
    "ormaza":            {"nombre": "Ormaza",                      "lat": 4.8088, "lon": -75.7030, "tipo": "estacion",       "zona": "centro"},
    "mercados":          {"nombre": "Mercados",                    "lat": 4.8100, "lon": -75.7010, "tipo": "estacion",       "zona": "centro"},
    "el_lago":           {"nombre": "El Lago",                     "lat": 4.8112, "lon": -75.6990, "tipo": "estacion",       "zona": "centro"},
    "otun":              {"nombre": "Otún",                        "lat": 4.8128, "lon": -75.6975, "tipo": "estacion",       "zona": "centro"},
    "victoria":          {"nombre": "Victoria",                    "lat": 4.8140, "lon": -75.6960, "tipo": "estacion",       "zona": "centro"},
    "del_cafe":          {"nombre": "Del Café",                    "lat": 4.8155, "lon": -75.6940, "tipo": "estacion",       "zona": "centro"},
    "libertad":          {"nombre": "Libertad",                    "lat": 4.8165, "lon": -75.6930, "tipo": "estacion",       "zona": "centro"},

    # ---------------- Centro por carreras 6 y 7 (sentido de regreso) ----------------
    "viaducto":          {"nombre": "Viaducto",                    "lat": 4.8175, "lon": -75.6915, "tipo": "estacion",       "zona": "centro"},
    "central":           {"nombre": "Central",                     "lat": 4.8150, "lon": -75.6950, "tipo": "estacion",       "zona": "centro"},
    "claret":            {"nombre": "Claret",                      "lat": 4.8130, "lon": -75.6975, "tipo": "estacion",       "zona": "centro"},
    "canarte":           {"nombre": "Cañarte",                     "lat": 4.8115, "lon": -75.6995, "tipo": "estacion",       "zona": "centro"},
    "las_flores":        {"nombre": "Las Flores",                  "lat": 4.8100, "lon": -75.7015, "tipo": "estacion",       "zona": "centro"},
    "banderas":          {"nombre": "Banderas",                    "lat": 4.8085, "lon": -75.7040, "tipo": "estacion",       "zona": "centro"},
    "palacio_justicia":  {"nombre": "Palacio de Justicia",         "lat": 4.8072, "lon": -75.7060, "tipo": "estacion",       "zona": "centro"},
    "la_ruana":          {"nombre": "La Ruana",                    "lat": 4.8062, "lon": -75.7080, "tipo": "estacion",       "zona": "centro"},

    # ---------------- Dosquebradas (Av. Simón Bolívar) ----------------
    "la_popa":           {"nombre": "La Popa",                     "lat": 4.8230, "lon": -75.6880, "tipo": "estacion",       "zona": "dosquebradas"},
    "santa_monica":      {"nombre": "Santa Mónica",                "lat": 4.8270, "lon": -75.6860, "tipo": "estacion",       "zona": "dosquebradas"},
    "milan":             {"nombre": "Milán",                       "lat": 4.8310, "lon": -75.6840, "tipo": "estacion",       "zona": "dosquebradas"},
    "fundadores":        {"nombre": "Fundadores",                  "lat": 4.8345, "lon": -75.6820, "tipo": "estacion",       "zona": "dosquebradas"},
    "cam":               {"nombre": "CAM",                         "lat": 4.8380, "lon": -75.6800, "tipo": "estacion",       "zona": "dosquebradas"},
    "dosquebradas":      {"nombre": "Intercambiador Dosquebradas", "lat": 4.8420, "lon": -75.6780, "tipo": "intercambiador", "zona": "dosquebradas"},
}


def existe(id_estacion):
    """Devuelve True si la estación está en la base de conocimiento."""
    return id_estacion in ESTACIONES


def _normalizar(texto):
    """Quita tildes, mayúsculas y espacios extra: ' Egoyá ' -> 'egoya'."""
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def buscar_por_nombre(texto):
    """
    Traduce lo que escribe el usuario al id interno de la estación.
    Acepta el id ('el_lago') o el nombre ('El Lago', 'el lago', 'EL LAGO').
    Devuelve None si no existe (caso de prueba: estación que no existe).
    """
    buscado = _normalizar(texto).replace(" ", "_")
    if buscado in ESTACIONES:
        return buscado
    for id_est, datos in ESTACIONES.items():
        if _normalizar(datos["nombre"]).replace(" ", "_") == buscado:
            return id_est
    return None


def distancia_km(id_a, id_b):
    """
    Distancia en línea recta (fórmula de Haversine) entre dos estaciones, en km.
    Es el insumo de la heurística h(n) del Integrante 3.
    """
    a, b = ESTACIONES[id_a], ESTACIONES[id_b]
    radio_tierra = 6371.0
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = lat2 - lat1
    dlon = math.radians(b["lon"] - a["lon"])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radio_tierra * math.asin(math.sqrt(h))

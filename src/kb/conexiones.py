"""
kb/conexiones.py  -  Base de conocimiento: CONEXIONES entre estaciones
=======================================================================
Integrante 1  |  Base teórica: Capítulos 2 y 3

Aquí se dice qué estación conecta con cuál, por qué ruta y cuántos minutos
tarda el tramo en condiciones NORMALES (sin hora pico ni transbordos:
esos ajustes los hacen las reglas de kb/reglas.py).

Cómo se escribe una ruta:
    Cada recorrido es una lista ordenada de (estacion, minutos_desde_la_anterior).
    La primera estación siempre lleva 0.
    - Si la ruta va y vuelve por las mismas estaciones -> "bidireccional": True
    - Si la ida y el regreso van por calles distintas  -> se escriben los dos
      recorridos por separado y "bidireccional": False

A partir de eso se genera automáticamente la lista CONEXIONES, donde cada
elemento es un hecho del tipo:
    {"origen": "maraya", "destino": "turin", "ruta": "R3", "minutos": 1, "zona": "centro"}

Fuentes: megabus.gov.co (recorridos oficiales) y Moovit (orden de paradas).
Tramos marcados con  # VERIFICAR  son deducciones del equipo: confirmarlos.
Los minutos son estimados (Moovit reporta ~27 min en toda la Ruta 1).
"""

from kb.estaciones import ESTACIONES, distancia_km

# Velocidad máxima del bus troncal en carril exclusivo (km/h).
# La usa el Integrante 3 para la heurística: h(n) = distancia / VELOCIDAD_MAXIMA.
# Se usa la MÁXIMA (no la promedio) para que h(n) nunca sobreestime.
VELOCIDAD_MAXIMA_KMH = 60

RUTAS = {
    # ------------------------------------------------------------------
    # RUTA 1: Cuba - Av. 30 de Agosto - Dosquebradas (misma vía ida y vuelta)
    # ------------------------------------------------------------------
    "R1": {
        "nombre": "Ruta 1: Cuba - Av. 30 de Agosto - Dosquebradas",
        "bidireccional": True,
        "recorridos": [[
            ("cuba", 0), ("san_fernando", 2), ("el_viajero", 2), ("aeropuerto", 2),
            ("batallon", 2), ("maraya", 2), ("el_jardin", 1), ("ucumari", 1),
            ("consota", 1), ("el_cafetero", 1), ("francisco_pereira", 1),
            ("parque_olaya", 2), ("condina", 2),
            ("la_popa", 4),                     # cruza el viaducto  # VERIFICAR
            ("santa_monica", 1), ("milan", 1), ("fundadores", 1), ("cam", 1),
            ("dosquebradas", 2),
        ]],
    },

    # ------------------------------------------------------------------
    # RUTA 2: Cuba - Centro - Dosquebradas
    # Hacia Dosquebradas va por carreras 8 y 10; hacia Cuba por carreras 6 y 7.
    # No entra a la estación El Viajero.
    # ------------------------------------------------------------------
    "R2": {
        "nombre": "Ruta 2: Cuba - Centro - Dosquebradas",
        "bidireccional": False,
        "recorridos": [
            [   # Ida: Cuba -> Dosquebradas
                ("cuba", 0), ("san_fernando", 2), ("aeropuerto", 3), ("batallon", 2),
                ("maraya", 2), ("turin", 1), ("egoya", 1), ("coliseo", 1), ("ormaza", 1),
                ("mercados", 1), ("el_lago", 1), ("otun", 1), ("victoria", 1),
                ("del_cafe", 1),
                ("la_popa", 4),                 # cruza el viaducto  # VERIFICAR
                ("santa_monica", 1), ("milan", 1), ("fundadores", 1), ("cam", 1),
                ("dosquebradas", 2),
            ],
            [   # Regreso: Dosquebradas -> Cuba (orden oficial según Moovit)
                ("dosquebradas", 0), ("cam", 2), ("fundadores", 1), ("milan", 1),
                ("santa_monica", 1), ("la_popa", 1), ("viaducto", 4), ("central", 1),
                ("claret", 1), ("canarte", 1), ("las_flores", 1), ("banderas", 1),
                ("palacio_justicia", 1), ("la_ruana", 1), ("maraya", 2), ("batallon", 2),
                ("aeropuerto", 2), ("san_fernando", 3), ("cuba", 2),
            ],
        ],
    },

    # ------------------------------------------------------------------
    # RUTA 3: Cuba - Centro - Cuba (circuito, NO va a Dosquebradas)
    # Ida por carreras 8 y 10 hasta Libertad; regreso por carreras 6 y 7.
    # ------------------------------------------------------------------
    "R3": {
        "nombre": "Ruta 3: Cuba - Centro - Cuba",
        "bidireccional": False,
        "recorridos": [
            [   # Ida: Cuba -> Libertad (orden oficial según Moovit)
                ("cuba", 0), ("san_fernando", 2), ("el_viajero", 2), ("aeropuerto", 2),
                ("batallon", 2), ("maraya", 2), ("turin", 1), ("egoya", 1), ("coliseo", 1),
                ("ormaza", 1), ("mercados", 1), ("el_lago", 1), ("otun", 1),
                ("victoria", 1), ("del_cafe", 1), ("libertad", 1),
            ],
            [   # Regreso: Libertad -> Cuba
                ("libertad", 0), ("viaducto", 1), ("central", 1), ("claret", 1),
                ("canarte", 1), ("las_flores", 1), ("banderas", 1), ("palacio_justicia", 1),
                ("la_ruana", 1), ("maraya", 2), ("batallon", 2), ("aeropuerto", 2),
                ("el_viajero", 2), ("san_fernando", 2), ("cuba", 2),
            ],
        ],
    },
}


def _generar_conexiones():
    """Convierte los recorridos de RUTAS en una lista plana de conexiones (arcos del grafo)."""
    conexiones = []
    for id_ruta, ruta in RUTAS.items():
        for recorrido in ruta["recorridos"]:
            for (origen, _), (destino, minutos) in zip(recorrido, recorrido[1:]):
                conexiones.append({
                    "origen": origen, "destino": destino, "ruta": id_ruta,
                    "minutos": minutos, "zona": ESTACIONES[destino]["zona"],
                })
                if ruta["bidireccional"]:
                    conexiones.append({
                        "origen": destino, "destino": origen, "ruta": id_ruta,
                        "minutos": minutos, "zona": ESTACIONES[origen]["zona"],
                    })
    return conexiones


# Lista final de hechos de conexión. Es lo que lee el motor de inferencia (Integrante 2).
CONEXIONES = _generar_conexiones()


def conexiones_desde(id_estacion):
    """Todas las conexiones que salen de una estación."""
    return [c for c in CONEXIONES if c["origen"] == id_estacion]


def rutas_de_estacion(id_estacion):
    """Conjunto de rutas que pasan por una estación. Ej: maraya -> {'R1','R2','R3'}."""
    return {c["ruta"] for c in CONEXIONES
            if id_estacion in (c["origen"], c["destino"])}


def estaciones_de_transbordo():
    """Estaciones donde se puede cambiar de ruta (pasa más de una ruta)."""
    resultado = {}
    for id_est in ESTACIONES:
        rutas = rutas_de_estacion(id_est)
        if len(rutas) > 1:
            resultado[id_est] = rutas
    return resultado


def validar():
    """
    Revisa que la base de conocimiento sea coherente. Devuelve una lista de errores
    (vacía = todo bien). Comprueba:
      1. Que toda estación usada en una ruta exista en ESTACIONES.
      2. Que ningún tramo dure menos de lo que tardaría el bus a velocidad máxima
         (si no, la heurística de A* dejaría de ser admisible).
      3. Que toda estación tenga al menos una conexión.
    """
    errores = []
    for c in CONEXIONES:
        for est in (c["origen"], c["destino"]):
            if est not in ESTACIONES:
                errores.append(f"Estación desconocida '{est}' en ruta {c['ruta']}")
        if c["origen"] in ESTACIONES and c["destino"] in ESTACIONES:
            minimo = distancia_km(c["origen"], c["destino"]) / VELOCIDAD_MAXIMA_KMH * 60
            if c["minutos"] < minimo:
                errores.append(
                    f"Tramo {c['origen']}->{c['destino']} ({c['ruta']}): {c['minutos']} min "
                    f"es menos que el mínimo físico {minimo:.2f} min")
    usadas = {c["origen"] for c in CONEXIONES} | {c["destino"] for c in CONEXIONES}
    for est in ESTACIONES:
        if est not in usadas:
            errores.append(f"La estación '{est}' no tiene conexiones")
    return errores

"""
engine/inferencia.py  -  Motor de inferencia (encadenamiento hacia adelante)
============================================================================
INTEGRANTE 2  |  Base teórica: Capítulo 3        *** PENDIENTE ***

Contrato acordado con el resto del equipo (ver la cabecera de kb/reglas.py):

    construir_mapa(hora: str) -> (mapa, traza)

    hora  : "HH:MM"
    mapa  : dict { nodo: [(nodo_vecino, minutos_ajustados), ...] }
            donde nodo = (id_estacion, id_ruta)
            - arcos de tramo      : (A, R1) -> (B, R1)
            - arcos de transbordo : (A, R1) -> (A, R2)   (misma estación)
    traza : lista de dicts {"arco": ..., "regla": "A2", "descripcion": "..."}

Entradas: kb.conexiones.CONEXIONES, kb.conexiones.estaciones_de_transbordo(),
          kb.estaciones.ESTACIONES, kb.reglas.REGLAS
"""


def construir_mapa(hora):
    raise NotImplementedError("Lo implementa el Integrante 2")

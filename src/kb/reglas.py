"""
kb/reglas.py  -  Base de conocimiento: REGLAS de producción (SI ... ENTONCES ...)
==================================================================================
Integrante 1  |  Base teórica: Capítulos 2 y 3

Las reglas NO están escritas como código "if" sino como DATOS, para que el
motor de inferencia (Integrante 2) pueda leerlas, evaluarlas y registrar en la
traza cuáles se activaron. Así se separa el conocimiento (qué sabemos) del
razonamiento (cómo lo usamos), que es la idea central de un sistema experto.

-------------------------------------------------------------------------------
HECHOS BASE que el motor debe crear para cada arco del mapa
-------------------------------------------------------------------------------
    tipo_arco      : "tramo" (viajar entre dos estaciones) o
                     "transbordo" (cambiar de ruta dentro de una misma estación)
    ruta_llegada   : ruta con la que se llega  (en un tramo es la misma ruta)
    ruta_salida    : ruta con la que se sale   (en un tramo es la misma ruta)
    estacion       : estación donde ocurre el arco (en un tramo, la de destino)
    tipo_estacion  : "intercambiador" o "estacion"
    zona_destino   : "occidente", "av30", "centro" o "dosquebradas"
    hora           : hora del viaje en MINUTOS desde medianoche (07:30 -> 450)
    minutos_base   : tiempo base del arco (0 en los transbordos)

¿Por qué existen arcos de "transbordo"? Porque el transbordo depende de cómo
llegas a una estación. Si el mapa usa como nodos (estación, ruta), el cambio de
ruta se vuelve un arco más y las reglas pueden evaluarlo sin conocer el camino.

-------------------------------------------------------------------------------
FORMATO DE UNA REGLA
-------------------------------------------------------------------------------
    "id"          : identificador corto (aparece en la traza)
    "tipo"        : "deduccion" -> ENTONCES agrega un hecho nuevo
                    "ajuste"    -> ENTONCES modifica el tiempo del arco
    "si"          : lista de condiciones; TODAS deben cumplirse (es un Y lógico)
                    Cada condición es (hecho, operador, valor)
    "entonces"    : deduccion -> ("agregar_hecho", nombre, valor)
                    ajuste    -> ("sumar", minutos) | ("multiplicar", factor) | ("bloquear",)
    "descripcion" : la regla en español (para la traza y el informe)

Operadores permitidos: "==", "!=", "<", ">=", "entre"
    - "entre" recibe ("HH:MM", "HH:MM") y se cumple si inicio <= hora < fin
    - Si el valor empieza con "$" se compara contra OTRO hecho.
      Ej: ("ruta_llegada", "!=", "$ruta_salida")
    - Si un hecho no existe todavía, la condición se considera FALSA.
    - Cuando el hecho es "hora", los valores se escriben "HH:MM" y el motor
      los convierte con hora_a_minutos() antes de comparar.

-------------------------------------------------------------------------------
ESTRATEGIA DE INFERENCIA ACORDADA (para el Integrante 2)
-------------------------------------------------------------------------------
    1. Encadenamiento hacia adelante con las reglas de "deduccion": se repiten
       hasta que ninguna agregue un hecho nuevo (punto fijo).
    2. Se aplican las reglas de "ajuste" en este orden:
         a) "bloquear"    -> el arco se elimina del mapa
         b) "multiplicar" -> factores de congestión
         c) "sumar"       -> penalizaciones fijas (no se multiplican)
    3. Cada regla disparada se guarda en la traza con su id y su descripción.
"""


def hora_a_minutos(hora_texto):
    """Convierte 'HH:MM' en minutos desde medianoche. Ej: '07:30' -> 450."""
    horas, minutos = hora_texto.strip().split(":")
    horas, minutos = int(horas), int(minutos)
    if not (0 <= horas <= 23 and 0 <= minutos <= 59):
        raise ValueError(f"Hora inválida: {hora_texto}")
    return horas * 60 + minutos


# Penalizaciones y factores en un solo lugar, para ajustarlos fácilmente.
TRANSBORDO_ESTACION_MIN = 5       # minutos de caminar y esperar en estación normal
TRANSBORDO_INTERCAMBIADOR_MIN = 3 # en intercambiador las plataformas están diseñadas para eso
ESPERA_NOCTURNA_MIN = 4           # de noche los buses pasan con menos frecuencia
FACTOR_HORA_PICO = 1.4            # tráfico general en hora pico
FACTOR_CENTRO_PICO = 1.2          # congestión adicional del centro en hora pico


REGLAS = [
    # =========================================================================
    # REGLAS DE DEDUCCIÓN  (crean hechos nuevos a partir de otros hechos)
    # =========================================================================
    {
        "id": "D1", "tipo": "deduccion",
        "si": [("hora", "entre", ("06:00", "08:00"))],
        "entonces": ("agregar_hecho", "es_hora_pico", True),
        # SI el viaje es entre las 6:00 y las 8:00 de la mañana
        # ENTONCES es hora pico (la gente va al trabajo y al colegio).
        "descripcion": "Entre 6:00 y 8:00 es hora pico de la mañana",
    },
    {
        "id": "D2", "tipo": "deduccion",
        "si": [("hora", "entre", ("17:00", "19:30"))],
        "entonces": ("agregar_hecho", "es_hora_pico", True),
        # SI el viaje es entre las 5:00 y las 7:30 de la tarde
        # ENTONCES es hora pico (salida del trabajo).
        "descripcion": "Entre 17:00 y 19:30 es hora pico de la tarde",
    },
    {
        "id": "D3", "tipo": "deduccion",
        "si": [("ruta_llegada", "!=", "$ruta_salida")],
        "entonces": ("agregar_hecho", "hay_transbordo", True),
        # SI llegas a la estación por una ruta Y sales por otra distinta
        # ENTONCES estás haciendo un transbordo.
        "descripcion": "Llegar por una ruta y salir por otra es un transbordo",
    },
    {
        "id": "D4", "tipo": "deduccion",
        "si": [("hora", "entre", ("21:00", "23:30"))],
        "entonces": ("agregar_hecho", "es_horario_nocturno", True),
        # SI el viaje es entre las 9:00 y las 11:30 de la noche
        # ENTONCES es horario nocturno (menos buses circulando).
        "descripcion": "Entre 21:00 y 23:30 es horario nocturno",
    },
    {
        "id": "D5", "tipo": "deduccion",
        "si": [("hora", "<", "05:00")],
        "entonces": ("agregar_hecho", "sistema_cerrado", True),
        # SI la hora es antes de las 5:00 de la mañana
        # ENTONCES el sistema no está operando.
        # (Supuesto del equipo según horarios publicados; verificar.)
        "descripcion": "Antes de las 5:00 el sistema Megabús está cerrado",
    },
    {
        "id": "D6", "tipo": "deduccion",
        "si": [("hora", ">=", "23:30")],
        "entonces": ("agregar_hecho", "sistema_cerrado", True),
        # SI la hora es desde las 11:30 de la noche en adelante
        # ENTONCES el sistema no está operando.
        "descripcion": "Desde las 23:30 el sistema Megabús está cerrado",
    },

    # =========================================================================
    # REGLAS DE AJUSTE  (modifican el tiempo del arco usando los hechos)
    # =========================================================================
    {
        "id": "A1", "tipo": "ajuste",
        "si": [("sistema_cerrado", "==", True)],
        "entonces": ("bloquear",),
        # SI el sistema está cerrado
        # ENTONCES ese arco no se puede usar (se elimina del mapa).
        # Con esto se prueba el caso "ruta imposible".
        "descripcion": "Con el sistema cerrado no se puede viajar",
    },
    {
        "id": "A2", "tipo": "ajuste",
        "si": [("tipo_arco", "==", "tramo"), ("es_hora_pico", "==", True)],
        "entonces": ("multiplicar", FACTOR_HORA_PICO),
        # SI se viaja entre dos estaciones Y es hora pico
        # ENTONCES el tramo tarda 40 % más (multiplica por 1.4).
        "descripcion": "En hora pico cada tramo tarda 40 % más",
    },
    {
        "id": "A3", "tipo": "ajuste",
        "si": [("tipo_arco", "==", "tramo"), ("es_hora_pico", "==", True),
               ("zona_destino", "==", "centro")],
        "entonces": ("multiplicar", FACTOR_CENTRO_PICO),
        # SI se viaja hacia una estación del centro Y es hora pico
        # ENTONCES se suma un 20 % más por la congestión de las carreras 6, 7, 8 y 10.
        # (Se aplica además de A2: en total 1.4 x 1.2 = 1.68.)
        "descripcion": "En hora pico el centro tiene 20 % más de congestión",
    },
    {
        "id": "A4", "tipo": "ajuste",
        "si": [("hay_transbordo", "==", True), ("tipo_estacion", "==", "estacion")],
        "entonces": ("sumar", TRANSBORDO_ESTACION_MIN),
        # SI hay transbordo Y se hace en una estación normal
        # ENTONCES suma 5 minutos (cambiar de plataforma y esperar el otro bus).
        "descripcion": "Transbordo en estación normal: +5 min",
    },
    {
        "id": "A5", "tipo": "ajuste",
        "si": [("hay_transbordo", "==", True), ("tipo_estacion", "==", "intercambiador")],
        "entonces": ("sumar", TRANSBORDO_INTERCAMBIADOR_MIN),
        # SI hay transbordo Y se hace en un intercambiador (Cuba o Dosquebradas)
        # ENTONCES suma solo 3 minutos, porque están diseñados para eso.
        "descripcion": "Transbordo en intercambiador: +3 min",
    },
    {
        "id": "A6", "tipo": "ajuste",
        "si": [("hay_transbordo", "==", True), ("es_horario_nocturno", "==", True)],
        "entonces": ("sumar", ESPERA_NOCTURNA_MIN),
        # SI hay transbordo Y es horario nocturno
        # ENTONCES suma 4 minutos más de espera (pasan menos buses).
        "descripcion": "Transbordo de noche: +4 min de espera",
    },
]


def reglas_por_tipo(tipo):
    """Devuelve solo las reglas de 'deduccion' o de 'ajuste'."""
    return [r for r in REGLAS if r["tipo"] == tipo]

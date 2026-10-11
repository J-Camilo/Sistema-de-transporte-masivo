"""
ml/integracion.py - Reglas aprendidas por el árbol dentro del motor de la Actividad 1
=====================================================================================
Rol C | Base teórica: Capítulo 17 (de árboles a reglas) y Capítulo 3 (inferencia)

Cierra el ciclo del proyecto: la Actividad 1 razonaba con reglas escritas a mano
(kb/reglas.py); aquí se toman reglas que el árbol descubrió solo
(docs/reglas_aprendidas.txt) y se ejecutan con el MISMO motor de inferencia.

    1. leer_reglas(texto)        export_text() -> una regla por hoja (camino raíz -> hoja)
    2. a_regla_motor(regla, id)  la regla queda con el formato de kb/reglas.py:
                                 SI condiciones ENTONCES agregar_hecho nivel_demora
    3. inferir_demora(hechos, reglas)
                                 encadenamiento hacia adelante del motor (engine/inferencia.py)
                                 con las reglas de la Actividad 1 MÁS las aprendidas.

Traducción de las condiciones del árbol a las del motor:
    clima_lluvia > 0.5         ->  ("clima", "==", "lluvia")      columnas de get_dummies()
    clima_lluvia <= 0.5        ->  ("clima", "!=", "lluvia")
    hora <= 16.5               ->  ("hora", "<", "17:00")         el motor trabaja en HH:MM
    es_festivo <= 0.5          ->  ("es_festivo", "==", 0)
    tiempo_base_min <= 7.11    ->  ("tiempo_base_min", "<", 7.11)
El motor no tiene "<=": se usa "<". Es equivalente porque los umbrales del árbol
son puntos medios entre dos valores del entrenamiento.

Ejecutar (desde la raíz, necesita docs/reglas_aprendidas.txt del Rol B):
    python src/ml/integracion.py --origen "Cuba" --destino "Dosquebradas" --hora 18:00 --clima lluvia
    python src/ml/integracion.py ... --html      (además abre el resultado en el navegador)
    python src/ml/integracion.py --listar        (muestra las reglas cargadas)
"""

import argparse
import csv
import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "data"))

from engine import inferencia
from kb import reglas as kb_reglas

RUTA_REGLAS = RAIZ / "docs" / "reglas_aprendidas.txt"
RUTA_CSV = RAIZ / "data" / "viajes_megabus.csv"
ARCHIVO_HTML = RAIZ / "resultado_integracion.html"

# Columnas de texto que preparacion.py convirtió con get_dummies().
CATEGORICAS = ["estacion_origen", "estacion_destino", "dia_semana", "clima", "ruta"]
NUMERICAS = ["num_transbordos", "distancia_km", "es_festivo", "tiempo_base_min"]

CANTIDAD_REGLAS = 4
ACIERTO_MINIMO = 0.75

_CONDICION = re.compile(r"^(?P<columna>.+?) (?P<op><=|>) +(?P<umbral>-?[\d.]+)$")
_CLASE = re.compile(r"^class: (?P<clase>\w+)$")


# ---------------------------------------------------------------------------
# 1. Leer el texto de export_text()
# ---------------------------------------------------------------------------
def leer_reglas(texto):
    """Cada hoja del árbol es una regla: las condiciones son el camino desde la raíz."""
    reglas, camino = [], []
    for linea in texto.splitlines():
        if "|---" not in linea:
            continue
        nivel = linea.index("|---") // 4
        contenido = linea.split("|--- ", 1)[1].strip()
        del camino[nivel:]

        clase = _CLASE.match(contenido)
        if clase:
            reglas.append({"condiciones": list(camino), "clase": clase["clase"]})
            continue

        cond = _CONDICION.match(contenido)
        if not cond:
            raise ValueError(f"Línea de export_text() no reconocida: {linea!r}")
        camino.append((cond["columna"], cond["op"], float(cond["umbral"])))
    return reglas


# ---------------------------------------------------------------------------
# 2. Traducir al formato de kb/reglas.py
# ---------------------------------------------------------------------------
def a_condicion_motor(columna, op, umbral):
    for categoria in CATEGORICAS:
        if columna.startswith(categoria + "_"):
            valor = columna[len(categoria) + 1:]
            return (categoria, "==" if op == ">" else "!=", valor)

    if columna == "es_festivo":
        return ("es_festivo", "==", 1 if op == ">" else 0)

    if columna == "hora":
        hora = f"{math.floor(umbral) + 1:02d}:00"
        return ("hora", "<" if op == "<=" else ">=", hora)

    return (columna, "<" if op == "<=" else ">=", umbral)


def simplificar(condiciones):
    """
    El camino de un árbol vuelve a preguntar por la misma columna con umbrales más
    finos (hora >= 9:00 ... hora >= 11:00 ... hora < 14:00). Por cada hecho se deja
    solo el límite más estrecho y, si hay dos, se usa el operador "entre" del motor.
    """
    por_hecho = {}
    for hecho, operador, valor in condiciones:
        por_hecho.setdefault(hecho, []).append((operador, valor))

    resultado = []
    for hecho, lista in por_hecho.items():
        clave = kb_reglas.hora_a_minutos if hecho == "hora" else (lambda v: v)
        iguales = [v for op, v in lista if op == "=="]
        if iguales:
            resultado.append((hecho, "==", iguales[0]))
            continue
        desde = max((v for op, v in lista if op == ">="), key=clave, default=None)
        hasta = min((v for op, v in lista if op == "<"), key=clave, default=None)
        if desde is not None and hasta is not None:
            resultado.append((hecho, "entre", (desde, hasta)))
        elif desde is not None:
            resultado.append((hecho, ">=", desde))
        elif hasta is not None:
            resultado.append((hecho, "<", hasta))
        resultado += [(hecho, "!=", v) for op, v in lista if op == "!="]
    return resultado


def _texto_condicion(hecho, operador, valor):
    nombre = hecho.replace("_", " ")
    if operador == "entre":
        return f"{nombre} entre {valor[0]} y {valor[1]}"
    return f"{nombre} {'=' if operador == '==' else operador} {valor}"


def a_regla_motor(regla, id_regla):
    si = simplificar([a_condicion_motor(*c) for c in regla["condiciones"]])
    descripcion = (" Y ".join(_texto_condicion(*c) for c in si)
                   + f" -> demora {regla['clase']}")
    return {
        "id": id_regla,
        "tipo": "deduccion",
        "si": si,
        "entonces": ("agregar_hecho", "nivel_demora", regla["clase"]),
        "descripcion": f"Aprendida del árbol: {descripcion}",
    }


# ---------------------------------------------------------------------------
# 3. Ejecutar con el motor de la Actividad 1
# ---------------------------------------------------------------------------
def hechos_de_fila(fila):
    """Hechos de un viaje del CSV. tiempo_real_min y nivel_demora no entran (son la respuesta)."""
    hechos = {c: fila[c] for c in CATEGORICAS}
    hechos.update({c: float(fila[c]) if "." in str(fila[c]) else int(fila[c])
                   for c in NUMERICAS})
    hechos["hora"] = int(fila["hora"]) * 60
    return hechos


def inferir_demora(hechos, reglas_aprendidas):
    """
    Corre el encadenamiento hacia adelante del motor con las reglas de kb/reglas.py
    más las aprendidas. Devuelve (nivel_demora o None, traza).

    Las reglas se agregan a la base de conocimiento solo mientras dura la inferencia,
    para no alterar la ruta que calcula construir_mapa().
    """
    hechos, traza = dict(hechos), []
    cantidad = len(kb_reglas.REGLAS)
    kb_reglas.REGLAS.extend(reglas_aprendidas)
    try:
        inferencia._deducir(hechos, "viaje", traza)
    finally:
        del kb_reglas.REGLAS[cantidad:]
    return hechos.get("nivel_demora"), traza


# ---------------------------------------------------------------------------
# Escoger las reglas que se cargan
# ---------------------------------------------------------------------------
def medir(regla, filas):
    """Soporte (viajes que cumplen la regla) y acierto (de esos, cuántos tienen esa clase)."""
    motor = a_regla_motor(regla, "?")
    cumplen = [f for f in filas if inferencia._se_cumple(motor, hechos_de_fila(f))]
    if not cumplen:
        return 0, 0.0
    aciertos = sum(f["nivel_demora"] == regla["clase"] for f in cumplen)
    return len(cumplen), aciertos / len(cumplen)


def seleccionar(reglas, filas, cantidad=CANTIDAD_REGLAS, acierto_minimo=ACIERTO_MINIMO):
    """
    Las reglas que valen la pena mostrar: generales, con buen acierto y que cubran
    muchos viajes. Se descartan las que exigen una estación concreta (estacion_X > 0.5):
    son casos sueltos que el árbol memorizó. Las que solo excluyen una estación
    (estacion_X <= 0.5) siguen siendo generales.
    Primero la mejor de cada clase y después las de más soporte.
    """
    candidatas = []
    for regla in reglas:
        if any(c.startswith("estacion_") and op == ">" for c, op, _ in regla["condiciones"]):
            continue
        soporte, acierto = medir(regla, filas)
        if soporte and acierto >= acierto_minimo:
            candidatas.append(dict(regla, soporte=soporte, acierto=acierto))

    candidatas.sort(key=lambda r: r["soporte"], reverse=True)
    elegidas = []
    for regla in candidatas:
        if all(r["clase"] != regla["clase"] for r in elegidas):
            elegidas.append(regla)
    elegidas += [r for r in candidatas if r not in elegidas]
    return sorted(elegidas[:cantidad], key=lambda r: r["soporte"], reverse=True)


def cargar_reglas_aprendidas(todas=False):
    """Lee docs/reglas_aprendidas.txt y devuelve las reglas ya en formato del motor."""
    if not RUTA_REGLAS.exists():
        raise FileNotFoundError(f"Falta {RUTA_REGLAS.relative_to(RAIZ)}: "
                                "primero corra python src/ml/extraer_reglas.py")
    reglas = leer_reglas(RUTA_REGLAS.read_text(encoding="utf-8"))
    if not todas:
        with open(RUTA_CSV, encoding="utf-8") as f:
            reglas = seleccionar(reglas, list(csv.DictReader(f)))
    return [dict(a_regla_motor(r, f"ML{i}"), soporte=r.get("soporte"), acierto=r.get("acierto"))
            for i, r in enumerate(reglas, start=1)]


# ---------------------------------------------------------------------------
# Consola: el sistema de la Actividad 1 + la demora que predicen las reglas aprendidas
# ---------------------------------------------------------------------------
def hechos_de_viaje(camino, origen, destino, hora, dia, clima, festivo):
    """Describe la ruta que encontró A* con las mismas columnas del CSV."""
    from generar_dataset import PENALIZACION_TRANSBORDO, VELOCIDAD_KMH
    from kb.estaciones import ESTACIONES, distancia_km

    transbordos = sum(a[0] == b[0] for a, b in zip(camino, camino[1:]))
    distancia = round(distancia_km(origen, destino), 3)
    base = max(distancia / VELOCIDAD_KMH * 60 + transbordos * PENALIZACION_TRANSBORDO, 3.0)
    return {
        "estacion_origen": ESTACIONES[origen]["nombre"],
        "estacion_destino": ESTACIONES[destino]["nombre"],
        "ruta": "Ruta " + camino[0][1][1:],
        "num_transbordos": transbordos,
        "distancia_km": distancia,
        "hora": kb_reglas.hora_a_minutos(hora),
        "dia_semana": dia,
        "es_festivo": int(festivo),
        "clima": clima,
        "tiempo_base_min": round(base, 2),
    }


def leer_argumentos(argv):
    p = argparse.ArgumentParser(description="Ruta de la Actividad 1 + demora según las reglas aprendidas.")
    p.add_argument("--origen")
    p.add_argument("--destino")
    p.add_argument("--hora", default="07:30", help="HH:MM")
    p.add_argument("--dia", default="lunes",
                   choices=["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"])
    p.add_argument("--clima", default="despejado", choices=["despejado", "nublado", "lluvia"])
    p.add_argument("--festivo", action="store_true")
    p.add_argument("--todas", action="store_true",
                   help="Carga TODAS las reglas del árbol, no solo las escogidas")
    p.add_argument("--listar", action="store_true", help="Muestra las reglas cargadas y termina")
    p.add_argument("--html", action="store_true", help="Abre el resultado en el navegador")
    return p.parse_args(argv)


def imprimir_reglas(reglas):
    print(f"\nREGLAS APRENDIDAS CARGADAS EN EL MOTOR ({len(reglas)})")
    for r in reglas:
        extra = f"  [cubre {r['soporte']} viajes, acierta {r['acierto']:.0%}]" if r["soporte"] else ""
        print(f"  {r['id']}: {r['descripcion'].removeprefix('Aprendida del árbol: ')}{extra}")


def main(argv=None):
    from kb.estaciones import buscar_por_nombre
    from main import imprimir_ruta
    from search.astar import buscar

    args = leer_argumentos(argv)
    try:
        aprendidas = cargar_reglas_aprendidas(todas=args.todas)
    except FileNotFoundError as error:
        print(error)
        return 1
    if args.listar or not (args.origen and args.destino):
        imprimir_reglas(aprendidas)
        return 0

    origen, destino = buscar_por_nombre(args.origen), buscar_por_nombre(args.destino)
    if not origen or not destino or origen == destino:
        print("Origen o destino inválido (deben existir y ser distintos). Use: python src/main.py --listar")
        return 1
    try:
        mapa, traza = inferencia.construir_mapa(args.hora)
    except ValueError as error:
        print(error)
        return 1
    camino, costo = buscar(mapa, origen, destino)
    if camino is None:
        print("No hay ruta a esa hora (sistema cerrado).")
        return 2

    imprimir_ruta(mapa, camino, costo, traza, origen, destino, args.hora)

    hechos = hechos_de_viaje(camino, origen, destino, args.hora, args.dia, args.clima, args.festivo)
    nivel, traza_viaje = inferir_demora(hechos, aprendidas)

    print("\nHECHOS DEL VIAJE: " + ", ".join(f"{k}={v}" for k, v in hechos.items() if k != "hora")
          + f", hora={args.hora}")
    for t in traza_viaje:
        marca = "APRENDIDA" if t["regla"].startswith("ML") else "a mano   "
        print(f"  [{t['regla']}] {marca} {t['descripcion'].removeprefix('Aprendida del árbol: ')}")
    if nivel:
        print(f"\nDEMORA ESPERADA: {nivel.upper()} (deducida por una regla que nadie escribió a mano)")
    else:
        print(f"\nDEMORA ESPERADA: ninguna de las {len(aprendidas)} reglas cargadas aplica a este viaje"
              " (pruebe con --todas)")

    if args.html:
        from ml.reporte import guardar_y_abrir, html_integracion
        guardar_y_abrir(html_integracion(mapa, camino, costo, origen, destino, args.hora, hechos,
                                         traza_viaje, aprendidas, nivel), ARCHIVO_HTML)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

"""
main.py  -  Interfaz por consola
================================
INTEGRANTE 3  |  Une las tres piezas del sistema:

    1. kb/      -> estaciones, conexiones y reglas        (Integrante 1)
    2. engine/  -> construir_mapa(hora) con la traza      (Integrante 2)
    3. search/  -> A* sobre ese mapa                      (Integrante 3)

Ejecutar:
    python main.py --origen "Cuba" --destino "Dosquebradas" --hora 07:30
    python main.py                      (pregunta origen, destino y hora)
    python main.py --listar             (muestra las estaciones disponibles)

Códigos de salida: 0 = ruta encontrada, 1 = dato inválido, 2 = no hay ruta.
"""
import argparse
import sys
from datetime import datetime

from engine.inferencia import construir_mapa
from kb.estaciones import ESTACIONES, buscar_por_nombre
from kb.reglas import REGLAS, hora_a_minutos
from search.astar import buscar, comparar


def nombre(id_estacion):
    return ESTACIONES[id_estacion]["nombre"]


def resumir_camino(mapa, camino):
    """
    Convierte la lista de nodos (estacion, ruta) en pasos legibles:
    los tramos seguidos por la misma ruta se juntan en uno solo y
    cada cambio de ruta se muestra como un TRANSBORDO.
    """
    pasos = []
    for (a, ruta_a), (b, ruta_b) in zip(camino, camino[1:]):
        minutos = dict(mapa[(a, ruta_a)])[(b, ruta_b)]
        if a == b:
            pasos.append({"tipo": "transbordo", "estacion": a,
                          "de": ruta_a, "a": ruta_b, "minutos": minutos})
        elif pasos and pasos[-1]["tipo"] == "tramo" and pasos[-1]["ruta"] == ruta_a:
            pasos[-1]["hasta"] = b
            pasos[-1]["minutos"] += minutos
        else:
            pasos.append({"tipo": "tramo", "ruta": ruta_a,
                          "desde": a, "hasta": b, "minutos": minutos})
    return pasos


def reglas_del_camino(camino, traza):
    """
    La traza del motor tiene las reglas de TODOS los arcos del mapa.
    Aquí se filtran solo las de los arcos que usa la ruta elegida,
    en el orden en que aparecen y contando cuántas veces se activó cada una.
    """
    etiquetas = {f"({a}, {ra}) -> ({b}, {rb})"
                 for (a, ra), (b, rb) in zip(camino, camino[1:])}
    reglas = {}
    for registro in traza:
        if registro["arco"] in etiquetas:
            regla = reglas.setdefault(registro["regla"], {
                "id": registro["regla"], "descripcion": registro["descripcion"], "veces": 0})
            regla["veces"] += 1
    return list(reglas.values())


def imprimir_ruta(mapa, camino, costo, traza, origen, destino, hora):
    print(f"\nRUTA RECOMENDADA  ({nombre(origen)} -> {nombre(destino)}, {hora})")
    for i, paso in enumerate(resumir_camino(mapa, camino), start=1):
        if paso["tipo"] == "tramo":
            texto = f"{nombre(paso['desde'])} -> {nombre(paso['hasta'])} "
            print(f"  {i}. {texto:.<52} {paso['ruta']} ... {paso['minutos']:.1f} min")
        else:
            texto = f"TRANSBORDO en {nombre(paso['estacion'])} ({paso['de']} -> {paso['a']}) "
            print(f"  {i}. {texto:.<58} +{paso['minutos']:.1f} min")

    reglas = reglas_del_camino(camino, traza)
    pico = any(r["id"] == "A2" for r in reglas)
    print(f"TIEMPO TOTAL: {costo:.1f} min" + (" (hora pico aplicada)" if pico else ""))

    print("\nREGLAS QUE SE ACTIVARON EN ESTA RUTA")
    for r in reglas:
        print(f"  [{r['id']}] {r['descripcion']}  (x{r['veces']})")


def imprimir_comparacion(mapa, origen, destino):
    resultado = comparar(mapa, origen, destino)
    a, d = resultado["astar"]["expandidos"], resultado["dijkstra"]["expandidos"]
    print(f"\nBÚSQUEDA: A* revisó {a} nodos | Dijkstra (sin heurística) revisó {d} nodos")


def leer_argumentos(argv):
    parser = argparse.ArgumentParser(description="Mejor ruta en Megabús (Pereira)")
    parser.add_argument("--origen", help="estación de origen (ej: Cuba)")
    parser.add_argument("--destino", help="estación de destino (ej: Dosquebradas)")
    parser.add_argument("--hora", help="hora del viaje HH:MM (por defecto, la hora actual)")
    parser.add_argument("--listar", action="store_true", help="muestra las estaciones")
    args = parser.parse_args(argv)

    # Si faltan datos, se le preguntan al usuario por consola.
    if not args.listar:
        args.origen = args.origen or input("Estación de origen: ")
        args.destino = args.destino or input("Estación de destino: ")
        args.hora = args.hora or input("Hora (HH:MM, Enter = ahora): ") or \
            datetime.now().strftime("%H:%M")
    return args


def main(argv=None):
    args = leer_argumentos(argv)

    if args.listar:
        for id_est, datos in ESTACIONES.items():
            print(f"  {datos['nombre']:<30} ({id_est})")
        return 0

    origen = buscar_por_nombre(args.origen)
    destino = buscar_por_nombre(args.destino)
    for texto, id_est in ((args.origen, origen), (args.destino, destino)):
        if id_est is None:
            print(f"La estación '{texto}' no existe. Usa --listar para ver las disponibles.")
            return 1

    try:
        hora_a_minutos(args.hora)
    except ValueError:
        print(f"Hora inválida: '{args.hora}'. Usa el formato HH:MM (ej: 07:30).")
        return 1

    if origen == destino:
        print(f"Ya estás en {nombre(origen)}: no hace falta viajar.")
        return 0

    mapa, traza = construir_mapa(args.hora)
    camino, costo = buscar(mapa, origen, destino)

    if camino is None:
        print(f"No hay ruta de {nombre(origen)} a {nombre(destino)} a las {args.hora}.")
        bloqueos = {r["regla"] for r in traza if r.get("accion") == "bloquear"}
        for regla in REGLAS:
            if regla["id"] in bloqueos:
                print(f"  [{regla['id']}] {regla['descripcion']}")
        return 2

    imprimir_ruta(mapa, camino, costo, traza, origen, destino, args.hora)
    imprimir_comparacion(mapa, origen, destino)
    return 0


if __name__ == "__main__":
    # La consola de Windows no siempre usa UTF-8: sin esto las tildes salen rotas.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

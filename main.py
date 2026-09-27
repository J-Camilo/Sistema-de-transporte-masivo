"""
main.py  -  Interfaz por consola
================================
INTEGRANTE 3 completa este archivo. Por ahora solo verifica la base de conocimiento.
Ejecutar:  python main.py
"""
from kb.estaciones import ESTACIONES
from kb.conexiones import CONEXIONES, validar
from kb.reglas import REGLAS


def main():
    errores = validar()
    print(f"Base de conocimiento: {len(ESTACIONES)} estaciones, "
          f"{len(CONEXIONES)} conexiones, {len(REGLAS)} reglas")
    print("Estado:", "OK" if not errores else "CON ERRORES")
    for e in errores:
        print("  -", e)
    # TODO (Integrante 3): pedir origen, destino y hora; llamar a
    # engine.inferencia.construir_mapa(hora) y luego a search.astar.buscar(...)


if __name__ == "__main__":
    main()

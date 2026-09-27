"""
demo_kb.py  -  Demostración de la base de conocimiento (para el video del Integrante 1)
Ejecutar desde la raíz del proyecto:  python3 demo_kb.py
"""
from kb.estaciones import ESTACIONES, buscar_por_nombre, distancia_km
from kb.conexiones import RUTAS, CONEXIONES, rutas_de_estacion, conexiones_desde, validar
from kb.reglas import REGLAS, hora_a_minutos


def titulo(texto):
    print("\n" + "=" * 60 + f"\n{texto}\n" + "=" * 60)


titulo("1. ESTACIONES (hechos)")
print(f"Total de estaciones: {len(ESTACIONES)}")
print("Ejemplo -> maraya:", ESTACIONES["maraya"])
print("Buscar 'Egoyá'          ->", buscar_por_nombre("Egoyá"))
print("Buscar 'Estación Marte' ->", buscar_por_nombre("Estación Marte"))
print(f"Distancia en línea recta Cuba -> Dosquebradas: {distancia_km('cuba', 'dosquebradas'):.2f} km")

titulo("2. CONEXIONES (qué conecta con qué, por qué ruta y cuántos minutos)")
for id_ruta, ruta in RUTAS.items():
    print(f"{id_ruta}: {ruta['nombre']}")
print(f"Total de conexiones generadas: {len(CONEXIONES)}")
print("Rutas que pasan por Maraya:", sorted(rutas_de_estacion("maraya")))
print("Conexiones que salen de El Lago:")
for c in conexiones_desde("el_lago"):
    print(f"   {c['origen']} -> {c['destino']}  por {c['ruta']}  ({c['minutos']} min)")

titulo("3. REGLAS (SI ... ENTONCES ...)")
for r in REGLAS:
    condiciones = " Y ".join(f"{h} {op} {v}" for h, op, v in r["si"])
    print(f"[{r['id']}] SI {condiciones}")
    print(f"      ENTONCES {r['entonces']}   -> {r['descripcion']}")
print("\nHora '07:30' en minutos:", hora_a_minutos("07:30"))

titulo("4. VALIDACIÓN DE LA BASE DE CONOCIMIENTO")
errores = validar()
print("Sin errores: la base es coherente." if not errores else errores)

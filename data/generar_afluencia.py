# -*- coding: utf-8 -*-
"""
Generador del dataset de afluencia por estacion y franja horaria
del sistema Megabus (Pereira - Dosquebradas).

Actividad de aprendizaje NO supervisado: el dataset NO tiene columna de
etiqueta. El objetivo es que un algoritmo de agrupamiento descubra por si
solo los perfiles de uso de las estaciones a partir de su curva de demanda
a lo largo del dia.

No existe una fuente publica con conteos de validaciones por estacion para
el sistema Megabus, por lo que se construye una muestra sintetica sobre el
mismo grafo de estaciones de las actividades anteriores. Los arquetipos de
estacion usados para generar los datos quedan registrados en un archivo
aparte (perfiles_reales.csv) y se usan UNICAMENTE para validar a posteriori
el agrupamiento; nunca como entrada del modelo.

Uso:
    python generar_afluencia.py [--dias 30] [--semilla 42]
"""

import argparse
import csv
import math
import random

# --------------------------------------------------------------------------
# Estaciones del sistema. Cada una se genera a partir de un arquetipo latente
# que el algoritmo de agrupamiento debera redescubrir sin conocerlo.
#
#   residencial : la gente SALE en la manana y REGRESA en la tarde
#   laboral     : la gente LLEGA en la manana y SALE en la tarde
#   mixta       : flujo en ambos sentidos, con repunte al mediodia
#   intercambio : flujo alto y relativamente plano durante todo el dia
# --------------------------------------------------------------------------
# Cada entrada es (arquetipo, escala, desfase_horario, mezcla)
#   escala          : volumen relativo de pasajeros de la estacion
#   desfase_horario : corrimiento en horas de los picos propios de la estacion
#   mezcla          : (arquetipo_secundario, peso) para estaciones de caracter
#                     ambiguo, que son las que hacen el problema interesante
ESTACIONES = {
    "Cuba":           ("residencial", 1.00, -0.4, None),
    "Perla del Otun": ("residencial", 0.72,  0.3, None),
    "Travesuras":     ("residencial", 0.65,  0.6, None),
    "Insuperables":   ("residencial", 0.58, -0.2, ("mixta", 0.22)),
    "La Romelia":     ("residencial", 0.81,  0.5, None),
    "Los Molinos":    ("residencial", 0.63, -0.5, None),
    "Guadalupe":      ("residencial", 0.55,  0.8, None),
    "La Macarena":    ("residencial", 0.60,  0.1, ("intercambio", 0.18)),

    "Centro":         ("laboral", 1.00, -0.3, None),
    "Egoya":          ("laboral", 0.88,  0.2, ("intercambio", 0.25)),
    "Victoria":       ("laboral", 0.70,  0.5, None),
    "Jardin":         ("laboral", 0.62, -0.4, None),
    "Postobon":       ("laboral", 0.57,  0.7, ("mixta", 0.20)),

    "Universidad":    ("mixta", 0.92, -0.6, None),
    "Parque Olaya":   ("mixta", 0.78,  0.4, None),
    "San Fernando":   ("mixta", 0.61,  0.2, ("residencial", 0.28)),
    "Corales":        ("mixta", 0.69, -0.3, None),

    "Terminal":       ("intercambio", 0.95,  0.0, None),
    "Viaducto":       ("intercambio", 0.74,  0.4, ("laboral", 0.24)),
    "Dosquebradas":   ("intercambio", 1.00, -0.2, None),
}

HORAS = list(range(5, 23))          # de 05:00 a 22:00
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
CLIMAS = ["despejado", "nublado", "lluvia"]
PESOS_CLIMA = [0.58, 0.27, 0.15]

BASE_ABORDAJES = 420                # escala general de pasajeros por hora


def campana(hora, centro, ancho, altura):
    """Curva gaussiana usada para modelar un pico de demanda."""
    return altura * math.exp(-((hora - centro) ** 2) / (2 * ancho ** 2))


def perfil(arquetipo, hora):
    """
    Devuelve (factor_abordajes, factor_descensos) para una hora dada.
    Aqui viven los patrones latentes que el agrupamiento debe descubrir.
    """
    if arquetipo == "residencial":
        sub = campana(hora, 6.8, 1.15, 1.00) + campana(hora, 12.3, 1.5, 0.18)
        baj = campana(hora, 18.2, 1.35, 0.92) + campana(hora, 13.0, 1.6, 0.16)

    elif arquetipo == "laboral":
        sub = campana(hora, 17.9, 1.30, 0.98) + campana(hora, 12.6, 1.5, 0.30)
        baj = campana(hora, 7.2, 1.20, 1.00) + campana(hora, 13.2, 1.5, 0.26)

    elif arquetipo == "mixta":
        sub = (campana(hora, 7.4, 1.4, 0.55) + campana(hora, 12.5, 1.5, 0.62)
               + campana(hora, 18.0, 1.4, 0.58))
        baj = (campana(hora, 7.1, 1.4, 0.58) + campana(hora, 12.8, 1.5, 0.60)
               + campana(hora, 17.8, 1.4, 0.54))

    else:  # intercambio
        meseta = 0.52 if 7 <= hora <= 20 else 0.20
        sub = meseta + campana(hora, 7.0, 2.2, 0.26) + campana(hora, 18.0, 2.2, 0.28)
        baj = meseta + campana(hora, 7.3, 2.2, 0.27) + campana(hora, 17.8, 2.2, 0.26)

    return sub, baj


def flujo_base(hora):
    """
    Flujo minimo de pasajeros que toda estacion tiene a cualquier hora.
    Es menor en la primera y la ultima franja (5:00 y 22:00), cuando el
    servicio arranca y termina.

    CORRECCION (Actividad 3, Rol A): esta funcion faltaba en la version del
    generador que se recibio. Sin ella el script NO reproduce el archivo
    afluencia_megabus.csv entregado (aparecen miles de horas con 0 pasajeros
    y el ARI con k = 4 baja de 1,000 a 0,900). Con ella, el CSV generado con
    la semilla 42 es identico, valor por valor, al entregado.
    """
    return 0.02 if hora in (5, 22) else 0.05


def perfil_estacion(arquetipo, mezcla, desfase, hora):
    """
    Perfil efectivo de una estacion: su arquetipo principal desplazado en el
    tiempo y, si corresponde, mezclado con un arquetipo secundario, mas el
    flujo base de la franja.
    """
    h = hora - desfase
    sub, baj = perfil(arquetipo, h)
    if mezcla is not None:
        arq2, peso = mezcla
        sub2, baj2 = perfil(arq2, h)
        sub = (1 - peso) * sub + peso * sub2
        baj = (1 - peso) * baj + peso * baj2
    base = flujo_base(hora)
    return sub + base, baj + base


def factor_dia(dia, festivo):
    if festivo:
        return 0.44
    return {"sabado": 0.62, "domingo": 0.38}.get(dia, 1.00)


def factor_clima(clima):
    # La lluvia aumenta el uso del transporte publico
    return {"despejado": 1.00, "nublado": 1.03, "lluvia": 1.14}[clima]


def generar(dias, semilla):
    random.seed(semilla)
    filas = []
    fecha_base = 1          # dia 1 = lunes
    for d in range(dias):
        dia_nombre = DIAS[(fecha_base + d - 1) % 7]
        festivo = 1 if random.random() < 0.06 else 0
        clima_dia = random.choices(CLIMAS, weights=PESOS_CLIMA, k=1)[0]
        f_dia = factor_dia(dia_nombre, festivo)
        f_clima = factor_clima(clima_dia)

        for estacion, (arquetipo, escala, desfase, mezcla) in ESTACIONES.items():
            # Variacion propia de cada estacion entre un dia y otro
            jitter_est = random.uniform(0.85, 1.15)
            for hora in HORAS:
                f_sub, f_baj = perfil_estacion(arquetipo, mezcla, desfase, hora)
                ruido_s = random.uniform(0.62, 1.38)
                ruido_b = random.uniform(0.62, 1.38)

                sub = BASE_ABORDAJES * escala * f_sub * f_dia * f_clima * jitter_est * ruido_s
                baj = BASE_ABORDAJES * escala * f_baj * f_dia * f_clima * jitter_est * ruido_b

                filas.append({
                    "fecha_dia": d + 1,
                    "dia_semana": dia_nombre,
                    "es_festivo": festivo,
                    "clima": clima_dia,
                    "estacion": estacion,
                    "hora": hora,
                    "abordajes": max(0, int(round(sub))),
                    "descensos": max(0, int(round(baj))),
                })
    return filas


def main():
    ap = argparse.ArgumentParser(
        description="Genera el dataset de afluencia por estacion y hora.")
    ap.add_argument("--dias", type=int, default=30)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--salida", default="afluencia_megabus.csv")
    ap.add_argument("--perfiles", default="perfiles_reales.csv",
                    help="Arquetipo real de cada estacion. Solo para validar, "
                         "nunca como entrada del modelo.")
    args = ap.parse_args()

    filas = generar(args.dias, args.semilla)

    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    with open(args.perfiles, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["estacion", "arquetipo_real", "arquetipo_secundario"])
        for est, (arq, _, _, mez) in ESTACIONES.items():
            w.writerow([est, arq, mez[0] if mez else ""])

    total = sum(r["abordajes"] for r in filas)
    print(f"Archivo generado: {args.salida}")
    print(f"Registros: {len(filas)}  ({len(ESTACIONES)} estaciones x "
          f"{args.dias} dias x {len(HORAS)} horas)")
    print(f"Archivo de validacion: {args.perfiles}  "
          f"({len(ESTACIONES)} estaciones)")
    print(f"Abordajes totales simulados: {total:,}")


if __name__ == "__main__":
    main()

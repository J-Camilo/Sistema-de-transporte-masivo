"""
engine/inferencia.py - Motor de inferencia por encadenamiento hacia adelante
============================================================================
Integrante 2 | Base teórica: Capítulo 3

Contrato:
    construir_mapa(hora: str) -> (mapa, traza)

    mapa  : { (id_estacion, id_ruta): [((id_estacion, id_ruta), minutos), ...] }
    traza : lista con las reglas disparadas y la razón de su activación.

El motor no contiene el conocimiento del dominio: lo lee desde kb/reglas.py,
kb/conexiones.py y kb/estaciones.py. De esta forma se separan la base de
conocimiento y el mecanismo de razonamiento.
"""

from kb.conexiones import CONEXIONES, estaciones_de_transbordo
from kb.estaciones import ESTACIONES
from kb.reglas import REGLAS, hora_a_minutos


def _valor_comparable(nombre_hecho, valor):
    """Convierte horas HH:MM a minutos cuando la condición trabaja con 'hora'."""
    if nombre_hecho == "hora" and isinstance(valor, str):
        return hora_a_minutos(valor)
    return valor


def _comparar(hechos, condicion):
    """Evalúa una condición (hecho, operador, valor) contra los hechos actuales."""
    nombre, operador, esperado = condicion

    if nombre not in hechos:
        return False

    actual = hechos[nombre]

    # Un valor como "$ruta_salida" significa comparar contra otro hecho.
    if isinstance(esperado, str) and esperado.startswith("$"):
        otro_hecho = esperado[1:]
        if otro_hecho not in hechos:
            return False
        esperado = hechos[otro_hecho]

    if operador == "entre":
        inicio, fin = esperado
        actual = _valor_comparable(nombre, actual)
        inicio = _valor_comparable(nombre, inicio)
        fin = _valor_comparable(nombre, fin)
        return inicio <= actual < fin

    actual = _valor_comparable(nombre, actual)
    esperado = _valor_comparable(nombre, esperado)

    if operador == "==":
        return actual == esperado
    if operador == "!=":
        return actual != esperado
    if operador == "<":
        return actual < esperado
    if operador == ">=":
        return actual >= esperado

    raise ValueError(f"Operador no soportado: {operador}")


def _se_cumple(regla, hechos):
    """Una regla se cumple únicamente si TODAS sus condiciones son verdaderas."""
    return all(_comparar(hechos, condicion) for condicion in regla["si"])


def _registrar(traza, arco, regla, tipo, **datos):
    """Agrega a la traza una explicación de una regla disparada."""
    registro = {
        "arco": arco,
        "regla": regla["id"],
        "descripcion": regla["descripcion"],
        "tipo": tipo,
    }
    registro.update(datos)
    traza.append(registro)


def _deducir(hechos, arco, traza):
    """
    Ejecuta encadenamiento hacia adelante hasta alcanzar un punto fijo.

    Cada regla de deducción que se cumple puede agregar un hecho nuevo. Luego se
    vuelven a revisar las reglas porque ese nuevo hecho podría habilitar otras.
    El proceso termina cuando una pasada completa no agrega conocimiento nuevo.
    """
    reglas = [r for r in REGLAS if r["tipo"] == "deduccion"]

    cambio = True
    while cambio:
        cambio = False

        for regla in reglas:
            if not _se_cumple(regla, hechos):
                continue

            accion = regla["entonces"]
            if accion[0] != "agregar_hecho":
                raise ValueError(f"Acción de deducción inválida en {regla['id']}: {accion}")

            _, nombre, valor = accion

            # Solo es una deducción nueva si el hecho todavía no tiene ese valor.
            if hechos.get(nombre) == valor:
                continue

            anterior = hechos.get(nombre)
            hechos[nombre] = valor
            cambio = True

            _registrar(
                traza,
                arco,
                regla,
                "deduccion",
                hecho=nombre,
                valor_anterior=anterior,
                valor_nuevo=valor,
            )

    return hechos

def _aplicar_ajustes(hechos, minutos_base, arco, traza):
    """
    Aplica las reglas de ajuste en el orden acordado:
      1. bloquear
      2. multiplicar
      3. sumar

    Devuelve None si el arco queda bloqueado; de lo contrario devuelve minutos.
    """
    reglas = [r for r in REGLAS if r["tipo"] == "ajuste" and _se_cumple(r, hechos)]

    prioridad = {"bloquear": 0, "multiplicar": 1, "sumar": 2}
    reglas.sort(key=lambda r: prioridad.get(r["entonces"][0], 99))

    tiempo = float(minutos_base)

    for regla in reglas:
        accion = regla["entonces"]
        tipo_accion = accion[0]

        if tipo_accion == "bloquear":
            _registrar(
                traza, arco, regla, "ajuste",
                accion="bloquear", antes=tiempo, despues=None,
            )
            return None

        antes = tiempo

        if tipo_accion == "multiplicar":
            tiempo *= accion[1]
        elif tipo_accion == "sumar":
            tiempo += accion[1]
        else:
            raise ValueError(f"Acción de ajuste inválida en {regla['id']}: {accion}")

        _registrar(
            traza, arco, regla, "ajuste",
            accion=tipo_accion,
            antes=round(antes, 4),
            despues=round(tiempo, 4),
        )

    return round(tiempo, 4)


def _procesar_arco(origen, destino, ruta_llegada, ruta_salida,
                    minutos_base, hora_minutos, tipo_arco, traza):
    """Crea los hechos de un arco, ejecuta inferencia y calcula su costo final."""
    estacion_reglas = destino if tipo_arco == "tramo" else origen
    datos_estacion = ESTACIONES[estacion_reglas]

    hechos = {
        "tipo_arco": tipo_arco,
        "ruta_llegada": ruta_llegada,
        "ruta_salida": ruta_salida,
        "estacion": estacion_reglas,
        "tipo_estacion": datos_estacion["tipo"],
        "zona_destino": datos_estacion["zona"],
        "hora": hora_minutos,
        "minutos_base": minutos_base,
    }

    etiqueta = (
        f"({origen}, {ruta_llegada}) -> ({destino}, {ruta_salida})"
    )

    _deducir(hechos, etiqueta, traza)
    return _aplicar_ajustes(hechos, minutos_base, etiqueta, traza)


def construir_mapa(hora):
    """
    Construye el mapa final que utilizará A*.

    1. Convierte la hora a minutos.
    2. Procesa cada tramo real de CONEXIONES.
    3. Crea arcos de transbordo donde coinciden dos o más rutas.
    4. Ejecuta las reglas sobre cada arco.
    5. Omite los arcos bloqueados.
    6. Devuelve (mapa, traza).
    """
    hora_minutos = hora_a_minutos(hora)
    mapa = {}
    traza = []

    def agregar_arco(nodo_origen, nodo_destino, minutos):
        mapa.setdefault(nodo_origen, []).append((nodo_destino, minutos))
        # También registramos el destino como nodo, aunque no tenga salidas.
        mapa.setdefault(nodo_destino, [])

    # ---------------------------------------------------------
    # 1. Arcos de tramo: viajar entre estaciones por misma ruta
    # ---------------------------------------------------------
    for conexion in CONEXIONES:
        origen = conexion["origen"]
        destino = conexion["destino"]
        ruta = conexion["ruta"]

        minutos = _procesar_arco(
            origen=origen,
            destino=destino,
            ruta_llegada=ruta,
            ruta_salida=ruta,
            minutos_base=conexion["minutos"],
            hora_minutos=hora_minutos,
            tipo_arco="tramo",
            traza=traza,
        )

        if minutos is not None:
            agregar_arco((origen, ruta), (destino, ruta), minutos)

    # ---------------------------------------------------------
    # 2. Arcos de transbordo: misma estación, diferente ruta
    # ---------------------------------------------------------
    for estacion, rutas in estaciones_de_transbordo().items():
        rutas = sorted(rutas)

        for ruta_llegada in rutas:
            for ruta_salida in rutas:
                if ruta_llegada == ruta_salida:
                    continue

                minutos = _procesar_arco(
                    origen=estacion,
                    destino=estacion,
                    ruta_llegada=ruta_llegada,
                    ruta_salida=ruta_salida,
                    minutos_base=0,
                    hora_minutos=hora_minutos,
                    tipo_arco="transbordo",
                    traza=traza,
                )

                if minutos is not None:
                    agregar_arco(
                        (estacion, ruta_llegada),
                        (estacion, ruta_salida),
                        minutos,
                    )

    return mapa, traza

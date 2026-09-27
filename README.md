# Planificador de rutas Megabús (Sistema experto + A*)

```
megabus/
├── kb/                 Integrante 1 – Base de conocimiento
│   ├── estaciones.py   37 estaciones con coordenadas, tipo y zona
│   ├── conexiones.py   Rutas R1, R2, R3 y sus tramos con minutos
│   └── reglas.py       12 reglas SI...ENTONCES (6 de deducción, 6 de ajuste)
├── engine/
│   └── inferencia.py   Integrante 2 – Motor de inferencia (encadenamiento hacia adelante)
├── search/
│   └── astar.py        Integrante 3 – Búsqueda A* (y comparación con Dijkstra)
├── tests/
│   ├── test_kb.py      Pruebas de la base de conocimiento
│   ├── test_astar.py   Pruebas de A* con un mapa falso
│   └── test_main.py    Pruebas de integración (motor real + consola)
├── demo_kb.py          Demostración de la base de conocimiento
├── main.py             Integrante 3 – Interfaz por consola
└── GUION_INTEGRANTE3.md Guion del video (Integrante 3)
```

Requisitos: Python 3.8+. No hay librerías externas, así que `pip install -r requirements.txt` no instala nada.

```
python main.py --origen "Cuba" --destino "Dosquebradas" --hora 07:30
python main.py                        # pregunta origen, destino y hora
python main.py --listar               # lista las estaciones disponibles
python demo_kb.py                     # demostración para el video (Integrante 1)
python -m unittest discover tests     # corre las pruebas
```

El contrato entre los tres módulos está documentado en la cabecera de
`kb/reglas.py`, `engine/inferencia.py` y `search/astar.py`.

## Ejemplo de ejecución

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 07:30
```
```
  1. Parque Olaya -> Maraya ..................... R1 ... 9.8 min
  2. TRANSBORDO en Maraya (R1 -> R2) .................. +5.0 min
  3. Maraya -> Egoyá ............................ R2 ... 3.4 min
TIEMPO TOTAL: 18.2 min (hora pico aplicada)
REGLAS: D1, A2, A3, D3, A4
BÚSQUEDA: A* revisó 20 nodos | Dijkstra revisó 27 nodos
```

Cómo se lee:

| Línea | Significado |
|---|---|
| 1 y 3 | Tramos en bus. Las estaciones seguidas en la misma ruta se agrupan en una línea. |
| 2 | Cambio de ruta dentro de la estación: +5 min (regla A4). |
| TIEMPO TOTAL | g(n) del destino: la suma de los minutos de todos los arcos. |
| D1 | 07:30 está entre 6:00 y 8:00, así que es hora pico. |
| A2 | En hora pico cada tramo tarda un 40 % más. |
| A3 | Egoyá queda en el centro: otro 20 % más. |
| D3 | Se llega por R1 y se sale por R2, así que hay transbordo. |
| A4 | Un transbordo en una estación normal suma 5 min. |
| BÚSQUEDA | Nodos que revisó cada algoritmo. A* encuentra el mismo tiempo revisando menos nodos. |

A las 10:00 la misma consulta da 14.0 min: sin hora pico solo se activan D3 y A4.
Códigos de salida: `0` hay ruta, `1` dato inválido, `2` no hay ruta (ej. `--hora 03:00`, sistema cerrado).

## Integrante 3: búsqueda A* e interfaz (capítulo 9)

| Tarea | Dónde |
|---|---|
| A* sobre el mapa del motor de inferencia | `search/astar.py` → `buscar()` |
| g(n) = minutos acumulados + transbordos | Los costos del mapa ya traen las penalizaciones del motor. A* solo los suma. |
| h(n) = distancia en línea recta / velocidad del bus | `search/astar.py` → `heuristica()` |
| Interfaz por consola | `main.py` (argumentos, o pregunta los datos si faltan) |
| Casos de prueba | `tests/test_astar.py` y `tests/test_main.py` (18 pruebas) |
| Extra: A* contra Dijkstra | `search/astar.py` → `comparar()` (Dijkstra es A* con h = 0) |

**¿Por qué h(n) nunca sobreestima?** La línea recta es la distancia más corta posible, y se divide
por la velocidad **máxima** del bus (60 km/h), no por la promedio. El resultado es el tiempo más
optimista posible, así que nunca supera el tiempo real. Con una heurística así (admisible), A* garantiza
la ruta óptima. Si se usara la velocidad promedio, h(n) podría pasarse en los tramos rápidos.

Los nodos del mapa son pares `(estación, ruta)`. Por eso la búsqueda arranca desde todas las rutas
que pasan por la estación de origen y termina en cualquier ruta que llegue a la estación de destino.

| Caso de prueba | Prueba |
|---|---|
| Misma ruta | `test_misma_ruta_sin_transbordo` |
| Con transbordo | `test_con_transbordo_si_sale_mas_barato` |
| Hora pico | `test_hora_pico_tarda_mas_que_hora_valle` |
| Origen = destino | `test_origen_igual_a_destino` |
| Estación inexistente | `test_estacion_que_no_existe` |
| Ruta imposible | `test_ruta_imposible`, `test_sistema_cerrado_ruta_imposible` |

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
└── main.py             Integrante 3 – Interfaz por consola
```

Requisitos: Python 3.8+ (sin librerías externas).

```
python main.py --origen "Cuba" --destino "Dosquebradas" --hora 07:30
python main.py                        # pregunta origen, destino y hora
python main.py --listar               # lista las estaciones disponibles
python demo_kb.py                     # demostración para el video (Integrante 1)
python -m unittest discover tests     # corre las pruebas
```

El contrato entre los tres módulos está documentado en la cabecera de
`kb/reglas.py`, `engine/inferencia.py` y `search/astar.py`.

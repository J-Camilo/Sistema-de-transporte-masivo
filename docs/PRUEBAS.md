# Documento de pruebas

Planificador de rutas Megabús (Sistema experto + A*).

## Cómo se corren

Desde la raíz del repositorio (Python 3.8+, sin librerías externas):

```
python -m unittest discover -s src/tests -t src -v
```

Resultado actual: **27 pruebas, 27 correctas**.

| Archivo | Qué prueba | Pruebas |
|---|---|---|
| [src/tests/test_kb.py](../src/tests/test_kb.py) | Base de conocimiento (Integrante 1) | 8 |
| [src/tests/test_astar.py](../src/tests/test_astar.py) | Búsqueda A* sobre un mapa falso (Integrante 3) | 8 |
| [src/tests/test_main.py](../src/tests/test_main.py) | Integración: motor de inferencia real + consola + reporte HTML | 11 |

## 1. Base de conocimiento — `test_kb.py`

| # | Prueba | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | `test_base_coherente` | `validar()` | Sin errores: toda conexión apunta a estaciones que existen |
| 2 | `test_buscar_estacion_con_y_sin_tildes` | "Egoyá", "egoya", "intercambiador cuba" | Encuentra `egoya` y `cuba` |
| 3 | `test_estacion_inexistente` | "Estación Marte" | `None` |
| 4 | `test_maraya_es_punto_de_transbordo` | Maraya | Pasan R1, R2 y R3 |
| 5 | `test_ruta3_no_llega_a_dosquebradas` | Dosquebradas | R3 no pasa por ahí |
| 6 | `test_distancia_cero_a_si_misma` | Cuba → Cuba | 0 km |
| 7 | `test_hora_a_minutos` | "07:30" y "25:00" | 450 minutos; "25:00" lanza `ValueError` |
| 8 | `test_reglas_bien_formadas` | Las 12 reglas | Ids únicos, tipo `deduccion` o `ajuste`, con SI / ENTONCES / descripción |

## 2. Búsqueda A* — `test_astar.py`

Usa un mapa falso pequeño para saber de antemano la respuesta correcta:

```
Cuba (R1) --20--> Maraya (R1) --2--> El Jardín (R1)
Cuba (R2) --10--> Maraya (R2) --6--> El Lago (R2)
Maraya R1 <--5--> Maraya R2   (transbordo)
Libertad (R3)                  (aislada)
```

| # | Caso | Prueba | Resultado esperado |
|---|---|---|---|
| 1 | Misma ruta | `test_misma_ruta_sin_transbordo` | Cuba → El Lago por R2, 16 min |
| 2 | Con transbordo | `test_con_transbordo_si_sale_mas_barato` | Cuba → El Jardín: R2 + transbordo en Maraya = 17 min (directo por R1 serían 22) |
| 3 | Origen = destino | `test_origen_igual_a_destino` | Camino vacío, 0 min |
| 4 | Ruta imposible | `test_ruta_imposible` | Cuba → Libertad: `(None, None)` |
| 5 | Sistema cerrado | `test_mapa_vacio_sistema_cerrado` | Mapa vacío: `(None, None)` |
| 6 | Heurística en el destino | `test_heuristica_cero_en_el_destino` | h = 0 |
| 7 | Heurística admisible | `test_heuristica_nunca_supera_el_costo_real` | h(n) ≤ costo real para todos los pares |
| 8 | A* contra Dijkstra | `test_dijkstra_da_el_mismo_costo_y_revisa_mas_o_igual_nodos` | Mismo costo; A* revisa igual o menos nodos |

## 3. Integración — `test_main.py`

Usa el motor de inferencia y la base de conocimiento reales.

| # | Caso | Prueba | Entrada | Resultado esperado |
|---|---|---|---|---|
| 1 | Consulta válida | `test_consulta_valida` | Cuba → Dosquebradas, 10:00 | Código 0, muestra RUTA RECOMENDADA y TIEMPO TOTAL |
| 2 | Tildes y mayúsculas | `test_acepta_nombres_con_tildes_y_mayusculas` | "EGOYÁ" → "el lago" | Código 0 |
| 3 | Estación inexistente | `test_estacion_que_no_existe` | "Estación Marte" | Código 1, mensaje "no existe" |
| 4 | Hora inválida | `test_hora_invalida` | 25:00 | Código 1 |
| 5 | Origen = destino | `test_origen_igual_a_destino` | Maraya → Maraya | Código 0, mensaje "Ya estás" |
| 6 | Ruta imposible | `test_sistema_cerrado_ruta_imposible` | Cuba → Dosquebradas, 03:00 | Código 2, se cita la regla A1 (sistema cerrado) |
| 7 | Reporte HTML | `test_html_se_genera_y_se_abre_en_el_navegador` | Parque Olaya → Egoyá, 07:30, `--html` | Genera `resultado.html` con el transbordo en Maraya y la hora pico, y lo abre |
| 8 | Hora pico | `test_hora_pico_tarda_mas_que_hora_valle` | Cuba → Dosquebradas a 07:30 y 10:00 | En hora pico tarda más |
| 9 | Heurística consistente | `test_heuristica_consistente_en_el_mapa_real` | Todos los arcos a varias horas | h(a) ≤ costo(a, b) + h(b) |
| 10 | Resumen del camino | `test_resumen_marca_los_transbordos` | Camino con cambio de ruta | Pasos: tramo, transbordo (+5 min), tramo |
| 11 | Reglas aplicadas | `test_reglas_del_camino_solo_incluye_arcos_usados` | Cuba → Maraya, 07:30 | Aparecen D1 y A2; no aparece A3 (no pasa por el centro) |

## Códigos de salida de la consola

| Código | Significado |
|---|---|
| 0 | Hay ruta (o origen = destino) |
| 1 | Dato inválido (estación u hora) |
| 2 | No hay ruta (por ejemplo, sistema cerrado a las 03:00) |

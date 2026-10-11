# Documento de pruebas del modelo

Actividad 2: aprendizaje supervisado con un árbol de decisión sobre los datos del Megabús.
Rol C: evaluación del modelo e integración con el motor de inferencia de la Actividad 1.

## Cómo reproducir los resultados

Desde la raíz del repositorio:

```
pip install -r requirements.txt
python src/ml/arbol.py               # Rol B: escoge la profundidad, entrena y guarda resultados/modelo_arbol.joblib
python src/ml/extraer_reglas.py      # Rol B: crea docs/reglas_aprendidas.txt
python src/ml/evaluacion.py          # Rol C: métricas, validación cruzada, comparación e integración
python -m unittest discover -s src/tests -t src     # pruebas automáticas (sin scikit-learn)
```

Todo usa la semilla `42`, así que los resultados se pueden repetir. Los datos son los de `data/viajes_megabus.csv`, con las 37 estaciones de la Actividad 1 (ver [descripcion_datos.md](descripcion_datos.md)).

El árbol usa `criterion="entropy"` y `max_depth=7`. Esa profundidad la escogió el Rol B con validación cruzada sobre el conjunto de entrenamiento ([comparacion_profundidades.png](../resultados/comparacion_profundidades.png)).

| Conjunto | Viajes |
|---|---|
| Entrenamiento (70 %, estratificado) | 2.800 |
| Prueba (30 %, estratificado) | 1.200 |
| Columnas después de `get_dummies()` | 92 |

`id_viaje` y `tiempo_real_min` no entran al modelo. La segunda delata la respuesta.

---

## 1. Métricas del árbol sobre el conjunto de prueba

**Accuracy: 80,3 %**, es decir, 964 de 1.200 viajes bien clasificados.

| Clase | Precisión | Recall | F1 | Viajes de prueba |
|---|---|---|---|---|
| baja | 84,5 % | 85,9 % | 85,2 % | 512 |
| media | 75,4 % | 81,5 % | 78,3 % | 417 |
| alta | 80,7 % | 67,9 % | 73,7 % | 271 |
| **Promedio macro** | **80,2 %** | **78,5 %** | **79,1 %** | 1.200 |

Cómo se leen:

- **Precisión**: de los viajes que el árbol marcó con esa clase, cuántos eran de verdad de esa clase.
- **Recall**: de los viajes que eran de esa clase, cuántos encontró el árbol.
- **F1**: combina precisión y recall en un solo número (promedio armónico). Solo es alto si las dos lo son.

### Matriz de confusión

![Matriz de confusión](figuras/06_matriz_confusion.png)

| Real \ Predicho | baja | media | alta |
|---|---|---|---|
| **baja** | **440** | 56 | 16 |
| **media** | 49 | **340** | 28 |
| **alta** | 32 | 55 | **184** |

**Análisis**

- **El árbol es prudente con la clase alta.** Cuando dice "alta" casi siempre acierta (precisión de 80,7 %), pero se le escapan 87 de los 271 viajes con demora alta (recall de 67,9 %). Es la clase con menos ejemplos (22,6 % del dataset), así que tiene menos casos de los que aprender.
- **La mayoría de los errores caen en la clase vecina.** De los viajes con demora alta que falla, 55 los clasifica como media. Sin embargo, 32 los manda directo a baja, y eso no lo explica la cercanía entre clases. Ahí aparece el **12 % de ruido** que mete el generador (`PROB_RUIDO = 0.12`): cambia la etiqueta por cualquier otra clase, y ningún modelo puede acertar esos viajes.
- **Techo teórico.** Si el 12 % de las etiquetas es aleatorio, el máximo esperable ronda el **88 %**. El árbol (80 %) está a 8 puntos de ese techo.

---

## 2. Validación cruzada (5 particiones)

Un solo corte 70/30 podría dar un buen resultado por suerte. Por eso se usa `StratifiedKFold(n_splits=5, shuffle=True)` sobre los 4.000 viajes: en cada partición el árbol se entrena desde cero y se prueba con datos que no vio.

| Partición | 1 | 2 | 3 | 4 | 5 | **Media** | **Desviación** |
|---|---|---|---|---|---|---|---|
| Árbol (profundidad 7) | 80,1 % | 78,1 % | 81,9 % | 81,6 % | 79,1 % | **80,2 %** | **1,4 %** |

Las cinco particiones quedan entre 78 % y 82 %, y la media (80,2 %) coincide con el acierto del corte 70/30 (80,3 %). El resultado es **estable**: no depende de qué viajes caen en la prueba.

### ¿La profundidad 7 está bien escogida?

El Rol B hizo la validación cruzada solo con el 70 % de entrenamiento, y la mejor profundidad le salió 7. Para confirmarlo, aquí se repite con los 4.000 viajes, sin mirar el acierto en prueba:

| Profundidad | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|
| CV media | 62,1 % | 69,3 % | 76,0 % | 78,2 % | **80,2 %** | 81,5 % | 81,7 % | 81,4 % | 80,6 % | 79,6 % |

- **Hasta la profundidad 7, el árbol mejora rápido.** Después se forma una meseta entre 7 y 10. La profundidad 9 gana apenas 1,5 puntos, lo mismo que la desviación entre particiones (1,4 %), así que no es una mejora clara.
- **La profundidad 7 sale más barata en reglas.** Con 7 el árbol produce **93 reglas**; con 9 produciría más de 200. Como el objetivo es extraer reglas legibles, el árbol más chico es la mejor elección.
- **Desde la profundidad 11, el acierto baja.** El árbol empieza a **memorizar el ruido**. El caso extremo es el árbol sin podar: llega a profundidad 24 con 567 hojas, acierta el 100 % en entrenamiento y baja a **76,1 %** en prueba. Es el ejemplo de libro del sobreajuste.

---

## 3. Comparación contra las referencias

![Comparación de modelos](figuras/07_comparacion_modelos.png)

| Modelo | Entrenamiento | Prueba (30 %) | CV media | CV desviación |
|---|---|---|---|---|
| Línea base (`DummyClassifier`, siempre dice "baja") | 42,6 % | 42,7 % | 42,7 % | 0,0 % |
| **Árbol de decisión (profundidad 7)** | 83,6 % | **80,3 %** | **80,2 %** | 1,4 % |
| `RandomForest` con 200 árboles (configuración por defecto) | 100,0 % | 73,2 % | 74,8 % | 2,0 % |
| `RandomForest` con 200 árboles (`max_features=None`) | 100,0 % | 81,5 % | 83,3 % | 1,7 % |

**Análisis**

1. **Contra la línea base.** El `DummyClassifier` siempre responde la clase más frecuente y acierta 42,7 %. El árbol casi **duplica** ese acierto (+37,5 puntos), así que aprendió algo real de los datos y no se limita a adivinar la clase mayoritaria.
2. **Con la configuración por defecto, el RandomForest salió PEOR que el árbol (74,8 % contra 80,2 %).** No era lo esperado. La explicación es interesante en sí misma:
   - Por defecto, en cada división el bosque mira solo `sqrt(92) ≈ 9` columnas escogidas al azar.
   - De las 92 columnas, **74 son estaciones** (`estacion_origen_*` y `estacion_destino_*`), y las estaciones casi no influyen en la demora.
   - Por eso muchas divisiones no ven `tiempo_base_min`, `hora` ni `clima`, y terminan partiendo por estación.
   - Con `max_features=None` (cada división mira todas las columnas), el bosque sube a **83,3 %** y supera al árbol por 3 puntos.
3. **Árbol contra bosque.** Bien configurado, el bosque gana 3 puntos, pero son 200 árboles votando: **no se puede leer** ni convertir en reglas. El árbol sacrifica esos 3 puntos y a cambio da reglas SI... ENTONCES... que una persona entiende y que el motor de la Actividad 1 puede ejecutar (sección 4). Para este proyecto vale más la interpretabilidad.

---

## 4. Integración: reglas aprendidas dentro del motor de la Actividad 1

En la Actividad 1, el motor de inferencia (`src/engine/inferencia.py`) razonaba con reglas escritas a mano (`src/kb/reglas.py`). Ahora las reglas las escribió el árbol. El módulo [`src/ml/integracion.py`](../src/ml/integracion.py) hace tres cosas:

1. Lee `docs/reglas_aprendidas.txt`, que es la salida de `export_text()` del Rol B. Cada camino de la raíz a una hoja es una regla.
2. Traduce cada regla al **mismo formato de `kb/reglas.py`** (`id`, `tipo`, `si`, `entonces` y `descripcion`):

   | Condición del árbol | Condición del motor |
   |---|---|
   | `clima_lluvia > 0.500` | `("clima", "==", "lluvia")` |
   | `clima_lluvia <= 0.500` | `("clima", "!=", "lluvia")` |
   | `hora > 16.500` y `hora <= 19.500` | `("hora", "entre", ("17:00", "20:00"))` |
   | `es_festivo <= 0.500` | `("es_festivo", "==", 0)` |
   | `tiempo_base_min > 7.980` | `("tiempo_base_min", ">=", 7.98)` |

   La conclusión de cada regla queda como `("agregar_hecho", "nivel_demora", "alta")`.

3. Ejecuta el **encadenamiento hacia adelante del mismo motor** (`inferencia._deducir`) con las reglas de la Actividad 1 **más** las aprendidas. En la misma traza aparecen juntas las reglas escritas a mano (D1, D2...) y las aprendidas (ML1, ML2...).

El código del motor **no se modificó**. Las reglas aprendidas solo se agregan a la base de conocimiento mientras dura la inferencia, así que el cálculo de rutas de la Actividad 1 sigue igual.

### Prueba de fidelidad: el motor reproduce al árbol

Se cargaron en el motor **las 93 reglas** del árbol y se le pidió la demora de los 1.200 viajes de prueba.

> El motor y el árbol coinciden en **1.200 de 1.200 viajes (100 %)**.

La traducción es **exacta**: el árbol completo se convirtió en una base de conocimiento que el sistema experto ejecuta sin perder nada.

### Las 4 reglas que se muestran en el sistema

`seleccionar()` escoge 4 de las 93 reglas con estos criterios:

- que acierten al menos el 75 % de los viajes que cubren;
- que no exijan una estación concreta (`estacion_X = ...`), porque esos son casos sueltos que el árbol memorizó;
- que cubran la mayor cantidad de viajes, con al menos una regla por clase cuando se pueda.

| Regla | SI... | ENTONCES demora | Viajes que cubre (dataset completo) | Acierto en el dataset completo | Viajes de prueba que cubre | Acierto en prueba |
|---|---|---|---|---|---|---|
| ML1 | tiempo base < 5,35 min Y hora entre 09:00 y 17:00 Y clima ≠ lluvia (además, origen ≠ Egoyá y día ≠ jueves) | **baja** | 413 | 89 % | 137 | 87,6 % |
| ML2 | tiempo base < 7,11 min Y hora entre 17:00 y 20:00 Y de lunes a viernes Y no festivo | **media** | 332 | 83 % | 89 | 82,0 % |
| ML3 | tiempo base ≥ 7,98 min Y hora entre 17:00 y 20:00 Y de lunes a viernes | **alta** | 328 | 86 % | 105 | 84,8 % |
| ML4 | tiempo base ≥ 7,11 min Y hora entre 06:00 y 09:00 Y de lunes a viernes Y no festivo (además, origen ≠ San Fernando) | **alta** | 248 | 89 % | 73 | 87,7 % |

Las reglas tienen sentido. **ML3** y **ML4** dicen que un viaje largo en la hora pico de la tarde o de la mañana, entre semana, tiene demora alta. Es la misma idea de las reglas D1, D2 y A2 que escribimos a mano en la Actividad 1, pero esta vez **el árbol la descubrió solo, a partir de los datos**.

### Demostración: el sistema de la Actividad 1 con reglas aprendidas

`integracion.py` busca la ruta con A*, igual que `main.py`, y después le pregunta al motor la demora del viaje:

```
python src/ml/integracion.py --origen "Cuba" --destino "Dosquebradas" --hora 18:00 --dia miercoles
```

```
RUTA RECOMENDADA  (Intercambiador Cuba -> Intercambiador Dosquebradas, 18:00)
  1. Intercambiador Cuba -> Intercambiador Dosquebradas . R1 ... 40.6 min
TIEMPO TOTAL: 40.6 min (hora pico aplicada)
...
HECHOS DEL VIAJE: ..., tiempo_base_min=23.97, hora=18:00
  [D2] a mano    Entre 17:00 y 19:30 es hora pico de la tarde
  [ML3] APRENDIDA tiempo base min >= 7.98 Y hora entre 17:00 y 20:00 Y dia semana != domingo Y dia semana != sabado -> demora alta

DEMORA ESPERADA: ALTA (deducida por una regla que nadie escribió a mano)
```

Al cambiar el viaje o la hora, el motor dispara otra regla aprendida:

| Comando (`python src/ml/integracion.py ...`) | Reglas que se disparan | Demora |
|---|---|---|
| `--origen "Cuba" --destino "Dosquebradas" --hora 18:00 --dia miercoles` | D2 (a mano) + **ML3** | alta |
| `--origen "Cuba" --destino "Dosquebradas" --hora 07:30 --dia lunes` | D1 (a mano) + **ML4** | alta |
| `--origen "Maraya" --destino "Egoyá" --hora 12:30 --dia martes` | **ML1** | baja |
| `--origen "Maraya" --destino "Egoyá" --hora 18:00 --dia miercoles` | D2 (a mano) + **ML2** | media |
| `--origen "Cuba" --destino "Dosquebradas" --hora 12:30 --dia martes` | ninguna | ninguna de las 4 aplica |
| igual al anterior, más `--todas` | una de las 93 (ML69) | media |

Los dos últimos casos muestran el límite de cargar solo 4 reglas: cubren un tercio de los viajes de prueba (404 de 1.200). Con `--todas`, el motor siempre llega a una respuesta, y es la misma que da el árbol.

---

## 5. Pruebas automáticas

[`src/tests/test_integracion.py`](../src/tests/test_integracion.py) tiene 19 pruebas de la integración. Usan un árbol pequeño escrito a mano con el formato de `export_text()`, así que **no necesitan scikit-learn** ni el modelo entrenado.

| Grupo | Qué se comprueba |
|---|---|
| Lectura de `export_text()` (3) | Cada hoja es una regla; cada regla guarda el camino desde la raíz; los nombres de columna con espacios (`estacion_destino_San Fernando`) se leen bien. |
| Traducción (8) | Columnas dummy a `==` o `!=`; hora a `HH:MM`; `es_festivo` a 0/1; columnas numéricas; condiciones repetidas que se juntan en un solo rango `entre`; un `==` que vuelve innecesarios los `!=`; formato de `kb/reglas.py`. |
| Motor con reglas aprendidas (5) | El motor deduce `nivel_demora`; las reglas de la Actividad 1 (D2) siguen disparándose; si ninguna regla aplica, no hay conclusión; `kb/reglas.py` queda intacto después de inferir. |
| Selección (3) | Soporte y acierto de una regla; se descartan las reglas que exigen una estación concreta; se ordenan por soporte. |

```
python -m unittest discover -s src/tests -t src
Ran 46 tests ... OK
```

Son 46 pruebas: las 27 de la Actividad 1 siguen pasando y se agregan las 19 nuevas.

---

## 6. Limitaciones

- **Los datos son sintéticos.** El árbol aprende las reglas del generador (`data/generar_dataset.py`), no el tráfico real de Pereira. Las métricas miden qué tan bien el árbol recupera la regla oculta del generador, no qué tan bien predeciría el Megabús real.
- **El acierto tiene un techo cercano al 88 %**, porque el 12 % de las etiquetas se cambiaron a propósito.
- **Algunos hechos los pone el usuario.** El motor de la Actividad 1 no conoce ni el clima ni el día, así que en la demostración se pasan con `--clima` y `--dia`. `tiempo_base_min` se calcula con la misma fórmula del generador (distancia en línea recta ÷ 21 km/h + 5 min por transbordo) y no sale de los minutos de `kb/conexiones.py`.
- **Las 4 reglas escogidas dependen del entrenamiento.** Si cambian los datos, la profundidad o la semilla, `reglas_aprendidas.txt` cambia y la selección también. Los números de este documento corresponden a profundidad 7 y semilla 42.

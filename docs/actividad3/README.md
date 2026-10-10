# Actividad 3 — Agrupamiento de estaciones del Megabús

Aprendizaje **no supervisado**: se agrupan las 20 estaciones según la forma de su curva de abordajes y descensos a lo largo del día, sin darle al algoritmo ninguna etiqueta.

> ⚠️ **`data/perfiles_reales.csv` NO es una entrada del modelo.** Contiene el tipo real de cada estación y solo se usa al final para validar (`src/cluster/validacion.py`). Si se mete en la matriz de entrada, el ejercicio deja de ser no supervisado.

## Archivos

| Ruta | Qué es |
|---|---|
| `data/afluencia_megabus.csv` | 10.800 registros sintéticos (20 estaciones × 30 días × 18 horas). Entrada principal. |
| `data/perfiles_reales.csv` | Tipo real de cada estación. **Solo validación.** |
| `data/generar_afluencia.py` | Generador de los dos CSV (semilla 42). |
| `src/cluster/preparacion.py` | Rol A: matriz 20 × 36 normalizada por fila. |
| `src/cluster/exploracion.py` | Rol A: gráficas de exploración. |
| `src/cluster/seleccion_k.py` | Rol B: estandarización y K-means para k = 2 a 8. |
| `src/cluster/kmeans_modelo.py` | Rol B: K-means con k = 4 y `grupos_encontrados.csv`. |
| `src/cluster/visualizacion.py` | Rol B: codo, silueta y PCA. |
| `src/cluster/jerarquico.py` | Rol C: Ward y dendrograma. |
| `src/cluster/validacion.py` | Rol C: comparación, DBSCAN, interpretación y validación final. |
| `src/cluster/ejecutar_todo.py` | Ejecuta todo el flujo en orden. |
| `src/cluster/estilo.py` | Colores y formato comunes de las gráficas. |
| `tests/test_cluster.py` | 8 pruebas automáticas. |
| `docs/actividad3/descripcion_datos.md` | Entregable 3: descripción de los datos. |
| `docs/actividad3/pruebas_modelo.md` | Entregable 4: pruebas realizadas. |
| `docs/actividad3/grupos_encontrados.csv` | Grupo de cada estación. |
| `docs/actividad3/figuras/` | 8 gráficas. |
| `docs/actividad3/resultados/` | Tablas intermedias (métricas, matriz, DBSCAN, etc.). |

Los documentos de esta actividad están en `docs/actividad3/` para no reemplazar `docs/descripcion_datos.md` de la Actividad 2.

## Cómo ejecutar (Windows, terminal de VS Code, en la raíz del repositorio)

```
py -m pip install -r requirements.txt
py -m src.cluster.ejecutar_todo
py -m unittest tests.test_cluster -v
```

El primer comando instala las librerías (solo una vez). El segundo genera todas las figuras y tablas en `docs/actividad3/` y termina con `LISTO`. El tercero debe terminar con `OK`.

No hace falta volver a generar los datos. Si se quiere comprobar el generador, hacerlo en una carpeta aparte para no tocar los CSV del repositorio (ver la guía paso a paso).

## Resultado principal

| Grupo | Estaciones |
|---|---|
| Residencial | Cuba, Guadalupe, Insuperables, La Macarena, La Romelia, Los Molinos, Perla del Otun, Travesuras |
| Laboral | Centro, Egoya, Jardin, Postobon, Victoria |
| Mixta | Corales, Parque Olaya, San Fernando, Universidad |
| Intercambio | Dosquebradas, Terminal, Viaducto |

K-means (k = 4): inercia 188,5, silueta 0,447. Coincide con Ward (ARI 1,000) y con los tipos reales (ARI 1,000).

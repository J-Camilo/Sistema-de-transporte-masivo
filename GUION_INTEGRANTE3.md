# Guion del video: Integrante 3 (minuto 5 a 8)

**Tema:** búsqueda A* e interfaz por consola (capítulo 9)
**Duración:** unos 3 minutos

## Antes de grabar

- Letra de la terminal grande (que se lea en el celular).
- Abrir `search/astar.py` en el editor.
- Tener la terminal abierta en la carpeta del proyecto.

---

## 1. Qué problema resuelve A* (5:00 – 5:30)

> "Mis compañeros ya construyeron el mapa: las estaciones, las conexiones y los tiempos
> ajustados por las reglas. Mi parte es encontrar la ruta **más rápida** dentro de ese mapa.
> Se podrían probar todos los caminos, pero sería lento. A* funciona como un GPS: en cada paso
> revisa primero la opción que parece más prometedora."

## 2. La fórmula f = g + h (5:30 – 6:10)

*Mostrar en pantalla la cabecera de `search/astar.py`.*

> "A* ordena las opciones con **f = g + h**.
> **g** es lo que ya sabemos: los minutos que llevamos acumulados. Esos minutos ya vienen con la
> hora pico y los transbordos, porque los calculó el motor de inferencia.
> **h** es una estimación de lo que falta: la distancia en línea recta hasta el destino,
> dividida entre la velocidad del bus."

## 3. Por qué la heurística es válida (6:10 – 6:40)

*Mostrar la función `heuristica()`.*

> "La heurística nunca puede decir que falta **más** tiempo del real, por dos razones:
> primero, la línea recta es el camino más corto posible; segundo, usamos la velocidad
> **máxima** del bus, 60 km/h, y no la promedio. Eso da el tiempo más optimista posible.
> Una heurística que nunca sobreestima se llama **admisible**, y con ella A* garantiza
> encontrar la ruta óptima."

## 4. Demo 1: ruta con transbordo en hora pico (6:40 – 7:15)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 07:30 --html
```

*Con `--html` se abre una pestaña del navegador con el mapa y la ruta resaltada. Mostrar primero
la terminal y luego la pestaña.*

> "Aquí la mejor ruta toma la R1, hace **transbordo en Maraya** y sigue en la R2: 18.2 minutos.
> Abajo aparecen las reglas que se activaron: D1 dice que es hora pico, A2 sube los tramos un
> 40 %, A3 agrega congestión del centro y A4 suma 5 minutos por el transbordo."

## 5. Demo 2: la misma ruta fuera de hora pico (7:15 – 7:40)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 10:00
```

> "La misma consulta a las 10 de la mañana tarda 14 minutos y solo se activan las reglas del
> transbordo. El sistema **razona** según la hora: no es un tiempo fijo."

## 6. A* contra Dijkstra (7:40 – 8:00)

*Señalar la última línea de la salida.*

> "Para demostrar que la heurística sirve, comparamos contra Dijkstra, que es A* sin heurística.
> Los dos encuentran el mismo tiempo, pero A* revisó 20 nodos y Dijkstra 27.
> Menos trabajo para el mismo resultado: eso es lo que aporta la heurística."

---

## Si el profesor pregunta

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué la velocidad máxima y no la promedio, como decía el plan? | Con la promedio, en un tramo rápido h daría más minutos que el tiempo real. Eso sobreestima y A* ya no garantiza la mejor ruta. |
| ¿Por qué los nodos son (estación, ruta)? | Así el transbordo es un arco más, con su costo. Si los nodos fueran solo estaciones, A* no sabría por qué ruta llegaste. |
| ¿Por qué A* ahorra poco frente a Dijkstra? | Las rutas de Megabús son casi líneas: hay pocos caminos para descartar. En redes más grandes la diferencia crece. |
| ¿Cómo sabes que funciona? | 18 pruebas: misma ruta, transbordo, hora pico, origen = destino, estación inexistente y ruta imposible. Se corren con `python -m unittest discover tests`. |

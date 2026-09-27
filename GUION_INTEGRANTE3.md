# Guion del video: Integrante 3 (minuto 5 a 8)

**Tema:** búsqueda A*, interfaz por consola y reporte visual (capítulo 9)
**Duración:** unos 3 minutos

## Antes de grabar

- Letra de la terminal grande (que se lea en el celular).
- Abrir `search/astar.py` en el editor.
- Tener la terminal abierta en la carpeta del proyecto y el navegador a mano.
- Correr una vez el comando de la demo 1, para que la pestaña abra rápido durante la grabación.

---

## 1. Qué problema resuelve A* (5:00 – 5:25)

> "Mis compañeros ya construyeron el mapa: las estaciones, las conexiones y los tiempos
> ajustados por las reglas. Mi parte es encontrar la ruta **más rápida** dentro de ese mapa.
> Se podrían probar todos los caminos, pero sería lento. A* funciona como un GPS: en cada paso
> revisa primero la opción que parece más prometedora."

## 2. La fórmula f = g + h (5:25 – 6:00)

*Mostrar la cabecera de `search/astar.py`.*

> "A* ordena las opciones con **f = g + h**.
> **g** es lo que ya sabemos: los minutos acumulados. Esos minutos ya traen la hora pico y los
> transbordos, porque los calculó el motor de inferencia.
> **h** es una estimación de lo que falta: la distancia en línea recta hasta el destino,
> dividida entre la velocidad del bus."

## 3. Por qué la heurística es válida (6:00 – 6:25)

*Mostrar la función `heuristica()`.*

> "La heurística nunca puede decir que falta **más** tiempo del real: la línea recta es el
> camino más corto posible, y usamos la velocidad **máxima** del bus, 60 km/h, no la promedio.
> Una heurística que nunca sobreestima se llama **admisible**, y con ella A* garantiza la
> ruta óptima."

## 4. Demo en hora pico: terminal + pestaña (6:25 – 7:15)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 07:30 --html
```

*Primero la terminal (unos 5 segundos):*

> "Esta es la interfaz por consola: el usuario escribe origen, destino y hora, y el programa
> responde con la ruta. Con la opción `--html` se abre además esta pestaña."

*Pasar al navegador y recorrerlo de arriba abajo:*

> "**Arriba** está el resultado: 18.2 minutos, en hora pico.
> En el **recorrido** está cada parada en orden, como en un mapa de metro, con el minuto en
> que el bus llega a cada una. La línea naranja es la R1; en Maraya, el anillo amarillo, se hace
> el **transbordo**, y la línea azul sigue por la R2 hasta Egoyá.
> En **paso a paso** está lo mismo en tarjetas: 9.8 minutos en R1, más 5 del transbordo y
> 3.4 en R2.
> Y aquí están las **reglas** que razonó el motor: D1 dice que es hora pico, A2 sube cada
> tramo un 40 %, A3 agrega congestión del centro, D3 detecta el transbordo y A4 le suma 5 minutos."

## 5. Demo fuera de hora pico (7:15 – 7:35)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 10:00 --html
```

> "La misma consulta a las 10 de la mañana: 14 minutos. La etiqueta ahora dice **hora valle** y
> solo quedan las reglas del transbordo. El sistema **razona** según la hora: el tiempo no es fijo."

## 6. A* contra Dijkstra (7:35 – 8:00)

*Bajar hasta "Nodos revisados".*

> "Para demostrar que la heurística sirve, comparamos con Dijkstra, que es A* sin heurística.
> Los dos encuentran el mismo tiempo, pero A* revisó 20 nodos y Dijkstra 27: un 26 % menos
> de trabajo para el mismo resultado. Eso es lo que aporta la heurística."

---

## Si el profesor pregunta

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué la velocidad máxima y no la promedio, como decía el plan? | Con la promedio, en un tramo rápido h daría más minutos que el tiempo real. Eso sobreestima y A* ya no garantiza la mejor ruta. |
| ¿Por qué los nodos son (estación, ruta)? | Así el transbordo es un arco más, con su costo. Si los nodos fueran solo estaciones, A* no sabría por qué ruta llegaste. |
| ¿Por qué A* ahorra poco en algunas consultas? | Las rutas de Megabús son casi líneas: hay pocos caminos para descartar. En promedio ahorra un 9 %; en consultas con transbordo, más. |
| ¿La página del navegador usa alguna librería? | No. El HTML se genera con la biblioteca estándar de Python, a partir del mismo camino que devuelve A*. |
| ¿Cómo sabes que funciona? | 19 pruebas del Integrante 3 (27 en total): misma ruta, transbordo, hora pico, origen = destino, estación inexistente, ruta imposible y el reporte HTML. Se corren con `python -m unittest discover tests`. |

# Guion: Integrante 3 (minuto 5 a 8)

**Antes de grabar:** terminal con letra grande y `search/astar.py` abierto.

## 1. A* (5:00)

> "Con el mapa que armó el motor, mi parte es encontrar la ruta más rápida. A* es como un GPS:
> revisa primero el camino que parece más prometedor, en lugar de probarlos todos."

## 2. f = g + h (5:30)

> "**g** son los minutos que llevamos, con hora pico y transbordos incluidos.
> **h** estima lo que falta: la distancia en línea recta dividida entre la velocidad del bus."

## 3. Por qué h es válida (6:00)

> "h nunca se pasa del tiempo real: la línea recta es lo más corto posible y usamos la
> velocidad **máxima**, 60 km/h. Por eso es **admisible**, y A* siempre encuentra la mejor ruta."

## 4. Demo en hora pico (6:25)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 07:30 --html
```

> "La terminal muestra la ruta y se abre esta pestaña: 18.2 minutos. Va por la R1, hace
> **transbordo en Maraya** y sigue por la R2. Abajo están las reglas que razonó el motor:
> hora pico, congestión del centro y +5 minutos por el transbordo."

## 5. Demo fuera de hora pico (7:15)

```
python main.py --origen "Parque Olaya" --destino "Egoyá" --hora 10:00 --html
```

> "A las 10 son 14 minutos y solo quedan las reglas del transbordo. El tiempo depende de la hora."

## 6. A* contra Dijkstra (7:35)

> "Dijkstra es A* sin heurística. Los dos encuentran el mismo tiempo, pero A* revisó 20 nodos
> y Dijkstra 28. Eso demuestra que la heurística sirve."

---

**Si el profe pregunta:**
- **¿Por qué la velocidad máxima y no la promedio?** Con la promedio, h podría pasarse del tiempo real.
- **¿Por qué los nodos son (estación, ruta)?** Para que el transbordo sea un arco con su propio costo.
- **¿Cómo sabes que funciona?** Con 27 pruebas: `python -m unittest discover tests`.

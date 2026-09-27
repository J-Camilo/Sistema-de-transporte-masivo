"""
reporte_html.py  -  Resultado de la consulta como página web
============================================================
INTEGRANTE 3  |  Lo usa main.py con la opción --html.

Genera un HTML autocontenido (sin librerías externas) con:
    - el recorrido parada por parada, estilo diagrama de metro
    - la ruta resumida paso a paso, con los transbordos marcados
    - las reglas que se activaron
    - la comparación de nodos revisados: A* contra Dijkstra
"""
from html import escape

from kb.estaciones import ESTACIONES

COLORES_RUTA = {"R1": "#e4572e", "R2": "#2e86ab", "R3": "#3bb273"}


def _color(ruta):
    return COLORES_RUTA.get(ruta, "#888")


def _paradas(mapa, camino):
    """
    Convierte el camino de nodos (estacion, ruta) en paradas con el minuto de llegada.
    Un transbordo no es una parada nueva: se anota en la estación donde ocurre.
    """
    paradas = []
    minuto = 0
    for anterior, nodo in zip([None] + camino, camino):
        if anterior is not None:
            costo = dict(mapa[anterior])[nodo]
            minuto += costo
            if anterior[0] == nodo[0]:
                paradas[-1]["transbordo"] = (anterior[1], nodo[1], costo)
                continue
        paradas.append({"estacion": nodo[0], "ruta": nodo[1], "minuto": minuto,
                        "transbordo": None})
    return paradas


def _recorrido_html(mapa, camino):
    paradas = _paradas(mapa, camino)
    filas = []
    for i, p in enumerate(paradas):
        ultima = i == len(paradas) - 1
        # El color de la línea que baja desde esta parada es el de la ruta del tramo siguiente.
        color = "transparent" if ultima else _color(paradas[i + 1]["ruta"])
        nombre = escape(ESTACIONES[p["estacion"]]["nombre"])
        if i == 0:
            clase, detalle = "clave", f"Origen · sube a {paradas[1]['ruta'] if len(paradas) > 1 else p['ruta']}"
        elif ultima:
            clase, detalle = "clave", "Destino"
        elif p["transbordo"]:
            de, a, costo = p["transbordo"]
            clase, detalle = "clave trans", f"Transbordo {de} → {a} · +{costo:.1f} min"
        else:
            clase, detalle = "", ""
        filas.append(
            f'<li class="{clase}" style="--c:{color}">'
            f'<span class="t">{p["minuto"]:.1f}</span><span class="punto"></span>'
            f'<div><b>{nombre}</b>{f"<small>{detalle}</small>" if detalle else ""}</div></li>')
    leyenda = "".join(f'<span><i style="background:{c}"></i>{r}</span>'
                      for r, c in COLORES_RUTA.items())
    return (f'<ol class="recorrido">{"".join(filas)}</ol>'
            f'<div class="leyenda">{leyenda}<span><i class="anillo"></i>Transbordo</span>'
            f'<span>Números: minuto de llegada</span></div>')


def _pasos_html(pasos):
    filas = []
    for paso in pasos:
        if paso["tipo"] == "tramo":
            filas.append(
                f'<li class="tramo" style="--c:{_color(paso["ruta"])}">'
                f'<span class="insignia">{paso["ruta"]}</span>'
                f'<div><b>{escape(ESTACIONES[paso["desde"]]["nombre"])} → '
                f'{escape(ESTACIONES[paso["hasta"]]["nombre"])}</b>'
                f'<small>{paso["paradas"]} parada(s)</small></div>'
                f'<span class="min">{paso["minutos"]:.1f} min</span></li>')
        else:
            filas.append(
                f'<li class="transbordo"><span class="insignia">⇄</span>'
                f'<div><b>Transbordo en {escape(ESTACIONES[paso["estacion"]]["nombre"])}</b>'
                f'<small>{paso["de"]} → {paso["a"]}</small></div>'
                f'<span class="min">+{paso["minutos"]:.1f} min</span></li>')
    return "".join(filas)


def _reglas_html(reglas):
    if not reglas:
        return '<p class="vacio">Ninguna: hora valle y sin transbordos.</p>'
    return "".join(
        f'<li><span class="id">{r["id"]}</span>{escape(r["descripcion"])}'
        f'<span class="veces">×{r["veces"]}</span></li>' for r in reglas)


def _comparacion_html(comparacion):
    a = comparacion["astar"]["expandidos"]
    d = comparacion["dijkstra"]["expandidos"]
    maximo = max(a, d, 1)
    ahorro = round(100 * (d - a) / d) if d else 0
    return (f'<div class="barra"><span>A*</span><div><i style="width:{100 * a / maximo:.0f}%;'
            f'background:var(--acento)"></i></div><b>{a}</b></div>'
            f'<div class="barra"><span>Dijkstra</span><div><i style="width:{100 * d / maximo:.0f}%">'
            f'</i></div><b>{d}</b></div>'
            f'<p class="nota">Mismo tiempo encontrado, {ahorro}% menos nodos revisados gracias a la heurística.</p>')


def generar_html(mapa, origen, destino, hora, camino, costo, pasos, reglas, comparacion):
    """Devuelve el HTML completo del reporte como texto."""
    pico = any(r["id"] == "A2" for r in reglas)
    titulo = f'{ESTACIONES[origen]["nombre"]} → {ESTACIONES[destino]["nombre"]}'
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ruta Megabús</title>
<style>
:root {{ --fondo:#f4f6f8; --tarjeta:#fff; --texto:#1d2733; --suave:#66768a; --borde:#e2e7ee;
        --acento:#2e86ab; --pico:#e4572e; --trans:#f2a541; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fondo:#0f141a; --tarjeta:#18212b; --texto:#e8edf2; --suave:#93a3b5; --borde:#2a3642; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--fondo); color:var(--texto);
       font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:24px 16px 48px; }}
header {{ display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px;
         margin-bottom:20px; }}
header small {{ color:var(--suave); text-transform:uppercase; letter-spacing:.08em; font-weight:600; }}
h1 {{ margin:4px 0 0; font-size:clamp(1.5rem, 4vw, 2.2rem); }}
.total {{ text-align:right; }}
.total b {{ display:block; font-size:clamp(2.2rem, 7vw, 3.4rem); line-height:1; }}
.chip {{ display:inline-block; padding:2px 10px; border-radius:99px; font-size:.8rem; font-weight:600;
        background:var(--borde); color:var(--suave); }}
.chip.pico {{ background:var(--pico); color:#fff; }}
.rejilla {{ display:grid; grid-template-columns:1.3fr 1fr; gap:16px; align-items:start; }}
@media (max-width:820px) {{ .rejilla {{ grid-template-columns:1fr; }} .total {{ text-align:left; }} }}
section {{ background:var(--tarjeta); border:1px solid var(--borde); border-radius:14px; padding:18px; }}
h2 {{ margin:0 0 12px; font-size:1rem; color:var(--suave); text-transform:uppercase; letter-spacing:.06em; }}
.recorrido {{ list-style:none; margin:0; padding:0; }}
.recorrido li {{ position:relative; display:grid; grid-template-columns:44px 28px 1fr;
                align-items:center; min-height:32px; }}
.recorrido li::before {{ content:""; position:absolute; left:58px; top:50%; height:100%;
                        width:6px; background:var(--c); }}
.recorrido .t {{ text-align:right; padding-right:10px; color:var(--suave); font-size:.8rem;
                font-variant-numeric:tabular-nums; }}
.recorrido .punto {{ position:relative; z-index:1; justify-self:center; width:12px; height:12px;
                    border-radius:50%; background:var(--tarjeta); border:3px solid var(--suave); }}
.recorrido li div {{ color:var(--suave); font-size:.9rem; padding:4px 0; }}
.recorrido li div b {{ font-weight:500; }}
.recorrido li.clave div {{ color:var(--texto); font-size:1rem; }}
.recorrido li.clave div b {{ font-weight:700; }}
.recorrido li.clave .punto {{ width:18px; height:18px; border-color:var(--texto); }}
.recorrido li.trans .punto {{ width:22px; height:22px; border:5px solid var(--trans); }}
.recorrido li small {{ display:block; color:var(--suave); font-size:.82rem; }}
.recorrido li.trans small {{ color:var(--trans); font-weight:600; }}
.leyenda {{ display:flex; gap:14px; flex-wrap:wrap; font-size:.85rem; color:var(--suave); margin-top:8px; }}
.leyenda i {{ display:inline-block; width:14px; height:4px; border-radius:2px; margin-right:6px;
             vertical-align:middle; }}
.leyenda i.anillo {{ width:12px; height:12px; border:3px solid var(--trans); border-radius:50%; }}
ol {{ list-style:none; margin:0; padding:0; }}
.pasos li {{ display:flex; align-items:center; gap:12px; padding:12px; border-radius:10px;
        border-left:5px solid var(--c, var(--trans)); background:var(--fondo); margin-bottom:8px; }}
.pasos li div {{ flex:1; min-width:0; }}
.pasos li small {{ display:block; color:var(--suave); }}
.insignia {{ flex:none; width:40px; height:40px; border-radius:10px; display:grid; place-items:center;
            font-weight:800; color:#fff; background:var(--c, var(--trans)); }}
.min {{ font-weight:700; white-space:nowrap; }}
.transbordo .min {{ color:var(--trans); }}
ul {{ list-style:none; margin:0; padding:0; }}
ul li {{ display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid var(--borde); }}
ul li:last-child {{ border-bottom:0; }}
.id {{ flex:none; font:700 .8rem ui-monospace, Consolas, monospace; padding:3px 8px; border-radius:6px;
      background:var(--acento); color:#fff; }}
.veces {{ margin-left:auto; color:var(--suave); font-size:.85rem; }}
.barra {{ display:grid; grid-template-columns:80px 1fr 40px; align-items:center; gap:10px; margin:8px 0; }}
.barra div {{ height:14px; background:var(--fondo); border-radius:7px; overflow:hidden; }}
.barra i {{ display:block; height:100%; background:var(--suave); border-radius:7px; }}
.nota, .vacio {{ color:var(--suave); font-size:.9rem; margin:10px 0 0; }}
.columna {{ display:grid; gap:16px; align-content:start; }}
.rejilla > * {{ min-width:0; }}
</style></head>
<body><main>
<header>
  <div><small>Ruta recomendada · {escape(hora)}</small><h1>{escape(titulo)}</h1></div>
  <div class="total"><b>{costo:.1f} min</b>
    <span class="chip{' pico' if pico else ''}">{'Hora pico aplicada' if pico else 'Hora valle'}</span></div>
</header>
<div class="rejilla">
  <section><h2>Recorrido</h2>{_recorrido_html(mapa, camino)}</section>
  <div class="columna">
    <section><h2>Paso a paso</h2><ol class="pasos">{_pasos_html(pasos)}</ol></section>
    <section><h2>Reglas activadas</h2><ul>{_reglas_html(reglas)}</ul></section>
    <section><h2>Nodos revisados</h2>{_comparacion_html(comparacion)}</section>
  </div>
</div>
</main></body></html>
"""

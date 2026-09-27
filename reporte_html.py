"""
reporte_html.py  -  Resultado de la consulta como página web
============================================================
INTEGRANTE 3  |  Lo usa main.py con la opción --html.

Genera un HTML autocontenido (sin librerías externas) con:
    - el mapa de estaciones dibujado con sus coordenadas reales y la ruta resaltada
    - la ruta paso a paso, con los transbordos marcados
    - las reglas que se activaron
    - la comparación de nodos revisados: A* contra Dijkstra
"""
import math
from html import escape

from kb.conexiones import CONEXIONES
from kb.estaciones import ESTACIONES

COLORES_RUTA = {"R1": "#e4572e", "R2": "#2e86ab", "R3": "#3bb273"}
ANCHO, ALTO, MARGEN = 640, 420, 30


def _color(ruta):
    return COLORES_RUTA.get(ruta, "#888")


def _proyectar():
    """Convierte lat/lon en coordenadas x/y del dibujo (proyección plana simple)."""
    lats = [e["lat"] for e in ESTACIONES.values()]
    lons = [e["lon"] for e in ESTACIONES.values()]
    lat0 = math.radians(sum(lats) / len(lats))
    ancho_geo = (max(lons) - min(lons)) * math.cos(lat0)
    alto_geo = max(lats) - min(lats)
    escala = min((ANCHO - 2 * MARGEN) / ancho_geo, (ALTO - 2 * MARGEN) / alto_geo)
    return {
        id_est: (MARGEN + (e["lon"] - min(lons)) * math.cos(lat0) * escala,
                 MARGEN + (max(lats) - e["lat"]) * escala)
        for id_est, e in ESTACIONES.items()
    }


def _mapa_svg(camino):
    pos = _proyectar()
    partes = []

    # Fondo: todas las conexiones de la red, tenues.
    for c in CONEXIONES:
        (x1, y1), (x2, y2) = pos[c["origen"]], pos[c["destino"]]
        partes.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="{_color(c["ruta"])}" stroke-opacity=".4" stroke-width="3"/>')

    # La ruta elegida, gruesa y del color de cada línea.
    for (a, ruta), (b, _) in zip(camino, camino[1:]):
        if a != b:
            (x1, y1), (x2, y2) = pos[a], pos[b]
            partes.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="{_color(ruta)}" stroke-width="6" stroke-linecap="round"/>')

    en_ruta = {est for est, _ in camino}
    transbordos = {a for (a, _), (b, _) in zip(camino, camino[1:]) if a == b}
    origen, destino = camino[0][0], camino[-1][0]
    for id_est, (x, y) in pos.items():
        radio = 6 if id_est in en_ruta else 3.5
        clase = "punto activo" if id_est in en_ruta else "punto"
        partes.append(f'<circle class="{clase}" cx="{x:.1f}" cy="{y:.1f}" r="{radio}">'
                      f'<title>{escape(ESTACIONES[id_est]["nombre"])}</title></circle>')
        if id_est in transbordos:
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="none" '
                          f'stroke="#f2a541" stroke-width="3"/>')
        if id_est in (origen, destino) or id_est in transbordos:
            partes.append(f'<text class="etiqueta" x="{x + 13:.1f}" y="{y + 4:.1f}">'
                          f'{escape(ESTACIONES[id_est]["nombre"])}</text>')

    leyenda = "".join(
        f'<span><i style="background:{color}"></i>{ruta}</span>'
        for ruta, color in COLORES_RUTA.items())
    return (f'<svg viewBox="0 0 {ANCHO} {ALTO}" role="img" '
            f'aria-label="Mapa de la ruta">{"".join(partes)}</svg>'
            f'<div class="leyenda">{leyenda}<span><i class="anillo"></i>Transbordo</span></div>')


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


def generar_html(origen, destino, hora, camino, costo, pasos, reglas, comparacion):
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
svg {{ width:100%; height:auto; display:block; }}
.punto {{ fill:var(--tarjeta); stroke:var(--suave); stroke-width:1.5; }}
.punto.activo {{ fill:var(--texto); stroke:var(--tarjeta); stroke-width:2; }}
.etiqueta {{ font-size:13px; font-weight:700; fill:var(--texto); paint-order:stroke;
            stroke:var(--tarjeta); stroke-width:4px; }}
.leyenda {{ display:flex; gap:14px; flex-wrap:wrap; font-size:.85rem; color:var(--suave); margin-top:8px; }}
.leyenda i {{ display:inline-block; width:14px; height:4px; border-radius:2px; margin-right:6px;
             vertical-align:middle; }}
.leyenda i.anillo {{ width:12px; height:12px; border:3px solid var(--trans); border-radius:50%; }}
ol {{ list-style:none; margin:0; padding:0; }}
ol li {{ display:flex; align-items:center; gap:12px; padding:12px; border-radius:10px;
        border-left:5px solid var(--c, var(--trans)); background:var(--fondo); margin-bottom:8px; }}
ol li div {{ flex:1; min-width:0; }}
ol li small {{ display:block; color:var(--suave); }}
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
  <section><h2>Mapa</h2>{_mapa_svg(camino)}</section>
  <div class="columna">
    <section><h2>Paso a paso</h2><ol>{_pasos_html(pasos)}</ol></section>
    <section><h2>Reglas activadas</h2><ul>{_reglas_html(reglas)}</ul></section>
    <section><h2>Nodos revisados</h2>{_comparacion_html(comparacion)}</section>
  </div>
</div>
</main></body></html>
"""

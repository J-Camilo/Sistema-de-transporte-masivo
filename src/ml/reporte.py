"""
ml/reporte.py - Resultados del Rol C como páginas web
=====================================================
Rol C | Mismo estilo que reporte_html.py de la Actividad 1.

    html_evaluacion(resultados)   lo usa evaluacion.py --html
        acierto, matriz de confusión, métricas por clase, comparación de modelos,
        validación cruzada y la prueba de fidelidad del motor.

    html_integracion(...)         lo usa integracion.py --html
        la ruta de la Actividad 1 + el razonamiento del motor, separando las reglas
        escritas a mano de las aprendidas, con cada condición marcada con el valor
        real del viaje.

HTML autocontenido, sin librerías externas.
"""
import webbrowser
from html import escape
from pathlib import Path

from engine import inferencia
from kb.estaciones import ESTACIONES
from reporte_html import _recorrido_html

COLOR_DEMORA = {"baja": "#3bb273", "media": "#f2a541", "alta": "#e4572e"}
CLASES = ["baja", "media", "alta"]

ESTILO = """
:root { --fondo:#f4f6f8; --tarjeta:#fff; --texto:#1d2733; --suave:#66768a; --borde:#e2e7ee;
        --acento:#2e86ab; --aprendida:#7b4fc9; --pico:#e4572e; --trans:#f2a541; --ok:#3bb273; }
@media (prefers-color-scheme: dark) {
  :root { --fondo:#0f141a; --tarjeta:#18212b; --texto:#e8edf2; --suave:#93a3b5; --borde:#2a3642;
          --aprendida:#a07ff0; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--fondo); color:var(--texto);
       font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:1100px; margin:0 auto; padding:24px 16px 48px; }
header { display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px;
         margin-bottom:20px; }
header small { color:var(--suave); text-transform:uppercase; letter-spacing:.08em; font-weight:600; }
h1 { margin:4px 0 0; font-size:clamp(1.5rem, 4vw, 2.2rem); }
.total { text-align:right; }
.total b { display:block; font-size:clamp(2.2rem, 7vw, 3.4rem); line-height:1; }
.chip { display:inline-block; padding:2px 10px; border-radius:99px; font-size:.8rem; font-weight:600;
        background:var(--borde); color:var(--suave); }
.rejilla { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:start; }
.rejilla.ruta { grid-template-columns:1fr 1.4fr; }
@media (max-width:820px) { .rejilla, .rejilla.ruta { grid-template-columns:1fr; } .total { text-align:left; } }
.rejilla > * { min-width:0; }
.columna { display:grid; gap:16px; align-content:start; }
section { background:var(--tarjeta); border:1px solid var(--borde); border-radius:14px; padding:18px; }
h2 { margin:0 0 12px; font-size:1rem; color:var(--suave); text-transform:uppercase; letter-spacing:.06em; }
.nota { color:var(--suave); font-size:.88rem; margin:10px 0 0; }
ul, ol { list-style:none; margin:0; padding:0; }
.id { flex:none; font:700 .8rem ui-monospace, Consolas, monospace; padding:3px 8px; border-radius:6px;
      background:var(--acento); color:#fff; }
.id.ml { background:var(--aprendida); }
.demora { display:inline-block; padding:4px 14px; border-radius:99px; color:#fff; font-weight:800;
          letter-spacing:.04em; }
/* barras */
.barra { display:grid; grid-template-columns:minmax(90px, 34%) 1fr 64px; align-items:center; gap:10px;
         margin:8px 0; font-size:.9rem; }
.barra div { height:14px; background:var(--fondo); border-radius:7px; overflow:hidden; }
.barra i { display:block; height:100%; background:var(--suave); border-radius:7px; }
.barra.destacada span, .barra.destacada b { font-weight:800; }
.barra.destacada i { background:var(--acento); }
.barra b { text-align:right; font-variant-numeric:tabular-nums; }
/* matriz de confusión */
.matriz { border-collapse:separate; border-spacing:4px; margin:0 auto; }
.matriz th { color:var(--suave); font-size:.8rem; font-weight:600; padding:4px 8px; }
.matriz td { width:76px; height:56px; text-align:center; border-radius:8px; font-weight:700;
             font-size:1.1rem; font-variant-numeric:tabular-nums; }
/* métricas por clase */
.clase { padding:10px 0; border-bottom:1px solid var(--borde); }
.clase:last-child { border-bottom:0; }
.clase .barra { grid-template-columns:80px 1fr 64px; margin:4px 0; }
/* fidelidad */
.grande { font-size:clamp(2rem, 6vw, 2.8rem); font-weight:800; line-height:1.1; color:var(--ok); }
table.reglas { width:100%; border-collapse:collapse; font-size:.88rem; margin-top:12px; }
table.reglas td, table.reglas th { padding:8px 6px; border-bottom:1px solid var(--borde); text-align:left;
                                   vertical-align:top; }
table.reglas th { color:var(--suave); font-weight:600; }
/* razonamiento */
.paso { padding:12px; border-radius:10px; background:var(--fondo); margin-bottom:10px;
        border-left:5px solid var(--acento); }
.paso.ml { border-left-color:var(--aprendida); }
.paso .cabeza { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.paso .tipo { font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
              color:var(--acento); }
.paso.ml .tipo { color:var(--aprendida); }
.paso p { margin:6px 0 0; }
.cond { display:grid; grid-template-columns:22px 1fr auto; gap:8px; align-items:center; font-size:.88rem;
        padding:3px 0; }
.cond .marca { font-weight:800; color:var(--ok); }
.cond.no .marca { color:var(--pico); }
.cond code { font:.85rem ui-monospace, Consolas, monospace; }
.cond .valor { color:var(--suave); font-variant-numeric:tabular-nums; }
.hechos { display:grid; grid-template-columns:auto 1fr; gap:4px 14px; font-size:.9rem; }
.hechos dt { color:var(--suave); }
.hechos dd { margin:0; font-weight:600; }
.cargada { display:flex; gap:10px; align-items:flex-start; padding:10px 0; border-bottom:1px solid var(--borde);
           font-size:.88rem; }
.cargada:last-child { border-bottom:0; }
.cargada.disparada { background:color-mix(in srgb, var(--aprendida) 12%, transparent); border-radius:8px;
                     padding:10px; }
.cargada small { display:block; color:var(--suave); }
.vacio { color:var(--suave); }
/* recorrido: mismos estilos que reporte_html.py de la Actividad 1 */
.recorrido { list-style:none; margin:0; padding:0; }
.recorrido li { position:relative; display:grid; grid-template-columns:44px 28px 1fr;
                align-items:center; min-height:32px; }
.recorrido li::before { content:""; position:absolute; left:58px; top:50%; height:100%;
                        width:6px; background:var(--c); }
.recorrido .t { text-align:right; padding-right:10px; color:var(--suave); font-size:.8rem;
                font-variant-numeric:tabular-nums; }
.recorrido .punto { position:relative; z-index:1; justify-self:center; width:12px; height:12px;
                    border-radius:50%; background:var(--tarjeta); border:3px solid var(--suave); }
.recorrido li div { color:var(--suave); font-size:.9rem; padding:4px 0; }
.recorrido li div b { font-weight:500; }
.recorrido li.clave div { color:var(--texto); font-size:1rem; }
.recorrido li.clave div b { font-weight:700; }
.recorrido li.clave .punto { width:18px; height:18px; border-color:var(--texto); }
.recorrido li.trans .punto { width:22px; height:22px; border:5px solid var(--trans); }
.recorrido li small { display:block; color:var(--suave); font-size:.82rem; }
.recorrido li.trans small { color:var(--trans); font-weight:600; }
.leyenda { display:flex; gap:14px; flex-wrap:wrap; font-size:.85rem; color:var(--suave); margin-top:8px; }
.leyenda i { display:inline-block; width:14px; height:4px; border-radius:2px; margin-right:6px;
             vertical-align:middle; }
.leyenda i.anillo { width:12px; height:12px; border:3px solid var(--trans); border-radius:50%; }
.total .demora { margin-top:6px; }
"""


def pct(valor):
    return f"{valor * 100:.1f} %".replace(".", ",")


def _pagina(titulo, cuerpo):
    return (f'<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{escape(titulo)}</title>\n<style>{ESTILO}</style></head>\n'
            f'<body><main>{cuerpo}</main></body></html>\n')


def _barra(etiqueta, valor, maximo=1.0, texto=None, destacada=False, color=None):
    estilo = f"width:{100 * valor / maximo:.1f}%" + (f";background:{color}" if color else "")
    return (f'<div class="barra{" destacada" if destacada else ""}"><span>{escape(etiqueta)}</span>'
            f'<div><i style="{estilo}"></i></div><b>{texto or pct(valor)}</b></div>')


def guardar_y_abrir(html, nombre):
    archivo = Path(nombre).resolve()
    archivo.write_text(html, encoding="utf-8")
    print(f"\nReporte visual: {archivo}")
    webbrowser.open(archivo.as_uri())


# ---------------------------------------------------------------------------
# Página de la evaluación
# ---------------------------------------------------------------------------
def _matriz_html(matriz):
    maximo = max(max(fila) for fila in matriz) or 1
    filas = []
    for clase, fila in zip(CLASES, matriz):
        celdas = []
        for j, valor in enumerate(fila):
            color = "var(--ok)" if CLASES[j] == clase else "var(--pico)"
            # La intensidad del color es proporcional a la cantidad de viajes.
            fondo = f"color-mix(in srgb, {color} {12 + 78 * valor / maximo:.0f}%, var(--tarjeta))"
            celdas.append(f'<td style="background:{fondo}">{valor}</td>')
        filas.append(f'<tr><th>{clase}</th>{"".join(celdas)}</tr>')
    cabeza = "".join(f"<th>{c}</th>" for c in CLASES)
    return (f'<table class="matriz"><tr><th>Real ↓ · Predicho →</th>{cabeza}</tr>{"".join(filas)}</table>'
            f'<p class="nota">En verde (la diagonal), los aciertos. En rojo, los errores.</p>')


def _por_clase_html(por_clase):
    bloques = []
    for clase, precision, recall, f1, viajes in por_clase:
        color = COLOR_DEMORA[clase]
        bloques.append(
            f'<div class="clase"><span class="demora" style="background:{color}">{clase}</span> '
            f'<small class="nota">{viajes} viajes</small>'
            + _barra("Precisión", precision, color=color)
            + _barra("Recall", recall, color=color)
            + _barra("F1", f1, color=color) + "</div>")
    return "".join(bloques)


def _modelos_html(modelos):
    maximo = max(max(m["cv"]) for m in modelos)
    filas = []
    for m in modelos:
        media = sum(m["cv"]) / len(m["cv"])
        filas.append(_barra(m["nombre"], media, maximo, destacada=m["nombre"].startswith("Árbol")))
    return "".join(filas) + '<p class="nota">Acierto medio en validación cruzada (5 particiones).</p>'


def _particiones_html(modelos):
    arbol = next(m for m in modelos if m["nombre"].startswith("Árbol"))
    media = sum(arbol["cv"]) / len(arbol["cv"])
    filas = "".join(_barra(f"Partición {i}", v, destacada=True) for i, v in enumerate(arbol["cv"], 1))
    return filas + f'<p class="nota">Todas cerca de la media ({pct(media)}): el resultado no depende de la suerte.</p>'


def _curva_html(curva, escogida):
    maximo = max(v for _, v in curva)
    return "".join(_barra(f"Profundidad {p}", v, maximo, destacada=p == escogida) for p, v in curva) + \
        f'<p class="nota">Validación cruzada sobre los 4.000 viajes. Resaltada: la que escogió el Rol B.</p>'


def html_evaluacion(r):
    fid = r["fidelidad"]
    base = next(m for m in r["modelos"] if m["nombre"].startswith("Línea base"))
    filas_reglas = "".join(
        f'<tr><td><span class="id ml">{escape(i)}</span></td><td>{escape(d)}</td>'
        f'<td>{n}</td><td>{pct(a) if n else "-"}</td></tr>' for i, d, n, a in r["por_regla"])
    cuerpo = f"""
<header>
  <div><small>Evaluación del árbol de decisión · profundidad {r["profundidad"]} ·
    {r["viajes_prueba"]} viajes de prueba</small><h1>¿Qué tan bueno es el árbol?</h1></div>
  <div class="total"><b>{pct(r["accuracy"])}</b>
    <span class="chip">Línea base: {pct(base["prueba"])}</span></div>
</header>
<div class="rejilla">
  <section><h2>Matriz de confusión</h2>{_matriz_html(r["matriz"])}</section>
  <section><h2>Métricas por clase</h2>{_por_clase_html(r["por_clase"])}</section>
  <section><h2>Árbol contra las referencias</h2>{_modelos_html(r["modelos"])}</section>
  <section><h2>Estabilidad: 5 particiones</h2>{_particiones_html(r["modelos"])}</section>
  <section><h2>¿Qué profundidad?</h2>{_curva_html(r["curva"], r["profundidad"])}</section>
  <section><h2>Reglas aprendidas dentro del motor</h2>
    <div class="grande">{fid["iguales"]} de {fid["viajes"]}</div>
    <p class="nota">Con las {fid["reglas"]} reglas del árbol cargadas, el motor de la Actividad 1
      da la misma respuesta que el árbol en {fid["iguales"]} de {fid["viajes"]} viajes de prueba.</p>
    <table class="reglas"><tr><th>Regla</th><th>Condiciones</th><th>Viajes</th><th>Acierto</th></tr>
      {filas_reglas}</table></section>
</div>"""
    return _pagina("Evaluación del árbol", cuerpo)


# ---------------------------------------------------------------------------
# Página de la integración
# ---------------------------------------------------------------------------
def _valor_hecho(hecho, hechos):
    valor = hechos.get(hecho)
    if hecho == "hora" and isinstance(valor, int):
        return f"{valor // 60:02d}:{valor % 60:02d}"
    return "-" if valor is None else str(valor)


def condiciones_marcadas(regla, hechos):
    """[(condición en texto, valor del viaje, se cumple)] para mostrar la regla como lista de chequeo."""
    from ml.integracion import _texto_condicion
    return [(_texto_condicion(*c), _valor_hecho(c[0], hechos), inferencia._comparar(hechos, c))
            for c in regla["si"]]


def _condiciones_html(regla, hechos):
    return "".join(
        f'<div class="cond{"" if ok else " no"}"><span class="marca">{"✓" if ok else "✗"}</span>'
        f'<code>{escape(texto)}</code><span class="valor">{escape(valor)}</span></div>'
        for texto, valor, ok in condiciones_marcadas(regla, hechos))


def _razonamiento_html(traza, aprendidas, hechos):
    por_id = {r["id"]: r for r in aprendidas}
    pasos = []
    for t in traza:
        regla = por_id.get(t["regla"])
        if regla:
            clase = regla["entonces"][2]
            pasos.append(
                f'<li class="paso ml"><div class="cabeza"><span class="id ml">{t["regla"]}</span>'
                f'<span class="tipo">Aprendida por el árbol</span>'
                f'<span class="demora" style="background:{COLOR_DEMORA[clase]}">demora {clase}</span></div>'
                f'{_condiciones_html(regla, hechos)}</li>')
        else:
            pasos.append(
                f'<li class="paso"><div class="cabeza"><span class="id">{t["regla"]}</span>'
                f'<span class="tipo">Escrita a mano · Actividad 1</span></div>'
                f'<p>{escape(t["descripcion"])}</p></li>')
    return "".join(pasos) or '<p class="vacio">Ninguna regla se disparó.</p>'


ETIQUETAS = {"estacion_origen": "Origen", "estacion_destino": "Destino", "ruta": "Ruta",
             "num_transbordos": "Transbordos", "distancia_km": "Distancia (km)", "hora": "Hora",
             "dia_semana": "Día", "es_festivo": "Festivo", "clima": "Clima",
             "tiempo_base_min": "Tiempo base (min)"}


def _hechos_html(hechos):
    return '<dl class="hechos">' + "".join(
        f"<dt>{ETIQUETAS.get(k, k)}</dt><dd>{escape(_valor_hecho(k, hechos))}</dd>"
        for k in ETIQUETAS if k in hechos) + "</dl>"


def _cargadas_html(aprendidas, disparadas):
    filas = []
    for r in aprendidas:
        clase = r["entonces"][2]
        cubre = (f'<small>Cubre {r["soporte"]} viajes del dataset y acierta {pct(r["acierto"])}</small>'
                 if r.get("soporte") else "")
        texto = escape(r["descripcion"].removeprefix("Aprendida del árbol: "))
        filas.append(
            f'<li class="cargada{" disparada" if r["id"] in disparadas else ""}">'
            f'<span class="id ml">{r["id"]}</span><div>{texto}{cubre}</div>'
            f'<span class="demora" style="background:{COLOR_DEMORA[clase]}">{clase}</span></li>')
    return "".join(filas)


def html_integracion(mapa, camino, costo, origen, destino, hora, hechos, traza, aprendidas, nivel):
    titulo = f'{ESTACIONES[origen]["nombre"]} → {ESTACIONES[destino]["nombre"]}'
    disparadas = {t["regla"] for t in traza}
    if nivel:
        demora = (f'<span class="demora" style="background:{COLOR_DEMORA[nivel]};font-size:1.2rem">'
                  f'Demora {nivel.upper()}</span>')
    else:
        demora = '<span class="chip">Ninguna de las reglas cargadas aplica</span>'
    contexto = f'{hora} · {hechos.get("dia_semana", "")} · {hechos.get("clima", "")}'
    cargadas = [r for r in aprendidas if r["id"] in disparadas] if len(aprendidas) > 10 else aprendidas
    titulo_cargadas = (f"Regla aprendida usada (de {len(aprendidas)} cargadas)" if len(aprendidas) > 10
                       else f"Reglas aprendidas cargadas ({len(aprendidas)})")
    cuerpo = f"""
<header>
  <div><small>Actividad 1 + reglas aprendidas · {escape(contexto)}</small><h1>{escape(titulo)}</h1></div>
  <div class="total"><b>{costo:.1f} min</b>{demora}</div>
</header>
<div class="rejilla ruta">
  <section><h2>Recorrido (A*)</h2>{_recorrido_html(mapa, camino)}</section>
  <div class="columna">
    <section><h2>Razonamiento del motor sobre el viaje</h2><ol>{_razonamiento_html(traza, aprendidas, hechos)}</ol>
      <p class="nota">Mismo motor de inferencia de la Actividad 1. Azul: regla escrita por el equipo.
        Morado: regla que el árbol descubrió en los datos.</p></section>
    <section><h2>Hechos del viaje</h2>{_hechos_html(hechos)}</section>
    <section><h2>{titulo_cargadas}</h2><ul>{_cargadas_html(cargadas, disparadas)}</ul></section>
  </div>
</div>"""
    return _pagina("Reglas aprendidas en el motor", cuerpo)

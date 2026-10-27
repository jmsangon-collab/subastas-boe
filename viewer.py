# -*- coding: utf-8 -*-
"""Genera data/visor.html: un visor autonomo (tabla + filtros + mapa) con los
datos embebidos. Se abre con doble clic en el navegador. Boton de descarga CSV
(se abre directamente en Excel) sobre la seleccion filtrada.
"""
import json
import os

import dataset

OUT = os.path.join(os.path.dirname(__file__), "data", "visor.html")
# copia publicada en GitHub Pages (ver .github/workflows/pages.yml)
OUT_WEB = os.path.join(os.path.dirname(__file__), "web_publicar", "index.html")


def generar(abrir_navegador=False):
    datos = dataset.cargar()
    html = (TEMPLATE
            .replace("/*GLOSARIO*/", GLOSARIO_HTML)
            .replace("/*GUIA*/", GUIA_HTML)
            .replace("/*DATOS*/", json.dumps(datos, ensure_ascii=False)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for ruta in (OUT, OUT_WEB):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"[OK] visor -> {OUT} y {OUT_WEB}  ({len(datos)} lotes).")
    if abrir_navegador:
        abrir()


def _buscar_chrome():
    """Ruta al chrome.exe en Windows, o None si no se encuentra."""
    import shutil
    cand = [
        shutil.which("chrome"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in cand:
        if c and os.path.exists(c):
            return c
    return None


def abrir():
    """Abre el visor en Chrome (donde estas logueado en el portal). Si no hay
    Chrome, cae al navegador por defecto."""
    import subprocess
    import webbrowser
    chrome = _buscar_chrome()
    if chrome:
        subprocess.Popen([chrome, OUT])
        print(f"[OK] abriendo en Chrome: {chrome}")
    else:
        webbrowser.open(OUT)
        print("[!] Chrome no encontrado; abierto en el navegador por defecto.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Subastas BOE · Viviendas y terrenos</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
  :root{
    --bg:#f4f6f9;--panel:#ffffff;--line:#e3e8ee;--fg:#1c2430;--mut:#66788c;
    --acc:#1f6feb;--acc-soft:#e8f0fe;--ok:#0f9d6b;--ok-soft:#e3f6ee;--warn:#c77800;--warn-soft:#fff3df;
    --bad:#d43f3f;--bad-soft:#fde9e9;--navy:#132238;--r:10px;--sh:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.1)
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;font:14px/1.45 -apple-system,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--fg)}
  a{color:var(--acc);text-decoration:none}
  a:hover{text-decoration:underline}
  button{font:inherit;cursor:pointer}
  .mut{color:var(--mut)}

  /* ---- barra superior ---- */
  #top{height:56px;background:var(--navy);color:#fff;display:flex;align-items:center;gap:14px;padding:0 16px;position:relative;z-index:20}
  #top h1{font-size:17px;font-weight:650;margin:0;letter-spacing:.2px;white-space:nowrap}
  #top h1 small{font-weight:400;opacity:.65;font-size:12px;margin-left:6px}
  .est{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;letter-spacing:.2px;white-space:nowrap}
  .est.proxima_apertura{background:#e8f0fe;color:#1a56c4}
  .est.celebrandose{background:#e3f6ee;color:#0b7a52}
  .est.concluida{background:#eef1f5;color:#5b6b7c}
  .est.suspendida,.est.cancelada{background:#fff3df;color:#9a5b00}
  .star{border:0;background:transparent;font-size:18px;line-height:1;color:#c3ccd6;padding:0 4px;cursor:pointer}
  .star.on{color:#f5b301}
  .star:hover{color:#f5b301}
  #vSeg,#vAna{overflow:auto;padding:14px}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:16px}
  .kpi{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:14px 16px;box-shadow:var(--sh)}
  .kpi small{display:block;color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
  .kpi b{display:block;font-size:24px;font-weight:750;color:var(--navy);margin-top:2px}
  .kpi span{font-size:12px;color:var(--mut)}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:14px 16px;box-shadow:var(--sh);margin-bottom:14px}
  .card h3{margin:0 0 10px;font-size:14px}
  .card p.nota{font-size:12px;color:var(--mut);margin:0 0 10px}
  .card table{box-shadow:none}
  .bar{display:grid;grid-template-columns:150px 1fr 60px;gap:8px;align-items:center;font-size:12.5px;margin:4px 0}
  .bar i{display:block;height:12px;border-radius:6px;background:var(--acc)}
  .bar.w i{background:var(--warn)}
  .bar span{text-align:right;color:var(--mut)}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  @media (max-width:900px){.grid2{grid-template-columns:1fr}}
  #vista{display:inline-flex;background:rgba(255,255,255,.1);border-radius:8px;padding:3px;margin-left:auto}
  #vista button{border:0;background:transparent;color:#fff;opacity:.75;padding:6px 12px;border-radius:6px;font-weight:600;font-size:13px;white-space:nowrap}
  #vista button.on{background:#fff;color:var(--navy);opacity:1}
  .tb{border:1px solid rgba(255,255,255,.22);background:transparent;color:#fff;border-radius:8px;padding:6px 11px;font-size:13px;white-space:nowrap}
  .tb:hover{background:rgba(255,255,255,.12)}
  #btnFiltros{display:none}

  /* ---- cuerpo: panel filtros + contenido ---- */
  #cuerpo{display:flex;height:calc(100% - 56px);overflow:hidden}
  #filtros{width:290px;flex:none;background:var(--panel);border-right:1px solid var(--line);overflow-y:auto;overflow-x:hidden;padding:14px 16px 24px}
  #filtros h4{margin:14px 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
  #filtros h4:first-child{margin-top:0}
  #filtros label{display:block;font-size:12px;color:var(--mut);margin-bottom:8px}
  #filtros label span.t{display:block;margin-bottom:3px}
  #filtros input,#filtros select{width:100%;border:1px solid var(--line);border-radius:8px;padding:7px 9px;font-size:13px;background:#fff;color:var(--fg)}
  #filtros input:focus,#filtros select:focus{outline:2px solid var(--acc-soft);border-color:var(--acc)}
  .fila2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .fila2 input{min-width:0}
  .seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:8px}
  .seg button{flex:1;border:0;background:#fff;color:var(--mut);padding:7px 4px;font-size:12.5px}
  .seg button+button{border-left:1px solid var(--line)}
  .seg button.on{background:var(--acc);color:#fff;font-weight:600}
  .sw{display:flex!important;align-items:center;gap:8px;color:var(--fg)!important;cursor:pointer;font-size:13px!important;padding:3px 0}
  .sw input{display:none}
  .sw .track{width:32px;height:18px;background:#cfd6df;border-radius:10px;position:relative;transition:.2s;flex:none}
  .sw .track::after{content:"";position:absolute;top:2px;left:2px;width:14px;height:14px;background:#fff;border-radius:50%;transition:.2s;box-shadow:0 1px 2px rgba(0,0,0,.3)}
  .sw input:checked + .track{background:var(--ok)}
  .sw input:checked + .track::after{transform:translateX(14px)}
  #limpiar{width:100%;margin-top:14px;border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px;color:var(--mut)}
  #limpiar:hover{color:var(--fg);border-color:#b9c3cf}

  #main{flex:1;position:relative;min-width:0}
  .vista{position:absolute;inset:0;display:none}
  .vista.on{display:block}

  /* ---- tabla ---- */
  #vTabla{overflow:auto;padding:14px}
  table{border-collapse:separate;border-spacing:0;width:100%;font-size:13px;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--sh);overflow:hidden}
  th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap;vertical-align:top}
  th{position:sticky;top:0;background:#f8fafc;color:var(--mut);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.4px;cursor:pointer;user-select:none;z-index:2}
  th.num,td.num{text-align:right}
  th.on{color:var(--acc)}
  th .dir{font-size:9px;margin-left:3px}
  tbody tr{cursor:pointer}
  tbody tr:hover td{background:#f5f8fc}
  tbody tr.sel td{background:var(--acc-soft)}
  tbody tr:last-child td{border-bottom:0}
  td.desc{white-space:normal;min-width:260px;max-width:420px;color:#3b4756}
  td.desc span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  td.loc b{display:block;font-weight:600}
  td.loc small{color:var(--mut)}
  td.precio{font-weight:700;font-size:14px}
  td.precio small{display:block;font-weight:400;font-size:11px;color:var(--mut)}
  td.fil:hover{text-decoration:underline;color:var(--acc)}
  .pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:#eef1f5;color:#3b4756}
  .pill.vivienda{background:#e8f0fe;color:#1a56c4}
  .pill.solar{background:#fff3df;color:#9a5b00}
  .pill.finca_rustica{background:#e3f6ee;color:#0b7a52}
  .tag{display:inline-block;padding:1px 7px;border-radius:6px;font-size:11px;font-weight:600}
  .tag.ok{background:var(--ok-soft);color:var(--ok)}
  .tag.warn{background:var(--warn-soft);color:var(--warn)}
  .tag.bad{background:var(--bad-soft);color:var(--bad)}
  .tag.mut{background:#eef1f5;color:var(--mut)}
  .vacio{padding:60px 20px;text-align:center;color:var(--mut)}

  /* ---- mapa ---- */
  #mapa{position:absolute;inset:0}
  .leaflet-container{font:inherit}
  .leaflet-popup-content-wrapper{border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.25);padding:0}
  .leaflet-popup-content{margin:0;width:300px!important}
  .pop{padding:14px 16px 12px}
  .pop .hd{display:flex;align-items:baseline;gap:8px;margin-bottom:2px}
  .pop .precio{font-size:20px;font-weight:750;color:var(--navy)}
  .pop .sub{font-size:12px;color:var(--mut);margin-bottom:10px}
  .pop .grid{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12.5px;margin-bottom:10px}
  .pop .grid div small{display:block;color:var(--mut);font-size:10.5px;text-transform:uppercase;letter-spacing:.4px}
  .pop .grid div b{font-weight:600}
  .pop .txt{font-size:12px;color:#3b4756;line-height:1.4;margin-bottom:10px;max-height:64px;overflow:hidden}
  .pop .acc{display:flex;gap:8px}
  .pop .acc a,.pop .acc button{flex:1;text-align:center;border-radius:8px;padding:7px 8px;font-size:12.5px;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--fg)}
  .pop .acc a.pri{background:var(--acc);border-color:var(--acc);color:#fff}
  .pop .aviso{font-size:11px;color:var(--warn);background:var(--warn-soft);border-radius:6px;padding:4px 8px;margin-bottom:8px}
  .leyenda{background:#fff;border-radius:8px;padding:8px 10px;font-size:11.5px;box-shadow:var(--sh);line-height:1.7}
  .leyenda i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px;vertical-align:-1px}
  .mk{border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)}
  .mk.aprox{border:2px dashed #fff;opacity:.8}
  .ctl{background:#fff;border:0;border-radius:8px;padding:7px 10px;font-size:12.5px;font-weight:600;box-shadow:var(--sh);color:var(--fg)}
  .marker-cluster-small{background:rgba(31,111,235,.25)} .marker-cluster-small div{background:rgba(31,111,235,.85);color:#fff}
  .marker-cluster-medium{background:rgba(31,111,235,.25)} .marker-cluster-medium div{background:rgba(31,111,235,.85);color:#fff}
  .marker-cluster-large{background:rgba(19,34,56,.25)} .marker-cluster-large div{background:rgba(19,34,56,.85);color:#fff}

  /* ---- panel de detalle ---- */
  #detalle{position:absolute;top:0;right:0;bottom:0;width:420px;max-width:100%;background:var(--panel);border-left:1px solid var(--line);box-shadow:-8px 0 24px rgba(0,0,0,.08);transform:translateX(105%);transition:transform .22s;z-index:900;overflow-y:auto;padding:18px 20px 30px}
  #detalle.on{transform:none}
  #detalle .x{position:absolute;top:12px;right:12px;border:1px solid var(--line);background:#fff;border-radius:8px;width:30px;height:30px}
  #detalle .precio{font-size:26px;font-weight:750;color:var(--navy);margin:6px 0 0}
  #detalle .sub{color:var(--mut);font-size:13px;margin-bottom:12px}
  #detalle h5{margin:16px 0 6px;font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
  .kv{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;font-size:13px}
  .kv div small{display:block;color:var(--mut);font-size:11px}
  .kv div b{font-weight:600}
  #detalle p.txt{font-size:13px;line-height:1.5;color:#3b4756;white-space:pre-wrap}
  .btns{display:flex;gap:8px;margin-top:14px;flex-wrap:wrap}
  .btns a,.btns button{border-radius:8px;padding:9px 12px;font-size:13px;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--fg);flex:1;text-align:center}
  .btns .pri{background:var(--acc);border-color:var(--acc);color:#fff}

  /* ---- modales ---- */
  .modal{position:fixed;inset:0;background:rgba(10,18,30,.55);display:none;z-index:1000;padding:40px 16px;overflow:auto}
  .modal.on{display:block}
  .modal .box{max-width:820px;margin:0 auto;background:var(--panel);border-radius:14px;padding:24px 28px;box-shadow:0 20px 60px rgba(0,0,0,.35)}
  .modal h2{margin:0 0 4px;font-size:20px}
  .modal .x{float:right;background:#fff;border:1px solid var(--line);border-radius:8px;width:30px;height:30px;font-size:16px}
  .modal h3{color:var(--acc);margin:22px 0 8px;font-size:15px;border-bottom:1px solid var(--line);padding-bottom:4px}
  .modal p,.modal li{line-height:1.55}
  .modal .term{margin:0 0 9px}
  .modal .term b{color:var(--navy)}
  .modal .warn{background:var(--warn-soft);border:1px solid #f3d9a4;border-radius:8px;padding:10px 12px;margin:10px 0}
  .modal .ok{background:var(--ok-soft);border:1px solid #b5e5cf;border-radius:8px;padding:10px 12px;margin:10px 0}
  .modal .buscar{width:100%;margin:8px 0 4px;padding:8px 10px;border:1px solid var(--line);border-radius:8px}
  .modal .oculto{display:none}
  .modal table{width:100%;border-collapse:collapse;margin:8px 0;font-size:13px;box-shadow:none;border-radius:0}
  .modal td,.modal th{border:1px solid var(--line);padding:6px 8px;text-align:left;white-space:normal;position:static;text-transform:none;letter-spacing:0}

  @media (max-width:900px){
    #top{gap:8px;padding:0 10px}
    #top h1 small,.tb.opc{display:none}
    #vista button{padding:6px 8px;font-size:12px}
    #btnFiltros{display:inline-block}
    #filtros{position:absolute;z-index:30;top:0;bottom:0;left:0;transform:translateX(-105%);transition:transform .2s;width:min(320px,90vw)}
    #filtros.on{transform:none;box-shadow:8px 0 24px rgba(0,0,0,.15)}
    #cuerpo{position:relative}
    #vTabla{padding:8px}
    #detalle{width:100%}
  }
</style>
</head>
<body>
<div id="top">
  <button class="tb" id="btnFiltros" onclick="document.getElementById('filtros').classList.toggle('on')">☰ Filtros</button>
  <h1>Subastas BOE<small>viviendas · solares · fincas rústicas</small></h1>
  <div id="vista">
    <button data-v="tabla" class="on">Tabla</button><button data-v="mapa">Mapa</button><button data-v="seg">★ Seguimiento <span id="nSeg"></span></button><button data-v="ana">Análisis</button>
  </div>
  <button class="tb opc" onclick="abrirModal('mGloss')">Glosario</button>
  <button class="tb opc" onclick="abrirModal('mGuia')">Cómo funciona</button>
  <button class="tb" id="dl" title="Descarga la selección filtrada en CSV">⤓ CSV</button>
</div>

<div id="cuerpo">
  <aside id="filtros">
    <h4>Estado</h4>
    <div class="seg" id="estSeg">
      <button type="button" data-v="activas" class="on">Activas</button><button type="button" data-v="proxima_apertura">Próximas</button><button type="button" data-v="celebrandose">En curso</button><button type="button" data-v="concluida">Concluidas</button>
    </div>
    <h4>Buscar</h4>
    <label><input id="q" placeholder="localidad, dirección, descripción…"></label>
    <h4>Precio y tipo</h4>
    <label><span class="t">Precio máximo (€)</span><input id="pmax" type="number" step="5000" value="60000"></label>
    <label><span class="t">Subtipo</span><select id="sub"><option value="">Todos</option></select></label>
    <span class="t mut" style="font-size:12px;display:block;margin-bottom:3px">Clase</span>
    <div class="seg" id="claseSeg">
      <button type="button" data-v="" class="on">Todas</button><button type="button" data-v="urbano">Urbano</button><button type="button" data-v="rural">Rural</button>
    </div>
    <h4>Dónde</h4>
    <label><span class="t">Comunidad autónoma</span><select id="ccaa"><option value="">Todas</option></select></label>
    <label><span class="t">Provincia</span><select id="prov"><option value="">Todas</option></select></label>
    <label><span class="t">Localidad</span><input id="loc" list="locs" placeholder="Todas"><datalist id="locs"></datalist></label>
    <label class="sw"><input id="solomar" type="checkbox"><span class="track"></span> A menos de 500 m del mar</label>
    <label class="sw"><input id="soloc" type="checkbox"><span class="track"></span> Solo ubicación exacta</label>
    <h4>Ocupación y visita</h4>
    <label><span class="t">Situación posesoria</span><select id="poses"><option value="">Todas</option></select></label>
    <label class="sw"><input id="solovis" type="checkbox"><span class="track"></span> Solo visitables</label>
    <h4>Pujas y plazos</h4>
    <label class="sw"><input id="sinpuj" type="checkbox"><span class="track"></span> Sin pujas todavía</label>
    <label><span class="t">Cierra en menos de (horas)</span><input id="hmax" type="number" step="1" placeholder="ej: 24"></label>
    <div class="fila2">
      <label><span class="t">Cierra desde</span><input id="fdesde" type="date"></label>
      <label><span class="t">Cierra hasta</span><input id="fhasta" type="date"></label>
    </div>
    <h4>Orden</h4>
    <label><select id="orden">
      <option value="fecha_fin|1">Cierre (próximo primero)</option>
      <option value="horas_rest|1">Horas para cerrar</option>
      <option value="fecha_inicio|-1">Publicación (reciente primero)</option>
      <option value="precio_ref|1">Precio (barato primero)</option>
      <option value="eur_m2|1">€/m² (barato primero)</option>
      <option value="dist_costa_m|1">Distancia al mar</option>
    </select></label>
    <button id="limpiar">Limpiar filtros</button>
  </aside>

  <div id="main">
    <div class="vista on" id="vTabla"></div>
    <div class="vista" id="vMapa"><div id="mapa"></div></div>
    <div class="vista" id="vSeg"></div>
    <div class="vista" id="vAna"></div>
    <div id="detalle"></div>
  </div>
</div>

<div class="modal" id="mGloss" onclick="if(event.target===this)cerrarModal('mGloss')">
  <div class="box">
    <button class="x" onclick="cerrarModal('mGloss')">✕</button>
    <h2>Glosario de subastas</h2>
    <p class="mut">Busca un término:</p>
    <input class="buscar" id="glossQ" placeholder="depósito, cargas, cesión de remate…">
    <div id="glossList">/*GLOSARIO*/</div>
  </div>
</div>
<div class="modal" id="mGuia" onclick="if(event.target===this)cerrarModal('mGuia')">
  <div class="box">
    <button class="x" onclick="cerrarModal('mGuia')">✕</button>
    <h2>Cómo funciona una subasta</h2>
    <p class="mut">Requisitos, pasos, dinero necesario y preguntas frecuentes.</p>
    /*GUIA*/
  </div>
</div>

<script>
const DATOS = /*DATOS*/;
const fmt = n => n==null ? "—" : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g,".");
const eur = n => n==null ? "—" : fmt(n)+" €";
const esc = s => String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;");
const $ = id => document.getElementById(id);
let sortKey="fecha_fin", sortDir=1, filtrados=[], claseVal="", estVal="activas", vistaActual="tabla", selId=null;
const ESTADO = {proxima_apertura:"Próx. apertura", celebrandose:"Celebrándose", concluida:"Concluida", suspendida:"Suspendida", cancelada:"Cancelada"};
const tagEst = d => `<span class="est ${d.estado}">${ESTADO[d.estado]||d.estado||"?"}</span>`;
// ---- seguimiento (estrella), guardado en el navegador ----
let favs = new Set(); try{ favs = new Set(JSON.parse(localStorage.getItem('boe_seguimiento')||"[]")); }catch(e){}
function guardarFavs(){ try{ localStorage.setItem('boe_seguimiento', JSON.stringify([...favs])); }catch(e){} $('nSeg').textContent = favs.size ? `(${favs.size})` : ""; }
function toggleFav(id, ev){ if(ev) ev.stopPropagation(); favs.has(id) ? favs.delete(id) : favs.add(id); guardarFavs();
  document.querySelectorAll(`.star[data-id="${id}"]`).forEach(b=>b.classList.toggle('on',favs.has(id)));
  if(vistaActual==='seg') renderSeg(); }
const starBtn = id => `<button class="star ${favs.has(id)?'on':''}" data-id="${id}" title="Seguimiento" onclick="toggleFav('${id}',event)">★</button>`;
const PREC = {exacta:"Ubicación exacta", municipio:"Aprox. · centro del municipio", provincia:"Aprox. · capital de provincia"};

// ---------- utilidades de presentacion ----------
function horasTxt(hr){ if(hr==null||hr<0) return null; return hr<1 ? "<1 h" : hr<48 ? Math.round(hr)+" h" : Math.round(hr/24)+" días"; }
function fechaTxt(iso){ if(!iso) return "—"; const [y,m,d]=iso.split("-"); return `${d}/${m}/${y}`; }
function pujasTxt(d){ return d.num_pujas==null ? "sin datos" : d.num_pujas===0 ? "sin pujas" : d.num_pujas+(d.num_pujas>1?" pujas":" puja"); }
function tagCierre(d){
  const t=horasTxt(d.horas_rest); if(!t) return "";
  const cls = d.horas_rest<=24 ? "bad" : d.horas_rest<=72 ? "warn" : "mut";
  return `<span class="tag ${cls}">${t}</span>`;
}
function tagPujas(d){
  if(d.num_pujas==null) return `<span class="tag mut">?</span>`;
  return d.num_pujas===0 ? `<span class="tag ok">sin pujas</span>` : `<span class="tag mut">${pujasTxt(d)}</span>`;
}

// ---------- vista tabla / mapa ----------
function setVista(v){
  vistaActual=v;
  document.querySelectorAll('#vista button').forEach(b=>b.classList.toggle('on',b.dataset.v===v));
  ['tabla','mapa','seg','ana'].forEach(k=>$('v'+k[0].toUpperCase()+k.slice(1)).classList.toggle('on',v===k));
  if(v==='seg') renderSeg(); if(v==='ana') renderAna();
  if(v==='mapa'){ setTimeout(()=>{ map.invalidateSize(); if(!mapaAjustado){ zoomAFiltrados(); mapaAjustado=true; } },30); }
}
document.querySelectorAll('#vista button').forEach(b=>b.onclick=()=>setVista(b.dataset.v));

// ---------- mapa ----------
const VISTA_ESP=[[27.5,-19.0],[44.0,4.5]];
const map = L.map('mapa',{zoomControl:true}).fitBounds(VISTA_ESP);
let mapaAjustado=false;
const callejero = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:19, attribution:'© Esri, HERE, Garmin, OpenStreetMap'}).addTo(map);
const satelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {maxZoom:19, attribution:'© Esri, Maxar, Earthstar'});
const etiquetas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:19});
L.control.layers({"Callejero":callejero,"Satélite":satelite},{"Etiquetas sobre satélite":etiquetas},{position:'topright'}).addTo(map);
const cluster = L.markerClusterGroup({maxClusterRadius:45, spiderfyOnMaxZoom:true, showCoverageOnHover:false, disableClusteringAtZoom:15});
map.addLayer(cluster);
let markers = {};

const Home = L.Control.extend({options:{position:'topleft'},
  onAdd:function(){ const b=L.DomUtil.create('button','ctl'); b.textContent='Ver todos';
    L.DomEvent.disableClickPropagation(b); b.onclick=()=>{ if(!zoomAFiltrados()) map.fitBounds(VISTA_ESP); }; return b;}});
map.addControl(new Home());
const Ley = L.Control.extend({options:{position:'bottomleft'},
  onAdd:function(){ const d=L.DomUtil.create('div','leyenda');
    d.innerHTML='<i style="background:#1f6feb"></i>Lote<br><i style="background:#0f9d6b"></i>A &lt;500 m del mar<br><i style="background:#1f6feb;border:2px dashed #fff;opacity:.8;box-shadow:0 0 0 1px #1f6feb"></i>Ubicación aproximada';
    return d;}});
map.addControl(new Ley());

function zoomAFiltrados(){
  const pts=filtrados.filter(d=>d.lat).map(d=>[d.lat,d.lon]);
  if(pts.length){ map.fitBounds(pts,{padding:[40,40],maxZoom:13}); return true; }
  return false;
}
function icono(d){
  const cerca=d.dist_costa_m!=null&&d.dist_costa_m<=500;
  const aprox=d.precision&&d.precision!=='exacta';
  const col=cerca?'#0f9d6b':'#1f6feb';
  return L.divIcon({className:'', iconSize:[16,16], iconAnchor:[8,8],
    html:`<div class="mk ${aprox?'aprox':''}" style="width:16px;height:16px;background:${col}"></div>`});
}
function popupHtml(d){
  const aprox=d.precision&&d.precision!=='exacta';
  return `<div class="pop">
    <div class="hd"><span class="precio">${eur(d.precio_ref)}</span><span class="pill ${d.subtipo}">${esc(d.subtipo)}</span><span style="margin-left:auto">${starBtn(d.id_sub)}</span></div>
    <div style="margin-bottom:6px">${tagEst(d)}</div>
    <div class="sub">${esc(d.localidad||"")}${d.barrio?" · "+esc(d.barrio):""} · ${esc(d.provincia||"")}</div>
    ${aprox?`<div class="aviso">${PREC[d.precision]}. La ficha del BOE indica la dirección real.</div>`:""}
    <div class="grid">
      <div><small>Superficie</small><b>${d.superficie_m2?fmt(d.superficie_m2)+" m²":"—"}</b></div>
      <div><small>€/m²</small><b>${d.eur_m2?fmt(d.eur_m2):"—"}</b></div>
      <div><small>Al mar</small><b>${d.dist_costa_m!=null?fmt(d.dist_costa_m)+" m":"—"}</b></div>
      <div><small>Cierra</small><b>${fechaTxt(d.fecha_fin)} ${tagCierre(d)}</b></div>
      <div><small>Pujas</small><b>${pujasTxt(d)}</b></div>
      <div><small>Depósito</small><b>${eur(d.deposito)}</b></div>
    </div>
    <div class="txt">${esc((d.descripcion||"").slice(0,160))}${(d.descripcion||"").length>160?"…":""}</div>
    <div class="acc"><button onclick="abrirDetalle('${d.id_sub}')">Detalle</button><a class="pri" href="${esc(d.url)}" target="_blank">Ficha BOE ↗</a></div>
  </div>`;
}
function pintarMapa(){
  cluster.clearLayers(); markers={};
  filtrados.filter(d=>d.lat).forEach(d=>{
    const m=L.marker([d.lat,d.lon],{icon:icono(d)}).bindPopup(popupHtml(d),{maxWidth:320});
    m.on('click',()=>marcarFila(d.id_sub,false));
    markers[d.id_sub]=m; cluster.addLayer(m);
  });
}
function verEnMapa(id){
  const d=DATOS.find(x=>x.id_sub===id); if(!d||!d.lat) return;
  setVista('mapa'); cerrarDetalle();
  setTimeout(()=>{ map.flyTo([d.lat,d.lon], d.precision==='exacta'?17:13, {duration:.9});
    const m=markers[id]; if(m) setTimeout(()=>{ cluster.zoomToShowLayer(m,()=>m.openPopup()); },950); },60);
}

// ---------- panel de detalle ----------
function abrirDetalle(id){
  const d=DATOS.find(x=>x.id_sub===id); if(!d) return;
  marcarFila(id,false);
  const p=$('detalle'); const aprox=d.precision&&d.precision!=='exacta';
  p.innerHTML=`<button class="x" onclick="cerrarDetalle()">✕</button>
    ${tagEst(d)} <span class="pill ${d.subtipo}">${esc(d.subtipo)}</span> <span class="tag mut">${esc(d.clase)}</span> ${starBtn(d.id_sub)}
    <div class="precio">${eur(d.precio_ref)}</div>
    <div class="sub">${esc(d.direccion||"")}<br>${esc(d.localidad||"")}${d.barrio?" · "+esc(d.barrio):""} · ${esc(d.provincia||"")} · ${esc(d.ccaa||"")}</div>
    ${tagCierre(d)} ${tagPujas(d)}
    <h5>Importes</h5>
    <div class="kv">
      <div><small>Postura mínima</small><b>${eur(d.postura_minima)}</b></div>
      <div><small>Valor de subasta</small><b>${eur(d.valor_subasta)}</b></div>
      <div><small>Depósito para pujar</small><b>${eur(d.deposito)}</b></div>
      <div><small>Cantidad reclamada</small><b>${eur(d.cantidad_reclamada)}</b></div>
      <div><small>Puja máxima actual</small><b>${eur(d.puja_maxima)}</b></div>
      <div><small>Pujas</small><b>${pujasTxt(d)}</b></div>
    </div>
    <h5>Inmueble</h5>
    <div class="kv">
      <div><small>Superficie</small><b>${d.superficie_m2?fmt(d.superficie_m2)+" m²":"—"}</b></div>
      <div><small>€/m²</small><b>${d.eur_m2?fmt(d.eur_m2)+" €/m²":"—"}</b></div>
      <div><small>Distancia al mar</small><b>${d.dist_costa_m!=null?fmt(d.dist_costa_m)+" m":"—"}</b></div>
      <div><small>Ubicación</small><b>${d.lat?PREC[d.precision]||"—":"sin geolocalizar"}</b></div>
    </div>
    <h5>Ocupación y visita</h5>
    <div class="kv">
      <div><small>Situación posesoria</small><b>${esc(d.situacion_posesoria||"—")}</b></div>
      <div><small>Visitable</small><b>${esc(d.visitable||"—")}</b></div>
      <div><small>Vivienda habitual</small><b>${esc(d.vivienda_habitual||"—")}</b></div>
      <div><small>Cargas declaradas</small><b>${eur(d.cargas)}</b></div>
    </div>
    <h5>Plazos</h5>
    <div class="kv">
      <div><small>Publicación</small><b>${fechaTxt(d.fecha_inicio)}</b></div>
      <div><small>Cierre</small><b>${fechaTxt(d.fecha_fin)}${d.fecha_fin_dt?" "+d.fecha_fin_dt.slice(11):""}</b></div>
    </div>
    <h5>Descripción registral</h5>
    <p class="txt">${esc(d.descripcion||"")}</p>
    <div class="btns">
      ${d.lat?`<button onclick="verEnMapa('${d.id_sub}')">Ver en el mapa</button>`:""}
      ${d.anuncio_boe?`<a href="${esc(d.anuncio_boe)}" target="_blank">Anuncio BOE</a>`:""}
      <a class="pri" href="${esc(d.url)}" target="_blank">Ficha en subastas.boe.es ↗</a>
    </div>
    <p class="mut" style="font-size:11px;margin-top:14px">Id ${esc(d.id_sub)}. Comprueba siempre cargas, posesión, tramos y fechas en la ficha oficial.</p>`;
  p.classList.add('on');
}
function cerrarDetalle(){ $('detalle').classList.remove('on'); }
function marcarFila(id,scroll){
  selId=id;
  document.querySelectorAll('#vTabla tr[data-id]').forEach(r=>{ const on=r.dataset.id===id; r.classList.toggle('sel',on); if(on&&scroll) r.scrollIntoView({block:'center'}); });
}

// ---------- filtros ----------
function unicos(k){return [...new Set(DATOS.map(d=>d[k]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));}
function llenar(sel,vals){vals.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o);});}
llenar($('sub'), unicos('subtipo')); llenar($('ccaa'), unicos('ccaa')); llenar($('prov'), unicos('provincia')); llenar($('locs'), unicos('localidad')); llenar($('poses'), unicos('situacion_posesoria'));
const PROV_DE_CCAA={};
DATOS.forEach(d=>{ if(d.ccaa&&d.provincia){(PROV_DE_CCAA[d.ccaa]=PROV_DE_CCAA[d.ccaa]||new Set()).add(d.provincia);} });
function refrescarProv(){
  const c=$('ccaa').value, sel=$('prov'), prev=sel.value;
  const vals = c ? [...(PROV_DE_CCAA[c]||[])].sort() : unicos('provincia');
  sel.innerHTML='<option value="">Todas</option>'; llenar(sel, vals); sel.value = vals.includes(prev) ? prev : "";
}
$('ccaa').addEventListener('change',()=>{refrescarProv();aplica();});

function aplica(){
  const q=$('q').value.toLowerCase().trim(), pmax=parseFloat($('pmax').value)||Infinity;
  const sub=$('sub').value, ccaa=$('ccaa').value, prov=$('prov').value, loc=$('loc').value.trim().toLowerCase();
  const solomar=$('solomar').checked, sinpuj=$('sinpuj').checked, soloc=$('soloc').checked;
  const poses=$('poses').value, solovis=$('solovis').checked;
  const hmax=parseFloat($('hmax').value), fdesde=$('fdesde').value, fhasta=$('fhasta').value;
  const ahora=Date.now();
  DATOS.forEach(d=>{ d.horas_rest = d.fecha_fin_dt ? (new Date(d.fecha_fin_dt)-ahora)/3.6e6 : null; });
  filtrados = DATOS.filter(d=>{
    if(estVal==='activas'){ if(d.estado!=='proxima_apertura' && d.estado!=='celebrandose') return false; }
    else if(estVal && d.estado!==estVal) return false;
    if(d.precio_ref==null || d.precio_ref>pmax) return false;
    if(sub && d.subtipo!==sub) return false;
    if(claseVal && d.clase!==claseVal) return false;
    if(ccaa && d.ccaa!==ccaa) return false;
    if(prov && d.provincia!==prov) return false;
    if(loc && !((d.localidad||"").toLowerCase().includes(loc))) return false;
    if(solomar && (d.dist_costa_m==null || d.dist_costa_m>500)) return false;
    if(sinpuj && !d.sin_pujas) return false;
    if(soloc && d.precision!=='exacta') return false;
    if(poses && d.situacion_posesoria!==poses) return false;
    if(solovis && !/^s[ií]/i.test(d.visitable||"")) return false;
    if(!isNaN(hmax) && (d.horas_rest==null || d.horas_rest<0 || d.horas_rest>hmax)) return false;
    if(fdesde && (!d.fecha_fin || d.fecha_fin<fdesde)) return false;
    if(fhasta && (!d.fecha_fin || d.fecha_fin>fhasta)) return false;
    if(q){const t=((d.descripcion||"")+" "+(d.localidad||"")+" "+(d.direccion||"")+" "+(d.provincia||"")).toLowerCase(); if(!t.includes(q)) return false;}
    return true;
  });
  filtrados.sort((a,b)=>{const x=a[sortKey],y=b[sortKey]; if(x==null)return 1; if(y==null)return -1; return (x>y?1:x<y?-1:0)*sortDir;});
  render();
}

function tablaHtml(lista, ordenable){
  const cols=[["estado","Estado",""],["precio_ref","Precio","num"],["subtipo","Tipo",""],["superficie_m2","m²","num"],["eur_m2","€/m²","num"],
    ["dist_costa_m","Al mar","num"],["localidad","Localidad",""],["descripcion","Descripción",""],
    ["fecha_fin","Cierre",""],["num_pujas","Pujas",""]];
  let h="<table><thead><tr><th></th>";
  cols.forEach(c=>h+=`<th class="${c[2]} ${ordenable&&sortKey===c[0]?'on':''}" ${ordenable?`data-k="${c[0]}"`:''}>${c[1]}${ordenable&&sortKey===c[0]?`<span class="dir">${sortDir>0?'▲':'▼'}</span>`:''}</th>`);
  h+="<th></th></tr></thead><tbody>";
  lista.forEach(d=>{
    const cerca = d.dist_costa_m!=null && d.dist_costa_m<=500;
    h+=`<tr data-id="${d.id_sub}" class="${selId===d.id_sub?'sel':''}">`+
      `<td>${starBtn(d.id_sub)}</td><td>${tagEst(d)}</td>`+
      `<td class="precio num">${eur(d.precio_ref)}${d.deposito?`<small>dep. ${eur(d.deposito)}</small>`:""}</td>`+
      `<td class="fil" data-f="sub" data-v="${esc(d.subtipo)}"><span class="pill ${d.subtipo}">${esc(d.subtipo)}</span></td>`+
      `<td class="num">${d.superficie_m2?fmt(d.superficie_m2):""}</td><td class="num">${d.eur_m2?fmt(d.eur_m2):""}</td>`+
      `<td class="num">${d.dist_costa_m==null?"":cerca?`<span class="tag ok">${fmt(d.dist_costa_m)} m</span>`:fmt(d.dist_costa_m)+" m"}</td>`+
      `<td class="loc"><b class="fil" data-f="loc" data-v="${esc(d.localidad)}">${esc(d.localidad||"")}</b><small class="fil" data-f="prov" data-v="${esc(d.provincia)}">${esc(d.provincia||"")}</small></td>`+
      `<td class="desc"><span title="${esc(d.descripcion)}">${esc(d.descripcion||"")}</span></td>`+
      `<td>${fechaTxt(d.fecha_fin)}<br>${tagCierre(d)}</td>`+
      `<td>${d.estado==='concluida'&&d.puja_maxima?`${pujasTxt(d)}<br><small class="mut">máx. ${eur(d.puja_maxima)}${d.pct_valor?` (${d.pct_valor}%)`:""}</small>`:tagPujas(d)}</td>`+
      `<td><a href="${esc(d.url)}" target="_blank" onclick="event.stopPropagation()">BOE ↗</a></td></tr>`;
  });
  return h+"</tbody></table>";
}
function activarTabla(cont){
  cont.querySelectorAll('tr[data-id]').forEach(tr=>{ tr.onclick=()=>abrirDetalle(tr.dataset.id); });
  cont.querySelectorAll('.fil').forEach(td=>td.onclick=(e)=>{ e.stopPropagation(); const el=$(td.dataset.f); if(el){ el.value=td.dataset.v; aplica(); } });
}
function render(){
  $('vTabla').innerHTML = filtrados.length ? tablaHtml(filtrados,true) : '<div class="vacio">Ningún lote cumple los filtros.</div>';
  document.querySelectorAll('#vTabla th[data-k]').forEach(th=>th.onclick=()=>{ const k=th.dataset.k; sortDir=(k===sortKey)?-sortDir:1; sortKey=k; aplica();});
  activarTabla($('vTabla'));
  pintarMapa();
  if(vistaActual==='seg') renderSeg(); if(vistaActual==='ana') renderAna();
}
function renderSeg(){
  const lista = DATOS.filter(d=>favs.has(d.id_sub)).sort((a,b)=>(a.fecha_fin||"z")<(b.fecha_fin||"z")?-1:1);
  $('vSeg').innerHTML = lista.length ? `<p class="mut" style="margin:0 0 10px;font-size:12.5px">${lista.length} subastas en seguimiento. Se guardan en este navegador. Pulsa ★ para quitar.</p>`+tablaHtml(lista,false)
    : '<div class="vacio">Sin subastas en seguimiento. Marca la ★ de cualquier lote en la tabla, el mapa o el detalle.</div>';
  activarTabla($('vSeg'));
}

// ---------- analisis de subastas concluidas ----------
function pct(a,b){ return b ? Math.round(100*a/b) : 0; }
function barras(titulo, grupos, cls){
  const max=Math.max(1,...grupos.map(g=>g[1]));
  return `<div class="card"><h3>${titulo}</h3>`+grupos.map(g=>`<div class="bar ${cls||''}"><span style="text-align:left;color:var(--fg)">${esc(g[0])}</span><i style="width:${pct(g[1],max)}%"></i><span>${g[2]!=null?g[2]:g[1]}</span></div>`).join("")+`</div>`;
}
function renderAna(){
  // concluidas que cumplen los filtros de tipo/lugar (ignora estado y precio)
  const sub=$('sub').value, ccaa=$('ccaa').value, prov=$('prov').value, loc=$('loc').value.trim().toLowerCase();
  const C = DATOS.filter(d=>d.estado==='concluida' && (!sub||d.subtipo===sub) && (!claseVal||d.clase===claseVal) && (!ccaa||d.ccaa===ccaa) && (!prov||d.provincia===prov) && (!loc||(d.localidad||"").toLowerCase().includes(loc)));
  if(!C.length){ $('vAna').innerHTML='<div class="vacio">Todavía no hay subastas concluidas en la base de datos.<br><small>Se incorporan con <code>python run.py historico</code> (el proceso automático lo hace a diario).</small></div>'; return; }
  const conDato=C.filter(d=>d.num_pujas!=null), sinP=conDato.filter(d=>d.num_pujas===0), unaP=conDato.filter(d=>d.num_pujas===1);
  const ratios=C.filter(d=>d.pct_valor!=null).map(d=>d.pct_valor).sort((a,b)=>a-b);
  const mediana=ratios.length?ratios[Math.floor(ratios.length/2)]:null;
  const bajo50=C.filter(d=>d.pct_valor!=null&&d.pct_valor<50).length, bajo70=C.filter(d=>d.pct_valor!=null&&d.pct_valor<70).length;
  let h=`<div class="kpis">
    <div class="kpi"><small>Concluidas analizadas</small><b>${C.length}</b><span>${conDato.length} con datos de pujas</span></div>
    <div class="kpi"><small>Sin ninguna puja</small><b>${pct(sinP.length,conDato.length)}%</b><span>${sinP.length} subastas</span></div>
    <div class="kpi"><small>Con una sola puja</small><b>${pct(unaP.length,conDato.length)}%</b><span>${unaP.length} subastas</span></div>
    <div class="kpi"><small>Mejor puja / valor de subasta</small><b>${mediana!=null?mediana+"%":"—"}</b><span>mediana, ${ratios.length} con puja</span></div>
    <div class="kpi"><small>Cerradas por debajo del 50%</small><b>${bajo50}</b><span>del valor de subasta · ${bajo70} por debajo del 70%</span></div>
  </div>
  <p class="mut" style="font-size:12px;margin:0 0 14px">Fuente: pestaña de pujas del portal en subastas concluidas. La mejor puja no equivale a la adjudicación definitiva (el juzgado o la AEAT deben aprobar el remate; sin pujas, el acreedor puede pedir la adjudicación). Úsalo como orientación de mercado.</p>`;
  const tramos=[["Sin pujas",sinP.length],["< 50 %",0],["50–70 %",0],["70–100 %",0],["≥ 100 %",0]];
  C.forEach(d=>{ if(d.pct_valor==null) return; const r=d.pct_valor; tramos[r<50?1:r<70?2:r<100?3:4][1]++; });
  const agg=(k)=>{ const m={}; conDato.forEach(d=>{ const g=m[d[k]]=m[d[k]]||[0,0]; g[0]++; if(d.num_pujas===0) g[1]++; }); return Object.entries(m).sort((a,b)=>b[1][0]-a[1][0]).map(([n,[t,s]])=>[`${n} (${t})`, pct(s,t), pct(s,t)+"%"]); };
  h+=`<div class="grid2">${barras("Mejor puja como % del valor de subasta",tramos)}${barras("Sin pujas por tipo (% de las concluidas)",agg('subtipo'),'w')}</div>`;
  h+=`<div class="grid2">${barras("Sin pujas por provincia",agg('provincia'),'w')}${barras("Sin pujas por clase",agg('clase'),'w')}</div>`;
  const baratas=C.filter(d=>d.pct_valor!=null&&d.num_pujas>0).sort((a,b)=>a.pct_valor-b.pct_valor).slice(0,40);
  h+=`<div class="card"><h3>Cerradas más baratas respecto al valor de subasta</h3><p class="nota">Mejor puja más baja en proporción al valor. ${baratas.length} de ${C.length}.</p>${baratas.length?tablaHtml(baratas,false):""}</div>`;
  const desiertas=sinP.slice().sort((a,b)=>(b.fecha_fin||"")<(a.fecha_fin||"")?-1:1).slice(0,40);
  h+=`<div class="card"><h3>Quedaron sin pujas (desiertas)</h3><p class="nota">Pueden volver a salir a subasta o adjudicarse al acreedor. Últimas ${desiertas.length}.</p>${desiertas.length?tablaHtml(desiertas,false):""}</div>`;
  $('vAna').innerHTML=h; activarTabla($('vAna'));
}

$('dl').onclick=()=>{
  const cols=["id_sub","subtipo","estado","precio_ref","valor_subasta","postura_minima","deposito","superficie_m2","eur_m2",
    "descripcion","direccion","localidad","provincia","ccaa","dist_costa_m","lat","lon","precision","fecha_inicio","fecha_fin","num_pujas","puja_maxima","pct_valor","situacion_posesoria","visitable","vivienda_habitual","cargas","anuncio_boe","url"];
  const e=v=>'"'+String(v==null?"":v).replace(/"/g,'""')+'"';
  let csv="﻿"+cols.join(";")+"\n"; filtrados.forEach(d=>csv+=cols.map(c=>e(d[c])).join(";")+"\n");
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"})); a.download="subastas_filtradas.csv"; a.click();
};
['q','pmax','sub','prov','loc','solomar','sinpuj','hmax','fdesde','fhasta','soloc','poses','solovis'].forEach(id=>{ $(id).addEventListener('input',aplica); $(id).addEventListener('change',aplica); });
document.querySelectorAll('#estSeg button').forEach(b=>b.onclick=()=>{ document.querySelectorAll('#estSeg button').forEach(x=>x.classList.remove('on')); b.classList.add('on'); estVal=b.dataset.v; aplica();});
document.querySelectorAll('#claseSeg button').forEach(b=>b.onclick=()=>{ document.querySelectorAll('#claseSeg button').forEach(x=>x.classList.remove('on')); b.classList.add('on'); claseVal=b.dataset.v; aplica();});
$('orden').addEventListener('change',e=>{ const [k,dd]=e.target.value.split("|"); sortKey=k; sortDir=parseInt(dd); aplica();});
$('limpiar').onclick=()=>{ ['q','loc','hmax','fdesde','fhasta'].forEach(id=>$(id).value=""); ['sub','ccaa','prov','poses'].forEach(id=>$(id).value=""); $('pmax').value=60000;
  ['solomar','sinpuj','soloc','solovis'].forEach(id=>$(id).checked=false); claseVal=""; estVal="activas"; document.querySelectorAll('#estSeg button').forEach(x=>x.classList.toggle('on',x.dataset.v==="activas")); document.querySelectorAll('#claseSeg button').forEach(x=>x.classList.toggle('on',x.dataset.v==="")); refrescarProv(); aplica(); };

// ---------- modales ----------
function abrirModal(id){$(id).classList.add('on');}
function cerrarModal(id){$(id).classList.remove('on');}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){ document.querySelectorAll('.modal.on').forEach(m=>m.classList.remove('on')); cerrarDetalle(); }});
$('glossQ').addEventListener('input',e=>{ const q=e.target.value.toLowerCase().trim();
  document.querySelectorAll('#glossList .term').forEach(t=>{ t.classList.toggle('oculto', q && !t.textContent.toLowerCase().includes(q));}); });
guardarFavs(); aplica();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Contenido de los dos modales de ayuda (glosario + guia/FAQ). Documentado a
# partir de la LEC (arts. 647-680) y la reforma LO 1/2025, de 2 de enero.
def _terminos(pares):
    return "\n".join(f'<div class="term"><b>{t}.</b> {d}</div>' for t, d in pares)


GLOSARIO_HTML = _terminos([
    ("Valor de tasación", "Precio en que se valora el inmueble (por perito o, en hipoteca, el pactado en escritura). Es el punto de partida para calcular todo lo demás."),
    ("Valor de subasta (tipo)", "Cantidad por la que el bien «sale» a subasta y sobre la que se calculan los porcentajes legales (depósito, umbrales). Suele coincidir con la tasación."),
    ("Postura / Puja", "Cada oferta económica que haces por el bien. Son sinónimos."),
    ("Puja mínima", "La cantidad más baja que el sistema admite como primera oferta válida. El portal la indica en cada subasta."),
    ("Tramos", "Escalón mínimo en que suben las pujas (p. ej. de 2.000 € en 2.000 €). No puedes ofertar cantidades intermedias, solo múltiplos del tramo."),
    ("Depósito / consignación", "Dinero que bloqueas por adelantado para poder pujar. Garantiza que, si ganas, pagarás. Se devuelve a quien no gana."),
    ("Importe del depósito", "El porcentaje del valor de subasta que hay que consignar: <b>5 %</b> en subastas de la Agencia Tributaria y notariales; <b>20 %</b> para inmuebles en ejecuciones judiciales presentadas desde el 3-abr-2025 (antes 5 %)."),
    ("Sobre cerrado", "Modalidad en que dejas una puja máxima reservada: el sistema puja por ti tramo a tramo solo lo necesario para ir ganando, sin revelar tu tope."),
    ("Adjudicación (remate)", "Acto por el que el bien se atribuye al mejor postor, una vez cerrada la subasta y aprobado el remate."),
    ("Cesión de remate", "Ceder tu posición de adjudicatario a un tercero para que el inmueble se inscriba a su nombre. En ejecución normalmente solo puede hacerlo el ejecutante (acreedor)."),
    ("Quiebra de la subasta", "Cuando el ganador no paga el resto en plazo: pierde el depósito y la subasta se resuelve a favor de los siguientes postores o se reabre."),
    ("Ejecutante", "Quien promueve la ejecución para cobrar (banco, Hacienda, particular). Es el acreedor."),
    ("Ejecutado", "Aquel contra quien se dirige la ejecución: el deudor o dueño del bien embargado."),
    ("Acreedor / Deudor", "Acreedor: quien tiene derecho a cobrar. Deudor: quien debe pagar."),
    ("Cargas", "Gravámenes que pesan sobre la finca inscritos en el Registro: hipotecas, embargos, servidumbres, usufructos…"),
    ("Cargas anteriores / preferentes", "Cargas inscritas ANTES de la que motiva la subasta. Son las peligrosas: <b>no se cancelan</b> y el comprador las hereda."),
    ("Subrogación de cargas", "Regla por la que el rematante se queda con las cargas anteriores subsistentes. Puedes acabar pagando el remate <b>y además</b> una hipoteca previa."),
    ("Certificación de dominio y cargas", "Documento del Registro con el titular actual y todas las cargas de la finca. Fuente esencial para saber qué compras."),
    ("Nota simple", "Extracto informativo (no certificado) del Registro con titularidad y cargas. Barata y muy recomendable antes de pujar."),
    ("Referencia catastral", "Código único de 20 caracteres que identifica el inmueble en el Catastro. Permite ver su superficie y ubicación."),
    ("Hipoteca", "Garantía sobre un inmueble que permite al acreedor subastarlo si no se paga la deuda garantizada."),
    ("Embargo", "Traba judicial o administrativa sobre un bien para asegurar el cobro de una deuda. Se anota en el Registro."),
    ("Usufructo", "Derecho a usar y disfrutar un bien ajeno (habitarlo, alquilarlo) sin ser su dueño."),
    ("Nuda propiedad", "Propiedad «vacía» de uso: eres dueño pero no puedes usar el bien mientras exista un usufructo. Al extinguirse este, recuperas el pleno dominio."),
    ("Pleno dominio", "Propiedad completa: nuda propiedad + usufructo en la misma persona (usar, disfrutar y disponer sin límites)."),
    ("Proindiviso / cuota", "Copropiedad: varios dueños por cuotas (p. ej. 50 %). Ojo: muchas subastas venden solo <b>una cuota</b>, no el inmueble entero."),
    ("Finca urbana vs. rústica", "Urbana: suelo o edificación en suelo urbano (viviendas, locales). Rústica: suelo agrícola/forestal o no urbanizable. Cambian usos, valor y límites."),
    ("Ocupantes / posesión", "Quien vive u ocupa el inmueble. Ganar la subasta da la propiedad, pero <b>no siempre la posesión inmediata</b>: puede haber que desalojar."),
    ("Lanzamiento / desahucio", "Procedimiento judicial para desalojar a los ocupantes y entregarte la posesión. Requiere trámite adicional y tiempo."),
    ("ITP / IVA en la adjudicación", "Impuesto que grava la compra. Según quién venda y qué se venda, tributa por ITP (particular) o por IVA + AJD (empresario). No los dos a la vez."),
    ("Testimonio del decreto de adjudicación", "Documento judicial que acredita que se te ha adjudicado el bien. Es el «título» con el que inscribes la propiedad en el Registro."),
    ("Mandamiento de cancelación de cargas", "Orden judicial al Registro para cancelar la carga que originó la ejecución y las posteriores. Es lo que «limpia» la finca (nunca de las cargas anteriores)."),
])


GUIA_HTML = r"""
<div class="warn"><b>Antes de nada — la reforma de 2025.</b> La Ley Orgánica 1/2025 cambió el régimen
de las subastas <i>judiciales</i> (por ejemplo, el depósito para inmuebles pasó del 5 % al 20 %). Se
aplica a ejecuciones cuya demanda se presentó desde el <b>3 de abril de 2025</b>; las anteriores siguen
con las reglas viejas. Las subastas de la <b>Agencia Tributaria</b> y las <b>notariales</b> mantienen el
<b>5 %</b>. Comprueba siempre las condiciones concretas de cada subasta.</div>

<h3>¿Qué requisitos hay para participar?</h3>
<p>Estar dado de alta como usuario en el <b>Portal de Subastas del BOE</b> (subastas.boe.es), lo que exige
<b>identificación electrónica</b>: certificado digital, DNI electrónico o <b>Cl@ve</b>. Después, para cada
subasta concreta hay que <b>constituir el depósito</b> por la pasarela de pago del portal; solo entonces
quedas habilitado para pujar. No es obligatorio abogado ni procurador, pero sí muy recomendable asesorarse.</p>

<h3>Pasos, de principio a fin</h3>
<ol>
  <li><b>Buscar</b> la subasta (esto es lo que hace este visor).</li>
  <li><b>Estudiar el expediente</b>: edicto, valor, cargas, situación posesoria y documentación aneja.</li>
  <li><b>Comprobar por tu cuenta</b>: nota simple en el Registro, referencia catastral, IBI y deudas de comunidad, y si está ocupado.</li>
  <li><b>Darte de alta</b> en el portal y <b>constituir el depósito</b>.</li>
  <li><b>Pujar</b> durante el plazo (las subastas del BOE duran, en general, <b>20 días naturales</b>; se prorrogan si hay pujas al final).</li>
  <li><b>Cierre</b> y envío de la mejor postura al Juzgado/Notaría.</li>
  <li><b>Aprobación del remate</b> (decreto de adjudicación) si la puja alcanza los umbrales legales.</li>
  <li><b>Pagar el resto del precio</b> en plazo.</li>
  <li>Obtener el <b>testimonio del decreto</b> y el <b>mandamiento de cancelación de cargas</b>.</li>
  <li><b>Inscribir</b> en el Registro a tu nombre y, si procede, <b>tomar posesión</b> (con lanzamiento si hay ocupantes).</li>
</ol>

<h3>💶 ¿Cuánto dinero en efectivo necesito para pujar?</h3>
<p>Necesitas <b>consignar por adelantado un porcentaje del valor de subasta</b>:</p>
<ul>
  <li><b>Agencia Tributaria y notariales: 5 %</b> del valor de subasta.</li>
  <li><b>Judicial (demanda desde el 3-abr-2025): 20 %</b> para inmuebles (mín. 1.000 €). Antes era el 5 %.</li>
</ul>
<div class="ok"><b>Ejemplo real (piso de Sevilla, subasta AT):</b> valor de subasta 204.119,28 € →
depósito para pujar = <b>10.205,96 € (5 %)</b>. Puja mínima 20.411,93 €, tramos de 2.000 €.</div>
<p>El depósito se ingresa <b>antes de pujar</b> por la pasarela del portal y queda retenido. A quien
<b>no gana</b> se le devuelve al cerrarse la subasta; al <b>ganador</b> se le imputa al precio (lo paga a cuenta).</p>

<h3>¿Qué pasa si gano? Plazo de pago y consecuencias de no pagar</h3>
<p>Debes pagar la <b>diferencia</b> entre el depósito y el precio total del remate. Tras la reforma el plazo
del mejor postor se redujo <b>de 40 a 20 días</b> desde el cierre (art. 670 LEC). Si no pagas
(<b>quiebra de la subasta</b>) <b>pierdes el depósito</b>, que se aplica a la deuda, y el bien pasa a los
siguientes postores o se reabre la subasta.</p>

<h3>¿Cómo suben las pujas? (tramos)</h3>
<p>El tramo es el escalón mínimo de subida. Con tramo de 2.000 €, sobre una postura de 80.000 € la siguiente
válida es 82.000 €. En <b>sobre cerrado</b>, el sistema sube solo un tramo por encima del rival hasta tu tope.</p>

<h3>⚠️ Riesgos clave</h3>
<ul>
  <li><b>Cargas que subsisten:</b> las anteriores/preferentes <b>NO se cancelan</b>; te subrogas en ellas. Lee la certificación de cargas.</li>
  <li><b>Ocupantes:</b> ganar da la propiedad, no siempre la posesión. Puede hacer falta un lanzamiento (coste y demora).</li>
  <li><b>Estado del inmueble:</b> normalmente <b>no es visitable</b> por dentro; compras «a ciegas».</li>
  <li><b>Deudas pendientes:</b> respondes de la comunidad del año en curso y los <b>3 años anteriores</b> (art. 9 LPH), más el IBI.</li>
</ul>

<h3>Impuestos que paga el adjudicatario</h3>
<ul>
  <li><b>ITP</b> si vende un particular (habitual): tipo autonómico, orientativamente <b>6 %–10 %</b>.</li>
  <li><b>IVA + AJD</b> si vende empresario/profesional: IVA 10 % (vivienda) o 21 % (suelo/local) + AJD 0,5 %–1,5 %.</li>
  <li>Regla práctica: <b>o ITP o IVA</b>, no ambos. Suma también inscripción registral y posibles gastos de cancelación/lanzamiento.</li>
</ul>

<h3>Judicial vs. notarial vs. Agencia Tributaria</h3>
<table>
  <tr><th>Tipo</th><th>Quién la ordena</th><th>Depósito</th><th>Título para inscribir</th></tr>
  <tr><td>Judicial</td><td>Juzgado (LEC 647-680)</td><td>20 % inmuebles (5 % antes de 2025)</td><td>Decreto de adjudicación</td></tr>
  <tr><td>Notarial</td><td>Notario</td><td>5 %</td><td>Acta notarial de adjudicación</td></tr>
  <tr><td>Agencia Tributaria</td><td>AEAT (apremio)</td><td>5 %</td><td>Certificación del acta de adjudicación</td></tr>
</table>
<p>En los tres casos se puja por el <b>mismo portal del BOE</b>, pero cambian la norma, el porcentaje y el documento final.</p>

<h3>¿Mi puja basta para que me adjudiquen? (umbrales, art. 670 LEC)</h3>
<ul>
  <li><b>≥ 70 % del valor de subasta:</b> se aprueba el remate directamente.</li>
  <li><b>&lt; 70 %:</b> el deudor tiene 10 días para presentar a un tercero que mejore (≥ 60 %, o menos si cubre toda la deuda).</li>
  <li><b>Si no hay mejora:</b> se aprueba al mejor postor si ofrece <b>≥ 50 %</b>; excepcionalmente por menos si cubre el crédito, nunca por debajo del <b>40 %</b>.</li>
</ul>
<div class="warn"><b>Vivienda habitual y adjudicación al acreedor:</b> los arts. 670 y 671 LEC exigen
umbrales reforzados (en torno al 70 %, o la deuda total si es mayor). Verifica el supuesto concreto.</div>

<p class="mut" style="margin-top:18px;font-size:12px">Información orientativa, no es asesoramiento jurídico ni fiscal.
Basado en la LEC (arts. 647-680) y la LO 1/2025, de 2 de enero. Revisa siempre las condiciones de cada subasta.</p>
"""

if __name__ == "__main__":
    generar()

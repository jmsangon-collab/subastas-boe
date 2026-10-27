# -*- coding: utf-8 -*-
"""Carga los lotes de la BD y calcula metricas intrinsecas del propio lote:
precio_ref (postura minima o valor de subasta), superficie, eur_m2, clase
(rural/urbano), CCAA y fechas normalizadas.
Fuente unica compartida por el export y el visor HTML.
"""
import re
import db
import provincias

CAMPOS = ["id_sub", "subtipo", "estado", "precio_ref", "valor_subasta",
          "postura_minima", "deposito", "cantidad_reclamada", "superficie_m2", "eur_m2",
          "descripcion", "direccion", "localidad", "barrio", "distrito",
          "provincia", "ccaa", "clase", "dist_costa_m", "lat", "lon", "precision",
          "fecha_inicio", "fecha_fin", "fecha_fin_dt", "num_pujas", "puja_maxima",
          "sin_pujas", "pct_valor", "vivienda_habitual", "situacion_posesoria",
          "visitable", "cargas", "anuncio_boe", "url"]


def _clase(descripcion, subtipo):
    """rural / urbano / desconocido, segun la descripcion registral del BOE."""
    t = (descripcion or "").upper()
    if "RUSTICA" in t or "R\xdaSTICA" in t or "RÚSTICA" in t:
        return "rural"
    if "URBANA" in t:
        return "urbano"
    return {"finca_rustica": "rural", "solar": "urbano", "vivienda": "urbano"}.get(subtipo, "desconocido")


def _fecha_iso(txt):
    """Extrae la fecha ISO (YYYY-MM-DD) del texto del BOE. None si no hay."""
    if not txt:
        return None
    m = re.search(r"ISO:\s*(\d{4}-\d{2}-\d{2})", txt)
    if m:
        return m.group(1)
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", txt)  # respaldo dd-mm-yyyy
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def _fecha_iso_dt(txt):
    """Fecha+hora ISO 'YYYY-MM-DDTHH:MM' del texto del BOE. None si no hay hora."""
    if not txt:
        return None
    m = re.search(r"ISO:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", txt)
    return m.group(1) if m else None


def cargar():
    con = db.conectar()
    filas = con.execute("SELECT * FROM subastas").fetchall()
    out = []
    for r in filas:
        d = dict(r)
        d["precio_ref"] = d.get("postura_minima") or d.get("valor_subasta")
        sup = d.get("superficie_m2")
        d["eur_m2"] = round(d["precio_ref"] / sup, 1) if (d["precio_ref"] and sup) else None
        d["clase"] = _clase(d.get("descripcion"), d.get("subtipo"))
        d["ccaa"] = provincias.ccaa(d.get("provincia_cod"))
        d["fecha_inicio"] = _fecha_iso(d.get("fecha_inicio"))
        fin_raw = d.get("fecha_fin")
        d["fecha_fin_dt"] = _fecha_iso_dt(fin_raw)
        d["fecha_fin"] = _fecha_iso(fin_raw)
        ge = d.get("geocode_estado")
        d["precision"] = "exacta" if ge == "ok" else ge  # BD antiguas: ok == exacta
        np = d.get("num_pujas")
        d["sin_pujas"] = (np == 0)
        vs = d.get("valor_subasta")
        pm = d.get("puja_maxima")
        d["pct_valor"] = round(100 * pm / vs, 1) if (pm and vs) else None
        out.append({k: d.get(k) for k in CAMPOS})
    return out

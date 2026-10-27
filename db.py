# -*- coding: utf-8 -*-
"""Almacenamiento SQLite de las subastas."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "subastas.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS subastas (
    id_sub            TEXT PRIMARY KEY,
    subtipo           TEXT,   -- vivienda / solar / finca_rustica ...
    estado            TEXT,   -- de la ficha de resultados
    tipo_subasta      TEXT,
    descripcion       TEXT,
    superficie_m2     REAL,
    direccion         TEXT,
    cod_postal        TEXT,
    localidad         TEXT,
    provincia         TEXT,
    provincia_cod     TEXT,
    barrio            TEXT,
    distrito          TEXT,
    municipio_geo     TEXT,
    valor_subasta     REAL,
    tasacion          REAL,
    postura_minima    REAL,
    deposito          REAL,
    cantidad_reclamada REAL,
    anuncio_boe       TEXT,
    fecha_inicio      TEXT,
    fecha_fin         TEXT,
    lotes             TEXT,
    url               TEXT,
    -- estado de pujas (pestana ver=5, publico)
    num_pujas         INTEGER,
    puja_maxima       REAL,
    -- posesion y visita (pestana ver=3)
    vivienda_habitual TEXT,
    situacion_posesoria TEXT,
    visitable         TEXT,
    cargas            REAL,
    estado_portal     TEXT,   -- concluidas: PC (en portal) / FS (por autoridad gestora)
    -- enriquecimiento geografico
    lat               REAL,
    lon               REAL,
    dist_costa_m      REAL,
    geocode_estado    TEXT,   -- exacta / municipio / provincia / no_encontrado
    fetched_at        TEXT
);
"""


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute(SCHEMA)
    # migracion: añadir columnas nuevas a BD existentes
    existentes = {r[1] for r in con.execute("PRAGMA table_info(subastas)")}
    for col, tipo in [("superficie_m2", "REAL"), ("barrio", "TEXT"),
                      ("distrito", "TEXT"), ("municipio_geo", "TEXT"),
                      ("num_pujas", "INTEGER"), ("puja_maxima", "REAL"),
                      ("vivienda_habitual", "TEXT"), ("situacion_posesoria", "TEXT"),
                      ("visitable", "TEXT"), ("cargas", "REAL"),
                      ("estado_portal", "TEXT")]:
        if col not in existentes:
            con.execute(f"ALTER TABLE subastas ADD COLUMN {col} {tipo}")
    return con


def upsert(con, row):
    cols = list(row.keys())
    ph = ",".join("?" for _ in cols)
    upd = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id_sub")
    con.execute(
        f"INSERT INTO subastas ({','.join(cols)}) VALUES ({ph}) "
        f"ON CONFLICT(id_sub) DO UPDATE SET {upd}",
        [row[c] for c in cols],
    )


def pendientes_geocode(con):
    return con.execute(
        "SELECT * FROM subastas WHERE lat IS NULL"
    ).fetchall()

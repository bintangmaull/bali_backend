# app/repository/repo_directloss.py

import os
import pandas as pd
from sqlalchemy import create_engine, text
from app.config import Config

DEBUG_DIR = os.path.join(os.getcwd(), "debug_output")
os.makedirs(DEBUG_DIR, exist_ok=True)

def get_db_connection():
    """Membuat koneksi ke database PostgreSQL."""
    try:
        return create_engine(Config.SQLALCHEMY_DATABASE_URI)
    except Exception as e:
        raise ConnectionError(f"❌ Gagal terhubung ke database: {e}")

def get_bangunan_data():
    """Mengambil data bangunan lengkap."""
    query = text("""
        SELECT
            b.id_bangunan,
            b.geom,
            b.luas,
            b.nama_gedung,
            b.alamat,
            b.kode_bangunan,
            b.taxonomy,
            b.provinsi,
            b.kota,
            b.jumlah_lantai,
            COALESCE(k.hsbgn_sederhana, 0.0) AS hsbgn_sederhana,
            COALESCE(k.hsbgn_tidaksederhana, 0.0) AS hsbgn_tidaksederhana
        FROM bangunan_copy b
        LEFT JOIN kota k ON b.kota = k.kota;
    """)
    engine = get_db_connection()
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

def get_city_bangunan_data(kota_name):
    """Mengambil data bangunan per kota."""
    query = text("""
        SELECT
            b.id_bangunan,
            b.geom,
            b.luas,
            b.nama_gedung,
            b.alamat,
            b.kode_bangunan,
            b.taxonomy,
            b.provinsi,
            b.kota,
            b.jumlah_lantai,
            COALESCE(k.hsbgn_sederhana, 0.0) AS hsbgn_sederhana,
            COALESCE(k.hsbgn_tidaksederhana, 0.0) AS hsbgn_tidaksederhana
        FROM bangunan_copy b
        LEFT JOIN kota k ON b.kota = k.kota
        WHERE b.kota = :kota;
    """)
    engine = get_db_connection()
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"kota": kota_name})


def _vcols_taxonomy(pre, s):
    """Kolom dmgratio per taksonomi (cr, mcf) untuk gempa & tsunami."""
    return [
        f"h.dmgratio_cr_{pre}{s}   AS nilai_y_cr_{pre}{s}",
        f"h.dmgratio_mcf_{pre}{s}  AS nilai_y_mcf_{pre}{s}",
    ]

def _vcols_lantai(pre, s):
    """Kolom dmgratio per jumlah lantai (1 vs 2) untuk banjir_r & banjir_rc."""
    return [
        f"h.dmgratio_1_{pre}{s} AS nilai_y_1_{pre}{s}",
        f"h.dmgratio_2_{pre}{s} AS nilai_y_2_{pre}{s}",
    ]


# =============================================================================
# Mapping konfigurasi bencana untuk query
# PREFIX: nama prefix kolom di tabel dmg_ratio_*
# SUFFIX: suffix kolom (misal pga100, inundansi, r25, rc25)
# =============================================================================
DISASTER_MAPPING = {
    "gempa": {
        "raw":       "model_intensitas_gempa",
        "dmgr":      "dmg_ratio_gempa",
        "prefix":    "pga",
        "scales":    ["100", "200", "250", "500", "1000"],
        "threshold": 525,
        "vcols":     _vcols_taxonomy,
        "mode":      "taxonomy",   # cr/mcf/mur/w based
    },
    "tsunami": {
        "raw":       "model_intensitas_tsunami",
        "dmgr":      "dmg_ratio_tsunami",
        "prefix":    "",
        "scales":    ["inundansi"],
        "threshold": 110,
        "vcols":     lambda pre, s: _vcols_taxonomy("", "inundansi"),
        "mode":      "taxonomy",
    },
    "banjir_r": {
        "raw":       "model_intensitas_banjir",
        "dmgr":      "dmg_ratio_banjir",
        "prefix":    "r",
        "scales":    ["2", "5", "10", "25", "50", "100", "250"],
        "threshold": 17,
        "vcols":     _vcols_lantai,
        "mode":      "lantai",     # jumlah_lantai based
    },
    "banjir_rc": {
        "raw":       "model_intensitas_banjir",
        "dmgr":      "dmg_ratio_banjir",
        "prefix":    "rc",
        "scales":    ["2", "5", "10", "25", "50", "100", "250"],
        "threshold": 17,
        "vcols":     _vcols_lantai,
        "mode":      "lantai",
    },
}


def _build_disaster_query(mapping, kota_name=None):
    """
    Bangun query SQL untuk tiap bencana menggunakan LATERAL JOIN nearest neighbour.
    Jika kota_name diberikan, filter bangunan per kota.
    """
    engine = get_db_connection()
    all_data = {}

    with engine.connect() as conn:
        for name, cfg in mapping.items():
            raw_table  = cfg["raw"]
            dmgr_table = cfg["dmgr"]
            pre        = cfg["prefix"]
            scales     = cfg["scales"]
            threshold  = cfg["threshold"]
            make_vcols = cfg["vcols"]

            subq_parts = []
            sel_parts  = []
            for s in scales:
                for expr in make_vcols(pre, s):
                    subq_parts.append(expr)
                    alias = expr.split(" AS ")[1].strip()
                    sel_parts.append(f"near.{alias}")

            subq_cols  = ",\n       ".join(subq_parts)
            outer_cols = ",\n  ".join(sel_parts)

            if kota_name:
                from_clause = "(SELECT id_bangunan, geom FROM bangunan_copy WHERE kota = :kota) b"
            else:
                from_clause = "bangunan_copy b"

            sql = f"""
                SELECT
                  b.id_bangunan,
                  {outer_cols}
                FROM {from_clause}
                JOIN LATERAL (
                  SELECT
                    {subq_cols}
                  FROM {raw_table} r
                  JOIN {dmgr_table} h ON r.id_lokasi::varchar = h.id_lokasi::varchar
                  WHERE ST_DWithin(
                    b.geom,
                    r.geom,
                    {threshold} / 111320.0
                  )
                  ORDER BY b.geom <-> r.geom
                  LIMIT 1
                ) AS near ON TRUE;
            """

            params = {"kota": kota_name} if kota_name else {}
            df = pd.read_sql(text(sql), conn, params=params)
            all_data[name] = df

    return all_data


def get_all_disaster_data():
    """Ambil data dmgratio seluruh bangunan untuk 4 bencana."""
    return _build_disaster_query(DISASTER_MAPPING)


def get_city_disaster_data(kota_name):
    """Ambil data dmgratio bangunan di satu kota untuk 4 bencana."""
    return _build_disaster_query(DISASTER_MAPPING, kota_name=kota_name)

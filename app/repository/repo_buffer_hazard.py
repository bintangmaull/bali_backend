import logging
from typing import Dict, Any, List, cast
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

# konfigurasi tiap jenis hazard
TYPE_CFG: Dict[str, Any] = {
    "gempa": {
      "table":      "model_intensitas_gempa",
      "buffer_deg": 0.0047,    # threshold 525m ~ 0.0047 deg
      "fields":     ["pga_100", "pga_200", "pga_250", "pga_500", "pga_1000"]
    },
    "tsunami": {
      "table":      "model_intensitas_tsunami",
      "buffer_deg": 0.00099,   # threshold 110m ~ 0.00099 deg
      "fields":     ["inundansi"]
    },
    "banjir_r": {
      "table":      "model_intensitas_banjir",
      "buffer_deg": 0.000153,  # threshold 17m ~ 0.000153 deg
      "fields":     ["r_25", "r_50", "r_100", "r_250"]
    },
    "banjir_rc": {
      "table":      "model_intensitas_banjir",
      "buffer_deg": 0.000153,
      "fields":     ["rc_25", "rc_50", "rc_100", "rc_250"]
    },
}

def get_buffered_features(dtype: str, field: str, bbox: dict, simplify_tolerance: float):
    """
    Buffer & simplify on-the-fly, hanya untuk baris yang memiliki nilai intensitas
    non-NULL **dan bukan nol** pada field yang diminta.
    """
    cfg = TYPE_CFG.get(dtype)
    if not cfg:
        logger.error(f"Unknown type {dtype}")
        return []

    valid_fields: List[str] = cast(List[str], cfg.get("fields", []))
    if field not in valid_fields:
        logger.error(f"Field '{field}' is not valid for type '{dtype}'")
        return []

    sql = text(f"""
    WITH env AS (
      SELECT ST_MakeEnvelope(
        :minlng, :minlat, :maxlng, :maxlat, 4326
      ) AS geom
    )
    SELECT
      ST_AsGeoJSON(
        ST_SimplifyPreserveTopology(
          ST_Buffer(p.geom::geography, :buf_deg * 111319.9)::geometry,
          :tol
        )
      ) AS geojson,
      p.{field} AS value
    FROM {cfg["table"]} p, env
    WHERE p.geom && env.geom
      AND ST_Intersects(p.geom, env.geom)
      AND p.{field} IS NOT NULL
      AND p.{field} <> 0;
    """)

    params = {
      "minlng": bbox["minlng"],
      "minlat": bbox["minlat"],
      "maxlng": bbox["maxlng"],
      "maxlat": bbox["maxlat"],
      "tol": simplify_tolerance,
      "buf_deg": cfg["buffer_deg"]
    }

    try:
        rows = db.session.execute(sql, params).fetchall()
        return rows
    except Exception as e:
        logger.error(f"Error buffering {dtype}: {e}")
        return []
    finally:
        db.session.close()

def get_nearest_point(dtype: str, field: str, lat: float, lng: float):
    """
    Cari titik terdekat, kembalikan satu nilai intensitas 'field' dan jarak.
    """
    cfg = TYPE_CFG.get(dtype)
    if not cfg:
        logger.error(f"Unknown type {dtype}")
        return None

    valid_fields: List[str] = cast(List[str], cfg.get("fields", []))
    if field not in valid_fields:
        logger.error(f"Field '{field}' is not valid for type '{dtype}'")
        return None

    sql = text(f"""
    SELECT
      {field} AS value,
      ST_Distance(
        geom::geography,
        ST_SetSRID(ST_Point(:lng, :lat),4326)::geography
      ) AS distance_m
    FROM {cfg["table"]}
    WHERE {field} IS NOT NULL
      AND {field} <> 0
    ORDER BY geom <-> ST_SetSRID(ST_Point(:lng, :lat),4326)
    LIMIT 1;
    """)

    try:
        row = db.session.execute(sql, {"lat": lat, "lng": lng}).fetchone()
        if row:
            return {
                field: float(row[0] or 0),
                "distance_m": float(row[1] or 0)
            }
    except Exception as e:
        logger.error(f"Error nearest {dtype}: {e}")
    finally:
        db.session.close()

    return None

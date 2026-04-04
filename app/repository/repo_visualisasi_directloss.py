# app/repository/repo_visualisasi_directloss.py

from sqlalchemy import text
from app.extensions import db
import logging
import sys
import os

# UTF-8 for console/logging
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Setup debug output directory & logger
DEBUG_DIR = os.path.join(os.getcwd(), "debug_output")
os.makedirs(DEBUG_DIR, exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(DEBUG_DIR, "repo_visualisasi_directloss.log"), encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(fh)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(ch)


class GedungRepository:
    @staticmethod
    def fetch_geojson(bbox=None, prov=None, kota=None, limit=None):
        where = ["1=1"]
        params = {}

        if bbox:
            west, south, east, north = map(float, bbox.split(","))
            where.append("b.geom && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
            params.update(west=west, south=south, east=east, north=north)

        if prov:
            where.append("TRIM(LOWER(b.provinsi)) = TRIM(LOWER(:provinsi))")
            params["provinsi"] = prov

        if kota:
            where.append("TRIM(LOWER(b.kota)) = TRIM(LOWER(:kota))")
            params["kota"] = kota
            
        limit_clause = ""
        if limit is not None:
             limit_clause = f"LIMIT {limit}"

        # Ensure provinsi/kota never null in the JSON properties
        sql = f"""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(f), '[]'::json)
        ) AS geojson
        FROM (
          -- Original Bangunan
          SELECT json_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(b.geom)::json,
            'properties',
              (to_jsonb(b)
                 - 'geom'
                 - 'provinsi'
                 - 'kota'
              )
              || jsonb_build_object(
                   'provinsi', COALESCE(b.provinsi, ''),
                   'kota',    COALESCE(b.kota, ''),
                   'id_bangunan', b.id_bangunan,
                   'hsbgn',   CASE WHEN b.jumlah_lantai = 1 THEN k.hsbgn_sederhana ELSE k.hsbgn_tidaksederhana END
                 )
              || to_jsonb(d)
          ) AS f
          FROM bangunan_copy b
          JOIN hasil_proses_directloss d USING(id_bangunan)
          LEFT JOIN kota k ON TRIM(LOWER(k.kota)) = TRIM(LOWER(b.kota))
          WHERE {" AND ".join(where)}
          
          UNION ALL
          
          -- BMN and Residential
          SELECT json_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(b.geom)::json,
            'properties',
              (to_jsonb(b)
                 - 'geom'
                 - 'provinsi'
                 - 'kota'
                 - 'id'
              )
              || jsonb_build_object(
                   'id_bangunan', b.id,
                   'provinsi', COALESCE(b.provinsi, ''),
                   'kota',    COALESCE(b.kota, '')
                 )
              -- fill direct loss columns with 0 since they don't have calculations yet
              || '{{
                "direct_loss_pga_100": 0, "direct_loss_pga_200": 0, "direct_loss_pga_250": 0, "direct_loss_pga_500": 0, "direct_loss_pga_1000": 0,
                "direct_loss_inundansi": 0,
                "direct_loss_r_2": 0, "direct_loss_r_5": 0, "direct_loss_r_10": 0, "direct_loss_r_25": 0, "direct_loss_r_50": 0, "direct_loss_r_100": 0, "direct_loss_r_250": 0,
                "direct_loss_rc_2": 0, "direct_loss_rc_5": 0, "direct_loss_rc_10": 0, "direct_loss_rc_25": 0, "direct_loss_rc_50": 0, "direct_loss_rc_100": 0, "direct_loss_rc_250": 0
              }}'::jsonb
          ) AS f
          FROM exposure_bmn_residential b
          WHERE {" AND ".join(where).replace("b.id_bangunan", "b.id")}
          {limit_clause}
        ) sub;
        """
        logger.debug("fetch_geojson SQL:\n%s", sql)
        return db.session.execute(text(sql), params).scalar()

    @staticmethod
    def fetch_provinsi():
        sql = """
        SELECT DISTINCT COALESCE(b.provinsi, '')
        FROM hasil_proses_directloss d
        JOIN bangunan_copy b USING (id_bangunan)
        WHERE b.provinsi IS NOT NULL
        ORDER BY b.provinsi
        """
        logger.debug("fetch_provinsi SQL:\n%s", sql)
        rows = db.session.execute(text(sql)).fetchall()
        # filter out any empty strings just in case
        return [r[0] for r in rows if r[0]]

    @staticmethod
    def fetch_kota(provinsi):
        sql = """
        SELECT DISTINCT COALESCE(b.kota, '')
        FROM hasil_proses_directloss d
        JOIN bangunan_copy b USING (id_bangunan)
        WHERE TRIM(LOWER(b.provinsi)) = TRIM(LOWER(:provinsi))
          AND b.kota IS NOT NULL
        ORDER BY b.kota
        """
        logger.debug("fetch_kota SQL:\n%s", sql)
        rows = db.session.execute(text(sql), {"provinsi": provinsi}).fetchall()
        return [r[0] for r in rows if r[0]]

    @staticmethod
    def fetch_aal_geojson(kota=None):
        where_clauses = ["1=1"]
        params = {}

        if kota:
            where_clauses.append("TRIM(LOWER(hak.id_kota)) = TRIM(LOWER(:kota))")
            params["kota"] = kota

        sql = f"""
        SELECT json_build_object(
          'type',       'FeatureCollection',
          'features',   COALESCE(json_agg(f), '[]'::json)
        ) AS geojson
        FROM (
          SELECT json_build_object(
            'type',     'Feature',
            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(k.geom, 0.01))::json,
            'properties', to_jsonb(hak)
          ) AS f
          FROM hasil_aal_kota hak
          JOIN kota k
            ON lower(k.kota) = lower(hak.id_kota)
          WHERE {" AND ".join(where_clauses)}
        ) sub;
        """
        logger.debug("fetch_aal_geojson SQL:\n%s", sql)
        return db.session.execute(text(sql), params).scalar()

    @staticmethod
    def fetch_aal_provinsi_list():
        sql = """
        SELECT DISTINCT id_kota
        FROM hasil_aal_kota
        WHERE id_kota IS NOT NULL AND id_kota <> ''
        ORDER BY id_kota
        """
        logger.debug("fetch_aal_provinsi_list SQL:\n%s", sql)
        rows = db.session.execute(text(sql)).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def fetch_aal_data(kota):
        sql = """
        SELECT *
        FROM hasil_aal_kota
        WHERE TRIM(LOWER(id_kota)) = TRIM(LOWER(:kota))
        """
        logger.debug("fetch_aal_data SQL for kota=%s", kota)
        row = db.session.execute(text(sql), {"kota": kota}).mappings().first()
        return dict(row) if row else None

    @staticmethod
    def stream_directloss_csv():
        copy_sql = """
        COPY (
          SELECT
            b.id_bangunan,
            COALESCE(b.provinsi,'') AS provinsi,
            COALESCE(b.kota,'')    AS kota,
            d.direct_loss
          FROM bangunan_copy b
          JOIN hasil_proses_directloss d USING (id_bangunan)
        ) TO STDOUT WITH CSV HEADER
        """
        raw_conn = db.session.connection().connection
        cur = raw_conn.cursor()
        logger.debug("stream_directloss_csv copy_sql prepared")
        return cur, copy_sql, {}

    @staticmethod
    def stream_aal_csv():
        copy_sql = """
        COPY (
          SELECT *
          FROM hasil_aal_kota
          ORDER BY id_kota
        ) TO STDOUT WITH CSV HEADER
        """
        raw_conn = db.session.connection().connection
        cur = raw_conn.cursor()
        logger.debug("stream_aal_csv copy_sql prepared")
        return cur, copy_sql, {}

    @staticmethod
    def fetch_aal_kota_geojson():
        sql = """
        SELECT json_build_object(
          'type',     'FeatureCollection',
          'features', COALESCE(json_agg(f), '[]'::json)
        ) AS geojson
        FROM (
          SELECT json_build_object(
            'type',     'Feature',
            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(k.geom, 0.01))::json,
            'properties', to_jsonb(hak)
          ) AS f
          FROM hasil_aal_kota hak
          JOIN kota k
            ON lower(k.kota) = lower(hak.id_kota)
        ) sub;
        """
        logger.debug("fetch_aal_kota_geojson SQL:\n%s", sql)
        return db.session.execute(text(sql)).scalar()

    @staticmethod
    def stream_aal_kota_csv():
        copy_sql = """
        COPY (
          SELECT *
          FROM hasil_aal_kota
          ORDER BY id_kota
        ) TO STDOUT WITH CSV HEADER
        """
        raw_conn = db.session.connection().connection
        cur = raw_conn.cursor()
        logger.debug("stream_aal_kota_csv copy_sql prepared")
        return cur, copy_sql, {}

    @staticmethod
    def fetch_rekap_aset_kota_geojson():
        sql = """
        SELECT 
            p.id_provinsi as id_prov, 
            r.id_kota as nama_kota,
            ST_AsGeoJSON(ST_SimplifyPreserveTopology(k.geom, 0.005))::json as geom_geojson,
            to_jsonb(r) as r_props
        FROM rekap_aset_kota r
        LEFT JOIN kota k ON TRIM(LOWER(r.id_kota)) = TRIM(LOWER(k.kota))
        LEFT JOIN provinsi p ON TRIM(LOWER(k.provinsi)) = TRIM(LOWER(p.provinsi))
        """
        rekapData = db.session.execute(text(sql)).fetchall()

        prov_ratios = {}
        city_count = 0
        
        features = []
        for row in rekapData:
            r_props = row[3] or {}
            dl_exp = r_props.get('dl_exposure', {})
            if isinstance(dl_exp, str):
                try:
                    dl_exp = json.loads(dl_exp)
                except:
                    dl_exp = {}
            
            # Update r_props with the correctly parsed dl_exposure and extra fields
            r_props['dl_exposure'] = dl_exp
            r_props['id_prov'] = row[0]
            r_props['nama_kota'] = row[1]
            r_props['is_gempa_ratio'] = True

            features.append({
                'type': 'Feature',
                'geometry': row[2],
                'properties': r_props
            })
            
            city_count += 1
            for cat, rps in dl_exp.items():
                if not isinstance(rps, dict): continue
                if cat not in prov_ratios:
                    prov_ratios[cat] = {}
                for rp, val in rps.items():
                    if rp.startswith('pga_'):
                        prov_ratios[cat][rp] = prov_ratios[cat].get(rp, 0) + (float(val) if val is not None else 0)

        if city_count > 0:
            for cat in prov_ratios:
                for rp in prov_ratios[cat]:
                    prov_ratios[cat][rp] = prov_ratios[cat][rp] / city_count

        return {
            'type': 'FeatureCollection',
            'features': features,
            'provincial_gempa_loss_ratios': prov_ratios
        }

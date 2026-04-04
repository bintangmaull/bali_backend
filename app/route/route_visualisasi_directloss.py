import io
import math
from flask import Blueprint, request, Response, jsonify
from app.service.service_visualisasi_directloss import GedungService

gedung_bp = Blueprint('gedung', __name__, url_prefix='/api')

# — GeoJSON endpoints (lama) —
@gedung_bp.route('/gedung', methods=['GET'])
def get_gedung():
    bbox = request.args.get('bbox')
    prov = request.args.get('provinsi')
    kota = request.args.get('kota')
    geojson = GedungService.get_geojson(bbox, prov, kota)
    return jsonify(geojson)

@gedung_bp.route('/provinsi', methods=['GET'])
def list_provinsi():
    return jsonify(GedungService.get_provinsi_list())

@gedung_bp.route('/kota', methods=['GET'])
def list_kota():
    prov = request.args.get('provinsi')
    if not prov:
        return jsonify([]), 400
    return jsonify(GedungService.get_kota_list(prov))

@gedung_bp.route('/aal-provinsi', methods=['GET'])
def get_aal_geojson():
    prov = request.args.get('provinsi')
    geojson = GedungService.get_aal_geojson(prov)
    return jsonify(geojson)

@gedung_bp.route('/aal-provinsi-list', methods=['GET'])
def list_aal_provinsi():
    return jsonify(GedungService.get_aal_provinsi_list())

@gedung_bp.route('/aal-provinsi-data', methods=['GET'])
def aal_data():
    prov = request.args.get('provinsi')
    if not prov:
        return jsonify({"error": "provinsi required"}), 400
    data = GedungService.get_aal_data(prov)
    if not data:
        return jsonify({}), 404
    # sanitize NaN / Inf
    for k, v in data.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            data[k] = 0.0
    return jsonify(data)

# — CSV download endpoints (tanpa filter) —
@gedung_bp.route('/gedung/download', methods=['GET'])
def download_directloss():
    """
    Stream CSV seluruh tabel hasil_proses_directloss + bangunan tanpa filter.
    Termasuk kolom nama_gedung dan alamat dari tabel bangunan.
    """
    # Ambil cursor psycopg2
    from app.extensions import db
    raw_conn = db.session.connection().connection
    cur = raw_conn.cursor()

    # Sertakan nama_gedung dan alamat
    copy_sql = """
    COPY (
      SELECT
        b.id_bangunan,
        b.nama_gedung,
        b.alamat,
        b.kota,
        b.provinsi,
        b.luas,
        b.taxonomy,
        b.jumlah_lantai,
        d.*
      FROM bangunan_copy b
      JOIN hasil_proses_directloss d USING (id_bangunan)
    ) TO STDOUT WITH CSV HEADER
    """

    def generate():
        buf = io.StringIO()
        cur.copy_expert(copy_sql, buf)
        buf.seek(0)
        while True:
            chunk = buf.read(8192)
            if not chunk:
                break
            yield chunk

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=directloss.csv'}
    )

@gedung_bp.route('/aal-provinsi/download', methods=['GET'])
def download_aal():
    """
    Stream CSV seluruh tabel hasil_aal_kota tanpa filter.
    """
    from app.extensions import db
    raw_conn = db.session.connection().connection
    cur = raw_conn.cursor()

    copy_sql = """
    COPY (
      SELECT h.*
      FROM hasil_aal_kota h
      ORDER BY h.id_kota
    ) TO STDOUT WITH CSV HEADER
    """

    def generate():
        buf = io.StringIO()
        cur.copy_expert(copy_sql, buf)
        buf.seek(0)
        while True:
            chunk = buf.read(8192)
            if not chunk:
                break
            yield chunk

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=aal_provinsi.csv'}
    )


@gedung_bp.route('/aal-kota', methods=['GET'])
def get_aal_kota_geojson():
    geojson = GedungService.get_aal_kota_geojson()
    return jsonify(geojson)

@gedung_bp.route('/rekap-aset-kota', methods=['GET'])
def get_rekap_aset_kota_geojson():
    geojson = GedungService.get_rekap_aset_kota_geojson()
    return jsonify(geojson)

@gedung_bp.route('/kota-boundary', methods=['GET'])
def get_kota_boundary():
    """Return GeoJSON boundary untuk satu kota dari tabel kota."""
    from app.extensions import db
    from sqlalchemy import text
    kota = request.args.get('kota', '').strip()
    if not kota:
        return jsonify({"error": "parameter kota diperlukan"}), 400
    sql = text("""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', json_build_array(
            json_build_object(
              'type', 'Feature',
              'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(geom, 0.005))::json,
              'properties', json_build_object('kota', kota, 'provinsi', provinsi)
            )
          )
        )
        FROM kota
        WHERE lower(kota) = lower(:kota)
        LIMIT 1
    """)
    result = db.session.execute(sql, {"kota": kota}).scalar()
    return jsonify(result)

@gedung_bp.route('/aal-kota/download', methods=['GET'])
def download_aal_kota():
    """
    Stream CSV seluruh tabel hasil_aal_kota diurutkan per kota.
    """
    from app.extensions import db
    raw_conn = db.session.connection().connection
    cur = raw_conn.cursor()

    copy_sql = """
    COPY (
      SELECT h.*
      FROM hasil_aal_kota h
      ORDER BY h.id_kota
    ) TO STDOUT WITH CSV HEADER
    """

    def generate():
        buf = io.StringIO()
        cur.copy_expert(copy_sql, buf)
        buf.seek(0)
        while True:
            chunk = buf.read(8192)
            if not chunk:
                break
            yield chunk

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=aal_kota.csv'}
    )



@gedung_bp.route('/drought-sawah-loss', methods=['GET'])
def get_drought_sawah_loss():
    """
    Return drought rice field loss values for all cities and return periods.
    Response shape:
    {
      "return_periods": [25, 50, 100, 250],
      "cities": ["BADUNG", ...],
      "gpm": { "25": [{"kota": "BADUNG", "loss_2022": ..., "loss_2025": ..., "loss_2028": ...}, ...], ... },
      "mme": { ... }
    }
    """
    from app.extensions import db
    from sqlalchemy import text

    rows = db.session.execute(text("""
        SELECT kota, return_period, climate_change,
               loss_2022_idr, loss_2025_idr, loss_2028_idr
        FROM loss_drought_sawah
        ORDER BY climate_change, return_period, kota
    """)).fetchall()

    result = { 'gpm': {}, 'mme': {} }
    cities_set = set()
    rps_set = set()

    for row in rows:
        kota, rp, cc, l22, l25, l28 = row
        cc = cc.lower()
        rp_key = str(rp)
        cities_set.add(kota)
        rps_set.add(rp)
        if cc not in result:
            continue
        if rp_key not in result[cc]:
            result[cc][rp_key] = []
        result[cc][rp_key].append({
            'kota': kota,
            'loss_2022': l22 or 0,
            'loss_2025': l25 or 0,
            'loss_2028': l28 or 0,
        })

    result['return_periods'] = sorted(list(rps_set))
    result['cities'] = sorted(list(cities_set))
    return jsonify(result)


@gedung_bp.route('/flood-sawah-loss', methods=['GET'])
def get_flood_sawah_loss():
    """
    Return flood rice field loss values for all cities and return periods.
    Response shape:
    {
      "return_periods": [2, 5, 10, 25, 50, 100, 250],
      "cities": ["BADUNG", ...],
      "r":  { "2": [{"kota": "BADUNG", "loss_2022": ..., "loss_2025": ..., "loss_2028": ...}, ...], ... },
      "rc": { ... }
    }
    r  = non-climate-change scenario
    rc = climate-change scenario
    """
    from app.extensions import db
    from sqlalchemy import text

    rows = db.session.execute(text("""
        SELECT kota, return_period, climate_change,
               loss_2022_idr, loss_2025_idr, loss_2028_idr
        FROM loss_flood_sawah
        ORDER BY climate_change, return_period, kota
    """)).fetchall()

    result = { 'r': {}, 'rc': {} }
    cities_set = set()
    rps_set = set()

    for row in rows:
        kota, rp, cc, l22, l25, l28 = row
        cc = cc.lower()
        rp_key = str(rp)
        cities_set.add(kota)
        rps_set.add(rp)
        if cc not in result:
            continue
        if rp_key not in result[cc]:
            result[cc][rp_key] = []
        result[cc][rp_key].append({
            'kota': kota,
            'loss_2022': l22 or 0,
            'loss_2025': l25 or 0,
            'loss_2028': l28 or 0,
        })

    result['return_periods'] = sorted(list(rps_set))
    result['cities'] = sorted(list(cities_set))
    return jsonify(result)


@gedung_bp.route('/pml-gempa', methods=['GET'])
def get_pml_gempa():
    """
    Return PML values for earthquake per city and return period.
    """
    from app.models.models_database import HasilPMLGempaKota
    kota = request.args.get('kota')
    
    query = HasilPMLGempaKota.query
    if kota:
        query = query.filter(HasilPMLGempaKota.id_kota.ilike(kota))
    
    rows = query.order_by(HasilPMLGempaKota.return_period).all()
    
    return jsonify([r.to_dict() for r in rows])


def setup_visualisasi_routes(app):
    app.register_blueprint(gedung_bp)

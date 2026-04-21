import io
import math
from flask import Blueprint, request, Response, jsonify
from app.service.service_visualisasi_directloss import GedungService

gedung_bp = Blueprint('gedung', __name__)

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

@gedung_bp.route('/flood-building-aal', methods=['GET'])
def get_flood_building_aal():
    scheme = request.args.get('scheme', '1')
    kota = request.args.get('kota')
    cv = request.args.get('cv')
    
    if scheme == '2':
        data = GedungService.get_aal_flood_building_skema2(kota=kota)
        return jsonify({
            "data": data,
            "return_periods": [2, 5, 10, 25, 50, 100, 250]
        })
    
    data = GedungService.get_aal_flood_building(kota=kota, cv=cv)
    return jsonify({
        "data": data,
        "return_periods": [25, 50, 100, 250]
    })

# — CSV download endpoints (tanpa filter) —
@gedung_bp.route('/gedung/download', methods=['GET'])
def download_directloss():
    """
    Stream CSV seluruh tabel hasil_proses_directloss + bangunan tanpa filter.
    Termasuk kolom nama_gedung dan alamat dari tabel bangunan.
    """
    from app.extensions import db
    raw_conn = db.session.connection().connection
    cur = raw_conn.cursor()

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
    cv = request.args.get('cv', '0.15')
    scheme = request.args.get('scheme', '1')
    geojson = GedungService.get_aal_kota_geojson(cv=cv, scheme=scheme)
    return jsonify(geojson)

@gedung_bp.route('/rekap-aset-kota', methods=['GET'])
def get_rekap_aset_kota_geojson():
    geojson = GedungService.get_rekap_aset_kota_geojson()
    return jsonify(geojson)

@gedung_bp.route('/aal-drought', methods=['GET'])
def get_aal_drought_geojson():
    year = request.args.get('year')
    cc = request.args.get('cc')
    geojson = GedungService.get_aal_drought_geojson(year, cc)
    return jsonify(geojson)

@gedung_bp.route('/aal-flood-sawah', methods=['GET'])
def get_aal_flood_sawah_geojson():
    year = request.args.get('year')
    cc = request.args.get('cc')
    geojson = GedungService.get_aal_flood_sawah_geojson(year, cc)
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
    """
    from app.extensions import db
    from sqlalchemy import text

    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gedung_bp.route('/aal-drought-table', methods=['GET'])
def get_aal_drought_table():
    """
    Return detailed drought AAL metrics (AAL, VaR, TVaR, PML) for Sawah.
    If kota is not provided, returns aggregated results (All Bali).
    """
    from app.models.models_database import AALDroughtSawah
    from app.extensions import db
    from sqlalchemy import func
    
    kota = request.args.get('kota')
    year = request.args.get('year')
    cc = request.args.get('cc')
    aggregate = request.args.get('aggregate', 'true').lower() == 'true'
    
    if kota:
        query = AALDroughtSawah.query.filter(AALDroughtSawah.id_kota.ilike(kota))
        if year and year.isdigit():
            query = query.filter(AALDroughtSawah.year == int(year))
        if cc:
            query = query.filter(AALDroughtSawah.climate_change == cc)
        try:
            rows = query.order_by(AALDroughtSawah.year, AALDroughtSawah.climate_change).all()
            return jsonify([r.to_dict() for r in rows])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif not aggregate:
        query = AALDroughtSawah.query
        if year and year.isdigit():
            query = query.filter(AALDroughtSawah.year == int(year))
        if cc:
            query = query.filter(AALDroughtSawah.climate_change == cc)
        rows = query.order_by(AALDroughtSawah.id_kota, AALDroughtSawah.year).all()
        return jsonify([r.to_dict() for r in rows])
    else:
        query = db.session.query(
            AALDroughtSawah.year,
            AALDroughtSawah.climate_change,
            func.sum(AALDroughtSawah.aal).label('aal'),
            func.sum(AALDroughtSawah.var_95).label('var_95'),
            func.sum(AALDroughtSawah.tvar_95).label('tvar_95'),
            func.sum(AALDroughtSawah.var_99).label('var_99'),
            func.sum(AALDroughtSawah.tvar_99).label('tvar_99'),
            func.sum(AALDroughtSawah.pml_25).label('pml_25'),
            func.sum(AALDroughtSawah.pml_50).label('pml_50'),
            func.sum(AALDroughtSawah.pml_100).label('pml_100'),
            func.sum(AALDroughtSawah.pml_250).label('pml_250')
        ).group_by(AALDroughtSawah.year, AALDroughtSawah.climate_change)
        
        if year and year.isdigit():
            query = query.filter(AALDroughtSawah.year == int(year))
        if cc:
            query = query.filter(AALDroughtSawah.climate_change == cc)
            
        try:
            rows = query.order_by(AALDroughtSawah.year, AALDroughtSawah.climate_change).all()
            result = [dict(r._mapping) for r in rows]
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@gedung_bp.route('/aal-drought-all-cities', methods=['GET'])
def get_aal_drought_all_cities():
    """Returns unaggregated drought metrics for all cities."""
    from app.models.models_database import AALDroughtSawah
    year = request.args.get('year')
    cc = request.args.get('cc')
    query = AALDroughtSawah.query
    if year and year.isdigit():
        query = query.filter(AALDroughtSawah.year == int(year))
    if cc:
        query = query.filter(AALDroughtSawah.climate_change == cc)
    rows = query.order_by(AALDroughtSawah.id_kota, AALDroughtSawah.year).all()
    return jsonify([r.to_dict() for r in rows])

@gedung_bp.route('/flood-sawah-loss', methods=['GET'])
def get_flood_sawah_loss():
    """
    Return flood rice field loss values for all cities and return periods.
    Supports scheme parameter: 1 (default) or 2.
    """
    from flask import request
    from app.extensions import db
    from sqlalchemy import text
    from app.models.models_database import AALFloodSawahSkema2

    scheme = request.args.get('scheme', '1')

    if scheme == '2':
        # For Skema 2, we use the AALFloodSawahSkema2 table which has all RPs
        rows = AALFloodSawahSkema2.query.all()
        result = { 'r': {}, 'rc': {} }
        cities_set = set()
        rps_set = set([2, 5, 10, 25, 50, 100, 250])

        for row in rows:
            cc = 'rc' if row.climate_change.lower() == 'cc' else 'r'
            cities_set.add(row.kota)
            
            for rp in rps_set:
                rp_key = str(rp)
                if rp_key not in result[cc]:
                    result[cc][rp_key] = []
                
                # Check if this city already has an entry for this RP and CC
                existing = next((item for item in result[cc][rp_key] if item['kota'] == row.kota), None)
                
                loss_val = getattr(row, f'pml_{rp}', 0)
                
                if existing:
                    # Update the year-specific loss
                    existing[f'loss_{row.year}'] = loss_val
                else:
                    item = {
                        'kota': row.kota,
                        f'loss_{row.year}': loss_val
                    }
                    result[cc][rp_key].append(item)
                    
        result['return_periods'] = sorted(list(rps_set))
        result['cities'] = sorted(list(cities_set))
        return jsonify(result)

    else:
        # Default Skema 1 logic (original)
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
    from app.models.models_database import HasilPMLGempaKota
    kota = request.args.get('kota')
    query = HasilPMLGempaKota.query
    if kota:
        query = query.filter(HasilPMLGempaKota.id_kota.ilike(kota))
    rows = query.order_by(HasilPMLGempaKota.return_period).all()
    return jsonify([r.to_dict() for r in rows])

@gedung_bp.route('/flood-sawah-aal', methods=['GET'])
def get_flood_sawah_aal():
    from flask import request
    from app.models.models_database import AALFloodSawah, AALFloodSawahSkema2
    
    scheme = request.args.get('scheme', '1')
    
    if scheme == '2':
        rows = AALFloodSawahSkema2.query.order_by(
            AALFloodSawahSkema2.climate_change,
            AALFloodSawahSkema2.year,
            AALFloodSawahSkema2.kota
        ).all()
        return_periods = [2, 5, 10, 25, 50, 100, 250]
    else:
        rows = AALFloodSawah.query.order_by(
            AALFloodSawah.climate_change,
            AALFloodSawah.year,
            AALFloodSawah.kota
        ).all()
        return_periods = [10, 25, 50, 100, 250]

    result = []
    for row in rows:
        data_item = {
            'kota': row.kota,
            'year': row.year,
            'climate_change': row.climate_change.lower(),
            'aal': row.aal or 0,
            'pml_10': row.pml_10 or 0,
            'tvar_10': row.tvar_10 or 0,
            'pml_25': row.pml_25 or 0,
            'tvar_25': row.tvar_25 or 0,
            'pml_50': row.pml_50 or 0,
            'tvar_50': row.tvar_50 or 0,
            'pml_100': row.pml_100 or 0,
            'tvar_100': row.tvar_100 or 0,
            'pml_250': row.pml_250 or 0,
            'tvar_250': row.tvar_250 or 0
        }
        
        # Add extra RPs for Skema 2
        if scheme == '2':
            data_item.update({
                'pml_2': getattr(row, 'pml_2', 0),
                'tvar_2': getattr(row, 'tvar_2', 0),
                'pml_5': getattr(row, 'pml_5', 0),
                'tvar_5': getattr(row, 'tvar_5', 0),
            })
            
        result.append(data_item)

    return jsonify({
        'data': result,
        'return_periods': return_periods
    })

def setup_visualisasi_routes(app):
    app.register_blueprint(gedung_bp, url_prefix='/api')

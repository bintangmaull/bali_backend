from flask import Blueprint, request, jsonify
from app.service.service_visualisasi_directloss import GedungService

gedung_bp = Blueprint('gedung', __name__, url_prefix='/api')

@gedung_bp.route('/gedung', methods=['GET'])
def get_gedung():
    """
    GET /api/gedung
      query params:
        - bbox=minx,miny,maxx,maxy   (opsional)
        - provinsi=[nama provinsi]    (opsional)
        - kota=[nama kota]            (opsional)
        - limit=[angka]               (opsional)
    """
    bbox = request.args.get('bbox')
    prov = request.args.get('provinsi')
    kota = request.args.get('kota')
    limit = request.args.get('limit')
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            limit = None

    geojson = GedungService.get_geojson(bbox, prov, kota, limit)
    return jsonify(geojson)

from flask import Blueprint, jsonify
from app.service.service_visualisasi_hazard import RasterService
from app.geoserver_register import upload_all_geotiffs
bencana_bp = Blueprint('bencana_bp', __name__)

@bencana_bp.route('/generate-raster/<bencana>/<kolom>', methods=['GET'])
def generate_raster(bencana, kolom):
    allowed_bencana = ['gempa', 'tsunami', 'banjir_r', 'banjir_rc']
    if bencana not in allowed_bencana:
        return jsonify({'status': 'error', 'message': 'Jenis bencana tidak valid'}), 400

    raster_path, error = RasterService.generate_raster_from_points(bencana, kolom)
    if error:
        return jsonify({'status': 'error', 'message': error}), 404

    return jsonify({'status': 'success', 'raster_file': raster_path})


@bencana_bp.route('/generate-all-raster', methods=['GET'])
def generate_all_raster():
    bencana_map = {
        'gempa':    ['pga_100', 'pga_200', 'pga_250', 'pga_500', 'pga_1000'],
        'tsunami':  ['inundansi'],
        'banjir_r': ['r_25', 'r_50', 'r_100', 'r_250'],
        'banjir_rc':['rc_25', 'rc_50', 'rc_100', 'rc_250'],
    }

    hasil = []

    for bencana, koloms in bencana_map.items():
        for kolom in koloms:
            try:
                path, error = RasterService.generate_raster_from_points(bencana, kolom)
                if error:
                    hasil.append({
                        'bencana': bencana,
                        'kolom': kolom,
                        'status': 'error',
                        'message': error
                    })
                else:
                    success_item = {
                        'bencana': str(bencana),
                        'kolom': str(kolom),
                        'status': 'success',
                        'raster_file': str(path)
                    }
                    hasil.append(success_item)
            except Exception as e:
                error_item = {
                    'bencana': str(bencana),
                    'kolom': str(kolom),
                    'status': 'error',
                    'message': str(e)
                }
                hasil.append(error_item)

    return jsonify(hasil)


@bencana_bp.route('/geoserver/upload-all', methods=['GET'])
def upload_all_to_geoserver():
    """
    Generate semua raster sebagai GeoTIFF dan upload ke GeoServer
    via REST PUT external.geotiff
    """
    results = upload_all_geotiffs()
    return jsonify(results)
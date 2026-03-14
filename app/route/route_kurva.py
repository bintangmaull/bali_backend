from ..controller.controller_kurva import (
    process_kurva_gempa,
    process_kurva_tsunami,
    process_kurva_banjir_r,
    process_kurva_banjir_rc,
    process_kurva_banjir_all,
)

def setup_kurva_routes(app):
    """
    Menetapkan route API untuk pemrosesan kurva dari berbagai bencana.
    """
    app.add_url_rule('/process_kurva_gempa',    'process_kurva_gempa',    process_kurva_gempa,    methods=['POST', 'GET'])
    app.add_url_rule('/process_kurva_tsunami',   'process_kurva_tsunami',   process_kurva_tsunami,   methods=['POST', 'GET'])
    app.add_url_rule('/process_kurva_banjir_r',  'process_kurva_banjir_r',  process_kurva_banjir_r,  methods=['POST', 'GET'])
    app.add_url_rule('/process_kurva_banjir_rc', 'process_kurva_banjir_rc', process_kurva_banjir_rc, methods=['POST', 'GET'])
    app.add_url_rule('/process_kurva_banjir',    'process_kurva_banjir',    process_kurva_banjir_all, methods=['POST', 'GET'])

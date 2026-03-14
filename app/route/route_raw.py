from flask import Blueprint
from app.controller.controller_kurva import (
    process_kurva_gempa,
    process_kurva_tsunami,
    process_kurva_banjir_r,
    process_kurva_banjir_rc,
    process_kurva_banjir_all,
)

# Buat Blueprint
main_bp = Blueprint('main', __name__)

# Route Utama
@main_bp.route('/')
def index():
    return {"message": "Welcome to the main route!"}

# Route untuk setiap jenis bencana
@main_bp.route('/process_kurva_gempa', methods=['GET'])
def process_gempa():
    return process_kurva_gempa()

@main_bp.route('/process_kurva_tsunami', methods=['GET'])
def process_tsunami():
    return process_kurva_tsunami()

@main_bp.route('/process_kurva_banjir_r', methods=['GET'])
def process_banjir_r():
    return process_kurva_banjir_r()

@main_bp.route('/process_kurva_banjir_rc', methods=['GET'])
def process_banjir_rc():
    return process_kurva_banjir_rc()

@main_bp.route('/process_kurva_banjir', methods=['GET'])
def process_banjir_all():
    return process_kurva_banjir_all()

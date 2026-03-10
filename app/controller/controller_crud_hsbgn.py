import logging
from flask import request, jsonify
from app.service.service_crud_hsbgn import HSBGNService
from app.service.service_directloss import recalc_city_directloss_and_aal

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO)
loggerhsgbn = logging.getLogger(__name__)

class HSBGNController:
    @staticmethod
    def recalc(hsbgn_id):
        """
        Memicu perhitungan ulang Direct Loss dan AAL untuk kota terkait HSBGN ini.
        """
        try:
            hsbgn = HSBGNService.get_hsbgn_by_id(hsbgn_id)
            if not hsbgn:
                return jsonify({"error": "HSBGN not found"}), 404
            
            # HSBGN data has 'kota' field
            kota_name = hsbgn.get('kota')
            if not kota_name:
                return jsonify({"error": "City name not found for this HSBGN"}), 400
            
            result = recalc_city_directloss_and_aal(kota_name)
            return jsonify(result), 200
        except Exception as e:
            import traceback
            error_msg = f"Targeted recalc failed for city {kota_name if 'kota_name' in locals() else 'unknown'}: {str(e)}"
            loggerhsgbn.error(f"{error_msg}\n{traceback.format_exc()}")
            return jsonify({"error": error_msg, "traceback": traceback.format_exc()}), 500

    @staticmethod
    def get_all():
        """Mengambil semua data HSBGN"""
        try:
            data = HSBGNService.get_all_hsbgn()
            return jsonify(data), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil semua data HSBGN: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_by_id(hsbgn_id):
        """Mengambil satu HSBGN berdasarkan ID"""
        try:
            data = HSBGNService.get_hsbgn_by_id(hsbgn_id)
            if data:
                return jsonify(data), 200
            return jsonify({"error": "HSBGN tidak ditemukan"}), 404
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil data HSBGN ID {hsbgn_id}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_by_kota(kota):
        """Mengambil HSBGN berdasarkan Kota"""
        try:
            data = HSBGNService.get_hsbgn_by_kota(kota)
            return jsonify(data), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil data HSBGN kota {kota}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def create():
        """Menambahkan HSBGN baru"""
        try:
            data = request.json
            required_fields = ["kota", "provinsi", "hsbgn"]

            # Validasi apakah semua field wajib ada
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Kolom wajib tidak lengkap: {', '.join(missing_fields)}"}), 400
            
            new_hsbgn = HSBGNService.create_hsbgn(data)
            return jsonify(new_hsbgn), 201
        except Exception as e:
            loggerhsgbn.error(f"Error saat menambahkan HSBGN: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def update(hsbgn_id):
        """Mengedit data HSBGN"""
        try:
            data = request.json
            updated_hsbgn = HSBGNService.update_hsbgn(hsbgn_id, data)
            if updated_hsbgn:
                return jsonify(updated_hsbgn), 200
            return jsonify({"error": "HSBGN tidak ditemukan"}), 404
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengedit HSBGN ID {hsbgn_id}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def delete(hsbgn_id):
        """Menghapus data HSBGN"""
        try:
            if HSBGNService.delete_hsbgn(hsbgn_id):
                return jsonify({"message": "HSBGN berhasil dihapus"}), 204
            return jsonify({"error": "HSBGN tidak ditemukan"}), 404
        except Exception as e:
            loggerhsgbn.error(f"Error saat menghapus HSBGN ID {hsbgn_id}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    # Endpoint dropdown Provinsi & Kota
    @staticmethod
    def get_provinsi():
        """Mengambil daftar provinsi unik dari semua data HSBGN"""
        try:
            all_data = HSBGNService.get_all_hsbgn()
            provs = sorted({item['provinsi'] for item in all_data})
            return jsonify(provs), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil daftar provinsi: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_kota_by_provinsi(provinsi):
        """Mengambil daftar kota unik berdasarkan provinsi"""
        try:
            all_data = HSBGNService.get_all_hsbgn()
            kotas = sorted({item['kota'] for item in all_data if item['provinsi'] == provinsi})
            return jsonify(kotas), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil kota untuk provinsi {provinsi}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_all_kota():
        """Mengambil nama kota unik langsung dari tabel bangunan_copy (tanpa geometri)"""
        try:
            from app.extensions import db
            from sqlalchemy import text
            rows = db.session.execute(
                text("SELECT DISTINCT kota FROM bangunan_copy WHERE kota IS NOT NULL ORDER BY kota")
            ).fetchall()
            kotas = [r[0] for r in rows if r[0]]
            return jsonify(kotas), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil semua kota: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

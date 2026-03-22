import logging
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models_database import ActivityLog
from app.service.service_crud_hsbgn import HSBGNService
from app.service.service_directloss import recalc_city_directloss_and_aal

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO)
loggerhsgbn = logging.getLogger(__name__)


import traceback
import json

def _log_hsbgn(action, target_id, detail):
    """Helper: simpan activity log untuk aksi HSBGN."""
    try:
        user = get_jwt_identity()
        if isinstance(user, str):
            try:
                user = json.loads(user)
            except:
                user = {}
        entry = ActivityLog(
            user_nama=user.get('nama', 'Unknown') if isinstance(user, dict) else 'Unknown',
            user_email=user.get('email', 'Unknown') if isinstance(user, dict) else 'Unknown',
            action=action,
            target='hsbgn',
            target_id=str(target_id) if target_id else None,
            detail=detail,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        loggerhsgbn.error(f"Gagal mencatat activity log HSBGN: {e}")


class HSBGNController:
    @staticmethod
    @jwt_required()
    def recalc(hsbgn_id):
        """
        Memicu perhitungan ulang Direct Loss dan AAL untuk kota terkait HSBGN ini.
        """
        try:
            hsbgn = HSBGNService.get_hsbgn_by_id(hsbgn_id)
            if not hsbgn:
                return jsonify({"error": f"HSBGN dengan ID {hsbgn_id} tidak ditemukan"}), 404
            
            kota_name = hsbgn.get('kota')
            if not kota_name:
                return jsonify({"error": "Data HSBGN tidak memiliki field 'kota'"}), 400
            
            loggerhsgbn.info(f"Memicu perhitungan ulang (recalc) untuk kota: {kota_name}")
            recalc_city_directloss_and_aal(kota_name)
            
            _log_hsbgn(
                action='recalc',
                target_id=hsbgn_id,
                detail=f"Melakukan perhitungan ulang (recalc) AAL untuk kota {kota_name}."
            )

            return jsonify({
                "message": f"Perhitungan ulang untuk kota {kota_name} berhasil diselesaikan."
            }), 200
        except Exception as e:
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
    @jwt_required()
    def create():
        """Menambahkan HSBGN baru"""
        try:
            data = request.json
            required_fields = ["kota", "provinsi", "hsbgn_sederhana", "hsbgn_tidaksederhana"]

            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Kolom wajib tidak lengkap: {', '.join(missing_fields)}"}), 400
            
            new_hsbgn = HSBGNService.create_hsbgn(data)
            kota = data.get('kota', '-')
            _log_hsbgn(
                action='tambah',
                target_id=new_hsbgn.get('id_kota'),
                detail=f"Menambahkan data HSBGN untuk kota {kota} (Sederhana: {data.get('hsbgn_sederhana')}, Tidak Sederhana: {data.get('hsbgn_tidaksederhana')})."
            )
            return jsonify(new_hsbgn), 201
        except Exception as e:
            loggerhsgbn.error(f"Error saat menambahkan HSBGN: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    @jwt_required()
    def update(hsbgn_id):
        """Mengedit data HSBGN"""
        try:
            data = request.json
            old_data = HSBGNService.get_hsbgn_by_id(hsbgn_id)
            updated_hsbgn = HSBGNService.update_hsbgn(hsbgn_id, data)
            if updated_hsbgn:
                changes = []
                if old_data:
                    for key, new_val in data.items():
                        old_val = old_data.get(key)
                        if old_val is not None and str(old_val) != str(new_val):
                            changes.append(f"{key} dari '{old_val}' menjadi '{new_val}'")
                kota = old_data.get('kota', '-') if old_data else '-'
                detail = f"Mengedit HSBGN kota {kota}"
                if changes:
                    detail += ": " + "; ".join(changes)
                _log_hsbgn(action='edit', target_id=hsbgn_id, detail=detail + ".")
                return jsonify(updated_hsbgn), 200
            return jsonify({"error": "HSBGN tidak ditemukan"}), 404
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengedit HSBGN ID {hsbgn_id}: {e}")
            return jsonify({
                "error": f"Terjadi kesalahan server: {str(e)}", 
                "traceback": traceback.format_exc()
            }), 500

    @staticmethod
    @jwt_required()
    def delete(hsbgn_id):
        """Menghapus data HSBGN"""
        try:
            old_data = HSBGNService.get_hsbgn_by_id(hsbgn_id)
            if HSBGNService.delete_hsbgn(hsbgn_id):
                kota = old_data.get('kota', '-') if old_data else '-'
                _log_hsbgn(
                    action='hapus',
                    target_id=hsbgn_id,
                    detail=f"Menghapus data HSBGN kota {kota} (id: {hsbgn_id})."
                )
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
            from app.repository.repo_crud_hsbgn import HSBGNRepository
            kotas = HSBGNRepository.get_kota_by_provinsi(provinsi)
            return jsonify(kotas), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil kota untuk provinsi {provinsi}: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_all_kota():
        """Mengambil nama kota unik dari master tabel hsbgn"""
        try:
            from app.repository.repo_crud_hsbgn import HSBGNRepository
            kotas = HSBGNRepository.get_all_kotas()
            return jsonify(kotas), 200
        except Exception as e:
            loggerhsgbn.error(f"Error saat mengambil semua kota: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

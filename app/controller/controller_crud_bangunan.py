import logging
import json
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models_database import ActivityLog
from app.service.service_crud_bangunan import BangunanService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _log_action(action, target_id, detail):
    """Helper: simpan activity log ke database."""
    try:
        user = get_jwt_identity()
        # Flask-JWT-Extended 4.x: identity is a JSON string, parse it back to dict
        if isinstance(user, str):
            try:
                user = json.loads(user)
            except Exception:
                user = {}
        entry = ActivityLog(
            user_nama=user.get('nama', 'Unknown') if isinstance(user, dict) else 'Unknown',
            user_email=user.get('email', 'Unknown') if isinstance(user, dict) else 'Unknown',
            action=action,
            target='bangunan',
            target_id=str(target_id) if target_id else None,
            detail=detail,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Gagal mencatat activity log: {e}")



class BangunanController:
    @staticmethod
    def get_all():
        try:
            prov = request.args.get('provinsi')
            kota = request.args.get('kota')
            nama = request.args.get('nama')
            limit = request.args.get('limit')
            if limit is not None:
                try:
                    limit = int(limit)
                except ValueError:
                    limit = None
            data = BangunanService.get_all_bangunan(prov, kota, nama, limit)
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error get_all: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_by_id(bangunan_id):
        try:
            data = BangunanService.get_bangunan_by_id(bangunan_id)
            if data:
                return jsonify(data), 200
            return jsonify({"error": "Bangunan tidak ditemukan"}), 404
        except Exception as e:
            logger.error(f"Error get_by_id: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    @jwt_required()
    def create():
        try:
            data = request.get_json() or {}
            required = [
                "id_bangunan", "lon", "lat", "taxonomy",
                "luas", "nama_gedung", "alamat", "kota", "provinsi"
            ]
            missing = [f for f in required if f not in data]
            if missing:
                return jsonify({
                    "error": f"Kolom wajib tidak lengkap: {', '.join(missing)}"
                }), 400

            new_b = BangunanService.create_bangunan(data)
            bangunan_id = data.get('id_bangunan', '-')
            nama_gedung = data.get('nama_gedung', '-')
            _log_action(
                action='tambah',
                target_id=bangunan_id,
                detail=f"Menambahkan bangunan '{nama_gedung}' dengan id_bangunan {bangunan_id} di {data.get('kota', '-')}."
            )
            return jsonify(new_b), 201
        except Exception as e:
            logger.error(f"Error saat menambahkan bangunan: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    @jwt_required()
    def update(bangunan_id):
        try:
            data = request.get_json() or {}
            # Ambil data lama sebelum diupdate untuk mencatat perubahan
            old_data = BangunanService.get_bangunan_by_id(bangunan_id)
            data.pop("id_bangunan", None)
            data.pop("geom", None)
            upd = BangunanService.update_bangunan(bangunan_id, data)
            if upd:
                # Buat narasi perubahan field-by-field
                changes = []
                if old_data:
                    for key, new_val in data.items():
                        old_val = old_data.get(key)
                        if old_val is not None and str(old_val) != str(new_val):
                            changes.append(f"{key} dari '{old_val}' menjadi '{new_val}'")
                detail = f"Mengedit bangunan id_bangunan {bangunan_id}"
                if changes:
                    detail += ": " + "; ".join(changes)
                _log_action(action='edit', target_id=bangunan_id, detail=detail + ".")
                return jsonify(upd), 200
            return jsonify({"error": "Bangunan tidak ditemukan"}), 404
        except Exception as e:
            logger.error(f"Error saat mengedit bangunan: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    @jwt_required()
    def delete(bangunan_id, kota_val):
        try:
            old_data = BangunanService.get_bangunan_by_id(bangunan_id)
            ok = BangunanService.delete_bangunan(bangunan_id, kota_val)
            if ok:
                nama_gedung = old_data.get('nama_gedung', '-') if old_data else '-'
                _log_action(
                    action='hapus',
                    target_id=bangunan_id,
                    detail=f"Menghapus bangunan '{nama_gedung}' dengan id_bangunan {bangunan_id} di kota {kota_val}."
                )
                return jsonify({"message": "Bangunan berhasil dihapus"}), 200
            return jsonify({"error": "Bangunan tidak ditemukan"}), 404
        except Exception as e:
            logger.error(f"Error saat menghapus bangunan: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def new_id():
        taxonomy = request.args.get('taxonomy')
        if taxonomy not in ("FS", "FD", "ELECTRICITY", "HOTEL", "AIRPORT"):
            return jsonify({"error": "taxonomy invalid"}), 400
        try:
            new_id = BangunanService.generate_unique_id(taxonomy)
            return jsonify({"id_bangunan": new_id}), 200
        except Exception as e:
            logger.error(f"Error new_id: {e}")
            return jsonify({"error": "Terjadi kesalahan server"}), 500

    @staticmethod
    def get_provinsi_list():
        try:
            data = BangunanService.get_provinsi_list()
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error get_provinsi_list: {e}")
            return jsonify([]), 500

    @staticmethod
    def get_kota_list():
        prov = request.args.get('provinsi')
        try:
            data = BangunanService.get_kota_list(prov)
            return jsonify(data), 200
        except Exception as e:
            logger.error(f"Error get_kota_list: {e}")
            return jsonify([]), 500

    @staticmethod
    @jwt_required()
    def upload_csv():
        """
        POST /api/bangunan/upload
        Form-field 'file': CSV tanpa kolom geom, dengan header sesuai _fields di repo.
        """
        if 'file' not in request.files:
            return jsonify({"error": "File CSV harus di-upload"}), 400
        file = request.files['file']
        if file.filename == "":
            return jsonify({"error": "Nama file kosong"}), 400

        logger.info("Mulai upload CSV: %s", file.filename)
        try:
            result = BangunanService.upload_csv(file)
            logger.info("Upload CSV selesai sukses: %s", result)
            # Catat jumlah baris yang berhasil diupload
            inserted = result.get('inserted', 0)
            _log_action(
                action='upload_csv',
                target_id=None,
                detail=f"Upload CSV '{file.filename}' berhasil. {inserted} baris data bangunan ditambahkan."
            )
            return jsonify(result), 200

        except ValueError as ve:
            logger.error("Error upload CSV (ValueError): %s", ve)
            return jsonify({"error": str(ve)}), 400

        except Exception as e:
            logger.exception("Exception saat processing CSV upload")
            return jsonify({"error": "Terjadi kesalahan server saat upload CSV"}), 500

    @staticmethod
    @jwt_required()
    def recalc(bangunan_id):
        """
        POST /api/bangunan/<id>/recalc
        Hitung ulang directloss & AAL hanya untuk bangunan ini.
        """
        try:
            result = BangunanService.recalc_building_directloss_and_aal(bangunan_id)
            return jsonify({"status": "success", "detail": result}), 200
        except ValueError as ve:
            logger.error(f"Error recalc (ValueError): {ve}")
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            logger.error(f"Error recalc bangunan: {e}")
            return jsonify({"error": "Terjadi kesalahan perhitungan ulang"}), 500

    @staticmethod
    @jwt_required()
    def recalc_kota(kota_val):
        """
        POST /api/bangunan/kota/<kota_val>/recalc
        Hitung ulang directloss & AAL untuk seluruh bangunan di sebuah kota.
        """
        try:
            from app.service.service_directloss import recalc_city_directloss_and_aal
            result = recalc_city_directloss_and_aal(kota_val)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Error recalc kota {kota_val}: {e}")
            return jsonify({"error": "Terjadi kesalahan perhitungan ulang per kota"}), 500

import logging
import math
import time
import random
import io
import csv

import numpy as np
import pandas as pd
from app.extensions import db
from app.repository.repo_crud_bangunan import BangunanRepository
from app.models.models_database import HasilProsesDirectLoss, HasilAALProvinsi
from app.repository.repo_directloss import get_bangunan_data
from app.service.service_directloss import recalc_building_directloss_and_aal  # << import baru

PROB_CONFIG = {
    'gempa': {'500': 1/500, '250': 1/250, '100': 1/100},
    'banjir': {'100': 1/100, '50': 1/50, '25': 1/25},
    'longsor': {'5': 1/5, '2': 1/2},
    'gunungberapi': {'250': 1/250, '100': 1/100, '50': 1/50}
}

logger = logging.getLogger(__name__)

class BangunanService:
    @staticmethod
    def get_all_bangunan(provinsi=None, kota=None, nama=None):
        return BangunanRepository.get_all(provinsi, kota, nama)

    @staticmethod
    def get_bangunan_by_id(bangunan_id):
        return BangunanRepository.get_by_id(bangunan_id)

    @staticmethod
    def create_bangunan(data):
        return BangunanRepository.create(data)

    @staticmethod
    def update_bangunan(bangunan_id, data):
        return BangunanRepository.update(bangunan_id, data)

    # PASTIKAN KONFIGURASI INI TERSEDIA DI LUAR FUNGSI

    # Akhir bagian konfigurasi

    @staticmethod
    def delete_bangunan(bangunan_id, kota_val):
        """
        Menghapus data bangunan dan mengupdate AAL kota secara inkremental
        menggunakan metode trapesium yang benar.
        """
        logger.debug(f"=== START delete_bangunan (Trapezoid) for {bangunan_id} ===")
        
        kode_bgn = bangunan_id.split('_')[0].lower()

        # 1. Ambil data Direct Loss dari bangunan yang akan dihapus
        old_record = db.session.query(HasilProsesDirectLoss).filter_by(id_bangunan=bangunan_id).one_or_none()
        
        if not old_record:
            # Jika tidak ada data direct loss, hapus saja data bangunannya
            logger.warning(f"No direct loss record found for {bangunan_id}. Deleting building only.")
            BangunanRepository.delete(bangunan_id)
            db.session.commit()
            return {"message": f"Bangunan {bangunan_id} deleted. No AAL update needed."}

        old_losses = {c.name: getattr(old_record, c.name, 0) for c in old_record.__table__.columns if c.name.startswith('direct_loss_')}

        # 2. Ambil baris AAL kota yang akan diupdate
        aal_row = db.session.query(HasilAALProvinsi).filter_by(kota=kota_val).one_or_none()
        if not aal_row:
            raise RuntimeError(f"AAL untuk kota '{kota_val}' tidak ditemukan saat mencoba menghapus bangunan.")

        # 3. Hitung AAL yang disumbangkan oleh bangunan ini (ini adalah delta-nya)
        for disaster, prob_config in PROB_CONFIG.items():
            sorted_probs_data = sorted(prob_config.items(), key=lambda item: item[1])
            probabilities = [0] + [prob for _, prob in sorted_probs_data]

            # Ambil kerugian dari bangunan yang dihapus
            losses_to_remove = [0] + [old_losses.get(f'direct_loss_{disaster}_{rp}', 0) for rp, _ in sorted_probs_data]
            
            # Hitung AAL yang akan dihilangkan (delta)
            delta_aal = np.trapz(y=losses_to_remove, x=probabilities)

            # Kurangi nilai AAL dari total kota
            col_bgn = f"aal_{disaster}_{kode_bgn.lower()}"
            col_tot = f"aal_{disaster}_total"

            current_bgn_aal = getattr(aal_row, col_bgn, 0) or 0
            current_tot_aal = getattr(aal_row, col_tot, 0) or 0

            setattr(aal_row, col_bgn, float(current_bgn_aal - delta_aal))
            setattr(aal_row, col_tot, float(current_tot_aal - delta_aal))
            logger.debug(f"AAL to remove for {disaster}: {delta_aal:.2f}. Updating {col_bgn} and {col_tot}")

        # 4. Hapus record dari database dan commit semua perubahan
        try:
            # Hapus record direct loss
            db.session.delete(old_record)
            
            # Hapus record bangunan itu sendiri
            BangunanRepository.delete(bangunan_id)
            
            # Commit semua perubahan (update AAL dan delete) dalam satu transaksi
            db.session.commit()
            logger.info(f"✅ Successfully deleted {bangunan_id} and updated AAL for kota '{kota_val}'")

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Failed to delete building or update AAL: {e}")
            raise

        return {"message": f"Bangunan {bangunan_id} has been successfully deleted and AAL has been updated."}


    @staticmethod
    def generate_unique_id(taxonomy: str) -> str:
        if taxonomy not in ("BMN", "FS", "FD"):
            raise ValueError("kode_bangunan invalid, harus BMN/FS/FD")
        while True:
            ts = int(time.time())
            suffix = random.randint(100, 999)
            candidate = f"{taxonomy}_{ts}{suffix}"
            if not BangunanRepository.exists_id(candidate):
                return candidate

    @staticmethod
    def get_provinsi_list():
        return BangunanRepository.get_provinsi_list()

    @staticmethod
    def get_kota_list(provinsi):
        return BangunanRepository.get_kota_list(provinsi)

    @staticmethod
    def upload_csv(file_storage):
        """
        Baca CSV dengan kolom:
          nama_gedung, alamat, provinsi, kota,
          lon, lat,
          kode_bangunan (BMN/FS/FD),
          taxonomy (MUR/MCF/CR/Light Wood),
          luas
        Generate id_bangunan per baris dari kode_bangunan,
        lalu insert tanpa geom (Postgres akan generate geom).
        """
        text = file_storage.stream.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        created = 0

        for row in reader:
            # trim all inputs
            nama     = row.get("nama_gedung","").strip()
            alamat   = row.get("alamat","").strip()
            prov     = row.get("provinsi","").strip()
            kota     = row.get("kota","").strip()
            kode     = row.get("kode_bangunan","").strip()   # BMN/FS/FD
            tax      = row.get("taxonomy","").strip()        # MUR/MCF/CR/Light Wood
            lon      = float(row.get("lon") or 0)
            lat      = float(row.get("lat") or 0)
            luas     = float(row.get("luas") or 0)
            jumlah_lantai = int(row.get("jumlah_lantai") or 1) 

            # generate id from kode_bangunan, not taxonomy
            if kode not in ("BMN","FS","FD"):
                raise ValueError(f"Invalid kode_bangunan '{kode}' at line {reader.line_num}")
            data = {
                "id_bangunan": BangunanService.generate_unique_id(kode),
                "nama_gedung": nama,
                "alamat":      alamat,
                "provinsi":    prov,
                "kota":        kota,
                "lon":         lon,
                "lat":         lat,
                "taxonomy":    tax,
                "luas":        luas,
                "jumlah_lantai": jumlah_lantai
            }

            # insert record (geom akan di-generate di Postgres)
            BangunanRepository.create(data)
            created += 1

        return {"created": created}

    # ====================================================================
    # Metode baru: recalc Direct Loss & AAL untuk satu bangunan spesifik
    # ====================================================================
    @staticmethod
    def recalc_building_directloss_and_aal(bangunan_id: str):
        """
        Pertama periksa eksistensi bangunan di DB.
        Jika ada, delegasikan ke service_directloss.recalc_building_directloss_and_aal.
        """
        if not BangunanRepository.exists_id(bangunan_id):
            # kembalikan HTTP 400 via controller dengan ValueError di-raise
            raise ValueError(f"Bangunan '{bangunan_id}' tidak ditemukan")
        # panggil service_directloss yang melakukan perhitungan ulang
        return recalc_building_directloss_and_aal(bangunan_id)

from flask import jsonify
import logging
import pandas as pd

logger = logging.getLogger(__name__)

from app.service.service_kurva_gempa import process_data as process_gempa
from app.service.service_kurva_banjir_r import process_data as process_banjir_r
from app.service.service_kurva_banjir_rc import process_data as process_banjir_rc
from app.service.service_kurva_banjir import process_data_combined as process_banjir_combined
from app.service.service_kurva_tsunami import process_data as process_tsunami

from app.models.models_database import (
    RawGempa,       HasilProsesGempa,
    RawTsunami,     HasilProsesTsunami,
    RawBanjir,      HasilProsesBanjir,
    RawBanjirR,     HasilProsesBanjirR,
    RawBanjirRC,    HasilProsesBanjirRC,
)
from app.extensions import db


# ======================== GEMPA ========================
def process_kurva_gempa():
    try:
        # Optimasi: Ambil hanya kolom numerik (hindari geom agar tidak timeout)
        raw = db.session.query(
            RawGempa.id_lokasi,
            RawGempa.pga_100, RawGempa.pga_200,
            RawGempa.pga_250, RawGempa.pga_500, RawGempa.pga_1000
        ).all()
        
        if not raw:
            return jsonify({"error": "No data found in model_intensitas_gempa table"}), 404

        df = pd.DataFrame(raw, columns=['id_lokasi', 'pga_100', 'pga_200', 'pga_250', 'pga_500', 'pga_1000'])
        # Kolom sudah sesuai: pga_100, pga_200, pga_250, pga_500, pga_1000

        output = process_gempa(df)
        output.to_csv("output_kurva_gempa.csv", index=False)

        return jsonify({
            "status": "success",
            "message": "Gempa data successfully processed and saved to database",
            "processed_data_count": len(output)
        })

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


# ======================== TSUNAMI ========================
def process_kurva_tsunami():
    try:
        # Optimasi: Ambil hanya kolom numerik
        raw = db.session.query(
            RawTsunami.id_lokasi,
            RawTsunami.inundansi
        ).all()
        
        if not raw:
            return jsonify({"error": "No data found in model_intensitas_tsunami table"}), 404

        df = pd.DataFrame(raw, columns=['id_lokasi', 'inundansi'])
        # Kolom: id_lokasi, inundansi

        output = process_tsunami(df)
        output.to_csv("output_kurva_tsunami.csv", index=False)

        return jsonify({
            "status": "success",
            "message": "Tsunami data successfully processed and saved to database",
            "processed_data_count": len(output)
        })

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


# ======================== BANJIR R ========================
def process_kurva_banjir_r():
    try:
        # Optimasi: Ambil hanya kolom numerik (hindari geom agar tidak timeout)
        raw = db.session.query(
            RawBanjir.id_lokasi,
            RawBanjir.r_2, RawBanjir.r_5, RawBanjir.r_10,
            RawBanjir.r_25, RawBanjir.r_50,
            RawBanjir.r_100, RawBanjir.r_250
        ).all()
        
        if not raw:
            return jsonify({"error": "No data found in model_intensitas_banjir table"}), 404

        df = pd.DataFrame(raw, columns=['id_lokasi', 'r_2', 'r_5', 'r_10', 'r_25', 'r_50', 'r_100', 'r_250'])
        # Kolom: id_lokasi, r_2, r_5, r_10, r_25, r_50, r_100, r_250

        output = process_banjir_r(df)
        output.to_csv("output_kurva_banjir_r.csv", index=False)

        return jsonify({
            "status": "success",
            "message": "Banjir R data successfully processed and saved to database",
            "processed_data_count": len(output)
        })

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


# ======================== BANJIR RC ========================
def process_kurva_banjir_rc():
    try:
        # Optimasi: Ambil hanya kolom numerik
        raw = db.session.query(
            RawBanjir.id_lokasi,
            RawBanjir.rc_2, RawBanjir.rc_5, RawBanjir.rc_10,
            RawBanjir.rc_25, RawBanjir.rc_50,
            RawBanjir.rc_100, RawBanjir.rc_250
        ).all()
        
        if not raw:
            return jsonify({"error": "No data found in model_intensitas_banjir table"}), 404

        df = pd.DataFrame(raw, columns=['id_lokasi', 'rc_2', 'rc_5', 'rc_10', 'rc_25', 'rc_50', 'rc_100', 'rc_250'])
        # Kolom: id_lokasi, rc_2, rc_5, rc_10, rc_25, rc_50, rc_100, rc_250

        output = process_banjir_rc(df)
        output.to_csv("output_kurva_banjir_rc.csv", index=False)

        return jsonify({
            "status": "success",
            "message": "Banjir RC data successfully processed and saved to database",
            "processed_data_count": len(output)
        })

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
# ======================== BANJIR COMBINED ========================
def process_kurva_banjir_all():
    """
    Memproses R dan RC sekaligus dengan sistem Batch Processing (Chunks)
    untuk menghindari timeout pada data besar (814k baris).
    """
    try:
        # 1. Hitung total data
        total_count = db.session.query(RawBanjir).count()
        if total_count == 0:
            return jsonify({"error": "No data found in model_intensitas_banjir table"}), 404

        logger.info(f"🚀 Memulai Batch Processing untuk {total_count} baris...")
        
        # 2. Persiapan: Bersihkan tabel hasil lama
        db.session.query(HasilProsesBanjir).delete()
        db.session.commit()

        CHUNK_SIZE = 50000
        offset = 0
        processed_count = 0

        while offset < total_count:
            # 3. Ambil data per chunk
            raw_chunk = db.session.query(
                RawBanjir.id_lokasi,
                RawBanjir.r_2, RawBanjir.r_5, RawBanjir.r_10,
                RawBanjir.r_25, RawBanjir.r_50, RawBanjir.r_100, RawBanjir.r_250,
                RawBanjir.rc_2, RawBanjir.rc_5, RawBanjir.rc_10,
                RawBanjir.rc_25, RawBanjir.rc_50, RawBanjir.rc_100, RawBanjir.rc_250
            ).order_by(RawBanjir.id_lokasi).limit(CHUNK_SIZE).offset(offset).all()

            if not raw_chunk:
                break

            df_chunk = pd.DataFrame(raw_chunk, columns=[
                'id_lokasi', 
                'r_2', 'r_5', 'r_10', 'r_25', 'r_50', 'r_100', 'r_250',
                'rc_2', 'rc_5', 'rc_10', 'rc_25', 'rc_50', 'rc_100', 'rc_250'
            ])

            # 4. Proses Interpolasi (Combined R & RC)
            output_chunk = process_banjir_combined(df_chunk)

            # 5. Simpan ke Database (menggunakan pandas to_sql untuk efisiensi)
            # engine = db.engine
            output_chunk.to_sql(
                'dmg_ratio_banjir', 
                con=db.engine, 
                if_exists='append', 
                index=False,
                method='multi',
                chunksize=1000
            )

            processed_count += len(output_chunk)
            offset += CHUNK_SIZE
            logger.info(f"✅ Chunk selesai: {processed_count}/{total_count} baris diproses.")

        return jsonify({
            "status": "success",
            "message": "Flood (R & RC) data successfully processed (Combined & Batched)",
            "total_processed": processed_count
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Batch Processing error: {str(e)}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


# ======================== FUNGSI SIMPAN DATABASE ========================
def save_to_database(output_data, model_class, clear_old_data=True):
    try:
        if clear_old_data:
            db.session.query(model_class).delete()
            db.session.commit()

        output_data = output_data.astype(float)

        new_records = [
            model_class(**row.to_dict())
            for _, row in output_data.iterrows()
        ]

        db.session.bulk_save_objects(new_records)
        db.session.commit()

        print(f"✅ {len(new_records)} records saved to {model_class.__tablename__}")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving to database: {e}")
        raise

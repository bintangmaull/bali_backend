# app/service/service_kurva_tsunami.py

import logging
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from app.repository.repo_kurva_tsunami import get_reference_curves_tsunami
from app.extensions import db
from app.models.models_database import HasilProsesTsunami

logger = logging.getLogger(__name__)

TAXONOMY_TYPES = ['cr', 'mcf']

def to_float(v):
    if pd.isna(v):
        return None
    return float(v)

# interpolate_spline removed in favor of vectorized approach

def process_data(input_data):
    """
    Proses data Tsunami: interpolasi CR, MCF, MUR, W untuk kolom inundansi.
    Input DataFrame harus berisi kolom: id_lokasi, inundansi
    Simpan ke dmg_ratio_tsunami (bulk insert/update).
    """
    logger.info("📥 Mulai interpolasi data Tsunami...")
    rc = get_reference_curves_tsunami()
    if not rc:
        logger.warning("⚠️ Kurva Tsunami kosong, dibatalkan.")
        return pd.DataFrame()

    df = input_data.copy()
    df['inundansi'] = pd.to_numeric(df['inundansi'], errors='coerce')

    # Interpolasi per tipe kurva
    for tipe, ref in rc.items():
        x_ref, y_ref = ref['x'], ref['y']
        logger.info(f"📊 Kurva {tipe}: X={x_ref}, Y={y_ref}")
        
        if len(x_ref) < 2:
            logger.warning(f"⚠️ Titik kurva {tipe} < 2, dilewati.")
            continue
            
        interp_func = interp1d(x_ref, y_ref, kind='linear', fill_value='extrapolate')
        
        out_col = f'dmgratio_{tipe.lower()}_inundansi'
        
        vals = df['inundansi'].to_numpy()
        valid_mask = ~np.isnan(vals)
        
        interp_vals = np.zeros_like(vals)
        interp_vals[valid_mask] = interp_func(vals[valid_mask].astype(float))
        interp_vals = np.clip(interp_vals, 0, 1)
        
        df[out_col] = np.where(valid_mask, interp_vals, None)

    # Enforce ordering: cr ≤ mcf
    cr  = 'dmgratio_cr_inundansi'
    mcf = 'dmgratio_mcf_inundansi'
    df[mcf] = df[[cr, mcf]].max(axis=1)

    # Siapkan result
    cols = ['id_lokasi', cr, mcf]
    result = df[cols].copy()
    # Pastikan id_lokasi adalah integer
    result['id_lokasi'] = result['id_lokasi'].astype(float).astype(int)
    
    # Kolom damage ratio tetap float
    dmgr_cols = [c for c in cols if c != 'id_lokasi']
    result[dmgr_cols] = result[dmgr_cols].applymap(to_float)
    
    logger.info(f"✅ Interpolasi Tsunami selesai: {len(result)} baris.")

    # Simpan ke Database (Clear & Bulk Insert)
    try:
        # 1. Hapus data lama
        db.session.query(HasilProsesTsunami).delete()

        # 2. Siapkan data untuk bulk insert
        mappings = result.to_dict('records')

        # 3. Bulk insert
        db.session.bulk_insert_mappings(HasilProsesTsunami, mappings)
        db.session.commit()
        logger.info(f"✅ Berhasil menyimpan {len(mappings)} data ke tabel dmg_ratio_tsunami.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Gagal simpan data Tsunami ke database: {e}")

    return result

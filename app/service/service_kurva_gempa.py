# app/service/service_kurva_gempa.py

import logging
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from app.repository.repo_kurva_gempa import get_reference_curves_gempa
from app.extensions import db
from app.models.models_database import HasilProsesGempa

logger = logging.getLogger(__name__)

PGA_SCALES = ['100', '200', '250', '500', '1000']
TAXONOMY_TYPES = ['cr', 'mcf']

def to_float(v):
    """Helper: None if NaN/None, else Python float."""
    if pd.isna(v):
        return None
    return float(v)

# interpolate_spline function removed in favor of vectorized approach below

def process_data(input_data):
    """
    Proses data Gempa: interpolasi CR, MCF, MUR, W untuk PGA 100/200/250/500/1000.
    Input DataFrame harus berisi kolom: id_lokasi, pga_100, pga_200, pga_250, pga_500, pga_1000
    Simpan ke dmg_ratio_gempa (bulk insert/update).
    """
    logger.info("📥 Mulai interpolasi data Gempa...")
    rc = get_reference_curves_gempa()
    if not rc:
        logger.warning("⚠️ Kurva Gempa kosong, dibatalkan.")
        return pd.DataFrame()

    df = input_data.copy()
    for s in PGA_SCALES:
        df[f'pga_{s}'] = pd.to_numeric(df[f'pga_{s}'], errors='coerce')

    # Interpolasi per tipe kurva per skala
    for tipe, ref in rc.items():
        x_ref, y_ref = ref['x'], ref['y']
        logger.info(f"📊 Kurva {tipe}: X={x_ref}, Y={y_ref}")
        
        if len(x_ref) < 2:
            logger.warning(f"⚠️ Titik kurva {tipe} < 2, dilewati.")
            continue
            
        # Buat interpolator linear sekali untuk tiap kurva
        interp_func = interp1d(x_ref, y_ref, kind='linear', fill_value='extrapolate')
        
        for s in PGA_SCALES:
            in_col  = f'pga_{s}'
            out_col = f'dmgratio_{tipe.lower()}_pga{s}'
            
            # Vektorisasi: Jalankan spline pada seluruh kolom sekaligus
            vals = df[in_col].to_numpy()
            valid_mask = ~np.isnan(vals)
            
            interp_vals = np.zeros_like(vals)
            interp_vals[valid_mask] = interp_func(vals[valid_mask].astype(float))
            # Clamp [0, 1]
            interp_vals = np.clip(interp_vals, 0, 1)
            
            # Pasang None untuk yang NaN asli
            df[out_col] = np.where(valid_mask, interp_vals, None)

    # Enforce ordering: cr ≤ mcf
    for s in PGA_SCALES:
        cr  = f'dmgratio_cr_pga{s}'
        mcf = f'dmgratio_mcf_pga{s}'
        df[mcf] = df[[cr, mcf]].max(axis=1)

    # Siapkan result
    cols = ['id_lokasi'] + [
        f'dmgratio_{t}_pga{s}'
        for s in PGA_SCALES for t in TAXONOMY_TYPES
    ]
    result = df[cols].copy()
    # Pastikan id_lokasi adalah integer (tidak ada .0 jika disimpan ke varchar)
    result['id_lokasi'] = result['id_lokasi'].astype(float).astype(int)
    
    # Kolom damage ratio tetap float
    dmgr_cols = [c for c in cols if c != 'id_lokasi']
    result[dmgr_cols] = result[dmgr_cols].applymap(to_float)
    
    logger.info(f"✅ Interpolasi selesai: {len(result)} baris.")

    # Simpan ke Database (Clear & Bulk Insert agar lebih stabil)
    try:
        # 1. Hapus data lama
        db.session.query(HasilProsesGempa).delete()
        
        # 2. Siapkan data untuk bulk insert
        mappings = result.to_dict('records')
        
        # 3. Bulk insert
        db.session.bulk_insert_mappings(HasilProsesGempa, mappings)
        db.session.commit()
        logger.info(f"✅ Berhasil menyimpan {len(mappings)} data ke tabel dmg_ratio_gempa.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Gagal simpan data Gempa ke database: {e}")

    return result

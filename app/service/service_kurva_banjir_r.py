# app/service/service_kurva_banjir_r.py

import logging
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from app.repository.repo_kurva_banjir import get_reference_curves_banjir
from app.extensions import db
from app.models.models_database import HasilProsesBanjirR

logger = logging.getLogger(__name__)

R_SCALES = ['2', '5', '10', '25', '50', '100', '250']

# interpolate_spline removed in favor of vectorized approach below

def process_data(input_data: pd.DataFrame) -> pd.DataFrame:
    """
    Untuk setiap baris input_data:
      - ambil referensi kurva tipe '1' & '2' (jumlah lantai)
      - interpolasi r_25, r_50, r_100, r_250
      - hasilkan kolom dmgratio_1_r* dan dmgratio_2_r*
    Input DataFrame harus berisi kolom: id_lokasi, r_25, r_50, r_100, r_250
    """
    logger.info("📥 Memulai proses interpolasi Banjir R...")

    reference_curves = get_reference_curves_banjir()

    df = input_data.copy()
    for s in R_SCALES:
        df[f'r_{s}'] = pd.to_numeric(df[f'r_{s}'], errors='coerce')

    # Inisialisasi kolom hasil
    for tipe in ['1', '2']:
        for s in R_SCALES:
            df[f'dmgratio_{tipe}_r{s}'] = None

    # Interpolasi untuk tiap tipe (lantai 1 vs 2)
    for tipe, ref in reference_curves.items():
        x_ref, y_ref = ref['x'], ref['y']
        if not x_ref or not y_ref:
            logger.warning(f"⚠️ Referensi tipe {tipe} kosong: seluruh dmgratio_{tipe}_r* = None")
            continue
        logger.info(f"📊 Interpolasi kurva tipe {tipe} (n={len(x_ref)})")
        
        if len(x_ref) < 2:
            logger.warning(f"⚠️ Titik kurva {tipe} < 2, dilewati.")
            continue
            
        interp_func = interp1d(x_ref, y_ref, kind='linear', fill_value='extrapolate')
        
        for s in R_SCALES:
            in_col  = f'r_{s}'
            out_col = f'dmgratio_{tipe}_r{s}'
            
            vals = df[in_col].to_numpy()
            valid_mask = ~np.isnan(vals)
            
            interp_vals = np.zeros_like(vals)
            interp_vals[valid_mask] = interp_func(vals[valid_mask].astype(float))
            interp_vals = np.clip(interp_vals, 0, 0.4)
            
            df[out_col] = np.where(valid_mask, interp_vals, None)

    cols = ['id_lokasi'] + [
        f'dmgratio_{t}_r{s}'
        for t in ['1', '2'] for s in R_SCALES
    ]
    result = df[cols].copy()
    # Pastikan id_lokasi adalah integer
    result['id_lokasi'] = result['id_lokasi'].astype(float).astype(int)
    
    # Kolom damage ratio tetap float (atau None)
    # result sudah terisi di loop sebelumnya, kita hanya memastikan tipe id_lokasi murni.

    # Database saving removed to avoid timeout for large data.
    # User will insert manually from the generated CSV.
    return result

    return result

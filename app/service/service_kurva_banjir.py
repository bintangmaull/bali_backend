# app/service/service_kurva_banjir.py

import logging
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from app.repository.repo_kurva_banjir import get_reference_curves_banjir

logger = logging.getLogger(__name__)

R_SCALES = ['25', '50', '100', '250']
RC_SCALES = ['25', '50', '100', '250']

def process_data_combined(input_data: pd.DataFrame) -> pd.DataFrame:
    """
    Memproses interpolasi untuk R dan RC sekaligus.
    Input DataFrame harus berisi: id_lokasi, r_25, r_50, r_100, r_250, rc_25, rc_50, rc_100, rc_250
    """
    logger.info("📥 Memulai proses interpolasi Banjir (R & RC) Combined...")

    reference_curves = get_reference_curves_banjir()
    df = input_data.copy()
    
    # Ensure numeric
    for s in R_SCALES:
        df[f'r_{s}'] = pd.to_numeric(df[f'r_{s}'], errors='coerce')
    for s in RC_SCALES:
        df[f'rc_{s}'] = pd.to_numeric(df[f'rc_{s}'], errors='coerce')

    # Interpolasi untuk tiap tipe (lantai 1 vs 2)
    for tipe, ref in reference_curves.items():
        x_ref, y_ref = ref['x'], ref['y']
        if not x_ref or not y_ref:
            continue
        
        spline = CubicSpline(x_ref, y_ref, extrapolate=True)
        
        # Process R
        for s in R_SCALES:
            vals = df[f'r_{s}'].to_numpy()
            valid_mask = ~np.isnan(vals)
            interp_vals = np.zeros_like(vals)
            interp_vals[valid_mask] = spline(vals[valid_mask].astype(float))
            df[f'dmgratio_{tipe}_r{s}'] = np.where(valid_mask, np.clip(interp_vals, 0, 1), 0)

        # Process RC
        for s in RC_SCALES:
            vals = df[f'rc_{s}'].to_numpy()
            valid_mask = ~np.isnan(vals)
            interp_vals = np.zeros_like(vals)
            interp_vals[valid_mask] = spline(vals[valid_mask].astype(float))
            df[f'dmgratio_{tipe}_rc{s}'] = np.where(valid_mask, np.clip(interp_vals, 0, 1), 0)

    # Reorder columns
    cols = ['id_lokasi']
    for t in ['1', '2']:
        for s in R_SCALES: cols.append(f'dmgratio_{t}_r{s}')
        for s in RC_SCALES: cols.append(f'dmgratio_{t}_rc{s}')
        
    result = df[cols].copy()
    result['id_lokasi'] = result['id_lokasi'].astype(float).astype(int)
    
    return result

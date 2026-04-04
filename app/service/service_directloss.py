# service_directloss.py

import os
import sys
import math
import numpy as np
import pandas as pd
import logging

# Silencing FutureWarnings for cleaner logs
pd.set_option('future.no_silent_downcasting', True)

from sqlalchemy import text
from app.extensions import db
from app.models.models_database import HasilProsesDirectLoss, HasilAALProvinsi, RekapAsetKota
from app.repository.repo_directloss import (
    get_bangunan_data,
    get_all_disaster_data,
    get_db_connection,
    get_city_bangunan_data,
    get_city_disaster_data,
    DISASTER_MAPPING,
)
from collections import defaultdict
from typing import Any, cast, Dict

# UTF-8 for console/logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logger
DEBUG_DIR = os.path.join(os.getcwd(), "debug_output")
os.makedirs(DEBUG_DIR, exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(DEBUG_DIR, "service_directloss.log"), encoding="utf-8")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(formatter)
logger.addHandler(sh)

# =============================================================================
# Konfigurasi probabilitas per bencana per return period
# Urutan dari RP terkecil ke terbesar
# =============================================================================
PROB_CONFIG = {
    'gempa':    {'100': 1/100,  '200': 1/200, '250': 1/250, '500': 1/500,  '1000': 1/1000},
    'tsunami':  {'inundansi': 1/2500},
    'banjir_r': {'2': 1/2, '5': 1/5, '10': 1/10, '25': 1/25, '50': 1/50, '100': 1/100, '250': 1/250},
    'banjir_rc':{'2': 1/2, '5': 1/5, '10': 1/10, '25': 1/25, '50': 1/50, '100': 1/100, '250': 1/250},
}

TAXONOMY_TYPES = ['cr', 'mcf']


def _get_damage_ratio_by_taxonomy(df_raw, taxonomy_col_prefix, scale_suffix):
    """
    Pilih damage ratio berdasarkan taxonomy building.
    taxonomy_col_prefix: nama prefix kolom di df_raw, contoh 'nilai_y_{tax}_{prefix}{scale}'
    Kembalikan numpy array damage ratio.
    """
    raise NotImplementedError("Gunakan fungsi inline di bawah")


def _compute_dl_taxonomy(bld, df_raw, name, pre, s):
    """
    Hitung direct loss untuk bencana berbasis taksonomi (gempa/tsunami).
    Pilih kolom berdasarkan taxonomy masing-masing bangunan.
    """
    luas  = bld['luas'].to_numpy()
    hsbgn = bld['adjusted_hsbgn'].to_numpy()

    # Suffix kolom: contoh 'pga100' atau 'inundansi'
    suffix = f"{pre}{s}" if pre else s

    tax_lower  = bld['taxonomy'].str.lower().to_numpy()
    damage_ratio = np.zeros(len(bld))

    for tax in TAXONOMY_TYPES:
        col = f"nilai_y_{tax}_{suffix}"
        if col in df_raw.columns:
            mask = (tax_lower == tax)
            damage_ratio[mask] = df_raw[col].to_numpy()[mask]

    col_out = f"direct_loss_{name}_{s}" if pre else f"direct_loss_{name}_{s}"
    bld[col_out] = luas * hsbgn * damage_ratio
    bld[col_out] = bld[col_out].fillna(0)
    return col_out


def _compute_dl_lantai(bld, df_raw, name, pre, s):
    """
    Hitung direct loss untuk bencana berbasis jumlah lantai (banjir_r/rc).
    """
    luas   = bld['luas'].to_numpy()
    hsbgn  = bld['adjusted_hsbgn'].to_numpy()
    floors = np.clip(bld['jumlah_lantai'].to_numpy(), 1, 2)

    col1 = f"nilai_y_1_{pre}{s}"
    col2 = f"nilai_y_2_{pre}{s}"
    y1 = df_raw[col1].to_numpy() if col1 in df_raw.columns else np.zeros(len(bld))
    y2 = df_raw[col2].to_numpy() if col2 in df_raw.columns else np.zeros(len(bld))

    v = np.where(floors == 1, y1, y2)
    col_out = f"direct_loss_{name}_{s}"
    bld[col_out] = luas * hsbgn * v
    bld[col_out] = bld[col_out].fillna(0)
    return col_out


def _compute_hsbgn_adjusted(bld: pd.DataFrame) -> pd.DataFrame:
    """
    Pilih HSBGN berdasarkan jumlah lantai:
    - jumlah_lantai = 1 -> hsbgn_sederhana
    - jumlah_lantai > 1 -> hsbgn_tidaksederhana
    
    Lalu sesuaikan dengan multiplier berdasarkan kode_bangunan (Airport, Hotel, dll).
    """
    df = bld.copy()
    
    # Pilih HSBGN dasar berdasarkan jumlah_lantai
    df['base_hsbgn'] = np.where(
        df['jumlah_lantai'] <= 1,
        df['hsbgn_sederhana'],
        df['hsbgn_tidaksederhana']
    )
    
    # Multiplier mapping (case-insensitive)
    multipliers = {
        'airport': 1.0,
        'hotel':   1.0,
        'electricity': 1.0,
        # FS & FD menggunakan base (multiplier 1.0)
    }
    
    def get_multiplier(row):
        code = str(row['kode_bangunan']).lower()
        return multipliers.get(code, 1.0)
        
    df['multiplier'] = df.apply(get_multiplier, axis=1)
    df['adjusted_hsbgn'] = df['base_hsbgn'] * df['multiplier']
    
    return df


def _reindex_disaster_data(disaster_data, bld):
    """Selaraskan semua DataFrame hazard ke id_bangunan bld."""
    for name, df in disaster_data.items():
        df = (
            df
            .set_index('id_bangunan')
            .reindex(bld['id_bangunan'], fill_value=0)
            .reset_index(drop=True)
        )
        disaster_data[name] = df
    return disaster_data


# =============================================================================
# NAMA KOLOM direct_loss sesuai format tabel hasil_proses_directloss
# Gempa   : direct_loss_pga_100, _200, _250, _500, _1000
# Tsunami : direct_loss_inundansi
# Banjir_R : direct_loss_r_2, _5, _10, _25, _50, _100, _250
# Banjir_RC: direct_loss_rc_2, _5, _10, _25, _50, _100, _250
# =============================================================================

def _col_direct_loss(name, s):
    """Buat nama kolom direct_loss sesuai tabel DB."""
    if name == 'gempa':
        return f"direct_loss_pga_{s}"
    elif name == 'tsunami':
        return f"direct_loss_inundansi"
    elif name == 'banjir_r':
        return f"direct_loss_r_{s}"
    elif name == 'banjir_rc':
        return f"direct_loss_rc_{s}"
    return f"direct_loss_{name}_{s}"


def _compute_all_dl(bld, disaster_data):
    """
    Hitung semua kolom direct_loss di bld DataFrame.
    Returns list kolom yang baru ditambahkan.
    """
    dl_cols = []
    for name, df_raw in disaster_data.items():
        cfg = DISASTER_MAPPING[name]
        pre    = cfg['prefix']
        scales = cfg['scales']
        mode   = cfg['mode']

        for s in scales:
            col_db = _col_direct_loss(name, s)  # nama kolom di DB

            if mode == 'taxonomy':
                suffix = f"{pre}{s}" if pre else s
                tax_lower    = bld['taxonomy'].str.lower().to_numpy()
                damage_ratio = np.zeros(len(bld))
                for tax in TAXONOMY_TYPES:
                    col_raw = f"nilai_y_{tax}_{suffix}"
                    if col_raw in df_raw.columns:
                        mask = (tax_lower == tax)
                        damage_ratio[mask] = df_raw[col_raw].to_numpy()[mask]

            elif mode == 'lantai':
                floors = np.clip(bld['jumlah_lantai'].to_numpy(), 1, 2)
                col1 = f"nilai_y_1_{pre}{s}"
                col2 = f"nilai_y_2_{pre}{s}"
                y1 = df_raw[col1].to_numpy() if col1 in df_raw.columns else np.zeros(len(bld))
                y2 = df_raw[col2].to_numpy() if col2 in df_raw.columns else np.zeros(len(bld))
                damage_ratio = np.where(floors == 1, y1, y2)

            else:
                damage_ratio = np.zeros(len(bld))

            luas  = bld['luas'].to_numpy()
            hsbgn = bld['adjusted_hsbgn'].to_numpy()
            bld[col_db] = luas * hsbgn * damage_ratio
            bld[col_db] = bld[col_db].fillna(0)
            dl_cols.append(col_db)
            logger.debug(f"{col_db} sample: {bld[col_db].head(3).tolist()}")

    # === TEMPORARY: PRESERVE GEMPA DATA ===
    try:
        from app.extensions import db
        import pandas as pd
        from sqlalchemy import text
        
        gempa_cols = [
            'direct_loss_pga_100', 'direct_loss_pga_200', 
            'direct_loss_pga_250', 'direct_loss_pga_500', 
            'direct_loss_pga_1000'
        ]
        
        sql = f"SELECT id_bangunan, {', '.join(gempa_cols)} FROM hasil_proses_directloss"
        with db.engine.connect() as conn:
            existing_gempa = pd.read_sql(text(sql), conn)
            
        bld_temp = bld.merge(existing_gempa, on='id_bangunan', how='left')
        for c in gempa_cols:
            bld[c] = bld_temp[c].fillna(0.0)
            
        dl_cols.extend(gempa_cols)
        logger.debug("✅ Preserved existing gempa direct loss data from DB")
    except Exception as e:
        logger.warning(f"⚠️ Failed to preserve existing gempa data: {e}")
    # =======================================

    return list(dict.fromkeys(dl_cols))  # unique, preserve order


# =============================================================================
# Fungsi Utama: process_all_disasters
# =============================================================================

def process_all_disasters():
    logger.debug("=== START process_all_disasters ===")

    # Deletions of HasilProsesDirectLoss and HasilAALProvinsi are moved 
    # to their respective insertion blocks to ensure data is not empty 
    # during the lengthy calculation process.

    # 1) Bangunan
    bld = get_bangunan_data()
    logger.debug(f"📥 Buildings: {len(bld)} rows")
    if 'kode_bangunan' not in bld.columns or bld['kode_bangunan'].isna().all():
        bld['kode_bangunan'] = (
            bld['id_bangunan'].astype(str)
               .str.split('_').str[0]
               .str.lower()
        )
    bld['jumlah_lantai'] = bld['jumlah_lantai'].fillna(0).astype(int)
    bld['luas']  = bld['luas'].fillna(0)
    bld['taxonomy'] = bld['taxonomy'].fillna('').str.lower()
    bld = _compute_hsbgn_adjusted(bld)
    
    # Calculate asset value for exposure columns
    bld['building_asset'] = bld['luas'] * bld['adjusted_hsbgn']

    # 2) Hazard data
    disaster_data = get_all_disaster_data()
    disaster_data = _reindex_disaster_data(disaster_data, bld)

    # 3) Direct Loss
    dl_cols = _compute_all_dl(bld, disaster_data)

    # 4) Save Direct Loss
    bld = bld.drop_duplicates(subset='id_bangunan', keep='last')
    cols_to_keep = ['id_bangunan'] + dl_cols
    mappings = bld[cols_to_keep].to_dict('records')
    try:
        # Hapus data lama dan insert data baru dalam satu transaksi
        db.session.query(HasilProsesDirectLoss).delete()
        db.session.bulk_insert_mappings(HasilProsesDirectLoss, mappings)
        db.session.commit()
        logger.info("✅ Direct Loss saved (replaced data in single transaction)")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving Direct Loss failed: {e}")
        raise

    # 5) Dump CSV
    csv_path = os.path.join(DEBUG_DIR, "directloss_all.csv")
    cols_to_dump = ["kota", "kode_bangunan", "building_asset"] + dl_cols
    bld.to_csv(csv_path, index=False, sep=';', columns=cols_to_dump)
    logger.debug(f"📄 CSV DirectLoss subset for AAL: {csv_path}")

    # 6) Rekap Aset Kota
    _calculate_rekap_aset(bld)

    # 7) AAL
    calculate_aal()
    logger.debug("=== END process_all_disasters ===")
    return csv_path


def _calculate_rekap_aset(bld: pd.DataFrame):
    """
    Menghitung rekap aset per kota per tipe bangunan.
    Aset = luas * adjusted_hsbgn.
    """
    logger.debug("=== START _calculate_rekap_aset ===")
    
    # 1. Hitung nilai aset per bangunan
    df = bld.copy()
    df['building_asset'] = df['luas'] * df['adjusted_hsbgn']
    
    # 2. Agregasi per kota
    from app.repository.repo_directloss import DISASTER_MAPPING
    from app.models.models_database import LossRatioGempa
    
    # Supported types matching LossRatioGempa and frontend expectations
    supported_types = ['fs', 'fd', 'electricity', 'hotel', 'airport', 'residential', 'bmn']
    # Mapping for dl_exposure JSON (fs/fd used in frontend for healthcare/educational)
    exposure_mapping = {
        'fs': 'healthcare',
        'fd': 'educational',
        'electricity': 'electricity',
        'hotel': 'hotel',
        'airport': 'airport',
        'residential': 'residential',
        'bmn': 'bmn'
    }
    
    results = []
    for kota, group in df.groupby('kota'):
        res = {'id_kota': kota}
        
        # A) Hitung Aset per Tipe
        total_count = 0
        total_value = 0.0
        for btype in supported_types:
            sub = group[group['kode_bangunan'].str.lower() == btype]
            count = len(sub)
            value = float(sub['building_asset'].sum())
            res[f'count_{btype}'] = count
            res[f'total_asset_{btype}'] = value
            total_count += count
            total_value += value
            
        res['count_total'] = total_count
        res['total_asset_total'] = total_value
        
        # B) Hitung Direct Loss Sum & Ratio (Terhadap Total Aset Kota)
        dl_exposure_dict = {}

        for name, cfg in DISASTER_MAPPING.items():
            pre = cfg['prefix']
            scales = cfg['scales']
            for s in scales:
                rp_suffix = f"{pre}_{s}" if pre else s
                dl_col = f"direct_loss_{rp_suffix}"
                
                # Total for the whole city
                sum_val = 0.0
                ratio = 0.0

                if name == 'gempa':
                    # Fetch from LossRatioGempa table as requested by USER
                    # rp_suffix example: "100" or "200"
                    try:
                        lr_rec = db.session.query(LossRatioGempa).filter(
                            LossRatioGempa.kota == kota,
                            LossRatioGempa.return_period == int(s)
                        ).first()
                        
                        if lr_rec:
                            # Use average ratio for the city-level summary
                            ratios_to_avg = [
                                getattr(lr_rec, f"{exposure_mapping[bt].lower()}_loss_ratio", 0) or 0
                                for bt in supported_types
                            ]
                            ratio = sum(ratios_to_avg) / len(ratios_to_avg) if ratios_to_avg else 0.0
                            sum_val = total_value * ratio # Representative sum based on avg ratio
                        else:
                            logger.warning(f"⚠️ No LossRatioGempa record for {kota} RP {s}")
                    except Exception as e:
                        logger.error(f"⚠️ Failed to fetch LossRatioGempa: {e}")
                else:
                    # Original logic for other disasters
                    sum_val = float(group[dl_col].sum()) if dl_col in group.columns else 0.0
                    ratio = ((sum_val / total_value) * 100.0) if total_value > 0 else 0.0
                
                res[f'dl_sum_{rp_suffix}'] = sum_val
                res[f'ratio_{rp_suffix}'] = ratio
                
                # Breakdown by Exposure
                for btype in supported_types:
                    if btype not in dl_exposure_dict:
                        dl_exposure_dict[btype] = {}
                    
                    if name == 'gempa' and lr_rec:
                        # Use ratio from LossRatioGempa
                        field_name = f"{exposure_mapping[btype].lower()}_loss_ratio"
                        val = getattr(lr_rec, field_name, 0) or 0
                        dl_exposure_dict[btype][rp_suffix] = float(val)
                    else:
                        sub = group[group['kode_bangunan'].str.lower() == btype]
                        sum_val_exp = float(sub[dl_col].sum()) if dl_col in sub.columns else 0.0
                        dl_exposure_dict[btype][rp_suffix] = sum_val_exp

        import json
        res['dl_exposure'] = dl_exposure_dict
                
        results.append(res)
        
    # 3. Simpan ke Database
    try:
        if results:
            city_ids = [r['id_kota'] for r in results]
            db.session.query(RekapAsetKota).filter(RekapAsetKota.id_kota.in_(city_ids)).delete(synchronize_session=False)
            db.session.bulk_insert_mappings(RekapAsetKota, results)
        db.session.commit()
        logger.info(f"✅ Rekap Aset Kota saved ({len(results)} cities)")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving Rekap Aset failed: {e}")
        # Jangan raise agar proses AAL tetap lanjut jika rekap gagal



# =============================================================================
# calculate_aal
# =============================================================================

def calculate_aal():
    """
    Hitung Average Annual Loss (AAL) menggunakan metode trapesium.
    Pengelompokan per KOTA dan kode_bangunan.
    """
    logger.debug("=== START calculate_aal (Trapezoid, Per-Kota) ===")

    path = os.path.join(DEBUG_DIR, "directloss_all.csv")
    if not os.path.exists(path):
        logger.error(f"❌ Input file for AAL not found at: {path}")
        return

    df = pd.read_csv(path, delimiter=';')
    df.fillna(0, inplace=True)

    # Agregasi per kota & kode_bangunan
    grouped = df.groupby(['kota', 'kode_bangunan']).sum().reset_index()

    results = []
    unique_building_codes = sorted(df['kode_bangunan'].unique())

    for kota, kota_df in grouped.groupby('kota'):
        kota_result = defaultdict(float)
        kota_result['id_kota'] = kota

        for disaster, config in PROB_CONFIG.items():
            aal_total_disaster = 0.0

            for _, row in kota_df.iterrows():
                kode_bangunan = row['kode_bangunan']

                # Urutkan probabilitas dari kecil ke besar
                sorted_probs_data = sorted(config.items(), key=lambda x: x[1])
                probabilities = [0] + [prob for _, prob in sorted_probs_data]
                losses = [0]

                for rp, _ in sorted_probs_data:
                    col = _col_direct_loss(disaster, rp)
                    losses.append(row.get(col, 0))

                # Map building code to column suffix
                suffix = kode_bangunan.lower()
                if suffix == 'residential':
                    suffix = 'res'

                aal_col = f'aal_{_disaster_prefix(disaster)}_{suffix}'
                kota_result[aal_col] = float(cast(Any, kota_result[aal_col])) + aal_value
                aal_total_disaster   = float(aal_total_disaster) + aal_value

            kota_result[f'aal_{_disaster_prefix(disaster)}_total'] = float(aal_total_disaster)

        # Aggregation of Exposure (Total Asset) per category
        for _, row in kota_df.iterrows():
            suffix = row['kode_bangunan'].lower()
            if suffix == 'residential': suffix = 'res'
            
            # Only add for requested exposure columns
            if suffix in ['hotel', 'res', 'airport']:
                kota_result[suffix] = float(kota_result.get(suffix, 0)) + float(row.get('building_asset', 0))

        results.append(kota_result)

    if not results:
        logger.warning("Tidak ada hasil AAL yang dapat dihitung.")
        return

    final_df = pd.DataFrame(results).fillna(0)

    # Baris Total Keseluruhan
    total_row = final_df.select_dtypes(include=[np.number]).sum().to_dict()
    total_row['id_kota'] = "Total Keseluruhan"
    final_df = pd.concat([final_df, pd.DataFrame([total_row])], ignore_index=True)

    # Urutkan kolom
    output_columns = ['id_kota']
    dis_prefixes = [_disaster_prefix(d) for d in PROB_CONFIG.keys()]
    for dp in dis_prefixes:
        for bgn in unique_building_codes:
            output_columns.append(f'aal_{dp}_{bgn.lower()}')
        output_columns.append(f'aal_{dp}_total')

    existing_cols = [c for c in output_columns if c in final_df.columns]
    final_df = final_df[existing_cols]

    logger.debug(f"AAL calculation complete. Shape: {final_df.shape}")
    out_csv = os.path.join(DEBUG_DIR, "AAL_trapezoid_per_kota.csv")
    final_df.to_csv(out_csv, index=False, sep=';')
    logger.debug(f"📄 CSV AAL saved: {out_csv}")

    # Simpan ke Database
    try:
        # Hapus data lama dan insert data baru dalam satu transaksi untuk menghindari data kosong
        db.session.query(HasilAALProvinsi).delete()
        
        # Filter hanya kolom / atribut yang ada di model
        valid_keys = {c.key for c in HasilAALProvinsi.__table__.columns}
        records = []
        for rec in final_df.to_dict('records'):
            records.append({k: v for k, v in rec.items() if k in valid_keys})
        db.session.bulk_insert_mappings(HasilAALProvinsi, records)
        db.session.commit()
        logger.info("✅ AAL saved to database (replaced data in single transaction)")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving AAL failed: {e}")
        raise


    logger.debug("=== END calculate_aal ===")


def _disaster_prefix(disaster_name):
    """Mapping nama bencana ke prefix kolom AAL di tabel hasil_aal_kota."""
    mapping = {
        'gempa':     'pga',
        'tsunami':   'inundansi',
        'banjir_r':  'r',
        'banjir_rc': 'rc',
    }
    return mapping.get(disaster_name, disaster_name)


def recalc_city_rekap_only(kota_name: str):
    """
    Hanya mengupdate tabel rekap_aset_kota berdasarkan data bangunan saat ini.
    Sangat cepat karena tidak ada perhitungan hazard join.
    """
    logger.debug(f"=== START city rekap only for: {kota_name} ===")
    bld = get_city_bangunan_data(kota_name)
    if bld.empty:
        # Jika kosong, hapus rekap kota tersebut
        db.session.query(RekapAsetKota).filter_by(id_kota=kota_name).delete()
        db.session.commit()
        return
    
    # HSBGN Dinamis
    bld = _compute_hsbgn_adjusted(bld)
    # Rekap Aset
    _calculate_rekap_aset(bld)
    db.session.commit()
    logger.debug(f"=== END city rekap only for: {kota_name} ===")


# =============================================================================
# recalc_building_directloss_and_aal (incremental - satu bangunan)
# =============================================================================

def recalc_building_directloss_and_aal(bangunan_id: str):
    """
    Menghitung ulang Direct Loss dan AAL untuk satu bangunan secara inkremental.
    """
    logger.debug(f"=== START incremental recalc for {bangunan_id} ===")

    engine = get_db_connection()
    with engine.connect() as conn:
        b_query = text("""
            SELECT
                b.geom, b.luas, 
                COALESCE(k.hsbgn_sederhana, 0) AS hsbgn_sederhana,
                COALESCE(k.hsbgn_tidaksederhana, 0) AS hsbgn_tidaksederhana,
                COALESCE(b.jumlah_lantai, 0) AS jumlah_lantai,
                LOWER(b.taxonomy) AS taxonomy,
                b.kota, LOWER(split_part(b.id_bangunan, '_', 1)) AS kode_bangunan
            FROM bangunan_copy b
            LEFT JOIN kota k ON TRIM(LOWER(k.kota)) = TRIM(LOWER(b.kota))
            WHERE b.id_bangunan = :id
        """)
        b = conn.execute(b_query, {"id": bangunan_id}).mappings().first()
        if not b:
            raise ValueError(f"Bangunan {bangunan_id} tidak ditemukan")

        luas_val        = b["luas"] or 0
        hsbgn_sederhana = b["hsbgn_sederhana"] or 0
        hsbgn_tidak_s   = b["hsbgn_tidaksederhana"] or 0
        raw_floors      = int(b["jumlah_lantai"] or 0)
        kota_val        = b["kota"]
        kode_bgn        = b["kode_bangunan"]
        taxonomy_val    = b["taxonomy"] or ''

        # logic HSBGN Dinamis
        base_hsbgn = hsbgn_sederhana if raw_floors <= 1 else hsbgn_tidak_s
        
        # Multiplier Tipe
        multipliers = {
            'airport': 1.0,
            'hotel':   1.0,
            'electricity': 1.0,
        }
        multiplier = multipliers.get(str(kode_bgn).lower(), 1.0)
        hsbgn_val = base_hsbgn * multiplier

        floor_lantai  = int(np.clip(raw_floors, 1, 2))

        # 2. Hitung Direct Loss baru untuk setiap bencana
        direct_losses = {}

        for name, cfg in DISASTER_MAPPING.items():
            # === TEMPORARY: SKIP GEMPA ===
            if name == 'gempa':
                continue
            # ===============================

            pre       = cfg['prefix']
            scales    = cfg['scales']
            threshold = cfg['threshold']
            dmgr      = cfg['dmgr']
            raw_tbl   = cfg['raw']
            mode      = cfg['mode']

            if mode == 'taxonomy':
                # Bangun vcols semua taksonomi
                vcols = []
                for s in scales:
                    suffix = f"{pre}{s}" if pre else s
                    for tax in TAXONOMY_TYPES:
                        col_db  = f"h.dmgratio_{tax}_{suffix}"
                        col_as  = f"nilai_y_{tax}_{suffix}"
                        vcols.append(f"{col_db} AS {col_as}")
            else:  # lantai
                vcols = []
                for s in scales:
                    vcols.append(f"h.dmgratio_1_{pre}{s} AS nilai_y_1_{pre}{s}")
                    vcols.append(f"h.dmgratio_2_{pre}{s} AS nilai_y_2_{pre}{s}")

            subq_sql = ", ".join(vcols)
            outer_sql = ", ".join([expr.split(" AS ")[1].strip() for expr in vcols])

            shape = cfg.get("shape", "circle")
            if shape == "box":
                where_clause = f"r.geom && ST_Expand(b.geom, {threshold} / 111320.0)"
                order_by = f"b.geom <-> r.geom"
            else:
                where_clause = f"ST_DWithin(b.geom::geography, r.geom::geography, {threshold})"
                order_by = f"b.geom::geography <-> r.geom::geography"

            sql = text(f"""
                SELECT {outer_sql}
                FROM bangunan_copy b
                JOIN LATERAL (
                    SELECT {subq_sql}
                    FROM {raw_tbl} r
                    JOIN {dmgr} h USING(id_lokasi)
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT 1
                ) AS near ON TRUE
                WHERE b.id_bangunan = :id
            """)
            near = conn.execute(sql, {"id": bangunan_id}).mappings().first() or {}

            for s in scales:
                col_db = _col_direct_loss(name, s)
                v = 0.0
                if mode == 'taxonomy':
                    suffix  = f"{pre}{s}" if pre else s
                    col_raw = f"nilai_y_{taxonomy_val}_{suffix}"
                    v = near.get(col_raw, 0) or 0
                elif mode == 'lantai':
                    col_raw = f"nilai_y_{floor_lantai}_{pre}{s}"
                    v = near.get(col_raw, 0) or 0

                v = v if v and not math.isnan(float(v)) else 0.0
                direct_losses[col_db] = float(luas_val * hsbgn_val * v)

    # 3. Ambil old, simpan baru
    old_record = db.session.query(HasilProsesDirectLoss).filter_by(id_bangunan=bangunan_id).one_or_none()
    old_losses = (
        {c.name: getattr(old_record, c.name, 0)
         for c in HasilProsesDirectLoss.__table__.columns
         if c.name.startswith('direct_loss_')}
        if old_record else {}
    )

    # === TEMPORARY: PRESERVE GEMPA DATA ===
    gempa_cols = [
        'direct_loss_pga_100', 'direct_loss_pga_200', 
        'direct_loss_pga_250', 'direct_loss_pga_500', 
        'direct_loss_pga_1000'
    ]
    for c in gempa_cols:
        direct_losses[c] = old_losses.get(c, 0.0)
    # =======================================

    if old_record:
        db.session.delete(old_record)
        
    new_rec = HasilProsesDirectLoss(id_bangunan=bangunan_id, **direct_losses)
    db.session.add(new_rec)
    db.session.commit()
    logger.debug(f"✅ DirectLoss (recalc) saved for {bangunan_id} in single transaction")

    try:
        # 4. Delta AAL per bencana
        aal_row = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota_val).one_or_none()
        if not aal_row:
            raise RuntimeError(f"AAL untuk kota '{kota_val}' tidak ditemukan. Jalankan proses AAL penuh dahulu.")

        for disaster, prob_config in PROB_CONFIG.items():
            dis_pre = _disaster_prefix(disaster)
            sorted_probs_data = sorted(prob_config.items(), key=lambda item: item[1])
            probabilities = [0] + [prob for _, prob in sorted_probs_data]

            old_losses_sorted = [0] + [old_losses.get(_col_direct_loss(disaster, rp), 0) for rp, _ in sorted_probs_data]
            old_aal = np.trapz(y=old_losses_sorted, x=probabilities)

            new_losses_sorted = [0] + [direct_losses.get(_col_direct_loss(disaster, rp), 0) for rp, _ in sorted_probs_data]
            new_aal = np.trapz(y=new_losses_sorted, x=probabilities)

            delta_aal = new_aal - old_aal

            col_bgn = f"aal_{dis_pre}_{kode_bgn.lower()}"
            col_tot = f"aal_{dis_pre}_total"

            current_bgn = getattr(aal_row, col_bgn, 0) or 0
            current_tot = getattr(aal_row, col_tot, 0) or 0

            setattr(aal_row, col_bgn, float(current_bgn + delta_aal))
            setattr(aal_row, col_tot, float(current_tot + delta_aal))
            logger.debug(f"Delta AAL {disaster}: {delta_aal:.2f}. Updating {col_bgn} and {col_tot}")

        db.session.commit()
        logger.info(f"✅ AAL incrementally updated for kota '{kota_val}'")

        # 5. UPDATE REKAP KOTA (FAST)
        recalc_city_rekap_only(kota_val)

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Incremental recalc failed: {e}")
        raise
    finally:
        db.session.close()

    logger.debug(f"=== END incremental recalc for {bangunan_id} ===")

    return {"direct_losses": direct_losses, "status": "success"}


# =============================================================================
# recalc_city_directloss_and_aal (per kota - dipicu perubahan HSBGN)
# =============================================================================

def recalc_city_directloss_and_aal(kota_name: str):
    """
    Menghitung ulang Direct Loss dan AAL untuk SEMUA bangunan di satu kota.
    Dipicu ketika HSBGN kota tersebut diedit.
    """
    logger.info(f"=== START city recalc for city: {kota_name} ===")

    bld = get_city_bangunan_data(kota_name)
    logger.debug(f"📥 Buildings in {kota_name}: {len(bld)} rows")
    if bld.empty:
        return {"status": "success", "message": f"No buildings found in city {kota_name}"}

    if 'kode_bangunan' not in bld.columns or bld['kode_bangunan'].isna().all():
        bld['kode_bangunan'] = bld['id_bangunan'].astype(str).str.split('_').str[0].str.lower()

    bld['jumlah_lantai'] = bld['jumlah_lantai'].fillna(0).astype(int)
    bld['luas']          = bld['luas'].fillna(0)
    bld['taxonomy']      = bld['taxonomy'].fillna('').str.lower()
    
    # 1) HSBGN Dinamis
    bld = _compute_hsbgn_adjusted(bld)

    # 2) Direct Loss
    disaster_data = get_city_disaster_data(kota_name)
    disaster_data = _reindex_disaster_data(disaster_data, bld)
    dl_cols = _compute_all_dl(bld, disaster_data)

    # Update Direct Loss
    bld_ids = bld['id_bangunan'].tolist()
    try:
        db.session.query(HasilProsesDirectLoss).filter(
            HasilProsesDirectLoss.id_bangunan.in_(bld_ids)
        ).delete(synchronize_session=False)
        cols_to_keep = ['id_bangunan'] + dl_cols
        mappings = bld[cols_to_keep].to_dict('records')
        db.session.bulk_insert_mappings(HasilProsesDirectLoss, mappings)
        db.session.commit()
        logger.info(f"✅ City Direct Loss saved for {kota_name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving City Direct Loss failed: {e}")
        raise

    # 3) Rekap Aset Kota (Integrasi Baru)
    _calculate_rekap_aset(bld)

    # 4) Hitung AAL untuk kota ini
    kota_result = defaultdict(float)
    kota_result['id_kota'] = kota_name
    grouped = bld.groupby(['kode_bangunan']).sum(numeric_only=True).reset_index()

    for disaster, config in PROB_CONFIG.items():
        dis_pre = _disaster_prefix(disaster)
        aal_total_disaster = 0.0

        for _, row in grouped.iterrows():
            kode_bangunan = row['kode_bangunan']
            sorted_probs_data = sorted(config.items(), key=lambda x: x[1])
            probabilities = [0] + [prob for _, prob in sorted_probs_data]
            losses = [0]
            for rp, _ in sorted_probs_data:
                col = _col_direct_loss(disaster, rp)
                losses.append(row.get(col, 0))

            aal_value = np.trapz(y=losses, x=probabilities)
            aal_col = f'aal_{dis_pre}_{kode_bangunan.lower()}'
            kota_result[aal_col] = aal_value
            aal_total_disaster += aal_value

        kota_result[f'aal_{dis_pre}_total'] = aal_total_disaster

    # Update HasilAALProvinsi
    try:
        aal_row = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota_name).one_or_none()
        valid_keys = {c.key for c in HasilAALProvinsi.__table__.columns}
        if aal_row:
            for k, v in kota_result.items():
                if k != 'id_kota' and hasattr(aal_row, k):
                    setattr(aal_row, k, float(v))
        else:
            filtered = {k: v for k, v in kota_result.items() if k in valid_keys}
            new_aal  = HasilAALProvinsi(**filtered)
            db.session.add(new_aal)
        db.session.commit()
        logger.info(f"✅ City AAL updated for {kota_name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving City AAL failed: {e}")
        raise

    # Sinkronisasi Total Keseluruhan
    try:
        total_row = db.session.query(HasilAALProvinsi).filter_by(id_kota="Total Keseluruhan").one_or_none()
        if total_row:
            all_sums = db.session.query(
                *[db.func.sum(getattr(HasilAALProvinsi, c.key))
                  for c in HasilAALProvinsi.__table__.columns
                  if c.key != 'id_kota']
            ).filter(HasilAALProvinsi.id_kota != "Total Keseluruhan").first()
            if all_sums:
                col_names = [c.key for c in HasilAALProvinsi.__table__.columns if c.key != 'id_kota']
                for idx, col_name in enumerate(col_names):
                    setattr(total_row, col_name, float(all_sums[idx] or 0))
                db.session.commit()
                logger.info("✅ Total Keseluruhan sinkron")
    except Exception as e:
        logger.warning(f"⚠️ Gagal sinkronisasi Total Keseluruhan: {e}")
        db.session.rollback()
    finally:
        db.session.close()

    logger.info(f"=== END city recalc for {kota_name} ===")
    return {"status": "success", "city": kota_name}
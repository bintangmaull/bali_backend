# service_directloss.py

import os
import sys
import math
import numpy as np
import pandas as pd
import logging

from sqlalchemy import text 
from app.extensions import db
from app.models.models_database import HasilProsesDirectLoss, HasilAALProvinsi  # HasilAALProvinsi kini memetakan tabel hasil_aal_kota
from app.repository.repo_directloss import (
    get_bangunan_data, 
    get_all_disaster_data, 
    get_db_connection,
    get_city_bangunan_data,
    get_city_disaster_data
)
from collections import defaultdict

# UTF-8 for console/logging
sys.stdout.reconfigure(encoding='utf-8')
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

DISASTER_CONFIG = {
    "gempa": {"raw": "model_intensitas_gempa", "dmgr": "dmgratio_gempa", "prefix": "mmi", "scales": ["500", "250", "100"], "threshold": 9500, "damage_ratio_col": "nilai_y_cr_{pre}{s}"},
    "banjir": {"raw": "model_intensitas_banjir", "dmgr": "dmgratio_banjir_copy", "prefix": "depth", "scales": ["100", "50", "25"], "threshold": 700, "damage_ratio_col": "special_case"},
    "longsor": {"raw": "model_intensitas_longsor", "dmgr": "dmgratio_longsor", "prefix": "mflux", "scales": ["5", "2"], "threshold": 700, "damage_ratio_col": "nilai_y_mur_{pre}{s}"},
    "gunungberapi": {"raw": "model_intensitas_gunungberapi", "dmgr": "dmgratio_gunungberapi", "prefix": "kpa", "scales": ["250", "100", "50"], "threshold": 550, "damage_ratio_col": "nilai_y_lightwood_{pre}{s}"}
}

PROB_CONFIG = {
    'gempa': {'500': 1/500, '250': 1/250, '100': 1/100},
    'banjir': {'100': 1/100, '50': 1/50, '25': 1/25},
    'longsor': {'5': 1/5, '2': 1/2},
    'gunungberapi': {'250': 1/250, '100': 1/100, '50': 1/50}
}

def process_all_disasters():
    logger.debug("=== START process_all_disasters ===")

    # Clear old
    try:
        db.session.query(HasilProsesDirectLoss).delete()
        db.session.query(HasilAALProvinsi).delete()
        db.session.commit()
        logger.debug("✅ Cleared DirectLoss & AAL (per kota)")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Clearing old failed: {e}")

    # 1) Building data (with integer jumlah_lantai)
    bld = get_bangunan_data()
    logger.debug(f"📥 Buildings: {len(bld)} rows")
    if 'kode_bangunan' not in bld.columns or bld['kode_bangunan'].isna().all():
        bld['kode_bangunan'] = (
            bld['id_bangunan'].astype(str)
               .str.split('_').str[0]
               .str.lower()
        )
        logger.debug("🔧 Derived kode_bangunan from id_bangunan")
    bld['jumlah_lantai'] = bld['jumlah_lantai'].fillna(0).astype(int)
    bld['luas'] = bld['luas'].fillna(0)
    bld['hsbgn'] = bld['hsbgn'].fillna(0)

    coeff_map = {
        1: 1.000, 2: 1.090, 3: 1.120, 4: 1.135,
        5: 1.162, 6: 1.197, 7: 1.236, 8: 1.265,
    }
    floors_clipped = bld['jumlah_lantai'].clip(1, 8).astype(int)
    bld['hsbgn_coeff']     = floors_clipped.map(coeff_map).fillna(1.0)
    bld['adjusted_hsbgn']  = bld['hsbgn'] * bld['hsbgn_coeff']

    luas    = bld['luas'].to_numpy()
    hsbgn   = bld['adjusted_hsbgn'].to_numpy()

    # 2) Hazard data (reindexed to bld.index!)
    disaster_data = get_all_disaster_data()
    for name, df in disaster_data.items():
        # fill na, then reindex so length==len(bld)
        df = (
            df
            .set_index('id_bangunan')                  # pakai id_bangunan sebagai index
            .reindex(bld['id_bangunan'], fill_value=0) # selaraskan berdasarkan id_bangunan
            .reset_index(drop=True)                    # kembalikan index default agar 1-1 dengan bld
        )
        disaster_data[name] = df
        logger.debug(f"📥 {name}: {len(df)} rows (aligned to {len(bld)})")

    # 3) Direct loss calc
    prefix_map = {"gempa":"mmi","banjir":"depth","longsor":"mflux","gunungberapi":"kpa"}
    scales_map = {
      "gempa": ["500","250","100"],
      "banjir": ["100","50","25"],
      "longsor": ["5","2"],
      "gunungberapi": ["250","100","50"]
    }

    for name, df_raw in disaster_data.items():
        pre    = prefix_map[name]
        scales = scales_map[name]
        if name == "banjir":
            floors = np.clip(bld['jumlah_lantai'].to_numpy(), 1, 2)
            for s in scales:
                y1 = df_raw[f"nilai_y_1_{pre}{s}"].to_numpy()
                y2 = df_raw[f"nilai_y_2_{pre}{s}"].to_numpy()
                v = np.where(floors == 1, y1, y2)
                col = f"direct_loss_{name}_{s}"
                bld[col] = luas * hsbgn * v
                bld[col] = bld[col].fillna(0)
                logger.debug(f"{col} sample: {bld[col].head(3).tolist()}")
        else:
            for s in scales:
                # Mengambil kolom berdasarkan return period dan skala untuk gempa, longsor, dan gunung berapi
                damage_ratio_col = f"nilai_y_cr_{pre}{s}"  # Misalnya untuk gempa pada skala tertentu
                if name == "longsor":
                    damage_ratio_col = f"nilai_y_mur_{pre}{s}"  # Sesuaikan dengan longsor
                elif name == "gunungberapi":
                    damage_ratio_col = f"nilai_y_lightwood_{pre}{s}"  # Sesuaikan dengan gunung berapi

                damage_ratio = df_raw[damage_ratio_col].to_numpy()
                col = f"direct_loss_{name}_{s}"
                bld[col] = luas * hsbgn * damage_ratio
                bld[col] = bld[col].fillna(0)
                logger.debug(f"{col} sample: {bld[col].head(3).tolist()}")

    # 4) Save Direct Loss
    dl_cols = [c for c in bld.columns if c.startswith("direct_loss_")]

    bld = bld.drop_duplicates(subset='id_bangunan', keep='last')    

    mappings = [
        {"id_bangunan": row['id_bangunan'], **{c: row[c] for c in dl_cols}}
        for _, row in bld.iterrows()
    ]
    try:
        db.session.bulk_insert_mappings(HasilProsesDirectLoss, mappings)
        db.session.commit()
        logger.info("✅ Direct Loss saved")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving Direct Loss failed: {e}")
        raise

    # 5) Dump CSV & 6) AAL
    csv_path = os.path.join(DEBUG_DIR, "directloss_all.csv")
    cols_to_dump = ["kota", "kode_bangunan"] + dl_cols
    bld.to_csv(csv_path, index=False, sep=';', columns=cols_to_dump)
    logger.debug(f"📄 CSV DirectLoss subset for AAL: {csv_path}")

    calculate_aal()
    logger.debug("=== END process_all_disasters ===")
    return csv_path

def calculate_aal():
    """
    Menghitung Average Annual Loss (AAL) menggunakan metode trapesium.
    Pengelompokan dilakukan per KOTA (bukan per provinsi).
    Fungsi ini membaca data dari file CSV yang telah dibuat sebelumnya.
    """
    logger.debug("=== START calculate_aal (v5 Trapezoid, Per-Kota) ===")

    # 1. Baca data dari file CSV
    path = os.path.join(DEBUG_DIR, "directloss_all.csv")
    if not os.path.exists(path):
        logger.error(f"❌ Input file for AAL not found at: {path}")
        return

    df = pd.read_csv(path, delimiter=';')
    df.fillna(0, inplace=True)
    
    # 2. Konfigurasi Periode Ulang dan Probabilitas
    PROB_CONFIG = {
        'gempa': {'500': 1/500, '250': 1/250, '100': 1/100},
        'banjir': {'100': 1/100, '50': 1/50, '25': 1/25},
        'longsor': {'5': 1/5, '2': 1/2},
        'gunungberapi': {'250': 1/250, '100': 1/100, '50': 1/50}
    }

    # 3. Agregasi Direct Loss per KOTA dan kode_bangunan
    grouped = df.groupby(['kota', 'kode_bangunan']).sum().reset_index()

    # 4. Hitung AAL dengan Metode Trapesium
    results = []
    unique_building_codes = sorted(df['kode_bangunan'].unique())

    for kota, kota_df in grouped.groupby('kota'):
        kota_result = defaultdict(float)
        kota_result['kota'] = kota

        for disaster, config in PROB_CONFIG.items():
            aal_total_disaster = 0.0
            
            for _, row in kota_df.iterrows():
                kode_bangunan = row['kode_bangunan']
                
                probabilities = [0] + sorted(list(config.values()))
                losses = [0]

                for rp in sorted(config.keys(), key=float, reverse=True):
                    loss_col = f'direct_loss_{disaster}_{rp}'
                    losses.append(row.get(loss_col, 0))

                aal_value = np.trapz(y=losses, x=probabilities)
                
                aal_col_name = f'aal_{disaster}_{kode_bangunan.lower()}'
                kota_result[aal_col_name] += aal_value
                aal_total_disaster += aal_value
            
            kota_result[f'aal_{disaster}_total'] = aal_total_disaster

        results.append(kota_result)
    
    if not results:
        logger.warning("Tidak ada hasil AAL yang dapat dihitung.")
        return

    # 5. Konversi hasil ke DataFrame dan format akhir
    final_df = pd.DataFrame(results).fillna(0)
    
    # Menambahkan baris "Total Keseluruhan"
    total_row = final_df.select_dtypes(include=[np.number]).sum().to_dict()
    total_row['kota'] = "Total Keseluruhan"
    final_df = pd.concat([final_df, pd.DataFrame([total_row])], ignore_index=True)
    
    # Urutkan kolom sesuai permintaan
    output_columns = ['kota']
    for disaster in PROB_CONFIG.keys():
        for bgn_code in unique_building_codes:
             output_columns.append(f'aal_{disaster}_{bgn_code.lower()}')
        output_columns.append(f'aal_{disaster}_total')
    
    existing_cols = [col for col in output_columns if col in final_df.columns]
    final_df = final_df[existing_cols]

    logger.debug(f"AAL calculation complete. Shape: {final_df.shape}")
    out_csv = os.path.join(DEBUG_DIR, "AAL_trapezoid_per_kota.csv")
    final_df.to_csv(out_csv, index=False, sep=';')
    logger.debug(f"📄 CSV AAL (Trapezoid per kota) saved: {out_csv}")

    # 6. Simpan ke Database
    try:
        db.session.query(HasilAALProvinsi).delete()
        db.session.commit()
        db.session.bulk_insert_mappings(HasilAALProvinsi, final_df.to_dict('records'))
        db.session.commit()
        logger.info("✅ AAL (Trapezoid per kota) saved to database")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving AAL (Trapezoid per kota) failed: {e}")
        raise

    logger.debug("=== END calculate_aal (v5 Trapezoid, Per-Kota) ===")



def recalc_building_directloss_and_aal(bangunan_id: str):
    """
    Menghitung ulang Direct Loss dan AAL for satu bangunan secara inkremental
    menggunakan metode trapesium yang akurat. (v6 - Per Kota)
    """
    logger.debug(f"=== START incremental recalc (v6 Per-Kota) for {bangunan_id} ===")

    # 1. Ambil data bangunan dari database
    engine = get_db_connection()
    with engine.connect() as conn:
        b_query = text("""
            SELECT
                b.geom, b.luas, COALESCE(k.hsbgn, 0) AS hsbgn,
                COALESCE(b.jumlah_lantai, 0) AS jumlah_lantai,
                b.kota, LOWER(split_part(b.id_bangunan, '_', 1)) AS kode_bangunan
            FROM bangunan_copy b
            LEFT JOIN kota k ON b.kota = k.kota
            WHERE b.id_bangunan = :id
        """)
        b = conn.execute(b_query, {"id": bangunan_id}).mappings().first()
        if not b:
            raise ValueError(f"Bangunan {bangunan_id} tidak ditemukan")

        luas_val = b["luas"] or 0
        hsbgn_val_raw = b["hsbgn"] or 0
        raw_floors = int(b["jumlah_lantai"] or 0)
        kota_val = b["kota"]
        kode_bgn = b["kode_bangunan"]

        floor_banjir = int(np.clip(raw_floors, 1, 2))
        floor_hsbgn = int(np.clip(raw_floors, 1, 8))
        
        coeff_map = {1: 1.0, 2: 1.090, 3: 1.120, 4: 1.135, 5: 1.162, 6: 1.197, 7: 1.236, 8: 1.265}
        hsbgn_val = hsbgn_val_raw * coeff_map.get(floor_hsbgn, 1.0)

        # 2. Hitung Direct Loss baru untuk setiap skenario bencana
        direct_losses = {}
        for name, cfg in DISASTER_CONFIG.items():
            vcols = []
            damage_cols_map = {"gempa": "cr", "longsor": "mur", "gunungberapi": "lightwood"}
            if name == "banjir":
                for s in cfg['scales']:
                    vcols.append(f"h.dmgratio_1_{cfg['prefix']}{s} AS nilai_y_1_{cfg['prefix']}{s}")
                    vcols.append(f"h.dmgratio_2_{cfg['prefix']}{s} AS nilai_y_2_{cfg['prefix']}{s}")
            else:
                dmg_type = damage_cols_map.get(name)
                for s in cfg['scales']:
                    alias = cfg['damage_ratio_col'].format(pre=cfg['prefix'], s=s)
                    db_col_name = f"h.dmgratio_{dmg_type}_{cfg['prefix']}{s}"
                    vcols.append(f"{db_col_name} AS {alias}")
            
            subq_sql = ", ".join(vcols)
            outer_sql = ", ".join([expr.split(" AS ")[1].strip() for expr in vcols])

            sql = text(f"""
                SELECT {outer_sql}
                FROM bangunan_copy b
                JOIN LATERAL (
                    SELECT {subq_sql}
                    FROM {cfg['raw']} r
                    JOIN {cfg['dmgr']} h USING(id_lokasi)
                    WHERE ST_DWithin(b.geom::geography, r.geom::geography, {cfg['threshold']})
                    ORDER BY b.geom::geography <-> r.geom::geography
                    LIMIT 1
                ) AS near ON TRUE
                WHERE b.id_bangunan = :id
            """)
            near = conn.execute(sql, {"id": bangunan_id}).mappings().first() or {}

            for s in cfg['scales']:
                dlc = f"direct_loss_{name}_{s}"
                v = 0.0
                if name == "banjir":
                    y1 = near.get(f"nilai_y_1_{cfg['prefix']}{s}", 0)
                    y2 = near.get(f"nilai_y_2_{cfg['prefix']}{s}", 0)
                    v = y1 if floor_banjir == 1 else y2
                else:
                    damage_col_name = cfg['damage_ratio_col'].format(pre=cfg['prefix'], s=s)
                    v = near.get(damage_col_name, 0)
                
                v = v if v and not math.isnan(v) else 0.0
                direct_losses[dlc] = float(luas_val * hsbgn_val * v)

    # 3. Ambil DirectLoss LAMA dan simpan DirectLoss BARU
    old_record = db.session.query(HasilProsesDirectLoss).filter_by(id_bangunan=bangunan_id).one_or_none()
    old_losses = {c.name: getattr(old_record, c.name, 0) for c in HasilProsesDirectLoss.__table__.columns if c.name.startswith('direct_loss_')} if old_record else {}

    if old_record:
        db.session.delete(old_record)
        db.session.commit()
    new_rec = HasilProsesDirectLoss(id_bangunan=bangunan_id, **direct_losses)
    db.session.add(new_rec)
    db.session.commit()
    logger.debug(f"✅ DirectLoss (recalc) saved for {bangunan_id}")

    # 4. Hitung DELTA AAL menggunakan Metode Trapesium (per kota)
    aal_row = db.session.query(HasilAALProvinsi).filter_by(kota=kota_val).one_or_none()
    if not aal_row:
        raise RuntimeError(f"AAL untuk kota '{kota_val}' tidak ditemukan. Jalankan proses AAL penuh terlebih dahulu.")

    for disaster, prob_config in PROB_CONFIG.items():
        sorted_probs_data = sorted(prob_config.items(), key=lambda item: item[1])
        probabilities = [0] + [prob for _, prob in sorted_probs_data]

        old_aal_losses = [0] + [old_losses.get(f'direct_loss_{disaster}_{rp}', 0) for rp, _ in sorted_probs_data]
        old_aal_value = np.trapz(y=old_aal_losses, x=probabilities)

        new_aal_losses = [0] + [direct_losses.get(f'direct_loss_{disaster}_{rp}', 0) for rp, _ in sorted_probs_data]
        new_aal_value = np.trapz(y=new_aal_losses, x=probabilities)
        
        delta_aal = new_aal_value - old_aal_value

        col_bgn = f"aal_{disaster}_{kode_bgn.lower()}"
        col_tot = f"aal_{disaster}_total"

        current_bgn_aal = getattr(aal_row, col_bgn, 0) or 0
        current_tot_aal = getattr(aal_row, col_tot, 0) or 0
        
        setattr(aal_row, col_bgn, float(current_bgn_aal + delta_aal))
        setattr(aal_row, col_tot, float(current_tot_aal + delta_aal))
        
        logger.debug(f"Delta AAL for {disaster}: {delta_aal:.2f}. Updating {col_bgn} and {col_tot}")

    # Commit semua perubahan AAL ke database dalam satu transaksi
    db.session.commit()
    logger.info(f"✅ AAL (Trapezoid) incrementally updated for kota '{kota_val}'")
    logger.debug(f"=== END incremental recalc for {bangunan_id} ===")

    return {"direct_losses": direct_losses, "status": "success"}

def recalc_city_directloss_and_aal(kota_name: str):
    """
    Menghitung ulang Direct Loss dan AAL untuk SEMUA bangunan di satu kota.
    Ini dipicu ketika HSBGN kota tersebut diedit.
    """
    logger.info(f"=== START city recalc for city: {kota_name} ===")

    # 1) Ambil data bangunan di kota tersebut
    bld = get_city_bangunan_data(kota_name)
    logger.debug(f"📥 Buildings in {kota_name}: {len(bld)} rows")
    if bld.empty:
        return {"status": "success", "message": f"No buildings found in city {kota_name}"}

    # Derive kode_bangunan if missing
    if 'kode_bangunan' not in bld.columns or bld['kode_bangunan'].isna().all():
        bld['kode_bangunan'] = bld['id_bangunan'].astype(str).str.split('_').str[0].str.lower()
    
    bld['jumlah_lantai'] = bld['jumlah_lantai'].fillna(0).astype(int)
    bld['luas'] = bld['luas'].fillna(0)
    bld['hsbgn'] = bld['hsbgn'].fillna(0)

    coeff_map = {1: 1.000, 2: 1.090, 3: 1.120, 4: 1.135, 5: 1.162, 6: 1.197, 7: 1.236, 8: 1.265}
    floors_clipped = bld['jumlah_lantai'].clip(1, 8).astype(int)
    bld['hsbgn_coeff'] = floors_clipped.map(coeff_map).fillna(1.0)
    bld['adjusted_hsbgn'] = bld['hsbgn'] * bld['hsbgn_coeff']

    luas = bld['luas'].to_numpy()
    hsbgn = bld['adjusted_hsbgn'].to_numpy()

    # 2) Ambil Hazard data untuk kota ini
    disaster_data = get_city_disaster_data(kota_name)
    for name, df in disaster_data.items():
        df = (
            df.set_index('id_bangunan')
            .reindex(bld['id_bangunan'], fill_value=0)
            .reset_index(drop=True)
        )
        disaster_data[name] = df

    # 3) Direct loss calc
    prefix_map = {"gempa":"mmi","banjir":"depth","longsor":"mflux","gunungberapi":"kpa"}
    scales_map = {
      "gempa": ["500","250","100"],
      "banjir": ["100","50","25"],
      "longsor": ["5","2"],
      "gunungberapi": ["250","100","50"]
    }

    for name, df_raw in disaster_data.items():
        pre = prefix_map[name]
        scales = scales_map[name]
        if name == "banjir":
            floors = np.clip(bld['jumlah_lantai'].to_numpy(), 1, 2)
            for s in scales:
                y1 = df_raw[f"nilai_y_1_{pre}{s}"].to_numpy()
                y2 = df_raw[f"nilai_y_2_{pre}{s}"].to_numpy()
                v = np.where(floors == 1, y1, y2)
                col = f"direct_loss_{name}_{s}"
                bld[col] = luas * hsbgn * v
                bld[col] = bld[col].fillna(0)
        else:
            for s in scales:
                damage_ratio_col = f"nilai_y_cr_{pre}{s}"
                if name == "longsor":
                    damage_ratio_col = f"nilai_y_mur_{pre}{s}"
                elif name == "gunungberapi":
                    damage_ratio_col = f"nilai_y_lightwood_{pre}{s}"

                damage_ratio = df_raw[damage_ratio_col].to_numpy()
                col = f"direct_loss_{name}_{s}"
                bld[col] = luas * hsbgn * damage_ratio
                bld[col] = bld[col].fillna(0)

    # 4) Update Direct Loss in Database
    dl_cols = [c for c in bld.columns if c.startswith("direct_loss_")]
    bld_ids = bld['id_bangunan'].tolist()

    try:
        db.session.query(HasilProsesDirectLoss).filter(HasilProsesDirectLoss.id_bangunan.in_(bld_ids)).delete(synchronize_session=False)
        mappings = [
            {"id_bangunan": row['id_bangunan'], **{c: row[c] for c in dl_cols}}
            for _, row in bld.iterrows()
        ]
        db.session.bulk_insert_mappings(HasilProsesDirectLoss, mappings)
        db.session.commit()
        logger.info(f"✅ City Direct Loss saved for {kota_name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving City Direct Loss failed: {e}")
        raise

    # 5) Calculate AAL for this city
    kota_result = defaultdict(float)
    kota_result['kota'] = kota_name
    grouped = bld.groupby(['kode_bangunan']).sum().reset_index()

    for disaster, config in PROB_CONFIG.items():
        aal_total_disaster = 0.0
        for _, row in grouped.iterrows():
            kode_bangunan = row['kode_bangunan']
            probabilities = [0] + sorted(list(config.values()))
            losses = [0]
            for rp in sorted(config.keys(), key=float, reverse=True):
                loss_col = f'direct_loss_{disaster}_{rp}'
                losses.append(row.get(loss_col, 0))
            aal_value = np.trapz(y=losses, x=probabilities)
            aal_col_name = f'aal_{disaster}_{kode_bangunan.lower()}'
            kota_result[aal_col_name] = aal_value
            aal_total_disaster += aal_value
        kota_result[f'aal_{disaster}_total'] = aal_total_disaster

    # 6) Update HasilAALProvinsi for this city
    try:
        aal_row = db.session.query(HasilAALProvinsi).filter_by(kota=kota_name).one_or_none()
        if aal_row:
            for k, v in kota_result.items():
                if k != 'kota' and hasattr(aal_row, k):
                    setattr(aal_row, k, float(v))
        else:
            # Only use keys that exist in the model
            valid_keys = {c.name for c in HasilAALProvinsi.__table__.columns}
            filtered_result = {k: v for k, v in kota_result.items() if k in valid_keys}
            new_aal = HasilAALProvinsi(**filtered_result)
            db.session.add(new_aal)
        db.session.commit()
        logger.info(f"✅ City AAL updated for {kota_name}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Saving City AAL failed: {e}")
        raise

    # 7) Update "Total Keseluruhan" row
    try:
        total_row = db.session.query(HasilAALProvinsi).filter_by(kota="Total Keseluruhan").one_or_none()
        if total_row:
            all_sums = db.session.query(
                *[db.func.sum(getattr(HasilAALProvinsi, c.name)) 
                  for c in HasilAALProvinsi.__table__.columns 
                  if c.name != 'kota']
            ).filter(HasilAALProvinsi.kota != "Total Keseluruhan").first()
            if all_sums:
                col_names = [c.name for c in HasilAALProvinsi.__table__.columns if c.name != 'kota']
                for idx, col_name in enumerate(col_names):
                    setattr(total_row, col_name, float(all_sums[idx] or 0))
                db.session.commit()
                logger.info("✅ Total Keseluruhan sinkron")
    except Exception as e:
        logger.warning(f"⚠️ Gagal sinkronisasi Total Keseluruhan: {e}")
        db.session.rollback()

    logger.info(f"=== END city recalc for {kota_name} ===")
    return {"status": "success", "city": kota_name}
import sys

new_code = """
def recalc_city_directloss_and_aal(kota_name: str):
    \"\"\"
    Menghitung ulang Direct Loss dan AAL untuk SEMUA bangunan di satu kota.
    Ini dipicu ketika HSBGN kota tersebut diedit.
    \"\"\"
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
                if hasattr(aal_row, k):
                    setattr(aal_row, k, float(v))
        else:
            new_aal = HasilAALProvinsi(**kota_result)
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
"""

with open(r"e:\Dashboard\backend-capstone-aal\app\service\service_directloss.py", "a", encoding="utf-8") as f:
    f.write(new_code)

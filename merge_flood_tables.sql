
-- REVISI SQL Migrasi untuk Menggabungkan Tabel Banjir (R & RC)

-- Hapus tabel gabungan "kecil" yang mungkin tersisa dari percobaan sebelumnya
DROP TABLE IF EXISTS public.model_intensitas_banjir CASCADE;
DROP TABLE IF EXISTS public.dmg_ratio_banjir CASCADE;

-- 1. Gabungkan Tabel Intensitas (Total grid koordinat tetap ~814k)
CREATE TABLE public.model_intensitas_banjir AS
SELECT 
    r.id_lokasi, 
    r.lon, 
    r.lat, 
    r.geom, 
    r.r_25, r.r_50, r.r_100, r.r_250,
    rc.rc_25, rc.rc_50, rc.rc_100, rc.rc_250
FROM public.model_intensitas_banjir_r r
JOIN public.model_intensitas_banjir_rc rc USING(id_lokasi);

ALTER TABLE public.model_intensitas_banjir ADD PRIMARY KEY (id_lokasi);
CREATE INDEX idx_model_intensitas_banjir_geog ON public.model_intensitas_banjir USING gist (((geom)::geography));

-- 2. Gabungkan Tabel Damage Ratio
CREATE TABLE public.dmg_ratio_banjir AS
SELECT 
    r.id_lokasi,
    r.dmgratio_1_r25, r.dmgratio_2_r25,
    r.dmgratio_1_r50, r.dmgratio_2_r50,
    r.dmgratio_1_r100, r.dmgratio_2_r100,
    r.dmgratio_1_r250, r.dmgratio_2_r250,
    rc.dmgratio_1_rc25, rc.dmgratio_2_rc25,
    rc.dmgratio_1_rc50, rc.dmgratio_2_rc50,
    rc.dmgratio_1_rc100, rc.dmgratio_2_rc100,
    rc.dmgratio_1_rc250, rc.dmgratio_2_rc250
FROM public.dmg_ratio_banjir_r r
JOIN public.dmg_ratio_banjir_rc rc USING(id_lokasi);

ALTER TABLE public.dmg_ratio_banjir ADD PRIMARY KEY (id_lokasi);

-- 3. Maintenance Awal
VACUUM ANALYZE public.model_intensitas_banjir;
VACUUM ANALYZE public.dmg_ratio_banjir;


-- SQL untuk Optimasi Database AAL (Supabase) - REVISI

-- 1. Hapus Index Redundan
-- Menggunakan CASCADE dan menghapus prefix public jika perlu (walaupun biasanya tidak pengaruh)
DROP INDEX IF EXISTS idx_model_intensitas_banjir_r_geom CASCADE;
DROP INDEX IF EXISTS idx_model_intensitas_banjir_rc_geom CASCADE;

-- 2. Optimasi Tipe Data (Hanya pada kolom intensitas)
-- Skip lat/lon karena digunakan oleh generated column 'geom'

-- Tabel model_intensitas_banjir_r
ALTER TABLE model_intensitas_banjir_r 
  ALTER COLUMN r_25 TYPE real,
  ALTER COLUMN r_50 TYPE real,
  ALTER COLUMN r_100 TYPE real,
  ALTER COLUMN r_250 TYPE real;

-- Tabel model_intensitas_banjir_rc
ALTER TABLE model_intensitas_banjir_rc 
  ALTER COLUMN rc_25 TYPE real,
  ALTER COLUMN rc_50 TYPE real,
  ALTER COLUMN rc_100 TYPE real,
  ALTER COLUMN rc_250 TYPE real;

-- Catatan: dmg_ratio_banjir_* sudah berhasil diubah ke real pada run pertama.
-- Kita jalankan lagi tidak apa-apa untuk memastikan.

-- Tabel dmg_ratio_banjir_r
ALTER TABLE dmg_ratio_banjir_r 
  ALTER COLUMN dmgratio_1_r25 TYPE real, ALTER COLUMN dmgratio_2_r25 TYPE real,
  ALTER COLUMN dmgratio_1_r50 TYPE real, ALTER COLUMN dmgratio_2_r50 TYPE real,
  ALTER COLUMN dmgratio_1_r100 TYPE real, ALTER COLUMN dmgratio_2_r100 TYPE real,
  ALTER COLUMN dmgratio_1_r250 TYPE real, ALTER COLUMN dmgratio_2_r250 TYPE real;

-- Tabel dmg_ratio_banjir_rc
ALTER TABLE dmg_ratio_banjir_rc 
  ALTER COLUMN dmgratio_1_rc25 TYPE real, ALTER COLUMN dmgratio_2_rc25 TYPE real,
  ALTER COLUMN dmgratio_1_rc50 TYPE real, ALTER COLUMN dmgratio_2_rc50 TYPE real,
  ALTER COLUMN dmgratio_1_rc100 TYPE real, ALTER COLUMN dmgratio_2_rc100 TYPE real,
  ALTER COLUMN dmgratio_1_rc250 TYPE real, ALTER COLUMN dmgratio_2_rc250 TYPE real;

-- 3. Maintenance
VACUUM FULL model_intensitas_banjir_r;
VACUUM FULL model_intensitas_banjir_rc;
VACUUM FULL dmg_ratio_banjir_r;
VACUUM FULL dmg_ratio_banjir_rc;

-- 4. Reindex
REINDEX TABLE model_intensitas_banjir_r;
REINDEX TABLE model_intensitas_banjir_rc;

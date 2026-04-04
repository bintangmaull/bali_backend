import os
import sys
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import psycopg2
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Load env variables explicitly
env_path = r"E:\Dashboard\backend-capstone-aal\conversion\.env"
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Fix PROJ on Windows
proj_path = os.path.join(r"E:\Dashboard\backend-capstone-aal\myenv311", "Lib", "site-packages", "pyproj", "proj_dir", "share", "proj")
if os.path.exists(proj_path):
    os.environ['PROJ_LIB'] = proj_path

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "geotiff-cogs")

DB_HOST = os.getenv("DB_HOST", "aws-1-ap-southeast-1.pooler.supabase.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres.upcxonhddesvrvttvjjt")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_db():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)


def assign_crs_and_convert(src_path: Path):
    print(f"\n[PROCESS] Processing {src_path.name}...")
    dest_name = f"cog_{src_path.name}"
    tmp_crs_path = src_path.parent / f"tmp_crs_{src_path.name}"
    cog_path = src_path.parent / dest_name

    try:
        # Step 1: Assign CRS without reprojection
        print("  Assigning EPSG:4326...")
        with rasterio.open(str(src_path), 'r', ignore_geometry_validity=True) as src:
            kwargs = src.meta.copy()
            # Override CRS to WGS84
            kwargs.update({'crs': 'EPSG:4326'})
            
            with rasterio.open(str(tmp_crs_path), 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    dst.write(src.read(i), i)
        
        # Step 2: Convert to COG
        print("  Converting to COG...")
        prof = cog_profiles.get("lzw")
        with rasterio.open(str(tmp_crs_path)) as src:
            cog_translate(src, str(cog_path), prof, quiet=True)
            
        # Step 3: Upload
        print("  Uploading to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        with open(str(cog_path), 'rb') as f:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                path=dest_name,
                file=f,
                file_options={"content-type": "image/tiff", "upsert": "true"}
            )
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{dest_name}"
        print(f"  Upload OK -> {public_url}")

        # Step 4: DB
        print("  Logging to DB...")
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM raster_metadata WHERE filename = %s", (src_path.name,))
            cur.execute(
                "INSERT INTO raster_metadata (filename, storage_path, public_url) VALUES (%s, %s, %s)",
                (src_path.name, dest_name, public_url)
            )
            conn.commit()
            print("  DB Log OK")
        finally:
            conn.close()

    except Exception as e:
        print(f"  [ERROR] Failed to process {src_path.name}: {e}")
        
    finally:
        # Cleanup
        for tmp_file in [tmp_crs_path, cog_path]:
            if tmp_file.exists():
                try:
                    os.remove(tmp_file)
                    print(f"  Cleaned up {tmp_file.name}")
                except Exception as e:
                    pass

def main():
    sawah_dir = Path(r"E:\Dashboard\Data\Exposure\sawah")
    if not sawah_dir.exists():
        print("[ERROR] Sawah directory not found!")
        sys.exit(1)
        
    files = list(sawah_dir.glob("*.tif")) + list(sawah_dir.glob("*.tiff"))
    files = [f for f in files if not f.name.startswith("cog_") and not f.name.startswith("tmp_crs_")]
    
    print(f"Found {len(files)} files to process.")
    for f in files:
        assign_crs_and_convert(f)
    print("\n[DONE] Finished processing sawah exposures.")

if __name__ == "__main__":
    main()

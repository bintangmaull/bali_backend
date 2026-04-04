import os
import sys
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import psycopg2
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from supabase import create_client, Client
from pathlib import Path

# Add proj logic to prevent errors
proj_path = os.path.join(os.getcwd(), "..", "myenv311", "Lib", "site-packages", "pyproj", "proj_dir", "share", "proj")
if os.path.exists(proj_path):
    os.environ['PROJ_LIB'] = proj_path

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "geotiff-cogs")
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_db():
    return psycopg2.connect(host=DB_HOST,port=DB_PORT,dbname=DB_NAME,user=DB_USER,password=DB_PASSWORD)

def process_sawah():
    sawah_dir = Path(r"E:\Dashboard\Data\Exposure\sawah")
    files = list(sawah_dir.glob("*.tif"))
    for f in files:
        if f.name.startswith("cog_") or f.name.startswith("wgs84_"): continue
        dest_name = f"cog_{f.name}"
        wgs_path = sawah_dir / f"wgs84_{f.name}"
        cog_path = sawah_dir / dest_name

        print(f"Processing {f.name}...")
        
        # 1. Reproject
        with rasterio.open(str(f)) as src:
            transform, width, height = calculate_default_transform(src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({'crs': 'EPSG:4326', 'transform': transform, 'width': width, 'height': height})
            with rasterio.open(str(wgs_path), 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(source=rasterio.band(src, i), destination=rasterio.band(dst, i), src_transform=src.transform, src_crs=src.crs, dst_transform=transform, dst_crs='EPSG:4326', resampling=Resampling.nearest)
        print("  Reprojected")

        # 2. COG
        prof = cog_profiles.get("lzw")
        with rasterio.open(str(wgs_path)) as src:
            cog_translate(src, str(cog_path), prof, quiet=True)
        print("  Converted to COG")

        # 3. Upload
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        with open(str(cog_path), 'rb') as fp:
            supabase.storage.from_(STORAGE_BUCKET).upload(path=dest_name, file=fp, file_options={"content-type": "image/tiff", "upsert": "true"})
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{dest_name}"
        print("  Uploaded")

        # 4. DB log
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM raster_metadata WHERE filename = %s", (f.name,))
        cur.execute("INSERT INTO raster_metadata (filename, storage_path, public_url) VALUES (%s, %s, %s)", (f.name, dest_name, public_url))
        conn.commit()
        conn.close()
        print(f"  Logged to DB")

        if wgs_path.exists(): wgs_path.unlink()

if __name__ == "__main__":
    process_sawah()
    print("ALL DONE")

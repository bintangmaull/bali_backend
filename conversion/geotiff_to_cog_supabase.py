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

# Load environment variables explicitly from backend conversion folder
env_path = r"E:\Dashboard\backend-capstone-aal\conversion\.env"
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Fix PROJ on Windows to avoid conflicts with PostgreSQL/GDAL installations
proj_path = os.path.join(os.getcwd(), "myenv311", "Lib", "site-packages", "pyproj", "proj_dir", "share", "proj")
if os.path.exists(proj_path):
    os.environ['PROJ_LIB'] = proj_path
    print(f"[CONFIG] Set PROJ_LIB to: {proj_path}")

# Supabase Storage Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "geotiff-cogs")

# Supabase Database Configuration
DB_HOST = os.getenv("DB_HOST", "aws-1-ap-southeast-1.pooler.supabase.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres.upcxonhddesvrvttvjjt")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_db_connection():
    """Establish a connection to the Supabase PostgreSQL database."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def ensure_metadata_table():
    """Ensure the raster_metadata table exists in the database."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raster_metadata (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                public_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()

def log_metadata_to_db(filename: str, storage_path: str, public_url: str):
    """Insert file metadata into the database."""
    print(f"[DB] Logging metadata for {filename}...")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO raster_metadata (filename, storage_path, public_url)
            VALUES (%s, %s, %s)
        """, (filename, storage_path, public_url))
        conn.commit()
        cur.close()
    finally:
        conn.close()

def reproject_to_wgs84(src_path: str, tmp_dst_path: str):
    """Reproject a GeoTIFF to EPSG:4326 (WGS 84)."""
    dst_crs = 'EPSG:4326'
    print(f"[REPROJECT] {src_path} -> WGS84...")

    with rasterio.open(src_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(tmp_dst_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
    print(f"[REPROJECT] Done: {tmp_dst_path}")

def convert_to_cog(src_path: str, dst_path: str):
    """Convert a GeoTIFF to a Cloud Optimized GeoTIFF (COG) using rio-cogeo (GDAL)."""
    print(f"[COG] Converting {src_path}...")

    # Define COG profile (using lzw compression for faster browser decoding)
    output_profile = cog_profiles.get("lzw")

    with rasterio.open(src_path) as src:
        cog_translate(
            src,
            dst_path,
            output_profile,
            quiet=True
        )
    print(f"[COG] Done: {dst_path}")

def ensure_storage_bucket():
    """Ensure the Supabase Storage bucket exists."""
    if not SUPABASE_URL or not SUPABASE_KEY or "PASTE_YOUR" in SUPABASE_KEY:
        return

    print(f"[BUCKET] Checking Supabase bucket '{STORAGE_BUCKET}'...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        buckets = supabase.storage.list_buckets()
        exists = any(b.name == STORAGE_BUCKET for b in buckets)

        if not exists:
            print(f"[BUCKET] Creating new bucket: {STORAGE_BUCKET}...")
            supabase.storage.create_bucket(STORAGE_BUCKET, options={"public": True})
            print(f"[BUCKET] Created '{STORAGE_BUCKET}'.")
        else:
            print(f"[BUCKET] Verified '{STORAGE_BUCKET}'.")
    except Exception as e:
        print(f"[WARNING] Could not verify/create bucket: {e}")

def upload_to_supabase(file_path: str, destination_name: str):
    """Upload a file to Supabase Storage and return the public URL on success."""
    if not SUPABASE_URL or not SUPABASE_KEY or "PASTE_YOUR" in SUPABASE_KEY:
        print(f"[SKIP] Missing SUPABASE_SERVICE_ROLE_KEY for {destination_name}.")
        return None

    print(f"[UPLOAD] {file_path} -> '{destination_name}'...")

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        with open(file_path, 'rb') as f:
            response = supabase.storage.from_(STORAGE_BUCKET).upload(
                path=destination_name,
                file=f,
                file_options={"content-type": "image/tiff", "upsert": "true"}
            )

        # Supabase-py 2.x returns the object on success, or raises an exception
        if isinstance(response, dict) and 'error' in response:
            print(f"[ERROR] Upload failed for {destination_name}: {response['error']}")
            return None

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{destination_name}"
        print(f"[UPLOAD] OK: {destination_name}")
        return public_url
    except Exception as e:
        print(f"[ERROR] Upload error for {destination_name}: {e}")
        return None

def process_file(input_path: Path, base_dir: Path | None = None):
    """Process a single GeoTIFF: Reproject -> COG -> Upload -> Log to DB."""
    try:
        # Determine destination name for Supabase (preserving subfolder structure)
        if base_dir:
            relative_path = input_path.relative_to(base_dir)
            destination_name = str(relative_path.with_name(f"cog_{input_path.name}")).replace("\\", "/")
        else:
            destination_name = f"cog_{input_path.name}"

        # Local paths
        cog_path = input_path.with_name(f"cog_{input_path.name}")
        tmp_reprojected = input_path.with_name(f"wgs84_{input_path.name}")

        # 1. Reproject to WGS84
        reproject_to_wgs84(str(input_path), str(tmp_reprojected))

        # 2. Convert reprojected file to COG
        convert_to_cog(str(tmp_reprojected), str(cog_path))

        # 3. Upload to Supabase
        public_url = upload_to_supabase(str(cog_path), destination_name)

        # 4. Log to Database
        if public_url:
            log_metadata_to_db(input_path.name, destination_name, public_url)

        # 5. Clean up temporary files
        if tmp_reprojected.exists():
            os.remove(tmp_reprojected)
            print(f"[CLEANUP] Removed tmp: {tmp_reprojected.name}")

        if cog_path.exists():
            os.remove(cog_path)
            print(f"[CLEANUP] Removed cog: {cog_path.name}")

    except Exception as e:
        print(f"[ERROR] Error processing {input_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python geotiff_to_cog_supabase.py <input_path_or_dir>")
        sys.exit(1)

    raw_path = sys.argv[1]
    input_path = Path(raw_path)

    if not input_path.exists():
        print(f"[ERROR] Path {input_path} not found.")
        sys.exit(1)

    # Prepare Supabase
    try:
        ensure_metadata_table()
        ensure_storage_bucket()
    except Exception as e:
        print(f"[WARNING] Could not verify/create database or storage resources: {e}")

    if input_path.is_dir():
        print(f"[SCAN] Scanning directory: {input_path}")
        files = list(input_path.rglob("*.tif")) + list(input_path.rglob("*.tiff"))
        # Skip already-processed files
        files = [f for f in files if not f.name.startswith("cog_") and not f.name.startswith("wgs84_")]

        print(f"[SCAN] Found {len(files)} files to process.")
        for f in files:
            process_file(f, base_dir=input_path)
    else:
        process_file(input_path)

    print("[DONE] Conversion complete.")

if __name__ == "__main__":
    main()

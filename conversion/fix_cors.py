import os
from supabase import create_client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "geotiff-cogs")

def fix_cors():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return

    print(f"🔧 Connecting to Supabase at {SUPABASE_URL}...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"🌐 Updating CORS rules for bucket '{STORAGE_BUCKET}'...")
    try:
        # Programmatically update bucket to allow CORS from all origins
        # This is useful when the UI menu is hard to find
        supabase.storage.update_bucket(STORAGE_BUCKET, {
            'public': True,
            'cors_rules': [
                {
                    'allowed_origins': ['*', 'http://localhost:8000', 'http://127.0.0.1:8000'],
                    'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'],
                    'allowed_headers': ['Range', 'Content-Type', 'Authorization', 'x-client-info', 'apikey'],
                    'exposed_headers': ['Content-Length', 'Content-Range', 'Content-Type', 'ETag'],
                    'max_age_seconds': 3600
                }
            ]
        })
        print(f"✅ CORS rules successfully updated for '{STORAGE_BUCKET}'!")
        print("💡 Sekarang Anda bisa merefresh halaman test_cog_leaflet.html di browser.")
    except Exception as e:
        print(f"❌ Failed to update CORS: {e}")

if __name__ == "__main__":
    fix_cors()

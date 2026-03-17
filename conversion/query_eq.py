import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('conversion/.env')

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cur = conn.cursor()
cur.execute("SELECT public_url, filename FROM raster_metadata WHERE filename ILIKE '%earthquake%'")
rows = cur.fetchall()
for row in rows:
    print(f"{row[0]}|{row[1]}")
cur.close()
conn.close()

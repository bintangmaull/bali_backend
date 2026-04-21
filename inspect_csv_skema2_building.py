import pandas as pd

file_path = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood7_building_merge.csv"
try:
    df = pd.read_csv(file_path)
    print("Columns:")
    print(list(df.columns))
    print("\nFirst 3 rows:")
    print(df.head(3).to_string())
except Exception as e:
    print(f"Error parsing CSV: {e}")

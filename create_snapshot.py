import glob
import os
import pyarrow.dataset as ds
import pandas as pd

print("Scanning micro-batch files...")
files = glob.glob("data/delta/user_features_gold/**/*.parquet", recursive=True)
if not files:
    files = glob.glob("data/delta/user_features_gold/*.parquet")

print(f"Found {len(files)} micro-batch files. Combining dataset...")

if not files:
    raise FileNotFoundError("No parquet files found in data/delta/user_features_gold!")

# Fast C++ dataset reading via PyArrow
dataset = ds.dataset(files, format="parquet")
df = dataset.to_table().to_pandas()

# Force UTC timezone awareness
df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True)

# Save consolidated snapshot file
os.makedirs("data", exist_ok=True)
output_path = "data/user_features_snapshot.parquet"
df.to_parquet(output_path, index=False)

print(f"Snapshot created successfully at '{output_path}' with {len(df)} rows!")
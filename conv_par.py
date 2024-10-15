import pandas as pd

# Step 1: Load JSON file (without 'lines=True' since it's not newline-delimited)
json_file = 'filtered_pop_lyrics_dataset.json'
df = pd.read_json(json_file)

# Step 2: Convert to Parquet
parquet_file = 'poplyric-1k.parquet'
df.to_parquet(parquet_file)

print("Conversion successful!")

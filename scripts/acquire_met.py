
import requests
import pandas as pd
import hashlib
from pathlib import Path

url = (
    "https://media.githubusercontent.com/media/"
    "metmuseum/openaccess/master/MetObjects.csv"
)

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

output_path = raw_dir / "met_artworks.csv"

# Download the dataset
response = requests.get(url, stream=True, timeout=120)
response.raise_for_status()

with open(output_path, "wb") as file:
    for chunk in response.iter_content(chunk_size=8192):
        file.write(chunk)

# Calculate SHA-256 checksum
sha256 = hashlib.sha256()

with open(output_path, "rb") as file:
    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)

checksum = sha256.hexdigest()

# Save checksum
with open(raw_dir / "met_sha256.txt", "w") as file:
    file.write(checksum + "\n")

# Load and inspect the dataset
df = pd.read_csv(output_path, low_memory=False)

print("Met dataset downloaded successfully!")
print("Dataset shape:", df.shape)
print("SHA-256:", checksum)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

columns = [
    "Object ID",
    "Title",
    "Artist Display Name",
    "Artist Nationality",
    "Artist Begin Date",
    "Artist End Date",
    "Artist Wikidata URL",
    "Object Begin Date",
    "Object End Date",
    "Classification"
]

print(df[columns].head(10))

print("\nMissing values:")
print(df[columns].isna().sum())

print("\nUnique artist names:")
print(df["Artist Display Name"].nunique())

print("\nRecords with Wikidata URLs:")
print(df["Artist Wikidata URL"].notna().sum())
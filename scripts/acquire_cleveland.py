
import requests
import json
import hashlib
from pathlib import Path

url = (
    "https://media.githubusercontent.com/media/"
    "ClevelandMuseumArt/openaccess/master/data.json"
)

raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)

output_path = raw_dir / "cleveland_artworks.json"
temp_path = raw_dir / "cleveland_artworks.json.tmp"

print("Downloading Cleveland Museum dataset...")

# Download the full dataset
response = requests.get(url, stream=True, timeout=120)
response.raise_for_status()

with open(temp_path, "wb") as file:
    for chunk in response.iter_content(chunk_size=8192):
        file.write(chunk)

# Load and validate JSON
with open(temp_path, "r", encoding="utf-8") as file:
    data = json.load(file)

if isinstance(data, dict):
    artworks = data.get("data", [])
else:
    artworks = data

if not isinstance(artworks, list) or not artworks:
    raise ValueError("No valid artwork records found")

# Check for duplicate IDs
ids = [artwork["id"] for artwork in artworks]

if len(ids) != len(set(ids)):
    raise ValueError("Duplicate artwork IDs detected")

# Save validated download
temp_path.replace(output_path)

# Generate SHA-256 checksum
sha256 = hashlib.sha256()

with open(output_path, "rb") as file:
    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)

checksum = sha256.hexdigest()

with open(raw_dir / "cleveland_sha256.txt", "w") as file:
    file.write(checksum + "\n")

# Display results
print("\nCleveland dataset downloaded successfully!")
print("Total artworks:", len(artworks))
print("Unique artwork IDs:", len(set(ids)))
print("SHA-256:", checksum)

print("\nAvailable fields:")
print(list(artworks[0].keys()))

print("\nSample creator information:")
for artwork in artworks:
    if artwork.get("creators"):
        print(json.dumps(artwork["creators"], indent=2))
        break

print("\nArtworks with creator information:")
print(sum(bool(a.get("creators")) for a in artworks))

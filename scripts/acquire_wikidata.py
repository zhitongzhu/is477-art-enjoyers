
import requests
import pandas as pd
import json
import hashlib
import re
import time
from pathlib import Path

raw_dir = Path("data/raw")

met_path = raw_dir / "met_artworks.csv"
output_path = raw_dir / "wikidata_artists.json"

url = "https://query.wikidata.org/sparql"

met = pd.read_csv(
    met_path,
    usecols=["Artist Wikidata URL"],
    low_memory=False
)

qids = set()

for value in met["Artist Wikidata URL"].dropna():
    ids = re.findall(r"Q[1-9]\d*", str(value))
    qids.update(ids)

qids = sorted(qids)

print("Unique Wikidata IDs found:", len(qids))

if not qids:
    raise ValueError("No Wikidata IDs found")

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "IS477ArtEnjoyers/1.0 "
        "(https://github.com/zhitongzhu/is477-art-enjoyers)"
    ),
    "Accept": "application/sparql-results+json"
})

batch_size = 100
all_results = []

for i in range(0, len(qids), batch_size):

    batch = qids[i:i + batch_size]

    values = " ".join(f"wd:{qid}" for qid in batch)

    query = f"""
    SELECT DISTINCT ?artist ?artistLabel
           ?birthDate ?deathDate
           ?country ?countryLabel
    WHERE {{
        VALUES ?artist {{ {values} }}

        ?artist wdt:P31 wd:Q5.

        OPTIONAL {{ ?artist wdt:P569 ?birthDate. }}
        OPTIONAL {{ ?artist wdt:P570 ?deathDate. }}
        OPTIONAL {{ ?artist wdt:P27 ?country. }}

        SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "en".
        }}
    }}
    """


    for attempt in range(5):
        try:
            response = session.get(
                url,
                params={
                    "query": query,
                    "format": "json"
                },
                timeout=90
            )

            response.raise_for_status()
            result = response.json()
            break

        except (requests.RequestException, ValueError):
            if attempt == 4:
                raise

            wait = 10 * (attempt + 1)
            print(f"Request failed. Retrying in {wait}s")
            time.sleep(wait)

    records = result["results"]["bindings"]
    all_results.extend(records)

    print(
        f"Queried {min(i + batch_size, len(qids))}"
        f"/{len(qids)} artist IDs"
    )

    time.sleep(2)

if not all_results:
    raise ValueError("No Wikidata records retrieved")


with open(output_path, "w", encoding="utf-8") as file:
    json.dump(all_results, file, ensure_ascii=False, indent=2)

sha256 = hashlib.sha256()

with open(output_path, "rb") as file:
    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)

checksum = sha256.hexdigest()

with open(raw_dir / "wikidata_sha256.txt", "w") as file:
    file.write(checksum + "\n")


unique_artists = {
    row["artist"]["value"]
    for row in all_results
}

print("\nWikidata dataset downloaded successfully!")
print("Artist IDs queried:", len(qids))
print("Unique artists retrieved:", len(unique_artists))
print("Total result rows:", len(all_results))
print("SHA-256:", checksum)

print("\nSample record:")
print(json.dumps(all_results[0], indent=2))

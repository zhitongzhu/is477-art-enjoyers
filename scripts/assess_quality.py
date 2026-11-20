import csv
import json
import re
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

RAW = Path("data/raw")
RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

rows = []

def record(dataset, dimension, metric, value, notes=""):
    rows.append({
        "dataset": dataset,
        "dimension": dimension,
        "metric": metric,
        "value": value,
        "notes": notes
    })

# METROPOLITAN MUSEUM
met_path = RAW / "met_artworks.csv"

if met_path.exists():
    total = 0
    missing_artist = 0
    missing_nationality = 0
    missing_wikidata = 0
    duplicate_ids = 0
    invalid_dates = 0
    ids = set()

    for chunk in pd.read_csv(
        met_path, chunksize=10000, low_memory=False,
        dtype=str, keep_default_na=False
    ):
        total += len(chunk)

        def missing(col):
            if col not in chunk.columns:
                return pd.Series(True, index=chunk.index)
            return chunk[col].str.strip().eq("")

        missing_artist += missing("Artist Display Name").sum()
        missing_nationality += missing("Artist Nationality").sum()
        missing_wikidata += missing("Artist Wikidata URL").sum()

        if "Object ID" in chunk:
            for value in chunk["Object ID"]:
                if value in ids:
                    duplicate_ids += 1
                ids.add(value)

        for col in ["Artist Begin Date", "Artist End Date"]:
            if col in chunk:
                values = pd.to_numeric(chunk[col], errors="coerce")
                invalid_dates += (
                    chunk[col].str.strip().ne("")
                    & (values.isna() | (values < -5000) | (values > 2026))
                ).sum()

    record("Met", "completeness", "total_artworks", total)
    record("Met", "completeness", "missing_artist_names", int(missing_artist))
    record("Met", "completeness", "missing_nationalities", int(missing_nationality))
    record("Met", "completeness", "missing_wikidata_urls", int(missing_wikidata))
    record("Met", "consistency", "duplicate_object_ids", duplicate_ids)
    record("Met", "accuracy", "unparseable_or_implausible_artist_dates", int(invalid_dates),
           "Automated plausibility check, not external fact verification")
    record("Met", "timeliness", "assessment_date",
           datetime.now(timezone.utc).date().isoformat(),
           "Assessment date is not the source's last update date")
else:
    print("Met dataset not found; skipping.")

# CLEVELAND MUSEUM
cle_path = RAW / "cleveland_artworks.json"

if cle_path.exists():
    with open(cle_path, encoding="utf-8") as f:
        obj = json.load(f)

    if isinstance(obj, list):
        artworks = obj
    elif isinstance(obj, dict):
        artworks = next(
            (obj[k] for k in ["data", "artworks", "results"]
             if isinstance(obj.get(k), list)),
            []
        )
    else:
        artworks = []

    total = len(artworks)
    missing_creators = 0
    duplicate_ids = 0
    ids = set()

    for artwork in artworks:
        if not isinstance(artwork, dict):
            continue
        if not artwork.get("creators"):
            missing_creators += 1
        artwork_id = artwork.get("id")
        if artwork_id is not None:
            if artwork_id in ids:
                duplicate_ids += 1
            ids.add(artwork_id)

    record("Cleveland", "completeness", "total_artworks", total)
    record("Cleveland", "completeness", "artworks_without_creators", missing_creators)
    record("Cleveland", "consistency", "duplicate_artwork_ids", duplicate_ids)
    record("Cleveland", "timeliness", "assessment_date",
           datetime.now(timezone.utc).date().isoformat(),
           "Source update date not independently verified")
else:
    print("Cleveland dataset not found; skipping.")

# WIKIDATA
wiki_path = RAW / "wikidata_artists.json"

if wiki_path.exists():
    with open(wiki_path, encoding="utf-8") as f:
        obj = json.load(f)

    if isinstance(obj, dict):
        bindings = obj.get("results", {}).get("bindings", [])
    elif isinstance(obj, list):
        bindings = obj
    else:
        bindings = []

    record("Wikidata", "completeness", "total_binding_rows", len(bindings))

    if bindings:
        fields = set().union(
            *(row.keys() for row in bindings if isinstance(row, dict))
        )
        for field in sorted(fields):
            missing_count = sum(
                not row.get(field) or
                (isinstance(row.get(field), dict)
                 and not row[field].get("value"))
                for row in bindings
            )
            record("Wikidata", "completeness",
                   f"missing_{field}", missing_count)

        record("Wikidata", "consistency", "exact_duplicate_binding_rows",
               len(bindings) - len({
                   json.dumps(row, sort_keys=True) for row in bindings
               }),
               "Repeated artist IDs may be legitimate due to multiple properties")

    record("Wikidata", "timeliness", "assessment_date",
           datetime.now(timezone.utc).date().isoformat(),
           "Query retrieval timestamp not independently verified")
else:
    print("Wikidata dataset not found; skipping.")

output = RESULTS / "preliminary_quality.csv"
pd.DataFrame(rows).to_csv(output, index=False)

print(f"\nSaved {len(rows)} assessment metrics to {output}")
print(pd.DataFrame(rows).to_string(index=False))

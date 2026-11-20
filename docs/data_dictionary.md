
# Data Dictionary

## 1. Project Overview

This project investigates artist representation across the
Metropolitan Museum of Art and Cleveland Museum of Art
collections by integrating artwork records with artist
biographical information from Wikidata.

The data dictionary documents the source datasets,
relevant attributes, and planned integration procedures.

## 2. Source Datasets

| Dataset | Format | Records | Approximate Size |
|---|---|---:|---:|
| Metropolitan Museum of Art | CSV | 503,378 | 325 MB |
| Cleveland Museum of Art | JSON | 68,819 | 330 MB |
| Wikidata | JSON | To be verified | 17 MB |

The original datasets are stored in `data/raw/`.

## 3. Metropolitan Museum of Art

**File:** `data/raw/met_artworks.csv`

| Attribute | Description |
|---|---|
| Object ID | Unique identifier for an artwork |
| Title | Artwork title |
| Artist Display Name | Artist name as recorded by the museum |
| Artist Nationality | Nationality information associated with the artist |
| Artist Begin Date | Beginning year associated with the artist |
| Artist End Date | Ending year associated with the artist |
| Artist Wikidata URL | Link to the artist's Wikidata entity |
| Object Begin Date | Beginning year associated with the artwork |
| Object End Date | Ending year associated with the artwork |
| Classification | Museum artwork classification |

These attributes are referenced in the existing
Met acquisition script.

## 4. Cleveland Museum of Art

**File:** `data/raw/cleveland_artworks.json`

The acquisition script indicates that artwork records
contain an `id` field and may contain a `creators` field.

| Attribute | Description |
|---|---|
| id | Artwork identifier |
| creators | Creator information associated with an artwork |

Additional attributes and nested JSON structures
will be documented after schema inspection.

## 5. Wikidata

**File:** `data/raw/wikidata_artists.json`

Artist information is retrieved using SPARQL queries.

The acquisition script extracts Wikidata identifiers
from the Met dataset's `Artist Wikidata URL` field.

The retrieved information is intended to supplement
artist biographical attributes.

The exact JSON schema and attribute definitions
will be documented after inspection.

## 6. Data Integration

The planned integration process will combine museum
artwork records with artist biographical information.

Potential matching approaches include:

- Matching available Wikidata identifiers
- Standardizing artist names
- Comparing relevant biographical attributes
- Identifying possible duplicate artist records

Final matching rules will be confirmed with the
team member responsible for data integration.

## 7. Data Quality

The project plans to evaluate:

- Completeness
- Accuracy
- Consistency
- Timeliness

Pre-integration and post-integration quality
assessment results will be documented when available.

## 8. Data Integrity

The project uses SHA-256 checksums to detect changes
to source dataset files.

Current verification results:

| Dataset | Status |
|---|---|
| Met | Verified |
| Cleveland | Verified |
| Wikidata | Checksum mismatch under investigation |

The Wikidata mismatch was detected during preliminary
workflow testing. No source files or checksum values
have been modified to resolve the discrepancy.

## 9. Future Updates

This dictionary will be expanded to include:

- Complete source schemas
- Attribute data types
- Missing-value statistics
- Standardized attribute definitions
- Integrated dataset schema
- Data provenance and machine-readable metadata

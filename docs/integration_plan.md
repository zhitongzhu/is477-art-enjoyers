# Data Integration and Record Linkage: Preliminary Plan and Results

**Status:** preliminary (interim report, 2026-11-19).
**Script:** `scripts/integrate.py`
**Input:** the **raw** files in `data/raw/`. The final run will use Bernice's cleaned files (see section 6).
Raw files are only read and never modified. All checksums matched before the run (see section 1).

```bash
python scripts/integrate.py                         # full run (~1.5 min)
python scripts/integrate.py --sample-cleveland 300  # quick sample test
```

---

## 1. Inputs and integrity

| File | Records | SHA-256 matches `*_sha256.txt` |
|---|---|---|
| `data/raw/met_artworks.csv` | 503,378 artworks | yes |
| `data/raw/cleveland_artworks.json` | 68,819 artworks (JSON list) | yes |
| `data/raw/wikidata_artists.json` | 25,679 SPARQL bindings → 19,665 QIDs | yes |

## 2. What the data actually looks like (exploration findings)

**Met (`met_artworks.csv`)**
- 303,658 artworks have at least one named creator. Several creators share one row as `|`-separated values (104,526 rows). Role, name, nationality, dates and Wikidata URL always have the same number of segments, so they can be split by position (0 misaligned rows).
- **`Constituent ID` cannot be used as an artist key.**
  - In multi-creator rows the IDs are concatenated with no delimiter (e.g. object 35, Paulding Farnham | Tiffany & Co. → `108316253`).
  - Even in single-creator rows, 10,295 distinct IDs cover 29,266 distinct names. For example, ID `10003` appears on "Anonymous, American, 18th century", "Hatch & Co." and "William Endicott".
  - Decision: key Met artists on the **Wikidata QID** when present. Otherwise use the **normalized name + begin year + end year**.
- `Artist End Date = 9999` means living/active, so it is treated as missing.
- Dates are padded with spaces (`"1859      "`), and the file begins with a UTF-8 BOM.

**Cleveland (`cleveland_artworks.json`)**
- 48,692 of 68,819 artworks have `creators`; there are 57,045 creator links and 9,135 distinct creator IDs.
- Creator IDs are stable: only 44 IDs have more than one description, and those differ mostly in punctuation (`–` vs `-`).
- `qualifier` sits on the artwork-creator link (`after`, `attributed to`, `circle of`, `workshop of`, …). It describes the attribution, not the person, so it is kept on the link and never used for matching.
- Name and nationality are parsed from `description` (`"Camille Pissarro (French, 1830–1903)"`). Years come from the structured `birth_year` / `death_year` fields.
  - 102 creators have a description year that disagrees with the structured field. Example: "Kuncan (Chinese, 1612–c. 1673)" has `death_year = 1678`.
- The artwork-level Wikidata URL (`external_resources.wikidata`) identifies the **artwork**, so it is not used for artists.

**Wikidata (`wikidata_artists.json`)**
- Raw SPARQL bindings contain one row per artist × date × citizenship. They collapse to 19,665 QIDs.
- 2,462 artists have more than one citizenship. These are kept in **one row** as a `"; "` list so a join can never multiply artwork counts.
- 808 artists have several distinct birth years and 446 have several death years. In those cases the single value is left blank and every value is kept.
- 823 QIDs have no English label. Some dates are "unknown value" blank nodes (`…/.well-known/genid/…`), which become missing. BCE years are negative.
- Coverage is limited to QIDs found in the Met. `acquire_wikidata.py` also keeps only humans (`P31 = Q5`).

## 3. Integration schema

```
                         ┌──────────────────────────┐
                         │ wikidata_artist (1 / QID)│
                         │ qid PK, label, birth,    │
                         │ death, countries ("; ")  │
                         └────────────▲─────────────┘
                                      │ qid (many-to-one)
       ┌──────────────────────────────┴─────────────────────────────┐
       │                    unified_artist_id                         │
       │  wd:Q…  (QID known)  |  met:<name>|<birth>|<death>  |  cle:<id>│
       └───────▲───────────────────────────────────────────▲────────┘
               │ met_artist_key                             │ match (cleveland_matches.csv)
   ┌───────────┴────────────┐                  ┌────────────┴───────────┐
   │ met_artwork_artist     │                  │ cle_artwork_creator    │
   │ artwork_id, position,  │                  │ artwork_id, creator_id,│
   │ role, name, dates, qid │                  │ role, qualifier, dates │
   └───────────▲────────────┘                  └────────────▲───────────┘
               │                                            │
         Met artwork (Object ID)                Cleveland artwork (id)
```

Integrated output (`data/integrated/artwork_artist_integrated.csv`, git-ignored, 85 MB) has **one row per museum × artwork × creator**:
`museum, artwork_id, position, n_creators_on_artwork, role, qualifier, artist_name, local_artist_id, unified_artist_id, match_status, qid, nationality_museum, birth_year_museum, death_year_museum, object_begin_date, object_end_date, wd_label, birth_year_wd, death_year_wd, wd_countries, birth_year, death_year`

`birth_year` / `death_year` hold the museum value, with Wikidata filling the gaps. Artwork counts must be computed as `nunique(artwork_id)` per `unified_artist_id`, never as row counts. A 2,000-row sample is committed as `results/preliminary/integrated_sample_2000.csv`.

**Guard against inflated counts.** Every join is `validate="many_to_one"`, and the script asserts the row count is unchanged after the Wikidata join. Result: 479,195 Met + 57,045 Cleveland = 536,240 rows, both before and after.

## 4. Matching rules

**Met → Wikidata (identifier link).** The QID is extracted from `Artist Wikidata URL`. Years are then compared with ± 2 years tolerance.
- `confirmed_qid`: dates agree or one side is missing.
- `confirmed_qid_date_conflict`: the link stands because the identifier is authoritative, but the disagreement is flagged.
- `qid_not_in_wikidata_file`: the QID is absent from the Wikidata pull.

**Cleveland → Met/Wikidata (no shared identifier).**
1. *Blocking:* exact equality of a normalized name variant. Normalization lower-cases, strips accents and punctuation, and turns `&` into `and`. Variants also include the Latin-only part (`Kano Motonobu 狩野元信` → `kano motonobu`), the text inside and outside parentheses, and Wikidata labels.
2. *Evidence per candidate:* birth and death year, ± 2 years.
   - **strong:** name + birth agree, and death agrees (or both sides have no death year).
   - **conflict:** a known year disagrees.
   - **weak:** not enough dates.
3. *Decision per Cleveland creator:*

| Status | Rule |
|---|---|
| `confirmed` | exactly one strong candidate; **or** several strong candidates that all point to ≤ 1 QID (Met-side duplicate records of the same person → the QID record is chosen) |
| `ambiguous` | only weak or conflict candidates, or strong candidates with different QIDs → **manual review, never auto-merged** |
| `unmatched` | no Met/Wikidata record shares a name |
| `excluded_anonymous` | "Unknown", "Anonymous", "Unidentified" … |

An identical name on its own **never** produces a confirmed match.

## 5. Preliminary results (full raw data, tolerance ± 2, run 2026-11-19)

**Met → Wikidata.** 20,137 distinct QIDs:
- 17,351 `confirmed_qid`
- 2,314 `confirmed_qid_date_conflict` (e.g. Charles Cromwell Ingham: Met 1786, Wikidata 1796)
- 472 `qid_not_in_wikidata_file`, mostly firms, workshops and conventional names (Vincennes Manufactory, Taller de Gráfica Popular, Amykos Painter). A few are people (e.g. Liang Kai Q45403177), possibly redirected QIDs → check with Jared.

64.3% of named Met creator mentions carry a QID (296,576 / 461,558). 42,338 Met artist keys have no QID.

**Cleveland → Met/Wikidata** (9,135 creator IDs):

| Status | Creators | Detail |
|---|---|---|
| confirmed | 3,358 | 3,276 clean; 72 with other same-name candidates rejected; 10 resolved Met-side duplicates |
| ambiguous | 905 | 613 same name / insufficient dates; 292 same name / year disagrees |
| unmatched | 4,862 | no name match (mostly Cleveland-only artists or spelling differences) |
| excluded | 10 | anonymous |

- The 3,358 confirmed creator IDs map to **3,304 distinct people** in both museums (3,065 with a QID).
- 107 Cleveland creator IDs share a confirmed person with another ID (53 people), which points to **likely duplicate creator records in Cleveland**. Examples: John Singer Sargent `2559` / `287402`, James Barry `26891` / `291834`. File: `cleveland_possible_duplicate_creators.csv`.
- Largest shared artists by Cleveland count (Cleveland / Met artworks): Edward Sheriff Curtis 785 / 153, John Taylor Arms 517 / 100, Larry Fink 505 / 7, Winslow Homer 380 / 318, James McNeill Whistler 302 / 618.

**Completeness before → after Wikidata (distinct artists):**

| | Met | Cleveland |
|---|---|---|
| birth year | 75.8% → 76.5% | 76.0% → 76.0% |
| death year | 69.7% → 70.5% | 61.6% → 61.6% |
| citizenship from Wikidata | 27.6% | 32.0% |

Cleveland gains no birth or death years. A confirmed match already *requires* agreeing years, so Wikidata can only add years to Cleveland artists after the coverage expansion in section 7.

**Spot check.** I hand-checked a 25-record sample of confirmed matches (seed 477). All 25 were plausibly the same person (e.g. Egon Schiele 1890–1918, Louise Bourgeois 1911–2010, George Stubbs 1724–1806). A fresh 25 confirmed + 25 ambiguous review sheet with blank verdict columns is in `manual_review_sample.csv` for the team. This is a sanity check, not a precision estimate.

## 6. Expected structure of the cleaned datasets (for Bernice)

The final run should pass `--met`, `--cleveland`, `--wikidata` pointing at cleaned files. To keep the matching code unchanged, the cleaned files should:

1. **Keep the original identifiers untouched:** Met `Object ID`, Cleveland artwork `id` and creator `id`, Wikidata QIDs.
2. **Keep one creator per position.** Either keep the Met `|` structure, or provide a long table `artwork_id, position, role, name, nationality, begin_year, end_year, qid`. Please don't drop secondary creators.
3. **Not rely on Met `Constituent ID`** (see section 2). Flag it as a known quality issue.
4. **Years as integers** (BCE negative). Met `9999` → missing. Keep the original value in a separate column if it changes.
5. **Not merge duplicate Cleveland creators** in cleaning. Flag them instead (`cleveland_possible_duplicate_creators.csv`) and let integration resolve them via `unified_artist_id`.
6. **Keep Wikidata multi-valued fields** (several citizenships or birth dates) as lists or flags, not extra artist rows.
7. **Keep Cleveland `qualifier`** on the artwork-creator link.
8. Use names as published. Integration does its own normalization, so please don't overwrite display names.

If the cleaned format differs, only the `load_*` functions in `integrate.py` need to change.

## 7. Open challenges / next steps

- **Wikidata coverage for Cleveland-only artists.** 4,862 Cleveland creators are unmatched because the Wikidata pull was seeded from Met QIDs. Proposal for Jared: query Wikidata by label + birth year for unmatched Cleveland creators, then re-run the same rules.
- **Met-side duplicates.** No-QID Met keys can duplicate QID records (spelling or script variants). These need consolidating before nationality counts (RQ1).
- **Date conflicts.** Decide whether ± 2 years is right. Some Met dates look like active years rather than life dates (e.g. Edward Ancourt 1872–1895).
- **Ambiguous review.** The 292 "year disagrees" cases include clear same-person data errors (Walt Kuhn 1877 vs 1880; Roman Vishniac death 1990 vs 1997). Manual review rules are needed.
- **Nationality vocabulary.** Museum nationality ("American") differs from Wikidata citizenship ("United States"). A mapping is needed for RQ1/RQ2.
- Re-run on cleaned data and compare counts with this preliminary run.

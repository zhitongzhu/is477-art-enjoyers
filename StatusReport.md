## Data Acquisition and Storage

The initial data acquisition stage has been completed for all three data sources. Python scripts were developed to automate the retrieval of artwork records from the Metropolitan Museum of Art and Cleveland Museum of Art, as well as artist biographical information from Wikidata.

Metropolian Museum of Art has 503,378 records, is in CSV format, and is 325 MB. Cleveland Musem of Art has 68,819 records, is in JSON format, and is 330 MB. Wikidata has the artists biographical records, is in JSON and is 17 MB.

The Metropolitan Museum of Art dataset was acquired using its official bulk CSV download through acquire_met.py. The dataset contains 54 attributes, including artist names, nationalities, birth and death dates, and Wikidata identifiers.

The Cleveland Museum of Art dataset was acquired through acquire_cleveland.py. Preliminary inspection confirmed that all 68,819 artwork IDs are unique and that 48,692 artwork records contain creator information.

The Wikidata dataset was acquired through acquire_wikidata.py, which extracts unique artist Wikidata identifiers from the Met dataset and submits SPARQL queries in batches. The retrieved information includes artist names, birth dates, death dates, and countries of citizenship.

SHA-256 checksums were generated for all three datasets to support data integrity verification. The museum datasets are stored in our shared Box folder because they exceed the course's GitHub file size limit. The Wikidata dataset is stored directly in the repository.

### Changes to the Original Project Plan and Challenges
Our original project plan proposed retrieving both museum datasets through their REST APIs. However, during the Cleveland Museum acquisition process, we encountered duplicate artwork identifiers after retrieving approximately 5,500 records through pagination.

To address this issue, we switched to the museum's official bulk JSON dataset. We also used the Metropolitan Museum of Art's official bulk CSV download rather than making individual API requests. These changes simplified the acquisition process and reduced the number of API requests needed.

Another limitation is that our initial Wikidata dataset only includes artists whose identifiers were extracted from the Met dataset. Additional Wikidata acquisition may be necessary to improve coverage of artists represented exclusively in Cleveland.

### Individual Contribution - Jared
I finished collecting all three datasets, created reusable Python download scripts, generated SHA-256 checksums, and set up a consistent directory structure for storing all raw data files. I also prepared the Python environment, listed package dependencies in requirements.txt, and added a .gitignore file to keep oversized datasets from being committed to GitHub.I addressed problems encountered during Cleveland Museum API pagination and established shared Box storage so that my teammates can access identical dataset snapshots whenever needed. My remaining tasks involve broadening Wikidata coverage, implementing automated integrity checks and Box retrieval, and finishing the data-source documentation.

### Individual Contribution - Bernice
I began developing a Python script that helps us to evaluate the accuracy, completeness, consistency, and timeliness of the datasets. This will focus on any missing artist information, inconsistencies in the date format, duplicated records, and other errors in the biographical information. Our findings will be used to determine the next step in terms of cleaning the datasets and standardizing them for integration. My next steps will include completing the preliminary assessment and documenting those results and also collaborating with my team members to work on the data integration and make sure our artist-matching fields are consistent.


### Data Integration and Record Linkage - Zhitong

**Work completed (branch `data-integration`)**

- Verified that all three datasets matched the committed SHA-256 checksums before use.
- Explored the structure of all three sources (`docs/integration_plan.md` §2), with three key findings:
  - The Met's `Constituent ID` is not a usable artist key. It is concatenated without a delimiter for multi-creator artworks, and the same ID is reused for different names (10,295 IDs across 29,266 names in single-creator rows).
  - Cleveland creator IDs are museum-specific, but stable.
  - Wikidata bindings repeat artists once per citizenship and date value.
- Designed a preliminary integration schema (§3):
  - artists are keyed on a `unified_artist_id` (Wikidata QID when known);
  - artwork-creator link tables are kept per museum;
  - all joins are many-to-one with row-count assertions, so multiple citizenships cannot inflate artwork counts.
- Wrote `scripts/integrate.py`:
  - Met → Wikidata linkage by QID with a date check;
  - Cleveland → Met/Wikidata matching by normalized name, with birth and death years (± 2) as evidence;
  - every Cleveland creator classified as confirmed / ambiguous / unmatched / excluded. An identical name alone never confirms a match.
- Ran it on the full **raw** data as a preliminary test. The final run will use the cleaned datasets.

**Preliminary results** (`results/preliminary/`)

- Met: 20,137 artist QIDs. 17,351 are consistent with Wikidata, 2,314 linked but with date conflicts, and 472 are absent from the Wikidata pull (mostly firms and workshops).
- Cleveland (9,135 creators):
  - 3,358 confirmed (3,304 distinct people found in both museums);
  - 905 ambiguous (kept for manual review);
  - 4,862 unmatched;
  - 10 anonymous.
- Wikidata adds citizenship for 27.6% of Met and 32.0% of Cleveland artists. It raises Met birth-year completeness only slightly (75.8% → 76.5%).
- 53 people appear under two Cleveland creator IDs (likely duplicate records), flagged for cleaning.
- Spot check: all 25 sampled confirmed matches were correct.

**Challenges / next steps**

- Expand Wikidata coverage to Cleveland-only artists (with Jared).
- Agree on the cleaned-data structure (`docs/integration_plan.md` §6, with Bernice) and re-run on cleaned data.
- Consolidate Met duplicate artist records.
- Set manual-review rules for ambiguous matches.
- Map museum nationalities to Wikidata citizenship for the analysis.

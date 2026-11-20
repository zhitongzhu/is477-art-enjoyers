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

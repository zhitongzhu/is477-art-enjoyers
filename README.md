# is477-art-enjoyers

## Workflow Automation

The project uses `run_all.py` to coordinate data acquisition and integrity verification.

### Environment Setup

Create a Python virtual environment and install the required dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Dataset Setup

The project uses three datasets:

- Metropolitan Museum of Art (`met_artworks.csv`)
- Cleveland Museum of Art (`cleveland_artworks.json`)
- Wikidata (`wikidata_artists.json`)

The Met and Cleveland datasets are stored in the team's Box folder and must be placed in `data/raw/`.

Large raw datasets should not be committed to GitHub.

### Running the Workflow

From the repository root, run:

```powershell
python run_all.py
```

The preliminary workflow:

1. Checks whether datasets already exist.
2. Avoids unnecessary downloads.
3. Verifies SHA-256 checksums.
4. Executes acquisition scripts when appropriate.
5. Stops execution if a validation or script error occurs.

### Current Development Status

The preliminary acquisition orchestration and checksum verification have been implemented.

During testing, the Met and Cleveland datasets passed SHA-256 verification. A checksum mismatch was detected for the Wikidata dataset and is being investigated.

Data cleaning, integration, post-integration quality assessment, analysis, and visualization have not yet been connected to the orchestrator.

See [Workflow Diagram](docs/workflow.md) for the planned pipeline.

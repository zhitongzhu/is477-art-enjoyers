### Tongxin Yang — Workflow Automation and Documentation

For Milestone 3, I developed a preliminary `run_all.py` workflow orchestrator to coordinate data acquisition and integrity verification. The script checks whether datasets already exist, avoids unnecessary downloads, verifies SHA-256 checksums, and handles execution errors. It also respects the dependency between the Met and Wikidata acquisition scripts.

During testing, the Met and Cleveland datasets passed checksum verification. However, the Wikidata dataset failed verification because its calculated SHA-256 value did not match the recorded checksum. I identified this issue and contacted Jared to confirm the correct dataset snapshot.

I also created a workflow diagram illustrating the planned stages of acquisition, integrity verification, quality assessment, cleaning, integration, and analysis. Additionally, I updated `README.md` with environment setup and workflow execution instructions and created `docs/data_dictionary.md` to document the source datasets, relevant attributes, and planned integration procedures.

The downstream workflow stages are not yet implemented. My next steps are to coordinate script interfaces with Bernice and Zhitong, connect their completed scripts, and develop the analysis and visualization components.

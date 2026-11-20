
from pathlib import Path
import argparse
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"

DATASETS = [
    {
        "name": "Met",
        "script": "scripts/acquire_met.py",
        "data": "met_artworks.csv",
        "checksum": "met_sha256.txt",
    },
    {
        "name": "Cleveland",
        "script": "scripts/acquire_cleveland.py",
        "data": "cleveland_artworks.json",
        "checksum": "cleveland_sha256.txt",
    },
    {
        "name": "Wikidata",
        "script": "scripts/acquire_wikidata.py",
        "data": "wikidata_artists.json",
        "checksum": "wikidata_sha256.txt",
    },
]


def verify_checksum(data_path, checksum_path):
    expected = checksum_path.read_text(
        encoding="utf-8"
    ).strip().lower()

    if len(expected) != 64:
        raise ValueError(
            f"Invalid SHA-256 checksum: {checksum_path.name}"
        )

    sha256 = hashlib.sha256()

    with data_path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            sha256.update(chunk)

    actual = sha256.hexdigest()

    if actual != expected:
        raise ValueError(
            f"Checksum mismatch: {data_path.name}"
        )

    print(f"[VERIFIED] {data_path.name}")


def acquire_dataset(dataset):
    name = dataset["name"]
    data_path = RAW_DIR / dataset["data"]
    checksum_path = RAW_DIR / dataset["checksum"]

    if data_path.is_file():
        if not checksum_path.is_file():
            raise FileNotFoundError(
                f"Missing checksum for {name}"
            )

        verify_checksum(data_path, checksum_path)
        print(f"[SKIPPED] {name}: existing snapshot")
        return

    if checksum_path.is_file():
        raise FileNotFoundError(
            f"{name} data is missing, but its checksum "
            "exists. Restore the matching snapshot "
            "rather than downloading a different version."
        )

    script = ROOT / dataset["script"]

    if not script.is_file():
        raise FileNotFoundError(
            f"Missing acquisition script: {script}"
        )

    print(f"[RUNNING] {name} acquisition", flush=True)

    subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=True,
    )

    if not data_path.is_file():
        raise RuntimeError(
            f"Expected output missing: {data_path.name}"
        )

    if not checksum_path.is_file():
        raise RuntimeError(
            f"Expected checksum missing: {checksum_path.name}"
        )

    verify_checksum(data_path, checksum_path)
    print(f"[SUCCESS] {name} acquisition")


def main():
    parser = argparse.ArgumentParser(
        description="Museum data workflow orchestrator"
    )
    parser.parse_args()

    print("Starting IS 477 museum data workflow")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Met must be processed before Wikidata.
        for dataset in DATASETS:
            acquire_dataset(dataset)

    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"[FAILED] {error}", file=sys.stderr)
        return 1

    print("\nAcquisition and integrity checks complete.")
    print("Remaining workflow stages are not connected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

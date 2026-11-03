
from pathlib import Path

import pandas as pd

from src.ingestion.metadata_extractor import (
    extract_metadata,
    validate_dataset,
    generate_ingestion_report
)


SUPPORTED_FORMATS = {
    ".csv",
    ".xlsx",
    ".xls",
    ".json",
    ".parquet"
}


def discover_files(directory="datasets/raw"):
    """Recursively discover supported dataset files."""

    root = Path(directory)

    if not root.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {root}"
        )

    files = sorted(
        file for file in root.rglob("*")
        if file.is_file() and file.suffix.lower() in SUPPORTED_FORMATS
    )

    return files


def detect_file_type(file_path):
    """Detect dataset format."""

    extension = Path(file_path).suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return extension


def load_file(file_path):
    """Load a dataset based on its file extension."""

    file_path = Path(file_path)
    file_type = detect_file_type(file_path)

    if file_type == ".csv":
        return pd.read_csv(file_path)

    if file_type in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)

    if file_type == ".json":
        return pd.read_json(file_path)

    if file_type == ".parquet":
        return pd.read_parquet(file_path)

    raise ValueError(f"Cannot load file: {file_path}")


def save_processed_file(data, output_path):
    """Save processed dataset in Parquet format."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(output_path, index=False)

    return output_path


def run_ingestion_pipeline(
    raw_directory="datasets/raw",
    processed_directory="datasets/processed",
    report_directory="logs"
):
    """Run complete dataset ingestion pipeline."""

    raw_root = Path(raw_directory)
    processed_root = Path(processed_directory)

    files = discover_files(raw_directory)

    print(f"\nDiscovered datasets: {len(files)}")

    results = []

    for file_path in files:

        relative_path = file_path.relative_to(raw_root)
        dataset_name = relative_path.with_suffix("").as_posix().replace("/", "__")

        print(f"\nProcessing: {relative_path}")

        try:
            # 1. Load dataset
            data = load_file(file_path)

            # 2. Extract metadata
            metadata = extract_metadata(data, dataset_name)

            # 3. Validate dataset
            validation = validate_dataset(metadata)

            # 4. Save processed dataset
            output_path = (
                processed_root /
                relative_path.with_suffix(".parquet")
            )

            save_processed_file(data, output_path)

            # 5. Generate report
            generate_ingestion_report(
                metadata,
                validation,
                report_directory
            )

            status = "SUCCESS"

            print(f"Status: {status}")
            print(f"Quality: {validation['quality_status']}")
            print(f"Valid: {validation['is_valid']}")
            print(f"Errors: {len(validation['errors'])}")
            print(f"Warnings: {len(validation['warnings'])}")
            print(f"Saved: {output_path}")

            results.append({
                "dataset": dataset_name,
                "status": status,
                "quality_status": validation["quality_status"]
            })

        except Exception as error:

            print("Status: FAILED")
            print(f"Error: {error}")

            results.append({
                "dataset": dataset_name,
                "status": "FAILED",
                "error": str(error)
            })

    # Final summary
    successful = sum(
        result["status"] == "SUCCESS"
        for result in results
    )

    failed = len(results) - successful

    print("\n" + "=" * 50)
    print("INGESTION PIPELINE SUMMARY")
    print("=" * 50)

    print(f"Total datasets: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    return results


if __name__ == "__main__":
    run_ingestion_pipeline()

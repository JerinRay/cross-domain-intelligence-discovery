
from pathlib import Path

import pandas as pd

from src.ingestion.metadata_extractor import (
    extract_metadata,
    validate_dataset,
    generate_ingestion_report
)


def discover_files(directory: str):
    """Discover all supported dataset files."""

    raw_directory = Path(directory)

    if not raw_directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    if not raw_directory.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {directory}"
        )

    supported_extensions = {
        ".csv", ".xlsx", ".xls", ".json", ".parquet"
    }

    return sorted(
        file_path
        for file_path in raw_directory.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in supported_extensions
    )


def detect_file_type(file_path: str):
    """Identify the dataset format."""

    extension = Path(file_path).suffix.lower()

    formats = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".json": "json",
        ".parquet": "parquet"
    }

    if extension not in formats:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return formats[extension]


def load_file(file_path: str):
    """Load a dataset based on its format."""

    file_type = detect_file_type(file_path)

    if file_type == "csv":
        return pd.read_csv(file_path)

    if file_type == "excel":
        return pd.read_excel(file_path)

    if file_type == "json":
        return pd.read_json(file_path)

    if file_type == "parquet":
        return pd.read_parquet(file_path)

    raise ValueError(f"Unsupported file type: {file_type}")


def save_processed_file(data, output_path: str):
    """Save dataset in Parquet format."""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(output_file, index=False)

    return output_file


def run_ingestion_pipeline(
    raw_directory="datasets/raw",
    processed_directory="datasets/processed",
    report_directory="logs"
):
    """Execute the complete dataset ingestion pipeline."""

    files = discover_files(raw_directory)

    print(f"\nDiscovered datasets: {len(files)}")

    results = []

    for file_path in files:

        print(f"\nProcessing: {file_path.name}")

        try:
            # 1. Load dataset
            data = load_file(str(file_path))

            # 2. Extract metadata
            metadata = extract_metadata(
                data,
                file_path.stem
            )

            # 3. Validate dataset
            validation = validate_dataset(metadata)

            # 4. Save processed dataset
            output_path = (
                Path(processed_directory)
                / f"{file_path.stem}.parquet"
            )

            save_processed_file(data, output_path)

            # 5. Generate ingestion report
            generate_ingestion_report(
                metadata,
                validation,
                report_directory
            )

            result = {
                "dataset": file_path.name,
                "status": "success",
                "valid": validation["is_valid"],
                "rows": metadata["row_count"],
                "columns": metadata["column_count"],
                "issues": validation["issues"]
            }

            print("Status: SUCCESS")
            print("Valid:", validation["is_valid"])

        except Exception as error:

            result = {
                "dataset": file_path.name,
                "status": "failed",
                "error": str(error)
            }

            print("Status: FAILED")
            print("Error:", error)

        results.append(result)

    # 6. Final summary
    successful = sum(
        item["status"] == "success"
        for item in results
    )

    failed = len(results) - successful

    print("\n" + "=" * 50)
    print("INGESTION PIPELINE SUMMARY")
    print("=" * 50)

    print("Total datasets:", len(results))
    print("Successful:", successful)
    print("Failed:", failed)

    return results


if __name__ == "__main__":

    run_ingestion_pipeline()

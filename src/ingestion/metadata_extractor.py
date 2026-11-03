
import json
from pathlib import Path

import pandas as pd


def extract_metadata(data: pd.DataFrame, dataset_name: str):
    """Extract structural metadata from a dataset."""

    return {
        "dataset_name": dataset_name,
        "row_count": int(data.shape[0]),
        "column_count": int(data.shape[1]),
        "columns": data.columns.tolist(),
        "data_types": {
            column: str(dtype)
            for column, dtype in data.dtypes.items()
        },
        "missing_values": {
            column: int(count)
            for column, count in data.isnull().sum().items()
        },
        "duplicate_rows": int(data.duplicated().sum()),
        "memory_usage_bytes": int(
            data.memory_usage(deep=True).sum()
        )
    }


def validate_dataset(metadata: dict):
    """Classify data quality findings."""

    errors = []
    warnings = []
    info = []

    # Structural checks
    if metadata["row_count"] == 0:
        errors.append("Dataset is empty.")

    if metadata["column_count"] == 0:
        errors.append("Dataset has no columns.")

    # Duplicate checks
    duplicate_count = metadata["duplicate_rows"]

    if duplicate_count > 0:
        warnings.append(
            f"{duplicate_count} duplicate rows detected."
        )

    # Missing-value checks
    missing_values = metadata["missing_values"]
    total_missing = sum(missing_values.values())

    for column, count in missing_values.items():
        if count > 0:
            warnings.append(
                f"{column} contains {count} missing values."
            )

    # Dataset information
    info.append(
        f"Dataset contains {metadata['row_count']} rows "
        f"and {metadata['column_count']} columns."
    )

    info.append(f"Total missing values: {total_missing}")

    # Final status
    if errors:
        quality_status = "INVALID"
    elif warnings:
        quality_status = "WARNING"
    else:
        quality_status = "CLEAN"

    return {
        "is_valid": len(errors) == 0,
        "quality_status": quality_status,
        "errors": errors,
        "warnings": warnings,
        "info": info
    }


def generate_ingestion_report(
    metadata,
    validation,
    output_directory="logs"
):
    """Generate JSON ingestion report."""

    report_directory = Path(output_directory)
    report_directory.mkdir(parents=True, exist_ok=True)

    report = {
        "metadata": metadata,
        "validation": validation
    }

    report_path = (
        report_directory /
        f'{metadata["dataset_name"]}_report.json'
    )

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Ingestion report saved: {report_path}")

    return report_path

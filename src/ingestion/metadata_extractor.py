
import json
from pathlib import Path

import pandas as pd


def extract_metadata(data: pd.DataFrame, dataset_name: str):
    """Extract structural and statistical metadata."""

    metadata = {
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

    return metadata


def validate_dataset(metadata: dict):
    """Perform basic data quality validation."""

    issues = []

    if metadata["row_count"] == 0:
        issues.append("Dataset is empty.")

    if metadata["column_count"] == 0:
        issues.append("Dataset has no columns.")

    if metadata["duplicate_rows"] > 0:
        issues.append(
            f'{metadata["duplicate_rows"]} duplicate rows found.'
        )

    for column, count in metadata["missing_values"].items():
        if count > 0:
            issues.append(
                f"{column} contains {count} missing values."
            )

    return {
        "is_valid": len(issues) == 0,
        "issues": issues
    }


def generate_ingestion_report(
    metadata: dict,
    validation: dict,
    output_directory: str = "logs"
):
    """Save metadata and validation results as JSON."""

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


from pathlib import Path

import pandas as pd


def discover_files(directory: str):
    """
    Automatically discover supported dataset files
    inside a directory and its subdirectories.
    """
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
        ".csv",
        ".xlsx",
        ".xls",
        ".json",
        ".parquet"
    }

    discovered_files = []

    for file_path in raw_directory.rglob("*"):
        if (
            file_path.is_file()
            and file_path.suffix.lower() in supported_extensions
        ):
            discovered_files.append(file_path)

    return sorted(discovered_files)


def detect_file_type(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    supported_formats = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".json": "json",
        ".parquet": "parquet"
    }

    if extension not in supported_formats:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return supported_formats[extension]


def load_file(file_path: str):
    file_type = detect_file_type(file_path)

    if file_type == "csv":
        return pd.read_csv(file_path)

    elif file_type == "excel":
        return pd.read_excel(file_path)

    elif file_type == "json":
        return pd.read_json(file_path)

    elif file_type == "parquet":
        return pd.read_parquet(file_path)


def save_processed_file(data, output_path: str):
    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data.to_parquet(
        output_file,
        index=False
    )

    print(f"Processed dataset saved: {output_file}")


if __name__ == "__main__":

    raw_directory = "datasets/raw"

    print("Discovering datasets...\n")

    discovered_files = discover_files(raw_directory)

    if not discovered_files:
        print("No supported datasets found.")

    else:
        for file_path in discovered_files:
            print("Discovered:", file_path)

    print("\nTesting dataset loading...\n")

    file_path = "datasets/raw/customers.csv"

    print("Detected file type:", detect_file_type(file_path))

    data = load_file(file_path)

    print("\nLoaded Dataset:")
    print(data)

    print("\nDataset Shape:", data.shape)

    print("\nColumn Names:")
    print(data.columns.tolist())

    print("\nMissing Values:")
    print(data.isnull().sum())

    save_processed_file(
        data,
        "datasets/processed/customers.parquet"
    )

    saved_data = pd.read_parquet(
        "datasets/processed/customers.parquet"
    )

    print("\nVerified Parquet Dataset:")
    print(saved_data)

    print("\nParquet Shape:", saved_data.shape)

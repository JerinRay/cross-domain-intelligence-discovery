from pathlib import Path

import pandas as pd
import polars as pl
import pyarrow as pa

import json
import logging
def detect_file_type(file_path: str) -> str:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    supported_formats = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".json": "json",
        ".parquet": "parquet"
    }

    if extension not in supported_formats:
        raise ValueError(f"Unsupported file format: {extension}")

    return supported_formats[extension]
if __name__ == "__main__":
    print(detect_file_type("datasets/raw/customers.csv"))
    if __name__ == "__main__":
        print(detect_file_type("datasets/raw/customers.csv"))
        
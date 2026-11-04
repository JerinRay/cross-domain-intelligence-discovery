
from pathlib import Path
import pandas as pd

from src.data_understanding.engine import DataUnderstandingEngine


def main():
    dataset_path = Path(
        "datasets/processed/olist/olist_orders_dataset.parquet"
    )

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    print("Loading Olist Orders dataset...")

    data = pd.read_parquet(dataset_path)

    print(f"Dataset shape: {data.shape}")

    engine = DataUnderstandingEngine(sample_size=100_000)

    report = engine.analyze_dataset(
        data,
        dataset_name="olist_orders"
    )

    report_path = engine.save_report(report)

    print("\n========== TEST SUMMARY ==========")
    print("Status:", report["status"])
    print("Analyzers completed:", len(report["results"]))
    print("Analyzers:", list(report["results"].keys()))
    print("Report:", report_path)


if __name__ == "__main__":
    main()


from pathlib import Path

import pandas as pd

from src.discovery.cross_domain_pattern_engine import (
    CrossDomainPatternEngine
)


def main():
    data_dir = Path("datasets/processed")

    dataset_files = {
        "customers": "olist_customers_dataset.parquet",
        "orders": "olist_orders_dataset.parquet",
        "order_items": "olist_order_items_dataset.parquet",
        "products": "olist_products_dataset.parquet",
        "sellers": "olist_sellers_dataset.parquet",
        "payments": "olist_order_payments_dataset.parquet",
        "reviews": "olist_order_reviews_dataset.parquet",
    }

    datasets = {}

    print("=" * 65)
    print("OLIST CROSS-DOMAIN PATTERN DISCOVERY")
    print("=" * 65)

    for name, filename in dataset_files.items():
        filepath = data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"Dataset not found: {filepath}"
            )

        dataframe = pd.read_parquet(filepath)

        print(
            f"{name}: {len(dataframe):,} rows, "
            f"{len(dataframe.columns)} columns"
        )

        # Use a reproducible sample to keep pairwise analysis
        # manageable on a local MacBook.
        if len(dataframe) > 5000:
            dataframe = dataframe.sample(
                n=5000,
                random_state=42
            )

        datasets[name] = dataframe

    print("\nRunning cross-domain analysis...")

    engine = CrossDomainPatternEngine(sample_size=3000)
    report = engine.analyze(datasets)

    output_path = engine.save_report(report)

    print("\n" + "=" * 65)
    print("CROSS-DOMAIN ANALYSIS RESULTS")
    print("=" * 65)

    print("Datasets:", report["dataset_count"])
    print("Dataset pairs:", report["dataset_pair_count"])
    print(
        "Connected pairs:",
        report["connected_dataset_pair_count"]
    )
    print(
        "Relationship candidates:",
        report["total_relationship_candidates"]
    )
    print("Confidence:", report["confidence_summary"])

    print("\nPairwise results:")

    for pair in report["dataset_pair_analysis"]:
        print(
            f"{pair['dataset_a']} <-> {pair['dataset_b']}: "
            f"{pair['candidate_count']} candidates"
        )

    print("\nReport saved:", output_path)
    print("Status:", report["status"])
    print("\nAnalysis completed.")


if __name__ == "__main__":
    main()

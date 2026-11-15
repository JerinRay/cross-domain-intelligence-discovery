
from pathlib import Path

import pandas as pd


DATA_DIR = Path("datasets/processed")


# Dataset filename mapping
DATASET_FILES = {
    "customers": "olist_customers_dataset.parquet",
    "orders": "olist_orders_dataset.parquet",
    "order_items": "olist_order_items_dataset.parquet",
    "products": "olist_products_dataset.parquet",
    "sellers": "olist_sellers_dataset.parquet",
    "payments": "olist_order_payments_dataset.parquet",
    "reviews": "olist_order_reviews_dataset.parquet",
}


# Expected relationships to validate
RELATIONSHIPS = [
    ("customers", "customer_id", "orders", "customer_id"),
    ("orders", "order_id", "order_items", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("orders", "order_id", "payments", "order_id"),
    ("orders", "order_id", "reviews", "order_id"),
    ("order_items", "order_id", "reviews", "order_id"),
]


def load_dataset(name):
    """Load an Olist Parquet dataset."""

    if name not in DATASET_FILES:
        raise ValueError(f"Unknown dataset: {name}")

    filepath = DATA_DIR / DATASET_FILES[name]

    if not filepath.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {filepath}"
        )

    dataframe = pd.read_parquet(filepath)

    print(
        f"Loaded {name}: "
        f"{len(dataframe):,} rows, "
        f"{len(dataframe.columns)} columns"
    )

    return dataframe


def validate_relationship(
    left,
    left_key,
    right,
    right_key
):
    """Validate matching unique key values between two datasets."""

    if left_key not in left.columns:
        raise KeyError(f"Column '{left_key}' not found.")

    if right_key not in right.columns:
        raise KeyError(f"Column '{right_key}' not found.")

    left_values = set(
        left[left_key].dropna().unique()
    )

    right_values = set(
        right[right_key].dropna().unique()
    )

    matched_values = left_values & right_values

    unmatched_left = left_values - right_values
    unmatched_right = right_values - left_values

    left_coverage = (
        len(matched_values) / len(left_values) * 100
        if left_values else 0
    )

    right_coverage = (
        len(matched_values) / len(right_values) * 100
        if right_values else 0
    )

    return {
        "matched_unique_values": len(matched_values),
        "left_unique_values": len(left_values),
        "right_unique_values": len(right_values),
        "unmatched_left_values": len(unmatched_left),
        "unmatched_right_values": len(unmatched_right),
        "left_coverage_percent": round(left_coverage, 2),
        "right_coverage_percent": round(right_coverage, 2),
    }


def main():
    print("=" * 70)
    print("OLIST FULL DATASET RELATIONSHIP VALIDATION")
    print("=" * 70)

    required_datasets = sorted({
        dataset_name
        for relationship in RELATIONSHIPS
        for dataset_name in (
            relationship[0],
            relationship[2]
        )
    })

    datasets = {}

    # Load all required datasets
    print("\nSTEP 1: Loading datasets")
    print("-" * 70)

    for name in required_datasets:
        datasets[name] = load_dataset(name)

    # Validate relationships
    print("\nSTEP 2: Validating relationships")
    print("-" * 70)

    for (
        left_name,
        left_key,
        right_name,
        right_key
    ) in RELATIONSHIPS:

        print(
            f"\n{left_name}.{left_key} "
            f"-> {right_name}.{right_key}"
        )

        result = validate_relationship(
            datasets[left_name],
            left_key,
            datasets[right_name],
            right_key
        )

        for metric, value in result.items():
            print(f"  {metric}: {value}")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()

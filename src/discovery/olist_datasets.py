"""Shared loading of the Olist datasets for the cross-domain scan.

Ingestion mirrors the raw folder layout, so files from datasets/raw/olist/ end up in
datasets/processed/olist/.  Older runs wrote them straight into datasets/processed/,
so both locations are checked (olist/ first).
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "datasets" / "processed"

# scan name -> processed file
OLIST_SCAN_FILES = {
    "customers": "olist_customers_dataset.parquet",
    "orders": "olist_orders_dataset.parquet",
    "order_items": "olist_order_items_dataset.parquet",
    "products": "olist_products_dataset.parquet",
    "sellers": "olist_sellers_dataset.parquet",
    "payments": "olist_order_payments_dataset.parquet",
    "reviews": "olist_order_reviews_dataset.parquet",
}


def locate_processed(filename, processed_dir=PROCESSED_DIR):
    """Path of a processed file, looking in processed/olist/ then processed/."""
    processed_dir = Path(processed_dir)
    for path in (processed_dir / "olist" / filename, processed_dir / filename):
        if path.exists():
            return path
    return None


def load_scan_frames(processed_dir=PROCESSED_DIR, max_rows=5000, random_state=42):
    """Load the seven Olist tables, each sampled to at most `max_rows` rows."""
    frames = {}
    for name, filename in OLIST_SCAN_FILES.items():
        path = locate_processed(filename, processed_dir)
        if path is None:
            raise FileNotFoundError(
                f"{filename} not found in {Path(processed_dir) / 'olist'} or {processed_dir}"
            )
        frame = pd.read_parquet(path)
        if len(frame) > max_rows:
            frame = frame.sample(n=max_rows, random_state=random_state)
        frames[name] = frame
    return frames
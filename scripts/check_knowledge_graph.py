"""Manual check: build the Olist knowledge graph and print a summary.

Run from anywhere:  python scripts/check_knowledge_graph.py
(It lives in scripts/, not tests/, because it needs the full processed datasets.)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.discovery.olist_datasets import locate_processed  # noqa: E402
from src.knowledge_graph.olist_graph_loader import OlistGraphLoader  # noqa: E402
from src.knowledge_graph.graph_validator import KnowledgeGraphValidator  # noqa: E402

files = {
    "orders_path": "olist_orders_dataset.parquet",
    "customers_path": "olist_customers_dataset.parquet",
    "order_items_path": "olist_order_items_dataset.parquet",
    "products_path": "olist_products_dataset.parquet",
    "sellers_path": "olist_sellers_dataset.parquet",
    "payments_path": "olist_order_payments_dataset.parquet",
    "reviews_path": "olist_order_reviews_dataset.parquet",
}
paths = {name: locate_processed(filename) for name, filename in files.items()}

for name, path in paths.items():
    if path is None:
        raise FileNotFoundError(f"Missing {name}: {files[name]} (looked in datasets/processed/olist and datasets/processed)")

print("All seven dataset files found.")
print("Building cross-domain knowledge graph...")

loader = OlistGraphLoader()
builder = loader.load_data(
    **{name: str(path) for name, path in paths.items()}
)

print("\nGRAPH SUMMARY")
print(builder.get_graph_summary())

print("\nENTITY TYPE COUNTS")
from collections import Counter

entity_counts = Counter(
    data.get("entity_type")
    for _, data in builder.graph.nodes(data=True)
)
print(dict(entity_counts))

print("\nRELATIONSHIP TYPE COUNTS")
relationship_counts = Counter(
    data.get("relationship_type")
    for _, _, data in builder.graph.edges(data=True)
)
print(dict(relationship_counts))

print("\nGRAPH VALIDATION")
validator = KnowledgeGraphValidator()
validation = validator.validate(builder)
print(validation)

print("\nDAY 11 GRAPH INTEGRATION TEST COMPLETED")
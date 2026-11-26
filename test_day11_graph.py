from pathlib import Path

from src.knowledge_graph.olist_graph_loader import OlistGraphLoader
from src.knowledge_graph.graph_validator import KnowledgeGraphValidator

base = Path("datasets/processed")

paths = {
    "orders_path": base / "olist_orders_dataset.parquet",
    "customers_path": base / "olist_customers_dataset.parquet",
    "order_items_path": base / "olist_order_items_dataset.parquet",
    "products_path": base / "olist_products_dataset.parquet",
    "sellers_path": base / "olist_sellers_dataset.parquet",
    "payments_path": base / "olist_order_payments_dataset.parquet",
    "reviews_path": base / "olist_order_reviews_dataset.parquet",
}

for name, path in paths.items():
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")

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

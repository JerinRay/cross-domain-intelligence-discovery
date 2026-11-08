
import json

from src.knowledge_graph.olist_graph_loader import OlistGraphLoader
from src.explainability.explanation_engine import ExplanationEngine


def main():
    print("=" * 65)
    print("OLIST KNOWLEDGE GRAPH EXPLAINABILITY DEMO")
    print("=" * 65)

    orders_path = (
        "datasets/processed/olist/olist_orders_dataset.parquet"
    )

    customers_path = (
        "datasets/processed/olist/olist_customers_dataset.parquet"
    )

    # Step 1: Load real Olist graph
    loader = OlistGraphLoader()

    builder = loader.load_data(
        orders_path,
        customers_path
    )

    print("\nGraph summary:")
    print(json.dumps(
        builder.get_graph_summary(),
        indent=4,
        default=str
    ))

    # Step 2: Select an existing Customer -> Order relationship
    source_id = (
        "customer:9ef432eb6251297304e76186b10a928d"
    )

    target_id = (
        "order:e481f51cbdc54678b7cc49136f2d6af7"
    )

    # Step 3: Initialize unified explanation engine
    engine = ExplanationEngine(graph_builder=builder)

    # Step 4: Explain direct relationship
    result = engine.explain_relationship(
        source_id,
        target_id
    )

    print("\n" + "=" * 65)
    print("GRAPH RELATIONSHIP EXPLANATION")
    print("=" * 65)

    print(json.dumps(
        result,
        indent=4,
        default=str
    ))

    # Step 5: Save explanation
    output_path = (
        "logs/olist_graph_relationship_explanation.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=4,
            default=str
        )

    print("\nExplanation saved to:", output_path)
    print("\nGraph explainability integration completed.")


if __name__ == "__main__":
    main()

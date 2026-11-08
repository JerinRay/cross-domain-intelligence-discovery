
from src.knowledge_graph.olist_graph_loader import OlistGraphLoader
from src.knowledge_graph.graph_evolver import GraphEvolver


def main():
    print("=" * 60)
    print("DAY 8 - KNOWLEDGE GRAPH EVOLUTION DEMO")
    print("=" * 60)

    # Load the real Olist dataset
    loader = OlistGraphLoader()

    builder = loader.load_data(
        "datasets/processed/olist/olist_orders_dataset.parquet",
        "datasets/processed/olist/olist_customers_dataset.parquet"
    )

    evolver = GraphEvolver(builder)

    print("\n1. INITIAL GRAPH SUMMARY")
    print(builder.get_graph_summary())

    # Select existing entities from the graph
    customer_id = "customer:9ef432eb6251297304e76186b10a928d"
    order_id = "order:e481f51cbdc54678b7cc49136f2d6af7"

    print("\n2. UPDATE EXISTING CUSTOMER")
    result = evolver.update_entity(
        customer_id,
        evolution_demo_tag="day_8_verified"
    )
    print("Update result:", result)
    print(
        "Updated property:",
        builder.graph.nodes[customer_id].get("evolution_demo_tag")
    )

    print("\n3. TEST DUPLICATE RELATIONSHIP PREVENTION")
    result = evolver.add_relationship(
        customer_id,
        order_id,
        "PLACED"
    )
    print("Duplicate relationship result:", result)

    print("\n4. ADD A SYNTHETIC DEMO ENTITY")
    result = evolver.add_entity(
        "product:day8_demo_001",
        "Product",
        product_name="Synthetic Demo Product",
        is_demo=True
    )
    print("Entity addition result:", result)

    print("\n5. ADD A SYNTHETIC DEMO RELATIONSHIP")
    result = evolver.add_relationship(
        order_id,
        "product:day8_demo_001",
        "DEMO_CONTAINS",
        is_demo=True
    )
    print("Relationship addition result:", result)

    print("\n6. FINAL GRAPH SUMMARY")
    print(builder.get_graph_summary())

    print("\n7. EVOLUTION SUMMARY")
    print(evolver.get_evolution_summary())

    print("\n8. EVOLUTION HISTORY")
    for change in evolver.get_evolution_history():
        print(change)

    print("\nDAY 8 DEMO COMPLETED")


if __name__ == "__main__":
    main()

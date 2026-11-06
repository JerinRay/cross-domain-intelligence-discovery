
from src.knowledge_graph.olist_graph_loader import OlistGraphLoader
from src.knowledge_graph.graph_reasoner import GraphReasoner
from src.knowledge_graph.query_engine import GraphQueryEngine


def main():
    orders_path = (
        "datasets/processed/olist/"
        "olist_orders_dataset.parquet"
    )

    customers_path = (
        "datasets/processed/olist/"
        "olist_customers_dataset.parquet"
    )

    print("Loading Olist knowledge graph...")

    loader = OlistGraphLoader()
    builder = loader.load_data(
        orders_path,
        customers_path
    )

    reasoner = GraphReasoner(builder)
    engine = GraphQueryEngine(reasoner)

    graph = builder.graph

    print("\nKnowledge Graph Summary")
    print("----------------------")
    print(builder.get_graph_summary())

    # Select an order that has an incoming customer relationship.
    order_id = next(
        (
            node
            for node, data in graph.nodes(data=True)
            if data.get("entity_type") == "Order"
            and graph.in_degree(node) > 0
        ),
        None
    )

    if order_id is None:
        print("No connected order found.")
        return

    customer_id = next(graph.predecessors(order_id))

    print("\nSelected Customer:", customer_id)
    print("Selected Order:", order_id)

    print("\n1. Customer Entity Query")
    print("-----------------------")

    print(
        engine.execute({
            "operation": "GET_ENTITY",
            "entity_id": customer_id
        })
    )

    print("\n2. Customer Relationship Query")
    print("------------------------------")

    print(
        engine.execute({
            "operation": "GET_NEIGHBORS",
            "entity_id": customer_id
        })
    )

    print("\n3. Customer-to-Order Path Query")
    print("-------------------------------")

    print(
        engine.execute({
            "operation": "FIND_PATH",
            "source_id": customer_id,
            "target_id": order_id,
            "max_depth": 1
        })
    )

    print("\n4. Direct Relationship Query")
    print("----------------------------")

    print(
        engine.execute({
            "operation": "GET_RELATIONSHIPS",
            "source_id": customer_id,
            "target_id": order_id
        })
    )

    print("\nReal Olist reasoning demonstration completed.")


if __name__ == "__main__":
    main()

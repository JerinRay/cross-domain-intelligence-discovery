
import pandas as pd
import pytest

from src.knowledge_graph.olist_graph_loader import OlistGraphLoader


@pytest.fixture
def sample_datasets(tmp_path):
    datasets = {
        "customers": pd.DataFrame([
            {
                "customer_id": "customer_1",
                "customer_unique_id": "unique_1",
                "customer_zip_code_prefix": 1000,
                "customer_city": "city_a",
                "customer_state": "SP",
            }
        ]),
        "orders": pd.DataFrame([
            {
                "order_id": "order_1",
                "customer_id": "customer_1",
                "order_status": "delivered",
                "order_purchase_timestamp": pd.Timestamp("2026-01-01"),
            },
            {
                "order_id": "order_2",
                "customer_id": "customer_1",
                "order_status": "delivered",
                "order_purchase_timestamp": pd.Timestamp("2026-01-02"),
            },
        ]),
        "order_items": pd.DataFrame([
            {
                "order_id": "order_1",
                "order_item_id": 1,
                "product_id": "product_1",
                "seller_id": "seller_1",
                "shipping_limit_date": pd.Timestamp("2026-01-03"),
                "price": 100.0,
                "freight_value": 10.0,
            }
        ]),
        "products": pd.DataFrame([
            {
                "product_id": "product_1",
                "product_category_name": "electronics",
                "product_weight_g": 500.0,
            }
        ]),
        "sellers": pd.DataFrame([
            {
                "seller_id": "seller_1",
                "seller_zip_code_prefix": 2000,
                "seller_city": "city_b",
                "seller_state": "RJ",
            }
        ]),
        "payments": pd.DataFrame([
            {
                "order_id": "order_1",
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 2,
                "payment_value": 110.0,
            }
        ]),
        "reviews": pd.DataFrame([
            {
                "review_id": "review_1",
                "order_id": "order_1",
                "review_score": 5,
                "review_comment_title": "Great",
                "review_comment_message": "Excellent product",
                "review_creation_date": pd.Timestamp("2026-01-05"),
                "review_answer_timestamp": pd.Timestamp("2026-01-06"),
            },
            {
                "review_id": "review_1",
                "order_id": "order_2",
                "review_score": 4,
                "review_comment_title": "Good",
                "review_comment_message": "Good product",
                "review_creation_date": pd.Timestamp("2026-01-07"),
                "review_answer_timestamp": pd.Timestamp("2026-01-08"),
            },
        ]),
    }

    paths = {}
    for name, dataframe in datasets.items():
        file_path = tmp_path / f"{name}.parquet"
        dataframe.to_parquet(file_path, index=False)
        paths[name] = str(file_path)

    return paths


def test_load_all_seven_datasets(sample_datasets):
    loader = OlistGraphLoader()
    builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
        order_items_path=sample_datasets["order_items"],
        products_path=sample_datasets["products"],
        sellers_path=sample_datasets["sellers"],
        payments_path=sample_datasets["payments"],
        reviews_path=sample_datasets["reviews"],
    )

    graph = builder.graph

    assert graph.number_of_nodes() == 9
    assert graph.number_of_edges() == 8

    entity_types = [
        data["entity_type"] for _, data in graph.nodes(data=True)
    ]

    assert entity_types.count("Customer") == 1
    assert entity_types.count("Order") == 2
    assert entity_types.count("OrderItem") == 1
    assert entity_types.count("Product") == 1
    assert entity_types.count("Seller") == 1
    assert entity_types.count("Payment") == 1
    assert entity_types.count("Review") == 2


def test_all_expected_relationships_are_created(sample_datasets):
    loader = OlistGraphLoader()
    builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
        order_items_path=sample_datasets["order_items"],
        products_path=sample_datasets["products"],
        sellers_path=sample_datasets["sellers"],
        payments_path=sample_datasets["payments"],
        reviews_path=sample_datasets["reviews"],
    )

    relationship_types = [
        data["relationship_type"]
        for _, _, data in builder.graph.edges(data=True)
    ]

    assert relationship_types.count("PLACED") == 2
    assert relationship_types.count("CONTAINS") == 1
    assert relationship_types.count("REFERENCES") == 1
    assert relationship_types.count("SOLD_BY") == 1
    assert relationship_types.count("HAS_PAYMENT") == 1
    assert relationship_types.count("HAS_REVIEW") == 2


def test_duplicate_review_ids_use_composite_node_ids(sample_datasets):
    loader = OlistGraphLoader()
    builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
        reviews_path=sample_datasets["reviews"],
    )

    review_nodes = [
        node
        for node, data in builder.graph.nodes(data=True)
        if data.get("entity_type") == "Review"
    ]

    assert len(review_nodes) == 2
    assert "review:review_1:order_1" in review_nodes
    assert "review:review_1:order_2" in review_nodes


def test_old_two_dataset_api_remains_compatible(sample_datasets):
    loader = OlistGraphLoader()
    builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
    )

    assert builder.graph.number_of_nodes() == 3
    assert builder.graph.number_of_edges() == 2
    assert "customer:customer_1" in builder.graph
    assert "order:order_1" in builder.graph
    assert "order:order_2" in builder.graph


def test_loader_can_be_reused_without_old_graph_data(sample_datasets):
    loader = OlistGraphLoader()

    first_builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
    )

    second_builder = loader.load_data(
        orders_path=sample_datasets["orders"],
        customers_path=sample_datasets["customers"],
        products_path=sample_datasets["products"],
    )

    assert first_builder.graph.number_of_nodes() == 3
    assert second_builder.graph.number_of_nodes() == 4
    assert "product:product_1" in second_builder.graph


import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.explainability.graph_explainer import GraphExplainer


class TestGraphExplainer(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()

        self.builder.add_entity(
            "customer_1",
            "Customer",
            city="Sao Paulo"
        )

        self.builder.add_entity(
            "order_1",
            "Order",
            status="delivered"
        )

        self.builder.add_entity(
            "product_1",
            "Product",
            name="Laptop"
        )

        self.builder.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        self.builder.add_relationship(
            "order_1",
            "product_1",
            "CONTAINS",
            quantity=1
        )

        self.explainer = GraphExplainer(self.builder)

    def test_explains_direct_relationship(self):
        result = self.explainer.explain_relationship(
            "customer_1",
            "order_1"
        )

        self.assertEqual(
            result["relationship_count"], 1
        )

        self.assertEqual(
            result["relationships"][0]["relationship_type"],
            "PLACED"
        )

    def test_explains_multiple_relationships(self):
        self.builder.add_relationship(
            "customer_1",
            "order_1",
            "ASSOCIATED_WITH"
        )

        result = self.explainer.explain_relationship(
            "customer_1",
            "order_1"
        )

        self.assertEqual(
            result["relationship_count"], 2
        )

    def test_handles_entities_without_direct_relationship(self):
        result = self.explainer.explain_relationship(
            "customer_1",
            "product_1"
        )

        self.assertEqual(
            result["relationship_count"], 0
        )

    def test_explains_multi_hop_path(self):
        result = self.explainer.explain_path([
            "customer_1",
            "order_1",
            "product_1"
        ])

        self.assertEqual(result["path_length"], 2)
        self.assertEqual(len(result["steps"]), 2)

        self.assertEqual(
            result["steps"][0]["relationship_types"],
            ["PLACED"]
        )

        self.assertEqual(
            result["steps"][1]["relationship_types"],
            ["CONTAINS"]
        )

    def test_rejects_invalid_path_type(self):
        with self.assertRaises(TypeError):
            self.explainer.explain_path("customer_1")

    def test_rejects_short_path(self):
        with self.assertRaises(ValueError):
            self.explainer.explain_path(["customer_1"])

    def test_rejects_missing_entity(self):
        with self.assertRaises(ValueError):
            self.explainer.explain_relationship(
                "unknown_customer",
                "order_1"
            )

    def test_rejects_nonexistent_path_relationship(self):
        with self.assertRaises(ValueError):
            self.explainer.explain_path([
                "customer_1",
                "product_1"
            ])

    def test_rejects_invalid_graph_builder(self):
        with self.assertRaises(TypeError):
            GraphExplainer({})


if __name__ == "__main__":
    unittest.main()

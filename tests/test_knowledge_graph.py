
import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder


class TestKnowledgeGraphBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()

    def test_add_entity(self):
        self.builder.add_entity(
            "customer_1",
            "Customer",
            name="John"
        )

        self.assertIn("customer_1", self.builder.graph.nodes)
        self.assertEqual(
            self.builder.graph.nodes["customer_1"]["entity_type"],
            "Customer"
        )

    def test_add_relationship(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("order_1", "Order")

        self.builder.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        self.assertEqual(self.builder.graph.number_of_edges(), 1)

    def test_relationship_requires_existing_entities(self):
        self.builder.add_entity("customer_1", "Customer")

        with self.assertRaises(ValueError):
            self.builder.add_relationship(
                "customer_1",
                "order_1",
                "PLACED"
            )

    def test_graph_summary(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("order_1", "Order")

        self.builder.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        summary = self.builder.get_graph_summary()

        self.assertEqual(summary["total_entities"], 2)
        self.assertEqual(summary["total_relationships"], 1)
        self.assertIn("Customer", summary["entity_types"])
        self.assertIn("Order", summary["entity_types"])


if __name__ == "__main__":
    unittest.main()

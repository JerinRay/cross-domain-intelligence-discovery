
import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_validator import KnowledgeGraphValidator


class TestKnowledgeGraphValidator(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()
        self.validator = KnowledgeGraphValidator()

    def test_valid_graph(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("order_1", "Order")
        self.builder.add_relationship(
            "customer_1", "order_1", "PLACED"
        )

        result = self.validator.validate(self.builder)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["total_nodes"], 2)
        self.assertEqual(result["total_edges"], 1)

    def test_entity_type_counts(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("customer_2", "Customer")
        self.builder.add_entity("order_1", "Order")

        self.builder.add_relationship(
            "customer_1", "order_1", "PLACED"
        )
        self.builder.add_relationship(
            "customer_2", "order_1", "PLACED"
        )

        result = self.validator.validate(self.builder)

        self.assertEqual(
            result["entity_type_counts"]["Customer"], 2
        )
        self.assertEqual(
            result["entity_type_counts"]["Order"], 1
        )

    def test_relationship_type_counts(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("order_1", "Order")
        self.builder.add_relationship(
            "customer_1", "order_1", "PLACED"
        )

        result = self.validator.validate(self.builder)

        self.assertEqual(
            result["relationship_type_counts"]["PLACED"], 1
        )

    def test_isolated_nodes_make_graph_invalid(self):
        self.builder.add_entity("customer_1", "Customer")
        self.builder.add_entity("unused_1", "Product")

        result = self.validator.validate(self.builder)

        self.assertFalse(result["is_valid"])
        self.assertEqual(result["isolated_nodes"], 2)


if __name__ == "__main__":
    unittest.main()

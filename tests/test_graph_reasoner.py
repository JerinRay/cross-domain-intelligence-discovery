
import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_reasoner import GraphReasoner


class TestGraphReasoner(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()

        # Create sample entities
        self.builder.add_entity(
            "customer:1",
            "Customer",
            city="Chennai"
        )

        self.builder.add_entity(
            "order:101",
            "Order",
            status="delivered"
        )

        self.builder.add_entity(
            "product:501",
            "Product",
            name="Laptop"
        )

        # Create relationships
        self.builder.add_relationship(
            "customer:1",
            "order:101",
            "PLACED"
        )

        self.builder.add_relationship(
            "order:101",
            "product:501",
            "CONTAINS"
        )

        self.reasoner = GraphReasoner(self.builder)

    def test_get_existing_entity(self):
        result = self.reasoner.get_entity("customer:1")

        self.assertIsNotNone(result)
        self.assertEqual(result["entity_type"], "Customer")
        self.assertEqual(result["city"], "Chennai")

    def test_get_non_existing_entity(self):
        result = self.reasoner.get_entity("customer:999")

        self.assertIsNone(result)

    def test_get_neighbors(self):
        result = self.reasoner.get_neighbors("customer:1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["entity_id"], "order:101")
        self.assertEqual(result[0]["relationship"], "PLACED")
        self.assertEqual(result[0]["entity_type"], "Order")

    def test_get_neighbors_for_missing_entity(self):
        result = self.reasoner.get_neighbors("customer:999")

        self.assertEqual(result, [])

    def test_find_directed_path(self):
        result = self.reasoner.find_paths(
            "customer:1",
            "order:101"
        )

        self.assertEqual(
            result,
            [["customer:1", "order:101"]]
        )

    def test_find_multi_hop_path(self):
        result = self.reasoner.find_paths(
            "customer:1",
            "product:501",
            max_depth=2
        )

        self.assertEqual(
            result,
            [[
                "customer:1",
                "order:101",
                "product:501"
            ]]
        )

    def test_find_path_for_missing_entity(self):
        result = self.reasoner.find_paths(
            "customer:999",
            "product:501"
        )

        self.assertEqual(result, [])

    def test_find_path_with_insufficient_depth(self):
        result = self.reasoner.find_paths(
            "customer:1",
            "product:501",
            max_depth=1
        )

        self.assertEqual(result, [])

    def test_find_path_with_invalid_depth(self):
        with self.assertRaises(ValueError):
            self.reasoner.find_paths(
                "customer:1",
                "product:501",
                max_depth=0
            )

    def test_find_path_to_same_entity(self):
        result = self.reasoner.find_paths(
            "customer:1",
            "customer:1"
        )

        self.assertEqual(result, [["customer:1"]])

    def test_get_direct_relationships(self):
        result = self.reasoner.get_relationships(
            "customer:1",
            "order:101"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["relationship_type"],
            "PLACED"
        )

    def test_get_relationships_for_missing_entities(self):
        result = self.reasoner.get_relationships(
            "customer:999",
            "order:101"
        )

        self.assertEqual(result, [])

    def test_get_relationships_without_connection(self):
        result = self.reasoner.get_relationships(
            "customer:1",
            "product:501"
        )

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()

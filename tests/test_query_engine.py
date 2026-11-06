
import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_reasoner import GraphReasoner
from src.knowledge_graph.query_engine import GraphQueryEngine


class TestGraphQueryEngine(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()

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
        self.engine = GraphQueryEngine(self.reasoner)

    def test_get_entity_query(self):
        result = self.engine.execute({
            "operation": "GET_ENTITY",
            "entity_id": "customer:1"
        })

        self.assertEqual(result["entity_type"], "Customer")

    def test_get_neighbors_query(self):
        result = self.engine.execute({
            "operation": "GET_NEIGHBORS",
            "entity_id": "customer:1"
        })

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["entity_id"], "order:101")

    def test_find_path_query(self):
        result = self.engine.execute({
            "operation": "FIND_PATH",
            "source_id": "customer:1",
            "target_id": "product:501",
            "max_depth": 2
        })

        self.assertEqual(
            result,
            [["customer:1", "order:101", "product:501"]]
        )

    def test_get_relationships_query(self):
        result = self.engine.execute({
            "operation": "GET_RELATIONSHIPS",
            "source_id": "customer:1",
            "target_id": "order:101"
        })

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["relationship_type"],
            "PLACED"
        )

    def test_unsupported_operation(self):
        with self.assertRaises(ValueError):
            self.engine.execute({
                "operation": "UNKNOWN"
            })

    def test_missing_entity_id(self):
        with self.assertRaises(ValueError):
            self.engine.execute({
                "operation": "GET_ENTITY"
            })

    def test_missing_path_parameters(self):
        with self.assertRaises(ValueError):
            self.engine.execute({
                "operation": "FIND_PATH",
                "source_id": "customer:1"
            })

    def test_invalid_query_type(self):
        with self.assertRaises(TypeError):
            self.engine.execute("GET_ENTITY")

    def test_invalid_max_depth(self):
        with self.assertRaises(ValueError):
            self.engine.execute({
                "operation": "FIND_PATH",
                "source_id": "customer:1",
                "target_id": "product:501",
                "max_depth": "two"
            })


if __name__ == "__main__":
    unittest.main()

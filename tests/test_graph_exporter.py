
import json
import os
import tempfile
import unittest

import networkx as nx

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_exporter import KnowledgeGraphExporter


class TestKnowledgeGraphExporter(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()
        self.exporter = KnowledgeGraphExporter()

        self.builder.add_entity(
            "customer_1", "Customer", city="Chennai"
        )
        self.builder.add_entity(
            "order_1", "Order", status="delivered"
        )
        self.builder.add_relationship(
            "customer_1", "order_1", "PLACED"
        )

        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_graphml(self):
        path = os.path.join(self.temp_dir.name, "test.graphml")

        self.exporter.export_graphml(self.builder, path)

        self.assertTrue(os.path.exists(path))

        graph = nx.read_graphml(path)

        self.assertEqual(graph.number_of_nodes(), 2)
        self.assertEqual(graph.number_of_edges(), 1)

    def test_export_json(self):
        path = os.path.join(self.temp_dir.name, "test.json")

        self.exporter.export_json(self.builder, path)

        self.assertTrue(os.path.exists(path))

        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["edges"]), 1)

    def test_exported_json_preserves_relationship(self):
        path = os.path.join(self.temp_dir.name, "test.json")

        self.exporter.export_json(self.builder, path)

        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        edge = data["edges"][0]

        self.assertEqual(edge["relationship_type"], "PLACED")


if __name__ == "__main__":
    unittest.main()

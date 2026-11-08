
import unittest

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_evolver import GraphEvolver


class TestGraphEvolver(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder()
        self.evolver = GraphEvolver(self.builder)

        self.evolver.add_entity(
            "customer_1",
            "Customer",
            name="John"
        )

        self.evolver.add_entity(
            "order_1",
            "Order",
            status="Pending"
        )

    def test_add_new_entity(self):
        result = self.evolver.add_entity(
            "product_1",
            "Product",
            name="Laptop"
        )

        self.assertEqual(result, "ENTITY_ADDED")
        self.assertIn("product_1", self.builder.graph)

    def test_duplicate_entity_updates_existing_entity(self):
        result = self.evolver.add_entity(
            "customer_1",
            "Customer",
            city="Chennai"
        )

        self.assertEqual(result, "ENTITY_UPDATED")
        self.assertEqual(
            self.builder.graph.nodes["customer_1"]["city"],
            "Chennai"
        )

        self.assertEqual(self.builder.graph.number_of_nodes(), 2)

    def test_entity_type_mismatch(self):
        with self.assertRaises(ValueError):
            self.evolver.add_entity(
                "customer_1",
                "Product",
                name="Laptop"
            )

    def test_update_entity(self):
        result = self.evolver.update_entity(
            "customer_1",
            city="Chennai"
        )

        self.assertEqual(result, "ENTITY_UPDATED")
        self.assertEqual(
            self.builder.graph.nodes["customer_1"]["city"],
            "Chennai"
        )

    def test_update_missing_entity(self):
        with self.assertRaises(ValueError):
            self.evolver.update_entity(
                "unknown_entity",
                city="Chennai"
            )

    def test_add_relationship(self):
        result = self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        self.assertEqual(result, "RELATIONSHIP_ADDED")
        self.assertEqual(self.builder.graph.number_of_edges(), 1)

    def test_duplicate_relationship_prevention(self):
        self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        result = self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        self.assertEqual(result, "RELATIONSHIP_ALREADY_EXISTS")
        self.assertEqual(self.builder.graph.number_of_edges(), 1)

    def test_relationship_requires_existing_entities(self):
        with self.assertRaises(ValueError):
            self.evolver.add_relationship(
                "customer_1",
                "unknown_order",
                "PLACED"
            )

    def test_update_relationship(self):
        self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED",
            status="Pending"
        )

        result = self.evolver.update_relationship(
            "customer_1",
            "order_1",
            "PLACED",
            status="Confirmed"
        )

        self.assertEqual(result, "RELATIONSHIP_UPDATED")

        edge_data = self.builder.graph.get_edge_data(
            "customer_1",
            "order_1"
        )

        self.assertEqual(
            edge_data[0]["status"],
            "Confirmed"
        )

    def test_update_missing_relationship(self):
        with self.assertRaises(ValueError):
            self.evolver.update_relationship(
                "customer_1",
                "order_1",
                "PLACED",
                status="Confirmed"
            )

    def test_evolution_history(self):
        self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        history = self.evolver.get_evolution_history()

        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["operation"], "ADD_ENTITY")
        self.assertEqual(history[2]["operation"], "ADD_RELATIONSHIP")
        self.assertIn("timestamp", history[0])

    def test_evolution_summary(self):
        self.evolver.add_relationship(
            "customer_1",
            "order_1",
            "PLACED"
        )

        summary = self.evolver.get_evolution_summary()

        self.assertEqual(summary["total_changes"], 3)
        self.assertEqual(
            summary["operation_counts"]["ADD_ENTITY"],
            2
        )
        self.assertEqual(
            summary["operation_counts"]["ADD_RELATIONSHIP"],
            1
        )


if __name__ == "__main__":
    unittest.main()

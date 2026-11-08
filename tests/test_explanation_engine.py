
import unittest
import pandas as pd

from src.explainability.explanation_engine import ExplanationEngine
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder


class TestExplanationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ExplanationEngine()

        self.reference_data = pd.DataFrame({
            "delivery_delay_days": [1, 2, 2, 3, 2, 1, 3, 2],
            "delivery_duration_days": [4, 5, 5, 6, 5, 4, 6, 5]
        })

        self.observation = pd.Series({
            "delivery_delay_days": 15,
            "delivery_duration_days": 5
        })

        self.detection_report = {
            "dataset_name": "olist_orders",
            "method": "IsolationForest",
            "anomalies": [
                {
                    "row_index": 10,
                    "anomaly_score": -0.25
                }
            ]
        }

    def test_explain_anomaly(self):
        result = self.engine.explain_anomaly(
            self.observation,
            self.reference_data,
            self.detection_report
        )

        self.assertEqual(
            result["explanation_type"],
            "ANOMALY"
        )
        self.assertIn("feature_analysis", result)
        self.assertIn("anomaly_analysis", result)

    def test_anomaly_contains_feature_evidence(self):
        result = self.engine.explain_anomaly(
            self.observation,
            self.reference_data,
            self.detection_report
        )

        self.assertGreater(
            result["feature_analysis"]["unusual_feature_count"],
            0
        )

    def test_explain_relationship(self):
        builder = KnowledgeGraphBuilder()

        builder.add_entity("customer:1", "Customer")
        builder.add_entity("order:1", "Order")

        builder.add_relationship(
            "customer:1",
            "order:1",
            "PLACED"
        )

        engine = ExplanationEngine(graph_builder=builder)

        result = engine.explain_relationship(
            "customer:1",
            "order:1"
        )

        self.assertEqual(
            result["explanation_type"],
            "GRAPH_RELATIONSHIP"
        )

        self.assertEqual(
            result["graph_analysis"]["relationship_count"],
            1
        )

    def test_explain_path(self):
        builder = KnowledgeGraphBuilder()

        builder.add_entity("customer:1", "Customer")
        builder.add_entity("order:1", "Order")
        builder.add_entity("product:1", "Product")

        builder.add_relationship(
            "customer:1",
            "order:1",
            "PLACED"
        )

        builder.add_relationship(
            "order:1",
            "product:1",
            "CONTAINS"
        )

        engine = ExplanationEngine(graph_builder=builder)

        result = engine.explain_path([
            "customer:1",
            "order:1",
            "product:1"
        ])

        self.assertEqual(
            result["explanation_type"],
            "GRAPH_PATH"
        )

        self.assertEqual(
            result["graph_analysis"]["path_length"],
            2
        )

    def test_relationship_without_graph_builder(self):
        with self.assertRaises(RuntimeError):
            self.engine.explain_relationship(
                "customer:1",
                "order:1"
            )

    def test_path_without_graph_builder(self):
        with self.assertRaises(RuntimeError):
            self.engine.explain_path([
                "customer:1",
                "order:1"
            ])


if __name__ == "__main__":
    unittest.main()

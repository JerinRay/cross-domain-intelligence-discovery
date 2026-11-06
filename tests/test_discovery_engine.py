
import unittest
import pandas as pd

from src.discovery.duplicate_detector import DuplicateDetector
from src.discovery.similarity_analyzer import SimilarityAnalyzer
from src.discovery.join_key_detector import JoinKeyDetector
from src.discovery.relationship_discoverer import RelationshipDiscoverer
from src.discovery.engine import DiscoveryEngine


class TestDiscoveryEngine(unittest.TestCase):

    def setUp(self):
        self.orders = pd.DataFrame({
            "order_id": ["A101", "A102", "A103", "A104"],
            "customer_id": ["C1", "C2", "C3", "C4"],
            "order_status": ["delivered", "shipped", "delivered", "cancelled"]
        })

        self.items = pd.DataFrame({
            "order_id": ["A101", "A101", "A102", "A103", "A104"],
            "order_item_id": [1, 2, 1, 1, 1],
            "seller_id": ["S1", "S2", "S1", "S3", "S4"]
        })

    def test_duplicate_detector(self):
        detector = DuplicateDetector()
        result = detector.analyze(self.orders, "orders")

        self.assertEqual(result["duplicate_rows"], 0)
        self.assertEqual(result["total_rows"], 4)

    def test_duplicate_detector_finds_duplicates(self):
        data = pd.DataFrame({
            "id": [1, 2, 2, 3]
        })

        detector = DuplicateDetector()
        result = detector.analyze(data)

        self.assertEqual(result["duplicate_rows"], 1)

    def test_similarity_analyzer(self):
        analyzer = SimilarityAnalyzer(sample_size=100)

        result = analyzer.analyze(
            self.orders,
            self.items,
            "orders",
            "items"
        )

        self.assertGreater(
            len(result["similarity_candidates"]), 0
        )

        matching_columns = [
            item for item in result["similarity_candidates"]
            if item["column_a"] == "order_id"
            and item["column_b"] == "order_id"
        ]

        self.assertTrue(matching_columns)

    def test_join_key_detector(self):
        detector = JoinKeyDetector(sample_size=100)

        result = detector.analyze(
            self.orders,
            self.items,
            "orders",
            "items"
        )

        candidates = result["join_key_candidates"]

        matching_candidates = [
            item for item in candidates
            if item["column_a"] == "order_id"
            and item["column_b"] == "order_id"
        ]

        self.assertTrue(matching_candidates)

    def test_relationship_discoverer(self):
        join_result = {
            "dataset_a": "orders",
            "dataset_b": "items",
            "join_key_candidates": [{
                "column_a": "order_id",
                "column_b": "order_id",
                "name_similarity": 1.0,
                "overlap_coefficient": 1.0,
                "uniqueness_ratio_a": 1.0,
                "uniqueness_ratio_b": 0.8
            }]
        }

        discoverer = RelationshipDiscoverer()
        result = discoverer.analyze(join_result)

        self.assertEqual(
            result["relationships_discovered"], 1
        )

        self.assertEqual(
            result["relationships"][0]["relationship_type"],
            "ONE_TO_MANY"
        )

        self.assertEqual(
            result["relationships"][0]["validation_status"],
            "UNVERIFIED"
        )

    def test_discovery_engine(self):
        engine = DiscoveryEngine(sample_size=100)

        report = engine.analyze(
            self.orders,
            self.items,
            "orders",
            "items"
        )

        self.assertEqual(report["status"], "SUCCESS")

        self.assertIn("duplicate_detection", report)
        self.assertIn("similarity_analysis", report)
        self.assertIn("join_key_detection", report)
        self.assertIn("relationship_discovery", report)

    def test_empty_dataset_rejected(self):
        engine = DiscoveryEngine()

        empty = pd.DataFrame()

        with self.assertRaises(ValueError):
            engine.analyze(
                empty,
                self.items,
                "empty",
                "items"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)

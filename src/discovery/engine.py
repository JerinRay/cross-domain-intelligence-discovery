
import json
import os
from datetime import datetime, timezone

from src.discovery.duplicate_detector import DuplicateDetector
from src.discovery.similarity_analyzer import SimilarityAnalyzer
from src.discovery.join_key_detector import JoinKeyDetector
from src.discovery.relationship_discoverer import RelationshipDiscoverer


class DiscoveryEngine:
    """
    Central engine integrating duplicate detection,
    dataset similarity, join-key detection and
    relationship discovery.
    """

    def __init__(self, sample_size=10000):
        self.duplicate_detector = DuplicateDetector()

        self.similarity_analyzer = SimilarityAnalyzer(
            sample_size=min(sample_size, 5000)
        )

        self.join_key_detector = JoinKeyDetector(
            sample_size=sample_size
        )

        self.relationship_discoverer = RelationshipDiscoverer()

    def analyze(self, dataset_a, dataset_b,
                dataset_a_name="dataset_a",
                dataset_b_name="dataset_b"):

        if dataset_a.empty or dataset_b.empty:
            raise ValueError("Both datasets must contain records.")

        if not hasattr(dataset_a, "columns") or not hasattr(dataset_b, "columns"):
            raise TypeError("Both inputs must be pandas DataFrames.")

        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Duplicate detection
        duplicate_result_a = self.duplicate_detector.analyze(
            dataset_a, dataset_a_name
        )

        duplicate_result_b = self.duplicate_detector.analyze(
            dataset_b, dataset_b_name
        )

        # 2. Dataset similarity
        similarity_result = self.similarity_analyzer.analyze(
            dataset_a,
            dataset_b,
            dataset_a_name,
            dataset_b_name
        )

        # 3. Join key detection
        join_key_result = self.join_key_detector.analyze(
            dataset_a,
            dataset_b,
            dataset_a_name,
            dataset_b_name
        )

        # 4. Relationship discovery
        relationship_result = self.relationship_discoverer.analyze(
            join_key_result,
            similarity_result
        )

        return {
            "engine": "Cross-Domain Discovery Engine",
            "generated_at": timestamp,
            "status": "SUCCESS",
            "datasets": {
                "dataset_a": dataset_a_name,
                "dataset_b": dataset_b_name
            },
            "duplicate_detection": {
                dataset_a_name: duplicate_result_a,
                dataset_b_name: duplicate_result_b
            },
            "similarity_analysis": similarity_result,
            "join_key_detection": join_key_result,
            "relationship_discovery": relationship_result
        }

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {
                str(key): DiscoveryEngine._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                DiscoveryEngine._json_safe(item)
                for item in value
            ]

        if hasattr(value, "item"):
            return DiscoveryEngine._json_safe(value.item())

        if isinstance(value, float):
            import math
            if not math.isfinite(value):
                return None

        return value

    def save_report(self, report, output_dir="logs/discovery"):
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"discovery_report_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        safe_report = self._json_safe(report)

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
                safe_report,
                file,
                indent=4,
                ensure_ascii=False
            )

        return filepath

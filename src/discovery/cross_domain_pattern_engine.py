
import json
import os
from datetime import datetime, timezone
from itertools import combinations

import pandas as pd

from src.discovery.engine import DiscoveryEngine


class CrossDomainPatternEngine:
    """
    Analyzes multiple datasets pairwise and consolidates
    cross-domain relationship hypotheses into an intelligence report.

    Discovered relationships are candidates, not verified joins.
    """

    def __init__(self, sample_size=10000):
        self.discovery_engine = DiscoveryEngine(
            sample_size=sample_size
        )

    def analyze(self, datasets):
        if not isinstance(datasets, dict):
            raise TypeError("datasets must be a dictionary.")

        if len(datasets) < 2:
            raise ValueError("At least two datasets are required.")

        for name, dataframe in datasets.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Dataset names must be non-empty strings.")

            if not isinstance(dataframe, pd.DataFrame):
                raise TypeError(
                    f"Dataset '{name}' must be a pandas DataFrame."
                )

            if dataframe.empty:
                raise ValueError(
                    f"Dataset '{name}' must contain records."
                )

        pair_results = []
        all_relationships = []

        dataset_names = sorted(datasets.keys())

        for name_a, name_b in combinations(dataset_names, 2):
            result = self.discovery_engine.analyze(
                datasets[name_a],
                datasets[name_b],
                dataset_a_name=name_a,
                dataset_b_name=name_b
            )

            relationships = result["relationship_discovery"][
                "relationships"
            ]

            pair_results.append({
                "dataset_a": name_a,
                "dataset_b": name_b,
                "candidate_count": len(relationships),
                "relationships": relationships
            })

            all_relationships.extend(relationships)

        confidence_counts = {
            level: sum(
                item["confidence"] == level
                for item in all_relationships
            )
            for level in ("HIGH", "MEDIUM", "LOW")
        }

        connected_pairs = sum(
            result["candidate_count"] > 0
            for result in pair_results
        )

        return {
            "engine": "Cross-Domain Pattern Discovery Engine",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "SUCCESS",
            "dataset_count": len(datasets),
            "dataset_names": dataset_names,
            "dataset_pair_count": len(pair_results),
            "connected_dataset_pair_count": connected_pairs,
            "total_relationship_candidates": len(all_relationships),
            "confidence_summary": confidence_counts,
            "dataset_pair_analysis": pair_results,
            "disclaimer": (
                "Relationships are discovery hypotheses based on "
                "sampled value overlap, column-name similarity and "
                "uniqueness. They are not verified joins or evidence "
                "of causation."
            )
        }

    @staticmethod
    def save_report(report, output_dir="logs/cross_domain"):
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(
            output_dir,
            f"cross_domain_report_{timestamp}.json"
        )

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        return filepath


import pandas as pd
from difflib import SequenceMatcher


class JoinKeyDetector:
    """
    Discovers potential join keys between two datasets using:
    - Column name similarity
    - Data type compatibility
    - Key uniqueness
    - Null percentage
    - Sampled value overlap

    This module identifies candidates only.
    It does not perform automatic joins.
    """

    def __init__(self, sample_size=10000, name_threshold=0.5):
        self.sample_size = sample_size
        self.name_threshold = name_threshold

    @staticmethod
    def _normalize_name(name):
        return "".join(
            char.lower()
            for char in str(name)
            if char.isalnum()
        )

    @staticmethod
    def _name_similarity(name_a, name_b):
        return round(
            SequenceMatcher(
                None,
                JoinKeyDetector._normalize_name(name_a),
                JoinKeyDetector._normalize_name(name_b)
            ).ratio(),
            3
        )

    def _column_statistics(self, series):
        non_missing = series.dropna()

        if non_missing.empty:
            return {
                "row_count": len(series),
                "non_missing_count": 0,
                "null_percentage": 100.0,
                "uniqueness_ratio": 0.0,
                "unique_count": 0
            }

        unique_count = int(non_missing.nunique())

        return {
            "row_count": int(len(series)),
            "non_missing_count": int(len(non_missing)),
            "null_percentage": round(
                series.isna().mean() * 100, 2
            ),
            "uniqueness_ratio": round(
                unique_count / len(non_missing), 4
            ),
            "unique_count": unique_count
        }

    def _sample_values(self, series):
        values = series.dropna()

        if len(values) > self.sample_size:
            values = values.sample(
                n=self.sample_size,
                random_state=42
            )

        return set(values.astype(str).tolist())

    def analyze(self, dataset_a, dataset_b,
                dataset_a_name="dataset_a",
                dataset_b_name="dataset_b"):

        if not isinstance(dataset_a, pd.DataFrame):
            raise TypeError("dataset_a must be a pandas DataFrame.")

        if not isinstance(dataset_b, pd.DataFrame):
            raise TypeError("dataset_b must be a pandas DataFrame.")

        if dataset_a.empty or dataset_b.empty:
            raise ValueError("Both datasets must contain records.")

        candidates = []

        for column_a in dataset_a.columns:
            stats_a = self._column_statistics(dataset_a[column_a])

            if stats_a["non_missing_count"] == 0:
                continue

            values_a = self._sample_values(dataset_a[column_a])

            for column_b in dataset_b.columns:
                stats_b = self._column_statistics(dataset_b[column_b])

                if stats_b["non_missing_count"] == 0:
                    continue

                name_score = self._name_similarity(
                    column_a, column_b
                )

                type_a = str(dataset_a[column_a].dtype)
                type_b = str(dataset_b[column_b].dtype)

                type_match = type_a == type_b

                # Avoid comparing incompatible data types.
                if not type_match:
                    continue

                values_b = self._sample_values(dataset_b[column_b])

                if not values_a or not values_b:
                    continue

                intersection_count = len(values_a & values_b)

                overlap_a = round(
                    intersection_count / len(values_a), 4
                )

                overlap_b = round(
                    intersection_count / len(values_b), 4
                )

                overlap_coefficient = round(
                    intersection_count /
                    min(len(values_a), len(values_b)),
                    4
                )

                if (
                    name_score >= self.name_threshold
                    or overlap_coefficient > 0
                ):

                    candidates.append({
                        "column_a": str(column_a),
                        "column_b": str(column_b),
                        "name_similarity": name_score,
                        "data_type": type_a,
                        "uniqueness_ratio_a": (
                            stats_a["uniqueness_ratio"]
                        ),
                        "uniqueness_ratio_b": (
                            stats_b["uniqueness_ratio"]
                        ),
                        "null_percentage_a": (
                            stats_a["null_percentage"]
                        ),
                        "null_percentage_b": (
                            stats_b["null_percentage"]
                        ),
                        "unique_values_a": stats_a["unique_count"],
                        "unique_values_b": stats_b["unique_count"],
                        "overlap_a": overlap_a,
                        "overlap_b": overlap_b,
                        "overlap_coefficient": overlap_coefficient,
                        "sampled_values_a": len(values_a),
                        "sampled_values_b": len(values_b)
                    })

        candidates.sort(
            key=lambda item: (
                item["overlap_coefficient"],
                item["name_similarity"],
                min(
                    item["uniqueness_ratio_a"],
                    item["uniqueness_ratio_b"]
                )
            ),
            reverse=True
        )

        return {
            "dataset_a": dataset_a_name,
            "dataset_b": dataset_b_name,
            "candidate_count": len(candidates),
            "join_key_candidates": candidates
        }

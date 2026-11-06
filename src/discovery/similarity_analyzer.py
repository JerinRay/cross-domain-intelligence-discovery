
import pandas as pd
from difflib import SequenceMatcher


class SimilarityAnalyzer:
    """
    Compares two datasets to identify potentially related columns
    using column names, data types, and sample value overlap.

    This module identifies candidate similarities only.
    It does not automatically join datasets.
    """

    def __init__(self, sample_size=5000):
        self.sample_size = sample_size

    @staticmethod
    def _normalize_name(name):
        return "".join(
            character.lower()
            for character in str(name)
            if character.isalnum()
        )

    @staticmethod
    def _name_similarity(name_a, name_b):
        return round(
            SequenceMatcher(
                None,
                SimilarityAnalyzer._normalize_name(name_a),
                SimilarityAnalyzer._normalize_name(name_b)
            ).ratio(),
            3
        )

    def _value_overlap(self, series_a, series_b):
        values_a = series_a.dropna()
        values_b = series_b.dropna()

        if values_a.empty or values_b.empty:
            return 0.0

        values_a = values_a.astype(str).head(self.sample_size)
        values_b = values_b.astype(str).head(self.sample_size)

        set_a = set(values_a)
        set_b = set(values_b)

        if not set_a or not set_b:
            return 0.0

        overlap = len(set_a.intersection(set_b))
        denominator = min(len(set_a), len(set_b))

        return round(overlap / denominator, 4)

    def analyze(self, dataset_a, dataset_b,
                dataset_a_name="dataset_a",
                dataset_b_name="dataset_b"):

        if not isinstance(dataset_a, pd.DataFrame):
            raise TypeError("dataset_a must be a pandas DataFrame.")

        if not isinstance(dataset_b, pd.DataFrame):
            raise TypeError("dataset_b must be a pandas DataFrame.")

        if dataset_a.empty or dataset_b.empty:
            raise ValueError("Both datasets must contain records.")

        similarities = []

        for column_a in dataset_a.columns:
            for column_b in dataset_b.columns:

                name_score = self._name_similarity(
                    column_a, column_b
                )

                type_a = str(dataset_a[column_a].dtype)
                type_b = str(dataset_b[column_b].dtype)

                type_match = type_a == type_b

                value_overlap = self._value_overlap(
                    dataset_a[column_a],
                    dataset_b[column_b]
                )

                if name_score >= 0.5 or value_overlap > 0:

                    similarities.append({
                        "column_a": str(column_a),
                        "column_b": str(column_b),
                        "name_similarity": name_score,
                        "data_type_a": type_a,
                        "data_type_b": type_b,
                        "data_type_match": type_match,
                        "value_overlap": value_overlap
                    })

        similarities.sort(
            key=lambda item: (
                item["value_overlap"],
                item["name_similarity"],
                item["data_type_match"]
            ),
            reverse=True
        )

        return {
            "dataset_a": dataset_a_name,
            "dataset_b": dataset_b_name,
            "columns_compared": (
                len(dataset_a.columns) * len(dataset_b.columns)
            ),
            "similarity_candidates": similarities
        }


import unittest

import pandas as pd

from src.explainability.feature_explainer import FeatureExplainer


class TestFeatureExplainer(unittest.TestCase):

    def setUp(self):
        self.explainer = FeatureExplainer(
            deviation_threshold=1.5
        )

        self.reference_data = pd.DataFrame({
            "delivery_delay_days": [
                0, 1, 0, 2, 1, 0, 1, 2, 0, 1
            ],
            "approval_delay_hours": [
                1, 2, 1, 3, 2, 1, 2, 3, 1, 2
            ]
        })

    def test_detects_unusual_feature(self):
        observation = pd.Series({
            "delivery_delay_days": 20,
            "approval_delay_hours": 2
        })

        result = self.explainer.explain(
            observation,
            self.reference_data
        )

        self.assertEqual(
            result["unusual_feature_count"], 1
        )

        self.assertEqual(
            result["explanations"][0]["feature"],
            "delivery_delay_days"
        )

    def test_returns_no_unusual_features(self):
        observation = pd.Series({
            "delivery_delay_days": 1,
            "approval_delay_hours": 2
        })

        result = self.explainer.explain(
            observation,
            self.reference_data
        )

        self.assertEqual(
            result["unusual_feature_count"], 0
        )

    def test_handles_missing_observation(self):
        observation = pd.Series({
            "delivery_delay_days": None,
            "approval_delay_hours": 2
        })

        result = self.explainer.explain(
            observation,
            self.reference_data
        )

        self.assertEqual(
            result["unusual_feature_count"], 0
        )

    def test_rejects_wrong_observation_type(self):
        with self.assertRaises(TypeError):
            self.explainer.explain(
                {"delivery_delay_days": 20},
                self.reference_data
            )

    def test_rejects_empty_reference_data(self):
        with self.assertRaises(ValueError):
            self.explainer.explain(
                pd.Series({"delivery_delay_days": 20}),
                pd.DataFrame()
            )

    def test_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            FeatureExplainer(deviation_threshold=0)


if __name__ == "__main__":
    unittest.main()

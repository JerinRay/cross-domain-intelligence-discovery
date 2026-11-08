
import unittest

from src.explainability.anomaly_explainer import AnomalyExplainer


class TestAnomalyExplainer(unittest.TestCase):

    def setUp(self):
        self.explainer = AnomalyExplainer()

        self.detection_report = {
            "dataset_name": "olist_orders",
            "method": "Isolation Forest",
            "anomalies": [
                {
                    "row_index": "100",
                    "anomaly_score": -0.25
                }
            ]
        }

        self.feature_explanation = {
            "explanations": [
                {
                    "feature": "delivery_delay_days",
                    "observed_value": 20.0,
                    "reference_median": 1.0,
                    "direction": "higher",
                    "deviation_ratio": 19.0,
                    "evidence": (
                        "delivery_delay_days is higher "
                        "than the reference median"
                    )
                }
            ]
        }

    def test_generates_anomaly_summary(self):
        result = self.explainer.explain(
            self.detection_report,
            self.feature_explanation
        )

        self.assertIn("1 potential anomalies", result["summary"])
        self.assertEqual(result["anomaly_count"], 1)

    def test_includes_feature_evidence(self):
        result = self.explainer.explain(
            self.detection_report,
            self.feature_explanation
        )

        self.assertEqual(
            result["evidence"][0]["feature"],
            "delivery_delay_days"
        )

    def test_handles_no_anomalies(self):
        report = {
            "dataset_name": "test_dataset",
            "method": "Isolation Forest",
            "anomalies": []
        }

        result = self.explainer.explain(
            report,
            self.feature_explanation
        )

        self.assertEqual(result["anomaly_count"], 0)
        self.assertIn("No anomalies", result["summary"])

    def test_handles_missing_feature_evidence(self):
        result = self.explainer.explain(
            self.detection_report,
            {"explanations": []}
        )

        self.assertEqual(
            result["feature_evidence_count"], 0
        )
        self.assertIn(
            "no unusual feature evidence",
            result["summary"]
        )

    def test_rejects_invalid_detection_report(self):
        with self.assertRaises(TypeError):
            self.explainer.explain(
                [],
                self.feature_explanation
            )

    def test_rejects_missing_required_field(self):
        with self.assertRaises(ValueError):
            self.explainer.explain(
                {"dataset_name": "test"},
                self.feature_explanation
            )

    def test_rejects_invalid_feature_explanation(self):
        with self.assertRaises(TypeError):
            self.explainer.explain(
                self.detection_report,
                []
            )


if __name__ == "__main__":
    unittest.main()

import unittest
import pandas as pd

from src.anomaly_detection.anomaly_investigator import (
    AnomalyInvestigator
)


class TestAnomalyInvestigator(unittest.TestCase):

    def setUp(self):

        self.original_data = pd.DataFrame({
            "order_id": ["ORD001", "ORD002", "ORD003"],
            "order_status": [
                "delivered",
                "delivered",
                "shipped"
            ]
        })

        self.features = pd.DataFrame({
            "delivery_duration_days": [
                5.0, 45.0, 8.0
            ]
        })

        self.detection_report = {
            "dataset_name": "sample_orders",
            "anomalies": [
                {
                    "row_index": "1",
                    "anomaly_score": -0.15
                }
            ]
        }

        self.investigator = AnomalyInvestigator()

    def test_original_order_details_preserved(self):

        report = self.investigator.investigate(
            self.original_data,
            self.features,
            self.detection_report
        )

        self.assertEqual(
            report.iloc[0]["order_id"],
            "ORD002"
        )

    def test_anomaly_score_preserved(self):

        report = self.investigator.investigate(
            self.original_data,
            self.features,
            self.detection_report
        )

        self.assertEqual(
            report.iloc[0]["anomaly_score"],
            -0.15
        )

    def test_feature_values_preserved(self):

        report = self.investigator.investigate(
            self.original_data,
            self.features,
            self.detection_report
        )

        self.assertEqual(
            report.iloc[0]["delivery_duration_days"],
            45.0
        )

    def test_report_row_count(self):

        report = self.investigator.investigate(
            self.original_data,
            self.features,
            self.detection_report
        )

        self.assertEqual(len(report), 1)

    def test_empty_anomalies(self):

        detection_report = {
            "dataset_name": "sample_orders",
            "anomalies": []
        }

        report = self.investigator.investigate(
            self.original_data,
            self.features,
            detection_report
        )

        self.assertTrue(report.empty)

    def test_invalid_original_data(self):

        with self.assertRaises(TypeError):
            self.investigator.investigate(
                [1, 2, 3],
                self.features,
                self.detection_report
            )

    def test_invalid_features(self):

        with self.assertRaises(TypeError):
            self.investigator.investigate(
                self.original_data,
                [1, 2, 3],
                self.detection_report
            )

    def test_mismatched_indexes(self):

        wrong_features = self.features.copy()
        wrong_features.index = [10, 11, 12]

        with self.assertRaises(ValueError):
            self.investigator.investigate(
                self.original_data,
                wrong_features,
                self.detection_report
            )

    def test_unknown_anomaly_index(self):

        invalid_report = {
            "dataset_name": "sample_orders",
            "anomalies": [
                {
                    "row_index": "999",
                    "anomaly_score": -0.15
                }
            ]
        }

        with self.assertRaises(ValueError):
            self.investigator.investigate(
                self.original_data,
                self.features,
                invalid_report
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
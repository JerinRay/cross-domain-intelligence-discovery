import unittest
import pandas as pd

from src.anomaly_detection.isolation_forest_detector import (
    IsolationForestDetector
)


class TestIsolationForestDetector(unittest.TestCase):

    def setUp(self):

        self.detector = IsolationForestDetector(
            contamination=0.05,
            random_state=42
        )

        self.sample_data = pd.DataFrame({
            "order_value": [
                100, 110, 105, 115, 120,
                108, 112, 118, 125, 130,
                107, 113, 119, 122, 128,
                109, 114, 117, 123, 126,
                5000
            ],
            "delivery_days": [
                2, 3, 2, 4, 3,
                2, 3, 4, 3, 2,
                3, 2, 4, 3, 2,
                3, 4, 2, 3, 2,
                100
            ]
        })

    def test_detector_identifies_anomalies(self):

        report = self.detector.analyze(
            self.sample_data,
            dataset_name="sample_ecommerce"
        )

        self.assertGreater(
            report["anomaly_count"],
            0
        )

    def test_report_details(self):

        report = self.detector.analyze(
            self.sample_data,
            dataset_name="sample_ecommerce"
        )

        self.assertEqual(
            report["dataset_name"],
            "sample_ecommerce"
        )

        self.assertEqual(
            report["method"],
            "Isolation Forest"
        )

        self.assertEqual(
            report["rows_analyzed"],
            21
        )

    def test_numeric_features_detected(self):

        report = self.detector.analyze(
            self.sample_data
        )

        self.assertIn(
            "order_value",
            report["features_used"]
        )

        self.assertIn(
            "delivery_days",
            report["features_used"]
        )

    def test_missing_values_handled(self):

        data = self.sample_data.copy()

        data.loc[0, "order_value"] = None

        report = self.detector.analyze(data)

        self.assertEqual(
            report["rows_analyzed"],
            21
        )

    def test_empty_dataset(self):

        with self.assertRaises(ValueError):
            self.detector.analyze(pd.DataFrame())

    def test_invalid_input(self):

        with self.assertRaises(TypeError):
            self.detector.analyze([1, 2, 3])

    def test_no_numeric_features(self):

        data = pd.DataFrame({
            "customer_name": [
                "A", "B", "C", "D", "E"
            ]
        })

        with self.assertRaises(ValueError):
            self.detector.analyze(data)

    def test_insufficient_rows(self):

        data = pd.DataFrame({
            "amount": [10, 20, 30, 40]
        })

        with self.assertRaises(ValueError):
            self.detector.analyze(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
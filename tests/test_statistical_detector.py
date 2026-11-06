
import unittest
import pandas as pd

from src.anomaly_detection.statistical_detector import (
    StatisticalAnomalyDetector
)


class TestStatisticalAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = StatisticalAnomalyDetector()

        self.sample_data = pd.DataFrame({
            "delivery_days": [
                2, 3, 3, 4, 4, 5, 5, 6, 7, 45
            ],
            "order_value": [
                100, 120, 110, 130, 125,
                140, 135, 150, 145, 2000
            ]
        })

    def test_detect_delivery_anomaly(self):
        report = self.detector.analyze(
            self.sample_data,
            dataset_name="sample_ecommerce"
        )

        delivery_result = next(
            item for item in report["column_results"]
            if item["column"] == "delivery_days"
        )

        self.assertIn(
            45.0,
            delivery_result["outlier_values"]
        )

    def test_detect_order_value_anomaly(self):
        report = self.detector.analyze(
            self.sample_data,
            dataset_name="sample_ecommerce"
        )

        order_result = next(
            item for item in report["column_results"]
            if item["column"] == "order_value"
        )

        self.assertIn(
            2000.0,
            order_result["outlier_values"]
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

        self.assertEqual(report["method"], "IQR")
        self.assertEqual(report["columns_analyzed"], 2)
        self.assertEqual(report["total_outliers"], 2)

    def test_empty_dataset(self):
        empty_data = pd.DataFrame()

        with self.assertRaises(ValueError):
            self.detector.analyze(empty_data)

    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            self.detector.analyze([1, 2, 3])


if __name__ == "__main__":
    unittest.main(verbosity=2)

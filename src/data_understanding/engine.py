
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

from .profiler import DatasetProfiler
from .column_analyzer import ColumnAnalyzer
from .correlation_analyzer import CorrelationAnalyzer
from .outlier_detector import OutlierDetector
from .distribution_analyzer import DistributionAnalyzer


class DataUnderstandingEngine:

    def __init__(self, sample_size=100_000):
        self.profiler = DatasetProfiler(sample_size=sample_size)
        self.column_analyzer = ColumnAnalyzer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.outlier_detector = OutlierDetector(sample_size=sample_size)
        self.distribution_analyzer = DistributionAnalyzer(
            sample_size=sample_size
        )

    @staticmethod
    def _json_safe(value):

        if isinstance(value, dict):
            return {
                str(key): DataUnderstandingEngine._json_safe(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                DataUnderstandingEngine._json_safe(item)
                for item in value
            ]

        if isinstance(value, np.ndarray):
            return DataUnderstandingEngine._json_safe(value.tolist())

        if isinstance(value, np.generic):
            return DataUnderstandingEngine._json_safe(value.item())

        if isinstance(value, (pd.Timestamp, datetime)):
            return value.isoformat()

        if value is pd.NA or value is pd.NaT:
            return None

        if isinstance(value, float) and not np.isfinite(value):
            return None

        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    def analyze_dataset(self, data, dataset_name="unnamed_dataset"):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot analyze an empty dataset.")

        print(f"\nStarting analysis: {dataset_name}")

        report = {
            "dataset_name": dataset_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "results": {}
        }

        analyzers = [
            ("profiling", self.profiler.profile_dataset),
            ("column_analysis", self.column_analyzer.analyze_columns),
            ("correlation_analysis",
             self.correlation_analyzer.analyze_correlations),
            ("outlier_analysis", self.outlier_detector.detect_outliers),
            ("distribution_analysis",
             self.distribution_analyzer.analyze_distributions),
        ]

        errors = []

        for name, method in analyzers:
            try:
                print(f"Running {name}...")
                report["results"][name] = method(data)
                print(f"Completed {name}.")

            except Exception as error:
                errors.append({
                    "analysis": name,
                    "error": str(error)
                })

        if errors:
            report["status"] = (
                "PARTIAL_SUCCESS" if report["results"] else "FAILED"
            )
            report["errors"] = errors

        return self._json_safe(report)

    def save_report(self, report, output_dir="logs/data_understanding"):

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        dataset_name = report.get("dataset_name", "dataset")
        safe_name = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in dataset_name
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"{safe_name}_{timestamp}.json"

        with report_file.open("w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False,
                allow_nan=False
            )

        print(f"Unified report saved: {report_file}")
        return report_file

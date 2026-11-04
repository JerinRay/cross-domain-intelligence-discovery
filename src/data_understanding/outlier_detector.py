
import pandas as pd
import numpy as np


class OutlierDetector:

    def __init__(self, sample_size=100_000):
        self.sample_size = sample_size

    def detect_outliers(self, data: pd.DataFrame):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot analyze an empty dataset.")

        if len(data) > self.sample_size:
            sample = data.sample(
                n=self.sample_size,
                random_state=42
            )
            sampling_used = True
        else:
            sample = data
            sampling_used = False

        numeric_data = sample.select_dtypes(
            include=[np.number]
        )

        if numeric_data.empty:
            return {
                "status": "NO_NUMERICAL_COLUMNS",
                "message": "No numerical columns available.",
                "sampling_used": sampling_used,
                "outliers": {}
            }

        results = {}

        for column in numeric_data.columns:

            series = numeric_data[column].dropna()

            if series.empty or series.nunique() < 2:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)

            iqr = q3 - q1

            if iqr == 0:
                continue

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            outlier_mask = (
                (series < lower_bound)
                | (series > upper_bound)
            )

            outlier_count = int(outlier_mask.sum())

            results[column] = {
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": outlier_count,
                "outlier_percentage": round(
                    (outlier_count / len(series)) * 100,
                    2
                ),
                "minimum": float(series.min()),
                "maximum": float(series.max())
            }

        return {
            "status": "SUCCESS",
            "sampling_used": sampling_used,
            "outliers": results
        }

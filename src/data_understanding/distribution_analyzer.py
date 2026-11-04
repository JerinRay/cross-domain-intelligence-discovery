
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis


class DistributionAnalyzer:

    def __init__(self, sample_size=100_000):
        self.sample_size = sample_size

    def analyze_distributions(self, data: pd.DataFrame):

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
                "distributions": {}
            }

        results = {}

        for column in numeric_data.columns:

            series = numeric_data[column].dropna()

            if series.empty:
                continue

            mean_value = float(series.mean())
            median_value = float(series.median())

            skewness = (
                float(skew(series))
                if series.nunique() > 2 else 0.0
            )

            kurtosis_value = (
                float(kurtosis(series))
                if series.nunique() > 3 else 0.0
            )

            if skewness > 0.5:
                distribution_type = "RIGHT_SKEWED"
            elif skewness < -0.5:
                distribution_type = "LEFT_SKEWED"
            else:
                distribution_type = "APPROXIMATELY_SYMMETRIC"

            results[column] = {
                "mean": mean_value,
                "median": median_value,
                "standard_deviation": float(
                    series.std()
                ),
                "minimum": float(series.min()),
                "maximum": float(series.max()),
                "skewness": round(skewness, 4),
                "kurtosis": round(kurtosis_value, 4),
                "distribution_type": distribution_type
            }

        return {
            "status": "SUCCESS",
            "sampling_used": sampling_used,
            "distributions": results
        }


import numpy as np
import pandas as pd


class StatisticalAnomalyDetector:

    def __init__(self, multiplier=1.5):
        if multiplier <= 0:
            raise ValueError("Multiplier must be greater than zero")

        self.multiplier = multiplier

    def analyze(self, data, dataset_name="dataset"):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if data.empty:
            raise ValueError("Dataset is empty")

        results = []

        numeric_columns = data.select_dtypes(
            include=["number"]
        ).columns

        for column in numeric_columns:

            if pd.api.types.is_bool_dtype(data[column]):
                continue

            values = pd.to_numeric(
                data[column],
                errors="coerce"
            )

            valid_mask = np.isfinite(values)
            clean_values = values[valid_mask]

            if len(clean_values) < 4:
                continue

            q1 = clean_values.quantile(0.25)
            q3 = clean_values.quantile(0.75)

            iqr = q3 - q1

            lower_bound = q1 - (
                self.multiplier * iqr
            )

            upper_bound = q3 + (
                self.multiplier * iqr
            )

            outlier_mask = (
                valid_mask
                & (
                    (values < lower_bound)
                    | (values > upper_bound)
                )
            )

            outlier_positions = np.flatnonzero(
                outlier_mask.to_numpy()
            )

            outlier_values = values.iloc[
                outlier_positions
            ].tolist()

            results.append({
                "column": str(column),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": len(outlier_positions),
                "outlier_values": [
                    float(value)
                    for value in outlier_values
                ]
            })

        return {
            "dataset_name": dataset_name,
            "method": "IQR",
            "columns_analyzed": len(results),
            "total_outliers": sum(
                item["outlier_count"]
                for item in results
            ),
            "column_results": results,
            "interpretation": (
                "Potential anomalies identified. "
                "These are not confirmed errors."
            )
        }

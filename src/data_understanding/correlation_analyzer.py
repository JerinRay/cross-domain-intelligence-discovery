
import pandas as pd
import numpy as np


class CorrelationAnalyzer:

    def analyze_correlations(self, data: pd.DataFrame):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot analyze an empty dataset.")

        numeric_data = data.select_dtypes(
            include=[np.number]
        )

        if numeric_data.shape[1] < 2:
            return {
                "status": "INSUFFICIENT_NUMERICAL_COLUMNS",
                "message": (
                    "At least two numerical columns "
                    "are required for correlation analysis."
                ),
                "pearson": {},
                "spearman": {},
                "high_correlations": []
            }

        # Remove constant columns
        numeric_data = numeric_data.loc[
            :, numeric_data.nunique() > 1
        ]

        if numeric_data.shape[1] < 2:
            return {
                "status": "INSUFFICIENT_VARIATION",
                "message": (
                    "At least two non-constant numerical "
                    "columns are required."
                ),
                "pearson": {},
                "spearman": {},
                "high_correlations": []
            }

        pearson = numeric_data.corr(
            method="pearson"
        )

        spearman = numeric_data.corr(
            method="spearman"
        )

        high_correlations = []

        for i, column_a in enumerate(pearson.columns):

            for column_b in pearson.columns[i + 1:]:

                correlation = pearson.loc[
                    column_a, column_b
                ]

                if pd.notna(correlation) and abs(correlation) >= 0.7:
                    high_correlations.append({
                        "column_1": column_a,
                        "column_2": column_b,
                        "pearson_correlation": round(
                            float(correlation), 4
                        )
                    })

        return {
            "status": "SUCCESS",
            "pearson": pearson.round(4).to_dict(),
            "spearman": spearman.round(4).to_dict(),
            "high_correlations": high_correlations
        }

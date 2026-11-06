import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer


class IsolationForestDetector:

    def __init__(
        self,
        contamination="auto",
        random_state=42,
        n_estimators=100
    ):
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators

        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=self.n_estimators
        )

        self.imputer = SimpleImputer(strategy="median")

    def analyze(self, data, dataset_name="dataset"):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if data.empty:
            raise ValueError("Dataset is empty")

        numeric_data = data.select_dtypes(
            include=["number"]
        ).copy()

        numeric_data = numeric_data.drop(
            columns=[
                column
                for column in numeric_data.columns
                if pd.api.types.is_bool_dtype(
                    numeric_data[column]
                )
            ]
        )

        numeric_data = numeric_data.replace(
            [np.inf, -np.inf],
            np.nan
        )

        numeric_data = numeric_data.dropna(
            axis=1,
            how="all"
        )

        if numeric_data.empty:
            raise ValueError(
                "No usable numeric features found"
            )

        if len(numeric_data) < 5:
            raise ValueError(
                "At least 5 rows are required"
            )

        features = self.imputer.fit_transform(
            numeric_data
        )

        predictions = self.model.fit_predict(
            features
        )

        scores = self.model.decision_function(
            features
        )

        anomaly_positions = np.flatnonzero(
            predictions == -1
        )

        anomalies = []

        for position in anomaly_positions:

            anomalies.append({
                "row_index": str(
                    data.index[position]
                ),
                "anomaly_score": float(
                    scores[position]
                )
            })

        return {
            "dataset_name": dataset_name,
            "method": "Isolation Forest",
            "rows_analyzed": len(data),
            "features_used": [
                str(column)
                for column in numeric_data.columns
            ],
            "anomaly_count": len(anomaly_positions),
            "normal_count": int(
                np.sum(predictions == 1)
            ),
            "anomalies": anomalies,
            "interpretation": (
                "Potential anomalies identified by "
                "Isolation Forest. Lower decision scores "
                "indicate more unusual observations. "
                "These are not confirmed errors or fraud."
            )
        }
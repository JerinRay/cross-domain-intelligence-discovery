
import pandas as pd


class ColumnAnalyzer:

    def analyze_columns(self, data: pd.DataFrame):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot analyze an empty dataset.")

        results = {}

        for column in data.columns:

            series = data[column]

            total_rows = len(series)
            missing_count = int(series.isna().sum())
            unique_count = int(series.nunique())

            missing_percentage = (
                (missing_count / total_rows) * 100
                if total_rows > 0 else 0
            )

            cardinality_ratio = (
                unique_count / total_rows
                if total_rows > 0 else 0
            )

            column_name = str(column).lower()

            # Identify possible datetime columns
            datetime_keywords = [
                "date", "time", "timestamp", "created_at",
                "updated_at", "approved_at", "delivered_at"
            ]

            is_datetime_candidate = any(
                keyword in column_name
                for keyword in datetime_keywords
            )

            # Identify possible identifier columns
            is_id_candidate = (
                column_name == "id"
                or column_name.endswith("_id")
                or column_name.endswith("id")
            )

            results[column] = {
                "data_type": str(series.dtype),
                "unique_values": unique_count,
                "missing_count": missing_count,
                "missing_percentage": round(
                    missing_percentage, 2
                ),
                "cardinality_ratio": round(
                    cardinality_ratio, 4
                ),
                "is_constant": unique_count <= 1,
                "is_id_candidate": is_id_candidate,
                "is_datetime_candidate": is_datetime_candidate
            }

        return results

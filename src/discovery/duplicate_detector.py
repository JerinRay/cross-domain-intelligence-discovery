
import pandas as pd


class DuplicateDetector:
    """
    Detects exact and key-based duplicate records
    without modifying the original dataset.
    """

    def analyze(self, data: pd.DataFrame, dataset_name="dataset"):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot analyze an empty dataset.")

        total_rows = len(data)

        # Identify fully duplicated rows.
        duplicate_mask = data.duplicated(keep="first")
        duplicate_count = int(duplicate_mask.sum())

        duplicate_percentage = (
            duplicate_count / total_rows
        ) * 100

        # Detect columns that may contain repeated values.
        repeated_value_columns = {}

        for column in data.columns:
            non_missing = data[column].dropna()

            if non_missing.empty:
                continue

            unique_count = int(non_missing.nunique())
            repeated_count = int(len(non_missing) - unique_count)

            if repeated_count > 0:
                repeated_value_columns[column] = {
                    "unique_values": unique_count,
                    "repeated_values": repeated_count,
                    "uniqueness_percentage": round(
                        unique_count / len(non_missing) * 100, 2
                    )
                }

        return {
            "dataset_name": dataset_name,
            "total_rows": int(total_rows),
            "duplicate_rows": duplicate_count,
            "duplicate_percentage": round(
                duplicate_percentage, 2
            ),
            "duplicate_row_indices": (
                data.index[duplicate_mask].tolist()[:100]
            ),
            "repeated_value_columns": repeated_value_columns
        }

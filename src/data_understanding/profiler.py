
import pandas as pd
import numpy as np


class DatasetProfiler:
    """
    Generates a comprehensive statistical profile
    for structured datasets, including validated
    datetime columns stored as strings.
    """

    DATETIME_KEYWORDS = (
        "date", "time", "timestamp", "datetime","_at"
    )

    def __init__(self, sample_size=100_000, datetime_threshold=0.80):
        self.sample_size = sample_size
        self.datetime_threshold = datetime_threshold

    def profile_dataset(self, data: pd.DataFrame):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if data.empty:
            raise ValueError("Cannot profile an empty dataset.")

        # Work on a copy to preserve the original dataset.
        if len(data) > self.sample_size:
            sample = data.sample(
                n=self.sample_size,
                random_state=42
            ).copy()
            sampling_used = True
        else:
            sample = data.copy()
            sampling_used = False

        original_datetime_columns = (
            sample.select_dtypes(include=["datetime"]).columns.tolist()
        )

        numeric_data = sample.select_dtypes(
            include=[np.number]
        )

        # Detect and validate string-based datetime columns.
        detected_datetime_columns = {}
        datetime_validation = {}

        for column in sample.columns:

            if column in original_datetime_columns:
                continue

            if not any(
                keyword in str(column).lower()
                for keyword in self.DATETIME_KEYWORDS
            ):
                continue

            if (
                pd.api.types.is_numeric_dtype(sample[column])
                or pd.api.types.is_bool_dtype(sample[column])
            ):
                continue

            valid_values = sample[column].dropna()

            if valid_values.empty:
                datetime_validation[column] = {
                    "is_valid_datetime": False,
                    "valid_percentage": 0.0,
                    "reason": "No non-missing values"
                }
                continue

            parsed = pd.to_datetime(
                valid_values,
                errors="coerce",
                utc=True
            )

            valid_count = int(parsed.notna().sum())
            valid_percentage = valid_count / len(valid_values)

            is_datetime = (
                valid_percentage >= self.datetime_threshold
            )

            datetime_validation[column] = {
                "is_valid_datetime": is_datetime,
                "valid_percentage": round(
                    valid_percentage * 100, 2
                ),
                "valid_count": valid_count,
                "invalid_count": int(
                    len(valid_values) - valid_count
                )
            }

            if is_datetime:
                detected_datetime_columns[column] = pd.to_datetime(
                    sample[column],
                    errors="coerce",
                    utc=True
                )

        # Include columns already stored as datetime.
        for column in original_datetime_columns:
            detected_datetime_columns[column] = pd.to_datetime(
                sample[column],
                errors="coerce",
                utc=True
            )

        datetime_column_names = list(
            detected_datetime_columns.keys()
        )

        # Exclude detected datetime columns from categorical analysis.
        categorical_data = sample.drop(
            columns=datetime_column_names,
            errors="ignore"
        ).select_dtypes(
            include=["object", "category", "string", "bool"]
        )

        # Numerical statistics.
        numerical_statistics = (
            numeric_data.describe().to_dict()
            if not numeric_data.empty
            else {}
        )

        # Categorical statistics.
        categorical_statistics = {}

        for column in categorical_data.columns:
            mode_values = categorical_data[column].mode()

            categorical_statistics[column] = {
                "unique_values": int(
                    categorical_data[column].nunique()
                ),
                "most_frequent": (
                    str(mode_values.iloc[0])
                    if not mode_values.empty
                    else None
                )
            }

        # Datetime statistics.
        datetime_statistics = {}

        for column, parsed in detected_datetime_columns.items():

            valid_dates = parsed.dropna()

            datetime_statistics[column] = {
                "minimum": (
                    valid_dates.min().isoformat()
                    if not valid_dates.empty else None
                ),
                "maximum": (
                    valid_dates.max().isoformat()
                    if not valid_dates.empty else None
                ),
                "unique_values": int(valid_dates.nunique()),
                "missing_or_invalid_count": int(
                    parsed.isna().sum()
                )
            }

        profile = {
            "dataset_overview": {
                "total_rows": int(len(data)),
                "total_columns": int(len(data.columns)),
                "memory_usage_bytes": int(
                    data.memory_usage(deep=True).sum()
                ),
                "sampling_used": sampling_used,
                "sampled_rows": int(len(sample))
            },

            "column_categories": {
                "numerical": numeric_data.columns.tolist(),
                "categorical": categorical_data.columns.tolist(),
                "datetime": datetime_column_names
            },

            "datetime_validation": datetime_validation,

            "missing_values": {
                column: int(count)
                for column, count in sample.isnull().sum().items()
            },

            "numerical_statistics": numerical_statistics,

            "categorical_statistics": categorical_statistics,

            "datetime_statistics": datetime_statistics
        }

        return profile

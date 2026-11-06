import pandas as pd


class EcommerceFeatureBuilder:

    REQUIRED_COLUMNS = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]

    def build_features(self, data):

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if data.empty:
            raise ValueError("Dataset is empty")

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        features = pd.DataFrame(index=data.index)

        purchase = pd.to_datetime(
            data["order_purchase_timestamp"],
            errors="coerce",
            utc=True
        )

        approved = pd.to_datetime(
            data["order_approved_at"],
            errors="coerce",
            utc=True
        )

        delivered = pd.to_datetime(
            data["order_delivered_customer_date"],
            errors="coerce",
            utc=True
        )

        estimated = pd.to_datetime(
            data["order_estimated_delivery_date"],
            errors="coerce",
            utc=True
        )

        features["purchase_hour"] = (
            purchase.dt.hour
        )

        features["approval_delay_hours"] = (
            approved - purchase
        ).dt.total_seconds() / 3600

        features["delivery_duration_days"] = (
            delivered - purchase
        ).dt.total_seconds() / 86400

        features["delivery_delay_days"] = (
            delivered - estimated
        ).dt.total_seconds() / 86400

        return features
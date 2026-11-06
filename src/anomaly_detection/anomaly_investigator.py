import pandas as pd


class AnomalyInvestigator:

    def investigate(
        self,
        original_data,
        features,
        detection_report
    ):

        if not isinstance(original_data, pd.DataFrame):
            raise TypeError(
                "Original data must be a pandas DataFrame"
            )

        if not isinstance(features, pd.DataFrame):
            raise TypeError(
                "Features must be a pandas DataFrame"
            )

        if original_data.empty or features.empty:
            raise ValueError("Input dataset is empty")

        if not original_data.index.equals(features.index):
            raise ValueError(
                "Original data and features must have matching indexes"
            )

        if not isinstance(detection_report, dict):
            raise TypeError(
                "Detection report must be a dictionary"
            )

        if "anomalies" not in detection_report:
            raise ValueError(
                "Detection report has no anomalies field"
            )

        if "dataset_name" not in detection_report:
            raise ValueError(
                "Detection report has no dataset_name field"
            )

        anomaly_records = detection_report["anomalies"]

        if not isinstance(anomaly_records, list):
            raise ValueError(
                "Anomalies must be provided as a list"
            )

        if not anomaly_records:
            return pd.DataFrame()

        rows = []

        for anomaly in anomaly_records:

            row_index = anomaly.get("row_index")

            try:
                original_index = next(
                    index
                    for index in original_data.index
                    if str(index) == str(row_index)
                )
            except StopIteration:
                raise ValueError(
                    f"Unknown anomaly row index: {row_index}"
                )

            original_row = original_data.loc[
                original_index
            ]

            feature_row = features.loc[
                original_index
            ]

            record = {
                "row_index": str(original_index),
                "anomaly_score": anomaly["anomaly_score"]
            }

            record.update(
                original_row.to_dict()
            )

            record.update(
                feature_row.to_dict()
            )

            rows.append(record)

        report = pd.DataFrame(rows)

        return report

    def save_report(
        self,
        report,
        output_path="logs/anomaly_investigation"
    ):

        if not isinstance(report, pd.DataFrame):
            raise TypeError(
                "Report must be a pandas DataFrame"
            )

        import os

        os.makedirs(
            os.path.dirname(output_path) or ".",
            exist_ok=True
        )

        report.to_csv(
            output_path,
            index=False
        )

        return output_path
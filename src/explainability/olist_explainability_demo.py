
import json
import pandas as pd

from src.anomaly_detection.feature_builder import (
    EcommerceFeatureBuilder
)
from src.explainability.explanation_engine import (
    ExplanationEngine
)


def main():
    print("=" * 65)
    print("OLIST EXPLAINABILITY INTEGRATION DEMO")
    print("=" * 65)

    orders_path = (
        "datasets/processed/olist/olist_orders_dataset.parquet"
    )

    report_path = (
        "logs/anomaly_investigation/olist_anomaly_report.csv"
    )

    # Step 1: Load original Olist orders
    orders = pd.read_parquet(orders_path)

    print("\nOriginal orders shape:", orders.shape)

    # Step 2: Build numerical features
    feature_builder = EcommerceFeatureBuilder()
    features = feature_builder.build_features(orders)

    print("Feature dataset shape:", features.shape)
    print("Features:", features.columns.tolist())

    # Step 3: Load previously detected anomalies
    anomaly_report = pd.read_csv(report_path)

    print("\nTotal potential anomalies:", len(anomaly_report))

    # Step 4: Select first anomaly
    selected = anomaly_report.iloc[0]

    row_index = int(selected["row_index"])

    print("\nSelected anomaly row index:", row_index)
    print("Selected order ID:", selected["order_id"])
    print("Anomaly score:", selected["anomaly_score"])

    # Step 5: Retrieve its feature observation
    observation = features.loc[row_index]

    # Step 6: Build a single-record detection report
    detection_report = {
        "dataset_name": "olist_orders",
        "method": "IsolationForest",
        "anomalies": [
            {
                "row_index": row_index,
                "anomaly_score": float(
                    selected["anomaly_score"]
                )
            }
        ]
    }

    # Step 7: Generate unified explanation
    engine = ExplanationEngine()

    result = engine.explain_anomaly(
        observation=observation,
        reference_data=features,
        detection_report=detection_report
    )

    # Step 8: Display explanation
    print("\n" + "=" * 65)
    print("ANOMALY EXPLANATION")
    print("=" * 65)

    print(json.dumps(result, indent=4, default=str))

    # Step 9: Save explanation
    output_path = (
        "logs/anomaly_investigation/"
        "olist_first_anomaly_explanation.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            indent=4,
            default=str
        )

    print("\nExplanation saved to:", output_path)
    print("\nIntegration demo completed successfully.")


if __name__ == "__main__":
    main()

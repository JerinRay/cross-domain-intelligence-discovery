
class AnomalyExplainer:
    """
    Converts anomaly detection results and feature-level
    evidence into a human-readable explanation.

    This module does not claim that unusual features
    caused the detected anomaly.
    """

    def explain(self, detection_report, feature_explanation):
        if not isinstance(detection_report, dict):
            raise TypeError(
                "Detection report must be a dictionary"
            )

        if not isinstance(feature_explanation, dict):
            raise TypeError(
                "Feature explanation must be a dictionary"
            )

        required_fields = [
            "dataset_name",
            "method",
            "anomalies"
        ]

        for field in required_fields:
            if field not in detection_report:
                raise ValueError(
                    f"Detection report missing field: {field}"
                )

        if "explanations" not in feature_explanation:
            raise ValueError(
                "Feature explanation missing explanations field"
            )

        anomalies = detection_report["anomalies"]

        if not isinstance(anomalies, list):
            raise ValueError(
                "Anomalies must be a list"
            )

        feature_details = feature_explanation["explanations"]

        if not isinstance(feature_details, list):
            raise ValueError(
                "Feature explanations must be a list"
            )

        evidence = []

        for item in feature_details:

            if not isinstance(item, dict):
                raise ValueError(
                    "Each feature explanation must be a dictionary"
                )

            evidence.append({
                "feature": item.get("feature"),
                "observed_value": item.get("observed_value"),
                "reference_median": item.get("reference_median"),
                "direction": item.get("direction"),
                "deviation_ratio": item.get("deviation_ratio"),
                "evidence": item.get("evidence")
            })

        if not anomalies:
            summary = "No anomalies were detected in this dataset."

        elif evidence:
            feature_names = [
                str(item["feature"])
                for item in evidence
                if item["feature"] is not None
            ]

            summary = (
                f"{len(anomalies)} potential anomalies were "
                f"detected in {detection_report['dataset_name']}. "
                f"The supplied observation has unusual values in: "
                f"{', '.join(feature_names)}."
            )

        else:
            summary = (
                f"{len(anomalies)} potential anomalies were detected "
                f"in {detection_report['dataset_name']}, but no "
                f"unusual feature evidence was supplied."
            )

        return {
            "dataset_name": detection_report["dataset_name"],
            "detection_method": detection_report["method"],
            "anomaly_count": len(anomalies),
            "feature_evidence_count": len(evidence),
            "summary": summary,
            "evidence": evidence,
            "interpretation": (
                "This explanation summarizes statistical evidence. "
                "It does not establish causation, fraud, or model "
                "feature importance."
            )
        }


import pandas as pd


class FeatureExplainer:
    """
    Explains unusual feature values by comparing
    an observation against reference data.

    This is a statistical explanation, not a
    causal explanation or model feature attribution.
    """

    def __init__(self, deviation_threshold=1.5):
        if deviation_threshold <= 0:
            raise ValueError(
                "Deviation threshold must be positive"
            )

        self.deviation_threshold = deviation_threshold

    def explain(self, observation, reference_data):
        if not isinstance(observation, pd.Series):
            raise TypeError(
                "Observation must be a pandas Series"
            )

        if not isinstance(reference_data, pd.DataFrame):
            raise TypeError(
                "Reference data must be a pandas DataFrame"
            )

        if reference_data.empty:
            raise ValueError("Reference data is empty")

        explanations = []

        for feature in observation.index:

            if feature not in reference_data.columns:
                continue

            if not pd.api.types.is_numeric_dtype(
                reference_data[feature]
            ):
                continue

            value = pd.to_numeric(
                pd.Series([observation[feature]]),
                errors="coerce"
            ).iloc[0]

            reference = pd.to_numeric(
                reference_data[feature],
                errors="coerce"
            ).dropna()

            if pd.isna(value) or reference.empty:
                continue

            median = float(reference.median())
            q1 = float(reference.quantile(0.25))
            q3 = float(reference.quantile(0.75))
            iqr = q3 - q1

            if iqr == 0:
                deviation = (
                    abs(float(value) - median)
                    / max(abs(median), 1.0)
                )
            else:
                deviation = (
                    abs(float(value) - median) / iqr
                )

            if deviation >= self.deviation_threshold:

                direction = (
                    "higher"
                    if value > median
                    else "lower"
                )

                explanations.append({
                    "feature": str(feature),
                    "observed_value": float(value),
                    "reference_median": median,
                    "reference_q1": q1,
                    "reference_q3": q3,
                    "direction": direction,
                    "deviation_ratio": float(deviation),
                    "evidence": (
                        f"{feature} is {direction} than "
                        f"the reference median"
                    )
                })

        explanations.sort(
            key=lambda item: item["deviation_ratio"],
            reverse=True
        )

        return {
            "features_examined": len(observation.index),
            "unusual_feature_count": len(explanations),
            "explanations": explanations,
            "interpretation": (
                "Feature deviations describe unusual values "
                "relative to the supplied reference data. "
                "They do not establish causation or model "
                "feature importance."
            )
        }


from src.explainability.feature_explainer import FeatureExplainer
from src.explainability.anomaly_explainer import AnomalyExplainer
from src.explainability.graph_explainer import GraphExplainer


class ExplanationEngine:
    """
    Unified interface for anomaly and knowledge graph
    explanations.
    """

    def __init__(
        self,
        graph_builder=None,
        deviation_threshold=1.5
    ):
        self.feature_explainer = FeatureExplainer(
            deviation_threshold=deviation_threshold
        )

        self.anomaly_explainer = AnomalyExplainer()

        self.graph_explainer = (
            GraphExplainer(graph_builder)
            if graph_builder is not None
            else None
        )

    def explain_anomaly(
        self,
        observation,
        reference_data,
        detection_report
    ):
        feature_explanation = (
            self.feature_explainer.explain(
                observation,
                reference_data
            )
        )

        anomaly_explanation = (
            self.anomaly_explainer.explain(
                detection_report,
                feature_explanation
            )
        )

        return {
            "explanation_type": "ANOMALY",
            "feature_analysis": feature_explanation,
            "anomaly_analysis": anomaly_explanation
        }

    def explain_relationship(
        self,
        source_id,
        target_id
    ):
        if self.graph_explainer is None:
            raise RuntimeError(
                "Knowledge graph builder was not provided"
            )

        result = self.graph_explainer.explain_relationship(
            source_id,
            target_id
        )

        return {
            "explanation_type": "GRAPH_RELATIONSHIP",
            "graph_analysis": result
        }

    def explain_path(self, path):
        if self.graph_explainer is None:
            raise RuntimeError(
                "Knowledge graph builder was not provided"
            )

        result = self.graph_explainer.explain_path(path)

        return {
            "explanation_type": "GRAPH_PATH",
            "graph_analysis": result
        }


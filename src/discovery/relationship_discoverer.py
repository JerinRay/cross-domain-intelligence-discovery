
class RelationshipDiscoverer:
    """
    Classifies potential relationships between datasets
    using similarity and join-key evidence.

    Relationships are hypotheses, not guaranteed joins.
    """

    def __init__(self, min_overlap=0.01, min_name_similarity=0.5):
        self.min_overlap = min_overlap
        self.min_name_similarity = min_name_similarity

    def _classify_cardinality(self, uniqueness_a, uniqueness_b):
        threshold = 0.98

        unique_a = uniqueness_a >= threshold
        unique_b = uniqueness_b >= threshold

        if unique_a and unique_b:
            return "ONE_TO_ONE"

        if unique_a and not unique_b:
            return "ONE_TO_MANY"

        if not unique_a and unique_b:
            return "MANY_TO_ONE"

        return "MANY_TO_MANY"

    def analyze(self, join_key_result, similarity_result=None):

        if not isinstance(join_key_result, dict):
            raise TypeError("join_key_result must be a dictionary.")

        candidates = join_key_result.get(
            "join_key_candidates", []
        )

        if not isinstance(candidates, list):
            raise ValueError("join_key_candidates must be a list.")

        relationships = []

        for candidate in candidates:

            overlap = candidate.get(
                "overlap_coefficient", 0
            )

            name_similarity = candidate.get(
                "name_similarity", 0
            )

            uniqueness_a = candidate.get(
                "uniqueness_ratio_a", 0
            )

            uniqueness_b = candidate.get(
                "uniqueness_ratio_b", 0
            )

            # Require actual value overlap to establish
            # a candidate relationship.
            if overlap < self.min_overlap:
                continue

            if (
                name_similarity < self.min_name_similarity
                and overlap < 0.5
            ):
                continue

            cardinality = self._classify_cardinality(
                uniqueness_a,
                uniqueness_b
            )

            if name_similarity >= 0.8 and overlap >= 0.5:
                confidence = "HIGH"
            elif overlap >= 0.1:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            relationships.append({
                "dataset_a": join_key_result.get("dataset_a"),
                "dataset_b": join_key_result.get("dataset_b"),
                "column_a": candidate.get("column_a"),
                "column_b": candidate.get("column_b"),
                "relationship_type": cardinality,
                "name_similarity": name_similarity,
                "overlap_coefficient": overlap,
                "uniqueness_ratio_a": uniqueness_a,
                "uniqueness_ratio_b": uniqueness_b,
                "confidence": confidence,
                "validation_status": "UNVERIFIED"
            })

        relationships.sort(
            key=lambda item: (
                item["confidence"] == "HIGH",
                item["overlap_coefficient"],
                item["name_similarity"]
            ),
            reverse=True
        )

        return {
            "dataset_a": join_key_result.get("dataset_a"),
            "dataset_b": join_key_result.get("dataset_b"),
            "relationships_discovered": len(relationships),
            "relationships": relationships,
            "disclaimer": (
                "Discovered relationships are hypotheses. "
                "Validate key coverage and cardinality before "
                "performing joins or making causal claims."
            )
        }

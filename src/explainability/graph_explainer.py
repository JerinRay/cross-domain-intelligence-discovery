
class GraphExplainer:
    """
    Explains direct relationships and graph paths
    using evidence stored in a NetworkX graph.

    Explanations describe graph structure, not causation.
    """

    def __init__(self, graph_builder):
        if not hasattr(graph_builder, "graph"):
            raise TypeError(
                "Graph builder must provide a graph attribute"
            )

        self.graph = graph_builder.graph

    def explain_relationship(
        self,
        source_id,
        target_id
    ):
        if source_id not in self.graph:
            raise ValueError(
                f"Source entity not found: {source_id}"
            )

        if target_id not in self.graph:
            raise ValueError(
                f"Target entity not found: {target_id}"
            )

        source_data = dict(
            self.graph.nodes[source_id]
        )

        target_data = dict(
            self.graph.nodes[target_id]
        )

        edge_data = self.graph.get_edge_data(
            source_id,
            target_id,
            default={}
        )

        relationships = []

        for edge_key, properties in edge_data.items():

            relationship = dict(properties)

            relationships.append({
                "edge_key": edge_key,
                "relationship_type": relationship.get(
                    "relationship_type"
                ),
                "properties": relationship
            })

        return {
            "source": {
                "entity_id": source_id,
                "entity_type": source_data.get("entity_type"),
                "properties": source_data
            },
            "target": {
                "entity_id": target_id,
                "entity_type": target_data.get("entity_type"),
                "properties": target_data
            },
            "relationship_count": len(relationships),
            "relationships": relationships,
            "explanation": (
                f"{source_id} is directly connected to "
                f"{target_id} through "
                f"{len(relationships)} relationship(s)."
            ),
            "interpretation": (
                "This explanation describes stored graph "
                "relationships. It does not establish causation."
            )
        }

    def explain_path(self, path):
        if not isinstance(path, list):
            raise TypeError("Path must be a list")

        if len(path) < 2:
            raise ValueError(
                "Path must contain at least two entities"
            )

        for entity_id in path:
            if entity_id not in self.graph:
                raise ValueError(
                    f"Entity not found: {entity_id}"
                )

        steps = []

        for source_id, target_id in zip(
            path[:-1],
            path[1:]
        ):

            edge_data = self.graph.get_edge_data(
                source_id,
                target_id,
                default={}
            )

            if not edge_data:
                raise ValueError(
                    f"No direct relationship between "
                    f"{source_id} and {target_id}"
                )

            relationship_types = [
                data.get("relationship_type")
                for data in edge_data.values()
            ]

            steps.append({
                "source_id": source_id,
                "target_id": target_id,
                "relationship_types": relationship_types
            })

        return {
            "path": path,
            "path_length": len(path) - 1,
            "steps": steps,
            "explanation": (
                f"The path connects {len(path)} entities "
                f"through {len(steps)} relationship steps."
            ),
            "interpretation": (
                "The path represents graph connectivity, "
                "not a causal chain."
            )
        }

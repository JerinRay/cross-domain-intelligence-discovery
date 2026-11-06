
import networkx as nx


class KnowledgeGraphBuilder:
    """
    Builds and manages a knowledge graph using NetworkX.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity_id, entity_type, **properties):
        """Add an entity as a graph node."""

        self.graph.add_node(
            entity_id,
            entity_type=entity_type,
            **properties
        )

    def add_relationship(
        self,
        source_id,
        target_id,
        relationship_type,
        **properties
    ):
        """Add a directed relationship between two entities."""

        if source_id not in self.graph:
            raise ValueError(f"Source entity not found: {source_id}")

        if target_id not in self.graph:
            raise ValueError(f"Target entity not found: {target_id}")

        self.graph.add_edge(
            source_id,
            target_id,
            relationship_type=relationship_type,
            **properties
        )

    def get_graph_summary(self):
        """Return basic graph statistics."""

        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "entity_types": list({
                data.get("entity_type")
                for _, data in self.graph.nodes(data=True)
            })
        }

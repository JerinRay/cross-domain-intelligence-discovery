
import networkx as nx


class GraphReasoner:
    """
    Performs graph-based reasoning and relationship traversal
    using a NetworkX directed multigraph.
    """

    def __init__(self, builder):
        self.graph = builder.graph

    def get_entity(self, entity_id):
        """
        Retrieve an entity and its properties.

        Returns None if the entity does not exist.
        """

        if entity_id not in self.graph:
            return None

        return {
            "entity_id": entity_id,
            **self.graph.nodes[entity_id]
        }

    def get_neighbors(self, entity_id):
        """
        Retrieve entities directly connected through
        outgoing relationships.
        """

        if entity_id not in self.graph:
            return []

        neighbors = []

        for _, target, data in self.graph.out_edges(
            entity_id,
            data=True
        ):
            neighbors.append({
                "entity_id": target,
                "entity_type": self.graph.nodes[target].get(
                    "entity_type"
                ),
                "relationship": data.get("relationship_type"),
                "properties": dict(data)
            })

        return neighbors

    def find_paths(self, source_id, target_id, max_depth=3):
        """
        Find all simple directed paths between two entities.

        max_depth represents the maximum number of edges.
        """

        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")

        if source_id not in self.graph:
            return []

        if target_id not in self.graph:
            return []

        if source_id == target_id:
            return [[source_id]]

        return list(
            nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=max_depth
            )
        )

    def get_relationships(self, source_id, target_id):
        """
        Retrieve direct relationships between two entities.
        """

        if source_id not in self.graph:
            return []

        if target_id not in self.graph:
            return []

        relationships = []

        edge_data = self.graph.get_edge_data(
            source_id,
            target_id,
            default={}
        )

        for relationship in edge_data.values():
            relationships.append(dict(relationship))

        return relationships


from collections import Counter

import networkx as nx


class CommunityDetector:
    """
    Detect communities in a knowledge graph using NetworkX Louvain.

    The original graph is never modified.
    """

    def __init__(self, resolution=1.0, seed=42):
        self.resolution = resolution
        self.seed = seed

    def detect_communities(self, graph, max_nodes=100000):
        if graph is None or graph.number_of_nodes() == 0:
            return {
                "status": "empty",
                "message": "Knowledge graph is empty.",
                "total_nodes": 0,
                "total_edges": 0,
                "total_communities": 0,
                "communities": [],
            }

        total_nodes = graph.number_of_nodes()
        total_edges = graph.number_of_edges()

        # Avoid unexpectedly processing the entire large graph.
        if total_nodes > max_nodes:
            return {
                "status": "too_large",
                "message": (
                    f"Graph contains {total_nodes:,} nodes. "
                    f"Current safe limit is {max_nodes:,}. "
                    "Use a sampled subgraph for community detection."
                ),
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_communities": 0,
                "communities": [],
            }

        # Convert directed multigraph into a simple undirected graph.
        undirected = nx.Graph()
        undirected.add_nodes_from(graph.nodes(data=True))

        for source, target in graph.edges():
            if source != target:
                undirected.add_edge(source, target)

        if undirected.number_of_edges() == 0:
            groups = [{node} for node in undirected.nodes()]
        else:
            groups = nx.community.louvain_communities(
                undirected,
                weight=None,
                resolution=self.resolution,
                seed=self.seed,
            )

        communities = []

        for community_id, members in enumerate(
            sorted(groups, key=len, reverse=True)
        ):
            entity_types = Counter(
                graph.nodes[node].get("entity_type", "Unknown")
                for node in members
            )

            communities.append({
                "community_id": community_id,
                "size": len(members),
                "entity_types": dict(entity_types),
                "sample_entities": [
                    str(node) for node in list(members)[:10]
                ],
            })

        return {
            "status": "success",
            "message": "Community detection completed.",
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "total_communities": len(communities),
            "communities": communities,
        }

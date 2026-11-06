
class KnowledgeGraphValidator:

    def validate(self, builder):
        graph = builder.graph

        entity_type_counts = {}
        relationship_type_counts = {}

        for _, data in graph.nodes(data=True):
            entity_type = data.get("entity_type", "UNKNOWN")
            entity_type_counts[entity_type] = (
                entity_type_counts.get(entity_type, 0) + 1
            )

        for _, _, data in graph.edges(data=True):
            relationship_type = data.get(
                "relationship_type", "UNKNOWN"
            )
            relationship_type_counts[relationship_type] = (
                relationship_type_counts.get(relationship_type, 0) + 1
            )

        missing_entity_types = [
            node
            for node, data in graph.nodes(data=True)
            if not data.get("entity_type")
        ]

        isolated_nodes = list(nx.isolates(graph))

        return {
            "is_valid": (
                len(missing_entity_types) == 0
                and len(isolated_nodes) == 0
            ),
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "entity_type_counts": entity_type_counts,
            "relationship_type_counts": relationship_type_counts,
            "missing_entity_types": len(missing_entity_types),
            "isolated_nodes": len(isolated_nodes)
        }


import networkx as nx

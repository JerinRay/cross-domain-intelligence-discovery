
from datetime import datetime, timezone
from copy import deepcopy


class GraphEvolver:
    """
    Manages knowledge graph evolution.

    Supports:
    - Adding new entities
    - Updating existing entities
    - Adding relationships
    - Updating relationships
    - Recording graph evolution history
    """

    def __init__(self, graph_builder):
        self.builder = graph_builder
        self.graph = graph_builder.graph
        self.evolution_history = []

    def _record_change(self, operation, target_id, details):
        """Record every successful graph modification."""

        self.evolution_history.append({
            "operation": operation,
            "target_id": target_id,
            "details": deepcopy(details),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def add_entity(self, entity_id, entity_type, **properties):
        """Add a new entity or update an existing entity."""

        if entity_id in self.graph:
            existing_type = self.graph.nodes[entity_id].get("entity_type")

            if existing_type != entity_type:
                raise ValueError(
                    f"Entity type mismatch for {entity_id}: "
                    f"{existing_type} != {entity_type}"
                )

            return self.update_entity(entity_id, **properties)

        self.builder.add_entity(
            entity_id,
            entity_type,
            **properties
        )

        self._record_change(
            "ADD_ENTITY",
            entity_id,
            {
                "entity_type": entity_type,
                "properties": properties
            }
        )

        return "ENTITY_ADDED"

    def update_entity(self, entity_id, **properties):
        """Update properties of an existing entity."""

        if entity_id not in self.graph:
            raise ValueError(f"Entity not found: {entity_id}")

        if not properties:
            return "NO_CHANGES"

        old_properties = deepcopy(dict(self.graph.nodes[entity_id]))

        self.graph.nodes[entity_id].update(properties)

        self._record_change(
            "UPDATE_ENTITY",
            entity_id,
            {
                "old_properties": old_properties,
                "updated_properties": properties
            }
        )

        return "ENTITY_UPDATED"

    def add_relationship(
        self,
        source_id,
        target_id,
        relationship_type,
        **properties
    ):
        """Add a relationship if an equivalent one does not exist."""

        if source_id not in self.graph:
            raise ValueError(f"Source entity not found: {source_id}")

        if target_id not in self.graph:
            raise ValueError(f"Target entity not found: {target_id}")

        existing_edges = self.graph.get_edge_data(source_id, target_id, default={})

        for edge_key, edge_data in existing_edges.items():
            if edge_data.get("relationship_type") == relationship_type:
                return "RELATIONSHIP_ALREADY_EXISTS"

        self.builder.add_relationship(
            source_id,
            target_id,
            relationship_type,
            **properties
        )

        self._record_change(
            "ADD_RELATIONSHIP",
            f"{source_id}->{target_id}",
            {
                "relationship_type": relationship_type,
                "properties": properties
            }
        )

        return "RELATIONSHIP_ADDED"

    def update_relationship(
        self,
        source_id,
        target_id,
        relationship_type,
        **properties
    ):
        """Update an existing relationship."""

        existing_edges = self.graph.get_edge_data(
            source_id,
            target_id,
            default={}
        )

        if not existing_edges:
            raise ValueError("Relationship not found")

        for edge_key, edge_data in existing_edges.items():
            if edge_data.get("relationship_type") == relationship_type:
                old_properties = deepcopy(dict(edge_data))

                self.graph.edges[source_id, target_id, edge_key].update(
                    properties
                )

                self._record_change(
                    "UPDATE_RELATIONSHIP",
                    f"{source_id}->{target_id}",
                    {
                        "relationship_type": relationship_type,
                        "old_properties": old_properties,
                        "updated_properties": properties
                    }
                )

                return "RELATIONSHIP_UPDATED"

        raise ValueError("Relationship type not found")

    def get_evolution_history(self):
        """Return a copy of graph evolution history."""

        return deepcopy(self.evolution_history)

    def get_evolution_summary(self):
        """Return summary of recorded graph changes."""

        operation_counts = {}

        for change in self.evolution_history:
            operation = change["operation"]
            operation_counts[operation] = (
                operation_counts.get(operation, 0) + 1
            )

        return {
            "total_changes": len(self.evolution_history),
            "operation_counts": operation_counts
        }

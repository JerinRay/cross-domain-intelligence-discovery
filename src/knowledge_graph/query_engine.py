
class GraphQueryEngine:
    """
    Executes structured queries against the knowledge graph
    using GraphReasoner.
    """

    def __init__(self, reasoner):
        self.reasoner = reasoner

    def execute(self, query):
        """
        Execute a structured graph query.

        Supported operations:
        - GET_ENTITY
        - GET_NEIGHBORS
        - FIND_PATH
        - GET_RELATIONSHIPS
        """

        if not isinstance(query, dict):
            raise TypeError("Query must be a dictionary")

        operation = query.get("operation")

        if operation == "GET_ENTITY":
            entity_id = query.get("entity_id")

            if not entity_id:
                raise ValueError("entity_id is required")

            return self.reasoner.get_entity(entity_id)

        elif operation == "GET_NEIGHBORS":
            entity_id = query.get("entity_id")

            if not entity_id:
                raise ValueError("entity_id is required")

            return self.reasoner.get_neighbors(entity_id)

        elif operation == "FIND_PATH":
            source_id = query.get("source_id")
            target_id = query.get("target_id")
            max_depth = query.get("max_depth", 3)

            if not source_id or not target_id:
                raise ValueError(
                    "source_id and target_id are required"
                )

            if not isinstance(max_depth, int) or isinstance(max_depth, bool):
                raise ValueError("max_depth must be an integer")

            return self.reasoner.find_paths(
                source_id,
                target_id,
                max_depth=max_depth
            )

        elif operation == "GET_RELATIONSHIPS":
            source_id = query.get("source_id")
            target_id = query.get("target_id")

            if not source_id or not target_id:
                raise ValueError(
                    "source_id and target_id are required"
                )

            return self.reasoner.get_relationships(
                source_id,
                target_id
            )

        else:
            raise ValueError(
                f"Unsupported query operation: {operation}"
            )


import re
import sqlite3
from pathlib import Path


class KnowledgeGraphSearchIndex:
    """Build and query a SQLite FTS5 knowledge graph search index."""

    def __init__(self, database_path):
        self.database_path = Path(database_path)

    @staticmethod
    def _safe_text(value, limit=300):
        if value is None:
            return ""

        if isinstance(value, (str, int, float, bool)):
            return str(value)[:limit]

        return ""

    @staticmethod
    def _prepare_query(query):
        """Convert user input into a safe FTS5 prefix query."""

        if not query:
            return ""

        tokens = re.findall(r"[A-Za-z0-9_]+", str(query).lower())

        if not tokens:
            return ""

        # Quote each token to prevent FTS5 operator injection.
        return " AND ".join(f'"{token}"*' for token in tokens[:10])

    @staticmethod
    def _validate_limit(limit):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 20

        return max(1, min(limit, 100))

    def build(self, builder):
        """Create searchable indexes for graph entities and relationships."""

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if self.database_path.exists():
            self.database_path.unlink()

        connection = sqlite3.connect(self.database_path)

        entity_count = 0
        relationship_count = 0
        batch_size = 5000

        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")

            connection.execute("""
                CREATE VIRTUAL TABLE entities_fts USING fts5(
                    entity_id UNINDEXED,
                    entity_type UNINDEXED,
                    searchable
                )
            """)

            connection.execute("""
                CREATE VIRTUAL TABLE relationships_fts USING fts5(
                    source_id UNINDEXED,
                    target_id UNINDEXED,
                    relationship_type UNINDEXED,
                    searchable
                )
            """)

            entity_batch = []

            for entity_id, attributes in builder.graph.nodes(data=True):
                entity_type = attributes.get(
                    "entity_type", "Unknown"
                )

                searchable_parts = [
                    str(entity_id),
                    str(entity_type)
                ]

                for key, value in attributes.items():
                    if key == "entity_type":
                        continue

                    text = self._safe_text(value)

                    if text:
                        searchable_parts.append(str(key))
                        searchable_parts.append(text)

                searchable = " ".join(searchable_parts)[:2000]

                entity_batch.append((
                    str(entity_id),
                    str(entity_type),
                    searchable
                ))

                if len(entity_batch) >= batch_size:
                    connection.executemany(
                        """
                        INSERT INTO entities_fts
                        (entity_id, entity_type, searchable)
                        VALUES (?, ?, ?)
                        """,
                        entity_batch
                    )
                    entity_count += len(entity_batch)
                    entity_batch.clear()

            if entity_batch:
                connection.executemany(
                    """
                    INSERT INTO entities_fts
                    (entity_id, entity_type, searchable)
                    VALUES (?, ?, ?)
                    """,
                    entity_batch
                )
                entity_count += len(entity_batch)

            relationship_batch = []

            for source, target, attributes in builder.graph.edges(data=True):
                relationship_type = attributes.get(
                    "relationship_type", "UNKNOWN"
                )

                source_type = builder.graph.nodes[source].get(
                    "entity_type", ""
                )

                target_type = builder.graph.nodes[target].get(
                    "entity_type", ""
                )

                searchable = (
                    f"{source} {target} {relationship_type} "
                    f"{source_type} {target_type}"
                )

                relationship_batch.append((
                    str(source),
                    str(target),
                    str(relationship_type),
                    searchable
                ))

                if len(relationship_batch) >= batch_size:
                    connection.executemany(
                        """
                        INSERT INTO relationships_fts
                        (source_id, target_id, relationship_type, searchable)
                        VALUES (?, ?, ?, ?)
                        """,
                        relationship_batch
                    )
                    relationship_count += len(relationship_batch)
                    relationship_batch.clear()

            if relationship_batch:
                connection.executemany(
                    """
                    INSERT INTO relationships_fts
                    (source_id, target_id, relationship_type, searchable)
                    VALUES (?, ?, ?, ?)
                    """,
                    relationship_batch
                )
                relationship_count += len(relationship_batch)

            connection.commit()

        finally:
            connection.close()

        return {
            "database_path": str(self.database_path),
            "entities_indexed": entity_count,
            "relationships_indexed": relationship_count
        }

    def search_entities(self, query, limit=20):
        """Search graph entities using the FTS5 index."""

        prepared_query = self._prepare_query(query)

        if not prepared_query or not self.database_path.exists():
            return []

        limit = self._validate_limit(limit)

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT entity_id, entity_type, searchable
                FROM entities_fts
                WHERE entities_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (prepared_query, limit)
            ).fetchall()

        return [dict(row) for row in rows]

    def search_relationships(self, query, limit=20):
        """Search graph relationships using the FTS5 index."""

        prepared_query = self._prepare_query(query)

        if not prepared_query or not self.database_path.exists():
            return []

        limit = self._validate_limit(limit)

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                """
                SELECT
                    source_id,
                    target_id,
                    relationship_type,
                    searchable
                FROM relationships_fts
                WHERE relationships_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (prepared_query, limit)
            ).fetchall()

        return [dict(row) for row in rows]

    def search_all(self, query, limit=20):
        """Search entities and relationships together."""

        return {
            "query": query,
            "entities": self.search_entities(query, limit),
            "relationships": self.search_relationships(query, limit)
        }

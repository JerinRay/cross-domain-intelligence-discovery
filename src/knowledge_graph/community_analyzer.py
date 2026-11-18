
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path

import networkx as nx


class CommunityAnalyzer:
    """Detect communities in a connected Olist knowledge graph sample."""

    def __init__(
        self,
        database_path="logs/knowledge_graph_search.sqlite",
        resolution=1.0,
        seed=42,
        customer_sample_size=300,
        batch_size=400,
    ):
        self.database_path = Path(database_path)
        self.resolution = resolution
        self.seed = seed
        self.customer_sample_size = customer_sample_size
        self.batch_size = batch_size

    def _fetch_edges(self, connection, source_ids, relationship_type):
        """Fetch outgoing edges in safe SQLite batches."""
        edges = []

        for start in range(0, len(source_ids), self.batch_size):
            batch = source_ids[start:start + self.batch_size]
            placeholders = ",".join("?" for _ in batch)

            query = f"""
                SELECT source_id, target_id
                FROM relationships_fts
                WHERE relationship_type = ?
                AND source_id IN ({placeholders})
            """

            rows = connection.execute(
                query,
                [relationship_type, *batch],
            ).fetchall()

            edges.extend(rows)

        return edges

    def _add_edges(self, graph, edges):
        graph.add_edges_from(edges)
        return list(dict.fromkeys(target for _, target in edges))

    def analyze(self):
        if not self.database_path.exists():
            return {
                "status": "error",
                "message": "Knowledge graph search database not found.",
                "communities": [],
            }

        connection = None

        try:
            connection = sqlite3.connect(
                f"file:{self.database_path.resolve()}?mode=ro",
                uri=True,
            )

            total_entities = connection.execute(
                "SELECT COUNT(*) FROM entities_fts"
            ).fetchone()[0]

            total_relationships = connection.execute(
                "SELECT COUNT(*) FROM relationships_fts"
            ).fetchone()[0]

            # Select a reproducible random sample of customers.
            customer_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT entity_id
                    FROM entities_fts
                    WHERE entity_type = 'Customer'
                    """
                ).fetchall()
            ]

            if not customer_ids:
                return {
                    "status": "empty",
                    "message": "No Customer entities found.",
                    "communities": [],
                }

            rng = random.Random(self.seed)
            selected_customers = rng.sample(
                customer_ids,
                min(self.customer_sample_size, len(customer_ids)),
            )

            graph = nx.Graph()
            graph.add_nodes_from(
                (customer_id, {"entity_type": "Customer"})
                for customer_id in selected_customers
            )

            # Customer -> Order
            placed_edges = self._fetch_edges(
                connection, selected_customers, "PLACED"
            )
            order_ids = self._add_edges(graph, placed_edges)

            # Order -> OrderItem
            contains_edges = self._fetch_edges(
                connection, order_ids, "CONTAINS"
            )
            item_ids = self._add_edges(graph, contains_edges)

            # Order -> Payment
            payment_edges = self._fetch_edges(
                connection, order_ids, "HAS_PAYMENT"
            )
            self._add_edges(graph, payment_edges)

            # Order -> Review
            review_edges = self._fetch_edges(
                connection, order_ids, "HAS_REVIEW"
            )
            self._add_edges(graph, review_edges)

            # OrderItem -> Product
            product_edges = self._fetch_edges(
                connection, item_ids, "REFERENCES"
            )
            self._add_edges(graph, product_edges)

            # OrderItem -> Seller
            seller_edges = self._fetch_edges(
                connection, item_ids, "SOLD_BY"
            )
            self._add_edges(graph, seller_edges)

            # Load entity types for every sampled graph node.
            sampled_nodes = list(graph.nodes())

            for start in range(0, len(sampled_nodes), self.batch_size):
                batch = sampled_nodes[start:start + self.batch_size]
                placeholders = ",".join("?" for _ in batch)

                rows = connection.execute(
                    f"""
                    SELECT entity_id, entity_type
                    FROM entities_fts
                    WHERE entity_id IN ({placeholders})
                    """,
                    batch,
                ).fetchall()

                for entity_id, entity_type in rows:
                    graph.nodes[entity_id]["entity_type"] = entity_type

            for node in graph.nodes():
                graph.nodes[node].setdefault("entity_type", "Unknown")

            if graph.number_of_nodes() == 0:
                return {
                    "status": "empty",
                    "message": "No connected entities found.",
                    "communities": [],
                }

            # Run Louvain on the connected sample.
            if graph.number_of_edges() == 0:
                groups = [{node} for node in graph.nodes()]
            else:
                groups = nx.community.louvain_communities(
                    graph,
                    weight=None,
                    resolution=self.resolution,
                    seed=self.seed,
                )

            communities = []

            for community_id, members in enumerate(
                sorted(groups, key=len, reverse=True)
            ):
                entity_types = Counter(
                    graph.nodes[node]["entity_type"]
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
                "message": "Connected sample community detection completed.",
                "analysis_scope": "connected_customer_order_sample",
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "sampled_customers": len(selected_customers),
                "analyzed_nodes": graph.number_of_nodes(),
                "analyzed_edges": graph.number_of_edges(),
                "connected_components": nx.number_connected_components(graph),
                "total_communities": len(communities),
                "resolution": self.resolution,
                "seed": self.seed,
                "communities": communities,
            }

        except (sqlite3.Error, OSError, nx.NetworkXException) as exc:
            return {
                "status": "error",
                "message": str(exc),
                "communities": [],
            }

        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def save_report(
        result,
        output_path="logs/community_report.json",
    ):
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as file:
            json.dump(result, file, indent=2, ensure_ascii=False)

        return str(output)

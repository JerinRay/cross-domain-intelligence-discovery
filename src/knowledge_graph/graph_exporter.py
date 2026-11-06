
import json
import networkx as nx


class KnowledgeGraphExporter:
    """
    Exports a knowledge graph into GraphML and JSON formats.
    """

    def export_graphml(self, builder, output_path):
        """Export graph into GraphML format."""

        nx.write_graphml(builder.graph, output_path)

        return output_path

    def export_json(self, builder, output_path):
        """Export graph into JSON format."""

        graph_data = nx.node_link_data(
            builder.graph,
            edges="edges"
        )

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(
                graph_data,
                file,
                indent=4,
                ensure_ascii=False
            )

        return output_path

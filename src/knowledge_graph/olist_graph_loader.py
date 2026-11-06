
import pandas as pd

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder


class OlistGraphLoader:

    def __init__(self):
        self.builder = KnowledgeGraphBuilder()

    def load_data(self, orders_path, customers_path):
        orders = pd.read_parquet(orders_path)
        customers = pd.read_parquet(customers_path)

        # Add customer entities
        for row in customers.to_dict("records"):
            self.builder.add_entity(
                f"customer:{row['customer_id']}",
                "Customer",
                customer_unique_id=row["customer_unique_id"],
                city=row["customer_city"],
                state=row["customer_state"],
                zip_code=str(row["customer_zip_code_prefix"])
            )

        # Add order entities and relationships
        for row in orders.to_dict("records"):
            order_node = f"order:{row['order_id']}"
            customer_node = f"customer:{row['customer_id']}"

            self.builder.add_entity(
                order_node,
                "Order",
                order_status=row["order_status"],
                purchase_timestamp=str(row["order_purchase_timestamp"])
            )

            if customer_node in self.builder.graph:
                self.builder.add_relationship(
                    customer_node,
                    order_node,
                    "PLACED"
                )

        return self.builder

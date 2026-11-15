import pandas as pd

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder


class OlistGraphLoader:
    """Build a cross-domain graph from Olist datasets."""

    def __init__(self):
        self.builder = KnowledgeGraphBuilder()

    @staticmethod
    def clean_record(row):
        """Convert missing values and timestamps into safe Python values."""
        result = {}

        for key, value in row.items():
            if pd.isna(value):
                result[key] = None
            elif isinstance(value, pd.Timestamp):
                result[key] = str(value)
            elif hasattr(value, "item"):
                result[key] = value.item()
            else:
                result[key] = value

        return result

    def load_data(
        self,
        orders_path,
        customers_path,
        order_items_path=None,
        products_path=None,
        sellers_path=None,
        payments_path=None,
        reviews_path=None
    ):
        """Load two required datasets and up to five optional datasets."""

        self.builder = KnowledgeGraphBuilder()

        # 1. Customers
        customers = pd.read_parquet(customers_path)

        for row in customers.to_dict("records"):
            data = self.clean_record(row)

            self.builder.add_entity(
                f"customer:{data['customer_id']}",
                "Customer",
                customer_unique_id=data["customer_unique_id"],
                city=data["customer_city"],
                state=data["customer_state"],
                zip_code=str(data["customer_zip_code_prefix"])
            )

        # 2. Orders and Customer -> Order relationships
        orders = pd.read_parquet(orders_path)

        for row in orders.to_dict("records"):
            data = self.clean_record(row)

            order_node = f"order:{data['order_id']}"
            customer_node = f"customer:{data['customer_id']}"

            self.builder.add_entity(
                order_node,
                "Order",
                order_status=data["order_status"],
                purchase_timestamp=str(data["order_purchase_timestamp"])
            )

            if customer_node in self.builder.graph:
                self.builder.add_relationship(
                    customer_node, order_node, "PLACED"
                )

        # 3. Products
        if products_path is not None:
            products = pd.read_parquet(products_path)

            for row in products.to_dict("records"):
                data = self.clean_record(row)
                product_id = data.pop("product_id")

                self.builder.add_entity(
                    f"product:{product_id}",
                    "Product",
                    **data
                )

        # 4. Sellers
        if sellers_path is not None:
            sellers = pd.read_parquet(sellers_path)

            for row in sellers.to_dict("records"):
                data = self.clean_record(row)
                seller_id = data.pop("seller_id")

                self.builder.add_entity(
                    f"seller:{seller_id}",
                    "Seller",
                    zip_code=str(data["seller_zip_code_prefix"]),
                    city=data["seller_city"],
                    state=data["seller_state"]
                )

        # 5. Order items and their relationships
        if order_items_path is not None:
            items = pd.read_parquet(order_items_path)

            for row in items.to_dict("records"):
                data = self.clean_record(row)

                order_node = f"order:{data['order_id']}"
                product_node = f"product:{data['product_id']}"
                seller_node = f"seller:{data['seller_id']}"

                item_node = (
                    f"order_item:{data['order_id']}:"
                    f"{data['order_item_id']}"
                )

                self.builder.add_entity(
                    item_node,
                    "OrderItem",
                    order_item_id=data["order_item_id"],
                    price=data["price"],
                    freight_value=data["freight_value"],
                    shipping_limit_date=str(data["shipping_limit_date"])
                )

                if order_node in self.builder.graph:
                    self.builder.add_relationship(
                        order_node, item_node, "CONTAINS"
                    )

                if product_node in self.builder.graph:
                    self.builder.add_relationship(
                        item_node, product_node, "REFERENCES"
                    )

                if seller_node in self.builder.graph:
                    self.builder.add_relationship(
                        item_node, seller_node, "SOLD_BY"
                    )

        # 6. Payments
        if payments_path is not None:
            payments = pd.read_parquet(payments_path)

            for row in payments.to_dict("records"):
                data = self.clean_record(row)

                order_node = f"order:{data['order_id']}"
                payment_node = (
                    f"payment:{data['order_id']}:"
                    f"{data['payment_sequential']}"
                )

                self.builder.add_entity(
                    payment_node,
                    "Payment",
                    payment_sequential=data["payment_sequential"],
                    payment_type=data["payment_type"],
                    payment_installments=data["payment_installments"],
                    payment_value=data["payment_value"]
                )

                if order_node in self.builder.graph:
                    self.builder.add_relationship(
                        order_node, payment_node, "HAS_PAYMENT"
                    )

        # 7. Reviews
        if reviews_path is not None:
            reviews = pd.read_parquet(reviews_path)

            for row in reviews.to_dict("records"):
                data = self.clean_record(row)

                order_node = f"order:{data['order_id']}"

                # Composite key handles repeated review IDs safely.
                review_node = (
                    f"review:{data['review_id']}:"
                    f"{data['order_id']}"
                )

                self.builder.add_entity(
                    review_node,
                    "Review",
                    review_id=data["review_id"],
                    order_id=data["order_id"],
                    review_score=data["review_score"],
                    review_title=data["review_comment_title"],
                    review_message=data["review_comment_message"],
                    review_creation_date=str(data["review_creation_date"]),
                    review_answer_timestamp=str(
                        data["review_answer_timestamp"]
                    )
                )

                if order_node in self.builder.graph:
                    self.builder.add_relationship(
                        order_node, review_node, "HAS_REVIEW"
                    )

        return self.builder


import pandas as pd

from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder


class OlistGraphLoader:
    """
    Loads Olist datasets and constructs a cross-domain knowledge graph.

    The original two-argument load_data() API is preserved for
    backward compatibility with earlier project modules.
    """

    def __init__(self):
        self.builder = KnowledgeGraphBuilder()

    @staticmethod
    def _clean_value(value):
        """Convert pandas missing values and timestamps safely."""

        if pd.isna(value):
            return None

        if isinstance(value, pd.Timestamp):
            return str(value)

        if hasattr(value, "item"):
            return value.item()

        return value

    @classmethod
    def _clean_record(cls, row):
        """Clean a dataset record before adding it to the graph."""

        return {
            key: cls._clean_value(value)
            for key, value in row.items()
        }

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
        """
        Load Olist data and build a cross-domain knowledge graph.

        Required:
            orders_path
            customers_path

        Optional:
            order_items_path
            products_path
            sellers_path
            payments_path
            reviews_path
        """

        self.builder = KnowledgeGraphBuilder()

        orders = pd.read_parquet(orders_path)
        customers = pd.read_parquet(customers_path)

        # --------------------------------------------------
        # 1. CUSTOMER ENTITIES
        # --------------------------------------------------

        for _, row in customers.iterrows():
            data = self._clean_record(row.to_dict())

            customer_node = f"customer:{data['customer_id']}"

            self.builder.add_entity(
                customer_node,
                "Customer",
                customer_unique_id=data["customer_unique_id"],
                city=data["customer_city"],
                state=data["customer_state"],
                zip_code=str(data["customer_zip_code_prefix"])
            )

        # --------------------------------------------------
        # 2. ORDER ENTITIES AND PLACED RELATIONSHIPS
        # --------------------------------------------------

        for _, row in orders.iterrows():
            data = self._clean_record(row.to_dict())

            order_node = f"order:{data['order_id']}"
            customer_node = f"customer:{data['customer_id']}"

            self.builder.add_entity(
                order_node,
                "Order",
                order_status=data["order_status"],
                purchase_timestamp=str(
                    data["order_purchase_timestamp"]
                )
            )

            if customer_node in self.builder.graph:
                self.builder.add_relationship(
                    customer_node,
                    order_node,
                    "PLACED"
                )

        # --------------------------------------------------
        # 3. PRODUCT ENTITIES
        # --------------------------------------------------

        if products_path is not None:
            products = pd.read_parquet(products_path)

            for _, row in products.iterrows():
                data = self._clean_record(row.to_dict())

                product_node = f"product:{data['product_id']}"

                properties = {
                    key: value
                    for key, value in data.items()
                    if key != "product_id"
                }

                self.builder.add_entity(
                    product_node,
                    "Product",
                    **properties
                )

        # --------------------------------------------------
        # 4. SELLER ENTITIES
        # --------------------------------------------------

        if sellers_path is not None:
            sellers = pd.read_parquet(sellers_path)

            for _, row in sellers.iterrows():
                data = self._clean_record(row.to_dict())

                seller_node = f"seller:{data['seller_id']}"

                self.builder.add_entity(
                    seller_node,
                    "Seller",
                    zip_code=str(data["seller_zip_code_prefix"]),
                    city=data["seller_city"],
                    state=data["seller_state"]
                )

        # --------------------------------------------------
        # 5. ORDER ITEMS AND THEIR RELATIONSHIPS
        # --------------------------------------------------

        if order_items_path is not None:
            order_items = pd.read_parquet(order_items_path)

            for _, row in order_items.iterrows():
                data = self._clean_record(row.to_dict())

                order_node = f"order:{data['order_id']}"
                item_node = (
                    f"order_item:{data['order_id']}:"
                    f"{data['order_item_id']}"
                )
                product_node = f"product:{data['product_id']}"
                seller_node = f"seller:{data['seller_id']}"

                self.builder.add_entity(
                    item_node,
                    "OrderItem",
                    order_item_id=data["order_item_id"],
                    price=data["price"],
                    freight_value=data["freight_value"],
                    shipping_limit_date=str(
                        data["shipping_limit_date"]
                    )
                )

                if order_node in self.builder.graph:
                    self.builder.add_relationship(
                        order_node,
                        item_node,
                        "CONTAINS"
                    )

                if product_node in self.builder.graph:
                    self.builder.add_relationship(
                        item_node,
                        product_node,
                        "REFERENCES"
                    )

                if seller_node in self.builder.graph:
                    self.builder.add_relationship(
                        item_node,
                        seller_node,
                        "SOLD_BY"
                    )

        # --------------------------------------------------
        # 6. PAYMENT ENTITIES AND RELATIONSHIPS
        # --------------------------------------------------

        if payments_path is not None:
            payments = pd.read_parquet(payments_path)

            for _, row in payments.iterrows():
                data = self._clean_record(row.to_dict())

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
                        order_node,
                        payment_node,
                        "HAS_PAYMENT"
                    )

        # --------------------------------------------------
        # 7. REVIEW ENTITIES AND RELATIONSHIPS
        # --------------------------------------------------

        if reviews_path is not None:
            reviews = pd.read_parquet(reviews_path)

            for _, row in reviews.iterrows():
                data = self._clean_record(row.to_dict())

                order_node = f"order:{data['order_id']}"

                # Composite identifier avoids review_id collisions.
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
                    review_creation_date=str(
                        data["review_creation_date"]
                    ),
                    review_answer_timestamp=str(
                        data["review_answer_timestamp"]
                    )
                )

                if order_node in self.builder.graph:
                    self.builder.add_relationship(
                        order_node,
                        review_node,
                        "HAS_REVIEW"
                    )

        return self.builder

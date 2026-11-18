
from pathlib import Path

import pandas as pd

from src.pipeline.orchestrator import IntelligenceOrchestrator

from src.ingestion.data_loader import run_ingestion_pipeline

from src.data_understanding.engine import DataUnderstandingEngine
from src.discovery.engine import DiscoveryEngine

from src.anomaly_detection.feature_builder import EcommerceFeatureBuilder
from src.anomaly_detection.isolation_forest_detector import IsolationForestDetector
from src.anomaly_detection.anomaly_investigator import AnomalyInvestigator

from src.nlp.text_preprocessor import TextPreprocessor

from src.knowledge_graph.olist_graph_loader import OlistGraphLoader
from src.knowledge_graph.graph_validator import KnowledgeGraphValidator
from src.knowledge_graph.graph_exporter import KnowledgeGraphExporter
from src.knowledge_graph.search_index import KnowledgeGraphSearchIndex


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path.cwd()

PROCESSED_DIR = PROJECT_ROOT / "datasets" / "processed" / "olist"
LOG_DIR = PROJECT_ROOT / "logs"
PIPELINE_LOG_DIR = LOG_DIR / "pipeline"
INGESTION_LOG_DIR = LOG_DIR / "ingestion"

ORDERS_PATH = PROCESSED_DIR / "olist_orders_dataset.parquet"
CUSTOMERS_PATH = PROCESSED_DIR / "olist_customers_dataset.parquet"
ORDER_ITEMS_PATH = PROCESSED_DIR / "olist_order_items_dataset.parquet"
PRODUCTS_PATH = PROCESSED_DIR / "olist_products_dataset.parquet"
SELLERS_PATH = PROCESSED_DIR / "olist_sellers_dataset.parquet"
PAYMENTS_PATH = PROCESSED_DIR / "olist_order_payments_dataset.parquet"
REVIEWS_PATH = PROCESSED_DIR / "olist_order_reviews_dataset.parquet"


def ensure_directories():
    PIPELINE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    INGESTION_LOG_DIR.mkdir(parents=True, exist_ok=True)


def check_dataset(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required dataset not found: {path}"
        )

    return path


def main():

    ensure_directories()

    pipeline = IntelligenceOrchestrator()

    # --------------------------------------------------
    # STAGE 1: INGESTION
    # --------------------------------------------------

    def run_ingestion():

        result = run_ingestion_pipeline(
            raw_directory="datasets/raw",
            processed_directory="datasets/processed",
            report_directory=str(INGESTION_LOG_DIR)
        )

        return {
            "result": result
        }

    pipeline.execute_stage(
        "INGESTION",
        run_ingestion
    )

    # --------------------------------------------------
    # STAGE 2: DATA UNDERSTANDING
    # --------------------------------------------------

    def run_data_understanding():

        check_dataset(ORDERS_PATH)

        orders = pd.read_parquet(ORDERS_PATH)

        engine = DataUnderstandingEngine(
            sample_size=100000
        )

        report = engine.analyze_dataset(
            data=orders,
            dataset_name="olist_orders"
        )

        report_path = engine.save_report(
            report,
            output_dir=str(PIPELINE_LOG_DIR / "data_understanding")
        )

        return {
            "dataset": "olist_orders",
            "rows": len(orders),
            "columns": len(orders.columns),
            "analysis_status": report["status"],
            "analyzers_completed": list(
                report["results"].keys()
            ),
            "report_path": str(report_path)
        }

    pipeline.execute_stage(
        "DATA_UNDERSTANDING",
        run_data_understanding
    )

    # --------------------------------------------------
    # STAGE 3: DATA DISCOVERY
    # --------------------------------------------------

    def run_data_discovery():

        check_dataset(ORDERS_PATH)
        check_dataset(ORDER_ITEMS_PATH)

        orders = pd.read_parquet(ORDERS_PATH)
        order_items = pd.read_parquet(ORDER_ITEMS_PATH)

        engine = DiscoveryEngine(
            sample_size=10000
        )

        report = engine.analyze(
            dataset_a=orders,
            dataset_b=order_items,
            dataset_a_name="olist_orders",
            dataset_b_name="olist_order_items"
        )

        report_path = engine.save_report(
            report,
            output_dir=str(PIPELINE_LOG_DIR / "data_discovery")
        )

        return {
            "datasets": [
                "olist_orders",
                "olist_order_items"
            ],
            "orders_rows": len(orders),
            "order_items_rows": len(order_items),
            "discovery_status": report["status"],
            "report_path": str(report_path)
        }

    pipeline.execute_stage(
        "DATA_DISCOVERY",
        run_data_discovery
    )

    # --------------------------------------------------
    # STAGE 4: ANOMALY DETECTION
    # --------------------------------------------------

    def run_anomaly_detection():

        check_dataset(ORDERS_PATH)

        orders = pd.read_parquet(ORDERS_PATH)

        feature_builder = EcommerceFeatureBuilder()

        features = feature_builder.build_features(orders)

        detector = IsolationForestDetector(
            contamination=0.02,
            random_state=42
        )

        detection_report = detector.analyze(
            data=features,
            dataset_name="olist_orders"
        )

        investigator = AnomalyInvestigator()

        investigation = investigator.investigate(
            original_data=orders,
            features=features,
            detection_report=detection_report
        )

        output_path = (
            PIPELINE_LOG_DIR /
            "olist_anomaly_investigation.csv"
        )

        saved_path = investigator.save_report(
            investigation,
            output_path=str(output_path)
        )

        return {
            "dataset": "olist_orders",
            "total_records": len(orders),
            "features": list(features.columns),
            "anomaly_count": detection_report["anomaly_count"],
            "investigated_records": len(investigation),
            "normal_count": detection_report["normal_count"],
            "method": detection_report["method"],
            "interpretation": detection_report["interpretation"],
            "output": str(saved_path)
        }

    pipeline.execute_stage(
        "ANOMALY_DETECTION",
        run_anomaly_detection
    )

    # --------------------------------------------------
    # STAGE 5: NLP PROCESSING
    # --------------------------------------------------

    def run_nlp_processing():

        check_dataset(REVIEWS_PATH)

        reviews = pd.read_parquet(REVIEWS_PATH)

        required_columns = [
            "review_comment_title",
            "review_comment_message"
        ]

        for column in required_columns:

            if column not in reviews.columns:

                raise ValueError(
                    f"Missing required NLP column: {column}"
                )

        titles = (
            reviews["review_comment_title"]
            .fillna("")
            .astype(str)
        )

        messages = (
            reviews["review_comment_message"]
            .fillna("")
            .astype(str)
        )

        reviews["review_text"] = (
            titles.str.strip() + " " + messages.str.strip()
        ).str.strip()

        preprocessor = TextPreprocessor()

        processed_reviews = preprocessor.preprocess_dataframe(
            data=reviews,
            text_column="review_text",
            output_column="processed_text"
        )

        if "processed_text" not in processed_reviews.columns:

            raise ValueError(
                "NLP preprocessing did not create processed_text column."
            )

        output_path = (
            PIPELINE_LOG_DIR /
            "processed_reviews.parquet"
        )

        processed_reviews.to_parquet(
            output_path,
            index=False
        )

        return {
            "total_reviews": len(processed_reviews),
            "reviews_with_text": int(
                processed_reviews["review_text"].str.len().gt(0).sum()
            ),
            "reviews_without_text": int(
                processed_reviews["review_text"].str.len().eq(0).sum()
            ),
            "reviews_with_processed_text": int(
                processed_reviews["processed_text"].str.len().gt(0).sum()
            ),
            "output": str(output_path)
        }

    pipeline.execute_stage(
        "NLP_PROCESSING",
        run_nlp_processing
    )

    # --------------------------------------------------
    # STAGE 6: KNOWLEDGE GRAPH CONSTRUCTION
    # --------------------------------------------------

    def run_knowledge_graph():

        required_graph_datasets = [
            ORDERS_PATH,
            CUSTOMERS_PATH,
            ORDER_ITEMS_PATH,
            PRODUCTS_PATH,
            SELLERS_PATH,
            PAYMENTS_PATH,
            REVIEWS_PATH
        ]

        for dataset_path in required_graph_datasets:
            check_dataset(dataset_path)

        # Build graph
        loader = OlistGraphLoader()

        builder = loader.load_data(
            orders_path=str(ORDERS_PATH),
            customers_path=str(CUSTOMERS_PATH),
            order_items_path=str(ORDER_ITEMS_PATH),
            products_path=str(PRODUCTS_PATH),
            sellers_path=str(SELLERS_PATH),
            payments_path=str(PAYMENTS_PATH),
            reviews_path=str(REVIEWS_PATH)
        )

        # Validate graph
        validator = KnowledgeGraphValidator()

        validation = validator.validate(builder)

        graph_summary = builder.get_graph_summary()

        # Export knowledge graph as JSON
        exporter = KnowledgeGraphExporter()

        graph_output_path = (
            LOG_DIR /
            "olist_knowledge_graph_day11.json"
        )

        exported_path = exporter.export_json(
            builder,
            str(graph_output_path)
        )

        # --------------------------------------------------
        # BUILD SQLITE KNOWLEDGE GRAPH SEARCH INDEX
        # --------------------------------------------------

        search_database_path = (
            LOG_DIR /
            "knowledge_graph_search.sqlite"
        )

        search_index = KnowledgeGraphSearchIndex(
            search_database_path
        )

        search_index_result = search_index.build(builder)

        print("\nKNOWLEDGE GRAPH SEARCH INDEX")
        print("-" * 50)
        print(search_index_result)

        return {
            "graph_summary": graph_summary,
            "validation": validation,
            "graph_export_path": str(exported_path),
            "search_index": search_index_result
        }

    pipeline.execute_stage(
        "KNOWLEDGE_GRAPH",
        run_knowledge_graph
    )

    # --------------------------------------------------
    # SAVE UNIFIED PIPELINE REPORT
    # --------------------------------------------------

    report_path = pipeline.save_pipeline_report()

    print("\n" + "=" * 60)
    print("CROSS-DOMAIN INTELLIGENCE PIPELINE SUMMARY")
    print("=" * 60)

    print("\nPIPELINE SUMMARY:")
    print(pipeline.results["summary"])

    print("\nSTAGE RESULTS:")

    for stage_name, stage_result in pipeline.results["stages"].items():

        print(
            f"{stage_name}: "
            f"{stage_result['status']}"
        )

    print("\nUnified Report:", report_path)
    print("=" * 60)


if __name__ == "__main__":
    main()

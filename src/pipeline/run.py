
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


def main():

    pipeline = IntelligenceOrchestrator()

    orders_path = (
        "datasets/processed/olist/"
        "olist_orders_dataset.parquet"
    )

    customers_path = (
        "datasets/processed/olist/"
        "olist_customers_dataset.parquet"
    )

    # --------------------------------------------------
    # STAGE 1: INGESTION
    # --------------------------------------------------

    def run_ingestion():

        result = run_ingestion_pipeline(
            raw_directory="datasets/raw",
            processed_directory="datasets/processed",
            report_directory="logs/ingestion"
        )

        return {
            "result": result
        }

    pipeline.execute_stage("INGESTION", run_ingestion)

    # --------------------------------------------------
    # STAGE 2: DATA UNDERSTANDING
    # --------------------------------------------------

    def run_data_understanding():

        orders = pd.read_parquet(orders_path)

        engine = DataUnderstandingEngine(
            sample_size=100000
        )

        report = engine.analyze_dataset(
            data=orders,
            dataset_name="olist_orders"
        )

        report_path = engine.save_report(
            report,
            output_dir="logs/pipeline/data_understanding"
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

        orders = pd.read_parquet(orders_path)

        order_items = pd.read_parquet(
            "datasets/processed/olist/"
            "olist_order_items_dataset.parquet"
        )

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
            output_dir="logs/pipeline/data_discovery"
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

        orders = pd.read_parquet(orders_path)

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
            "logs/pipeline/"
            "olist_anomaly_investigation.csv"
        )

        saved_path = investigator.save_report(
            investigation,
            output_path=output_path
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
            "output": saved_path
        }

    pipeline.execute_stage(
        "ANOMALY_DETECTION",
        run_anomaly_detection
    )

    # --------------------------------------------------
    # STAGE 5: NLP PROCESSING
    # --------------------------------------------------

    def run_nlp_processing():

        reviews = pd.read_parquet(
            "datasets/processed/olist/"
            "olist_order_reviews_dataset.parquet"
        )

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

        output_path = (
            "logs/pipeline/"
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
            "output": output_path
        }

    pipeline.execute_stage(
        "NLP_PROCESSING",
        run_nlp_processing
    )

    # --------------------------------------------------
    # STAGE 6: KNOWLEDGE GRAPH CONSTRUCTION
    # --------------------------------------------------

    def run_knowledge_graph():

        loader = OlistGraphLoader()

        builder = loader.load_data(
            orders_path=orders_path,
            customers_path=customers_path
        )

        validator = KnowledgeGraphValidator()

        validation = validator.validate(builder)

        graph_summary = builder.get_graph_summary()

        return {
            "graph_summary": graph_summary,
            "validation": validation
        }

    pipeline.execute_stage(
        "KNOWLEDGE_GRAPH",
        run_knowledge_graph
    )

    # --------------------------------------------------
    # SAVE UNIFIED PIPELINE REPORT
    # --------------------------------------------------

    report_path = pipeline.save_pipeline_report()

    print("\n" + "=" * 55)
    print("CROSS-DOMAIN INTELLIGENCE PIPELINE SUMMARY")
    print("=" * 55)

    print(pipeline.results["summary"])

    for stage_name, stage_result in pipeline.results["stages"].items():
        print(
            f"{stage_name}: "
            f"{stage_result['status']}"
        )

    print("\nUnified Report:", report_path)
    print("=" * 55)


if __name__ == "__main__":
    main()

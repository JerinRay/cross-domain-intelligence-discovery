from src.discovery.cross_domain_pattern_engine import (
    CrossDomainPatternEngine
)
from src.discovery.olist_datasets import PROJECT_ROOT, load_scan_frames


def main():
    print("=" * 65)
    print("OLIST CROSS-DOMAIN PATTERN DISCOVERY")
    print("=" * 65)

    # Reads datasets/processed/olist/ (where ingestion writes) and falls back to
    # datasets/processed/.  Each table is sampled to 5,000 rows so the pairwise
    # analysis stays fast on a laptop.
    datasets = load_scan_frames(max_rows=5000, random_state=42)

    for name, dataframe in datasets.items():
        print(
            f"{name}: {len(dataframe):,} sampled rows, "
            f"{len(dataframe.columns)} columns"
        )

    print("\nRunning cross-domain analysis...")

    engine = CrossDomainPatternEngine(sample_size=3000)
    report = engine.analyze(datasets)

    output_path = engine.save_report(
        report, output_dir=str(PROJECT_ROOT / "logs" / "cross_domain")
    )

    print("\n" + "=" * 65)
    print("CROSS-DOMAIN ANALYSIS RESULTS")
    print("=" * 65)

    print("Datasets:", report["dataset_count"])
    print("Dataset pairs:", report["dataset_pair_count"])
    print(
        "Connected pairs:",
        report["connected_dataset_pair_count"]
    )
    print(
        "Relationship candidates:",
        report["total_relationship_candidates"]
    )
    print("Confidence:", report["confidence_summary"])

    print("\nPairwise results:")

    for pair in report["dataset_pair_analysis"]:
        print(
            f"{pair['dataset_a']} <-> {pair['dataset_b']}: "
            f"{pair['candidate_count']} candidates"
        )

    print("\nReport saved:", output_path)
    print("Status:", report["status"])
    print("\nAnalysis completed.")


if __name__ == "__main__":
    main()

import pandas as pd
import pytest

from src.discovery.cross_domain_pattern_engine import (
    CrossDomainPatternEngine
)


@pytest.fixture
def sample_datasets():
    customers = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3"],
        "city": ["A", "B", "C"]
    })

    orders = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "customer_id": ["C1", "C2", "C3"]
    })

    products = pd.DataFrame({
        "product_id": ["P1", "P2", "P3"],
        "category": ["X", "Y", "Z"]
    })

    return {
        "customers": customers,
        "orders": orders,
        "products": products
    }


def test_analyze_multiple_datasets(sample_datasets):
    engine = CrossDomainPatternEngine(sample_size=100)

    result = engine.analyze(sample_datasets)

    assert result["status"] == "SUCCESS"
    assert result["dataset_count"] == 3
    assert result["dataset_pair_count"] == 3


def test_detect_customer_order_relationship(sample_datasets):
    engine = CrossDomainPatternEngine(sample_size=100)

    result = engine.analyze(sample_datasets)

    pair = next(
        item for item in result["dataset_pair_analysis"]
        if item["dataset_a"] == "customers"
        and item["dataset_b"] == "orders"
    )

    assert pair["candidate_count"] >= 1


def test_confidence_summary(sample_datasets):
    engine = CrossDomainPatternEngine(sample_size=100)

    result = engine.analyze(sample_datasets)

    summary = result["confidence_summary"]

    assert set(summary.keys()) == {"HIGH", "MEDIUM", "LOW"}
    assert sum(summary.values()) == result["total_relationship_candidates"]


def test_reject_non_dictionary_input():
    engine = CrossDomainPatternEngine()

    with pytest.raises(TypeError):
        engine.analyze([])


def test_reject_single_dataset(sample_datasets):
    engine = CrossDomainPatternEngine()

    with pytest.raises(ValueError):
        engine.analyze({"customers": sample_datasets["customers"]})


def test_reject_empty_dataset():
    engine = CrossDomainPatternEngine()

    with pytest.raises(ValueError):
        engine.analyze({
            "customers": pd.DataFrame(),
            "orders": pd.DataFrame({"order_id": ["O1"]})
        })


def test_reject_non_dataframe():
    engine = CrossDomainPatternEngine()

    with pytest.raises(TypeError):
        engine.analyze({
            "customers": ["C1", "C2"],
            "orders": pd.DataFrame({"order_id": ["O1"]})
        })


def test_save_report(tmp_path, sample_datasets):
    engine = CrossDomainPatternEngine()

    result = engine.analyze(sample_datasets)

    filepath = engine.save_report(
        result,
        output_dir=str(tmp_path)
    )

    import json

    with open(filepath, encoding="utf-8") as file:
        saved = json.load(file)

    assert saved["status"] == "SUCCESS"
    assert saved["dataset_count"] == 3

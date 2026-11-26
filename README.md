# An Autonomous Cross-Domain Intelligence Discovery and Self-Evolving Knowledge Graph Framework

## 1. Project Overview

This project aims to develop an autonomous AI framework capable of discovering meaningful patterns, extracting knowledge, identifying anomalies, and reasoning across multiple independent data domains.

The framework integrates structured and unstructured data analysis, machine learning, natural language processing, and knowledge graph technologies to build an evidence-grounded intelligence system.

It will also investigate controlled knowledge evolution by detecting changes, identifying conflicting information, and updating knowledge representations based on validated evidence.

## 2. Problem Statement

Traditional data analytics systems generally operate within isolated datasets and predefined analytical workflows.

They often lack the ability to:
- Discover previously unknown relationships across independent domains.
- Combine structured and unstructured information.
- Maintain evidence and provenance for discovered knowledge.
- Detect evolving patterns and conflicting information.
- Update knowledge representations based on newly available evidence.

This project aims to address these limitations through an integrated intelligence discovery framework.

## 3. Project Objectives

1. Develop an automated multi-source data ingestion system.
2. Perform intelligent data profiling and understanding.
3. Discover hidden patterns using machine learning.
4. Identify unusual patterns using anomaly detection.
5. Extract entities and semantic information from text.
6. Discover evidence-supported cross-domain relationships.
7. Construct an evidence-grounded knowledge graph.
8. Track knowledge changes through graph versioning.
9. Detect data drift and conflicting information.
10. Implement controlled knowledge and model updates.
11. Provide explainable results with evidence provenance.

## 4. Proposed Architecture

The framework will contain the following major modules:

- Data Ingestion Engine
- Intelligent Data Understanding
- Pattern Discovery Engine
- Anomaly Detection Engine
- NLP Intelligence Engine
- Cross-Domain Reasoning Engine
- Knowledge Graph Engine
- Knowledge Evolution Engine
- Explainability and Visualization Layer

## 5. Dataset Sources

**Implemented and evaluated: Brazilian E-Commerce (Olist).** Its seven linked tables are
treated as separate domains: Customers, Orders, Order Items, Products, Sellers, Payments
and Reviews (plus Geolocation for inventory). Cross-domain discovery, the knowledge graph,
anomaly detection and NLP all run on these tables.

Any further dataset (CSV, JSON, Parquet or Excel) can be added at run time through the
dashboard's **Add Dataset** page; the self-evolving graph then proposes links to it.

Planned for future evaluation (not yet implemented):

| Dataset | Domain |
|---|---|
| Online Retail II | Retail |
| Credit Card Fraud Detection | Financial transactions |
| 20 Newsgroups | Text and document classification |

Cross-domain relationships are treated as hypotheses unless supported by evidence;
unrelated records are not artificially joined.

## 6. Technology Stack

### Programming
- Python 3.12

### Data Processing
- NumPy
- Pandas
- Polars
- PyArrow
- SciPy

### Machine Learning
- Scikit-learn
- PyTorch (planned)

### Graph Processing
- NetworkX

### Visualization
- Streamlit (dashboard)
- Plotly

### Planned Extensions
- Text embeddings and vector search
- FastAPI
- PostgreSQL

## 7. Expected Outcomes

The expected outcome is a modular research prototype that can:

- Ingest and understand multiple data sources.
- Discover patterns and anomalies.
- Extract semantic knowledge from text.
- Identify evidence-supported relationships across domains.
- Build and maintain a provenance-aware knowledge graph.
- Detect changes and conflicts in accumulated knowledge.
- Explain its findings through traceable evidence.

## 8. Development Status

Implemented: ingestion, data understanding, join-key and cross-domain discovery,
Isolation Forest anomaly detection, review-text NLP, knowledge graph (build, validate,
export, SQLite search index, community detection), explainability, the self-evolving
graph (upload → link candidates → accept/reject → new graph version) and the Streamlit
dashboard.

### How to run

1. Install dependencies: `pip install -r requirements.txt`
   then the spaCy NER model: `python -m spacy download xx_ent_wiki_sm`
2. Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
   and unzip the CSV files into `datasets/raw/olist/`.
3. Run the pipeline from the project root: `python -m src.pipeline.run`
4. Start the dashboard from the project root: `streamlit run frontend/app.py`

Run the tests with `python -m pytest`.


## 9. Project Structure

```text
project/
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── external/
├── src/
│   ├── ingestion/
│   ├── data_understanding/
│   ├── discovery/
│   ├── anomaly_detection/
│   ├── nlp/
│   ├── reasoning/
│   ├── knowledge_graph/
│   ├── evolution/
│   └── explainability/
├── models/
├── knowledge_base/
├── experiments/
├── tests/
├── configs/
├── notebooks/
├── logs/
├── requirements.txt
└── README.md
```
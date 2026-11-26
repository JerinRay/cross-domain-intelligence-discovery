"""
Incremental dataset onboarding + knowledge-graph evolution.

Uses your existing modules:
  ingestion      -> load_file, extract_metadata, validate_dataset, save_processed_file
  discovery      -> DiscoveryEngine (join keys + relationship hypotheses)
  knowledge_graph-> KnowledgeGraphBuilder + GraphEvolver (with evolution history)

Flow for ONE new dataset (nothing already in the graph is recomputed):
  1. ingest + validate + save Parquet
  2. profile columns
  3. compare ONLY the new dataset against each existing dataset (sampled, so RAM stays low)
  4. store relationship *candidates* (hypotheses, status=pending)
  5. add Dataset + Column nodes to a schema-level knowledge graph, bump version
  6. user accepts/rejects candidates -> accepted ones become graph edges (feedback loop)

State lives in knowledge_base/ (state.json + schema_graph.json), so nothing is lost on restart.
"""
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import pandas as pd

from src.discovery.engine import DiscoveryEngine
from src.ingestion.data_loader import SUPPORTED_FORMATS, load_file, save_processed_file
from src.ingestion.metadata_extractor import (
    extract_metadata,
    generate_ingestion_report,
    validate_dataset,
)
from src.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_evolver import GraphEvolver


def _slug(text):
    return re.sub(r"[^a-z0-9_]+", "_", str(text).strip().lower()).strip("_") or "dataset"


def _norm(col):
    return "".join(ch.lower() for ch in str(col) if ch.isalnum())


def _now():
    return datetime.now(timezone.utc).isoformat()


class IncrementalUpdater:
    def __init__(self, root=".", sample_rows=20000):
        self.root = Path(root)
        self.processed_dir = self.root / "datasets" / "processed"
        self.state_dir = self.root / "knowledge_base"
        self.report_dir = self.root / "logs" / "ingestion"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rows = sample_rows          # keeps pairwise discovery light on a laptop
        self.state_path = self.state_dir / "state.json"
        self.graph_path = self.state_dir / "schema_graph.json"
        self.state = self._load_state()

    # ---------------- persistence ----------------
    def _load_state(self):
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {"version": 0, "datasets": {}, "candidates": [], "history": []}

    def _save_state(self):
        self.state_path.write_text(json.dumps(self.state, indent=2, default=str))

    def _load_builder(self):
        builder = KnowledgeGraphBuilder()
        if self.graph_path.exists():
            data = json.loads(self.graph_path.read_text())
            builder.graph = nx.node_link_graph(data, edges="edges")
        return builder

    def _save_graph(self, builder):
        data = nx.node_link_data(builder.graph, edges="edges")
        self.graph_path.write_text(json.dumps(data, default=str))

    # ---------------- helpers ----------------
    def existing_datasets(self):
        """name -> parquet path for every processed dataset (deeper folders win over duplicates)."""
        found = {}
        for p in sorted(self.processed_dir.rglob("*.parquet"), key=lambda x: len(x.parts)):
            found[p.stem] = p
        return found

    def _sample(self, path):
        df = pd.read_parquet(path)
        if len(df) > self.sample_rows:
            df = df.sample(self.sample_rows, random_state=42)
        return df.reset_index(drop=True)

    def _learned_pairs(self):
        return {
            (_norm(c["column_a"]), _norm(c["column_b"]))
            for c in self.state["candidates"] if c["status"] == "accepted"
        }

    def _rejected_keys(self):
        return {
            (c["dataset_a"], c["column_a"], c["dataset_b"], c["column_b"])
            for c in self.state["candidates"] if c["status"] == "rejected"
        }

    @staticmethod
    def _ds_node(name):
        return f"dataset:{name}"

    @staticmethod
    def _col_node(ds, col):
        return f"column:{ds}.{col}"

    def _ensure_nodes(self, evolver, dataset, column, domain="unknown"):
        evolver.add_entity(self._ds_node(dataset), "Dataset", name=dataset, domain=domain)
        evolver.add_entity(self._col_node(dataset, column), "Column", dataset=dataset, name=column)
        evolver.add_relationship(self._ds_node(dataset), self._col_node(dataset, column), "HAS_COLUMN")

    # ---------------- main entry ----------------
    def add_dataset(self, file_path, name=None, domain="unknown", progress=None):
        """Onboard one dataset. `progress(stage, pct)` is optional (used by the UI)."""
        p = progress or (lambda stage, pct: None)
        timings, t0 = {}, time.time()
        file_path = Path(file_path)
        name = _slug(name or file_path.stem)

        if file_path.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format {file_path.suffix}. Use CSV, JSON, Parquet or Excel.")
        if name in self.state["datasets"] or name in self.existing_datasets():
            raise ValueError(f"A dataset named '{name}' already exists. Rename it and try again.")

        # 1. ingest
        t = time.time(); p("Ingest", 5)
        data = load_file(file_path)
        meta = extract_metadata(data, name)
        validation = validate_dataset(meta)
        if not validation["is_valid"]:
            raise ValueError("; ".join(validation["errors"]))
        out_path = save_processed_file(data, self.processed_dir / _slug(domain) / f"{name}.parquet")
        generate_ingestion_report(meta, validation, self.report_dir)
        timings["ingest"] = round(time.time() - t, 2)

        # 2. understand (profile)
        t = time.time(); p("Understand", 25)
        profile = [{
            "column": c,
            "dtype": meta["data_types"][c],
            "nulls": meta["missing_values"][c],
            "null_pct": round(100 * meta["missing_values"][c] / max(1, meta["row_count"]), 2),
            "distinct": int(data[c].nunique(dropna=True)),
        } for c in meta["columns"]]
        timings["understand"] = round(time.time() - t, 2)

        # 3. discover: new dataset vs each existing one only
        t = time.time()
        engine = DiscoveryEngine(sample_size=5000)
        new_sample = data.sample(min(len(data), self.sample_rows), random_state=42).reset_index(drop=True) \
            if len(data) > self.sample_rows else data.reset_index(drop=True)
        others = {k: v for k, v in self.existing_datasets().items() if k != name}
        learned, rejected = self._learned_pairs(), self._rejected_keys()
        found, failed_pairs = [], []
        for i, (other_name, other_path) in enumerate(others.items()):
            p(f"Discover ({other_name})", 30 + 50 * (i + 1) / max(1, len(others)))
            try:
                other = self._sample(other_path)
                report = engine.analyze(new_sample, other, name, other_name)
                for r in report["relationship_discovery"]["relationships"]:
                    key = (name, r["column_a"], other_name, r["column_b"])
                    if key in rejected:
                        continue
                    boost = 0.1 if (_norm(r["column_a"]), _norm(r["column_b"])) in learned else 0.0
                    score = round(0.7 * r["overlap_coefficient"] + 0.3 * r["name_similarity"] + boost, 3)
                    found.append({
                        "id": uuid.uuid4().hex[:8],
                        "dataset_a": name, "column_a": r["column_a"],
                        "dataset_b": other_name, "column_b": r["column_b"],
                        "relationship_type": r["relationship_type"],
                        "overlap": r["overlap_coefficient"], "name_similarity": r["name_similarity"],
                        "confidence": r["confidence"], "score": score,
                        "learned_boost": boost > 0,
                        "status": "pending", "created": _now(),
                        "evidence": (f"value overlap {r['overlap_coefficient']:.0%}, "
                                     f"name similarity {r['name_similarity']:.0%}, {r['relationship_type']}"),
                    })
            except Exception as exc:               # one bad pair must not stop the run
                failed_pairs.append({"dataset": other_name, "error": str(exc)})
        found.sort(key=lambda c: c["score"], reverse=True)
        timings["discover"] = round(time.time() - t, 2)

        # 4. graph: schema-level nodes for the new dataset
        t = time.time(); p("Graph", 88)
        builder = self._load_builder()
        evolver = GraphEvolver(builder)
        evolver.add_entity(self._ds_node(name), "Dataset", name=name, domain=domain,
                           rows=meta["row_count"], columns=meta["column_count"])
        for col in meta["columns"]:
            evolver.add_entity(self._col_node(name, col), "Column", dataset=name, name=col)
            evolver.add_relationship(self._ds_node(name), self._col_node(name, col), "HAS_COLUMN")
        self._save_graph(builder)
        timings["graph"] = round(time.time() - t, 2)

        # 5. version + state
        self.state["version"] += 1
        version = self.state["version"]
        self.state["datasets"][name] = {
            "path": str(out_path), "domain": domain, "rows": meta["row_count"],
            "columns": meta["column_count"], "version": version, "added": _now(),
            "profile": profile, "quality": validation["quality_status"],
        }
        self.state["candidates"].extend(found)
        diff = {
            "dataset": name, "version": version, "rows": meta["row_count"],
            "columns": meta["column_count"], "quality": validation["quality_status"],
            "warnings": len(validation["warnings"]),
            "datasets_compared": len(others), "candidates_found": len(found),
            "high_confidence": sum(c["confidence"] == "HIGH" for c in found),
            "nodes_added": 1 + meta["column_count"], "failed_pairs": failed_pairs,
            "timings": timings, "total_seconds": round(time.time() - t0, 2),
            "profile": profile,
        }
        self.state["history"].append({"version": version, "time": _now(), "event": "DATASET_ADDED",
                                      "dataset": name, "candidates": len(found),
                                      "evolution": evolver.get_evolution_summary()})
        self._save_state()
        p("Done", 100)
        return diff

    # ---------------- feedback loop ----------------
    def list_candidates(self, status="pending"):
        return sorted((c for c in self.state["candidates"] if c["status"] == status),
                      key=lambda c: c["score"], reverse=True)

    def decide(self, candidate_id, accept):
        cand = next((c for c in self.state["candidates"] if c["id"] == candidate_id), None)
        if cand is None:
            raise ValueError("Unknown candidate")
        cand["status"] = "accepted" if accept else "rejected"
        cand["decided"] = _now()
        builder = self._load_builder()
        evolver = GraphEvolver(builder)
        if accept:
            for ds, col in ((cand["dataset_a"], cand["column_a"]), (cand["dataset_b"], cand["column_b"])):
                domain = self.state["datasets"].get(ds, {}).get("domain", "existing")
                self._ensure_nodes(evolver, ds, col, domain)
            evolver.add_relationship(
                self._col_node(cand["dataset_a"], cand["column_a"]),
                self._col_node(cand["dataset_b"], cand["column_b"]),
                "JOINABLE_ON", overlap=cand["overlap"], confidence=cand["confidence"],
                relationship_type_detail=cand["relationship_type"],
                validation_status="ACCEPTED_BY_USER", evidence=cand["evidence"])
            self._save_graph(builder)
        self.state["history"].append({"version": self.state["version"], "time": _now(),
                                      "event": "LINK_ACCEPTED" if accept else "LINK_REJECTED",
                                      "candidate": candidate_id})
        self._save_state()

    # ---------------- rollback ----------------
    def rollback_dataset(self, name):
        """Undo one uploaded dataset: its files, graph nodes, and candidates."""
        info = self.state["datasets"].get(name)
        if not info:
            raise ValueError(f"'{name}' was not added through the upload flow")
        builder = self._load_builder()
        doomed = [n for n, d in builder.graph.nodes(data=True)
                  if n == self._ds_node(name) or (d.get("entity_type") == "Column" and d.get("dataset") == name)]
        builder.graph.remove_nodes_from(doomed)
        self._save_graph(builder)
        Path(info["path"]).unlink(missing_ok=True)
        self.state["candidates"] = [c for c in self.state["candidates"]
                                    if name not in (c["dataset_a"], c["dataset_b"])]
        del self.state["datasets"][name]
        self.state["history"].append({"version": self.state["version"], "time": _now(),
                                      "event": "DATASET_ROLLED_BACK", "dataset": name})
        self._save_state()

    # ---------------- read-only views ----------------
    def stats(self):
        g = self._load_builder().graph
        cands = self.state["candidates"]
        return {
            "version": self.state["version"],
            "uploaded_datasets": len(self.state["datasets"]),
            "pending": sum(c["status"] == "pending" for c in cands),
            "accepted": sum(c["status"] == "accepted" for c in cands),
            "rejected": sum(c["status"] == "rejected" for c in cands),
            "graph_nodes": g.number_of_nodes(), "graph_edges": g.number_of_edges(),
        }

    def history(self):
        return list(reversed(self.state["history"]))

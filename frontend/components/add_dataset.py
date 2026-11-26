"""Add Dataset page: upload -> profile -> incremental pipeline -> review suggested links."""
from pathlib import Path

import pandas as pd
import streamlit as st

from src.evolution.incremental_updater import IncrementalUpdater

STAGES = ["Ingest", "Understand", "Discover", "Graph"]


@st.cache_resource
def _updater(root):
    return IncrementalUpdater(root)


def _save_upload(root, uploaded):
    folder = Path(root) / "datasets" / "raw" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / uploaded.name
    dest.write_bytes(uploaded.getbuffer())
    return dest


def render_add_dataset(root):
    up = _updater(str(root))
    up.state = up._load_state()          # pick up changes made in earlier reruns

    # ---- summary strip ----
    s = up.stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Graph version", f"v{s['version']}")
    c2.metric("Uploaded datasets", s["uploaded_datasets"])
    c3.metric("Links to review", s["pending"])
    c4.metric("Accepted links", s["accepted"])

    tab_add, tab_review, tab_history = st.tabs(["Add dataset", "Review links", "Version history"])

    # ================= ADD =================
    with tab_add:
        uploaded = st.file_uploader("Drop a CSV, JSON, Parquet or Excel file",
                                    type=["csv", "json", "parquet", "xlsx", "xls"])
        if uploaded is not None:
            size_mb = uploaded.size / 1024 / 1024
            if size_mb > 500:
                st.error("File is larger than 500 MB. Split it or upload a sample.")
            else:
                col_a, col_b = st.columns(2)
                name = col_a.text_input("Dataset name", value=Path(uploaded.name).stem)
                domain = col_b.text_input("Domain tag", value="new_domain",
                                          help="e.g. logistics, finance, healthcare")
                st.caption(f"{uploaded.name} · {size_mb:.1f} MB · only this file is compared against "
                           "existing datasets; nothing already in the graph is recomputed.")

                if st.button("Run incremental pipeline", type="primary"):
                    bar = st.progress(0, text="Starting...")
                    try:
                        dest = _save_upload(root, uploaded)
                        diff = up.add_dataset(
                            dest, name, domain,
                            progress=lambda stage, pct: bar.progress(int(pct), text=f"{stage}..."))
                        bar.progress(100, text="Done")
                        st.session_state["last_diff"] = diff
                    except Exception as exc:      # clear message instead of a stack trace
                        bar.empty()
                        st.error(f"Could not add dataset: {exc}")

        diff = st.session_state.get("last_diff")
        if diff:
            st.subheader(f"What changed: {diff['dataset']} (v{diff['version']})")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rows", f"{diff['rows']:,}")
            m2.metric("Columns", diff["columns"])
            m3.metric("Datasets compared", diff["datasets_compared"])
            m4.metric("Link candidates", diff["candidates_found"],
                      help=f"{diff['high_confidence']} high confidence")
            st.caption(f"Data quality: {diff['quality']} · finished in {diff['total_seconds']}s · "
                       f"stage timings: {diff['timings']}")
            if diff["failed_pairs"]:
                st.warning(f"{len(diff['failed_pairs'])} comparison(s) failed: {diff['failed_pairs']}")
            with st.expander("Column profile"):
                st.dataframe(pd.DataFrame(diff["profile"]), use_container_width=True, hide_index=True)
            if diff["candidates_found"]:
                st.info("Open the **Review links** tab to accept or reject the suggested links.")

    # ================= REVIEW =================
    with tab_review:
        pending = up.list_candidates("pending")
        st.caption("Candidates are hypotheses, not verified relationships. "
                   "Your choices improve scoring on later uploads.")
        if not pending:
            st.success("Nothing waiting for review.")
        for cand in pending[:25]:
            with st.container(border=True):
                left, right = st.columns([4, 1.4])
                left.markdown(
                    f"**{cand['dataset_a']}.{cand['column_a']}** → "
                    f"**{cand['dataset_b']}.{cand['column_b']}**  \n"
                    f"{cand['confidence']} · score {cand['score']} · {cand['evidence']}"
                    + ("  \n_boosted by an earlier accepted link_" if cand["learned_boost"] else ""))
                a, r = right.columns(2)
                if a.button("Accept", key=f"acc_{cand['id']}"):
                    up.decide(cand["id"], True); st.rerun()
                if r.button("Reject", key=f"rej_{cand['id']}"):
                    up.decide(cand["id"], False); st.rerun()
        if len(pending) > 25:
            st.caption(f"Showing top 25 of {len(pending)}.")

    # ================= HISTORY =================
    with tab_history:
        hist = up.history()
        if hist:
            st.dataframe(pd.DataFrame(hist).drop(columns=["evolution"], errors="ignore"),
                         use_container_width=True, hide_index=True)
        else:
            st.caption("No changes yet.")
        uploaded_names = list(up.state["datasets"].keys())
        if uploaded_names:
            st.divider()
            target = st.selectbox("Undo an uploaded dataset", uploaded_names)
            if st.button("Roll back this dataset"):
                up.rollback_dataset(target)
                st.session_state.pop("last_diff", None)
                st.rerun()

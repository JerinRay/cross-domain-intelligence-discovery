"""Full report for a dataset uploaded on the Add Dataset page.

Shows the incremental pipeline that ran (Ingest -> Understand -> Discover -> Graph),
an overview of the file, column profile, charts, an Isolation Forest anomaly scan of
the uploaded rows, the link candidates found, and what changed in the graph.
Everything is rebuilt from knowledge_base/state.json + the saved Parquet, so the
report also works for older uploads and after a restart.
"""
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STEPS = [
    ("ingest", "Ingest", "Load + validate + save as Parquet",
     '<path d="M12 3v11m0 0-4-4m4 4 4-4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>'),
    ("understand", "Understand", "Profile every column",
     '<path d="M4 20V11M10 20V5M16 20v-7M2 20h20"/>'),
    ("discover", "Discover", "Compare with every existing dataset",
     '<circle cx="10.5" cy="10.5" r="6"/><path d="m20 20-4.8-4.8"/>'),
    ("graph", "Graph", "Add dataset + column nodes, new version",
     '<circle cx="6" cy="6.5" r="2.3"/><circle cx="18" cy="8" r="2.3"/><circle cx="12" cy="18" r="2.3"/>'
     '<path d="m8 7.2 7.8.6M7.2 8.5l3.6 7.4M16.8 10l-3.6 5.9"/>'),
]
_STAGE_KEY = {"Ingest": "ingest", "Understand": "understand", "Graph": "graph"}
PALETTE = ["#b57bff", "#4f86ff", "#26cbd8", "#f3b649", "#ff7ccf", "#52d69a"]

CSS = """
<style>
.ur-steps{display:flex;align-items:flex-start;gap:0;margin:6px 0 4px;overflow-x:auto;padding:6px 2px}
.ur-step{flex:0 0 auto;width:150px;text-align:center}
.ur-ring{width:58px;height:58px;margin:0 auto;border-radius:50%;display:grid;place-items:center;position:relative;
  border:2px solid rgba(255,255,255,.18);background:rgba(255,255,255,.04)}
.ur-ring svg{width:26px;height:26px;stroke:#e6e2d8;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.ur-step.done .ur-ring{border-color:rgba(63,214,138,.8);background:rgba(63,214,138,.10)}
.ur-step.done svg{stroke:#7ff0b4}
.ur-step.running .ur-ring{border-color:#e9b765;background:rgba(233,183,101,.14);animation:urpulse 1.3s ease-out infinite}
.ur-step.running svg{stroke:#f5cd86}
.ur-step.queued{opacity:.45}
.ur-badge{position:absolute;right:-4px;bottom:-3px;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;
  font-size:12px;font-weight:700;color:#06120b;background:#3fd68a;border:2px solid #101118}
.ur-name{margin-top:8px;font-weight:600;color:#fff;font-size:14.5px}
.ur-desc{font-size:12px;color:#a7a399;line-height:1.35;margin-top:2px;padding:0 6px}
.ur-time{font-size:12px;color:#f5cd86;margin-top:3px}
.ur-link{flex:1 1 30px;min-width:24px;height:3px;margin-top:29px;border-radius:2px;background:rgba(255,255,255,.12)}
.ur-link.done{background:linear-gradient(90deg,rgba(63,214,138,.85),rgba(63,214,138,.5))}
@keyframes urpulse{0%{box-shadow:0 0 0 0 rgba(233,183,101,.55)}100%{box-shadow:0 0 0 14px rgba(233,183,101,0)}}
.ur-h{font:600 19px 'Exo 2',system-ui,sans-serif;color:#fff;margin:18px 0 8px;display:flex;align-items:center;gap:8px}
.ur-h span{color:#e9b765}
.ur-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.ur-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:10px 14px}
.ur-card small{display:block;color:#a7a399;font-size:12.5px}
.ur-card b{color:#fff;font-size:22px;font-weight:600}
.ur-card b.txt{font-size:17px;word-break:normal;overflow-wrap:anywhere}
.ur-card b.ok{color:#7ff0b4}.ur-card b.warn{color:#f5cd86}.ur-card b.bad{color:#ff8a94}
.ur-note{font-size:13px;color:#cfcabd;margin:6px 0}
</style>
"""


def stepper_html(states, timings=None):
    """states: {step_key: done|running|queued}; timings: {step_key: seconds}."""
    timings = timings or {}
    parts = []
    for i, (key, label, desc, icon) in enumerate(STEPS):
        state = states.get(key, "queued")
        if i:
            parts.append(f'<div class="ur-link{" done" if state == "done" else ""}"></div>')
        badge = '<span class="ur-badge">✓</span>' if state == "done" else ""
        t = timings.get(key)
        t_html = f'<div class="ur-time">{t:.2f}s</div>' if isinstance(t, (int, float)) else ""
        parts.append(f'<div class="ur-step {state}"><div class="ur-ring"><svg viewBox="0 0 24 24">{icon}</svg>{badge}</div>'
                     f'<div class="ur-name">{label}</div><div class="ur-desc">{desc}</div>{t_html}</div>')
    return CSS + '<div class="ur-steps">' + "".join(parts) + "</div>"


def live_states(stage):
    """Progress-callback stage text -> stepper states while the upload runs."""
    key = "discover" if stage.startswith("Discover") else _STAGE_KEY.get(stage, "graph" if stage == "Done" else None)
    order = [s[0] for s in STEPS]
    if stage == "Done":
        return {k: "done" for k in order}
    idx = order.index(key) if key in order else 0
    return {k: ("done" if i < idx else "running" if i == idx else "queued") for i, k in enumerate(order)}


def _card(label, value, tone=""):
    return f'<div class="ur-card"><small>{escape(label)}</small><b class="{tone}">{escape(str(value))}</b></div>'


@st.cache_data(show_spinner=False)
def _load(path, mtime):
    return pd.read_parquet(path)


def _anomaly_scan(frame):
    """Isolation Forest on the numeric columns (same method as the main pipeline)."""
    from sklearn.ensemble import IsolationForest
    num = frame.select_dtypes(include="number")
    num = num.loc[:, num.nunique(dropna=True) > 1]
    # ID-like columns (unique integer per row) carry no signal
    num = num.loc[:, [c for c in num.columns if not (num[c].nunique() == len(num) and "id" in c.lower())]]
    if num.shape[1] < 2 or len(num) < 50:
        return None
    X = num.fillna(num.median(numeric_only=True))
    model = IsolationForest(contamination=0.02, random_state=42).fit(X)
    flags = model.predict(X) == -1
    scores = model.decision_function(X)
    z = ((X - X.mean()) / X.std(ddof=0).replace(0, 1)).abs()
    out = frame.loc[flags].copy()
    out.insert(0, "anomaly_score", np.round(scores[flags], 4))
    out.insert(1, "most_unusual_column", z.loc[flags].idxmax(axis=1).values)
    return {"features": list(num.columns), "count": int(flags.sum()), "total": len(frame),
            "rows": out.sort_values("anomaly_score").head(15)}


def render_upload_report(up, name, diff=None):
    info = up.state["datasets"].get(name)
    if not info:
        st.info("Upload a dataset to see its report here.")
        return
    path = Path(info["path"])
    timings = (diff or {}).get("timings") if diff and diff.get("dataset") == name else None

    # ---------------- 1. pipeline ----------------
    st.markdown(f'<div class="ur-h"><span>▷</span> Pipeline for <b>{escape(name)}</b> (v{info["version"]})</div>',
                unsafe_allow_html=True)
    st.markdown(stepper_html({s[0]: "done" for s in STEPS}, timings), unsafe_allow_html=True)
    if timings:
        st.caption(f"Finished in {diff['total_seconds']}s. Only this file was compared against existing datasets; "
                   "nothing already in the graph was recomputed.")

    if not path.exists():
        st.warning(f"The processed file is missing: {path}")
        return
    frame = _load(str(path), path.stat().st_mtime)
    num_cols = frame.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in frame.columns if c not in num_cols]
    missing_pct = frame.isna().mean().mean() * 100
    dupes = int(frame.duplicated().sum())

    # ---------------- 2. overview ----------------
    st.markdown('<div class="ur-h"><span>▤</span> Overview</div>', unsafe_allow_html=True)
    q = info.get("quality", "—")
    st.markdown('<div class="ur-cards">' + "".join([
        _card("Rows", f"{len(frame):,}"), _card("Columns", len(frame.columns)),
        _card("Numeric / text columns", f"{len(num_cols)} / {len(cat_cols)}"),
        _card("Missing values", f"{missing_pct:.1f}%", "ok" if missing_pct < 5 else "warn"),
        _card("Duplicate rows", f"{dupes:,}", "ok" if dupes == 0 else "warn"),
        _card("Data quality", q, "ok" if q == "CLEAN" else "warn"),
        _card("Domain tag", info.get("domain", "—"), "txt"),
    ]) + "</div>", unsafe_allow_html=True)

    # ---------------- 3. columns ----------------
    st.markdown('<div class="ur-h"><span>☷</span> Columns</div>', unsafe_allow_html=True)
    rows = []
    for c in frame.columns:
        s = frame[c]
        row = {"column": c, "type": str(s.dtype), "missing %": round(s.isna().mean() * 100, 2),
               "distinct": int(s.nunique(dropna=True)),
               "example": ", ".join(map(str, s.dropna().unique()[:3]))}
        if c in num_cols:
            row.update({"min": f"{s.min():,.4g}", "mean": f"{s.mean():,.4g}", "max": f"{s.max():,.4g}"})
        else:
            row.update({"min": "", "mean": "", "max": ""})
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # ---------------- 4. charts ----------------
    show_num = [c for c in num_cols if frame[c].nunique() > 10 and "id" not in c.lower()][:4]
    show_cat = [c for c in cat_cols if 1 < frame[c].nunique() <= 30][:2]
    if show_num or show_cat:
        st.markdown('<div class="ur-h"><span>◔</span> Distributions</div>', unsafe_allow_html=True)
        charts = [("num", c) for c in show_num] + [("cat", c) for c in show_cat]
        for i in range(0, len(charts), 2):
            cols = st.columns(2)
            for col, (kind, c) in zip(cols, charts[i:i + 2]):
                colour = PALETTE[(i + charts[i:i + 2].index((kind, c))) % len(PALETTE)]
                if kind == "num":
                    fig = go.Figure(go.Histogram(x=frame[c].dropna(), nbinsx=30, marker_color=colour, opacity=.85))
                else:
                    vc = frame[c].astype(str).value_counts().head(10)
                    fig = go.Figure(go.Bar(x=vc.index, y=vc.values, marker_color=colour))
                fig.update_layout(title=dict(text=c, font=dict(size=14, color="#f3efe6")), height=250,
                                  margin=dict(l=8, r=8, t=36, b=8), paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)", bargap=.08,
                                  xaxis=dict(tickfont=dict(color="#a7a399", size=11), gridcolor="rgba(255,255,255,.05)"),
                                  yaxis=dict(tickfont=dict(color="#a7a399", size=11), gridcolor="rgba(255,255,255,.06)"))
                col.plotly_chart(fig, config={"displayModeBar": False}, key=f"ur_{name}_{c}")

    # ---------------- 5. anomalies ----------------
    st.markdown('<div class="ur-h"><span>◬</span> Anomaly scan</div>', unsafe_allow_html=True)
    try:
        scan = _anomaly_scan(frame)
    except Exception as exc:
        scan = None
        st.caption(f"Anomaly scan unavailable: {exc}")
    if scan:
        rate = scan["count"] / scan["total"] * 100
        st.markdown('<div class="ur-cards">' + "".join([
            _card("Rows flagged", f"{scan['count']:,}", "warn" if scan["count"] else "ok"),
            _card("Anomaly rate", f"{rate:.2f}%"),
            _card("Columns used", len(scan["features"])),
        ]) + "</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="ur-note">Isolation Forest (2% contamination) on: {escape(", ".join(scan["features"]))}. '
                    'Lower score = more unusual. Unusual is not the same as wrong.</div>', unsafe_allow_html=True)
        if scan["count"]:
            st.dataframe(scan["rows"], width="stretch", hide_index=True)
    elif scan is None:
        st.caption("Needs at least 2 numeric columns and 50 rows for an anomaly scan.")

    # ---------------- 6. links ----------------
    st.markdown('<div class="ur-h"><span>⛓</span> Links found to existing data</div>', unsafe_allow_html=True)
    cands = sorted((c for c in up.state["candidates"] if c["dataset_a"] == name), key=lambda c: -c["score"])
    if cands:
        def _row_number_like(col):
            s_ = frame[col].dropna() if col in frame.columns else pd.Series(dtype=float)
            if s_.empty or not pd.api.types.is_integer_dtype(s_) or not s_.is_unique:
                return False
            return int(s_.max()) - int(s_.min()) + 1 == len(s_)      # 1, 2, 3, ... with no gaps

        def _note(c):
            if _row_number_like(c["column_a"]):
                return "row numbers (1, 2, 3…): matches any numbered table, likely chance"
            if c["name_similarity"] < 0.5:
                return "names differ: may be chance"
            return ""

        likely_noise = sum(bool(_note(c)) for c in cands)
        table = pd.DataFrame([{
            "this column": c["column_a"], "links to": f'{c["dataset_b"]}.{c["column_b"]}',
            "confidence": c["confidence"], "value overlap": f'{c["overlap"]:.0%}',
            "name similarity": f'{c["name_similarity"]:.0%}', "status": c["status"],
            "note": _note(c),
        } for c in cands])
        st.dataframe(table, width="stretch", hide_index=True)
        msg = f"{len(cands)} candidate link(s). Accept or reject them in the **Review links** tab."
        if likely_noise:
            msg += (f" {likely_noise} look like coincidences (see the note column): small numbers, codes or row "
                    "numbers often match unrelated tables, e.g. Dependents 0–3 matching instalment counts. "
                    "Rejecting them teaches the framework not to suggest them again.")
        st.info(msg)
    else:
        st.success("No links to the existing datasets were found. This data looks unrelated to what is already in the graph.")

    # ---------------- 7. graph change ----------------
    st.markdown('<div class="ur-h"><span>✣</span> What changed in the knowledge graph</div>', unsafe_allow_html=True)
    accepted = sum(c["status"] == "accepted" for c in cands)
    st.markdown('<div class="ur-cards">' + "".join([
        _card("Graph version", f"v{info['version']}"),
        _card("Nodes added", 1 + int(info.get("columns", len(frame.columns)))),
        _card("Links accepted", accepted, "ok" if accepted else ""),
        _card("Links waiting", sum(c["status"] == "pending" for c in cands)),
    ]) + "</div>", unsafe_allow_html=True)
    st.caption("Nodes added = 1 dataset node + 1 node per column. Accepted links become JOINABLE_ON edges.")

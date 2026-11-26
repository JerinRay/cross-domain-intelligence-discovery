"""Floating chat box (bottom-right on every page).

* Without an API key it answers common questions straight from the live project
  data (anomalies, graph, pipeline, health, discoveries, datasets, versions).
* With a Gemini API key (entered in the chat's "Gemini (optional)" section) questions go to Gemini.
* Quick-question buttons stay visible, so you can keep asking without clearing the chat.

`facts` is a plain dict built by app.py, so this module never touches app globals.
"""
import json
import re
import urllib.request
from datetime import datetime
from html import escape

import streamlit as st

# (button label, question it asks) - shown under the chat at all times
SHORTCUTS = [
    ("⚠ Anomalies", "How many anomalies were found?"),
    ("✓ Health", "Is the system healthy?"),
    ("⌕ Discoveries", "What did discovery find?"),
    ("✣ Graph", "Summarise the knowledge graph"),
    ("▷ Pipeline", "When did the pipeline last run?"),
    ("⟲ Versions", "What is the graph version?"),
]


def _n(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


# ----------------------------------------------------------------- local answers
def local_answer(question, f):
    """Answer from project facts. Returns markdown."""
    q = question.lower()
    has = lambda *words: any(w in q for w in words)

    if has("anomal", "outlier", "fraud", "isolation"):
        rate = f["anomaly_rate"]
        return (f"**{_n(f['anomaly_count'])} orders** were flagged as anomalies out of "
                f"{_n(f['anomaly_total'])} ({rate:.2f}%), using **{f['anomaly_method']}**. "
                f"{_n(f['normal_count'])} orders look normal.\n\n"
                "An anomaly means *unusual*, not confirmed fraud. Open **Intelligence** to inspect them.")
    if has("health", "working", "status", "ok?", "broken", "error"):
        lines = "\n".join(f"- **{name}**: {state_word}" for name, state_word in f["health"])
        return f"System Health says **{f['health_text']}**.\n\n{lines}"
    if has("pipeline", "stage", "run", "last run", "duration"):
        return (f"The pipeline status is **{f['pipeline_status']}**: {f['stages_ok']} of {f['stages_total']} "
                f"stages succeeded. Last run: **{f['last_run']}** (took {f['duration']}).\n\n"
                "Use **Run pipeline** on the Dashboard to refresh everything.")
    if has("discover", "cross", "hypothes", "scan", "candidate", "join"):
        return (f"The cross-domain scan compared **{f['scan_pairs']} dataset pairs**, found "
                f"**{f['scan_connected']} connected pairs** and **{f['scan_hypotheses']} relationship "
                f"hypotheses** ({f['scan_when']}).\n\nHypotheses are not verified joins: they are "
                "based on value overlap and column-name similarity.")
    if has("evolv", "version", "upload", "accept", "reject", "add dataset"):
        return (f"The self-evolving graph is at **v{f['graph_version']}** with **{f['uploads']} uploaded "
                f"datasets**: {f['accepted']} links accepted, {f['rejected']} rejected, "
                f"{f['pending']} waiting for review.\n\nUpload a file on **Add Dataset** to create the next version.")
    if has("relationship", "edge", "link", "degree"):
        top = ", ".join(f"{k.replace('_', ' ').title()} ({_n(v)})" for k, v in f["top_relationships"])
        return (f"The knowledge graph has **{_n(f['relationships'])} relationships** "
                f"(average degree {f['avg_degree']:.2f}). Most common types: {top or 'not available'}.")
    if has("graph", "entit", "node", "domain", "largest", "biggest"):
        top = ", ".join(f"{k} ({_n(v)})" for k, v in f["top_domains"])
        return (f"The knowledge graph has **{_n(f['entities'])} entities** and **{_n(f['relationships'])} "
                f"relationships** across **{f['domain_count']} domains**. Largest domains: {top or 'not available'}.")
    if has("dataset", "record", "table", "row", "data"):
        return (f"**{f['datasets']} datasets** are loaded with **{_n(f['records'])} records** in total. "
                "See **Data Management** to search and download them.")
    if has("hello", "hi", "hey", "help", "what can"):
        return ("Hi! I can answer questions about this project's results, for example: anomalies, "
                "system health, the pipeline, cross-domain discoveries, the knowledge graph, datasets "
                "and graph versions. Add a Gemini API key in the **⚙ Gemini (optional)** section of this chat for open-ended questions.")
    return ("I can answer from the project data about **anomalies, health, the pipeline, discoveries, "
            "the knowledge graph, datasets and graph versions**. Try one of those, or add a Gemini API key "
            "in the **⚙ Gemini (optional)** section of this chat for open-ended questions.")


# ----------------------------------------------------------------- Gemini
def gemini_answer(messages, f):
    key = st.session_state.get("chat_api_key", "").strip()
    model = st.session_state.get("chat_model", "gemini-2.0-flash")
    context = (
        "You are the assistant inside the Cross-Domain Intelligence Platform. Answer briefly, "
        "using these live facts when relevant:\n" + json.dumps(f, default=str)
    )
    contents = [{"role": "user", "parts": [{"text": f"[CONTEXT]\n{context}"}]},
                {"role": "model", "parts": [{"text": "Understood."}]}]
    contents += [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                 for m in messages[-12:]]
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        data=json.dumps({"contents": contents,
                         "generationConfig": {"temperature": 0.5, "maxOutputTokens": 600}}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response.")


def _reply(question, f):
    messages = st.session_state.chat_messages
    if st.session_state.get("chat_api_key", "").strip():
        try:
            return gemini_answer(messages, f), "Gemini"
        except Exception as exc:  # fall back to project data if Gemini fails
            return (local_answer(question, f) + f"\n\n_(Gemini unavailable: {type(exc).__name__}; "
                    "answered from project data.)_"), "project data"
    return local_answer(question, f), "project data"


def _ask(question, f):
    question = question.strip()
    if not question:
        return
    now = datetime.now().strftime("%H:%M")
    st.session_state.chat_messages.append({"role": "user", "content": question, "time": now})
    answer, source = _reply(question, f)
    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "time": now, "source": source})


# ----------------------------------------------------------------- UI
CSS = """
<style>
.st-key-chat_fab{position:fixed!important;right:28px;bottom:26px;z-index:999;width:auto!important}
.st-key-chat_fab button{border-radius:999px!important;min-height:54px!important;padding:0 22px!important;
  background:linear-gradient(135deg,#ffe0a1,#b9853c)!important;border:1px solid rgba(255,220,160,.8)!important;
  box-shadow:0 10px 30px rgba(233,183,101,.38),0 0 0 6px rgba(233,183,101,.10)!important}
.st-key-chat_fab button p{color:#1d1406!important;font-weight:700!important;font-size:16px!important}
[data-testid="stPopoverBody"]:has(.cb-head){width:440px!important;max-width:92vw!important;
  background:#12131b!important;border:1px solid rgba(233,183,101,.35)!important;border-radius:18px!important;
  box-shadow:0 24px 60px rgba(0,0,0,.55)!important}
.cb-head{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.cb-av{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;font-size:16px;color:#1d1406;
  background:linear-gradient(135deg,#ffe0a1,#b9853c)}
.cb-title{font:700 16px 'Exo 2',system-ui,sans-serif;color:#fff}
.cb-sub{font-size:12px;color:#9a9fae}.cb-sub i{display:inline-block;width:7px;height:7px;border-radius:50%;
  background:#3fd68a;margin-right:5px;box-shadow:0 0 8px #3fd68a}
.cb-log{max-height:min(330px,46vh);overflow-y:auto;display:flex;flex-direction:column-reverse;gap:8px;padding:6px 4px 10px;margin-bottom:6px;border-bottom:1px solid rgba(255,255,255,.07)}
.cb-log::-webkit-scrollbar{width:6px}.cb-log::-webkit-scrollbar-thumb{background:rgba(233,183,101,.35);border-radius:3px}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stFormSubmitButton"] button{min-width:72px;white-space:nowrap}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stFormSubmitButton"] button p{white-space:nowrap}
.cb-msg{max-width:86%;padding:9px 12px;border-radius:14px;font-size:14px;line-height:1.5;color:#f1ede4}
.cb-msg.user{align-self:flex-end;background:linear-gradient(135deg,#e7b866,#b98538);color:#1d1406;border-bottom-right-radius:4px}
.cb-msg.ai{align-self:flex-start;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-bottom-left-radius:4px}
.cb-msg small{display:block;font-size:10.5px;opacity:.65;margin-top:4px}
.cb-empty{font-size:13.5px;color:#cfcabd;padding:8px 2px}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="InputInstructions"]{display:none!important}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] input{background:rgba(255,255,255,.05)!important;
  border:1px solid rgba(233,183,101,.35)!important;border-radius:12px!important;color:#f3efe6!important;min-height:44px}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] input::placeholder{color:#a7a399!important;opacity:1}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] input:focus{border-color:#e9b765!important;
  box-shadow:0 0 0 3px rgba(233,183,101,.18)!important}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] [data-baseweb="base-input"]{background:#1b1d27!important;border-color:transparent!important;border-radius:12px!important}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stTextInput"] input{background:#1b1d27!important}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stFormSubmitButton"] button{min-height:44px;border-radius:12px!important}
.st-key-cb_clear button{min-height:30px!important;padding:2px 10px!important}
.st-key-cb_clear button p,.st-key-cb_clear p{font-size:13px!important;color:#a7a399!important}
.st-key-cb_clear button:hover p{color:#f5cd86!important}
.cb-sug{font-size:11.5px;color:#8f8a7f;margin:2px 2px 4px;text-transform:uppercase;letter-spacing:.06em}
[class*="st-key-cbs_"] button{min-height:32px!important;padding:3px 10px!important;border-radius:999px!important;
  background:rgba(233,183,101,.08)!important;border:1px solid rgba(233,183,101,.3)!important}
[class*="st-key-cbs_"] button p{font-size:12.5px!important;color:#f3e2c0!important;white-space:nowrap!important}
[class*="st-key-cbs_"] button:hover{border-color:#e9b765!important;background:rgba(233,183,101,.16)!important}
/* compact shortcut pills: more specific than the dashboard's global button styles */
[data-testid="stPopoverBody"] [class*="st-key-cbs_"] button{padding:2px 6px!important;min-height:34px!important}
[data-testid="stPopoverBody"] [class*="st-key-cbs_"] button p,
[data-testid="stPopoverBody"] [class*="st-key-cbs_"] button div{font-size:12.5px!important;line-height:1.2!important;
  white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;letter-spacing:0!important}
[data-testid="stPopoverBody"]:has(.cb-head) [data-testid="stHorizontalBlock"]{gap:.45rem!important}
</style>
"""


def _md_to_html(text):
    """Tiny markdown subset for bubbles: **bold**, *italic*, `code`, line breaks, '- ' lists."""
    out = escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    out = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", out)
    out = re.sub(r"_\((.+?)\)_", r"<i>(\1)</i>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"(?m)^- ", "• ", out)
    return out.replace("\n", "<br>")


GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]


def _sync_key():
    st.session_state.chat_api_key = st.session_state.get("cb_key", "")


def _sync_model():
    st.session_state.chat_model = st.session_state.get("cb_model", GEMINI_MODELS[0])


def render_chat_box(facts):
    """Floating ✦ Ask AI button; the chat opens in a popover."""
    import os
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("chat_api_key", os.environ.get("GEMINI_API_KEY", ""))
    st.session_state.setdefault("chat_model", GEMINI_MODELS[0])
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        holder = st.container(key="chat_fab")
    except TypeError:
        holder = st.container()
    with holder:
        with st.popover("✦  Ask AI"):
            pending = st.session_state.pop("chat_fab_pending", None)
            if pending:
                _ask(pending, facts)
            using_gemini = bool(st.session_state.get("chat_api_key", "").strip())

            # ---- header: title + Clear ----
            h1, h2 = st.columns([4, 1.2], vertical_alignment="center")
            h1.markdown(
                '<div class="cb-head"><div class="cb-av">✦</div><div><div class="cb-title">Project Assistant</div>'
                f'<div class="cb-sub"><i></i>{"Gemini" if using_gemini else "Answers from your project data"}'
                '</div></div></div>', unsafe_allow_html=True)
            if st.session_state.chat_messages:
                try:
                    clear = h2.button("Clear", key="cb_clear", type="tertiary", width="stretch")
                except Exception:
                    clear = h2.button("Clear", key="cb_clear", width="stretch")
                if clear:
                    st.session_state.chat_messages = []
                    st.rerun()

            # ---- conversation ----
            msgs = st.session_state.chat_messages[-10:]
            if msgs:
                bubbles = "".join(
                    f'<div class="cb-msg {"user" if m["role"] == "user" else "ai"}">{_md_to_html(m["content"])}'
                    f'<small>{escape(m.get("time", ""))}</small></div>' for m in reversed(msgs))
                st.markdown(f'<div class="cb-log">{bubbles}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="cb-empty">Tap a topic below or type your own question.</div>',
                            unsafe_allow_html=True)

            # ---- shortcuts: always visible, so you never have to clear to ask again ----
            st.markdown('<div class="cb-sug">Quick questions</div>', unsafe_allow_html=True)
            for row in (SHORTCUTS[:3], SHORTCUTS[3:]):
                cols = st.columns(3)
                for col, (label, question) in zip(cols, row):
                    if col.button(label, key=f"cbs_{label}", width="stretch", help=question):
                        st.session_state.chat_fab_pending = question
                        st.rerun()

            # ---- typing box ----
            with st.form("cb_form", clear_on_submit=True, border=False):
                c1, c2 = st.columns([3.6, 1.4], vertical_alignment="center")
                text = c1.text_input("Message", placeholder="Type a question…", label_visibility="collapsed")
                sent = c2.form_submit_button("Send", type="primary", width="stretch")
            if sent and text.strip():
                st.session_state.chat_fab_pending = text
                st.rerun()

            # ---- optional Gemini (used to live on the AI Assistant page) ----
            with st.expander("⚙  Gemini (optional)"):
                st.text_input("Gemini API key", value=st.session_state.chat_api_key, type="password",
                              placeholder="AIza…", key="cb_key", on_change=_sync_key,
                              help="Get a key at https://aistudio.google.com. Kept in this session only.")
                model = st.session_state.chat_model
                st.selectbox("Model", GEMINI_MODELS,
                              index=GEMINI_MODELS.index(model) if model in GEMINI_MODELS else 0,
                              key="cb_model", on_change=_sync_model)
                st.caption("Without a key, answers come from your project data. With a key, Gemini answers "
                           "any question using the same live numbers.")
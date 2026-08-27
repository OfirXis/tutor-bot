"""
app.py — Course Tutor · curriculum-gated hybrid RAG chat.

Run:  streamlit run app.py
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import rag_engine as rag

load_dotenv()
os.chdir(Path(__file__).parent)

# ─────────────────────────────────────────────────────────────────────────────
# Page + theme
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Course Tutor",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Neutral dark palette — modeled on the flat, low-chroma look shared by
   ChatGPT / Claude / Gemini: no gradients, one restrained accent. */
:root {
    --bg:        #212121;
    --bg-sidebar:#171717;
    --surface:   #2f2f2f;
    --surface-2: #262626;
    --border:    #3a3a3a;
    --text:      #ececec;
    --text-dim:  #b4b4b4;
    --text-faint:#8e8e8e;
    --accent:    #10a37f;
}

html, body, .stApp { background: var(--bg) !important; }
* { font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }
code, pre, kbd { font-family: 'JetBrains Mono', Consolas, monospace !important; }

#MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 2rem !important; padding-bottom: 8rem !important; max-width: 720px; }

/* ── typography in chat ─────────────────────────────────────────────── */
.main p, .main li, .main span, .main td, .main th { color: var(--text); font-size: .98rem; line-height: 1.7; }
.main h1, .main h2, .main h3, .main h4 { color: var(--text); font-weight: 600; }

/* ── chat messages: no avatars, alignment carries the meaning ─────────── */
/* avatar = the stChatMessage child that ISN'T the stChatMessageContent div */
[data-testid="stChatMessage"] > div:not([data-testid="stChatMessageContent"]) { display: none !important; }

[data-testid="stChatMessage"] {
    display: flex !important;
    background: transparent !important;
    border: none !important;
    padding: .3rem 0 !important;
    max-width: 100%;
}
/* user → right-aligned bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"][aria-label="Chat message from user"]) {
    justify-content: flex-end;
}
[data-testid="stChatMessageContent"][aria-label="Chat message from user"] {
    background: var(--surface) !important;
    border-radius: 20px !important;
    padding: .6rem 1.1rem !important;
    max-width: 78%;
    width: fit-content;
}
/* assistant → plain full-width text, no bubble */
[data-testid="stChatMessageContent"][aria-label="Chat message from assistant"] {
    padding: .55rem 0 1rem 0 !important;
    width: 100%;
}

/* code blocks */
.main pre {
    background: #171717 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 14px !important;
}
.main pre code { color: #e6e6e6 !important; font-size: .85rem !important; }
.main :not(pre) > code {
    background: rgba(255,255,255,.08) !important;
    color: #ffb98a !important;
    padding: 2px 6px; border-radius: 5px; font-size: .84em !important;
}

/* KaTeX */
.katex { color: var(--text) !important; font-size: 1.03em !important; }

/* tables */
.main table { border-collapse: collapse; width: 100%; }
.main td, .main th { border: 1px solid var(--border) !important; padding: 6px 12px !important; }
.main th { background: var(--surface-2) !important; }

/* ── chat input ─────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 26px !important;
    box-shadow: 0 4px 18px rgba(0,0,0,.35) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #5a5a5a !important;
    box-shadow: 0 4px 18px rgba(0,0,0,.35) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-size: .96rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-faint) !important; }
[data-testid="stChatInput"] button {
    background: var(--text) !important;
    border-radius: 50% !important;
}
[data-testid="stChatInput"] button svg { color: var(--bg) !important; }
[data-testid="stBottomBlockContainer"], [data-testid="stBottom"] > div {
    background: linear-gradient(180deg, transparent, var(--bg) 45%) !important;
}

/* ── sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small { color: var(--text-faint) !important; }
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: .75rem 0 !important; }

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] .stTextInput input, [data-testid="stSidebar"] .stNumberInput input {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}
[data-baseweb="popover"] li, [data-baseweb="menu"] { background: var(--surface) !important; color: var(--text) !important; }

/* radio → flat segmented control */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    gap: 2px; background: var(--surface-2); border-radius: 10px; padding: 3px;
}
[data-testid="stSidebar"] .stRadio label {
    border-radius: 8px; padding: 6px 10px; width: 100%;
    transition: background .15s;
}
[data-testid="stSidebar"] .stRadio label:has(input:checked) { background: var(--surface); }

/* buttons */
.stButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: background .15s, border-color .15s !important;
}
.stButton > button:hover { background: var(--surface-2) !important; border-color: #4d4d4d !important; }

/* expanders (sources) */
[data-testid="stExpander"] {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary { color: var(--text-faint) !important; font-size: .84rem !important; }

/* status pill + hero */
.pill {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 13px;
    font-size: .78rem; color: var(--text-dim);
}
.pill .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }
.hero { text-align: center; padding: 3rem 0 1.4rem; }
.hero .logo {
    width: 44px; height: 44px; margin: 0 auto 16px; border-radius: 12px;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.hero h1 { font-size: 1.7rem; font-weight: 600; margin: 0 0 6px; color: var(--text); }
.hero p { color: var(--text-faint); font-size: .95rem; margin: 0; }

.src-line { color: var(--text-faint); font-size: .84rem; margin: 2px 0; }
.src-line b { color: var(--text-dim); font-weight: 500; }

/* scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 6px; }
::-webkit-scrollbar-track { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Cached resources
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading retrieval index…")
def get_retriever():
    return rag.HybridRetriever()


@st.cache_resource
def get_llm_cached(provider: str, model: str):
    os.environ["LLM_PROVIDER"] = provider
    if provider == "ollama":
        os.environ["OLLAMA_LLM_MODEL"] = model
    elif provider == "github":
        os.environ["GITHUB_MODEL"] = model
    elif provider == "openai":
        os.environ["OPENAI_MODEL"] = model
    return rag.get_llm()


@st.cache_data(ttl=30)
def ollama_models() -> list[str]:
    try:
        import urllib.request
        import json as _json
        url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/tags"
        with urllib.request.urlopen(url, timeout=2) as r:
            return sorted(m["name"] for m in _json.load(r)["models"])
    except Exception:
        return []


def fix_math(text: str) -> str:
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    return re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)


MAX_VERBATIM = 6  # exchanges sent verbatim; older ones become a breadcrumb


def trimmed_history(full: list) -> list:
    if len(full) <= MAX_VERBATIM * 2:
        return full
    older, recent = full[:-MAX_VERBATIM * 2], full[-MAX_VERBATIM * 2:]
    lines = []
    for i in range(0, len(older) - 1, 2):
        q = older[i].content[:70].replace("\n", " ")
        a = older[i + 1].content[:110].replace("\n", " ")
        lines.append(f"• Q: “{q}…” → A: “{a}…”")
    return [
        HumanMessage("[Recap of earlier discussion:\n" + "\n".join(lines) +
                     "\nBriefly re-explain, don't repeat in full, if these come up again.]"),
        AIMessage("[Noted — I'll build on what we already covered.]"),
    ] + recent


# ─────────────────────────────────────────────────────────────────────────────
# Guards: index must exist
# ─────────────────────────────────────────────────────────────────────────────

if not rag.INDEX_DIR.exists() or not rag.CHUNKS_FILE.exists():
    st.markdown(
        "<div class='hero'><div class='logo'>🎓</div><h1>Course Tutor</h1>"
        "<p>The course index hasn't been built yet.</p></div>",
        unsafe_allow_html=True,
    )
    st.code("python build_index.py", language="powershell")
    st.stop()

meta = rag.load_meta()
homework = rag.load_homework()
retriever = get_retriever()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🎓 Course Tutor")
    st.caption("Curriculum-gated hybrid RAG")
    st.divider()

    mode = st.radio("Mode", ["📖 Learn", "💪 Homework"], label_visibility="collapsed")
    is_hw = "Homework" in mode

    if not is_hw:
        tut_ids = sorted(meta, key=rag.tutorial_week)
        sel = st.selectbox(
            "Week / tutorial", tut_ids,
            format_func=lambda t: meta[t].get("display_name", t),
            index=len(tut_ids) - 1,
        )
        week = rag.tutorial_week(sel)
        display_name = meta[sel].get("display_name", sel)
        topics = meta[sel].get("topics", [])
    else:
        hw_ids = sorted(homework, key=lambda k: homework[k].get("week", 0))
        sel = st.selectbox(
            "Assignment", hw_ids,
            format_func=lambda k: f"Week {homework[k].get('week', '?')} · {homework[k].get('title', k)}",
        )
        week = homework[sel].get("week", 1)
        display_name = homework[sel].get("title", sel)
        topics = sorted({
            t for k, v in homework.items() if v.get("week", 0) <= week for t in v.get("topics", [])
        })

    st.divider()
    st.markdown("**Model**")

    providers = ["ollama", "github", "openai"]
    provider = st.selectbox(
        "Provider", providers,
        index=providers.index(os.getenv("LLM_PROVIDER", "ollama"))
        if os.getenv("LLM_PROVIDER", "ollama") in providers else 0,
        format_func={"ollama": "Ollama (local · free)", "github": "GitHub Models (free)",
                     "openai": "OpenAI (paid)"}.get,
    )

    if provider == "ollama":
        local = ollama_models()
        if local:
            default = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")
            model = st.selectbox("Model", local,
                                 index=local.index(default) if default in local else 0)
        else:
            st.error("Ollama isn't running — start it or pick another provider.")
            model = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")
    elif provider == "github":
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "Phi-3.5-mini-instruct",
                                       "Meta-Llama-3.1-8B-Instruct"])
        if not os.getenv("GITHUB_TOKEN"):
            tok = st.text_input("GitHub token", type="password", placeholder="github_pat_… / ghp_…")
            if tok:
                os.environ["GITHUB_TOKEN"] = tok
    else:
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"])
        if not os.getenv("OPENAI_API_KEY"):
            key = st.text_input("OpenAI key", type="password", placeholder="sk-…")
            if key:
                os.environ["OPENAI_API_KEY"] = key

    with st.expander("⚙️ Retrieval"):
        k_val = st.slider("Passages", 2, 8, 4)
        modes = ["dense", "hybrid", "hybrid+rerank"]
        ret_mode = st.selectbox(
            "Mode", modes,
            index=modes.index(rag.RETRIEVAL_MODE) if rag.RETRIEVAL_MODE in modes else 0,
            format_func={"dense": "Dense (benchmark winner · fast)",
                         "hybrid": "Hybrid (dense + BM25)",
                         "hybrid+rerank": "Hybrid + rerank (thorough · slow)"}.get,
        )
        show_sources = st.toggle("Show sources", value=True)

    st.divider()
    if st.button("🗑  Clear conversation", use_container_width=True):
        st.session_state.pop("history", None)
        st.session_state.pop("display", None)
        st.rerun()
    st.caption(f"Embeddings: `{rag.EMBED_MODEL.split('/')[-1]}` · index: "
               f"{len(retriever.chunks)} chunks")

# Reset chat when the context changes
ctx_key = f"{mode}|{sel}"
if st.session_state.get("ctx") != ctx_key:
    st.session_state.ctx = ctx_key
    st.session_state.history = []
    st.session_state.display = []

# ─────────────────────────────────────────────────────────────────────────────
# Hero + suggestions (empty chat)
# ─────────────────────────────────────────────────────────────────────────────

pending = None

if not st.session_state.get("display"):
    subtitle = ("Socratic guidance — hints and questions, never the final answer."
                if is_hw else "Grounded in your course material, week by week.")
    st.markdown(
        f"<div class='hero'><div class='logo'>{'💪' if is_hw else '🎓'}</div>"
        f"<h1>{display_name}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='text-align:center;margin-bottom:1.3rem'><span class='pill'>"
        f"<span class='dot'></span>{rag.llm_label()} · week {week} scope</span></div>",
        unsafe_allow_html=True,
    )

    if is_hw:
        chips = ["Where should I start?", "What technique fits this problem?",
                 "Can you check my reasoning so far?", "Give me a small hint."]
    else:
        pool = topics[-8:] if len(topics) > 8 else topics
        chips = [f"Explain: {t}" for t in pool[:2]] + [f"Give me an example of {t.lower()}" for t in pool[2:3]]
        chips.append("Quiz me on this week's material")

    cols = st.columns(2)
    for i, chip in enumerate(chips[:4]):
        if cols[i % 2].button(chip, key=f"chip{i}", use_container_width=True):
            pending = chip

# ─────────────────────────────────────────────────────────────────────────────
# Conversation
# ─────────────────────────────────────────────────────────────────────────────

for m in st.session_state.get("display", []):
    with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🎓"):
        st.markdown(m["content"])
        if m.get("sources") and show_sources:
            with st.expander(f"📚 {len(m['sources'])} sources"):
                for s in m["sources"]:
                    st.markdown(f"<div class='src-line'><b>{s['section']}</b> · score {s['score']:.2f}</div>",
                                unsafe_allow_html=True)

user_input = st.chat_input(f"Ask about {display_name}…")
question = pending or user_input

if question:
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🎓"):
        status = st.status(f"🔍 Searching week ≤ {week} course material…", expanded=False)
        with status:
            hits = retriever.retrieve(question, max_tutorial=week, k=k_val, mode=ret_mode)
            st.write(f"Found {len(hits)} candidate sections in the allowed material.")
            status.update(label="🛡️ Checking curriculum scope…")
            is_future, fut_tut = retriever.scope_check(question, week)
            if is_future:
                st.write(f"Question matches material from tutorial {fut_tut} — not covered yet.")
            else:
                for h in hits:
                    st.write(f"• {h.chunk.section}")

        if is_future:
            status.update(label="⛔ Outside this week's scope", state="complete", expanded=False)
            fut_name = meta.get(f"tutorial_{fut_tut}", {}).get("display_name", f"Tutorial {fut_tut}")
            suggest = "\n".join(f"- {t}" for t in topics[-3:]) if topics else ""
            answer = (
                f"That question touches material from **{fut_name}**, which you haven't "
                f"reached yet — we'll get there! 🔒\n\n"
                f"To keep you on track, I only answer from what the course has covered so far "
                f"(week ≤ {week}). From what you already know, I can help with:\n{suggest}\n\n"
                "Ask me anything about those and I'm all yours."
            )
            st.markdown(answer)
            sources = []
        else:
            context = rag.format_context(hits)
            if is_hw:
                sys_prompt = rag.homework_system_prompt(homework[sel], week, topics, context)
            else:
                sys_prompt = rag.tutor_system_prompt(week, display_name, topics, context)

            llm = get_llm_cached(provider, model)
            messages = ([SystemMessage(sys_prompt)]
                        + trimmed_history(st.session_state.history)
                        + [HumanMessage(question)])

            status.update(label="✍️ Formulating answer from course material…")
            slot, buf = st.empty(), ""
            try:
                for chunk in llm.stream(messages):
                    buf += chunk.content
                    slot.markdown(buf + " ▌")
                answer = fix_math(buf)
                slot.markdown(answer)
                status.update(label=f"✓ Answered from {len(hits)} course sections (week ≤ {week})",
                              state="complete", expanded=False)
            except Exception as exc:
                answer = f"⚠️ **Model error:** {exc}"
                slot.markdown(answer)
                status.update(label="⚠️ Model error", state="error", expanded=False)

            sources = [{"section": h.chunk.section, "score": h.score} for h in hits]

    st.session_state.history += [HumanMessage(question), AIMessage(answer)]
    st.session_state.display += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer, "sources": sources},
    ]
    st.rerun()

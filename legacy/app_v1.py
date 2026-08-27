"""
app.py  —  Socratic Course Tutor
Run:  streamlit run app.py  ->  http://localhost:8501
"""
import json, os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

PROVIDER  = os.getenv("LLM_PROVIDER", "openai").lower()
# Use script-relative path so the app works regardless of launch CWD
_HERE     = Path(__file__).parent
DB_DIR    = _HERE / "db"
META_FILE = DB_DIR / "metadata.json"
# Also switch CWD so relative paths in other places work consistently
os.chdir(_HERE)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Course Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Strip Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer { display:none !important; }
.block-container { padding-top:1.2rem !important; padding-bottom:0 !important; }

/* App background */
.stApp { background:#f0f4f8; }
.main .block-container { max-width:820px; }

/* Sidebar: dark admin panel */
[data-testid="stSidebar"] { background:#0f172a !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption { color:#94a3b8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color:#f1f5f9 !important; }
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stTextArea>div>div>textarea {
    background:#1e293b !important;
    border:1px solid #334155 !important;
    color:#e2e8f0 !important;
    border-radius:8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background:#1e293b !important;
    border:1px solid #334155 !important;
    border-radius:10px !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background:white !important;
    border-radius:14px !important;
    margin-bottom:6px !important;
    box-shadow:0 1px 4px rgba(0,0,0,.06) !important;
    border:1px solid #e8ecf1 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background:#eff6ff !important;
    border-color:#bfdbfe !important;
}
/* Force dark readable text everywhere in the main area */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] .stMarkdown { color:#0f172a !important; }
.main p, .main li, .main span, .main h1, .main h2, .main h3 { color:#0f172a !important; }
/* Inline code blocks — light background so they don't appear as black boxes */
[data-testid="stChatMessage"] code {
    color: #c7254e !important;
    background: #f9f2f4 !important;
    padding: 1px 5px !important;
    border-radius: 3px !important;
    font-size: 0.875em !important;
}
/* KaTeX math containers */
[data-testid="stChatMessage"] .katex,
[data-testid="stChatMessage"] .katex * { color:#0f172a !important; background:transparent !important; }
/* Alert/info/success boxes inside chat */
[data-testid="stChatMessage"] [data-testid="stAlert"] p { color:#0f172a !important; }

/* Chat input */
[data-testid="stChatInputContainer"]>div {
    background:white !important;
    border-radius:14px !important;
    border:1px solid #cbd5e1 !important;
    box-shadow:0 2px 8px rgba(0,0,0,.07) !important;
}

/* Selectbox pill */
.stSelectbox>div>div>div { border-radius:10px !important; font-weight:600; }

/* Divider */
hr { border-color:#e2e8f0 !important; margin:0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_meta() -> dict:
    return json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}

def save_meta(meta: dict) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

def load_homework() -> dict:
    """Load homework database from homework.json"""
    hw_file = DB_DIR / "homework.json"
    return json.loads(hw_file.read_text(encoding="utf-8")) if hw_file.exists() else {}

def get_hw_list() -> list:
    """Only return items that exist in metadata (keeps stale DB dirs invisible)."""
    meta = load_meta()
    if not DB_DIR.exists() or not meta:
        return []
    return sorted(
        name for name in meta
        if (DB_DIR / name).is_dir()
    )

def get_homework_list() -> list:
    """Return list of homework assignments"""
    hw = load_homework()
    return sorted(hw.keys())

def api_key_ok() -> bool:
    return (
        os.getenv("OPENAI_API_KEY", "").startswith("sk-")
        or os.getenv("GITHUB_TOKEN", "").startswith("github_pat_")
        or os.getenv("GITHUB_TOKEN", "").startswith("ghp_")
    )

# ── Smart history trimming ────────────────────────────────────────────────────
# Keep last 6 exchanges verbatim (12 messages) so the Socratic thread stays
# coherent. Older exchanges are condensed into a compact breadcrumb that
# preserves BOTH the student's questions AND the key points of the tutor's
# responses — so the tutor can reference or briefly re-explain past concepts
# if the student asks, without repeating full first-time explanations.

MAX_VERBATIM_EXCHANGES = 6  # last N full exchanges kept verbatim

def trimmed_history(full: list) -> list:
    max_msgs = MAX_VERBATIM_EXCHANGES * 2
    if len(full) <= max_msgs:
        return full                     # short session — send everything as-is

    recent = full[-max_msgs:]           # last N exchanges: full detail
    older  = full[:-max_msgs]           # earlier exchanges: condensed

    # Pair up [HumanMessage, AIMessage] from the older section and capture
    # both the question AND the first meaningful sentence of the tutor's hint,
    # so the model can reference or briefly re-explain those concepts if asked.
    condensed_lines = []
    for i in range(0, len(older) - 1, 2):
        if i + 1 >= len(older):
            break
        q = older[i].content[:70].replace("\n", " ").rstrip(".,;")
        a = older[i + 1].content[:120].replace("\n", " ").rstrip(".,;")
        condensed_lines.append(f"• Student asked: \"{q}…\"  →  Tutor hinted: \"{a}…\"")

    breadcrumb_text = "\n".join(condensed_lines)

    breadcrumb = [
        HumanMessage(
            content=(
                "[Earlier in this session we covered:\n"
                + breadcrumb_text
                + "\nIf I ask about any of these again, give a brief reminder "
                "rather than a full first-time explanation.]"
            )
        ),
        AIMessage(
            content=(
                "[Understood. I remember what we covered. I can re-explain or "
                "build on any of those concepts concisely if you need it.]"
            )
        ),
    ]
    return breadcrumb + recent

def save_env_var(key: str, value: str) -> None:
    env_path = Path(".env")
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    found = False
    for i, ln in enumerate(lines):
        if ln.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value

# ─────────────────────────────────────────────────────────────────────────────
# LLM HELPER
# ─────────────────────────────────────────────────────────────────────────────

def get_llm():
    if PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_LLM_MODEL", "llama3.2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
    from langchain_openai import ChatOpenAI
    # GitHub Models: OpenAI-compatible endpoint — uses your Copilot subscription
    gh_token = os.getenv("GITHUB_TOKEN", "")
    if gh_token:
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=gh_token,
            base_url="https://models.inference.ai.azure.com",
            temperature=0,
            streaming=True,
        )
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

@st.cache_resource
def build_chain(hw_id: str, topic_context: str, disp_name: str = "") -> dict:
    """Builds LangChain pipeline using pre-indexed material from metadata.json"""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = get_llm()

    # Load topic list from metadata for curriculum boundary enforcement
    _meta_now = json.loads(META_FILE.read_text(encoding="utf-8"))
    topic_list = _meta_now.get(hw_id, {}).get("topics", [])
    
    if topic_list:
        topics_formatted = "\n".join(f"  • {t}" for t in topic_list)
        topic_gate = f"{topics_formatted}\n\n"
    else:
        topic_gate = ""

    # Escape {{ }} so LangChain doesn't treat math notation like {1..k} as template vars
    safe_topic = topic_context.replace("{", "{{").replace("}", "}}")
    tutorial_label = disp_name or hw_id.replace("_", " ").title()

    topic_sec = f"\n{safe_topic}\n" if safe_topic.strip() else ""

    sys_msg = (
        f"You are a teacher for a student learning algorithms.\n\n"
        f"The student has learned the following topics so far:\n\n"
        + topic_gate
        + f"Current topic: {tutorial_label}\n\n"
        + "Guidelines:\n"
        + "- Answer questions ONLY about the topics listed above.\n"
        + "- If the student asks about something not covered yet, respond with:\n"
        + "  'We haven't covered [topic name] in this course yet. Based on what we've studied so far, I can help you with: [suggest 2-3 related topics].'\n"
        + "- Explain concepts clearly and help them learn.\n"
        + "- Use examples from the course material to illustrate points.\n"
        + "- Encourage understanding and thinking, not just memorization.\n"
        + "- Be patient, supportive, and encouraging.\n\n"
        + "Course material reference:\n"
        + topic_sec
        + "\n"
        + "Format all math using Markdown/KaTeX:\n"
        + "- Inline math: $O(n^2)$, $T(n) = 2T(n/2) + O(n)$\n"
        + "- Block math: $$T(n) = aT(n/b) + f(n)$$\n"
        + "Use only $...$ and $$...$$ delimiters.\n"
    )

    # Build the prompt template
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    return {
        "llm": llm,
        "answer_prompt": answer_prompt,
    }

@st.cache_resource
def build_homework_chain(hw_key: str, topics_covered: list, week_num: int) -> dict:
    """Builds LangChain pipeline for homework problem-solving (Socratic method)"""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = get_llm()
    hw_data = load_homework().get(hw_key, {})
    
    # Build topics known so far (cumulative: all weeks up to this week)
    all_hw = load_homework()
    known_concepts = []
    for k, v in all_hw.items():
        if v.get("week", 0) <= week_num:
            known_concepts.extend(v.get("topics", []))
    known_concepts = sorted(set(known_concepts))
    
    concepts_str = "\n".join(f"  • {c}" for c in known_concepts) if known_concepts else "  (foundational concepts)"
    
    hw_title = hw_data.get("title", f"Homework {week_num}")
    key_concepts = "\n".join(f"  • {c}" for c in hw_data.get("key_concepts", []))
    
    sys_msg = (
        f"You are a Socratic tutor helping a student solve {hw_title}.\n\n"
        f"The student has learned these concepts:\n{concepts_str}\n\n"
        f"**Problem Context**: {hw_data.get('description', '')}\n\n"
        f"**Key Concepts for This Assignment**:\n{key_concepts}\n\n"
        f"**Your Role**: Guide the student toward the solution using Socratic questioning.\n"
        f"- DO NOT give the answer directly\n"
        f"- DO guide them step-by-step with hints and leading questions\n"
        f"- DO encourage them to think about:\n"
        f"  * What algorithm/technique applies here?\n"
        f"  * What is the input and what should the output be?\n"
        f"  * How can they break the problem into smaller parts?\n"
        f"  * What data structures or patterns might help?\n"
        f"- DO ask \"Can you explain why?\" when they make a claim\n"
        f"- DO NOT reveal pseudocode or full solutions\n"
        f"- When they're stuck, ask: \"What have we learned that might apply?\"\n"
        f"- Celebrate progress: \"Good thinking! Now what about [next step]?\"\n\n"
        f"Format all math using Markdown/KaTeX:\n"
        f"- Inline math: $O(n^2)$, $T(n) = 2T(n/2) + O(n)$\n"
        f"- Block math: $$T(n) = aT(n/b) + f(n)$$\n"
        f"Use only $...$ and $$...$$ delimiters.\n"
    )
    
    # Build the prompt template
    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", sys_msg),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    return {
        "llm": llm,
        "answer_prompt": answer_prompt,
        "hw_data": hw_data,
    }

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  —  dark admin panel (teacher only)
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    with st.expander("🔑 API Key", expanded=not api_key_ok()):
        if api_key_ok():
            src = "GitHub Copilot" if os.getenv("GITHUB_TOKEN") else "OpenAI"
            st.success(f"{src} key saved ✅")

        st.markdown("**Option A — GitHub Copilot** *(recommended — you already pay for it)*")
        st.caption(
            "Get a free PAT at [github.com/settings/tokens](https://github.com/settings/tokens) "
            "→ *Generate new token (classic)* → no scopes needed → copy."
        )
        gh_input = st.text_input(
            "GitHub PAT", type="password",
            placeholder="github_pat_... or ghp_...",
            label_visibility="collapsed",
        )
        if st.button("Save GitHub token", use_container_width=True):
            if gh_input.startswith(("github_pat_", "ghp_")):
                save_env_var("GITHUB_TOKEN", gh_input)
                save_env_var("OPENAI_API_KEY", "")   # clear OpenAI key
                build_chain.clear()
                st.success("GitHub token saved! Uses gpt-4o-mini via Copilot.")
                st.rerun()
            else:
                st.error("Must start with github_pat_ or ghp_")

        st.divider()
        st.markdown("**Option B — OpenAI key** *(pay-per-use, needs credits)*")
        oi = st.text_input(
            "OpenAI key", type="password",
            placeholder="sk-proj-...",
            label_visibility="collapsed",
        )
        if st.button("Save OpenAI key", use_container_width=True):
            if oi.startswith("sk-"):
                save_env_var("OPENAI_API_KEY", oi)
                save_env_var("GITHUB_TOKEN", "")   # clear GH token
                build_chain.clear()
                st.success("OpenAI key saved!")
                st.rerun()
            else:
                st.error("Must start with sk-")

    st.divider()
    active = "GitHub Copilot" if os.getenv("GITHUB_TOKEN") else PROVIDER.upper()
    st.caption(f"LLM: **{active}**")
    if not api_key_ok():
        st.warning("Chat needs an API key.")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN  —  student chat interface
# ─────────────────────────────────────────────────────────────────────────────

meta    = load_meta()
hw_list = get_hw_list()
homework_list = get_homework_list()

# ── Nothing loaded yet ────────────────────────────────────────────────────────
if not hw_list and not homework_list:
    st.markdown(
        "<div style=\"text-align:center;padding:80px 0;color:#64748b\">"
        "<div style=\"font-size:4rem\">🎓</div>"
        "<h2 style=\"color:#1e293b;margin:12px 0 8px\">Course Tutor</h2>"
        "<p style=\"font-size:1rem\">No tutorials or homework loaded.<br>"
        "Please ensure metadata.json and homework.json are populated in the db/ folder.</p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Mode selector: Tutorial vs Homework ───────────────────────────────────────
col_mode_1, col_mode_2 = st.columns(2)
with col_mode_1:
    mode_tabs = st.radio(
        "Select mode:",
        options=["📖 Learn Material", "💪 Solve Homework"],
        horizontal=True,
        key="mode_selector",
    )

mode = "homework" if "Homework" in mode_tabs else "tutorial"

# ────────────────────────────────────────────────────────────────────────────────
# TUTORIAL MODE
# ────────────────────────────────────────────────────────────────────────────────

if mode == "tutorial":
    if not hw_list:
        st.warning("No tutorials loaded yet. Add tutorial PDFs to metadata.json")
        st.stop()
    
    # ── HW selector bar ───────────────────────────────────────────────────────────
    hw_labels = {hw: meta.get(hw, {}).get("display_name", hw) for hw in hw_list}

    col_sel, col_clr = st.columns([5, 1])
    with col_sel:
        selected_hw = st.selectbox(
            "hw",
            options=hw_list,
            format_func=lambda hw: "📚  " + hw_labels[hw],
            label_visibility="collapsed",
            key="hw_selector",
        )
    with col_clr:
        if st.button("🗑 Clear", use_container_width=True, help="Clear conversation"):
            st.session_state.chat_history     = []
            st.session_state.display_messages = []
            st.rerun()

    hw_info   = meta.get(selected_hw, {})
    topic_ctx = hw_info.get("topic_context", "")
    disp_name = hw_info.get("display_name", selected_hw)

    # Reset on HW switch
    if st.session_state.get("active_hw") != selected_hw:
        st.session_state.active_hw        = selected_hw
        st.session_state.active_mode      = "tutorial"
        st.session_state.chat_history     = []
        st.session_state.display_messages = []

# ────────────────────────────────────────────────────────────────────────────────
# HOMEWORK MODE
# ────────────────────────────────────────────────────────────────────────────────

elif mode == "homework":
    if not homework_list:
        st.warning("No homework assignments loaded yet. Add homework.json to db/")
        st.stop()
    
    # ── Homework selector bar ─────────────────────────────────────────────────────
    homework_data = load_homework()
    hw_labels_hw = {k: f"Week {homework_data[k].get('week', '?')}: {homework_data[k].get('title', k)}" 
                    for k in homework_list}

    col_sel, col_clr = st.columns([5, 1])
    with col_sel:
        selected_hw = st.selectbox(
            "hw",
            options=homework_list,
            format_func=lambda hw: "💪  " + hw_labels_hw.get(hw, hw),
            label_visibility="collapsed",
            key="hw_selector_hw",
        )
    with col_clr:
        if st.button("🗑 Clear", use_container_width=True, help="Clear conversation"):
            st.session_state.chat_history     = []
            st.session_state.display_messages = []
            st.rerun()

    hw_info = homework_data.get(selected_hw, {})
    disp_name = hw_info.get("title", selected_hw)
    week_num = hw_info.get("week", 1)
    
    # Show homework info
    with st.expander(f"📋 {disp_name} Details", expanded=False):
        st.markdown(f"**Description**: {hw_info.get('description', 'N/A')}")
        st.markdown(f"**Problems**: {hw_info.get('problems', '?')}")
        st.markdown(f"**Topics**: {', '.join(hw_info.get('topics', []))}")
        if hw_info.get("problem_preview"):
            st.markdown(f"**Preview**: {hw_info['problem_preview'][:300]}...")

    # Reset on HW switch
    if st.session_state.get("active_hw") != selected_hw or st.session_state.get("active_mode") != "homework":
        st.session_state.active_hw        = selected_hw
        st.session_state.active_mode      = "homework"
        st.session_state.chat_history     = []
        st.session_state.display_messages = []
    
    # Use homework-specific chain
    topic_ctx = ""  # Not used in homework mode

st.divider()

# ── Welcome screen (empty chat) ───────────────────────────────────────────────
if not st.session_state.get("display_messages"):
    welcome_msg = (
        "I'm your Socratic tutor. I'll guide you toward the answer "
        "with questions and hints — not give it to you directly."
    )
    if mode == "homework":
        welcome_msg += f"\n\n**{disp_name}**: {hw_info.get('description', '')}"
    
    st.markdown(
        f"<div style=\"text-align:center;padding:32px 0 20px;color:#475569\">"
        f"<div style=\"font-size:3rem\">{'💪' if mode == 'homework' else '🎓'}</div>"
        f"<h3 style=\"color:#1e293b;margin:10px 0 6px\">{disp_name}</h3>"
        f"<p style=\"margin:0 auto;max-width:480px;line-height:1.6\">"
        f"{welcome_msg}<br>"
        "<b>Ask your first question below.</b>"
        "</p></div>",
        unsafe_allow_html=True,
    )

# ── Render conversation ───────────────────────────────────────────────────────
for msg in st.session_state.get("display_messages", []):
    avatar = "🧑‍🎓" if msg["role"] == "user" else "🎓"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── No API key guard ──────────────────────────────────────────────────────────
if not api_key_ok() and PROVIDER == "openai":
    st.chat_input("Open the sidebar to add your API key…", disabled=True)
    st.info("👈 Open the sidebar (top-left ▸) and add your OpenAI API key to start chatting.")
    st.stop()

# ── Chat input + streaming response ──────────────────────────────────────────
placeholder = f"Ask about {disp_name}…"
if user_input := st.chat_input(placeholder):

    # 1. Show user message IMMEDIATELY — before any processing
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(user_input)

    # 2. Build appropriate chain based on mode
    if mode == "homework":
        parts        = build_homework_chain(selected_hw, [], week_num)
    else:
        parts        = build_chain(selected_hw, topic_ctx, disp_name)
    
    llm          = parts["llm"]
    ans_prompt   = parts["answer_prompt"]
    chat_history = trimmed_history(st.session_state.get("chat_history", []))

    with st.chat_message("assistant", avatar="🎓"):
        # Build messages and stream response
        messages = ans_prompt.format_messages(
            chat_history=chat_history,
            input=user_input,
        )
        try:
            # Stream token-by-token with cursor, then re-render with math fixed
            _slot  = st.empty()
            _buf   = ""
            for _chunk in llm.stream(messages):
                _buf += _chunk.content
                _slot.markdown(_buf + "\u258c")   # ▌ cursor while streaming
            # Final render: convert \( \) and \[ \] to $ and $$ for KaTeX
            import re as _re
            _fixed = _re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", _buf, flags=_re.DOTALL)
            _fixed = _re.sub(r"\\\((.+?)\\\)",  r"$\1$",   _fixed, flags=_re.DOTALL)
            _slot.markdown(_fixed)
            answer = _fixed
        except Exception as exc:
            answer = f"⚠️ Error calling the model: {exc}"
            st.markdown(answer)

    # 5. Persist to session state, then force a clean re-render from history
    #    (prevents the "immediate render" coexisting with the history loop render)
    st.session_state.setdefault("chat_history", []).extend([
        HumanMessage(content=user_input),
        AIMessage(content=answer),
    ])
    st.session_state.setdefault("display_messages", []).extend([
        {"role": "user",      "content": user_input},
        {"role": "assistant", "content": answer},
    ])
    st.rerun()



"""
app.py — Course Tutor · curriculum-gated hybrid RAG chat.

Run:  streamlit run app.py
"""
from __future__ import annotations

import html
import os
import re
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

load_dotenv(Path(__file__).parent / ".env")

import rag_engine as rag
from local_models import HEBREW_MODELS, TRANSLATION_MODELS, TUTOR_MODELS, model_options, model_label, translation_fallback_model
from homework_material import (
    homework_pdf_path, homework_clarification, selected_statements,
    problem_numbers, resolve_homework_followup, homework_content_request, homework_overview_answer,
)
from curriculum import CURRICULUM_FILE, course_name

os.chdir(Path(__file__).parent)

# ─────────────────────────────────────────────────────────────────────────────
# Page + theme
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Course Tutor",
    page_icon="🎓",
    layout="wide",
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

/* The header also holds the button that reopens a collapsed sidebar, so it
   stays (transparent); only the menu, deploy button and toolbar are hidden. */
#MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stExpandSidebarButton"] { color: var(--text) !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 8rem !important; max-width: 760px; }

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

/* Hebrew chat content must align right even with English interface labels. */
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"],
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] p,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] li,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] h1,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] h2,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] h3 {
    direction: rtl !important; text-align: right !important;
}
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] pre,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] code,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] .katex,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] .katex-display,
[class*="st-key-rtl-"] [data-testid="stMarkdownContainer"] .katex-inline {
    direction: ltr !important; unicode-bidi: plaintext !important; text-align: left !important;
}

/* code blocks */
.main pre {
    background: #171717 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 14px !important;
}
.main pre, .main pre code {
    direction: ltr !important; text-align: left !important;
    unicode-bidi: isolate; color: #e6e6e6 !important; font-size: .85rem !important;
}
.main :not(pre) > code {
    background: rgba(255,255,255,.08) !important;
    color: #ffb98a !important;
    padding: 2px 6px; border-radius: 5px; font-size: .84em !important;
    direction: ltr; unicode-bidi: isolate; display: inline-block;
}

/* KaTeX — always LTR, never affected by parent RTL */
.katex, .katex-display, .katex-inline { 
    color: var(--text) !important; 
    font-size: 1.03em !important;
    direction: ltr !important; 
    unicode-bidi: plaintext !important; 
    text-align: left !important;
    display: inline-block !important;
}
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
    unicode-bidi: plaintext;
    text-align: start;
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

/* Sidebar section headers for better visual hierarchy */
[data-testid="stSidebar"] strong {
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: var(--text-faint) !important;
    display: block !important;
    margin-top: 12px !important;
    margin-bottom: 8px !important;
}

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
    font-size: .95rem !important;
    padding: 10px 16px !important;
    transition: all .15s ease !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: var(--bg) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* selectbox styling — make more visible and interactive */
[data-baseweb="select"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    transition: border-color .15s ease !important;
}
[data-baseweb="select"]:hover {
    border-color: var(--accent) !important;
}
[data-baseweb="select"] [role="button"] {
    color: var(--text) !important;
    font-weight: 500 !important;
}

/* radio buttons — segmented control style */
.stRadio {
    display: flex !important;
}
.stRadio [role="radiogroup"] {
    gap: 2px !important;
    display: flex !important;
    background: var(--surface-2) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    width: 100% !important;
}
.stRadio label {
    flex: 1 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all .15s ease !important;
    color: var(--text-dim) !important;
    font-weight: 500 !important;
}
.stRadio label:hover {
    background: rgba(16, 163, 127, 0.1) !important;
}
.stRadio label:has(input:checked) {
    background: var(--accent) !important;
    color: var(--bg) !important;
    box-shadow: 0 2px 8px rgba(16, 163, 127, 0.2) !important;
}

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
    border-radius: 999px; padding: 6px 14px;
    font-size: .78rem; color: var(--text-dim);
    font-weight: 500;
    animation: fadeIn 0.3s ease;
}
.pill .dot { 
    width: 6px; height: 6px; border-radius: 50%; background: var(--accent); 
    animation: pulse 2s infinite;
}

/* Loading animations */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Status boxes for loading states */
[data-testid="stStatus"] {
    animation: fadeIn 0.3s ease;
}
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

UI_TEXT = {
    "en": {
        "tagline": "Curriculum-gated hybrid RAG",
        "language": "Language / שפה",
        "mode": "Mode",
        "learn": "📖 Learn",
        "homework": "💪 Homework",
        "tutorial": "Week / tutorial",
        "assignment": "Assignment",
        "download_homework": "Download assignment PDF",
        "homework_unavailable": "The assignment PDF is unavailable. Restore its file in material/Homework before asking questions.",
        "week_assignment": "Week {week} · {title}",
        "model_heading": "Model",
        "provider": "Provider",
        "model": "Model",
        "ollama_down": "Ollama isn't running — start it or pick another provider.",
        "github_token": "GitHub token",
        "openai_key": "OpenAI key",
        "translation_fallback": "Hebrew translation will use the selected tutoring model. Configure an OpenAI key for more reliable Hebrew terminology.",
        "retrieval": "⚙️ Retrieval",
        "passages": "Passages",
        "retrieval_mode": "Mode",
        "show_sources": "Show sources",
        "clear": "🗑  Clear conversation",
        "index_stats": "Embeddings: `{model}` · index: {count} chunks",
        "hero_homework": "Socratic guidance — hints and questions, never the final answer.",
        "hero_learn": "Grounded in your course material, week by week.",
        "week_scope": "week {week} scope",
        "sources": "📚 {count} sources",
        "score": "score",
        "ask": "Ask about {name}…",
        "searching": "🔍 Searching week ≤ {week} course material…",
        "translating_question": "🌐 Translating question…",
        "found": "Found {count} candidate sections in the allowed material.",
        "checking_scope": "🛡️ Checking curriculum scope…",
        "future_match": "Question matches material from tutorial {tutorial} — not covered yet.",
        "outside_scope": "⛔ Outside this week's scope",
        "formulating": "✍️ Formulating answer from course material…",
        "translating_answer": "🌐 Translating answer…",
        "answered": "✓ Answered from {count} course sections (week ≤ {week})",
        "translation_failed": "⚠️ Translation failed",
        "translation_failed_answer": "⚠️ I couldn't translate this question. See the reason below.",
        "answer_translation_failed": "⚠️ I found the answer, but couldn't translate it. See the reason below.",
        "translation_invalid": "The translator's output failed validation; this does not mean the model is missing.",
        "translation_timeout": "The translator exceeded its time limit.",
        "translation_missing": "The selected translation model was not found on the Ollama server.",
        "translation_connection": "Could not connect to the translation server. Check that it is running.",
        "translation_unknown": "The translation request failed. Details are available below.",
        "insufficient_evidence": "Not enough supporting material",
        "clarify_question": "Which concept, statement, or example do you mean? Please name it so I can answer your exact question.",
        "choose_problem": "Which problem number in this assignment would you like help with?",
        "unknown_problem": "That problem number isn't in this assignment. Available problems: {numbers}.",
        "evidence_failed": "I couldn't verify the answer's source references. Please try again or provide the relevant passage.",
        "solution_leak_answer": "I want to help you work through this rather than just hand you the answer. What have you tried so far, or where are you stuck?",
        "no_material": "I couldn't find supporting course material for this question through week {week}. Please add the relevant concept, problem number, or passage.",
        "greeting_reply": "👋 Hi there! I'm your {course} course tutor. What would you like to learn today?",
        "wrong_mode_reply": "📋 That sounds like a homework question — switch to **Homework** mode in the sidebar to work on your assignment. This Learn mode is for the tutorial material only.",
        "overview_reply": "Here's what we've covered so far in **{name}** (week ≤ {week}):\n\n{topics}\n\nAsk me about any of these, or say \"quiz me\" to test your knowledge!",
        "scope_failed": "⚠️ I couldn't verify the course-week restriction. Please try again.",
        "scope_refusal": "🔒 This material is more advanced than your current course week (week {week}). You'll learn it later in the course, in week {tutorial}. For now, I can help with topics covered so far.",
        "model_error": "⚠️ Model error",
        "model_error_answer": "⚠️ **Model error:** {error}",
        "missing_credentials": "The selected provider is missing an API key. Add it in the sidebar or switch providers.",
    },
    "he": {
        "tagline": "מורה פרטי המבוסס על חומר הקורס",
        "language": "שפה / Language",
        "mode": "מצב",
        "learn": "📖 למידה",
        "homework": "💪 שיעורי בית",
        "tutorial": "שבוע / תרגול",
        "assignment": "מטלה",
        "download_homework": "הורדת המטלה כ־PDF",
        "homework_unavailable": "קובץ המטלה אינו זמין. יש להחזיר אותו לתיקיית material/Homework לפני שאפשר לשאול שאלות.",
        "week_assignment": "שבוע {week} · {title}",
        "model_heading": "מודל",
        "provider": "ספק",
        "model": "מודל",
        "ollama_down": "Ollama אינו פועל — הפעילו אותו או בחרו ספק אחר.",
        "github_token": "אסימון GitHub",
        "openai_key": "מפתח OpenAI",
        "translation_fallback": "התרגום לעברית ישתמש במודל ההוראה שנבחר. מומלץ להגדיר מפתח OpenAI למונחים מקצועיים אמינים יותר.",
        "retrieval": "⚙️ אחזור מידע",
        "passages": "מספר קטעים",
        "retrieval_mode": "שיטה",
        "show_sources": "הצגת מקורות",
        "clear": "🗑  ניקוי השיחה",
        "index_stats": "הטמעות: `{model}` · אינדקס: {count} קטעים",
        "hero_homework": "הכוונה סוקרטית — רמזים ושאלות, בלי למסור את התשובה הסופית.",
        "hero_learn": "תשובות המבוססות על חומר הקורס, שבוע אחר שבוע.",
        "week_scope": "חומר עד שבוע {week}",
        "sources": "📚 {count} מקורות",
        "score": "דמיון",
        "ask": "אפשר לשאול על {name}…",
        "searching": "🔍 חיפוש בחומר הקורס עד שבוע {week}…",
        "translating_question": "🌐 תרגום השאלה…",
        "found": "נמצאו {count} קטעים מתאימים בחומר המותר.",
        "checking_scope": "🛡️ בדיקת גבולות חומר הקורס…",
        "future_match": "השאלה מתאימה לחומר מתרגול {tutorial}, שעדיין לא נלמד.",
        "outside_scope": "⛔ מחוץ לחומר שנלמד השבוע",
        "formulating": "✍️ ניסוח תשובה מתוך חומר הקורס…",
        "translating_answer": "🌐 תרגום התשובה…",
        "answered": "✓ התשובה מבוססת על {count} קטעים מחומר הקורס (עד שבוע {week})",
        "translation_failed": "⚠️ התרגום נכשל",
        "translation_invalid": "התרגום שהמודל החזיר לא עבר אימות. אין פירוש הדבר שהמודל אינו מותקן.",
        "translation_timeout": "מודל התרגום חרג ממגבלת הזמן.",
        "translation_missing": "מודל התרגום שנבחר לא נמצא בשרת Ollama.",
        "translation_connection": "לא ניתן להתחבר לשרת התרגום. בדקו שהוא פועל.",
        "translation_unknown": "בקשת התרגום נכשלה. פרטי השגיאה מופיעים בהמשך.",
        "translation_failed_answer": "⚠️ לא הצלחתי לתרגם את השאלה. הסיבה מופיעה בהמשך.",
        "answer_translation_failed": "⚠️ מצאתי תשובה, אך לא הצלחתי לתרגם אותה. הסיבה מופיעה בהמשך.",
        "insufficient_evidence": "אין מספיק חומר תומך",
        "clarify_question": "לאיזה מושג, משפט או דוגמה הכוונה? כדאי לציין את הנושא כדי שאוכל לענות על השאלה המדויקת שלך.",
        "choose_problem": "באיזה מספר שאלה במטלה הזאת נדרשת עזרה?",
        "unknown_problem": "מספר השאלה הזה אינו מופיע במטלה. השאלות הזמינות: {numbers}.",
        "evidence_failed": "לא הצלחתי לאמת את ההפניות למקורות בתשובה. אפשר לנסות שוב או לצרף את הקטע הרלוונטי.",
        "solution_leak_answer": "אני רוצה לעזור לך לעבוד על השאלה ולא סתם למסור את התשובה. מה כבר ניסית, או איפה נתקעת?",
        "no_material": "לא מצאתי מספיק חומר קורס התומך בתשובה לשאלה עד שבוע {week}. אפשר לציין מושג, מספר שאלה או קטע רלוונטי.",
        "greeting_reply": "👋 היי! אני המורה הפרטי שלך בקורס {course}. במה תרצו להתמקד היום?",
        "wrong_mode_reply": "📋 זו נשמעת כמו שאלה על שיעורי הבית — יש לעבור למצב **שיעורי בית** בסרגל הצד כדי לעבוד על המטלה. מצב הלמידה הזה מיועד רק לחומר התרגול.",
        "overview_reply": "הנה מה שכיסינו עד כה ב**{name}** (עד שבוע {week}):\n\n{topics}\n\nאפשר לשאול על כל אחד מהנושאים האלה, או לבקש \"תבחן אותי\" כדי לתרגל!",
        "scope_failed": "⚠️ לא הצלחתי לבדוק שהשאלה מתאימה לשבוע הנוכחי. נסו שוב.",
        "scope_refusal": "🔒 החומר הזה מתקדם יותר מהשבוע הנוכחי שלך בקורס (שבוע {week}). נלמד אותו בהמשך הקורס, בשבוע {tutorial}. בינתיים אפשר לשאול על נושאים שכבר נלמדו.",
        "model_error": "⚠️ שגיאת מודל",
        "model_error_answer": "⚠️ **שגיאת מודל:** {error}",
        "missing_credentials": "לספק שנבחר חסר מפתח API. יש להוסיף אותו בסרגל הצד או לבחור ספק אחר.",
    },
}


def ui_text(language: str, key: str, **values) -> str:
    return UI_TEXT[language][key].format(course=course_name(language), **values)


def localized_title(identifier: str, default: str, language: str) -> str:
    if language != "he":
        return default
    if identifier in rag.load_meta():
        return rag.load_meta()[identifier]['display_name_he']
    number = re.fullmatch(r"hw_(\d+)", identifier)
    return f"שיעורי בית {number.group(1)}" if number else default


# ─────────────────────────────────────────────────────────────────────────────
# Cached resources
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading retrieval index…")
def get_retriever(index_revision: int):
    return rag.HybridRetriever()


@st.cache_resource
def get_llm_cached(provider: str, model: str, api_key: str = ""):
    # Settings are passed explicitly: one browser session must never change another's.
    return rag.get_llm(provider=provider, model=model, api_key=api_key or None)


OPENROUTER_MODELS = ["anthropic/claude-haiku-5.5", "openai/gpt-4o-mini", "openai/gpt-5-mini",
                     "google/gemini-2.5-flash", "anthropic/claude-sonnet-5.5"]


def openrouter_model_input(label: str, default: str, key: str) -> str:
    """Common OpenRouter models, plus any other model id typed by hand."""
    options = list(dict.fromkeys([default, *OPENROUTER_MODELS]))
    choice = st.selectbox(label, [*options, "custom"], key=key,
                          format_func=lambda value: "Custom / מותאם" if value == "custom" else value)
    if choice == "custom":
        return st.text_input("OpenRouter model id", placeholder="provider/model", key=key + "_custom")
    return choice


@st.cache_data(ttl=30)
def ollama_models(base_url: str | None = None) -> list[str]:
    try:
        import urllib.request
        import json as _json
        url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=2) as r:
            return sorted(m["name"] for m in _json.load(r)["models"])
    except Exception:
        return []


_BACKTICK_SPAN_RE = re.compile(r"(?<!`)`(?!`)([^`\n]+?)(?<!`)`(?!`)")
_LOOKS_LIKE_MATH_RE = re.compile(r"\\[a-zA-Z]|\^|\bf_?\d*\s*\([^()\n]*\)\s*=")


def fix_math(text: str) -> str:
    """Normalize the model's math formatting to KaTeX delimiters.

    Beyond the \\(\\)/\\[\\] LaTeX delimiters the prompt explicitly forbids,
    the model sometimes wraps math (e.g. `f_1(n) = 10n`, `n^{1.3}`,
    `\\log_2 n`) in single backticks like inline code instead of $...$ —
    prompt instructions alone don't reliably stop this, so this catches it
    mechanically. Leaves real inline code (plain identifiers) and fenced
    ```code blocks``` untouched — only spans that look mathy (a LaTeX
    command, a caret exponent, or an f(n)= style definition) get converted.
    """
    text = re.sub(r"\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.DOTALL)

    def _convert(m: re.Match) -> str:
        inner = m.group(1)
        return f"${inner}$" if _LOOKS_LIKE_MATH_RE.search(inner) else m.group(0)

    return _BACKTICK_SPAN_RE.sub(_convert, text)


def render_md(target, content: str, rtl: bool = False) -> None:
    """Render markdown; Hebrew goes in a keyed container that the CSS above lays out
    right-to-left, so no text (including the user's) is ever rendered as raw HTML."""
    if rtl:
        target.container(key=f"rtl-{uuid.uuid4().hex}").markdown(content)
    else:
        target.markdown(content)


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

if (not CURRICULUM_FILE.exists() or not rag.INDEX_DIR.exists()
        or not rag.CHUNKS_FILE.exists()):
    st.markdown(
        "<div class='hero'><div class='logo'>🎓</div><h1>Course Tutor</h1>"
        "<p>This course's knowledge base hasn't been built yet. Put the lecture PDFs in "
        "material/lectures (and homework PDFs in material/Homework), then run:</p></div>",
        unsafe_allow_html=True,
    )
    st.code("python build_course.py --all", language="text")
    st.stop()

meta = rag.load_meta()
homework = rag.load_homework()
retriever = get_retriever(rag.CHUNKS_FILE.stat().st_mtime_ns)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    sidebar_title = st.empty()

    configured_ui = os.getenv("UI_LANGUAGE", "en").lower()
    if configured_ui not in UI_TEXT:
        configured_ui = "en"
    ui_lang = st.selectbox(
        "Language / שפה",
        ["en", "he"],
        index=["en", "he"].index(configured_ui),
        format_func={"en": "English", "he": "עברית"}.get,
    )
    t = lambda key, **values: ui_text(ui_lang, key, **values)
    ui_is_he = ui_lang == "he"
    sidebar_title.markdown(f"### 🎓 {course_name(ui_lang)}")

    if ui_is_he:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] { direction: rtl; }
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 { text-align: right; }
            [data-testid="stChatInput"] textarea {
                direction: rtl !important;
                text-align: right !important;
            }
            .hero { direction: rtl; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.caption(t("tagline"))
    st.divider()

    mode = st.radio(
        t("mode"),
        ["learn", "homework"],
        format_func=lambda value: t(value),
        label_visibility="collapsed",
    )
    is_hw = mode == "homework"

    if not is_hw:
        tut_ids = sorted(meta, key=rag.tutorial_week)
        sel = st.selectbox(
            t("tutorial"),
            tut_ids,
            format_func=lambda tutorial: localized_title(
                tutorial,
                meta[tutorial].get("display_name", tutorial),
                ui_lang,
            ),
            index=0,
        )
        week = rag.tutorial_week(sel)
        display_name = localized_title(sel, meta[sel].get("display_name", sel), ui_lang)
        topics = rag.covered_topics(week)
    else:
        hw_ids = sorted(homework, key=lambda key: homework[key].get("week", 0))
        sel = st.selectbox(
            t("assignment"),
            hw_ids,
            format_func=lambda key: t(
                "week_assignment",
                week=homework[key].get("week", "?"),
                title=localized_title(
                    key,
                    homework[key].get("title", key),
                    ui_lang,
                ),
            ),
        )
        week = homework[sel].get("week", 1)
        display_name = localized_title(sel, homework[sel].get("title", sel), ui_lang)
        topics = rag.covered_topics(week)
        if homework[sel].get("source_error"):
            st.error(t("homework_unavailable"))
        else:
            pdf_path = homework_pdf_path(homework[sel])
            st.download_button(t("download_homework"), pdf_path.read_bytes(),
                               file_name=pdf_path.name, mime="application/pdf")

    st.divider()
    st.markdown(f"**{t('model_heading')}**")

    providers = ["ollama", "github", "openai", "openrouter"]
    provider_labels = {
        "ollama": "Ollama (מקומי · חינם)" if ui_is_he else "Ollama (local · free)",
        "github": "GitHub Models (חינם)" if ui_is_he else "GitHub Models (free)",
        "openai": "OpenAI (בתשלום)" if ui_is_he else "OpenAI (paid)",
        "openrouter": "OpenRouter (בתשלום)" if ui_is_he else "OpenRouter (paid)",
    }
    provider = st.selectbox(
        t("provider"),
        providers,
        index=providers.index(os.getenv("LLM_PROVIDER", "ollama"))
        if os.getenv("LLM_PROVIDER", "ollama") in providers else 0,
        format_func=provider_labels.get,
    )

    api_key = ""
    if provider == "ollama":
        local = ollama_models()
        default = os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b")
        options = model_options(local)
        if default in TRANSLATION_MODELS:
            default = options[0]
        if default not in options:
            options.insert(0, default)
        model = st.selectbox(t("model"), options, index=options.index(default),
                             format_func=model_label)
        if model in HEBREW_MODELS:
            st.caption(HEBREW_MODELS[model][1])
            if model not in local:
                st.caption("Download before testing / הורידו לפני בדיקה")
                st.code(f'ollama pull {model}', language="bash")
    elif provider == "github":
        model = st.selectbox(
            t("model"),
            ["gpt-4o-mini", "gpt-4o", "Phi-3.5-mini-instruct", "Meta-Llama-3.1-8B-Instruct"],
        )
        # Keys typed here live only in this browser session, never in the server environment.
        api_key = os.getenv("GITHUB_TOKEN", "") or st.text_input(
            t("github_token"), type="password", placeholder="github_pat_… / ghp_…",
            key="github_token")
    elif provider == "openrouter":
        model = openrouter_model_input(t("model"), os.getenv("OPENROUTER_MODEL", rag.OPENROUTER_DEFAULT_MODEL),
                                       key="openrouter_model")
        api_key = os.getenv("OPENROUTER_API_KEY", "") or st.text_input(
            "OpenRouter API key", type="password", placeholder="sk-or-…", key="openrouter_key")
    else:
        model = st.selectbox(t("model"), ["gpt-4o-mini", "gpt-4o"])
        api_key = os.getenv("OPENAI_API_KEY", "") or st.text_input(
            t("openai_key"), type="password", placeholder="sk-…", key="openai_key")

    with st.expander("🌐 Hebrew / עברית"):
        st.caption("מודלי תרגום מקומיים זמינים לבדיקה" if ui_is_he
                   else "Local translation candidates")
        for candidate, info in TRANSLATION_MODELS.items():
            st.caption(info[0])
        st.caption("בחרו Ollama כדי לבחור מודל מקומי" if ui_is_he
                   else "Select Ollama below to choose a local translation model.")
        translation_choices = ["auto", "ollama", "tutor", "openai", "openrouter"]
        configured_translation = os.getenv("TRANSLATION_PROVIDER", "auto")
        translation_provider = st.selectbox(
            "מודל תרגום" if ui_is_he else "Translation provider",
            translation_choices,
            index=translation_choices.index(configured_translation)
            if configured_translation in translation_choices else 0,
            format_func=lambda value: {
                "auto": "Automatic / אוטומטי", "ollama": "Ollama (local / מקומי)",
                "tutor": "Tutoring model / מודל ההוראה", "openai": "OpenAI",
                "openrouter": "OpenRouter"}[value],
        )
        translation_model = None
        local_fallback_model = None
        if translation_provider == "ollama":
            installed_translation_models = ollama_models(os.getenv("TRANSLATION_OLLAMA_BASE_URL"))
            translation_options = model_options(installed_translation_models, role="translation")
            configured_model = os.getenv("TRANSLATION_OLLAMA_MODEL", next(iter(TRANSLATION_MODELS)))
            if configured_model in TUTOR_MODELS:
                configured_model = next(iter(TRANSLATION_MODELS))
            if configured_model not in translation_options:
                translation_options.insert(0, configured_model)
            translation_choice = st.selectbox(
                "מודל מקומי לתרגום" if ui_is_he else "Local translation model",
                [*translation_options, "custom"],
                index=translation_options.index(configured_model),
                format_func=lambda value: "Custom / מותאם" if value == "custom" else model_label(value))
            translation_model = (st.text_input("Ollama model name", value=configured_model)
                                 if translation_choice == "custom" else translation_choice)
            if translation_model in HEBREW_MODELS:
                st.caption(HEBREW_MODELS[translation_model][1])
            candidate_fallback = translation_fallback_model(translation_model, installed_translation_models)
            if candidate_fallback and st.checkbox(
                "נסה את מודל 12B המותקן אם התרגום נכשל" if ui_is_he else
                "Retry failed translations with the installed 12B model", value=True):
                local_fallback_model = candidate_fallback
            if translation_model not in installed_translation_models:
                st.caption("Download before testing / הורידו לפני בדיקה")
                st.code(f'ollama pull {translation_model}', language="bash")
        elif translation_provider == "openai":
            translation_model = st.text_input(
                "מודל תרגום OpenAI" if ui_is_he else "OpenAI translation model",
                value=os.getenv("TRANSLATION_MODEL", "gpt-4o-mini"))
        elif translation_provider == "openrouter":
            translation_model = openrouter_model_input(
                "מודל תרגום OpenRouter" if ui_is_he else "OpenRouter translation model",
                os.getenv("TRANSLATION_OPENROUTER_MODEL",
                          os.getenv("OPENROUTER_MODEL", rag.OPENROUTER_DEFAULT_MODEL)),
                key="translation_openrouter_model")
        if translation_provider == "openrouter":
            translation_api_key = os.getenv("OPENROUTER_API_KEY", "") or (
                api_key if provider == "openrouter" else "") or st.text_input(
                "OpenRouter API key", type="password", key="translation_openrouter_key")
        else:
            translation_api_key = os.getenv("OPENAI_API_KEY", "") or (api_key if provider == "openai" else "")
            if translation_provider in {"auto", "openai"} and not translation_api_key:
                translation_api_key = st.text_input(t("openai_key"), type="password",
                                                    key="translation_openai_key")
        st.caption("עברית → English → tutor → English → עברית")

    with st.expander(t("retrieval")):
        k_val = st.slider(t("passages"), 2, 8, 4)
        modes = ["dense", "hybrid", "hybrid+rerank"]
        retrieval_labels = {
            "dense": "צפוף (מהיר · מוביל בבדיקה)" if ui_is_he else "Dense (benchmark winner · fast)",
            "hybrid": "משולב (צפוף + BM25)" if ui_is_he else "Hybrid (dense + BM25)",
            "hybrid+rerank": "משולב + דירוג מחדש" if ui_is_he else "Hybrid + rerank (thorough · slow)",
        }
        ret_mode = st.selectbox(
            t("retrieval_mode"),
            modes,
            index=modes.index(rag.RETRIEVAL_MODE) if rag.RETRIEVAL_MODE in modes else 0,
            format_func=retrieval_labels.get,
        )
        show_sources = st.toggle(t("show_sources"), value=True)

    st.divider()
    if st.button(t("clear"), use_container_width=True):
        st.session_state.pop("history", None)
        st.session_state.pop("display", None)
        st.session_state.pop("active_homework_problems", None)
        st.session_state.pop("quiz_chunks", None)
        st.session_state.pop("followup_chunks", None)
        st.rerun()
    st.caption(
        t(
            "index_stats",
            model=rag.EMBED_MODEL.split("/")[-1],
            count=len(retriever.chunks),
        )
    )

# Reset chat when the context changes
ctx_key = (mode, sel, tuple(topics), CURRICULUM_FILE.stat().st_mtime_ns,
           homework[sel].get("pdf_sha256") if is_hw else None)
if st.session_state.get("ctx") != ctx_key:
    st.session_state.ctx = ctx_key
    st.session_state.history = []
    st.session_state.display = []
    st.session_state.active_homework_problems = []
    st.session_state.quiz_chunks = []
    st.session_state.followup_chunks = []

# ─────────────────────────────────────────────────────────────────────────────
# Hero + suggestions (empty chat)
# ─────────────────────────────────────────────────────────────────────────────

pending = None

if not st.session_state.get("display"):
    subtitle = t("hero_homework") if is_hw else t("hero_learn")
    st.markdown(
        f"<div class='hero'><div class='logo'>{'💪' if is_hw else '🎓'}</div>"
        f"<h1>{html.escape(display_name)}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='text-align:center;margin-bottom:1.3rem'><span class='pill'>"
        f"<span class='dot'></span>{rag.llm_label(provider, model)} · "
        f"{t('week_scope', week=week)}</span></div>",
        unsafe_allow_html=True,
    )

    chips = rag.suggestion_chips(week, is_hw, ui_lang)

    cols = st.columns(2)
    for i, chip in enumerate(chips[:4]):
        if cols[i % 2].button(chip, key=f"chip{i}", use_container_width=True):
            pending = chip

# ─────────────────────────────────────────────────────────────────────────────
# Conversation
# ─────────────────────────────────────────────────────────────────────────────

for m in st.session_state.get("display", []):
    with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🎓"):
        render_md(st, m["content"], rtl=m.get("rtl", False))
        if m.get("translation_error"):
            with st.expander("Translation error / שגיאת תרגום"):
                st.text(m["translation_error"])
        if m.get("sources") and show_sources:
            with st.expander(t("sources", count=len(m["sources"]))):
                for source in m["sources"]:
                    score_text = (f" · {t('score')} {source['score']:.2f}"
                                  if source.get('score') is not None else "")
                    st.markdown(
                        f"<div class='src-line'><b>{html.escape(source['section'])}</b>{score_text}</div>",
                        unsafe_allow_html=True,
                    )

user_input = st.chat_input(t("ask", name=display_name),
                           disabled=is_hw and bool(homework[sel].get("source_error")))
question = pending or user_input

if question and not (is_hw and homework[sel].get("source_error")):
    q_is_he = rag.is_hebrew(question)
    # Canned/status replies always match the language the student actually
    # typed, never the sidebar's chrome-only Language selector — otherwise
    # an English question can come back with a Hebrew status message (or
    # vice versa) whenever the two disagree. The sidebar setting still
    # controls the static UI text (labels, buttons, placeholders) via t().
    message_lang = "he" if q_is_he else "en"
    mt = lambda key, **values: ui_text(message_lang, key, **values)

    try:
        llm = get_llm_cached(provider, model, api_key)
    except Exception:
        with st.chat_message("user", avatar="🧑‍🎓"):
            render_md(st, question, rtl=q_is_he)
        with st.chat_message("assistant", avatar="🎓"):
            answer = mt("model_error_answer", error=mt("missing_credentials"))
            render_md(st, answer, rtl=rag.is_hebrew(answer))
        st.stop()

    try:
        dedicated_translation_llm = None if not q_is_he else (
            rag.get_translation_llm(api_key=translation_api_key)
            if translation_provider == "auto" else
            rag.get_translation_llm(translation_provider, translation_model,
                                    api_key=translation_api_key))
        translator_setup_error = None
    except Exception as exc:
        dedicated_translation_llm = None
        translator_setup_error = exc
    primary_translation_llm = dedicated_translation_llm or llm
    fallback_translation_llm = (
        llm if translation_provider == "auto" and dedicated_translation_llm is not None
        and provider != "openai" else None
    )

    if q_is_he and local_fallback_model:
        fallback_translation_llm = rag.get_translation_llm('ollama', local_fallback_model)

    with st.chat_message("user", avatar="🧑‍🎓"):
        render_md(st, question, rtl=q_is_he)

    history_ready = False
    translation_diagnostic = None

    with st.chat_message("assistant", avatar="🎓"):
        status = st.status(mt("searching", week=week), expanded=False)
        query_en = question
        interpreted_question = question
        translation_error = translator_setup_error if q_is_he else None
        hits = []
        assignment_sources = []
        decision_status = None
        active_problems = st.session_state.get("active_homework_problems", []) if is_hw else []
        contextual_question = rag.expand_course_abbreviations(question)
        contextual_question = resolve_homework_followup(contextual_question, active_problems) if is_hw else contextual_question
        wrong_mode = not is_hw and rag.references_homework(contextual_question)
        fut_tut = rag.named_future_topic(contextual_question, week) if not wrong_mode else 0
        is_future = bool(fut_tut)
        scope_error = None
        # With a previous answer to refer back to, a bare "why?" is a follow-up, not ambiguous.
        followup_chunks = [] if is_hw else st.session_state.get("followup_chunks", [])
        clarification = ("clarify_question" if not wrong_mode and not followup_chunks
                         and rag.clarification_needed(contextual_question) else None)
        if is_hw:
            clarification = homework_clarification(homework[sel], contextual_question) or clarification

        with status:
            if q_is_he and translation_error is None and not is_future and not clarification and not wrong_mode:
                status.update(label=mt("translating_question"))
                try:
                    query_en = rag.translate_with_fallback(
                        question,
                        "en",
                        primary_translation_llm,
                        fallback_translation_llm,
                        on_fallback=lambda: status.update(label=(
                            "מנסה מודל תרגום חלופי…" if q_is_he else "Retrying with fallback translator…")),
                        progress=lambda chars, seconds: status.update(
                            label=mt("translating_question") + f" · {seconds}s · {chars} chars"),
                    )
                except Exception as exc:
                    translation_error = exc

            if translation_error is None and not is_future and not clarification and not wrong_mode:
                status.update(label=mt("checking_scope"))
                try:
                    retrieval_question = rag.expand_course_abbreviations(query_en)
                    retrieval_question = resolve_homework_followup(retrieval_question, active_problems) if is_hw else retrieval_question
                    decision = rag.prepare_retrieval(
                        retrieval_question, week, retriever, homework[sel] if is_hw else None,
                        k=k_val, mode=ret_mode, normalization_llm=llm)
                    interpreted_question = decision.normalized_question or query_en
                    decision_status = decision.status
                    is_future, fut_tut = decision.status == "future", decision.future_week
                    clarification = decision.clarification
                    hits = decision.hits
                    if (not is_hw and st.session_state.get("quiz_chunks")
                            and decision.status in ("insufficient", "overview", "clarify")):
                        # A reply to the previous quiz question is graded against its passages.
                        hits = [rag.Hit(retriever.chunks[cid], 1.0)
                                for cid in st.session_state.quiz_chunks if cid in retriever.chunks]
                        decision_status, clarification = "quiz", None
                    elif followup_chunks and decision.status in ("overview", "clarify"):
                        # A message naming no topic ("I don't understand", "why?") continues
                        # the previous answer; reuse its passages instead of listing topics.
                        hits = [rag.Hit(retriever.chunks[cid], 1.0) for cid in followup_chunks
                                if cid in retriever.chunks and retriever.chunks[cid].tutorial <= week]
                        if hits:
                            decision_status, clarification = "answer", None
                    if is_hw and decision.status == "answer":
                        assignment_sources = selected_statements(homework[sel], interpreted_question)
                    st.write(mt("found", count=len(hits)))
                except Exception as exc:
                    scope_error = exc
            if is_future:
                st.write(mt("future_match", tutorial=fut_tut))

        if translation_error is not None:
            status.update(label=mt("translation_failed"), state="error", expanded=False)
            answer_en = "The question could not be translated."
            from translation_support import translation_error_kind, translation_error_details
            translation_diagnostic = translation_error_details(translation_error)
            answer = mt("translation_failed_answer") + "\n\n" + mt("translation_" + translation_error_kind(translation_error))
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif scope_error is not None:
            status.update(label=mt("checking_scope"), state="error", expanded=False)
            answer = mt("scope_failed")
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif wrong_mode:
            status.update(label=mt("answered", count=0, week=week), state="complete", expanded=False)
            answer = mt("wrong_mode_reply")
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif is_future:
            status.update(label=mt("outside_scope"), state="complete", expanded=False)
            answer = mt("scope_refusal", week=week, tutorial=fut_tut)
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif clarification:
            status.update(label=mt("insufficient_evidence"), state="complete", expanded=False)
            numbers = ", ".join(str(p['number']) for p in homework[sel]['problem_statements']) if is_hw else ""
            answer = mt(clarification, numbers=numbers)
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif decision_status == "wrong_mode":
            status.update(label=mt("answered", count=0, week=week), state="complete", expanded=False)
            answer = mt("wrong_mode_reply")
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif decision_status == "greeting":
            status.update(label=mt("answered", count=0, week=week), state="complete", expanded=False)
            answer = mt("greeting_reply")
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif decision_status == "overview":
            status.update(label=mt("answered", count=0, week=week), state="complete", expanded=False)
            topics_list = "\n".join(f"- {t}" for t in topics) if topics else ""
            answer = mt("overview_reply", name=display_name, week=week, topics=topics_list)
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        elif not hits and not assignment_sources:
            status.update(label=mt("insufficient_evidence"), state="complete", expanded=False)
            answer = mt("no_material", week=week)
            render_md(st, answer, rtl=rag.is_hebrew(answer))
            sources = []
        else:
            context = rag.format_context(hits)
            if is_hw:
                sys_prompt = rag.homework_system_prompt(homework[sel], week, topics, context, interpreted_question)
            elif decision_status == "quiz":
                sys_prompt = rag.quiz_system_prompt(week, display_name, topics, context)
            else:
                sys_prompt = rag.tutor_system_prompt(week, display_name, topics, context)

            messages = (
                [SystemMessage(sys_prompt)]
                + trimmed_history(st.session_state.history)
                + [HumanMessage(rag.question_message(query_en, interpreted_question))]
            )

            status.update(label=mt("formulating"))
            slot = st.empty()
            generation_error = None
            evidence_error = None
            blocked_tutorial = 0
            solution_leaked = False
            try:
                if is_hw and homework_content_request(interpreted_question):
                    answer_en = homework_overview_answer(homework[sel], interpreted_question)
                    rag.validate_citations(answer_en, len(hits), len(assignment_sources))
                else:
                    evidence = {**{f"Source {i}": h.chunk.text for i, h in enumerate(hits, 1)},
                                **{f"Assignment {i}": p["text"]
                                   for i, p in enumerate(assignment_sources, 1)}}
                    answer_en = fix_math(rag.generate_scoped_answer(
                        llm, messages, retriever, week, len(hits), len(assignment_sources),
                        retry_citations=True, is_homework=is_hw, evidence=evidence))
            except rag.FutureMaterialError as exc:
                blocked_tutorial = exc.tutorial
            except rag.SolutionLeakError:
                solution_leaked = True
            except rag.EvidenceError as exc:
                evidence_error = exc
            except Exception as exc:
                generation_error = exc
                answer_en = f"Model error: {exc}"

            if blocked_tutorial:
                answer = mt("scope_refusal", week=week, tutorial=blocked_tutorial)
                render_md(slot, answer, rtl=rag.is_hebrew(answer))
                status.update(label=mt("outside_scope"), state="complete", expanded=False)
            elif solution_leaked:
                answer = mt("solution_leak_answer")
                render_md(slot, answer, rtl=rag.is_hebrew(answer))
                status.update(label=mt("insufficient_evidence"), state="complete", expanded=False)
            elif evidence_error is not None:
                answer = mt("evidence_failed")
                render_md(slot, answer, rtl=rag.is_hebrew(answer))
                status.update(label=mt("insufficient_evidence"), state="error", expanded=False)
            elif generation_error is not None:
                answer = mt("model_error_answer", error=generation_error)
                render_md(slot, answer, rtl=rag.is_hebrew(answer))
                status.update(label=mt("model_error"), state="error", expanded=False)
            elif q_is_he:
                status.update(label=mt("translating_answer"))
                try:
                    answer = rag.translate_with_fallback(
                        answer_en,
                        "he",
                        primary_translation_llm,
                        fallback_translation_llm,
                        on_fallback=lambda: status.update(label=(
                            "מנסה מודל תרגום חלופי…" if q_is_he else "Retrying with fallback translator…")),
                        progress=lambda chars, seconds: status.update(
                            label=mt("translating_answer") + f" · {seconds}s · {chars} chars"),
                    )
                    translated_future = rag.named_future_topic(answer, week)
                    if translated_future:
                        raise rag.FutureMaterialError(translated_future)
                    rag.validate_citations(answer, len(hits), len(assignment_sources))
                    answer = rag.localize_citations(rag.split_grouped_citations(answer), "he")
                    render_md(slot, answer, rtl=True)
                    history_ready = True
                    status.update(
                        label=mt("answered", count=len(hits), week=week),
                        state="complete",
                        expanded=False,
                    )
                except rag.FutureMaterialError as exc:
                    blocked_tutorial = exc.tutorial
                    answer = mt("scope_refusal", week=week, tutorial=blocked_tutorial)
                    render_md(slot, answer, rtl=rag.is_hebrew(answer))
                    status.update(label=mt("outside_scope"), state="complete", expanded=False)
                except rag.EvidenceError:
                    answer = mt("evidence_failed")
                    render_md(slot, answer, rtl=rag.is_hebrew(answer))
                    status.update(label=mt("insufficient_evidence"), state="error", expanded=False)
                except Exception as exc:
                    from translation_support import translation_error_kind, translation_error_details
                    translation_diagnostic = translation_error_details(exc)
                    answer = mt("answer_translation_failed") + "\n\n" + mt("translation_" + translation_error_kind(exc))
                    render_md(slot, answer, rtl=rag.is_hebrew(answer))
                    status.update(label=mt("translation_failed"), state="error", expanded=False)
            else:
                answer = answer_en
                slot.markdown(answer)
                status.update(
                    label=mt("answered", count=len(hits), week=week),
                    state="complete",
                    expanded=False,
                )
                history_ready = True

            source_label, assignment_label = ("מקור", "מטלה") if q_is_he else ("Source", "Assignment")
            sources = ([
                {"section": f"{source_label} {i} — {hit.chunk.section}", "score": hit.similarity}
                for i, hit in enumerate(hits, 1)
            ] + [
                {"section": f"{assignment_label} {i} — {Path(homework[sel]['problem_pdf']).name}, "
                            f"Problem {p['number']}, PDF pages {', '.join(map(str, p['pages']))}",
                 "score": None}
                for i, p in enumerate(assignment_sources, 1)
            ]) if history_ready else []

    # Only successful interactions enter the English history used by the LLM.
    if history_ready:
        st.session_state.quiz_chunks = ([h.chunk.id for h in hits]
                                        if decision_status == "quiz" else [])
        st.session_state.followup_chunks = ([h.chunk.id for h in hits]
                                            if not is_hw and decision_status == "answer" else [])
        if is_hw:
            selected = problem_numbers(interpreted_question)
            if selected:
                st.session_state.active_homework_problems = sorted(selected)
            elif assignment_sources:
                st.session_state.active_homework_problems = []
        history_answer = answer_en
        if is_hw and homework_content_request(interpreted_question):
            shown = ', '.join(str(p['number']) for p in assignment_sources)
            history_answer = (f"Displayed the exact PDF statements for problems {shown} "
                              "of the selected assignment and offered to work through them.")
        st.session_state.history += [
            HumanMessage(rag.question_message(query_en, interpreted_question)), AIMessage(history_answer)]
    elif decision_status != "greeting":
        # A refused or failed turn ends the topic; "I don't understand" must not
        # silently continue an answer from before it. Small talk keeps the topic.
        st.session_state.followup_chunks = []
    st.session_state.display += [
        {"role": "user", "content": question, "rtl": q_is_he},
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "rtl": rag.is_hebrew(answer),
            "translation_error": translation_diagnostic,
        },
    ]
    st.rerun()

# 🎓 Streamlit Algorithm Tutor — Complete Project Guide

A curriculum-aware AI tutoring system built with Streamlit, LangChain, and ChatGPT 4o mini. The bot guides students through a sequence of algorithm tutorials, enforcing cumulative learning by preventing discussions of topics not yet covered.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [The Complete Pipeline](#the-complete-pipeline)
5. [Installation & Setup](#installation--setup)
6. [Running the Application](#running-the-application)
7. [Key Components Explained](#key-components-explained)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**Purpose:** Create an interactive web-based tutoring system for algorithm education that:
- ✅ Teaches topics sequentially across 8 tutorials
- ✅ Enforces curriculum boundaries (blocks out-of-scope questions)
- ✅ Uses AI (ChatGPT 4o mini) for conversational explanation
- ✅ Provides semantic search over course material (via Chroma + embeddings)
- ✅ Maintains natural, supportive teaching dialogue

**Tech Stack:**
- **Web UI:** Streamlit 1.x
- **LLM:** ChatGPT 4o mini (via Azure OpenAI API / GitHub Copilot)
- **RAG Pipeline:** LangChain (prompt templates, message history, custom retriever)
- **Vector DB:** Chroma (stores embedded course material)
- **Embeddings:** all-MiniLM-L6-v2 (HuggingFace)
- **PDF Processing:** PyPDF2
- **Environment:** Python 3.11 + virtual environment

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│          STREAMLIT WEB UI (app.py)                      │
│  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │ Sidebar Admin Panel  │  │  Chat Interface      │   │
│  │ (tutorial selector)  │  │ (message history +   │   │
│  │                      │  │  input field)        │   │
│  └──────────────────────┘  └──────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ User Question
                     ↓
┌─────────────────────────────────────────────────────────┐
│          LANGCHAIN RAG PIPELINE                         │
│  ┌────────────────────────────────────────────────┐    │
│  │ 1. Topic Gate: Check if question in scope     │    │
│  │    (explicit topic whitelist)                 │    │
│  │                                                │    │
│  │ 2. CumulativeRetriever: Search course         │    │
│  │    material across current + prior tutorials  │    │
│  │    (semantic search via Chroma)               │    │
│  │                                                │    │
│  │ 3. ChatPromptTemplate: Build system prompt    │    │
│  │    - Teacher role                             │    │
│  │    - Topic whitelist                          │    │
│  │    - Course material context                  │    │
│  │    - Chat history                             │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│          CHATGPT 4O MINI (Azure OpenAI API)             │
│          Streaming response with content filtering      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│          RESPONSE PROCESSING                            │
│  - Parse streaming chunks                              │
│  - Post-process math notation ($ ... $, $$ ... $$)    │
│  - Display with Streamlit UI                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
tutor-bot/
├── README_PROJECT_STRUCTURE.md    ← You are here
├── requirements.txt               ← Python dependencies
├── .env.example                   ← Template for API keys
├── .gitignore                     ← Git exclusions
│
├── CORE APPLICATION
├── app.py                         ← Main Streamlit app (400+ lines)
│   ├── Page config + CSS styling
│   ├── UI: Sidebar admin panel + chat interface
│   ├── Session state management (messages, metadata)
│   ├── build_chain(): Constructs LangChain RAG pipeline
│   ├── load_meta(): Loads curriculum data from metadata.json
│   ├── get_llm(): Initializes ChatGPT 4o mini
│   └── Chat loop: Streaming responses + message display
│
├── PIPELINE SCRIPTS (Data Generation)
├── extract_tutorials_pipeline.py  ← Stage 1: Extract PDFs → raw text
│   ├── extract_text_from_pdf()
│   ├── get_tutorial_files()
│   └── extract_all_tutorials()
│   Output: raw_tutorial_texts/tutorial_{1-8}_raw.txt
│
├── process_with_llm.py            ← Stage 2: Raw text → ChatGPT indexing
│   ├── get_indexing_prompt()
│   ├── process_tutorial_with_llm()
│   └── process_all_tutorials()
│   Output: indexed_tutorials.json
│
├── process_failed_tutorials.py    ← Stage 2b: Token-efficient reprocessing
│   ├── load_existing_results()
│   ├── get_missing_tutorials()
│   ├── split_by_pages()
│   ├── process_chunk_with_llm()
│   └── merge_chunk_results()
│   Output: Updated indexed_tutorials.json
│
├── transform_to_metadata.py       ← Stage 3: Indexed data → app metadata
│   ├── load_indexed_tutorials()
│   ├── build_cumulative_topics()
│   ├── build_topic_context()
│   └── build_metadata()
│   Output: db/metadata.json (final curriculum data)
│
├── DATABASE & MATERIAL
├── db/
│   ├── metadata.json              ← **SOURCE OF TRUTH** (generated by pipeline)
│   │   Structure:
│   │   {
│   │     "tutorial_1": {
│   │       "display_name": "Tutorial 1 — Intro to Algorithm Analysis",
│   │       "topics": [18 cumulative topics],
│   │       "topic_context": "## Key Algorithms\n## Theorems and Concepts"
│   │     },
│   │     ...
│   │     "tutorial_8": {
│   │       "display_name": "Tutorial 8 — Shortest Paths",
│   │       "topics": [67 cumulative topics from T1-T8],
│   │       "topic_context": "..."
│   │     }
│   │   }
│   │
│   ├── metadata_backup.json       ← Auto-created backup before overwrite
│   ├── metadata_enhanced.json     ← Previous version (kept for reference)
│   ├── hw1_os/                    ← Custom tutorial data (expandable)
│   └── tutorial_{1-8}/            ← Chroma vector stores
│       ├── .chroma/
│       │   ├── data.parquet       ← Embedded chunks
│       │   ├── index/
│       │   └── ...
│       └── metadata files
│
├── raw_tutorial_texts/            ← Output of Stage 1 (PDF extraction)
│   ├── tutorial_1_raw.txt
│   ├── tutorial_2_raw.txt
│   └── ... (8 files total)
│
├── DOCUMENTATION & REFERENCE
├── PIPELINE_README.md             ← Older pipeline documentation
├── README_LEARNING_PHASE.md       ← Learning phase notes
├── TEST_RESULTS.md                ← Previous test outcomes
├── LEARNING_PHASE_TODO.md         ← TODO list
├── STEP_0_LOCATE_MATERIALS.md     ← Material setup instructions
├── TO_DO_LIST.md                  ← Task list
│
├── HELPER SCRIPTS
├── show_new_prompt.py             ← Display current system prompt
├── show_prompt.py                 ← Display system prompt (legacy)
├── show_system_prompt.py          ← Display system prompt (legacy)
├── show_t8_system_prompt.py       ← Display T8-specific prompt
├── audit_prompts.py               ← Audit all prompts
├── deep_check.py                  ← Deep system check
├── diagnose.py                    ← Diagnostic tool
├── extract_curriculum.py          ← Extract curriculum from metadata
├── extract_from_chroma.py         ← Extract stored vectors
├── full_fib_search.py             ← Search example
├── rebuild_metadata.py            ← Metadata regeneration
├── reingest_all.py                ← Reingest all tutorials
├── bulk_ingest.py                 ← Bulk ingestion (legacy)
├── bulk_ingest2.py                ← Bulk ingestion v2 (legacy)
├── ingest.py                      ← Single ingest (legacy)
│
├── OUTPUT & LOGS
├── indexed_tutorials.json         ← Stage 2 output (before metadata)
├── extracted_tutorials_preview.json ← Preview of extraction
├── ingest_log.txt                 ← Ingest logs
├── deep_check.txt                 ← Deep check results
├── diagnose_report.txt            ← Diagnostic report
├── full_fib_search.txt            ← Search results log
│
├── CONFIGURATION
├── .env                           ← Local API keys (GITHUB_TOKEN)
│                                    **DO NOT COMMIT**
├── .env.example                   ← Template (commit this)
│                                    ```
│                                    LLM_PROVIDER=openai
│                                    GITHUB_TOKEN=ghp_...
│                                    ```
└── .venv/                         ← Virtual environment (DO NOT COMMIT)
    └── [Python packages]
```

---

## 🔄 The Complete Pipeline

### **Stage 0: Prerequisites**
- Collect 8 algorithm tutorial PDFs (algolectures.zip)
- Place in `/material/` directory
- Ensure `GITHUB_TOKEN` env var set (for Azure OpenAI API access)

### **Stage 1: PDF Extraction** (`extract_tutorials_pipeline.py`)

**Input:** 8 tutorial PDFs
```
material/
  ├── algolectures_1.pdf  (20 pages, 0.57 MB)
  ├── algolectures_2.pdf  (26 pages, 0.81 MB)
  ├── ... (6 more PDFs)
  └── algolectures_8.pdf  (24 pages, 2.53 MB)
```

**Process:**
- Read each PDF with PyPDF2
- Extract text page-by-page
- Add page markers (`[PAGE X]`) for structure preservation
- Store as raw text files

**Output:** `raw_tutorial_texts/tutorial_{1-8}_raw.txt`
```
tutorial_1_raw.txt      (20,338 characters)
tutorial_2_raw.txt      (22,541 characters)
...
tutorial_8_raw.txt      (15,178 characters)
```

**Run:**
```bash
python extract_tutorials_pipeline.py
```

---

### **Stage 2: LLM Indexing** (`process_with_llm.py` + `process_failed_tutorials.py`)

**Input:** Raw tutorial texts

**Process:**
1. For each tutorial (T1-T8):
   - Send raw text to ChatGPT 4o mini with indexing prompt
   - ChatGPT extracts structured data:
     - `topics`: List of concepts/algorithms taught
     - `algorithms`: Name, complexity, description
     - `theorems_and_concepts`: Math concepts, definitions
   - Parse JSON response from model

2. **For large tutorials (T6, T7) that exceed token limits:**
   - Split by page markers (preserves semantic structure)
   - Process each chunk separately
   - Merge results by deduplicating topic names

**Output:** `indexed_tutorials.json`
```json
{
  "tutorial_1": {
    "topics": ["Introduction to Algorithm Design and Analysis", ..., 18 total],
    "algorithms": [
      {
        "name": "Algorithm for Maximum Diners",
        "complexity": "O(n log n)",
        "description": "..."
      }
    ],
    "theorems_and_concepts": [...]
  },
  ...
  "tutorial_8": {
    "topics": [...],
    "algorithms": [...],
    "theorems_and_concepts": [...]
  }
}
```

**Run:**
```bash
python process_with_llm.py          # Process T1-T8
# (if T6-T7 fail due to tokens)
python process_failed_tutorials.py  # Reprocess T6-T7 only (chunked)
```

---

### **Stage 3: Metadata Generation** (`transform_to_metadata.py`)

**Input:** `indexed_tutorials.json`

**Process:**
1. **Build cumulative topic lists:**
   - T1: 18 topics (from T1)
   - T2: 25 topics (T1 + T2)
   - T3: 33 topics (T1 + T2 + T3)
   - ...
   - T8: 67 topics (T1 + T2 + ... + T8)

   This enforces progressive curriculum: T1 can only access T1 topics; T8 can access all topics.

2. **Format course material:**
   ```
   ## Key Algorithms
   - **Dijkstra's Algorithm** (Complexity: O(E + V log V))
     An efficient algorithm for finding shortest paths...
   
   ## Theorems and Concepts
   - **Shortest Path Property**: Every sub-path of a shortest path is itself a shortest path.
   ```

3. **Build metadata structure:**
   ```json
   {
     "tutorial_1": {
       "display_name": "Tutorial 1 — Intro to Algorithm Analysis",
       "topics": [...],
       "topic_context": "## Key Algorithms\n..."
     },
     ...
   }
   ```

4. **Backup & overwrite:** Auto-creates `metadata_backup.json` before writing new version

**Output:** `db/metadata.json` (single source-of-truth for all curriculum)

**Run:**
```bash
python transform_to_metadata.py
```

---

### **Stage 4: Vector Indexing** (Automatic in app.py)

**When:** First time a tutorial is selected in the app

**Process:**
1. Load `metadata.json` → get `topic_context` (formatted material)
2. Chunk material into 1000-char overlapping sections
3. Embed with all-MiniLM-L6-v2
4. Store in Chroma vector DB at `db/tutorial_{1-8}/`

**Why:** Enables semantic search to retrieve relevant course snippets when student asks questions

---

## 🚀 Installation & Setup

### **1. Clone/Setup Project**
```bash
cd C:\Users\stein\tutor-bot
```

### **2. Create Virtual Environment**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure API Keys**
Create `.env` file in project root:
```
LLM_PROVIDER=openai
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Where to get `GITHUB_TOKEN`:**
- Go to: https://github.com/settings/tokens
- Create new token with `read:user` scope
- Copy token to `.env`

### **5. Verify Setup**
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('GITHUB_TOKEN:', os.getenv('GITHUB_TOKEN')[:10] + '...')"
```

Should print your token prefix.

---

## 🎯 Running the Application

### **Fresh Start (with new PDFs)**

```bash
# Stage 1: Extract PDFs
python extract_tutorials_pipeline.py

# Stage 2: Index with LLM
python process_with_llm.py

# (If T6-T7 fail)
python process_failed_tutorials.py

# Stage 3: Generate metadata
python transform_to_metadata.py

# Stage 4: Launch app
streamlit run app.py
```

App opens at: **http://localhost:8501**

### **Normal Operation (metadata already exists)**

```bash
streamlit run app.py
```

---

## 🔧 Key Components Explained

### **app.py — Main Application**

#### Sections:

| Section | Purpose |
|---------|---------|
| **Page Config & CSS** | Streamlit settings, custom styling (dark sidebar, light main) |
| **Session State** | Persist user messages, metadata, chat history across reruns |
| **load_meta()** | Load `metadata.json` into `st.session_state` |
| **get_llm()** | Initialize ChatGPT 4o mini client from `GITHUB_TOKEN` |
| **build_chain()** | Construct LangChain RAG pipeline:<br/>• Topic gate (whitelist)<br/>• CumulativeRetriever (search)<br/>• ChatPromptTemplate (prompt)<br/>• MessagesPlaceholder (history)<br/>• LLM chain |
| **Sidebar** | Admin panel: tutorial selector, clear button, API key status |
| **Main Chat Loop** | Display messages, handle input, stream response, update history |

#### Key Functions:

**`build_chain()`** (lines ~310-420)
- Creates LangChain chain with:
  - System prompt: Teacher role + topic gate + material context
  - Retriever: CumulativeRetriever (searches T1 through T_current)
  - Memory: Chat history as MessagesPlaceholder
  - Output: Streaming response from ChatGPT 4o mini

**System Prompt Structure:**
```
You are a teacher for a student learning algorithms.

The student has learned the following topics so far:
  • Introduction to Algorithm Design and Analysis
  • Deterministic Algorithms
  • ...

Current topic: Tutorial N — Topic Name

Guidelines:
- Answer questions ONLY about the topics listed above.
- If the student asks about something not covered yet, respond with:
  'We haven't covered [topic name] in this course yet. Based on what 
   we've studied so far, I can help you with: [suggest 2-3 related topics].'
- Explain concepts clearly and help them learn.
- Use examples from the course material to illustrate points.
- Encourage understanding and thinking, not just memorization.
- Be patient, supportive, and encouraging.

Course material reference:
[Formatted material from topic_context]

Format all math using Markdown/KaTeX:
- Inline math: $O(n^2)$, $T(n) = 2T(n/2) + O(n)$
- Block math: $$T(n) = aT(n/b) + f(n)$$
Use only $...$ and $$...$$ delimiters.

Retrieved course materials:
{context}
```

### **CumulativeRetriever** (Custom LangChain component)

**Purpose:** Search across tutorial T1 through T_current only

**Code Location:** app.py, lines ~180-210

**How it works:**
1. Student selects Tutorial N
2. Retriever searches Chroma stores for T1, T2, ..., T_N only
3. Ignores T_{N+1}, T_N+2, ..., T_8 (future tutorials)
4. Returns 4-8 most relevant passages

**Why:** Ensures bot only discusses material already taught

### **db/metadata.json** (Source of Truth)

**Format:**
```json
{
  "tutorial_N": {
    "display_name": "Tutorial N — Topic Name",
    "topics": [
      "Topic 1",
      "Topic 2",
      ...
      "Topic from Tutorial N"
    ],
    "topic_context": "## Key Algorithms\n..."
  }
}
```

**Key Properties:**
- `topics` is **cumulative**: T1 has T1 topics; T8 has T1+T2+...+T8 topics
- `topic_context` is **formatted material**: algorithms, theorems, definitions
- This file is **auto-generated** by `transform_to_metadata.py`
- **Never edit manually** — regenerate from PDFs using pipeline

### **Vector Stores** (db/tutorial_*/chroma/)

**What:** Embedded course material chunks
**Created:** First time tutorial is selected
**Used by:** CumulativeRetriever to find relevant passages
**Backed by:** Chroma + all-MiniLM-L6-v2 embeddings

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)

```env
# LLM Provider
LLM_PROVIDER=openai

# GitHub Token for Azure OpenAI API access
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **Streamlit Configuration** (`.streamlit/config.toml`)

To customize, create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#3498db"
backgroundColor = "#f0f4f8"
secondaryBackgroundColor = "#ffffff"
textColor = "#2c3e50"
font = "sans serif"

[logger]
level = "info"

[client]
showErrorDetails = true
```

### **LangChain Configuration** (in app.py)

- **Chunk size:** 1000 characters with 200-char overlap
- **Retriever limit:** Top 4-8 passages per query
- **LLM temperature:** 0.3 (deterministic)
- **Streaming:** Enabled (real-time token display)

---

## 🐛 Troubleshooting

### **Issue: "GITHUB_TOKEN not set"**
**Solution:**
```bash
# Create .env
echo "GITHUB_TOKEN=ghp_..." > .env

# Verify
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GITHUB_TOKEN'))"
```

### **Issue: "OpenAI API error: 401 Unauthorized"**
**Solution:** Token is invalid or expired
```bash
# Generate new token at: https://github.com/settings/tokens
# Update .env and restart app
```

### **Issue: "Chat returns generic responses (not using course material)"**
**Solution:** Vector store not built or retrieved
```bash
# Check Chroma stores exist:
ls db/tutorial_1/.chroma/

# If missing, delete db/tutorial_* and restart app (rebuilds)
rm -r db/tutorial_*
streamlit run app.py
```

### **Issue: "Bot explains T7 topics in T1"**
**Solution:** Cumulative topics list is wrong
```bash
# Verify metadata.json topics are cumulative:
python -c "
import json
with open('db/metadata.json') as f:
    m = json.load(f)
    for t in ['tutorial_1', 'tutorial_8']:
        print(f'{t}: {len(m[t][\"topics\"])} topics')
"
# Expected: T1=18, T8=67
```

### **Issue: "Chat is slow"**
**Solution:** 
- Reduce chunk count in retriever (lines ~215 in app.py)
- Reduce LLM streaming buffer size
- Use faster embedding model (but less accurate)

### **Issue: "Vector store corrupted"**
**Solution:**
```bash
# Rebuild from scratch
rm -r db/tutorial_*
streamlit run app.py  # Auto-rebuilds on first access
```

---

## 📚 Full Pipeline Example (Step-by-Step)

### **Step 1: Extract PDFs**
```bash
$ python extract_tutorials_pipeline.py
Tutorial 1 (algolectures_1.pdf): 20,338 chars ✓
Tutorial 2 (algolectures_2.pdf): 22,541 chars ✓
...
Tutorial 8 (algolectures_8.pdf): 15,178 chars ✓
Created: raw_tutorial_texts/tutorial_1_raw.txt ... tutorial_8_raw.txt
```

### **Step 2: Index with LLM**
```bash
$ python process_with_llm.py
Tutorial 1: Indexing... Extracted 18 topics ✓
Tutorial 2: Indexing... Extracted 25 topics ✓
...
Tutorial 8: Indexing... Extracted 22 topics ✓
Created: indexed_tutorials.json
```

### **Step 3: Generate Metadata**
```bash
$ python transform_to_metadata.py
Building cumulative topics...
Tutorial 1: 18 topics ✓
Tutorial 2: 25 topics (18 + 7 new) ✓
...
Tutorial 8: 67 topics (18 + 7 + 8 + 6 + 8 + 5 + 4 + 4 new) ✓
Backed up: metadata.json → metadata_backup.json
Created: db/metadata.json
```

### **Step 4: Launch App**
```bash
$ streamlit run app.py
Streamlit app created. You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501

2026-01-15 14:32:01.234 Thread started
...
```

### **Step 5: Use App**
1. Open http://localhost:8501 in browser
2. Select **Tutorial 1** from dropdown
3. Ask: "Explain asymptotic notation"
   - ✅ Bot accepts (in T1 topics)
   - 📚 Searches course material
   - 🎓 Provides detailed explanation
4. Ask: "Explain Dijkstra's algorithm"
   - ❌ Bot rejects (not in T1 topics)
   - 💡 Suggests related topics: "algorithm description, optimization algorithms, correctness"

---

## 🔐 Security Notes

- **Never commit `.env`** — it contains API tokens
- **`.gitignore` excludes:** `.env`, `.venv/`, `db/`, `*.pyc`
- **GITHUB_TOKEN is sensitive** — treat like password
- **API costs:** Monitor ChatGPT usage (4o mini is cheap)

---

## 📞 Support

- **Chat not responding?** Check GITHUB_TOKEN in `.env`
- **PDFs not extracted?** Verify files exist in `/material/`
- **Topics missing?** Regenerate metadata: `python transform_to_metadata.py`
- **Vector search broken?** Delete `db/tutorial_*/` and restart app

---

## 📄 License

[Your License Here]

---

**Generated:** 2026-01-15  
**Version:** 1.0  
**Python:** 3.11  
**Streamlit:** 1.40+

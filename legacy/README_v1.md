# 🎓 Streamlit Tutoring Bot with Curriculum-Enforced RAG

A lightweight interactive tutoring system that teaches algorithms through a Streamlit web interface, powered by ChatGPT 4o mini with enforced cumulative learning progression.

## 📋 Quick Overview

This project creates an **interactive tutoring chatbot** for teaching algorithms with these core features:

- **Real-time Chat Interface**: Streamlit-based UI with message history and streaming responses
- **Curriculum Boundaries**: Student can only learn topics from current tutorial + all prior tutorials (cumulative progression)
- **Pre-indexed Material**: Uses metadata.json with pre-extracted course material (no vector search needed)
- **Math Rendering**: Full KaTeX support for inline/block mathematical notation
- **Natural Teaching Style**: Friendly teacher-student dialogue

### Key Problem Solved

**Curriculum Boundary Enforcement**: The bot prevents discussing advanced topics before foundational concepts. For example:
- Tutorial 1: Student cannot ask about Dijkstra's algorithm (hasn't been introduced yet)
- Tutorial 8: Student can ask about Dijkstra's algorithm (covered in Tutorial 8)

This is achieved through an **explicit topic whitelist** in the system prompt, ensuring the LLM stays within scope.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT WEB UI                         │
│  (Chat interface, tutorial selector, settings panel)       │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ Load metadata.json    │
         │ (topics + material)   │
         └───────────┬───────────┘
                     │
         ┌───────────▼──────────────┐
         │   LangChain Pipeline     │
         │  (Prompt + Chat)         │
         └───────────┬──────────────┘
                     │
                ┌────▼─────────┐
                │ ChatGPT 4o   │
                │ min (Azure   │
                │ OpenAI API)  │
                └──────────────┘
```

### Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Streamlit App** | Web UI and chat orchestration | Streamlit 1.40+ |
| **LangChain** | Prompt templates and chat chain | LangChain 0.3+ |
| **ChatGPT 4o mini** | LLM backend for responses | Azure OpenAI API (GitHub Copilot) |
| **metadata.json** | Curriculum and material index | Pre-indexed JSON |

---

## 📁 Directory Structure

```
C:\Users\stein\tutor-bot\
│
├── README.md                          # This file
├── app.py                             # Main Streamlit application (350+ lines)
├── requirements.txt                   # Python dependencies (minimal)
│
├── .venv/                             # Python virtual environment
│
├── db/                                # Database folder
│   └── metadata.json                  # **MAIN DATA FILE**: All curriculum info
│
├── extract_tutorials_pipeline.py      # Stage 1: PDF → raw text files
├── process_with_llm.py                # Stage 2: Raw text → indexed topics
├── process_failed_tutorials.py        # Stage 2b: Handle large PDFs
├── transform_to_metadata.py           # Stage 3: Indexed → metadata.json
│
└── algolectures.zip                   # Source: 8 tutorial PDFs (if needed)
```

### Key Files

**`app.py`** (Main Application, 350+ lines)
- `get_llm()`: Initializes ChatGPT 4o mini connection
- `build_chain()`: Constructs LangChain prompt with curriculum boundary + material
- Chat loop: Displays history, handles input, streams responses
- CSS fixes: Light pink background for code notation

**`db/metadata.json`** (Single Source of Truth)
```json
{
  "tutorial_1": {
    "display_name": "Tutorial 1 — Intro to Algorithm Analysis",
    "topics": [
      "Introduction to Algorithm Design and Analysis",
      "Algorithm Complexity",
      ...18 topics total...
    ],
    "topic_context": "## Key Algorithms\n- **Algorithm for...**"
  },
  ...
  "tutorial_8": {
    "display_name": "Tutorial 8 — Shortest Paths",
    "topics": [67 cumulative topics from T1-T8],
    "topic_context": "..."
  }
}
```

**Cumulative Structure**:
- Tutorial 1: 18 topics
- Tutorial 2: 25 topics (T1 + T2)
- Tutorial 8: 67 topics (T1 + T2 + ... + T8)

---

## 🔄 Data Pipeline (3 Stages)

### **Stage 1: PDF Text Extraction**

**File**: `extract_tutorials_pipeline.py`

Converts 8 PDF files to raw text files with page markers:
```bash
python extract_tutorials_pipeline.py
```

**Output**: `raw_tutorial_texts/tutorial_1_raw.txt` through `tutorial_8_raw.txt`

---

### **Stage 2: LLM-Based Topic Indexing**

**Files**: `process_with_llm.py` + `process_failed_tutorials.py`

Sends raw tutorial texts to ChatGPT 4o mini and extracts structured topics:
```bash
# Process all tutorials
python process_with_llm.py

# Handle large PDFs (T6-T7) with chunking
python process_failed_tutorials.py
```

**Output**: `indexed_tutorials.json` with topics, algorithms, and theorems per tutorial

**Example Request**:
```
Extract all topics, algorithms, and theorems from this tutorial.

Return JSON:
{
  "topics": ["Topic 1", "Topic 2", ...],
  "algorithms": [
    {
      "name": "Algorithm Name",
      "complexity": "O(n log n)",
      "description": "..."
    }
  ],
  "theorems_and_concepts": [...]
}
```

---

### **Stage 3: Metadata Transformation**

**File**: `transform_to_metadata.py`

Transforms indexed material into app-ready format:
```bash
python transform_to_metadata.py
```

**Process**:
1. Build cumulative topics (T1 has 18, T2 has 25, T8 has 67)
2. Format algorithms/theorems as readable markdown
3. Create final `db/metadata.json`
4. Backup old metadata before overwrite

**Output**: `db/metadata.json` (ready for app)

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Windows PowerShell or terminal
- GitHub token (or OpenAI API key)

### Step 1: Create Virtual Environment
```bash
cd C:\Users\stein\tutor-bot
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set API Key
```bash
# GitHub Copilot (recommended)
$env:GITHUB_TOKEN = "your-github-token-here"

# OR OpenAI
$env:OPENAI_API_KEY = "your-openai-key-here"
```

### Step 4: Run the Pipeline (One-Time)
```bash
# Extract PDFs
python extract_tutorials_pipeline.py

# Index with LLM
python process_with_llm.py
python process_failed_tutorials.py  # if needed

# Transform to metadata
python transform_to_metadata.py
```

### Step 5: Start the App
```bash
streamlit run app.py
```

Open browser to `http://localhost:8501`

---

## 🚀 Using the App

1. **Select Tutorial**: Choose from dropdown (Tutorial 1-8)
2. **Ask Questions**: Type any question about the tutorial's topics
3. **Get Responses**: Bot answers with curriculum enforcement
4. **View History**: Scroll to see past questions/answers

### Sidebar Settings
- **API Key**: Add GitHub Copilot or OpenAI key
- **Current LLM**: Shows which provider is active

---

## 🎯 Key Features

### 1. Curriculum Boundary Enforcement
Explicit topic whitelist prevents out-of-scope discussions:
```
User (T1): "Explain Dijkstra's algorithm"
Bot: "We haven't covered Dijkstra's algorithm in this course yet. 
Based on what we've studied so far, I can help you with: 
[suggests 2-3 T1 topics]"
```

### 2. Cumulative Learning
Each tutorial builds on all prior tutorials:
```
T1: 18 base topics
T2: 18 + 7 new = 25 total
T3: 25 + 8 new = 33 total
...
T8: 60 + 7 new = 67 total
```

### 3. Material Injection
Pre-indexed material is injected directly into system prompt (no vector search):
```
System Prompt:
  Topics: [explicit whitelist]
  Course Material: [formatted from topic_context]
  Guidelines: [teaching approach]
  Chat History: [conversation so far]
```

### 4. Natural Teaching Style
Simplified system prompt (no Socratic levels):
```
You are a teacher for a student learning algorithms.

The student has learned these topics: [list]

Guidelines:
- Answer questions ONLY about topics listed above
- If asked about unlisted topic: "We haven't covered [topic] yet..."
- Explain clearly using course examples
- Be supportive and encouraging
```

### 5. Math Rendering
Full KaTeX support:
- Inline: `$O(n^2)$` 
- Block: `$$T(n) = 2T(n/2) + O(n)$$`
- Custom CSS for dark mode (light pink background)

---

## 📦 Dependencies

Minimal and focused:
```
streamlit>=1.40          # Web UI
langchain>=0.3           # Prompt/chat orchestration
langchain-openai>=0.2    # ChatGPT integration
langchain-ollama>=0.2    # Optional: local LLM fallback
python-dotenv>=1.0       # Environment variables
pypdf>=4.0               # PDF extraction (for pipeline only)
```

**NO vector databases, NO embeddings, NO external AI models.**

---

## 🔧 Configuration

### Environment Variables
```bash
GITHUB_TOKEN      # Recommended: GitHub Copilot PAT
OPENAI_API_KEY    # Alternative: OpenAI API key
LLM_PROVIDER      # "openai" (default) or "ollama"
OLLAMA_LLM_MODEL  # Model name if using Ollama
OLLAMA_BASE_URL   # Ollama endpoint (default: http://localhost:11434)
```

### System Prompt Location
Edit `build_chain()` function in `app.py` (lines ~240-290) to customize:
- Topic boundary rules
- Teaching guidelines
- Math formatting instructions

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **App Startup** | <3s |
| **Response Time** | 3-10s (streaming) |
| **Memory Usage** | ~200MB (Streamlit + Python) |
| **No dependencies on** | Vector DB, embeddings, or GPU |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt` |
| "No module named 'openai'" | `pip install langchain-openai` |
| "GITHUB_TOKEN not set" | `$env:GITHUB_TOKEN = "your-token"` |
| "No tutorials loaded" | Ensure `db/metadata.json` exists and is populated |

---

## 📝 Example Workflow

### Initial Setup (One-Time, ~10 minutes)
```bash
# 1. Extract PDFs
python extract_tutorials_pipeline.py

# 2. Process with LLM (takes 5-10 min due to API calls)
python process_with_llm.py
python process_failed_tutorials.py  # if T6-T7 needed chunking

# 3. Transform to metadata
python transform_to_metadata.py

# 4. Verify
# Check that db/metadata.json contains all tutorials with topics
```

### Daily Usage
```bash
# Start app
streamlit run app.py

# Select tutorial from dropdown
# Ask questions → get curriculum-bounded responses
# Clear history when done
```

---

## 🎓 Teaching Philosophy

**Natural Dialogue over Socratic Method**: 

The system provides **clear explanations** grounded in course material, while maintaining **topic boundaries** through the curriculum whitelist.

Example interaction:
- User: "What is Big-O notation?"
- Bot: "Big-O notation is a mathematical tool used to describe the behavior of functions as input grows toward infinity. For example, O(n²) means... [full explanation with examples]"

Rather than:
- User: "What is Big-O notation?"
- Bot: "Can you think about what happens to this function when the input gets really big?" (Socratic)

---

## 📚 Curriculum Structure

```
Tutorial 1: Intro to Algorithm Analysis (18 topics)
├─ Introduction to Algorithm Design
├─ Asymptotic Notation (Big-O, Omega, Theta)
├─ Time Complexity Comparison
└─ 15 more topics

Tutorial 2: Divide and Conquer (+7 new = 25 total)
├─ Divide and Conquer Strategy
├─ Merge Sort
├─ Fast Exponentiation
└─ 4 more new topics

...

Tutorial 8: Shortest Paths (+7 new = 67 total)
├─ Dijkstra's Algorithm
├─ Bellman-Ford Algorithm
├─ Graph Traversal
└─ 4 more new topics
```

Topics are **cumulative**: Students build from foundational concepts to advanced algorithms.

---

## ❓ FAQ

**Q: Can I add more tutorials?**
A: Yes. Add PDFs, update `extract_tutorials_pipeline.py`, and run the 3-stage pipeline.

**Q: How do I change the teaching style?**
A: Edit the system prompt in `app.py` lines ~260-280.

**Q: Why no vector database?**
A: Material is pre-indexed in metadata.json. Vector search adds complexity without benefit for fixed, pre-indexed data.

**Q: Can I use a local LLM?**
A: Yes. Set `OLLAMA_LLM_MODEL` and `OLLAMA_BASE_URL` to use local models via Ollama.

**Q: What if the bot explains something out of scope?**
A: The topic whitelist in metadata.json is incomplete. Regenerate it by re-running the pipeline.

---

## 🚀 Next Steps

1. Run the pipeline: `python extract_tutorials_pipeline.py`
2. Start the app: `streamlit run app.py`
3. Add your API key in the sidebar settings
4. Select a tutorial and start asking questions!

---

**Version**: 1.0 (Simplified)
**Last Updated**: July 11, 2026
**Status**: Production Ready ✓
**Dependencies**: 6 packages (minimal footprint)

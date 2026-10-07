# 🚀 Quick Start Guide

## For Users: How to Use the Tutor

### 1. Open the App
```
http://localhost:8501
```

### 2. Select Your Settings
- **Language**: English or עברית (Hebrew)
- **Mode**: 📖 Learn (course material) or 💪 Homework (problem help)
- **Week**: Choose which week/tutorial
- **Model**: Pick Ollama (local) or OpenAI/GitHub (cloud)

### 3. Ask Questions
Four ways to interact:

**A) Click Suggestion Chips**
- \"Explain: Algorithm definition and categories\"
- \"Quiz me on this week's material\"
- \"Give me an example of...\"

**B) Type Free-Form Questions**
- \"What's a proof by induction?\"
- \"Can you show me an example of recursion?\"
- \"Quiz me\" (automatic quiz mode)

**C) Homework Mode**
- Select \"💪 Homework\" mode
- Choose which assignment
- Ask about specific problem numbers

**D) Bilingual Support**
- Type in Hebrew or English
- System auto-translates and responds
- Hebrew text renders right-to-left automatically

### 4. Work with Results
- **Read the answer** (grounded in course material)
- **See sources**: Click \"Show sources\" to see which passages were used
- **Get hints**: System provides guidance, not full solutions
- **Ask follow-ups**: Continue the conversation naturally

---

## For Admins: Deploy & Manage

### Prerequisites
- Python 3.11+
- 4GB+ RAM
- For local models: Ollama installed
- For cloud models: GitHub/OpenAI API key

### Setup (First Time)

```bash
# 1. Clone/setup project
cd tutor-bot
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\Activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure course
#    Place PDFs in:
#    - material/lectures/*.pdf (course material)
#    - material/Homework/*.pdf (assignments)
#    
#    Create material/course.json:
{
  "name": "Algorithms",
  "subject": "Computer Science",
  "unit_label": "Tutorial",
  "lectures": [
    {"title": "Introduction to Algorithms", "weeks": 1},
    ...
  ],
  "glossary": [...],
  "homework_weeks": [4, 4, 6, 8, 9]
}

# 4. Build knowledge base (5-10 min)
python build_course.py --all

# 5. Verify it built correctly
python build_course.py --check
```

### Running the App

**Option A: Local (Development)**
```bash
# Start Ollama in one terminal
ollama serve

# Start Streamlit in another
streamlit run app.py
```

**Option B: With OpenAI API**
```bash
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...
streamlit run app.py
```

**Option C: Production**
```bash
# Use environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export UI_LANGUAGE=en

# Run with production settings
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.maxUploadSize=1000 \
  --logger.level=info
```

### Environment Variables

Create `.env` file:
```env
# Required
OLLAMA_BASE_URL=http://localhost:11434
EMBED_MODEL=bge-small-en-v1.5

# Optional (only for specific models)
OLLAMA_LLM_MODEL=mistral
TRANSLATION_PROVIDER=auto
LLM_MAX_TOKENS=1200
LLM_TIMEOUT_SECONDS=120
RETRIEVAL_MODE=hybrid

# Only if using cloud APIs
GITHUB_TOKEN=ghp_...
OPENAI_API_KEY=sk-...
```

### Maintenance

**Weekly**
```bash
# Check index integrity
python build_course.py --check

# Review any translation failures
# (Show up in app error messages)
```

**Monthly**
```bash
# Backup curriculum
cp -r material/english material/english.backup
cp db/metadata.json db/metadata.backup

# Update to new course (optional)
python build_course.py --stages extract,notes,topics,curriculum,homework
# Review in material/curriculum_review/
python build_course.py --install --check
```

**Anytime (Rebuild Index)**
```bash
# If you change embedding model or course materials
python build_course.py --install --check
```

---

## Troubleshooting

### App Won't Start
```bash
# Check Python version
python --version  # Must be 3.11+

# Check dependencies
pip list | grep -E \"streamlit|langchain|chromadb\"

# Reinstall if needed
pip install --upgrade -r requirements.txt

# Check for port conflicts
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows
```

### No Responses from Model
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check model is available
ollama list

# Download model if needed
ollama pull mistral

# For OpenAI, check API key
echo $OPENAI_API_KEY  # Should show sk-...
```

### Slow Generation
```bash
# Could be:
# 1. Model is 13B+ (use 3B-8B models)
ollama pull mistral:7b  # Faster

# 2. Retrieval has too many chunks
# Go to ⚙️ Retrieval → Passages: reduce from 8 to 4

# 3. Reranking is slow
# Disable Hybrid+Rerank, use Dense or Hybrid
```

### Translation Issues
```bash
# For Hebrew support:
# Option 1: Use OpenAI (most reliable)
export OPENAI_API_KEY=sk-...

# Option 2: Download Hebrew model
ollama pull aya:8b

# Set in app: 🌐 Hebrew / עברית → Ollama → aya:8b
```

### Missing Course Material
```bash
# Verify PDFs are placed correctly
ls material/lectures/  # Should have *.pdf files
ls material/Homework/  # Should have assignment PDFs

# Rebuild if you added new PDFs
python build_course.py --stages extract,notes,topics,curriculum,homework

# Check extraction worked
wc -l db/chunks.jsonl  # Should be 100+
```

---

## Performance Tuning

### For Faster Responses
```env
# Use smaller models
OLLAMA_LLM_MODEL=mistral:7b
EMBED_MODEL=bge-small-en-v1.5

# Use dense retrieval (faster than hybrid)
RETRIEVAL_MODE=dense

# Reduce context passages
# Set Passages: 2-4 in ⚙️ Retrieval

# Reduce timeout
LLM_MAX_TOKENS=800
LLM_TIMEOUT_SECONDS=60
```

### For Better Quality
```env
# Use larger models
OLLAMA_LLM_MODEL=mistral:13b

# Use hybrid + reranking (slower, better)
RETRIEVAL_MODE=hybrid+rerank

# Use more passages
# Set Passages: 6-8 in ⚙️ Retrieval

# Increase timeout
LLM_MAX_TOKENS=1500
LLM_TIMEOUT_SECONDS=180
```

### For Multi-User (Scale Up)
```bash
# Use Gunicorn + multiple workers
gunicorn -w 4 -k sync \
  --timeout 300 \
  -b 0.0.0.0:8501 \
  'streamlit.web.cli:_main_run()'

# Use cloud models (more reliable under load)
export OPENAI_API_KEY=sk-...
export GITHUB_TOKEN=ghp_...

# Use managed retrieval service
# (Optional: Move ChromaDB to separate service)
```

---

## Support

### Check Logs
```bash
# Terminal output shows:
# - Retrieval queries
# - LLM calls
# - Errors with diagnostics

# In app:
# - Errors appear in red banners
# - Diagnostics available in expansions
```

### Reporting Issues
Include:
1. The exact question asked
2. Week/mode selected
3. Model and provider being used
4. Error message (if any)
5. Terminal output

### Contact
- Code issues: Check GitHub repo
- Course content: Review `material/curriculum_review/`
- Model performance: Try different `OLLAMA_LLM_MODEL`

---

## Key Features Checklist

- ✅ Works with any course (PDF → knowledge base)
- ✅ Curriculum-gated (prevents jumping ahead)
- ✅ Multi-language (English + Hebrew)
- ✅ Quiz mode (practice with course material)
- ✅ Homework mode (guided help, never solutions)
- ✅ Local or cloud models (Ollama, OpenAI, GitHub)
- ✅ Citation system (shows source passages)
- ✅ Scope verification (respects learning order)
- ✅ Production-grade security (no key leaks)
- ✅ Professional UI (dark theme, responsive)

---

**Ready to teach? 🎓**

```bash
streamlit run app.py
```

Then visit: **http://localhost:8501**

# Learning Phase Pipeline — Complete Guide

## Overview

This pipeline extracts all 8 algorithm tutorials from the provided ZIP file and uses ChatGPT 4o mini to automatically generate a comprehensive, indexed learning material database.

**Goal**: Replace the manually-created topics/curriculum with material extracted directly from the official tutorials.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: PDF EXTRACTION                                             │
├─────────────────────────────────────────────────────────────────────┤
│ Input:  algolectures.zip (8 tutorial PDFs)                          │
│ Tool:   extract_tutorials_pipeline.py                               │
│ Output: raw_tutorial_texts/tutorial_{1-8}_raw.txt                   │
│ Size:   20K-32K characters per tutorial                             │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: LLM INDEXING                                               │
├─────────────────────────────────────────────────────────────────────┤
│ Input:  raw_tutorial_texts/tutorial_{1-8}_raw.txt                   │
│ Tool:   process_with_llm.py                                         │
│ LLM:    ChatGPT 4o mini (via GitHub Copilot API)                    │
│ Output: indexed_tutorials.json                                      │
│ Format: Topics, algorithms, theorems for each tutorial              │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: METADATA GENERATION                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Input:  indexed_tutorials.json                                      │
│ Tool:   transform_to_metadata.py                                    │
│ Output: db/metadata.json (cumulative topic lists)                   │
│ Format: Ready for Streamlit app                                     │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: APPLICATION RESTART                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Action: Restart Streamlit app                                       │
│ Result: All topic boundaries now respect extracted curriculum       │
│ Topics: Loaded from indexed tutorials (not manual)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Execution

### Prerequisites

Ensure you have:
- Python 3.11+ with `.venv` virtual environment
- `GITHUB_TOKEN` environment variable set (for ChatGPT 4o mini API access)
- `PyPDF2` installed (will be installed automatically if missing)
- `C:\Users\stein\Downloads\algolectures.zip` extracted

### Step 1: Extract PDFs

```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe extract_tutorials_pipeline.py
```

**What happens:**
- Extracts text from all 8 tutorial PDFs
- Saves raw text files to `raw_tutorial_texts/`
- Creates `extracted_tutorials_preview.json`
- Prepares prompts for LLM

**Time:** ~5 seconds
**Output files:**
- `raw_tutorial_texts/tutorial_1_raw.txt` through `tutorial_8_raw.txt`
- `extracted_tutorials_preview.json`
- `llm_prompts.json`

---

### Step 2: Send to ChatGPT 4o mini

**⚠️ IMPORTANT: Set GitHub Token First**

```powershell
# In PowerShell, set the environment variable:
$env:GITHUB_TOKEN = "your_github_token"

# Then run:
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe process_with_llm.py
```

**What happens:**
- Reads each raw tutorial text
- Sends to ChatGPT 4o mini with structured prompt
- Extracts topics, algorithms, theorems
- Saves results to `indexed_tutorials.json`

**Time:** ~30-60 seconds (depends on API response times)
**Output files:**
- `indexed_tutorials.json` (the indexed material from ChatGPT)

**Expected output:**
```
[T1] Sending to ChatGPT 4o mini (attempt 1)...
     ✓ Successfully indexed 25 topics
[T2] Sending to ChatGPT 4o mini (attempt 1)...
     ✓ Successfully indexed 18 topics
... (continues for T3-T8)
```

---

### Step 3: Transform to Metadata

```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe transform_to_metadata.py
```

**What happens:**
- Loads `indexed_tutorials.json`
- Builds cumulative topic lists (T1 only has T1 topics, T2 has T1+T2, etc.)
- Formats curriculum detail sections
- Creates new `db/metadata.json`
- Backs up old `db/metadata.json` to `db/metadata_backup.json`

**Time:** ~2 seconds
**Output files:**
- `db/metadata.json` (REPLACES old metadata.json)
- `db/metadata_backup.json` (backup of old version)

**Expected output:**
```
T1: 20 cumulative topics
T2: 38 cumulative topics
T3: 45 cumulative topics
...
T8: 120 cumulative topics (all topics from all tutorials)
```

---

### Step 4: Restart Streamlit App

```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\streamlit run app.py
```

Or if already running: Press `R` in the Streamlit terminal to refresh.

**Result:**
- App now uses the extracted tutorials as source of truth
- Topic boundaries enforced based on actual course material
- All Socratic responses constrained to what students learned

---

## Files Generated by Pipeline

| File | Purpose | Generated By | Can Delete? |
|------|---------|--------------|------------|
| `raw_tutorial_texts/` | Raw PDF text extraction | Stage 1 | ✅ Yes (cache) |
| `extracted_tutorials_preview.json` | Preview of extracted text | Stage 1 | ✅ Yes (cache) |
| `llm_prompts.json` | LLM prompt templates | Stage 1 | ✅ Yes (cache) |
| `indexed_tutorials.json` | LLM output (indexed material) | Stage 2 | ✅ Yes (cache) |
| `db/metadata_backup.json` | Backup of old metadata | Stage 3 | ✅ Yes (old) |
| `db/metadata.json` | **NEW ACTIVE METADATA** | Stage 3 | ❌ **NO** |

---

## Troubleshooting

### Issue: `GITHUB_TOKEN` not found

**Solution:**
```powershell
# Set the token in current session:
$env:GITHUB_TOKEN = "ghp_xxxxx..."

# Or set permanently (Windows):
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_xxxxx...", "User")

# Verify:
echo $env:GITHUB_TOKEN
```

### Issue: JSON parsing error from ChatGPT

**Solution:**
The script has retry logic (3 attempts). If still failing:
1. Check `indexed_tutorials.json` exists
2. Inspect the response manually
3. Check API quota and rate limits

### Issue: PyPDF2 not found

**Solution:**
```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe -m pip install PyPDF2
```

### Issue: App not loading new metadata

**Solution:**
1. Stop the Streamlit app (Ctrl+C)
2. Clear cache: Delete `.streamlit/` folder (if exists)
3. Restart: `.venv\Scripts\streamlit run app.py`

---

## Data Flow Example

### Raw Extraction (Stage 1)
```
PDF: "Tutorial 1 — Intro to Algorithm Analysis"
     ↓ (extract text)
→ tutorial_1_raw.txt
  - 20,338 characters
  - 461 lines
  - Contains: algorithm definitions, complexity examples, sorting algorithms
```

### LLM Indexing (Stage 2)
```
tutorial_1_raw.txt + Prompt
     ↓ (send to ChatGPT 4o mini)
→ indexed_tutorials.json
{
  "tutorial_1": {
    "topics": ["Big-O notation", "time complexity", "insertion sort", ...],
    "algorithms": [{"name": "bubble sort", "complexity": "O(n²)", ...}],
    "theorems_and_concepts": [{"name": "asymptotic notation", ...}]
  }
}
```

### Metadata Generation (Stage 3)
```
indexed_tutorials.json
     ↓ (build cumulative lists & format)
→ db/metadata.json
{
  "tutorial_1": {
    "display_name": "Tutorial 1 — Intro to Algorithm Analysis",
    "topics": ["Big-O notation", "time complexity", ...],  // 20 topics
    "topic_context": "## Key Algorithms\n- **Bubble Sort** ..."
  },
  "tutorial_2": {
    "display_name": "Tutorial 2 — Divide and Conquer",
    "topics": ["Big-O notation", ..., "merge sort", ...],  // 38 topics (T1 + T2)
    "topic_context": "..."
  }
}
```

### App Usage (Stage 4)
```
app.py loads db/metadata.json
     ↓ (student selects Tutorial 2)
→ LLM receives system prompt with 38 allowed topics
     ↓ (student asks about Dijkstra)
→ LLM rejects: "We haven't covered Dijkstra's shortest path algorithm
   in this course yet up to this point. Based on what we've studied
   so far, I can help you with: divide and conquer, merge sort, or
   recurrence relations."
```

---

## Manual Intervention (If Needed)

If you need to edit the extracted material:

1. **Edit raw tutorial texts:**
   - Edit `raw_tutorial_texts/tutorial_{n}_raw.txt`
   - Re-run Step 2 (process_with_llm.py)

2. **Edit indexed material:**
   - Edit `indexed_tutorials.json`
   - Re-run Step 3 (transform_to_metadata.py)

3. **Edit metadata directly:**
   - Edit `db/metadata.json` (but will be overwritten on next pipeline run)

---

## Full Pipeline Command (One-Shot)

To run the entire pipeline in sequence:

```powershell
$env:GITHUB_TOKEN = "your_token"
cd C:\Users\stein\tutor-bot
Write-Host "Stage 1: Extracting PDFs..."
.venv\Scripts\python.exe extract_tutorials_pipeline.py

Write-Host "`nStage 2: Indexing with ChatGPT..."
.venv\Scripts\python.exe process_with_llm.py

Write-Host "`nStage 3: Generating metadata..."
.venv\Scripts\python.exe transform_to_metadata.py

Write-Host "`nDone! Restart Streamlit app with:"
Write-Host ".venv\Scripts\streamlit run app.py"
```

---

## Next Steps

After running the pipeline:

1. ✅ Restart Streamlit app
2. ✅ Test curriculum boundaries (e.g., ask about Dijkstra in T1 - should be rejected)
3. ✅ Verify topics are comprehensive
4. ✅ Adjust prompts if needed
5. ✅ Commit `db/metadata.json` to version control

---

## Architecture Notes

- **Why cumulative topics?** Students must learn prerequisites before advanced topics. T8 should have all topics.
- **Why extract to intermediate JSON files?** Allows inspection and debugging at each stage.
- **Why ChatGPT 4o mini?** Fast, reliable structured extraction from long documents.
- **Why backup old metadata?** Safety mechanism in case new extraction has issues.

---

## Contact / Support

For issues or questions about this pipeline, refer to the generated files:
- `indexed_tutorials.json` - Raw output from ChatGPT
- `extracted_tutorials_preview.json` - Raw PDF content
- `raw_tutorial_texts/` - Individual tutorial texts for manual inspection

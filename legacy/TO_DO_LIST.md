# Learning Phase Pipeline — TO-DO LIST

## ✅ COMPLETED

### Phase 1: Pipeline Setup (DONE)
- [x] Extract text from all 8 tutorials (PDFs → raw text)
  - Script: `extract_tutorials_pipeline.py`
  - Output: `raw_tutorial_texts/tutorial_{1-8}_raw.txt`
  - Status: Tested and working

- [x] Create LLM processing script to index material with ChatGPT 4o mini
  - Script: `process_with_llm.py`
  - Purpose: Extract topics, algorithms, theorems from each tutorial
  - Status: Ready to run

- [x] Create metadata transformation script
  - Script: `transform_to_metadata.py`
  - Purpose: Convert indexed material → metadata.json (app-ready format)
  - Status: Ready to run

- [x] Generate comprehensive documentation
  - Created: `PIPELINE_README.md`
  - Created: `TO_DO_LIST.md` (this file)
  - Status: Complete

---

## 🚀 NEXT STEPS (IN ORDER)

### Step 1: Set GitHub Token Environment Variable
**Status:** ⏳ AWAITING USER ACTION

```powershell
# Run this in PowerShell:
$env:GITHUB_TOKEN = "your_github_token"

# Where "your_github_token" is your GitHub Personal Access Token
# Need help? Get token from: https://github.com/settings/tokens
```

**Why:** Need API access to ChatGPT 4o mini via GitHub Copilot

---

### Step 2: Extract Tutorials from PDFs
**Status:** ⏳ READY TO RUN

```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe extract_tutorials_pipeline.py
```

**What it does:**
- Reads 8 tutorial PDFs from `algolectures_extracted/`
- Extracts raw text from each
- Saves to `raw_tutorial_texts/`
- Prepares LLM prompts

**Expected output:**
```
[T1] Extracted 20,338 characters
[T2] Extracted 18,520 characters
...
[T8] Extracted 15,178 characters
✓ Generated 8 LLM prompts
```

**Time:** ~5 seconds
**Output files:**
- `raw_tutorial_texts/tutorial_1_raw.txt` through `tutorial_8_raw.txt`
- `extracted_tutorials_preview.json`
- `llm_prompts.json`

---

### Step 3: Index Tutorials with ChatGPT 4o mini
**Status:** ⏳ READY TO RUN (after Step 1 & 2)

```powershell
$env:GITHUB_TOKEN = "your_token"  # Must set again each session
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe process_with_llm.py
```

**What it does:**
- Sends each raw tutorial to ChatGPT 4o mini
- Extracts topics, algorithms, theorems
- Parses JSON responses
- Saves to `indexed_tutorials.json`

**Expected output:**
```
[T1] Sending to ChatGPT 4o mini (attempt 1)...
     ✓ Successfully indexed 25 topics
[T2] Sending to ChatGPT 4o mini (attempt 1)...
     ✓ Successfully indexed 18 topics
... (continues for T3-T8)
✓ Indexed 8 tutorials
```

**Time:** ~30-60 seconds
**Output files:**
- `indexed_tutorials.json` (critical file - contains ChatGPT output)

---

### Step 4: Generate Metadata for App
**Status:** ⏳ READY TO RUN (after Step 3)

```powershell
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe transform_to_metadata.py
```

**What it does:**
- Loads `indexed_tutorials.json`
- Builds cumulative topic lists:
  - T1 has only T1 topics
  - T2 has T1 + T2 topics
  - T3 has T1 + T2 + T3 topics
  - ... (cumulative through T8)
- Formats curriculum detail sections
- Creates `db/metadata.json`
- Backs up old metadata to `db/metadata_backup.json`

**Expected output:**
```
T1: 20 cumulative topics
T2: 38 cumulative topics
T3: 45 cumulative topics
T4: 56 cumulative topics
T5: 63 cumulative topics
T6: 71 cumulative topics
T7: 92 cumulative topics
T8: 120 cumulative topics
✓ Metadata saved to: db/metadata.json
```

**Time:** ~2 seconds
**Output files:**
- `db/metadata.json` (REPLACES old metadata)
- `db/metadata_backup.json` (backup of old)

---

### Step 5: Restart Streamlit App
**Status:** ⏳ READY TO RUN (after Step 4)

```powershell
# If app is already running: Press Ctrl+C to stop it
# Then restart:
cd C:\Users\stein\tutor-bot
.venv\Scripts\streamlit run app.py

# Or simply press R in the running Streamlit terminal to refresh
```

**What it does:**
- App loads new `db/metadata.json`
- All topic boundaries now use extracted curriculum
- LLM system prompt includes real extracted topics
- Socratic responses constrained to learned material

**Expected result:**
- App starts on `http://localhost:8501`
- New metadata loaded from PDFs only
- No manual topics list (pure extraction)

---

## 🔍 VERIFICATION TESTS (After Step 5)

After restarting the app, test these scenarios:

### Test 1: Tutorial 1 Rejects Advanced Topic
```
Tutorial: T1 (Intro to Algorithm Analysis)
Question: "Explain Dijkstra's shortest path algorithm"
Expected: Rejection - "We haven't covered Dijkstra..."
Why: Dijkstra is T8 topic, not in T1 list
```

### Test 2: Tutorial 7 Accepts Graph Topic
```
Tutorial: T7 (Minimum Spanning Trees)
Question: "How does Kruskal's algorithm work?"
Expected: Full Socratic explanation
Why: Kruskal is in T7 topics list
```

### Test 3: Tutorial 8 Accepts Dijkstra
```
Tutorial: T8 (Shortest Paths)
Question: "Explain Dijkstra's shortest path algorithm"
Expected: Full Socratic explanation
Why: Dijkstra is in T8 topics list
```

---

## 📊 PIPELINE STATUS SUMMARY

| Stage | Script | Input | Output | Status |
|-------|--------|-------|--------|--------|
| 1 | `extract_tutorials_pipeline.py` | 8 PDFs | Raw texts | ✅ DONE |
| 2 | `process_with_llm.py` | Raw texts | `indexed_tutorials.json` | ⏳ READY |
| 3 | `transform_to_metadata.py` | Indexed JSON | `db/metadata.json` | ⏳ READY |
| 4 | Streamlit restart | New metadata | App running | ⏳ READY |

---

## 🎯 QUICK START (Copy-Paste)

```powershell
# 1. Set token
$env:GITHUB_TOKEN = "your_github_token"

# 2. Extract
cd C:\Users\stein\tutor-bot
.venv\Scripts\python.exe extract_tutorials_pipeline.py

# 3. Index with ChatGPT
.venv\Scripts\python.exe process_with_llm.py

# 4. Generate metadata
.venv\Scripts\python.exe transform_to_metadata.py

# 5. Restart app
.venv\Scripts\streamlit run app.py
```

---

## ❓ FAQ

**Q: Can I run all steps at once?**
A: Yes! See "Full Pipeline Command" in PIPELINE_README.md

**Q: What if Step 3 fails (ChatGPT API error)?**
A: Script has retry logic (3 attempts). Check GitHub token and API quota.

**Q: What if I want to edit the extracted material?**
A: Edit `indexed_tutorials.json` and re-run Step 4.

**Q: Will my old metadata be lost?**
A: No! Backed up to `db/metadata_backup.json` before Step 4.

**Q: Do I need to run this every time?**
A: No! Only when you want to refresh from the PDFs. App will use same metadata until you re-run.

**Q: How many topics will I have per tutorial?**
A: Depends on ChatGPT extraction. Typically 15-30 per tutorial.

---

## 📝 NOTES

- All intermediate files (raw texts, indexed JSON) can be deleted after Step 4
- Only `db/metadata.json` is needed for the app to run
- Backup of old metadata kept automatically
- Pipeline is idempotent (can run multiple times safely)
- All timestamps logged in output

---

## 🚨 IMPORTANT REMINDERS

1. **GitHub Token Required**: Set `$env:GITHUB_TOKEN` before running Step 3
2. **Internet Connection**: Step 3 needs API access to ChatGPT
3. **Rate Limiting**: Pause 1 second between tutorial requests (built-in)
4. **Restart App**: New metadata won't load without app restart
5. **Backup**: Old metadata automatically backed up

---

## 📋 COMPLETION CHECKLIST

When all steps are done, check these boxes:

- [ ] GitHub token set in PowerShell
- [ ] Step 1 (extract): Completed successfully
- [ ] Step 2 (LLM index): Completed successfully
- [ ] Step 3 (transform): Completed successfully
- [ ] Step 4 (restart): App running with new metadata
- [ ] Test 1 (T1 rejects Dijkstra): ✓ Passed
- [ ] Test 2 (T7 accepts Kruskal): ✓ Passed
- [ ] Test 3 (T8 accepts Dijkstra): ✓ Passed

---

**Pipeline created:** 2026-07-11
**Status:** Ready for user execution
**Next action:** Run Step 1 after setting GitHub token

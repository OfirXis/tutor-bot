# 🎓 Tutor-Bot: Curriculum-Gated Hybrid RAG for Algorithm Courses

A production-ready AI tutoring system for algorithm courses with **curriculum-gated learning**. The bot answers **only from course material**, **only up to the week the student has reached**, with a professional UI, bilingual support (English + Hebrew), and advanced retrieval-augmented generation.

**Status**: ✅ Production Ready | **Tests**: 246 passing | **Scope Accuracy**: 98%

### Key Improvements (Latest Session)

✅ **Fixed ChromaDB Database** - Resolved vector database corruption (v1.5.9)  
✅ **Enhanced Sidebar UI** - Model/tutorial selectors now clearly visible with professional styling  
✅ **Improved Bilingual LaTeX** - Math equations stay English/LTR even in Hebrew mode  
✅ **Added Loading Animations** - Smooth pulse, fadeIn, and spin effects  
✅ **Verified Scope Gating** - System correctly rejects out-of-curriculum questions  
✅ **Cleaned Curriculum** - Renamed bad topic names (e.g., "pursuit-evasion game")

---

## Why This Design

The previous version built separate Chroma DBs but never queried them. This production rebuild makes retrieval real and enforces curriculum at the *retrieval layer*:

| Problem before | Now |
|---|---|
| No retrieval at question time | Every question retrieves top-k passages from the index |
| 8 separate Chroma DBs | **One collection**, each chunk tagged `tutorial: N` |
| Curriculum enforced only by prompt | **Two deterministic gates**: retrieval filter `tutorial <= week` + scope check that rejects questions matching future material better than current week |
| 1000-char blind chunks | **Header-aware markdown chunks** with breadcrumbs (e.g., "Tutorial 4 › Worked Examples › Rod Cutting") |
| all-MiniLM-L6-v2 embeddings | **bge-small-en-v1.5** (benchmark winner), BM25 + cross-encoder reranking available |
| No evaluation | 246 test suite + golden QA benchmark + production verification |

**Measured Performance**: Hit@1 0.97, MRR 0.967, 35ms/query

---

## 🆕 Session Improvements (Latest)

### Issue 1: ChromaDB Database Corruption ✅
**Problem**: Vector database corrupted with KeyError on index path  
**Root Cause**: Version mismatch in chromadb dependency  
**Solution**: Downgraded chromadb to v1.5.9 (stable, fully compatible)  
**Verification**: Database rebuilt with 203 chunks, all tests passing

**Commands used**:
```bash
# Deleted corrupted database
rm -r db/index

# Downgraded chromadb
pip install --force-reinstall chromadb==1.5.9

# Rebuilt index
python build_index.py

# Verified with tests
pytest tests -q
```

### Issue 2: Sidebar Controls Not Visible ✅
**Problem**: Model/tutorial selectors weren't showing in web UI  
**Root Cause**: CSS visibility and layout issues  
**Solution**: 
- Enhanced sidebar section headers (uppercase, proper spacing)
- Improved radio button styling (segmented control appearance)
- Better hover states and visual feedback
- Updated selectbox styling with accent color borders

**Result**: All controls now clearly visible with professional styling

### Issue 3: LaTeX Rendering in Hebrew Mode ✅
**Problem**: Math equations weren't properly isolated in RTL (Hebrew) context  
**Root Cause**: `unicode-bidi: isolate` not strong enough for bidirectional text  
**Solution**: 
- Changed to `unicode-bidi: plaintext` (stronger isolation)
- Added explicit `text-align: left` to all KaTeX classes
- Applied to `.katex`, `.katex-display`, `.katex-inline`
- Enhanced RTL container selectors to prevent parent direction takeover

**Result**: Math equations stay English/LTR even when viewing Hebrew content

### Issue 4: No Feedback for Out-of-Scope Questions ✅
**Problem**: System was answering questions about material not yet covered  
**Root Cause**: Need clearer user feedback on scope rejection  
**Solution**: Verified existing scope-gating is working properly with message:
```
🔒 This material is more advanced than your current course week (week 1). 
You'll learn it later in the course, in week 5. For now, I can help with 
topics covered so far.
```

### Issue 5: Bad Curriculum Topic Names ✅
**Problem**: Topic stored as "Rami and Dina pursuit game" (unprofessional)  
**Root Cause**: Poor extraction from Hebrew source material  
**Solution**: Renamed to professional algorithm name "Pursuit-Evasion Game" with aliases

### Additional Enhancements 🎨
- **Professional Loading Animations**: Smooth pulse, fadeIn, spin effects
- **Button Styling**: Enhanced hover states with accent color and elevation
- **Radio Buttons**: Segmented control appearance with flex layout
- **Selectboxes**: Improved borders and hover feedback
- **Status Pills**: Animation on appearance with pulsing indicator dot

---

## Architecture

```
material/english/tutorial_*.txt  (clean markdown course notes)
        │  build_index.py
        ▼
┌─────────────────────────────────────────────┐
│ header-aware chunker (breadcrumb + section) │
│   → Chroma "course" collection (dense)      │
│   → chunks.jsonl (BM25 corpus)              │
└──────────────────┬──────────────────────────┘
                   │ query + filter tutorial ≤ week      ← curriculum gate
                   ▼
   dense (bge-small) ─┐
   BM25 ──────────────┼─ RRF fusion ─ (optional cross-encoder rerank)
                      ▼
        top-k passages + topic whitelist
                      ▼
        system prompt (tutor / Socratic homework)
                      ▼
   LLM  =  Ollama │ GitHub Models │ OpenAI │ any OpenAI-compatible
                      ▼
        scope-checked answer + cited sources (Streamlit UI)
```

## Course-week restriction

Select the current week in the sidebar (new chats default to week 1). Learning and
homework both use the same topic schedule, based on the English tutorial notes.
Explicit topic names and common Hebrew aliases are checked alongside semantic
similarity to future material. Mixed questions requesting a future topic are refused.

Answers are buffered and checked before display, so detected future material is
replaced with a refusal. Rejected exchanges do not enter model history, and changing
the week clears the conversation. If scope checking fails, no answer is shown.
The prompts also prohibit filling gaps with general knowledge. Topic names, aliases, prerequisites, introduction weeks, and localized tutorial titles live in
`db/curriculum.json`; update this shared schedule when the syllabus changes. Semantic
checks are heuristic, so unfamiliar paraphrases can still need additional coverage.

## Quickstart

Prerequisites: Python 3.11+ and [Ollama](https://ollama.com) (for the free local default).

The cross-platform launcher creates `.venv`, installs requirements, builds the retrieval
index when needed, and starts Streamlit.

### Linux / macOS

```bash
git clone https://github.com/steinergad/tutor-bot.git
cd tutor-bot
ollama pull llama3.2:3b
./run.sh
```

If the executable bit was not preserved when copying the project, use `sh run.sh` or
`python3 run.py`.

### Windows PowerShell

```powershell
git clone https://github.com/steinergad/tutor-bot.git
cd tutor-bot
ollama pull llama3.2:3b
.\run.ps1
```

If PowerShell blocks local scripts, use `python run.py` instead. The Python launcher works
on Linux, macOS, and Windows. To prepare everything without starting the app, pass
`--setup-only`.

Optionally copy `.env.example` to `.env` before launching to customize the provider and
model; the local Ollama defaults work without an `.env` file.

Open http://localhost:8501, pick the week, ask questions.

## Evidence and question handling

The tutor preserves the displayed question and adds a small term-cleanup step before
retrieval, after Hebrew translation when needed. The selected tutor model (local
Ollama by default) can approve curriculum-based spelling corrections and abbreviation
expansions: `devide and conqer` → `divide and conquer`, `dc`/`d&c` → `Divide and conquer`,
and `dijsktra` → `dijkstra`. It selects candidate edits, never writes a replacement
question. Very short abbreviations need recognizable course context; `DC voltage`
and `Washington DC` are left alone.

Only approved term spans change. Exclusions, problem numbers, and formatted code/math
are preserved. Retrieval, scope checking and evidence filtering use the interpretation;
the answer model receives both the original question and the interpretation. Corrected
future topics still trigger the week limit. No candidates means no extra model call;
failed or invalid cleanup leaves the question unchanged. Unknown or uncertain wording
may remain uncorrected. Bare references such as "Why does that work?" still ask for
clarification, and chat history is never used to invent a new question.

`prepare_retrieval(..., normalization_llm=llm)` enables this step. The offline evaluation
omits the model and measures the original retrieval path; normalization has separate
regression tests. This is English course-term cleanup, not general spellchecking or
a change to the Hebrew translation provider.

Dense retrieval now reports actual cosine similarity, instead of scores derived
from result positions. Before generation, passages must pass both the similarity
floor and a content-word overlap check. This is a relevance heuristic, not a proof
that every answer claim follows from a source. Insufficient evidence produces a
different message from the later-week refusal. Unknown homework numbers ask the
student to choose a real problem.

A request such as "Explain BFS without Dijkstra" excludes a method instead of
requesting it. Explicit exclusions are recognized in English and Hebrew. The
internal scope comparison omits excluded names so they do not dominate similarity;
term cleanup preserves those exclusions in the interpreted question. A
subsequent request to explain a future algorithm still triggers the week limit.

Homework `problem_topics` entries reference concept IDs from `db/curriculum.json`.
The selected assignment's `week` is the cumulative course boundary: all topics from
weeks 1 through that week are available, not just the topics listed for the problem.
Problem topics guide retrieval; they do not replace that cumulative boundary.
Standalone prerequisite questions (for example, Dijkstra while on Homework 5)
use the regular teaching prompt; a selected problem uses the homework guidance prompt.
For a selected problem, retrieval attaches its concepts and exact PDF statement.
If that query finds no supporting lecture passages, it also searches the mapped
prerequisites within the same week limit. The PDF statement itself is valid evidence
for explaining the task and asking a useful first-step question.

Requests to see the homework or a specific problem's wording display the actual
extracted statements, with their original numbering and assignment citations. They
do not depend on lecture similarity or a model reconstructing the PDF. Formula
extraction can be imperfect; the downloadable PDF remains the reference.
"First question" and "question two" are recognized. Once a problem is explicitly
selected, follow-ups such as "What next?" retain it; changing assignments or clearing
the chat resets that selection. Displayed PDF statements are summarized in model history
to avoid repeatedly filling its context window with the entire assignment. The tutor explains the task directly and guides
solutions step by step. An uncited homework answer gets one checked retry before
being withheld; source and week checks still apply.

`tools/extract_curriculum.py` reads the shared schedule, including week 9, instead
of maintaining a second hard-coded syllabus. It extracts all PDF pages into
`material/curriculum_review`; `--generate` optionally drafts source-grounded notes
using the configured tutor model. Review those drafts before replacing runtime
notes in `material/english` and running `python build_index.py`. Existing runtime
notes are not automatically regenerated by this tool.

Answers must use supplied `(Source N)` or `(Assignment N)` identifiers; invalid or
missing references are withheld. Hebrew `(מקור N)` and `(מטלה N)` references are
also validated. Reference validation does not establish mathematical correctness
or claim-level entailment. Dense retrieval remains the default; this update adds
no reranking stage; translation providers can now be selected independently.

`EVIDENCE_MIN_SIMILARITY=0.60` is the current relevance floor for the existing BGE
embedding model. Re-evaluate it when changing embeddings or course content. A
higher floor can reject legitimate paraphrases; it is not a confidence percentage.

Run the passage-level regression evaluation without generation or translation APIs:

```bash
.venv/bin/python evaluate_rag.py
```

See `RAG_EVALUATION.md` for supporting-passage recall, unnecessary abstentions,
future-topic refusals, latency, and unresolved misses. Unlike the old tutorial-level
benchmark, this uses specific reviewed passage IDs. The Hebrew cases use fixed
reference translations, and homework cases include a manual answer-review rubric.
The offline evaluation does not measure live LLM correctness or solution leakage.

## Tutorial 9 and homework PDFs

Tutorial 9 is based on `material/lectures/algo-maxflow-9-3.pdf`. The English notes in
`material/english/tutorial_9.txt` include source-page references. Tutorial 6 also
includes graph traversal from `Tutorial algo 6.pdf`, needed for Homework 3.

Homework mode reads `db/homework.json` for the assignment's course-week limit and
its `problem_pdf` path inside `material/Homework`. The actual PDF supplies complete
problem statements and page references. Ask, for example, "Give me a hint for
problem 3"; only the selected assignment's statements go into the tutoring prompt.
The original PDF can be downloaded from the sidebar. Homework PDFs are kept out
of the general course index, and the tutor continues to give hints rather than
complete solutions.

Assignment numbers are not course-week numbers. These limits are inferred from
the supplied PDFs and tutorial topics; edit `week` in `db/homework.json` if the
instructor's schedule differs:

| Assignment | PDF | Material through tutorial |
| --- | --- | --- |
| HW1 | HW1.pdf | 3 |
| HW2 | HW2_algo.pdf | 5 |
| HW3 | HW3_ALGO.pdf | 6 |
| HW4 | HW4_ALGO.pdf | 8 |
| HW5 | HW5_ALGO.pdf | 9 |

To refresh the extracted text and problem counts in the JSON after updating PDFs:

```bash
.venv/bin/python tools/extract_homework.py
```

The extractor preserves configured week limits. The app also refreshes PDF content
when a mapped file changes. Changing an assignment or its PDF clears chat history.
The launcher rebuilds the course index when tutorial notes change; if you start
Streamlit directly, run `python build_index.py` after editing course notes.

## Hebrew support

Select **עברית** from the language control in the sidebar for Hebrew labels,
right-to-left input, and localized course titles. Hebrew questions are detected
automatically even when the interface remains in English.

The retrieval index stays in English: Hebrew questions are translated before
retrieval, and answers are translated back while code and math are preserved
verbatim. The student sees only the Hebrew response; English stays inside retrieval
and model history. The tutor and translator can use completely different models.
Select the translation provider and local model name under **Hebrew / עברית** in
the sidebar, or configure `.env`:

```dotenv
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=dictalm-translator
TRANSLATION_OLLAMA_BASE_URL=http://localhost:11434
TRANSLATION_NUM_CTX=4096
```

The local model must already be installed/imported in Ollama under that name.
`dictalm-translator` is an example local alias, not a built-in downloadable tag.
Explicit local selection does not silently switch to OpenAI or the tutoring model
on failure. `auto` preserves the previous behavior: OpenAI when a key exists,
otherwise the selected tutor. `tutor` explicitly shares the tutor; `openai` uses
`TRANSLATION_MODEL` and requires a key. Set `UI_LANGUAGE=he` for Hebrew UI labels.

Candidate to test on a 4 GB GPU: [DictaLM 3.0 1.7B Instruct](https://huggingface.co/dicta-il/DictaLM-3.0-1.7B-Instruct),
preferably quantized. Its bilingual training makes it a plausible translator;
translation quality for algorithms must still be checked. Larger DictaLM variants
need substantially more memory or CPU offloading. [Intel Hebrew Math Tutor v1](https://huggingface.co/Intel/hebrew-math-tutor-v1)
is a 4B thinking model specialized for Hebrew math answers, rather than a dedicated
translation model. Use it as a tutoring experiment before choosing it for literal
translation. No new Hebrew model has been downloaded or quality-benchmarked here.
Two local models may compete for GPU memory and need to be loaded sequentially.

## Swapping the LLM (no code changes)

Set in `.env` (or the sidebar):

| Provider | `.env` | Cost |
|---|---|---|
| **Ollama** (default) | `LLM_PROVIDER=ollama`, `OLLAMA_LLM_MODEL=llama3.2:3b` | free, local |
| **GitHub Models** | `LLM_PROVIDER=github`, `GITHUB_TOKEN=…` | free tier — **being retired by GitHub (410 brownouts)** |
| **OpenAI** | `LLM_PROVIDER=openai`, `OPENAI_API_KEY=…` | paid (gpt-4o-mini ≈ $0.15/M in) |
| **Anything OpenAI-compatible** (LM Studio, vLLM, Groq, OpenRouter) | `LLM_PROVIDER=compatible`, `LLM_BASE_URL=…`, `LLM_MODEL=…` | varies |

Local model guidance for this machine (RTX 5070 Laptop, 4 GB VRAM): 3B models
(`llama3.2:3b`, `qwen2.5:3b`, `phi4-mini`) fit fully in VRAM and stream fast; 7B (`mistral`)
partially offloads to RAM and is noticeably slower. See [BENCHMARK_LLM.md](BENCHMARK_LLM.md)
for the full 5-model local comparison (+ cloud status).

## Benchmarks & tests

```text
python benchmark_embeddings.py        # embedding models × retrieval modes → BENCHMARK_RESULTS.md
python benchmark_llm.py --models llama3.2:3b phi4-mini github:openai/gpt-4o-mini   # tutor quality/speed → BENCHMARK_LLM.md
pytest tests -v                        # chunker, RRF, prompts, curriculum gate
python rag_engine.py "why does dijkstra fail with negative weights" --week 8   # CLI retrieval debug
```

The golden set lives in [eval/golden_qa.json](eval/golden_qa.json) — extend it as the
course grows; a *hit* means a retrieved chunk comes from the tutorial containing the answer.

## Project layout

```
app.py                   Streamlit chat UI (Learn + Homework modes)
rag_engine.py            chunking · hybrid retrieval · curriculum gate · LLM factory · prompts
build_index.py           (re)build the course index
benchmark_embeddings.py  retrieval benchmark  → BENCHMARK_RESULTS.md
benchmark_llm.py         LLM tutor benchmark  → BENCHMARK_LLM.md
eval/golden_qa.json      golden retrieval QA set
tests/test_rag.py        pytest suite
db/index/                Chroma collection      db/chunks.jsonl  BM25 corpus
db/curriculum.json       authoritative course topics, aliases, prerequisites, titles and source PDFs
db/metadata.json         compatibility export; runtime reads curriculum.json
db/homework.json         homework PDF mapping, course-week limits, extracted statements
homework_material.py     PDF extraction and selected-assignment context
material/english/        course notes (markdown, source of truth)
tools/                   one-shot data-prep scripts (PDF → material/, homework extraction)
SUMMARY.md               project summary — what changed, why, and the benchmark results
```

## Adding material

1. Drop `tutorial_10.txt` (markdown with `#`/`##`/`###` headers) into material/english/.
2. Add the tutorial, topic IDs, aliases, and prerequisite IDs to `db/curriculum.json`.
3. Run `python build_index.py` (or use the launcher, which detects changed notes).

### Installing local Hebrew translation models

Model weights are downloaded by Ollama, not by `pip` or `requirements.txt`.
Install or update [Ollama](https://ollama.com/download), start the Ollama desktop
app, and open a new PowerShell terminal. Verify it is running:

```powershell
ollama --version
ollama list
```

If the terminal cannot find `ollama`, reopen it after installation. If the server
is unavailable, start the Ollama app; on systems without its background service,
run `ollama serve` in a separate terminal. Run downloads on the machine hosting
Ollama (the default app connection is `http://localhost:11434`).

| Translation model | Parameters | Quantization | Weight download, approximately |
| --- | --- | --- | --- |
| TranslateGemma | 4 billion | Q4_K_M | 3.3 GB |
| DictaLM 3.0 Instruct | 1.7 billion | Q4_K_M | 1.11 GB |
| DictaLM 3.0 Nemotron Instruct | 12 billion | Q4_K_M | 7.49 GB |

Sizes describe weight files, not total GPU memory requirements. The 1.7B preset
uses a community conversion; the 12B preset uses DICTA's GGUF release. See the
[1.7B repository](https://huggingface.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF)
and [12B repository](https://huggingface.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF).

Download the lighter dedicated translator first:

```powershell
ollama pull translategemma:4b
```

The older DictaLM 1.7B experiment can be installed with
`ollama pull hf.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF:Q4_K_M`.

Download the larger translator to compare them:

```powershell
ollama pull hf.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF:Q4_K_M
ollama list
```

Keep the exact model names, including `hf.co/` and `:Q4_K_M`, so they match the
app presets. The same download commands work on Linux/macOS.

From the project directory, launch the app:

```powershell
.\run.ps1
```

Open **Hebrew / עברית** in the sidebar, choose **Ollama** as the translation
provider, and select **TranslateGemma — 4B parameters — Q4**,
**DictaLM 3.0 Instruct — 1.7B parameters — Q4**, or
**DictaLM 3.0 Nemotron Instruct — 12B parameters — Q4** under **Local translation
model**. Keep your answering model selected separately under **Model**.

To make a translator the startup default, add these settings to `.env` without
replacing your existing tutor or API settings:

```dotenv
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=hf.co/Ibrerhim/DictaLM-3.0-1.7B-Instruct-GGUF:Q4_K_M
TRANSLATION_OLLAMA_BASE_URL=http://localhost:11434
TRANSLATION_NUM_CTX=4096
```

For the 12B default, replace just the model setting:

```dotenv
TRANSLATION_OLLAMA_MODEL=hf.co/dicta-il/DictaLM-3.0-Nemotron-12B-Instruct-GGUF:Q4_K_M
```

Restart the app after changing `.env`. Test a Hebrew question about an allowed
topic, for example `מה זה דייקסטרה?` at week 9. Compare both translators for
meaning, algorithm names, exclusions such as “without Dijkstra,” formulas, and
source references. An English question should still use the tutor directly.
See the local translation smoke checks below; these are small samples, not a complete quality benchmark.

With 16 GB VRAM, start with TranslateGemma 4B and a small answering model.
Context and both models need additional memory; fitting both simultaneously is
not guaranteed. `ollama ps` shows currently loaded models. You can stop an unused
model with `ollama stop MODEL_NAME`, or reduce `TRANSLATION_NUM_CTX` if necessary.

If a download fails, update Ollama, verify the exact model name, and check access
to Hugging Face. If the app still labels a freshly downloaded model as missing,
wait 30 seconds and interact again (installed-model discovery is cached), or
restart the app. A “model not found” error means the selected name is not installed
on the Ollama server the app connects to. Do not use the example alias
`dictalm-translator` unless you have explicitly created that alias.

### Install Intel Hebrew Math Tutor and TranslateGemma 4B, step by step

The models have different roles:

| Model | Parameters | Select it under |
| --- | --- | --- |
| [Intel Hebrew Math Tutor v1](https://huggingface.co/Intel/hebrew-math-tutor-v1) | About 4B | **Provider → Ollama → Model** (answering) |
| [TranslateGemma](https://ollama.com/library/translategemma:4b) | 4B model family | **Hebrew / עברית → Ollama → Local translation model** |

The Intel Ollama preset uses a [community GGUF conversion](https://huggingface.co/mradermacher/hebrew-math-tutor-v1-GGUF)
of Intel's model. TranslateGemma downloads about 3.3 GB. The Intel model is an
optional answering experiment; selecting it still uses the app's normal
Hebrew → English → tutor → Hebrew pipeline.

1. Start the Ollama application/server. Open a terminal **in this project's
   directory**, where `run.py` and `tools/` are located. Use the terminal on the
   machine whose Ollama server the app connects to.
2. If `ollama` is not recognized, use the Python helper below. Ollama must be
   running, but its command does not need to be on PATH. The two install commands
   are independent; run the one for each model you want.

**Linux / WSL — including a terminal whose project path starts with `/home/Asaf`:**

```bash
.venv/bin/python tools/install_translation_models.py --model intel
.venv/bin/python tools/install_translation_models.py --model 4b
.venv/bin/python tools/install_translation_models.py --list
```

**Windows PowerShell:**

```powershell
.\.venv\Scripts\python.exe tools/install_translation_models.py --model intel
.\.venv\Scripts\python.exe tools/install_translation_models.py --model 4b
.\.venv\Scripts\python.exe tools/install_translation_models.py --list
```

If the virtual-environment Python does not exist yet, run `python3 run.py
--setup-only` on Linux/WSL or `py -3 run.py --setup-only` in Windows PowerShell,
then retry. If using another Python environment with the project dependencies,
you can use `python tools/install_translation_models.py ...` instead.

If `ollama` works in your terminal, these are the equivalent downloads on either
platform:

```bash
ollama pull hf.co/mradermacher/hebrew-math-tutor-v1-GGUF:Q4_K_M
ollama pull translategemma:4b
ollama list
```

3. Wait for `success` / `Installed` before selecting the model. Running a pull
   again reuses already-downloaded layers. The helper's `--model all` downloads
   only translation presets; Intel requires the explicit `--model intel` option.
4. Restart the app: `./run.sh` on Linux/WSL or `.\run.ps1` on Windows.
5. To test Intel, set **Provider = Ollama** and **Model = Intel Hebrew Math Tutor
   v1 — 4B parameters — Q4**. Under **Hebrew / עברית**, set **Translation provider
   = Ollama** and **Local translation model = TranslateGemma — 4B parameters — Q4**.
6. Choose week 9 and try `What is dynamic programming?`, then `מה זה תכנות דינמי?`.
   This checks the answering model first, then the full Hebrew pipeline. Intel
   is a reasoning model and may take longer than a lightweight chat model.

For persistent startup selections, edit just these keys in `.env`, keeping your
other settings:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_LLM_MODEL=hf.co/mradermacher/hebrew-math-tutor-v1-GGUF:Q4_K_M
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=translategemma:4b
```

If a model is missing from the dropdown, wait 30 seconds for the installed-model
cache or restart the app. The model must be installed on the same Ollama server
used by the corresponding selector. The helper uses `OLLAMA_BASE_URL` for Intel
and `TRANSLATION_OLLAMA_BASE_URL` (falling back to `OLLAMA_BASE_URL`) for translation
models. Override either with `--url http://HOST:11434`. With separate servers,
use `--model intel --list` to check the answering server and `--list` to check the
translation server. A connection error means the server must be started or its
URL corrected; installing a Python package will not download these model weights.

### Hebrew testing presets

The local translation selector includes DictaLM 3.0 1.7B Instruct and DictaLM 3.0
Nemotron 12B Instruct. The Ollama tutor selector includes Intel Hebrew Math Tutor v1.
All three are Q4_K_M GGUF presets, listed under their intended roles. Each uninstalled selection shows its exact `ollama pull` command.
Run that command on the machine hosting Ollama, then select the model to test.
The 1.7B and Intel presets use community quantizations; the 12B uses DICTA's release.
These are selectable candidates, not downloaded or quality-validated models.
Translation still uses the separate Hebrew → English → tutor → Hebrew pipeline.

### English evidence handling

Presentation requests such as “teach me” and “to a beginner” are excluded from
content-word evidence checks. Recognized course names get one canonical-topic
retrieval retry when the original query finds no supporting evidence. That retry
still checks the original question's content words and the selected week. English
questions do not initialize a translation model. Uncited answers can get one
scope-checked citation retry in either mode; fabricated citation IDs are withheld.

### If `ollama` is not found

The app uses Ollama's HTTP API; its command-line executable is not required if
an Ollama server is already running. You can download the translation models
using the project's Python helper instead:

```powershell
python tools/install_translation_models.py --list
python tools/install_translation_models.py --model 1.7b
python tools/install_translation_models.py --model 12b
```

Use `py -3` instead of `python` if that is your Windows Python command, or
`python3` on Linux/macOS. `--model all` installs both. The helper reads `.env`
server settings; `--url http://YOUR_SERVER:11434` overrides them. Downloads are
stored on that Ollama server, not in this project's Python environment.

If no server is reachable, install/start Ollama first. On Windows, install it
from https://ollama.com/download/windows, then restart VS Code and its terminal.
The default executable is `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`; test it
in PowerShell with:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
```

If this works but `ollama --version` does not, the terminal's PATH is stale or
missing that install directory. Restart the terminal first. On Linux, follow
https://docs.ollama.com/linux for installation on the machine hosting Ollama.

Local translators translate complete sentences in bounded blocks, rather than
splitting sentences around formulas. Code and formulas use checked placeholders;
citation IDs are checked and their original text restored. Long homework answers
are split before they exceed the output budget. One repair attempt is allowed
per translation.
Simple Hebrew requests for a known course topic (such as `ספר לי על הפרד ומשול`)
use the curriculum's exact English topic name, preventing the translator from
changing the question to a different algorithm.

Hebrew chat messages use right-to-left direction and right alignment regardless
of the sidebar language. Code blocks and formulas retain left-to-right direction.

### Local translation speed and quality

Translation progress shows elapsed seconds and generated character counts.
Local translation disables model reasoning, uses a 4096-token context, limits
output to 768 tokens per block, and keeps the translator loaded for 10 minutes. A 45-second
network timeout and elapsed-time checks stop stalled generation. An answer that
hits its output limit is rejected rather than displayed as a partial translation.
Configure these values in `.env`, then restart the app:

```ini
TRANSLATION_NUM_CTX=4096
TRANSLATION_MAX_TOKENS=768
TRANSLATION_TIMEOUT_SECONDS=45
TRANSLATION_KEEP_ALIVE=10m
```

For the 12B model on a 16 GB GPU, run `ollama ps` while translating and check the
PROCESSOR column. CPU or mixed CPU/GPU execution can explain long delays. Close
other GPU applications and stop unused models with `ollama stop MODEL_NAME`.
Reducing `TRANSLATION_NUM_CTX` to 2048 can reduce memory pressure for short
answers. Increasing context or output limits consumes more memory or time.
The first request may take longer while weights load; progress begins when
Ollama sends output. Check the error details panel if translation fails.

The 1.7B model remains less reliable: structured output and course-term checks
reduce topic drift and reject visible corruption, but cannot guarantee faithful
translation. It translated a short divide-and-conquer sample correctly in local
testing; a sentence split around a formula still failed language validation.
Use the 12B translator for better fidelity. Rejected translations show an error
and its details instead of garbled text; the English answer is not substituted
for the requested Hebrew response.


### Relevant-week refusals and Hebrew translation recovery

Course shorthand such as `DP`, `dc`, and `D&C` is expanded in recognizable
algorithm questions before scope checks, homework clarification, and retrieval.
This does not depend on the answering model returning valid normalization JSON.
Code, formulas, and non-course meanings such as Washington DC remain untouched.
Example requests also retrieve a worked example from a relevant course source
when available. Week restrictions and evidence checks still apply.

Hebrew translations no longer require English course titles to remain English
when the curriculum lacks Hebrew aliases. Invalid nested JSON and changed source
citations are rejected. If both DictaLM presets are installed, selecting the 1.7B
translator shows **Retry failed translations with the installed 12B model**
(enabled by default). You can turn this off to test the smaller model alone.
The fallback uses the same Ollama translation server and downloads nothing.
Each model has its own translation timeout, so a fallback may add another wait.

These checks do not establish semantic translation accuracy. The small model can
still mistranslate technical prose, and even the larger model needs review for
mathematical homework. TranslateGemma 4B is the lighter dedicated option; compare
it with the 12B model for your questions and treat DictaLM 1.7B as experimental. Restart the app after updating to load these changes.


### Lighter dedicated translator: TranslateGemma 4B

[TranslateGemma 4B](https://ollama.com/library/translategemma:4b) is a dedicated
translation model with an approximately 3.3 GB Ollama download. Install it with:

```bash
python tools/install_translation_models.py --model 4b
```

Or, if the Ollama command is available:

```bash
ollama pull translategemma:4b
```

Restart the app, open **Hebrew / עברית**, select **Ollama** as the translation
provider, and choose **TranslateGemma — 4B parameters — Q4**. It is listed under
translation models, not the answering-model presets. To make it the startup
selection, set these values in `.env`:

```ini
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=translategemma:4b
```

The app uses [TranslateGemma's native single-user translation prompt](https://ollama.com/library/translategemma),
with explicit English/Hebrew language codes and plain-text output. This model
must not use the JSON instruction format used for the general chat translators.
The same timeout, block-size, formula, and citation checks still apply. The 12B
fallback checkbox remains specific to the small DictaLM preset; selecting
TranslateGemma tests TranslateGemma itself.


Local smoke check: TranslateGemma completed two Hebrew-to-English questions and
four English-to-Hebrew answers (flow, DP, a divide-and-conquer example, and
Homework 5 problem 4 guidance) without a fallback. Warm answer translation took
about 0.8–2.3 seconds, versus 1.7–4.6 seconds for DictaLM 12B on the same inputs.
Initial model loading took longer. These are local sample measurements, not a
speed or accuracy guarantee; Hebrew phrasing can still be awkward. The app
normalizes a few known literal translations to the course terminology and
restores translated citation labels when their IDs match. If citations drift, it
keeps the translated prose and appends the original references at the end of
the affected block instead of rejecting the translation.
Results: `eval/translategemma_4b_smoke.json`.


### Translation failed even though the model is installed

A translation error is not necessarily an installation error. The chat now
separates unavailable models, connection failures, timeouts, and output-validation
failures. The **Translation error / שגיאת תרגום** panel stays attached to the
message after a page rerun, so its underlying error remains available.

Hebrew wording is no longer rejected simply because it is absent from the short
curriculum alias list. English retrieval queries still retain explicit topic
checks, and translated answers still undergo language, citation, and corruption
checks. Standalone code and formulas are copied without a translation request.
If TranslateGemma drops inline formula placeholders, one bounded retry presents
the original notation. Its protected spans must match before the original math
is restored; altered equations are rejected. This does not automatically switch
to a larger model.

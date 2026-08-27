# 🎓 Course Tutor — Curriculum-Gated Hybrid RAG

A local-first tutoring bot for an algorithms course. It answers **only from the course
material**, **only up to the week the student has reached**, with a professional chat UI,
streaming answers, source citations, and a Socratic homework mode.

Everything runs free: local embeddings, local reranker, local LLM via Ollama — and the
LLM is **swappable** (GitHub Models, OpenAI, or any OpenAI-compatible server) by changing
one env var.

---

## Why this design (the rethink)

The previous version built one Chroma DB per tutorial **but never queried any of them** —
it pasted a static topic summary into the prompt. This rebuild makes retrieval real and
enforces the curriculum at the *retrieval* layer, not just by prompt-begging:

| Problem before | Now |
|---|---|
| No retrieval at question time | Every question retrieves top-k passages from the index |
| 8 separate Chroma DBs | **One collection**, each chunk tagged `tutorial: N` |
| Curriculum enforced only by prompt | **Metadata filter `tutorial <= week`** — future material is physically unreachable (0/26 leaks in the benchmark) |
| 1000-char blind chunks of PDF text | **Header-aware markdown chunks** with breadcrumbs (`Tutorial 4 › Worked Examples › Rod Cutting`) |
| all-MiniLM-L6-v2 embeddings | **bge-small-en-v1.5** (benchmark winner), BM25 + cross-encoder rerank available |
| No evaluation | Golden QA set + benchmark scripts + pytest suite |

Measured on the 30-question golden set (see [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md)):
**Hit@1 0.97, MRR 0.967, 35 ms/query** with dense bge-small — vs 0.93/0.950 for the old
embedding model.

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
        streamed answer + cited sources (Streamlit UI)
```

## Quickstart

```powershell
# 1. deps (once)
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. local model (free)
ollama pull llama3.2:3b

# 3. build the index (once, ~15 s)
python build_index.py

# 4. run
streamlit run app.py
```

Open http://localhost:8501, pick the week, ask questions.

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

```powershell
python benchmark_embeddings.py        # embedding models × retrieval modes → BENCHMARK_RESULTS.md
python benchmark_llm.py --models llama3.2:3b phi4-mini github:openai/gpt-4o-mini   # tutor quality/speed → BENCHMARK_LLM.md
pytest tests\ -v                      # 14 tests: chunker, RRF, prompts, curriculum gate
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
db/metadata.json         week topic whitelists  db/homework.json Socratic homework data
material/english/        course notes (markdown, source of truth)
tools/                   one-shot data-prep scripts (PDF → material/, homework extraction)
legacy/                  previous implementation (reference only)
SUMMARY.md               project summary — what changed, why, and the benchmark results
```

## Adding material

1. Drop `tutorial_9.txt` (markdown with `#`/`##`/`###` headers) into material/english/.
2. Add its entry (display name + topics) to db/metadata.json.
3. `python build_index.py` — done.

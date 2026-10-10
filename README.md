# 🎓 Course Tutor: a curriculum-gated tutor bot for an algorithms course

Course Tutor is a chat tutor for a university algorithms course. Students pick the
week they have reached and ask questions in English or Hebrew. The bot answers
**only from the course notes**, **only up to that week**, and cites the passages it
used. In homework mode it guides students through an assignment with hints instead
of handing out solutions.

It runs fully offline with a free local model (Ollama), or with a cloud model
through OpenRouter or OpenAI.

## What it does

- **Answers from the course material.** Every question retrieves passages from the
  course notes. The answer must cite them as `(Source N)`; answers citing passages
  that were not supplied are retried once, then withheld.
- **Respects the course week.** Material from later weeks is filtered out before
  retrieval, questions naming later topics are refused, and answers are checked
  again before they are shown. This does not depend on the model obeying a prompt.
- **Homework mode.** Reads the assignment PDF, shows the exact problem statements,
  and gives Socratic hints. A separate check rewrites or withholds replies that give
  away a full solution.
- **Follow-up questions.** "I don't understand" or "why?" continue the previous answer
  with the same sources.
- **Hebrew.** Hebrew questions are translated to English for retrieval, and the answer
  is translated back, with formulas, code and citations protected.
- **Swappable models.** Local Ollama, OpenRouter, OpenAI or any OpenAI-compatible
  server, chosen in `.env` or in the sidebar.

## How it works

```
course notes (material/english/tutorial_*.txt)
        │  build_index.py: header-aware chunks, each tagged with its week
        ▼
Chroma vector index (bge-small-en-v1.5) + BM25 corpus
        │
question ──► [Hebrew → English] ──► named-topic check (later week? refuse)
        │
        ▼
retrieve passages WHERE week ≤ selected week ──► relevance + scope checks
        │
        ▼
tutor or homework prompt ──► LLM (Ollama │ OpenRouter │ OpenAI │ compatible)
        │
        ▼
answer checks: later-week content, valid citations, solution leaks (homework)
        │
        ▼
[English → Hebrew] ──► Streamlit chat with cited sources
```

Design details: [docs/DESIGN.md](docs/DESIGN.md). Hebrew pipeline and local
translators: [docs/HEBREW.md](docs/HEBREW.md).

## Requirements

- **Python 3.11 or newer**
- **[Ollama](https://ollama.com/download)** for the free local model. It is not needed
  if you only use a cloud provider.
- **Hardware for local models:** 16 GB RAM. An NVIDIA GPU with 4 GB or more is
  strongly recommended; on CPU only, answers take tens of seconds. Cloud providers
  need no GPU.
- About 5 GB of disk space: Python packages, the embedding model and one 3B local model.

## Quick start

```bash
git clone https://github.com/OfirXis/tutor-bot.git
cd tutor-bot
cp .env.example .env          # Windows: copy .env.example .env
ollama pull llama3.2:3b       # skip if you use a cloud provider
python run.py                 # Windows alternative: .\run.ps1   Linux/macOS: ./run.sh
```

`run.py` creates a virtual environment in `.venv`, installs the requirements, builds
the search index on first run (a few minutes), and starts the app. Open
**http://localhost:8501**, choose a week in the sidebar and ask a question.

- Use `python run.py --setup-only` to install and build without starting the app.
- Streamlit asks for an email address on its very first run; press Enter to skip.
- The first answer after starting is slower while the model loads.

## Choosing a model

Set the provider in `.env`, or switch it in the sidebar under **Model**. Restart the
app after editing `.env`.

| Provider | `.env` settings | Cost | Notes |
|---|---|---|---|
| **Ollama** (default) | `LLM_PROVIDER=ollama`<br>`OLLAMA_LLM_MODEL=llama3.2:3b` | Free | Runs on your machine; no data leaves it |
| **OpenRouter** | `LLM_PROVIDER=openrouter`<br>`OPENROUTER_API_KEY=sk-or-…`<br>`OPENROUTER_MODEL=anthropic/claude-haiku-5.5` | Paid per token | One key gives access to many models |
| **OpenAI** | `LLM_PROVIDER=openai`<br>`OPENAI_API_KEY=sk-…`<br>`OPENAI_MODEL=gpt-4o-mini` | Paid per token | |
| **OpenAI-compatible** | `LLM_PROVIDER=compatible`<br>`LLM_BASE_URL=…` `LLM_MODEL=…` `LLM_API_KEY=…` | Varies | LM Studio, vLLM, Groq, … |
| GitHub Models | `LLM_PROVIDER=github`, `GITHUB_TOKEN=…` | Free tier | Being retired by GitHub (HTTP 410); not recommended |

The chosen model writes the answers and also runs the small background checks
(off-topic detection, question cleanup, homework solution-leak check).

**One cloud key for everything.** With OpenRouter, set both of these to send answers,
background checks and Hebrew translation through the same key:

```dotenv
LLM_PROVIDER=openrouter
TRANSLATION_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
```

`TRANSLATION_OPENROUTER_MODEL` picks a different model for translation only. In the
sidebar, OpenRouter offers common models plus **Custom** for any model ID listed at
[openrouter.ai/models](https://openrouter.ai/models).

### Model comparison

Measured with `benchmark_llm.py` on 7 course questions (weeks 1–8) and 3
later-week questions asked by a week-1 student. See the column definitions below
the table.

Run on 2026-10-10, NVIDIA RTX 4050 Laptop GPU (6 GB), local models only:

| Model | Type | Term coverage | Cited | Refusal (model only) | Avg. answer time | Cost |
|---|---|---|---|---|---|---|
| `qwen2.5:3b` ⭐ | local | 0.76 | **1.00** | 1.00 | 16.8 s* | free |
| `llama3.2:3b` | local | 0.76 | 0.71 | 1.00 | 4.2 s | free |

\* Includes one 100-second cold model load on the first question; its warm answers
took 1.5–4 s, the same range as llama3.2. Both 3B models cover the same share of
course terms and refuse later-week material, but qwen2.5 cited its sources correctly
every time, while llama3.2 missed or mis-cited 2 of 7. That means fewer retries and
withheld answers in the app. Larger local models (`llama3.1:8b`, `phi4-mini`) and
cloud models through OpenRouter can be added with the command below.

- **Term coverage:** share of the key course terms a grounded answer should mention.
- **Cited:** share of answers that cite only the supplied passages. The app enforces
  this, so a low score means more retries and withheld answers.
- **Refusal (model only):** how often the model itself refused later-week material.
  The app blocks these questions before the model sees them, so this column shows how
  far the model alone could be trusted, not what students experience.
- Latency includes loading each local model once; later answers are faster.

**Run the comparison yourself**, including cloud models:

```bash
python benchmark_llm.py --models llama3.2:3b llama3.1:8b \
    openrouter:anthropic/claude-haiku-5.5 openrouter:openai/gpt-4o-mini
```

Cloud models are billed per token; one full run costs roughly a cent or less per
model at the prices above, and the table includes the estimated cost per model.
Results are written to [BENCHMARK_LLM.md](BENCHMARK_LLM.md). Retrieval (embedding
model) benchmarks are in [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md).

## Hebrew support

Hebrew questions are detected automatically. The answer comes back in Hebrew,
citations appear as `(מקור N)`, and formulas and code keep left-to-right layout.
Choose the translator under **🌐 Hebrew / עברית** in the sidebar, or in `.env`:

| `TRANSLATION_PROVIDER` | Translator | Notes |
|---|---|---|
| `openrouter` | OpenRouter model | Best quality and speed; uses `OPENROUTER_API_KEY` |
| `openai` | OpenAI model (`TRANSLATION_MODEL`) | Uses `OPENAI_API_KEY` |
| `ollama` | Local translator, e.g. `translategemma:4b` | Free; see below |
| `tutor` | The answering model itself | Small local models translate Hebrew poorly |
| `auto` (default) | OpenAI if `OPENAI_API_KEY` is set, otherwise `tutor` | |

For a free local setup, use a dedicated translator:

```bash
ollama pull translategemma:4b
```

```dotenv
TRANSLATION_PROVIDER=ollama
TRANSLATION_OLLAMA_MODEL=translategemma:4b
TRANSLATION_TIMEOUT_SECONDS=120
```

With two local models (answering and translating), each Hebrew question takes about
a minute on a 6 GB GPU, because the models take turns in GPU memory. Setting
`OLLAMA_NUM_CTX=4096` helps them fit. A cloud translator answers in seconds. Full
guide: [docs/HEBREW.md](docs/HEBREW.md).

## Using the app

- **Learn mode:** pick the week you have reached, then ask about any topic up to it.
  Later topics get a 🔒 message saying which week covers them.
- **Homework mode:** pick an assignment. Ask "what does problem 2 say?", "give me a
  hint for problem 3", or "check my reasoning". The assignment PDF can be downloaded
  from the sidebar. Each assignment opens the material up to its course week:

  | Assignment | Material through week |
  |---|---|
  | HW1 | 3 |
  | HW2 | 5 |
  | HW3 | 6 |
  | HW4 | 8 |
  | HW5 | 9 |

- **Sources:** open **📚 sources** under an answer to see the passages it cited, with
  tutorial, section and PDF pages.
- Changing the week or assignment clears the conversation.

## Configuration reference

All settings live in `.env` (see [.env.example](.env.example)). The most useful ones:

| Setting | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama`, `openrouter`, `openai`, `compatible`, `github` |
| `OLLAMA_LLM_MODEL` | `llama3.2:3b` | Local answering model |
| `OLLAMA_NUM_CTX` | `8192` | Local context window; use `4096` to fit two models in a small GPU |
| `OPENROUTER_MODEL` | `anthropic/claude-haiku-5.5` | OpenRouter answering model |
| `TRANSLATION_PROVIDER` | `auto` | See [Hebrew support](#hebrew-support) |
| `TRANSLATION_TIMEOUT_SECONDS` | `45` | Translation time limit; raise for slow local models |
| `LLM_TEMPERATURE` | `0.2` | Answer randomness |
| `LLM_MAX_TOKENS` | `1200` | Maximum answer length |
| `RETRIEVAL_MODE` | `dense` | `dense`, `hybrid` or `hybrid+rerank` |
| `EVIDENCE_MIN_SIMILARITY` | `0.60` | Relevance floor for passages; re-tune if you change the embedding model |
| `EMBED_DEVICE` | `cpu` | Set to `cuda` to run the embedding model on a GPU (needs a CUDA build of PyTorch) |
| `UI_LANGUAGE` | `en` | `he` for Hebrew interface labels |

## Updating the course

- **Course notes:** `material/english/tutorial_N.txt` (Markdown with `#`/`##`/`###`
  headings). The launcher rebuilds the index when notes change; otherwise run
  `python build_index.py`.
- **Schedule:** `db/curriculum.json` lists each week's topics, aliases (including
  Hebrew spellings) and prerequisites. The week gate and topic checks read this file.
- **Homework:** `db/homework.json` maps each assignment to its PDF in
  `material/Homework`, its course week and its problems' topics. Refresh extracted
  text with `python tools/extract_homework.py`.
- **Whole course from PDFs:** `python build_course.py --all` drafts notes, topics and
  homework mappings from lecture PDFs with the configured model. Review the generated
  `db/curriculum.json` and `db/homework.json` before use: the automatic topic tagging
  can be wrong (for example, homework problems tagged with an unrelated topic, which
  moves the assignment to the wrong week).

## Testing

```bash
python -m pytest tests -q        # 258 tests, no model server or API key needed
python evaluate_rag.py           # offline retrieval/decision evaluation → RAG_EVALUATION.md
```

Current state: 257 of 258 tests pass. The failing test,
`test_actual_cosine_scores_and_safe_exclusion`, flags a real retrieval gap: for "find
a shortest path in an unweighted graph" at week 6, the main BFS passage is not among
the results. See [Known limitations](#known-limitations).

`evaluate_rag.py` decides correctly on 90 of 96 regression cases, with no later-week
material supplied and no missed refusals. Its "supporting passage" figures are not
meaningful at the moment: the cases were labeled against an earlier version of the
course notes, and the notes (and their passage IDs) were regenerated since. The
cases need relabeling before those figures can be trusted again.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Windows: *"An Application Control policy has blocked this file"*, or a cloud provider reports missing credentials although the key is set | Windows **Smart App Control** is blocking a library file. Turn it off in Windows Security → App & browser control → Smart App Control. On many Windows 11 versions it cannot be turned back on without resetting Windows. |
| `ollama` is not recognized | Restart the terminal after installing Ollama, or run it by full path (`%LOCALAPPDATA%\Programs\Ollama\ollama.exe` on Windows). |
| Hebrew answers time out with two local models | Set `OLLAMA_NUM_CTX=4096` and `TRANSLATION_TIMEOUT_SECONDS=120`, or use a cloud translator. Check `ollama ps`: the PROCESSOR column should say GPU. |
| Every answer is slow | The model is running on CPU or swapping. Use a smaller model, close other GPU programs, or use a cloud provider. |
| The sidebar is hidden | Click the **»** arrow in the top-left corner. |
| *"The question could not be translated"* | Open **Translation error** under the message for the reason; it separates missing models, timeouts and rejected translations. |
| App shows "knowledge base hasn't been built yet" | Run `python build_index.py`, or `python run.py`, which builds it automatically. |

## Known limitations

- **Small local models make mistakes.** A 3B model can confuse related algorithms
  (for example, describe DFS with BFS behavior) even with the right passage in front
  of it. Use a larger local model or a cloud model for better answers.
- **Retrieval is a similarity search.** Paraphrased questions occasionally miss the
  most relevant passage (see [Testing](#testing)).
- **Citations are checked, facts are not.** The app verifies that cited passages were
  supplied and come from allowed weeks; it does not prove each sentence follows from
  them.
- **Hebrew translation is not proofread.** Translations are checked for visible
  corruption, lost course terms and broken citations, but wording can still be
  awkward or slightly wrong.

## Privacy and keys

- Keep API keys in `.env`. It is excluded from git (`.gitignore`); never commit it.
- Keys typed into the sidebar live only in that browser session.
- With a cloud provider, questions and the retrieved course passages are sent to that
  provider. With Ollama, nothing leaves the machine.

## Project layout

```
app.py                  Streamlit chat UI (Learn and Homework modes)
rag_engine.py           Chunking, retrieval, week gate, answer checks, LLM and translator factories
curriculum.py           Course schedule, topic matching, later-week detection
translation_support.py  Translation validation helpers
homework_material.py    Homework PDF extraction and problem selection
query_normalization.py  Course-term cleanup and abbreviation expansion
run.py                  Setup and launcher (also run.sh / run.ps1)
build_index.py          Rebuild the search index
build_course.py         Generate notes, schedule and homework mappings from PDFs
benchmark_llm.py        Model comparison  → BENCHMARK_LLM.md
benchmark_embeddings.py Embedding/retrieval comparison → BENCHMARK_RESULTS.md
evaluate_rag.py         Offline decision/evidence evaluation → RAG_EVALUATION.md
db/                     curriculum.json, homework.json, search index (index/ is rebuilt locally)
material/               Course notes (english/), lecture PDFs (lectures/), homework PDFs (Homework/)
tests/                  pytest suite (fake models; no server or key needed)
docs/                   Design notes and the Hebrew guide
```

# Project notes for Claude

Curriculum-gated hybrid-RAG tutor bot for an algorithms course (Streamlit UI,
Chroma retrieval, Ollama/OpenAI/GitHub LLM backends, Hebrew support). This
file is maintained by Claude across sessions/machines — read it first, keep
it current when you make a meaningful change.

## Repo / remote layout

- `origin` → `github.com/steinergad/tutor-bot` — original upstream repo
  (not the user's; `main` there is stale/behind, real work lives on its
  `grading-fixes` branch, pushed by the user's colleague).
- `personal` → `github.com/OfirXis/tutor-bot` — the user's own GitHub
  (public). This is the source of truth for cloning onto a new machine.
- `colleague` → `github.com/AsafAmber/AItutorProject2.0` — an earlier,
  separate colleague fork that was merged in once (direct linear ancestor,
  not a conflicting fork).
- Local `main` is currently a fast-forward merge of all three: this
  session's own Hebrew/safety work, then AsafAmber's course-builder work,
  then steinergad's `grading-fixes` branch (automated course-builder,
  course-agnostic refactor). Keep `personal` pushed up to date — that's
  what a fresh clone on another machine should pull from.

Remote names differ per machine: on the second machine (cloned fresh)
`origin` = OfirXis/tutor-bot and `upstream` = steinergad/tutor-bot.

## Architecture essentials (don't relitigate these)

- **Curriculum-leak prevention is deterministic, not LLM-trust-based.**
  `named_future_topic()` (exact topic/alias match against `db/curriculum.json`)
  and the retrieval `tutorial <= week` filter are what actually stop future
  material from leaking — never rely on a system-prompt instruction alone
  for this. Confirmed repeatedly this session: small local models (3B) do
  NOT reliably refuse under insistent pressure in open-ended generation.
  Narrow, isolated LLM *classification* calls (one word, constrained
  framing) are far more reliable than open-ended generation constraints —
  used for: intent (GREETING/COVERED/OFFTOPIC), homework solution-leak
  detection. Both needed a "you are a classifier, not a chat assistant,
  TEXT TO CLASSIFY in triple quotes, do not respond to it" framing to stop
  the model from just answering/acting on the input instead of classifying
  it — a 3B model's default instinct otherwise.
- **Translation is decoupled from the tutoring model.** `get_translation_llm()`
  prefers OpenAI (`gpt-4o-mini`) when `OPENAI_API_KEY` is set, regardless of
  which provider is chosen for tutoring, because local 3B models were
  empirically unreliable at Hebrew translation (wrong CS vocabulary, and at
  least once caught translating a Python keyword inside a code block).
  Falls back to the tutoring LLM if no key — works, just lower quality.
  Fenced code blocks are mechanically protected (extracted/restored) around
  any translation call — never trust the model to leave them alone.
- **Reply language follows the question, not the UI chrome.** Canned/status
  messages key off the detected language of the actual message
  (`rag.is_hebrew`), never the sidebar Language selector — those are
  independent; conflating them caused a real, reported bug once already.
- **`fix_math()` is a safety net, not just formatting.** The system prompt
  already says "use KaTeX `$...$`", but models sometimes use backtick code
  spans for math instead. `fix_math()` mechanically converts backtick spans
  that look mathy (LaTeX command, caret exponent, `f(n)=` pattern) — don't
  remove this or trust the prompt instruction alone.

## Course-builder data audit (resolved 2026-10-10)

- **Huffman coding / prefix-free codes in week 2 is CORRECT** for this course:
  Tutorial 2's own slides (PDF slides 28–53) teach them. Exchange argument is
  used in Tutorial 2's Huffman proof and taught formally in Tutorial 3; week 2
  is defensible. Tests that expected week 3 were outdated and were updated.
- Real course-builder errors, fixed by hand in `db/` (a rebuild with
  `build_course.py` would reintroduce them; review its output):
  - Dynamic programming lacked the common Hebrew spelling "תכנות דינמי" (only
    "תכנון דינאמי"), so Hebrew DP questions bypassed the week gate. Added it,
    plus LCS / longest common subsequence.
  - HW1 problem 4 (rope merging, greedy) was tagged DP → HW1 is week 3, not 4.
  - HW2 (all DP, incl. an edit-distance-style shuffle problem) was tagged with
    greedy/intro topics → week 5, not 4.
  - HW5 problems 4 (bipartite matching) and 5 (min cut) were tagged DP.
- Still open: `test_actual_cosine_scores_and_safe_exclusion` fails because
  "shortest path in an unweighted graph" at week 6 doesn't retrieve the main
  BFS passage — a genuine retrieval-quality gap, deliberately left failing.
- `eval/rag_cases.json` passage IDs predate the Oct 7 notes regeneration, so
  `evaluate_rag.py`'s supporting-passage metrics are stale until relabeled.

## Providers

`LLM_PROVIDER` / `TRANSLATION_PROVIDER` support `openrouter` (one key for
answers, background classifiers and translation). The user pays for cloud
calls — never run OpenRouter/OpenAI requests (benchmarks, smoke tests)
without asking; run tests with `OPENROUTER_API_KEY` overridden to a dummy.

## Environment facts — re-verify on a new machine, don't assume

Second machine (2026-10-10): Windows 11, RTX 4050 Laptop 6 GB, 16 GB RAM.
Two local models (tutor + translategemma:4b) don't fit together in 6 GB;
`OLLAMA_NUM_CTX=4096` + `TRANSLATION_TIMEOUT_SECONDS=120` makes Hebrew work
(~1 min/question). Windows Smart App Control blocked tiktoken's DLL (breaks
every langchain_openai provider) until the user turned it off.


The original dev sandbox for this project (where the above was found) had
**no NVIDIA GPU** (confirmed via `Win32_VideoController`/`Get-PnpDevice` —
only an Intel Iris Xe iGPU) and ran Ollama on CPU only, which made local
inference slow (tens of seconds per call) and made system-wide RAM pressure
a real factor affecting responsiveness. **This is a per-machine fact, not a
project constant — check `nvidia-smi` / `Win32_VideoController` fresh on
whatever machine you're on before assuming CPU-only.** If a GPU is present,
local inference should be much faster and some of the "local 3B model is
unreliable under X" findings may need re-verification at higher sampling
confidence (they were true on CPU-only free-tier testing; haven't been
re-checked on GPU).

## Setup on a fresh machine

```powershell
git clone https://github.com/OfirXis/tutor-bot.git
cd tutor-bot
copy .env.example .env        # defaults: ollama provider, llama3.2:3b
# install Ollama from ollama.com, then: ollama pull llama3.2:3b
python run.py                 # creates venv, installs deps, builds index, launches
```
`db/curriculum.json` / `db/homework.json` / `db/metadata.json` are
committed (tracked); `db/index/` and `db/chunks.jsonl` are gitignored and
rebuilt locally by `run.py`/`build_index.py` automatically — this takes a
few minutes on first run.

## Testing

`pytest tests\ -q` — 236+ tests as of this writing. Run after any change
before considering it done. When stress-testing LLM-dependent behavior
(classifiers, translation, generation), test empirically against real
examples before trusting a prompt change — this session repeatedly found
that prompt wording that looks right still needed actual measurement (e.g.
the solution-leak classifier needed two prompt iterations before its
recall on real leaked examples was acceptable; always check recall on the
*dangerous* failure direction, not just overall accuracy).

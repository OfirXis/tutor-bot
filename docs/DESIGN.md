# Design notes: scope, evidence and homework

Detailed behavior of the curriculum gate, evidence checks and homework mode. See the [README](../README.md) for setup.

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

### English evidence handling

Presentation requests such as “teach me” and “to a beginner” are excluded from
content-word evidence checks. Recognized course names get one canonical-topic
retrieval retry when the original query finds no supporting evidence. That retry
still checks the original question's content words and the selected week. English
questions do not initialize a translation model. Uncited answers can get one
scope-checked citation retry in either mode; fabricated citation IDs are withheld.


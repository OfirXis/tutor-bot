# RAG evidence evaluation

96 regression cases; dense retrieval; similarity floor 0.6.
These are development/regression cases, not an independent held-out benchmark.
Hebrew retrieval uses fixed reference translations; no translation model or external API was called.
A supporting hit means a reviewed passage ID was retrieved, not merely the correct tutorial.

| Check | Result |
| --- | --- |
| Correct answer/refusal/clarification decision | 96/96 |
| Supporting passage among supplied evidence | 67/72 |
| Supporting-passage MRR | 0.809 |
| Unnecessary abstentions on answerable cases | 0/72 |
| Missed future-topic refusals | 0/10 |
| Future-week passages supplied | 0 |
| Median decision time (includes retrieval) | 45.8 ms |

## Remaining misses

- `course_30`: What's the fastest way to find shortest paths in a graph with no cycles? — expected answer, got answer; supporting passage found: False; retrieved: tutorial_8::000, tutorial_8::006, tutorial_8::003, tutorial_8::013.
- `hw_1_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_1::009, tutorial_1::010, tutorial_1::014, tutorial_1::005.
- `hw_1_p4`: Give me a hint for problem 4 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_3::013, tutorial_3::010, tutorial_3::011, tutorial_3::012.
- `hw_2_p3`: Give me a hint for problem 3 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_4::003, tutorial_4::005, tutorial_3::004, tutorial_4::007.
- `hw_4_p1`: Give me a hint for problem 1 — expected answer, got answer; supporting passage found: False; retrieved: tutorial_7::009, tutorial_7::008, tutorial_7::005, tutorial_7::006.

## Limits and answer review

This offline run does not invoke the optional model-assisted term normalization used
by the app. Spelling and abbreviation cleanup has separate regression tests; the
retrieval figures above do not measure its live model quality.

This run does not generate answers and cannot establish mathematical correctness, factual entailment, or whether a live tutor gives away homework solutions. Source-ID validation is checked separately by tests; valid citation IDs alone do not prove the associated claims.
Before a model change, review generated answers for: the exact original request, supported claims and citations, correct formulas, allowed concepts, and hints rather than full homework solutions. The homework cases include this rubric.
Similarity plus content overlap is a conservative heuristic and can reject unfamiliar paraphrases. The report records such abstentions rather than counting them as successes.


### Week 9 and Hebrew regression check

The shared retrieval path now expands context-appropriate DP/DC shorthand before
homework clarification and scope checks, without requiring LLM approval. Example
requests include a worked example from a relevant source when one is available.
Regression tests cover the reported flow, DP and DC requests in both tutorial and
Homework 5 modes, as well as the earlier-week refusal boundaries.

`eval/week9_translation_smoke.json` records seven local Ollama checks using
`llama3.2:3b`: three English tutorial questions and four Hebrew Homework 5
questions (flow, DP, a DC example, and guidance on problem 4). All retrieved
supporting material and returned answers. On the final translation check, all
four Hebrew answers needed the installed DictaLM 12B fallback after the 1.7B
model failed validation. Final translation times including fallback were about
2.5–5.8 seconds on this environment; these are warm local measurements, not a
hardware-independent latency guarantee.

The Hebrew answers were reviewed for the requested topic, worked-example values,
and the homework task. Some wording remains awkward. These smoke checks establish
that the reported paths return usable responses, not general translation fidelity
or mathematical correctness across the course. The 1.7B translator remains
experimental; the app exposes its installed-12B fallback as a visible checkbox.


### TranslateGemma 4B local comparison

`eval/translategemma_4b_smoke.json` compares six translation inputs using
TranslateGemma 4B Q4_K_M and DictaLM 12B Q4_K_M on local Ollama. The dedicated
4B adapter uses its native single-user prompt with explicit language direction
and plain-text output. All six final cases passed language, protected-content,
and citation validation without fallback. The four Hebrew answer translations
measured 0.779, 1.447, 2.264 and 1.760 seconds for 4B, versus 1.740, 2.940, 4.587
and 3.615 seconds for 12B. These are warm measurements; model loading and CPU
spillover can change latency substantially. Short questions and repeated prompts
may also benefit from prompt caching.

Manual review found understandable translations of the tested questions and
answers, with awkward Hebrew wording still present. Known literal variants of
“divide and conquer”, “merge sort”, “recurrence relation” and “check-in question”
are normalized only when the corresponding source phrase is present. These
samples do not establish general mathematical translation accuracy.


### Week 7 divide-and-conquer translation regression

The question `ספר לי על הפרד ומשול`, with tutorial 7 and TranslateGemma 4B,
exposed two output-validation problems: valid Hebrew wording outside the short
alias list and dropped formula placeholders. The app's error panel was also
lost on the immediate chat rerun. Regression coverage now exercises persistent
error details for both translation directions, unchanged-equation recovery, and
rejection of altered equations. The locally generated explanation was translated
with the app's dollar-delimited math formatting and passed source-ID and week
checks; the output is recorded in `eval/week7_translation_failure.json`.
This is one reproduced explanation, not a guarantee across model generations.

The same reproduction also found inconsistent citation parsing: translation
preserved `(Source 1 — Tutorial 2 — ... )`, but final validation accepted only
`(Source 1)`. Both now use the same parser, and nonexistent IDs are still
rejected. The final formatted explanation translated in about 2.3 seconds in
this local warm check.

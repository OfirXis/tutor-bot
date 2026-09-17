# Translation improvements and model comparison

This report compares the repository's saved translation results and explains the citation-recovery change. **The latest change keeps otherwise valid translated prose when citations change, disappear, or are added.** It repairs the references instead of rejecting the entire translation.

The model timings below come from existing local Ollama runs, not a fresh benchmark of the latest code. The latest citation behavior was checked with deterministic regression tests.

## What improved

| Area | Earlier behavior / problem | Current behavior | Practical effect |
|---|---|---|---|
| Changed citation IDs | A change such as `(Source 1)` → `(מקור 99)` raised `ValueError: Translator changed source citations`. | Remove recognized translated citations and append the original citations at the end of the affected block. | The user can read the translation; the invented source number is removed. |
| Missing, extra, or reordered citations | Citation sequence mismatch rejected the translation. | Restore the original block's reference sequence after its translated prose. If the original had no citations, remove invented recognized citations. | Citation drift alone no longer causes a retry or discards the answer. |
| Correct citations with Hebrew labels | Citation labels need normalization to the original source format. | Matching citations are restored in place, including original titles. | Normal translations retain their inline references. |
| Bare native-model citations | TranslateGemma may produce `במקור 2` instead of `(Source 2)`. | Recognize supported bare citation forms, then normalize or recover references. | Small punctuation differences are recoverable. |
| Math and code | Small translators can drop placeholders or alter notation. | Protect spans, restore original content, and allow one bounded repair attempt; native repair can show actual notation. | Original math/code is preserved when validation succeeds. Altered protected content can still fail. |
| Long answers | Fragmenting sentences around formulas can lose useful context. | Translate bounded prose blocks with compact markers; copy standalone protected content directly. | The translator sees more sentence context and avoids unnecessary calls for formula-only blocks. |
| Hebrew terminology | Requiring exact course aliases rejected some acceptable paraphrases. | Hebrew paraphrases are allowed; limited native-model terminology normalization remains. | More usable prose survives validation, although semantic accuracy is not guaranteed. |
| Error reporting | A translation failure could be confused with an unavailable model. | Distinguish output validation, timeout, connection, and missing-model failures; retain error details in chat. | Failures are easier to diagnose. |

The first two rows describe the latest fix. The other rows describe supporting improvements already present in the repository.

### Example of the latest fix

Original answer:

```text
A problem. (Source 1)
```

Translator output:

```text
בעיה. (מקור 99)
```

Previously, the app rejected the translation. Now it returns:

```text
בעיה.

(Source 1)
```

References move to the end of the **affected translation block**, not necessarily the end of the entire answer. This avoids guessing which translated sentence each original reference belongs to. It preserves the original reference list but loses precise inline placement in that block. Recovery handles forms recognized by the citation parser; it is not a general detector for every possible malformed reference.

## How the models handle translation

| Model / project preset | Translation path | Evidence in this repository | Effect of the latest fix |
|---|---|---|---|
| TranslateGemma 4B (`translategemma:4b`) | Native single-user translation prompt; plain-text output; terminology normalization and bare-citation handling. | Six saved matching-input translations returned output without fallback. Separate week-7 formula regression also passed. | Citation drift can be repaired locally without discarding the translated prose or calling a larger model. |
| DictaLM 3.0 Nemotron 12B, Q4_K_M | Instruction prompt with structured JSON output. | Six saved matching-input translations returned output; also recovered four Hebrew answers in the older fallback run. | Uses the same block-level citation recovery, avoiding citation-only retries. |
| DictaLM 3.0 Instruct 1.7B, Q4_K_M | Instruction prompt with structured JSON output. | The older week-9 evaluation reports that all four Hebrew answers needed the installed 12B fallback after validation failed. | Citation-only failures are now recoverable. There is no fresh run showing how many of those older failures this fixes; other validation failures remain possible. |
| Intel Hebrew Math Tutor v1 4B, Q4_K_M | Classified as a tutor preset, not a translation preset. | No comparable translation measurements in the cited artifacts. | No measured translation-quality or speed claim can be made. |

The optional automatic larger-model fallback is restricted to selecting DictaLM 1.7B with DictaLM 12B installed. TranslateGemma does not automatically switch to 12B. Citation recovery itself is application logic shared by the local translation path; it does not retrain or improve the models' underlying language ability.

## Saved matching-input timings

Source: [eval/translategemma_4b_smoke.json](eval/translategemma_4b_smoke.json). Times are seconds for individual recorded translations.

| Input | Direction | TranslateGemma 4B | DictaLM 12B |
|---|---|---:|---:|
| Help with question 4 and explain the first step | Hebrew → English | 0.149 | 2.549 |
| Calculate the flow value in a network | Hebrew → English | 0.090 | 0.278 |
| Flow explanation with formulas and a citation | English → Hebrew | 0.779 | 1.740 |
| Dynamic programming explanation | English → Hebrew | 1.447 | 2.940 |
| Merge Sort / divide-and-conquer worked example | English → Hebrew | 2.264 | 4.587 |
| Homework 5 question 4 guidance | English → Hebrew | 1.760 | 3.615 |
| **Mean of the four Hebrew answers** | **English → Hebrew** | **1.563** | **3.221** |

For those four answers, TranslateGemma's mean elapsed time was about **51.5% lower**, or **2.06× faster**. These are small-sample local measurements, not a general speed guarantee. The artifacts do not provide repeated trials, confidence intervals, or complete per-call hardware/load metadata. Initial loading can affect timings; the Hebrew-answer timings are described as warm in the existing project documentation.

The older [week-9 results](eval/week9_translation_smoke.json) include fallback and differently scoped timing fields. They should not be mixed into this direct timing table.

## Quality observations from the saved outputs

Both models preserved the main structure of the tested answers, but readable output does not imply perfect technical Hebrew.

- **Flow:** TranslateGemma used `קצה` for “edge,” whereas DictaLM 12B used the course-appropriate `קשת` in this sample. Both preserved the protected `$f$` and `$|f|$` notation.
- **Dynamic programming:** Both conveyed subproblems and reuse. TranslateGemma rendered time complexity as `המורכבות הזמנית`; DictaLM used `מורכבות הזמן`, but also produced the grammatical error `שני תכונות`.
- **Merge Sort:** Both retained the worked numeric sequence. TranslateGemma used `מיון מיזוג`; DictaLM mixed English `Merge Sort` with Hebrew and used the awkward phrase `היחסה הרקורסיבית` for recurrence relation.
- **Week-7 formula recovery:** The saved TranslateGemma reproduction passed in 2.292 seconds and retained the recurrence, yet still contained awkward Hebrew. Passing structural checks is not a semantic quality score.

These observations describe the stored outputs, which may precede some current normalization rules. There is no blinded quality ranking or broad mathematical-accuracy evaluation in these files.

## Verification of the latest change

Command:

```sh
.venv/bin/python -m pytest tests/test_hebrew.py -q
```

Result after the citation-recovery edit: **48 passed**.

Regression cases cover changed citation IDs, missing citations, extra citations, invented citations when none existed, reordered source/assignment references, and TranslateGemma-style bare citation drift. The suite also covers protected math/code, native and structured model paths, language validation, and bounded repair behavior.

These tests use model doubles. They establish the application's handling of specific outputs, not the frequency with which a real model produces them. No live-model rerun was performed for this report, and no measured before/after real-model success-rate increase is claimed.

## Remaining limits

The fix allows citation drift to recover; it does not make every translation failure nonblocking. Empty or corrupted output, malformed structured JSON, timeouts, token-limit truncation, and changed protected content can still fail. Citation-only recovery adds no model call, but its wall-clock benefit has not been separately benchmarked.

The recorded comparison supports TranslateGemma's lower latency on these inputs. DictaLM 12B offers some better terminology in individual examples, with errors of its own. The available 1.7B evidence shows validation reliability problems before the latest fix; a new matched-input run is needed to quantify its current behavior.

## Evidence and implementation

- [Direct model comparison data](eval/translategemma_4b_smoke.json)
- [Older week-9 fallback results](eval/week9_translation_smoke.json)
- [Passing week-7 reproduction](eval/week7_translation_failure.json) — despite its filename, its stored status is `passed`.
- [Existing evaluation notes](RAG_EVALUATION.md)
- [Translation implementation](rag_engine.py), [validation and terminology helpers](translation_support.py)
- [Model presets and fallback selection](local_models.py)
- [Translation regression tests](tests/test_hebrew.py)

# Benchmark — Tutor LLMs: Local (Ollama) vs Cloud

*Run 2026-10-10 on NVIDIA GeForce RTX 4050 Laptop GPU · 6141 MiB. 7 in-scope questions (weeks 1–8, with retrieved course context) + 3 out-of-scope questions (week-1 student asking later material). Term coverage = fraction of expected course key-terms present in the answer. Cited = fraction of answers citing only supplied passages (the app's own check). Refusal = fraction of out-of-scope questions the model refused on its own; the app additionally blocks them before generation. Cloud latency includes network. Cost = estimated USD for this whole run (OpenRouter list prices; local models are free).*

| Model | Type | Term coverage | Cited | Refusal (model only) | TTFT (s) | Total (s) | tok/s | Run cost |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | local | 0.76 | 0.71 | 1.00 | 2.6 | 4.2 | 29 | free |
| qwen2.5:3b **⭐** | local | 0.76 | 1.00 | 1.00 | 15.0 | 16.8 | 34 | free |

**Best overall:** `qwen2.5:3b`.

Latency includes one cold model load per local model (the first question); warm answers are faster. Reproduce with `python benchmark_llm.py --models llama3.2:3b qwen2.5:3b`.

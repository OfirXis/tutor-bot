# Benchmark — Tutor LLMs: Local (Ollama) vs Cheap Cloud (GitHub Models)

*6 in-scope questions (with retrieved context) + 3 out-of-scope questions (week-1 student asking future material). Term coverage = fraction of expected course key-terms present in the answer. Refusal rate = fraction of out-of-scope questions correctly refused. Local hardware: RTX 5070 Laptop 4 GB VRAM. Cloud latency includes network; GitHub Models free tier is rate-limited but $0.*

| Model | Type | Term coverage | Curriculum refusal | TTFT (s) | Total (s) | tok/s |
|---|---|---|---|---|---|---|
| llama3.2:3b **⭐** | local | 0.92 | 1.00 | 1.6 | 5.6 | 81 |
| qwen2.5:3b | local | 0.92 | 0.67 | 1.7 | 4.7 | 98 |
| gemma3:4b | local | 0.86 | 0.00 | 9.9 | 16.3 | 65 |
| phi4-mini | local | 0.83 | 1.00 | 3.6 | 5.4 | 82 |
| mistral:latest | local | 0.83 | 0.00 | 2.0 | 9.6 | 50 |

**Best overall:** `llama3.2:3b`.

## Cloud comparison status (GitHub Models)

`github:openai/gpt-4o-mini`, `github:openai/gpt-4.1-mini` and `github:openai/gpt-4.1-nano`
were attempted with a valid token but every request returned **HTTP 410
`github_models_retirement_brownout`** — GitHub is retiring the free Models API and the old
`models.inference.ai.azure.com` endpoint no longer resolves at all. The benchmark keeps
`github:<model>` support (`python benchmark_llm.py --models ... github:openai/gpt-4o-mini`),
so the cloud rows will populate automatically if run during a non-brownout window; otherwise
use `LLM_PROVIDER=openai` with an OpenAI key (gpt-4o-mini ≈ $0.15/M input tokens) for a
cheap-cloud data point.

## Observations

- **llama3.2:3b** is the clear winner: tied-best term coverage (0.92), the only 3B model
  with a **perfect 3/3 curriculum refusal**, TTFT 1.6 s, 81 tok/s — and it fits entirely
  in 4 GB VRAM.
- **phi4-mini** is the runner-up: also 3/3 refusals and fast (82 tok/s), slightly weaker
  grounding (0.83).
- **qwen2.5:3b** has the highest raw speed (98 tok/s) and top coverage but missed one
  refusal (answered the out-of-scope Huffman question).
- **gemma3:4b** and **mistral:latest** refused *nothing* (0/3) and are the slowest —
  both are poor fits for this tutoring setup.
- The refusal spread (0.00–1.00 across models) confirms that prompt-level curriculum
  enforcement is model-dependent and unreliable; the retrieval-layer gate
  (`tutorial <= week` filter, 0/26 leaks in BENCHMARK_RESULTS.md) remains the real
  safety mechanism — even a never-refusing model has no future material to quote.
- Latency numbers include one cold model load per model (visible as the first-question
  outlier, e.g. gemma3's 61 s first answer); warm-state figures are lower.
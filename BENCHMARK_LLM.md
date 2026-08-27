# Benchmark — Local LLMs as Tutor (Ollama)

*6 in-scope questions (with retrieved context) + 3 out-of-scope questions (week-1 student asking future material). Term coverage = fraction of expected course key-terms present in the answer. Refusal rate = fraction of out-of-scope questions correctly refused. Hardware: RTX 5070 Laptop 4 GB VRAM.*

| Model | Term coverage | Curriculum refusal | TTFT (s) | Total (s) | tok/s |
|---|---|---|---|---|---|
| llama3.2:3b **⭐** | 0.92 | 0.67 | 0.8 | 5.0 | 73 |
| qwen2.5:3b | 0.92 | 0.67 | 10.3 | 14.4 | 67 |
| mistral:latest | 0.83 | 0.33 | 5.2 | 13.9 | 38 |

**Recommended default:** `llama3.2:3b`.

## Observations

- **llama3.2:3b** is the clear winner on this hardware: best grounding, best refusal
  behaviour, and ~3× faster than mistral 7B (fits fully in 4 GB VRAM; mistral partially
  offloads to CPU RAM).
- qwen2.5:3b ties on quality but its TTFT mean is inflated by a one-off 60 s cold model
  load; warm it is comparable to llama3.2.
- **No small model refused the out-of-scope Huffman question** — prompt-level curriculum
  enforcement is unreliable on 3B–7B models. This is exactly why this system also gates at
  the retrieval layer (`tutorial <= week` filter, 0/26 leaks in BENCHMARK_RESULTS.md): even
  when the model fails to refuse, it has no future course material to quote from.
- Numbers include one cold start per model; re-run for steady-state figures.
- For noticeably better instruction-following while staying free, use GitHub Models
  (`gpt-4o-mini`) via `LLM_PROVIDER=github` — same prompts, no code changes.
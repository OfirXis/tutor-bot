# Benchmark — Embedding Models & Retrieval Modes

*Golden set: 30 student questions across 8 tutorials (mix of verbatim and paraphrased). Hit = retrieved chunk comes from the tutorial containing the answer. Chunks indexed: 111. CPU only.*

| Model | Mode | Hit@1 | Hit@3 | Hit@5 | MRR | Query (ms) | Build (s) |
|---|---|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | dense | 0.93 | 0.97 | 0.97 | 0.950 | 16 | 20.2 |
| all-MiniLM-L6-v2 | bm25 | 0.80 | 0.87 | 0.87 | 0.833 | 0 | 20.2 |
| all-MiniLM-L6-v2 | hybrid | 0.87 | 0.97 | 0.97 | 0.911 | 16 | 20.2 |
| all-MiniLM-L6-v2 | hybrid+rerank | 0.93 | 0.97 | 0.97 | 0.944 | 733 | 20.2 |
| bge-small-en-v1.5 | dense **⭐** | 0.97 | 0.97 | 0.97 | 0.967 | 35 | 13.0 |
| bge-small-en-v1.5 | bm25 | 0.80 | 0.87 | 0.87 | 0.833 | 1 | 13.0 |
| bge-small-en-v1.5 | hybrid | 0.90 | 0.93 | 0.97 | 0.919 | 40 | 13.0 |
| bge-small-en-v1.5 | hybrid+rerank | 0.93 | 0.97 | 0.97 | 0.944 | 868 | 13.0 |
| e5-small-v2 | dense | 0.97 | 0.97 | 0.97 | 0.967 | 26 | 18.5 |
| e5-small-v2 | bm25 | 0.80 | 0.87 | 0.87 | 0.833 | 0 | 18.5 |
| e5-small-v2 | hybrid | 0.90 | 0.93 | 1.00 | 0.926 | 31 | 18.5 |
| e5-small-v2 | hybrid+rerank | 0.93 | 0.97 | 0.97 | 0.944 | 891 | 18.5 |

## Curriculum-boundary leak check

Retrieval filtered to one week **below** each answer's tutorial: **0/26 leaks** (must be 0 — the metadata filter makes future material unreachable regardless of the LLM).

**Recommended default:** `bge-small-en-v1.5` with `dense` (MRR 0.967).
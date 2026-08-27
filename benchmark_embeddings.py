"""
benchmark_embeddings.py — Compare free embedding models + retrieval modes on the
golden QA set (eval/golden_qa.json).

Metrics (tutorial-level relevance: a hit = a retrieved chunk comes from the
tutorial that contains the answer):
  • Hit@1 / Hit@3 / Hit@5, MRR
  • Index build time, mean query latency
  • Curriculum-leak check: with the filter set to week W < answer tutorial,
    the answer tutorial must NEVER appear.

Usage:
    python benchmark_embeddings.py                     # all default models
    python benchmark_embeddings.py --models BAAI/bge-small-en-v1.5
"""
from __future__ import annotations

import argparse
import gc
import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

from rag_engine import HybridRetriever, build_index, rrf_fuse

HERE = Path(__file__).parent
GOLDEN = json.loads((HERE / "eval" / "golden_qa.json").read_text(encoding="utf-8"))["questions"]

DEFAULT_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",   # old baseline used by ingest.py
    "BAAI/bge-small-en-v1.5",
    "intfloat/e5-small-v2",
]
MODES = ["dense", "bm25", "hybrid", "hybrid+rerank"]


def retrieve_ids(r: HybridRetriever, query: str, week: int, k: int, mode: str) -> list[str]:
    if mode == "dense":
        return r._dense(query, week, k)
    if mode == "bm25":
        return r._lexical(query, week, k)
    rerank = mode.endswith("rerank")
    return [h.chunk.id for h in r.retrieve(query, week, k=k, rerank=rerank)]


def evaluate(r: HybridRetriever, mode: str, k: int = 5) -> dict:
    hits1 = hits3 = hits5 = 0
    rr: list[float] = []
    times: list[float] = []
    for item in GOLDEN:
        t0 = time.perf_counter()
        ids = retrieve_ids(r, item["q"], 99, k, mode)  # no filter: pure retrieval quality
        times.append(time.perf_counter() - t0)
        tutorials = [r.chunks[cid].tutorial for cid in ids]
        expect = item["expect_tutorial"]
        rank = next((i + 1 for i, t in enumerate(tutorials) if t == expect), None)
        rr.append(1.0 / rank if rank else 0.0)
        hits1 += rank == 1
        hits3 += bool(rank and rank <= 3)
        hits5 += bool(rank and rank <= 5)
    n = len(GOLDEN)
    return {
        "hit@1": hits1 / n, "hit@3": hits3 / n, "hit@5": hits5 / n,
        "mrr": statistics.mean(rr), "latency_ms": 1000 * statistics.mean(times),
    }


def leak_check(r: HybridRetriever) -> tuple[int, int]:
    """Retrieve with the curriculum filter one week BELOW the answer tutorial."""
    total = leaks = 0
    for item in GOLDEN:
        expect = item["expect_tutorial"]
        if expect <= 1:
            continue
        total += 1
        ids = [h.chunk.id for h in r.retrieve(item["q"], expect - 1, k=5, rerank=False)]
        if any(r.chunks[cid].tutorial >= expect for cid in ids):
            leaks += 1
    return leaks, total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    ap.add_argument("--out", default="BENCHMARK_RESULTS.md")
    args = ap.parse_args()

    rows: list[dict] = []
    leak_result = None

    work = Path(tempfile.mkdtemp(prefix="tutor_bench_"))
    for model in args.models:
        print(f"\n=== {model} ===")
        slug = model.split("/")[-1].replace(".", "_")
        idx, cf = work / slug / "index", work / slug / "chunks.jsonl"
        t0 = time.perf_counter()
        n_chunks = build_index(embed_model=model, index_dir=idx, chunks_file=cf, quiet=True)
        build_s = time.perf_counter() - t0
        r = HybridRetriever(index_dir=idx, chunks_file=cf, embed_model=model)
        for mode in MODES:
            m = evaluate(r, mode)
            rows.append({"model": model.split("/")[-1], "mode": mode,
                         "build_s": build_s, **m})
            print(f"  {mode:14s} hit@1={m['hit@1']:.2f} hit@3={m['hit@3']:.2f} "
                  f"hit@5={m['hit@5']:.2f} mrr={m['mrr']:.3f} "
                  f"lat={m['latency_ms']:.0f}ms")
        if leak_result is None:
            leak_result = leak_check(r)
        del r
        gc.collect()
    shutil.rmtree(work, ignore_errors=True)  # best-effort: Chroma may hold locks on Windows

    # ── report ──────────────────────────────────────────────────────────────
    best = max(rows, key=lambda x: (x["mrr"], x["hit@1"]))
    lines = [
        "# Benchmark — Embedding Models & Retrieval Modes",
        "",
        f"*Golden set: {len(GOLDEN)} student questions across 8 tutorials "
        "(mix of verbatim and paraphrased). Hit = retrieved chunk comes from the tutorial "
        f"containing the answer. Chunks indexed: {n_chunks}. CPU only.*",
        "",
        "| Model | Mode | Hit@1 | Hit@3 | Hit@5 | MRR | Query (ms) | Build (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for x in rows:
        mark = " **⭐**" if x is best else ""
        lines.append(
            f"| {x['model']} | {x['mode']}{mark} | {x['hit@1']:.2f} | {x['hit@3']:.2f} "
            f"| {x['hit@5']:.2f} | {x['mrr']:.3f} | {x['latency_ms']:.0f} | {x['build_s']:.1f} |"
        )
    leaks, total = leak_result
    lines += [
        "",
        "## Curriculum-boundary leak check",
        "",
        f"Retrieval filtered to one week **below** each answer's tutorial: "
        f"**{leaks}/{total} leaks** (must be 0 — the metadata filter makes future material "
        "unreachable regardless of the LLM).",
        "",
        f"**Recommended default:** `{best['model']}` with `{best['mode']}` "
        f"(MRR {best['mrr']:.3f}).",
    ]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

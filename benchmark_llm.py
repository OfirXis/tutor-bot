"""
benchmark_llm.py — Compare tutor LLMs: local Ollama models vs cheap cloud models.

Model spec syntax:
    llama3.2:3b            → local Ollama model
    github:gpt-4o-mini     → GitHub Models (free tier, needs GITHUB_TOKEN in .env)

For each model:
  • Answer quality proxies on 6 in-scope questions with retrieved context:
      - key-term coverage (does the answer mention the concepts the course uses?)
      - latency: time-to-first-token, total time, tokens/sec
  • Curriculum-refusal test on 3 out-of-scope questions (week 1 student asks
    about later material): the model must refuse per the system prompt.

Usage:
    python benchmark_llm.py --models llama3.2:3b qwen2.5:3b mistral:latest ^
                                     github:gpt-4o-mini github:gpt-4.1-mini
"""
from __future__ import annotations

import argparse
import os
import re
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from rag_engine import HybridRetriever, format_context, load_meta, tutor_system_prompt

load_dotenv()

HERE = Path(__file__).parent

IN_SCOPE = [  # (question, week, key-term regexes a grounded answer should match)
    ("What is the formal definition of Big-O notation?", 1,
     [r"constant", r"n_?\{?0\}?|n₀", r"c\s*(?:\\cdot|\*|·|\\,)?\s*g"]),
    ("State the Master Theorem and its cases.", 2, [r"\\?log_?\{?b\}?|log b", r"case"]),
    ("How does the activity selection greedy algorithm work and why is it correct?", 3,
     [r"finish", r"exchange|greedy choice"]),
    ("Explain the DP solution to the rod cutting problem.", 4, [r"revenue|price", r"recurrence|max"]),
    ("How does Kruskal's algorithm work?", 7, [r"sort", r"cycle|union"]),
    ("Why does Dijkstra fail with negative edge weights?", 8,
     [r"negative", r"greedy|finalized|settled|visited|relax"]),
]

OUT_OF_SCOPE = [  # week-1 student must be refused
    ("Explain Dijkstra's algorithm.", 1),
    ("How do I build a Huffman tree?", 1),
    ("What is the Floyd-Warshall recurrence?", 1),
]

REFUSAL_PAT = re.compile(
    r"haven'?t covered|not (?:yet )?covered|we'?ll (?:get|cover)|later (?:week|tutorial)|"
    r"not (?:been )?introduced|beyond (?:the|our|what)|so far", re.I)


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)  # rough estimate; fine for relative comparison


def make_llm(spec: str):
    """'github:<model>' → GitHub Models (cloud); anything else → local Ollama."""
    if spec.startswith("github:"):
        from langchain_openai import ChatOpenAI
        token = os.getenv("GITHUB_TOKEN", "")
        if not token:
            raise RuntimeError("GITHUB_TOKEN missing from .env")
        return ChatOpenAI(model=spec.split(":", 1)[1], api_key=token,
                          base_url="https://models.github.ai/inference", temperature=0.2)
    return ChatOllama(model=spec, base_url="http://localhost:11434", temperature=0.2, num_ctx=8192)


def run_model(model: str, retriever: HybridRetriever, meta: dict) -> dict:
    llm = make_llm(model)
    ttfts, totals, tps, coverage = [], [], [], []

    for q, week, terms in IN_SCOPE:
        hits = retriever.retrieve(q, week, k=4)
        tut = meta.get(f"tutorial_{week}", {})
        sys = tutor_system_prompt(week, tut.get("display_name", f"Week {week}"),
                                  tut.get("topics", []), format_context(hits))
        t0 = time.perf_counter()
        first, buf = None, ""
        for chunk in llm.stream([SystemMessage(sys), HumanMessage(q)]):
            if first is None and chunk.content:
                first = time.perf_counter() - t0
            buf += chunk.content
        total = time.perf_counter() - t0
        ttfts.append(first or total)
        totals.append(total)
        tps.append(count_tokens(buf) / total)
        hit_terms = sum(bool(re.search(t, buf, re.I)) for t in terms)
        coverage.append(hit_terms / len(terms))
        print(f"    [{model}] in-scope  '{q[:38]}…' {total:5.1f}s  terms {hit_terms}/{len(terms)}")

    refused = 0
    for q, week in OUT_OF_SCOPE:
        hits = retriever.retrieve(q, week, k=4)
        tut = meta.get(f"tutorial_{week}", {})
        sys = tutor_system_prompt(week, tut.get("display_name", f"Week {week}"),
                                  tut.get("topics", []), format_context(hits))
        ans = llm.invoke([SystemMessage(sys), HumanMessage(q)]).content
        ok = bool(REFUSAL_PAT.search(ans))
        refused += ok
        print(f"    [{model}] out-scope '{q[:38]}…' refused={ok}")

    return {
        "model": model,
        "type": "cloud" if model.startswith("github:") else "local",
        "term_coverage": statistics.mean(coverage),
        "refusal_rate": refused / len(OUT_OF_SCOPE),
        "ttft_s": statistics.mean(ttfts),
        "total_s": statistics.mean(totals),
        "tok_per_s": statistics.mean(tps),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", default="BENCHMARK_LLM.md")
    args = ap.parse_args()

    retriever = HybridRetriever()
    meta = load_meta()
    rows = []
    for m in args.models:
        print(f"\n=== {m} ===")
        try:
            rows.append(run_model(m, retriever, meta))
        except Exception as e:  # skip unavailable models, keep the run alive
            print(f"    [{m}] SKIPPED: {e}")

    lines = [
        "# Benchmark — Tutor LLMs: Local (Ollama) vs Cheap Cloud (GitHub Models)",
        "",
        f"*{len(IN_SCOPE)} in-scope questions (with retrieved context) + "
        f"{len(OUT_OF_SCOPE)} out-of-scope questions (week-1 student asking future material). "
        "Term coverage = fraction of expected course key-terms present in the answer. "
        "Refusal rate = fraction of out-of-scope questions correctly refused. "
        "Local hardware: RTX 5070 Laptop 4 GB VRAM. Cloud latency includes network; "
        "GitHub Models free tier is rate-limited but $0.*",
        "",
        "| Model | Type | Term coverage | Curriculum refusal | TTFT (s) | Total (s) | tok/s |",
        "|---|---|---|---|---|---|---|",
    ]
    best = max(rows, key=lambda x: (x["refusal_rate"], x["term_coverage"], x["tok_per_s"]))
    best_local = max((x for x in rows if x["type"] == "local"), default=None,
                     key=lambda x: (x["refusal_rate"], x["term_coverage"], x["tok_per_s"]))
    for x in rows:
        mark = " **⭐**" if x is best else ""
        lines.append(f"| {x['model']}{mark} | {x['type']} | {x['term_coverage']:.2f} "
                     f"| {x['refusal_rate']:.2f} "
                     f"| {x['ttft_s']:.1f} | {x['total_s']:.1f} | {x['tok_per_s']:.0f} |")
    lines += ["", f"**Best overall:** `{best['model']}`."]
    if best_local and best_local is not best:
        lines += [f"**Best local (fully offline/free):** `{best_local['model']}`."]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

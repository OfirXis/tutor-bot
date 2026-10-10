"""
benchmark_llm.py — Compare tutor LLMs: local Ollama models vs cloud models.

Model spec syntax:
    llama3.2:3b                          → local Ollama model (free)
    openrouter:anthropic/claude-haiku-5.5 → OpenRouter (paid, needs OPENROUTER_API_KEY in .env)
    openai:gpt-4o-mini                   → OpenAI (paid, needs OPENAI_API_KEY in .env)
    github:openai/gpt-4o-mini            → GitHub Models (being retired; usually HTTP 410)

For each model:
  • Answer quality proxies on in-scope questions with retrieved course context:
      - key-term coverage (does the answer mention the concepts the course uses?)
      - citation validity (does it cite only the supplied passages, as the app requires?)
      - latency: time-to-first-token, total time, tokens/sec
  • Curriculum-refusal test on out-of-scope questions (week 1 student asks about
    later material): the model must refuse per the system prompt. The app also
    enforces this deterministically; this column shows how far the model alone
    can be trusted.
  • Estimated cost of the run for OpenRouter models (public price list).

Usage:
    python benchmark_llm.py --models llama3.2:3b openrouter:anthropic/claude-haiku-5.5
Cloud models are billed per token: a full run is a few cents at most per model.
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import statistics
import subprocess
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from rag_engine import (EvidenceError, HybridRetriever, OPENROUTER_BASE_URL, format_context,
                        load_meta, split_grouped_citations, tutor_system_prompt, validate_citations)

load_dotenv()

HERE = Path(__file__).parent

IN_SCOPE = [  # (question, week, key-term regexes a grounded answer should match)
    ("What is the formal definition of Big-O notation?", 1,
     [r"constant", r"n_?\{?0\}?|n₀", r"c\s*(?:\\cdot|\*|·|\\,)?\s*g"]),
    ("How does merge sort work, and what is its running time?", 2,
     [r"half|halves|split|divide", r"merg", r"n\s*\\?log\s*n"]),
    ("How does the earliest-finish-time greedy algorithm for interval scheduling work?", 3,
     [r"finish", r"earliest|greedy", r"overlap|compatible|conflict"]),
    ("Explain the dynamic programming solution for the longest increasing subsequence.", 4,
     [r"subsequence", r"increasing", r"n\^?\{?2\}?|n²|binary search|n\s*\\?log\s*n"]),
    ("How does BFS find shortest paths in an unweighted graph?", 6,
     [r"queue|FIFO", r"level|layer|distance"]),
    ("How does Kruskal's algorithm work?", 7, [r"sort", r"cycle|union"]),
    ("When do we use Bellman-Ford instead of Dijkstra's algorithm?", 8,
     [r"negative", r"Bellman"]),
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


def hardware() -> str:
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        gpu = ""
    return gpu.replace(", ", " · ") or f"CPU only ({platform.processor() or platform.machine()})"


def openrouter_prices() -> dict[str, tuple[float, float]]:
    """USD per token (input, output) from OpenRouter's public model list; {} if offline."""
    try:
        import json
        import urllib.request
        with urllib.request.urlopen(f"{OPENROUTER_BASE_URL}/models", timeout=15) as response:
            models = json.load(response)["data"]
        return {m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"]))
                for m in models}
    except Exception:
        return {}


def make_llm(spec: str):
    """'<provider>:<model>' → cloud chat model; anything else → local Ollama."""
    provider, _, name = spec.partition(":")
    if provider in {"openrouter", "openai", "github"} and name:
        from langchain_openai import ChatOpenAI
        key_var, base_url = {
            "openrouter": ("OPENROUTER_API_KEY", OPENROUTER_BASE_URL),
            "openai": ("OPENAI_API_KEY", None),
            "github": ("GITHUB_TOKEN", "https://models.github.ai/inference"),
        }[provider]
        key = os.getenv(key_var, "")
        if not key:
            raise RuntimeError(f"{key_var} missing from .env")
        return ChatOpenAI(model=name, api_key=key, temperature=0.2, max_tokens=1200,
                          **({"base_url": base_url} if base_url else {}))
    return ChatOllama(model=spec, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                      temperature=0.2, num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")))


def run_model(model: str, retriever: HybridRetriever, meta: dict, prices: dict) -> dict:
    llm = make_llm(model)
    ttfts, totals, tps, coverage = [], [], [], []
    cited = input_tokens = output_tokens = 0

    def prompt_for(q: str, week: int):
        hits = retriever.retrieve(q, week, k=4)
        tut = meta.get(f"tutorial_{week}", {})
        sys = tutor_system_prompt(week, tut.get("display_name", f"Week {week}"),
                                  tut.get("topics", []), format_context(hits))
        return [SystemMessage(sys), HumanMessage(q)], len(hits)

    for q, week, terms in IN_SCOPE:
        messages, source_count = prompt_for(q, week)
        t0 = time.perf_counter()
        first, buf = None, ""
        for chunk in llm.stream(messages):
            if first is None and chunk.content:
                first = time.perf_counter() - t0
            buf += chunk.content
        total = time.perf_counter() - t0
        ttfts.append(first or total)
        totals.append(total)
        tps.append(count_tokens(buf) / total)
        hit_terms = sum(bool(re.search(t, buf, re.I)) for t in terms)
        coverage.append(hit_terms / len(terms))
        try:
            validate_citations(split_grouped_citations(buf), source_count)
            cited += 1
        except EvidenceError:
            pass
        input_tokens += sum(count_tokens(m.content) for m in messages)
        output_tokens += count_tokens(buf)
        print(f"    [{model}] in-scope  '{q[:38]}…' {total:5.1f}s  terms {hit_terms}/{len(terms)}")

    refused = 0
    for q, week in OUT_OF_SCOPE:
        messages, _ = prompt_for(q, week)
        ans = llm.invoke(messages).content
        ok = bool(REFUSAL_PAT.search(ans))
        refused += ok
        input_tokens += sum(count_tokens(m.content) for m in messages)
        output_tokens += count_tokens(ans)
        print(f"    [{model}] out-scope '{q[:38]}…' refused={ok}")

    provider, _, name = model.partition(":")
    price = prices.get(name) if provider == "openrouter" else None
    return {
        "model": model,
        "type": "cloud" if provider in {"openrouter", "openai", "github"} else "local",
        "term_coverage": statistics.mean(coverage),
        "cited": cited / len(IN_SCOPE),
        "refusal_rate": refused / len(OUT_OF_SCOPE),
        "ttft_s": statistics.mean(ttfts),
        "total_s": statistics.mean(totals),
        "tok_per_s": statistics.mean(tps),
        "cost": (input_tokens * price[0] + output_tokens * price[1]) if price else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", default="BENCHMARK_LLM.md")
    args = ap.parse_args()

    retriever = HybridRetriever()
    meta = load_meta()
    prices = openrouter_prices() if any(m.startswith("openrouter:") for m in args.models) else {}
    rows = []
    for m in args.models:
        print(f"\n=== {m} ===")
        try:
            rows.append(run_model(m, retriever, meta, prices))
        except Exception as e:  # skip unavailable models, keep the run alive
            print(f"    [{m}] SKIPPED: {e}")
    if not rows:
        raise SystemExit("No model completed the benchmark.")

    lines = [
        "# Benchmark — Tutor LLMs: Local (Ollama) vs Cloud",
        "",
        f"*Run {date.today().isoformat()} on {hardware()}. "
        f"{len(IN_SCOPE)} in-scope questions (weeks 1–8, with retrieved course context) + "
        f"{len(OUT_OF_SCOPE)} out-of-scope questions (week-1 student asking later material). "
        "Term coverage = fraction of expected course key-terms present in the answer. "
        "Cited = fraction of answers citing only supplied passages (the app's own check). "
        "Refusal = fraction of out-of-scope questions the model refused on its own; the app "
        "additionally blocks them before generation. Cloud latency includes network. "
        "Cost = estimated USD for this whole run (OpenRouter list prices; local models are free).*",
        "",
        "| Model | Type | Term coverage | Cited | Refusal (model only) | TTFT (s) | Total (s) | tok/s | Run cost |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    rank = lambda x: (x["cited"] + x["term_coverage"] + x["refusal_rate"], x["tok_per_s"])
    best = max(rows, key=rank)
    best_local = max((x for x in rows if x["type"] == "local"), default=None, key=rank)
    for x in rows:
        mark = " **⭐**" if x is best else ""
        cost = "free" if x["type"] == "local" else (f"${x['cost']:.4f}" if x["cost"] is not None else "n/a")
        lines.append(f"| {x['model']}{mark} | {x['type']} | {x['term_coverage']:.2f} | {x['cited']:.2f} "
                     f"| {x['refusal_rate']:.2f} | {x['ttft_s']:.1f} | {x['total_s']:.1f} "
                     f"| {x['tok_per_s']:.0f} | {cost} |")
    lines += ["", f"**Best overall:** `{best['model']}`."]
    if best_local and best_local is not best:
        lines += [f"**Best local (fully offline/free):** `{best_local['model']}`."]
    lines += ["", "Latency includes one cold model load per local model (the first question); "
              "warm answers are faster. Reproduce with "
              f"`python benchmark_llm.py --models {' '.join(x['model'] for x in rows)}`."]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()

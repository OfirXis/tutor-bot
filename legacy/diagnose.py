"""
diagnose.py  —  Check retrieval quality across all 8 tutorials.
Run: python diagnose.py
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

emb = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

TESTS = [
    ("tutorial_1", [
        "Big-O notation asymptotic complexity",
        "sorting algorithm time complexity",
    ]),
    ("tutorial_2", [
        "divide and conquer recurrence relation",
        "merge sort Master Theorem",
    ]),
    ("tutorial_3", [
        "greedy algorithm correctness proof",
        "exchange argument optimal solution",
    ]),
    ("tutorial_4", [
        "dynamic programming Fibonacci O(n)",
        "optimal substructure overlapping subproblems",
        "memoization recurrence table",
    ]),
    ("tutorial_5", [
        "dynamic programming continued advanced",
        "DP recurrence solution reconstruction",
    ]),
    ("tutorial_6", [
        "subset sum partition problem",
        "counting ways divide set",
    ]),
    ("tutorial_7", [
        "minimum spanning tree cut property",
        "Kruskal Prim algorithm",
    ]),
    ("tutorial_8", [
        "Dijkstra shortest path algorithm",
        "Bellman-Ford negative edges relaxation",
    ]),
]

results = {}

for tut_id, queries in TESTS:
    db = Chroma(persist_directory=f"db/{tut_id}", embedding_function=emb)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    tut_results = []
    for q in queries:
        docs = retriever.invoke(q)
        snippets = [d.page_content[:80].replace("\n", " ") for d in docs]
        tut_results.append({
            "query": q,
            "hits": len(docs),
            "top_snippet": snippets[0] if snippets else "NO RESULTS",
        })
    results[tut_id] = tut_results

# Write to a UTF-8 report file
report_path = "diagnose_report.txt"
with open(report_path, "w", encoding="utf-8") as f:
    for tut_id, tut_results in results.items():
        f.write(f"\n{'='*60}\n{tut_id.upper()}\n{'='*60}\n")
        for r in tut_results:
            status = "✅" if r["hits"] > 0 else "❌"
            f.write(f"  {status} Query: {r['query']}\n")
            f.write(f"     Hits: {r['hits']}\n")
            f.write(f"     Top:  {r['top_snippet']}\n\n")

print(f"Report written to {report_path}")

# Also print a summary
ok = sum(1 for t in results.values() for r in t if r["hits"] > 0)
total = sum(len(t) for t in results.values())
print(f"Retrieval: {ok}/{total} queries returned results")

# Flag any zero-hit queries
for tut_id, tut_results in results.items():
    for r in tut_results:
        if r["hits"] == 0:
            print(f"  ⚠  NO RESULTS: [{tut_id}] '{r['query']}'")

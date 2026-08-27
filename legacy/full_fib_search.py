"""
full_fib_search.py — Find ALL Fibonacci-related chunks in tutorial_4
and measure overall chunk quality across all tutorials.
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

# ── 1. Get ALL Fibonacci chunks from tutorial_4 ───────────────────────────────
db4 = Chroma(persist_directory="db/tutorial_4", embedding_function=emb)
fib_docs = db4.as_retriever(search_kwargs={"k": 20}).invoke(
    "Fibonacci sequence dynamic programming O(n) memoization table"
)

report = ["=" * 60, "ALL FIBONACCI CHUNKS IN TUTORIAL_4 (k=20)", "=" * 60]
for i, d in enumerate(fib_docs[:10]):
    wc = len(d.page_content.split())
    report.append(f"\nChunk {i+1} ({wc} words):")
    report.append(d.page_content[:400])

# ── 2. Measure chunk quality across all tutorials ─────────────────────────────
report += ["", "=" * 60, "CHUNK QUALITY STATS PER TUTORIAL", "=" * 60]

for tut in [f"tutorial_{i}" for i in range(1, 9)]:
    db = Chroma(persist_directory=f"db/{tut}", embedding_function=emb)
    # Get all stored chunks via a broad query
    all_docs = db._collection.get()
    docs_text = all_docs["documents"]
    word_counts = [len(t.split()) for t in docs_text]
    thin = sum(1 for w in word_counts if w < 15)  # title-only chunks
    total = len(word_counts)
    avg = sum(word_counts) / total if total else 0
    report.append(
        f"  {tut}: {total} chunks, avg {avg:.0f} words, "
        f"thin (<15 words): {thin} ({100*thin//total if total else 0}%)"
    )

with open("full_fib_search.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("Written to full_fib_search.txt")

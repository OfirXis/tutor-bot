"""deep_check.py — Show full chunk content for key topics to spot thin/missing content."""
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

SPOT_CHECKS = [
    ("tutorial_4", "Fibonacci O(n) dynamic programming memoization table"),
    ("tutorial_4", "base case recurrence F(n) F(n-1) F(n-2)"),
    ("tutorial_1", "Big-O O(n) O(n log n) O(n^2) comparison"),
    ("tutorial_2", "recurrence T(n) Master Theorem case"),
    ("tutorial_7", "Kruskal cut property safe edge MST proof"),
    ("tutorial_8", "Dijkstra relaxation priority queue steps"),
]

report = []
for tut_id, query in SPOT_CHECKS:
    db = Chroma(persist_directory=f"db/{tut_id}", embedding_function=emb)
    docs = db.as_retriever(search_kwargs={"k": 2}).invoke(query)
    report.append(f"\n{'='*60}")
    report.append(f"[{tut_id}]  Query: {query}")
    report.append(f"{'='*60}")
    for i, d in enumerate(docs):
        content = d.page_content.strip()
        word_count = len(content.split())
        report.append(f"\n  --- Chunk {i+1} ({word_count} words) ---")
        report.append(content[:500])

with open("deep_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("Written to deep_check.txt")

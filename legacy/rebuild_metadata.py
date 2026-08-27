"""
rebuild_metadata.py — Rebuild metadata.json with comprehensive topic_context:
  Full lecture content (from material/english/tutorial_N.txt)
  + prerequisite summary
  + problem-solving framework (from current metadata)
"""
import json
from pathlib import Path

ENGLISH_DIR = Path("material/english")
META_FILE = Path("db/metadata.json")

current_meta = json.loads(META_FILE.read_text(encoding="utf-8"))

PREREQS = {
    "tutorial_1": "",
    "tutorial_2": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nTutorial 1: Big-O/Omega/Theta notation, complexity hierarchy O(1)<O(log n)<O(n)<O(n log n)<O(n^2)<O(2^n), counting operations in loops, insertion/selection/bubble sort O(n^2).\n",
    "tutorial_3": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1: Asymptotic notation (Big-O, Omega, Theta).\nT2: Divide & Conquer paradigm, Master Theorem (3 cases), merge sort O(n log n), binary search O(log n), Karatsuba O(n^1.585).\n",
    "tutorial_4": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1: Asymptotic notation.\nT2: D&C, Master Theorem, merge sort, binary search.\nT3: Greedy algorithms — activity selection O(n log n), fractional knapsack O(n log n), Huffman coding O(n log n), exchange argument correctness proofs.\n",
    "tutorial_5": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1: Asymptotic notation.\nT2: D&C, Master Theorem.\nT3: Greedy (activity selection, fractional knapsack, Huffman, exchange argument).\nT4: DP basics — Fibonacci O(n) vs O(2^n) brute force, rod cutting O(n^2), LCS O(mn), 0/1 knapsack O(nW). DP 5-step method: define state, recurrence, base cases, order, extract answer.\n",
    "tutorial_6": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1: Asymptotic notation.\nT2: D&C, Master Theorem.\nT3: Greedy.\nT4: DP basics — Fibonacci, rod cutting, LCS, 0/1 knapsack.\nT5: DP advanced — coin change O(amount*coins), matrix chain O(n^3), edit distance O(mn), LIS O(n^2), minimum vertex cover on trees O(n).\n",
    "tutorial_7": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1-T3: Algorithm analysis, D&C, Greedy.\nT4: DP basics.\nT5: DP advanced (coin change, matrix chain, edit distance, LIS).\nT6: DP combinatorics — subset sum O(nS), partition (reduce to subset sum), counting subsets, grid paths O(nm).\n",
    "tutorial_8": "PREREQUISITES COVERED BEFORE THIS TUTORIAL:\nT1-T3: Fundamentals.\nT4-T6: All DP variants (basics, advanced, combinatorics).\nT7: Minimum Spanning Trees — Cut Property, Cycle Property, Kruskal O(E log E), Prim O(E log V), Union-Find with path compression O(alpha(V)).\n",
}

new_meta = {}
for i in range(1, 9):
    tid = f"tutorial_{i}"
    txt_file = ENGLISH_DIR / f"tutorial_{i}.txt"
    if not txt_file.exists():
        print(f"WARNING: {txt_file} missing, skipping")
        continue

    lecture_text = txt_file.read_text(encoding="utf-8")
    old = current_meta.get(tid, {})
    ps_framework = old.get("topic_context", "")
    display = old.get("display_name", f"Tutorial {i}")
    prereqs = PREREQS.get(tid, "")

    parts = []
    if prereqs:
        parts.append(prereqs)
    parts.append(lecture_text)
    if ps_framework:
        parts.append("=== PROBLEM-SOLVING GUIDE ===\n" + ps_framework)

    full_context = "\n\n".join(parts)
    new_meta[tid] = {"display_name": display, "topic_context": full_context}
    chars = len(full_context)
    print(f"{tid}: {chars:,} chars in topic_context")

META_FILE.write_text(json.dumps(new_meta, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nmetadata.json rebuilt successfully.")

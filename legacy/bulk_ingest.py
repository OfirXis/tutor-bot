"""
bulk_ingest.py
Ingests all course material into the vector database.
Run once: python bulk_ingest.py
No API key needed — embeddings are 100% local.

NOTE: The lecture PDFs are Hebrew + diagram-heavy. Text extraction only gets
slide titles and fragments. The topic_context below therefore encodes the full
curriculum explicitly so the Socratic tutor can guide students correctly even
when retrieved text is thin.
"""
import json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent
os.chdir(ROOT)

import warnings
warnings.filterwarnings("ignore")

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_DIR    = ROOT / "db"
META_FILE = DB_DIR / "metadata.json"

print("Loading local embedding model (all-MiniLM-L6-v2)…")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
print("Model ready.\n")

# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL — (id, display_name, pdf_path, topic_context)
#
# topic_context encodes the FULL algorithm knowledge so the tutor can
# guide correctly even when PDF slides are image-heavy (no extractable text).
# ─────────────────────────────────────────────────────────────────────────────

MATERIAL = [
    # ── Tutorial 1: Algorithm Analysis & Asymptotic Notation ─────────────────
    (
        "tutorial_1",
        "Tutorial 1 — Intro to Algorithm Analysis",
        "material/lectures/Tutorial 1 (2).pdf",
        """Algorithm Design & Analysis — Tutorial 1: Introduction & Asymptotic Notation.

CORE KNOWLEDGE:
Asymptotic notation:
  - Big-O (upper bound):   f(n) = O(g(n))  iff  ∃ c>0, n₀ s.t. f(n) ≤ c·g(n) for all n ≥ n₀
  - Omega (lower bound):  f(n) = Ω(g(n))  iff  ∃ c>0, n₀ s.t. f(n) ≥ c·g(n) for all n ≥ n₀
  - Theta (tight bound):  f(n) = Θ(g(n))  iff  f(n) = O(g(n)) AND f(n) = Ω(g(n))

Common complexity hierarchy (slowest to fastest growing):
  O(1) < O(log n) < O(√n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)

Rules for counting operations:
  - Loops: multiply iterations × body cost
  - Nested loops: multiply all levels
  - Consecutive blocks: take the maximum (or add, then take dominant term)
  - Recursive calls: write a recurrence relation

Sorting algorithms covered:
  - Insertion sort: O(n²) worst, O(n) best (already sorted)
  - Selection sort: always O(n²)
  - Bubble sort: O(n²) worst

SOCRATIC GUIDANCE:
- Never give the final Big-O directly. Ask "How many times does the inner loop run for each outer iteration?"
- Ask students to write a sum and simplify it before giving the answer.
- If a student says "O(n²) because there are two loops", ask them to verify with an actual count.
- For 3n²+2n+5, ask "Which term dominates as n→∞? What can we drop?"
""",
    ),

    # ── Tutorial 2: Divide & Conquer ─────────────────────────────────────────
    (
        "tutorial_2",
        "Tutorial 2 — Divide & Conquer",
        "material/lectures/Tutorial 2 (2).pdf",
        """Algorithm Design & Analysis — Tutorial 2: Divide and Conquer.

CORE KNOWLEDGE:
Divide & Conquer pattern:
  1. Divide the problem into a subproblems of size n/b each
  2. Conquer: solve recursively
  3. Combine: merge solutions in f(n) time
  Recurrence: T(n) = a·T(n/b) + f(n)

Master Theorem — for T(n) = a·T(n/b) + f(n), let k = log_b(a):
  Case 1: f(n) = O(n^(k-ε))         → T(n) = Θ(n^k)           [recursion dominates]
  Case 2: f(n) = Θ(n^k · log^p(n))  → T(n) = Θ(n^k · log^(p+1)(n))  [equal work]
  Case 3: f(n) = Ω(n^(k+ε)) + regularity → T(n) = Θ(f(n))     [combination dominates]

Key algorithms and their recurrences:
  Merge sort:    T(n) = 2T(n/2) + O(n)    → O(n log n)    [Case 2, a=2, b=2, k=1]
  Binary search: T(n) = T(n/2) + O(1)     → O(log n)      [Case 2, a=1, b=2, k=0]
  Karatsuba mul: T(n) = 3T(n/2) + O(n)   → O(n^log₂3) ≈ O(n^1.585)

Merge sort algorithm:
  mergesort(A, l, r):
    if l >= r: return
    m = (l+r)//2
    mergesort(A, l, m)
    mergesort(A, m+1, r)
    merge(A, l, m, r)   ← O(n) step

SOCRATIC GUIDANCE:
- When a student writes a recurrence, ask "What is a? b? f(n)?" before applying Master Theorem.
- Ask "Which case of the Master Theorem applies? Compare f(n) to n^(log_b a) first."
- Never give the final answer. If they got the recurrence wrong, ask "How many recursive calls does each call make?"
""",
    ),

    # ── Tutorial 3: Greedy Algorithms ────────────────────────────────────────
    (
        "tutorial_3",
        "Tutorial 3 — Greedy Algorithms",
        "material/lectures/Tutorial 3 (2).pdf",
        """Algorithm Design & Analysis — Tutorial 3: Greedy Algorithms.

CORE KNOWLEDGE:
Greedy algorithm: always picks the locally optimal choice.
Two properties needed for greedy to work:
  1. Greedy choice property: local optimal ⇒ global optimal (no backtracking needed)
  2. Optimal substructure: optimal solution contains optimal solutions to subproblems

Exchange argument (proof technique):
  - Assume an optimal solution OPT differs from greedy solution G at some step.
  - Show you can swap OPT's choice for G's choice without making OPT worse.
  - Conclude G is at least as good as OPT.

Key greedy problems:
  Activity selection (interval scheduling):
    - Sort by finish time. Always pick earliest-finishing compatible activity.
    - Greedy works. T = O(n log n).

  Fractional knapsack:
    - Sort items by value/weight ratio descending. Take as much as possible.
    - Greedy works (can take fractions). T = O(n log n).

  0/1 Knapsack:
    - Greedy does NOT work. Requires Dynamic Programming.

  Huffman coding:
    - Build optimal prefix-free code. Use min-heap, merge two smallest frequencies.
    - Greedy works. T = O(n log n).

  Coin change (standard denominations like 1,5,10,25):
    - Greedy works for some denomination sets, NOT in general.
    - Counterexample: denominations {1,3,4}, target 6 → greedy gives 4+1+1=3 coins, optimal is 3+3=2 coins.

SOCRATIC GUIDANCE:
- Never confirm a greedy solution without asking "How would you prove it's always optimal? What's the exchange argument?"
- If student proposes greedy for 0/1 knapsack, ask "Can you find a small counterexample with 2-3 items?"
- Ask "Does the greedy choice property hold here? What if you chose differently at step 1?"
""",
    ),

    # ── Tutorial 4: Dynamic Programming ─────────────────────────────────────
    (
        "tutorial_4",
        "Tutorial 4 — Dynamic Programming",
        "material/lectures/Tutorial 4 (2).pdf",
        """Algorithm Design & Analysis — Tutorial 4: Dynamic Programming (DP).

CORE KNOWLEDGE:
Dynamic Programming applies when:
  1. Optimal substructure: optimal solution built from optimal sub-solutions
  2. Overlapping subproblems: same subproblems solved repeatedly (unlike D&C)

DP design steps:
  1. Define the subproblem (what does dp[i] or dp[i][j] represent?)
  2. Write the recurrence relation
  3. Identify base cases
  4. Determine computation order (bottom-up or top-down with memoization)
  5. Extract the answer

FIBONACCI SEQUENCE — the canonical DP example:
  Definition: F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2) for n≥2
  Naive recursive: exponential O(2^n) — recomputes same values
  DP solution (O(n) time, O(n) space):
    dp[0] = 0
    dp[1] = 1
    for i in range(2, n+1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
  Optimized (O(n) time, O(1) space — only keep last two values):
    a, b = 0, 1
    for _ in range(n-1):
        a, b = b, a+b
    return b

ROD CUTTING:
  Given rod of length n, prices p[1..n].
  dp[i] = max revenue from rod of length i
  dp[0] = 0
  dp[i] = max(p[j] + dp[i-j]) for j in 1..i
  T = O(n²)

LONGEST COMMON SUBSEQUENCE (LCS):
  dp[i][j] = length of LCS of s1[1..i] and s2[1..j]
  dp[0][j] = dp[i][0] = 0
  if s1[i] == s2[j]: dp[i][j] = dp[i-1][j-1] + 1
  else:              dp[i][j] = max(dp[i-1][j], dp[i][j-1])
  T = O(mn)

0/1 KNAPSACK:
  dp[i][w] = max value using items 1..i with weight capacity w
  dp[0][w] = 0
  dp[i][w] = dp[i-1][w]                           if weight[i] > w
           = max(dp[i-1][w], dp[i-1][w-weight[i]] + value[i])  otherwise
  T = O(nW)

SOCRATIC GUIDANCE:
- On Fibonacci: "The naive recursion is exponential. Can you draw the recursion tree and spot what's being recomputed?"
- "If F(5) requires F(4) and F(3), and F(4) requires F(3) and F(2)... what do you notice?"
- "What if you stored each F(i) as you compute it? How many distinct values do you need?"
- Never give the dp array directly. Ask "What would dp[0] and dp[1] be as base cases?"
- For O(1) space: "Do you actually need all previous values, or just the last two?"
""",
    ),

    # ── Tutorial 5: DP continued ─────────────────────────────────────────────
    (
        "tutorial_5",
        "Tutorial 5 — Dynamic Programming (cont.)",
        "material/lectures/Tutorial algo 5.pdf",
        """Algorithm Design & Analysis — Tutorial 5: Dynamic Programming (continued).

CORE KNOWLEDGE:
This tutorial covers advanced DP patterns building on Tutorial 4.

COIN CHANGE (min coins):
  dp[i] = minimum number of coins to make amount i
  dp[0] = 0
  dp[i] = min(dp[i - coin] + 1) for each coin ≤ i
  dp[i] = infinity if no combination works
  T = O(amount × num_coins)

MATRIX CHAIN MULTIPLICATION:
  Given matrices A1...An, find optimal parenthesization to minimize multiplications.
  dp[i][j] = min cost to multiply matrices Ai through Aj
  dp[i][i] = 0
  dp[i][j] = min over k in [i, j-1] of: dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]
  T = O(n³)

EDIT DISTANCE (Levenshtein):
  dp[i][j] = min edits to transform s1[1..i] into s2[1..j]
  Operations: insert, delete, replace (each cost 1)
  dp[0][j] = j,  dp[i][0] = i
  if s1[i]==s2[j]: dp[i][j] = dp[i-1][j-1]
  else: dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
  T = O(mn)

LONGEST INCREASING SUBSEQUENCE (LIS):
  dp[i] = length of LIS ending at index i
  dp[i] = 1 + max(dp[j] for j<i if A[j]<A[i]),  dp[i]=1 if no such j
  Answer = max(dp)
  T = O(n²) naive, O(n log n) with patience sorting

SOLUTION RECONSTRUCTION:
  Keep a "parent" array alongside dp to trace back the optimal solution.
  parent[i] = the previous index in the optimal solution ending at i.

SOCRATIC GUIDANCE:
- For coin change: "What subproblem do you solve before knowing dp[10]? What are its dependencies?"
- For matrix chain: "Interval DP: what does dp[i][j] represent? What split points k should you try?"
- For LIS: "For each position i, what information do you need from positions before i?"
- Ask students to fill a small example table before writing code.
""",
    ),

    # ── Tutorial 6: DP — Subset Sum & Combinatorics ──────────────────────────
    (
        "tutorial_6",
        "Tutorial 6 — DP: Partition & Combinatorics",
        "material/lectures/Tutorial algo 6.pdf",
        """Algorithm Design & Analysis — Tutorial 6: DP on Subsets and Counting.

CORE KNOWLEDGE:
SUBSET SUM:
  Problem: can a subset of array A[1..n] sum to target S?
  dp[i][s] = True if some subset of A[1..i] sums to s
  dp[0][0] = True,  dp[0][s>0] = False
  dp[i][s] = dp[i-1][s]  OR  (s >= A[i] AND dp[i-1][s-A[i]])
  Answer: dp[n][S]
  T = O(nS),  Space = O(nS) or O(S) with rolling array

PARTITION INTO EQUAL SUBSETS:
  Problem: can A[1..n] be split into two subsets with equal sum?
  Precondition: total sum must be even; target = sum/2
  Reduce to: subset sum with target = sum/2
  T = O(n × sum)

COUNT OF SUBSETS SUMMING TO S:
  dp[i][s] = number of subsets of A[1..i] that sum to s
  dp[0][0] = 1,  dp[0][s>0] = 0
  dp[i][s] = dp[i-1][s] + (dp[i-1][s-A[i]] if s >= A[i] else 0)

PARTITION INTO K EQUAL SUBSETS (harder):
  Use bitmask DP or backtracking.
  Not solvable efficiently with standard 2D DP for large k.

COUNTING PATHS IN A GRID:
  dp[i][j] = number of paths from top-left to cell (i,j) moving only right or down
  dp[0][j] = 1,  dp[i][0] = 1
  dp[i][j] = dp[i-1][j] + dp[i][j-1]

SOCRATIC GUIDANCE:
- "Before coding, what does dp[i][s] represent in words? Be precise."
- "What are the two choices for item i: include it or exclude it. How do both cases update dp[i][s]?"
- "If A = [1,2,3] and S = 3, trace through the dp table manually for the first two items."
- For partition: "What's the first check you should do before running DP? (hint: parity of sum)"
""",
    ),

    # ── Tutorial 7: Minimum Spanning Trees ───────────────────────────────────
    (
        "tutorial_7",
        "Tutorial 7 — Minimum Spanning Trees",
        "material/lectures/Tutorial algo 7.pdf",
        """Algorithm Design & Analysis — Tutorial 7: Minimum Spanning Trees (MST).

CORE KNOWLEDGE:
DEFINITIONS:
  Spanning tree: tree containing all V vertices of a connected graph, with V-1 edges.
  MST: spanning tree with minimum total edge weight.
  A graph can have multiple MSTs if edges have equal weights.

CUT PROPERTY (proof basis for greedy MST):
  For any cut (partition of vertices into two sets S and V-S),
  the minimum-weight edge crossing the cut belongs to some MST.
  → This justifies always picking the cheapest edge crossing a cut.

CYCLE PROPERTY:
  The maximum-weight edge in any cycle does NOT belong to any MST.
  (If it were in MST, removing it and adding a cheaper cross-cut edge gives a lighter spanning tree.)

KRUSKAL'S ALGORITHM:
  1. Sort all edges by weight ascending.  T = O(E log E)
  2. For each edge (u,v) in sorted order:
       if u and v are in different components: add edge to MST (Union-Find)
  Uses Union-Find (disjoint sets) with path compression + union by rank: O(α(V)) per op
  Total: O(E log E)  [dominated by sorting]

PRIM'S ALGORITHM:
  1. Start from any vertex. Mark it as in MST.
  2. Repeatedly add the cheapest edge from the MST frontier to a non-MST vertex.
  3. Use a min-heap (priority queue) of candidate edges.
  T = O(E log V) with binary heap.
  Good for dense graphs (E >> V).

UNION-FIND (Disjoint Sets):
  Operations: find(x) returns root of x's set; union(x,y) merges sets.
  Path compression: during find, point all nodes directly to root.
  Union by rank: attach smaller tree under larger.
  Combined: amortized O(α(n)) ≈ O(1) per operation.

SOCRATIC GUIDANCE:
- "Which algorithm would you choose if the graph is dense (many edges)? Why?"
- "In Kruskal's, what data structure prevents cycles? How does it work?"
- "State the cut property in your own words. For a given cut, which edge must be in the MST?"
- "If two edges have the same weight, can the MST be unique? Give an example."
- Never give the algorithm steps directly. Ask "What should we do with the cheapest edge in the whole graph?"
""",
    ),

    # ── Tutorial 8: Shortest Paths ───────────────────────────────────────────
    (
        "tutorial_8",
        "Tutorial 8 — Shortest Paths",
        "material/lectures/Tutorial algo 8.pdf",
        """Algorithm Design & Analysis — Tutorial 8: Shortest Path Algorithms.

CORE KNOWLEDGE:
RELAXATION (core operation for all shortest path algorithms):
  if d[u] + w(u,v) < d[v]:
      d[v] = d[u] + w(u,v)
      parent[v] = u
  "Relaxing edge (u,v)": update shortest known path to v through u.

DIJKSTRA'S ALGORITHM (non-negative weights only):
  1. Initialize d[source]=0, d[all others]=∞
  2. Insert all vertices into min-heap by d value
  3. While heap not empty:
       u = extract-min
       for each neighbor v of u:
           relax(u, v)
           update v's key in heap if improved
  T = O((V + E) log V) with binary heap
  FAILS with negative edges: once a vertex is extracted, its distance is "final".
  With negative edges, a later path might be shorter, violating this assumption.

BELLMAN-FORD ALGORITHM (handles negative weights):
  1. Initialize d[source]=0, d[all others]=∞
  2. Repeat V-1 times:
       for each edge (u,v) with weight w:
           relax(u,v)
  3. Check for negative cycles:
       for each edge (u,v): if d[u]+w < d[v]: NEGATIVE CYCLE DETECTED
  T = O(VE)
  Negative cycle: if a cycle has total negative weight, no shortest path exists (can loop forever).

COMPARISON:
  Dijkstra: faster O((V+E) log V), requires non-negative weights
  Bellman-Ford: slower O(VE), works with negative weights, detects negative cycles

DAG SHORTEST PATH (Directed Acyclic Graph):
  Topological sort, then relax edges in topological order.
  T = O(V + E), works with negative edges (no cycles to exploit).

FLOYD-WARSHALL (all-pairs shortest paths):
  dp[k][i][j] = shortest path from i to j using only vertices {1..k} as intermediates
  dp[0][i][j] = w(i,j) if edge exists, else ∞
  dp[k][i][j] = min(dp[k-1][i][j], dp[k-1][i][k] + dp[k-1][k][j])
  T = O(V³)

SOCRATIC GUIDANCE:
- "Why can't Dijkstra handle negative edges? Draw a 3-node example where it gives the wrong answer."
- "In Bellman-Ford, why exactly V-1 iterations? What's the longest possible shortest path in a graph with V vertices?"
- "After Bellman-Ford terminates, how do you detect if a negative cycle exists?"
- "Relaxation is the key step. In your own words, what does 'relaxing edge (u,v)' mean?"
- Never give the pseudocode directly. Ask students to reason about the invariant maintained at each step.
""",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# CUMULATIVE PREREQUISITES
# Each tutorial's context includes a summary of everything learned before it,
# so the tutor can answer questions that mix concepts from multiple tutorials.
# ─────────────────────────────────────────────────────────────────────────────

PREREQUISITES = {
    "tutorial_1": "",
    "tutorial_2": (
        "PREVIOUSLY COVERED (Tutorial 1): Big-O, Omega, Theta notation; "
        "O(1)<O(log n)<O(n)<O(n log n)<O(n²)<O(2ⁿ); insertion/selection/bubble sort O(n²)."
    ),
    "tutorial_3": (
        "PREVIOUSLY COVERED: Asymptotic notation O/Ω/Θ (T1); "
        "Divide & Conquer paradigm, Master Theorem (3 cases), merge sort O(n log n), binary search O(log n) (T2)."
    ),
    "tutorial_4": (
        "PREVIOUSLY COVERED: Asymptotic notation (T1); D&C + Master Theorem (T2); "
        "Greedy (activity selection, fractional knapsack, Huffman; exchange argument proofs) (T3)."
    ),
    "tutorial_5": (
        "PREVIOUSLY COVERED: Asymptotic notation (T1); D&C + Master Theorem (T2); Greedy (T3); "
        "DP basics — Fibonacci O(n), rod cutting, LCS, 0/1 knapsack (T4)."
    ),
    "tutorial_6": (
        "PREVIOUSLY COVERED: T1 notation; T2 D&C; T3 greedy; T4 DP basics; "
        "T5 DP advanced — coin change, matrix chain, edit distance, LIS."
    ),
    "tutorial_7": (
        "PREVIOUSLY COVERED: T1–T3 fundamentals; T4–T5 DP (Fibonacci→LIS); "
        "T6 DP on subsets (subset sum, partition, counting, grid paths)."
    ),
    "tutorial_8": (
        "PREVIOUSLY COVERED: T1–T3 fundamentals; T4–T6 DP (all variants); "
        "T7 MST — cut/cycle property, Kruskal O(E log E), Prim O(E log V), Union-Find."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# INGESTION
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_DIR     = ROOT / "material" / "english"
MIN_CHUNK_CHARS = 60   # filter noise chunks below this length

def build_full_context(hw_id: str, topic_context: str) -> str:
    """Combine prerequisites + English curriculum notes + topic knowledge."""
    prereqs = PREREQUISITES.get(hw_id, "")

    # Load English curriculum notes generated by extract_curriculum.py
    eng_file = ENGLISH_DIR / f"{hw_id}.txt"
    english_notes = eng_file.read_text(encoding="utf-8") if eng_file.exists() else ""

    parts = []
    if prereqs:
        parts.append(f"=== PREREQUISITE KNOWLEDGE ===\n{prereqs}")
    if english_notes:
        parts.append(f"=== CURRICULUM NOTES (from course slides, translated) ===\n{english_notes}")
    parts.append(f"=== ALGORITHM REFERENCE ===\n{topic_context}")

    return "\n\n".join(parts)


def ingest(hw_id: str, display_name: str, pdf_path: str, topic_context: str) -> int:
    from langchain_core.documents import Document

    path = ROOT / pdf_path
    if not path.exists():
        print(f"  ⚠  SKIP — file not found: {path}")
        return 0

    db_path = DB_DIR / hw_id
    if db_path.exists():
        shutil.rmtree(db_path)

    # ── 1. PDF chunks (slide fragments — Hebrew but contain math notation) ────
    pages     = PyPDFLoader(str(path)).load()
    all_chunks = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=150
    ).split_documents(pages)
    pdf_chunks = [c for c in all_chunks if len(c.page_content.strip()) >= MIN_CHUNK_CHARS]
    if len(all_chunks) - len(pdf_chunks):
        print(f"  (filtered {len(all_chunks)-len(pdf_chunks)} noise chunks from PDF)")

    # ── 2. English curriculum notes → split into searchable chunks ───────────
    eng_file = ENGLISH_DIR / f"{hw_id}.txt"
    eng_chunks = []
    if eng_file.exists():
        eng_text = eng_file.read_text(encoding="utf-8")
        splitter  = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        eng_chunks = splitter.create_documents(
            [eng_text],
            metadatas=[{"source": "curriculum_english", "tutorial": hw_id}],
        )
        print(f"  ({len(eng_chunks)} chunks from English curriculum notes)")

    # ── 3. Synthetic "curriculum reference" doc (always retrieved for any query) ──
    full_context = build_full_context(hw_id, topic_context)
    # Split into overlapping chunks so any part is searchable
    ctx_chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).create_documents(
        [full_context],
        metadatas=[{"source": "curriculum_reference", "tutorial": hw_id}],
    )

    all_docs = ctx_chunks + eng_chunks + pdf_chunks
    Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=str(db_path),
    )
    return len(all_docs)


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    meta = json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}

    total_chunks = 0
    for hw_id, display_name, pdf_path, topic_context in MATERIAL:
        print(f"→ [{hw_id}]  {display_name}")
        full_ctx = build_full_context(hw_id, topic_context)
        n = ingest(hw_id, display_name, pdf_path, topic_context)
        if n:
            # Store the full cumulative context so the app's system prompt is always complete
            meta[hw_id] = {"display_name": display_name, "topic_context": full_ctx}
            total_chunks += n
            print(f"   ✓  {n} chunks indexed")
        print()

    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done. {len(meta)} items in database, {total_chunks} total chunks.")
    print("Start the app:  streamlit run app.py")


if __name__ == "__main__":
    main()

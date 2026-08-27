"""
bulk_ingest2.py — Complete rewrite with rich topic prompts + noise filtering.
Replaces bulk_ingest.py's results. Run: python bulk_ingest2.py
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

print("Loading embedding model…")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
print("Model ready.\n")

# ─────────────────────────────────────────────────────────────────────────────
# MATERIAL — (id, display_name, pdf_path, topic_context)
# topic_context supplements thin PDF text with explicit curriculum knowledge
# so the tutor can guide students even when diagram content isn't extractable.
# ─────────────────────────────────────────────────────────────────────────────

MATERIAL = [
    (
        "tutorial_1",
        "Tutorial 1 — Intro to Algorithm Analysis",
        "material/lectures/Tutorial 1 (2).pdf",
        """Tutorial 1: Introduction to Algorithm Design & Analysis.

CURRICULUM (explicit knowledge to supplement the slides):
- Running time: count primitive operations as a function of input size n.
- Asymptotic notation:
    Big-O (upper bound): f = O(g) means f grows no faster than g.
    Omega (lower bound): f = Omega(g) means f grows at least as fast as g.
    Theta (tight): f = Theta(g) means both O and Omega hold.
- Complexity hierarchy (slowest to fastest growing):
    O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n)
- Identifying complexity from code:
    O(1) per element, single pass = O(n).
    Each step halves the problem = O(log n).
    Sort or binary-search on each element = O(n log n).
    Nested loops over all pairs = O(n^2).
- Sorting: Selection sort O(n^2), Insertion sort O(n^2), Merge sort O(n log n).

SOCRATIC GUIDANCE:
- Never state the complexity directly. Ask students to count operations first.
- "How many times does the inner loop execute for each outer iteration?"
- "What is the dominant term when n grows very large?"
""",
    ),
    (
        "tutorial_2",
        "Tutorial 2 — Divide & Conquer",
        "material/lectures/Tutorial 2 (2).pdf",
        """Tutorial 2: Divide and Conquer.

CURRICULUM:
- Paradigm: split into a subproblems of size n/b each, combine in f(n) → T(n) = a*T(n/b) + f(n).
- Master Theorem (compare f(n) to n^log_b(a) = n^c_crit):
    Case 1: f = O(n^(c_crit - eps)) → T(n) = Theta(n^c_crit)
    Case 2: f = Theta(n^c_crit * log^k(n)) → T(n) = Theta(n^c_crit * log^(k+1)(n))
    Case 3: f = Omega(n^(c_crit + eps)) and regularity → T(n) = Theta(f(n))
- Merge Sort: T(n) = 2T(n/2) + Theta(n) → Case 2 → Theta(n log n).
  Split array at midpoint, sort each half, merge two sorted halves in O(n).
- Binary Search: T(n) = T(n/2) + O(1) → Case 2 → O(log n).
- Maximum Subarray (D&C): O(n log n). Split at mid, find max crossing subarray in O(n), recurse.
- Fast Exponentiation: x^n = (x^(n/2))^2 [even] or x*(x^((n-1)/2))^2 [odd] → O(log n).

SOCRATIC GUIDANCE:
- Have students write the recurrence before solving it.
- "How many subproblems? What size? What does the combine step cost?"
- "Which Master Theorem case? Compare f(n) to n^log_b(a) step by step."
""",
    ),
    (
        "tutorial_3",
        "Tutorial 3 — Greedy Algorithms",
        "material/lectures/Tutorial 3 (2).pdf",
        """Tutorial 3: Greedy Algorithms.

CURRICULUM:
- Greedy strategy: at each step make the locally optimal (greedy) choice.
- Two conditions needed to prove correctness:
    1. Greedy Choice Property: the greedy choice is part of some optimal solution.
    2. Optimal Substructure: optimal solution to subproblem extends to full optimum.
- Exchange Argument (main proof technique):
    Take an optimal solution O that differs from greedy G at the first point.
    Show swapping O's choice with G's choice produces a solution that is at least as good.
    Conclude the greedy choice is always safe by induction.
- Interval Scheduling ("Scheduling all Intervals"):
    Input: n intervals with start/finish times. Goal: select max non-overlapping set.
    Greedy: sort by finish time, always pick the interval that finishes earliest.
    Proof: exchange argument — swapping first interval with earliest-finish never creates more conflicts.
    Time: O(n log n).
- Interval Partitioning (min rooms / coloring):
    Greedy: process by start time, assign to any compatible room, else open new room.
    Optimal number of rooms = depth (max overlapping intervals at any point).

SOCRATIC GUIDANCE:
- Before accepting any greedy: "Can you construct a counterexample?"
- "What is the exchange argument? What happens if you swap the greedy choice with the optimal one?"
- "After making the greedy choice, what smaller problem remains?"
""",
    ),
    (
        "tutorial_4",
        "Tutorial 4 — Dynamic Programming",
        "material/lectures/Tutorial 4 (2).pdf",
        """Tutorial 4: Dynamic Programming (DP) — Introduction.

CURRICULUM:
- DP applies when: (1) overlapping subproblems, (2) optimal substructure.
- DP recipe: (1) Define the subproblem. (2) Write the recurrence. (3) Identify base cases.
  (4) Fill the table in bottom-up order. (5) Extract the answer.

- Fibonacci Sequence (canonical DP example):
    Problem: compute F(n) where F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2).
    Naive recursion: T(n) = T(n-1) + T(n-2) + O(1) → O(2^n). Exponential — terrible.
    Why? The same subproblems (e.g. F(3)) are recomputed exponentially many times.
    DP solution (memoization / tabulation):
      Create array dp[0..n]. Set dp[0]=0, dp[1]=1.
      For i from 2 to n: dp[i] = dp[i-1] + dp[i-2].
      Return dp[n].
    Time: O(n). Space: O(n). Can reduce to O(1) space using just two variables (prev, curr).
    Key insight: store each subproblem result once → each of n subproblems solved in O(1) → O(n) total.

- Longest Increasing Subsequence (LIS):
    Subproblem: dp[i] = length of longest increasing subsequence ending at index i.
    Recurrence: dp[i] = 1 + max(dp[j]) for all j < i where A[j] < A[i]. (1 if no such j.)
    Base case: dp[i] = 1 for all i.
    Answer: max(dp[i]) for i in 0..n-1.
    Time: O(n^2). Space: O(n).

- Minimum Vertex Cover on Trees:
    dp[v][0] = min cover of subtree rooted at v, NOT including v.
    dp[v][1] = min cover of subtree rooted at v, including v.
    For each child c: dp[v][0] += dp[c][1]; dp[v][1] += min(dp[c][0], dp[c][1]).
    Base (leaf): dp[leaf][0]=0, dp[leaf][1]=1.

SOCRATIC GUIDANCE:
- NEVER give the recurrence or code directly.
- "What is the subproblem? What does dp[i] represent exactly?"
- "What is the time complexity of the naive recursion? Why is it so slow? What causes the redundant work?"
- "If you store each fib(i) the first time, how many unique subproblems are there?"
- For Fibonacci: lead student from O(2^n) to O(n) through questions about subproblem overlap.
""",
    ),
    (
        "tutorial_5",
        "Tutorial 5 — Dynamic Programming (cont.)",
        "material/lectures/Tutorial algo 5.pdf",
        """Tutorial 5: Dynamic Programming — continued (builds on Tutorial 4).

CURRICULUM:
- All Tutorial 4 concepts apply. Focus on harder DP problems.
- General technique: always identify what the "last decision" in an optimal solution is.

- Weighted Interval Scheduling:
    Sort intervals by finish time. For each interval i, let p(i) = last interval that ends before i starts.
    dp[i] = max profit considering first i intervals.
    Recurrence: dp[i] = max(dp[i-1], weight[i] + dp[p(i)]).
    Base: dp[0] = 0. Time: O(n log n) (sort + binary search for p(i)).

- Edit Distance (Levenshtein):
    dp[i][j] = min edits to convert A[1..i] to B[1..j].
    If A[i]==B[j]: dp[i][j] = dp[i-1][j-1].
    Else: dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                         (delete, insert, replace).
    Base: dp[i][0] = i, dp[0][j] = j.

- Matrix Chain Multiplication:
    dp[i][j] = min multiplications for A_i * ... * A_j.
    dp[i][j] = min over k: dp[i][k] + dp[k+1][j] + dim[i-1]*dim[k]*dim[j].
    Base: dp[i][i] = 0. Fill by increasing interval length.

- Solution Reconstruction: store parent/choice pointers during DP fill. Trace back from answer.

SOCRATIC GUIDANCE:
- "What is the last step/decision in an optimal solution?"
- "What dimensions does your DP table need? What does each dimension represent?"
- "How would you trace back through the table to find the actual solution, not just the cost?"
""",
    ),
    (
        "tutorial_6",
        "Tutorial 6 — DP: Partition & Combinatorics",
        "material/lectures/Tutorial algo 6.pdf",
        """Tutorial 6: Dynamic Programming — Partition and Counting Problems.

CURRICULUM:
- Counting how many ways to partition {1,...,n} into 2 subsets with equal sum.
  Step 1: check total sum is even (otherwise impossible).
  Step 2: run subset sum DP with target = total_sum / 2.
  Step 3: count paths to target using counting variant.

- Subset Sum (decision version):
    dp[i][s] = True if some subset of {A[1],...,A[i]} sums to s.
    Recurrence: dp[i][s] = dp[i-1][s] OR (s>=A[i] AND dp[i-1][s-A[i]]).
    Base: dp[0][0]=True, dp[0][s]=False for s>0.
    Time: O(n*T). Space: O(n*T) or O(T) with rolling array.

- Counting version (how many subsets sum to T):
    Replace OR with +: dp[i][s] = dp[i-1][s] + dp[i-1][s-A[i]].

- Number of Paths in a DAG:
    Topological sort the DAG. dp[v] = number of paths from source to v.
    dp[source] = 1. For each vertex u in topo order: for each edge (u,v): dp[v] += dp[u].
    Time: O(V + E).

- Partition into 2 equal subsets (equal partition):
    Special case of subset sum: find subset that sums to total/2.
    Number of such partitions: dp[n][total/2] / 2 (each partition counted twice).

SOCRATIC GUIDANCE:
- "What are the two dimensions of the DP table? What does dp[i][j] mean precisely?"
- "When you consider the i-th element, what are your two choices (include or exclude)?"
- "Is this problem asking can we? or how many ways? — how does that change the recurrence?"
""",
    ),
    (
        "tutorial_7",
        "Tutorial 7 — Minimum Spanning Trees",
        "material/lectures/Tutorial algo 7.pdf",
        """Tutorial 7: Minimum Spanning Trees (MST).

CURRICULUM:
- Spanning tree: connects all V vertices with V-1 edges, no cycles.
- MST: spanning tree with minimum total edge weight.

- Cut Property (safe edge theorem):
    A "cut" partitions vertices into two non-empty sets (S, V-S).
    The minimum-weight edge crossing any cut is in every MST.
    Used to prove greedy MST algorithms correct.

- Cycle Property:
    The maximum-weight edge in any simple cycle is NOT in any MST.

- Kruskal's Algorithm:
    1. Sort all edges by weight: O(E log E).
    2. Process edges in order: add edge (u,v) if u and v are in different components.
    3. Use Union-Find to track components.
    Total time: O(E log E) = O(E log V).
    Correctness: each added edge is the lightest crossing some cut (cut property).

- Prim's Algorithm:
    1. Start with any vertex s, set key[s]=0, key[v]=inf for others.
    2. Repeatedly extract the minimum-key vertex, add it to MST, update neighbors' keys.
    3. Use min-priority queue.
    Time: O(E log V) with binary heap.

- Union-Find (Disjoint Set Union):
    find(x): returns root of x's set (with path compression).
    union(x,y): merges sets of x and y (union by rank).
    Amortized O(alpha(n)) per operation.

SOCRATIC GUIDANCE:
- "What does the cut property guarantee? What makes an edge safe to add?"
- "In Kruskal's, when you add edge (u,v), what cut does it cross? Why is it the minimum?"
- "How does Union-Find help detect if adding an edge creates a cycle in O(log n)?"
""",
    ),
    (
        "tutorial_8",
        "Tutorial 8 — Shortest Paths",
        "material/lectures/Tutorial algo 8.pdf",
        """Tutorial 8: Shortest Path Algorithms.

CURRICULUM:
- Relaxation (fundamental operation): for edge (u,v,w), if dist[v] > dist[u]+w, set dist[v]=dist[u]+w.

- Dijkstra's Algorithm (non-negative weights only):
    Initialize: dist[s]=0, dist[v]=inf for all v≠s.
    Repeat V times: extract vertex u with minimum dist[u] (not yet finalized).
    Relax all edges out of u.
    Time: O(E log V) with binary heap, O(E + V log V) with Fibonacci heap.
    Correctness: when u is extracted, dist[u] is final (greedy argument with non-negative weights).
    WHY IT FAILS with negative edges: a future negative edge could make dist[u] smaller
    after u was already finalized — Dijkstra never revisits finalized vertices.
    Example of failure: s→u (weight 2), s→v (weight 4), v→u (weight -5).
    Dijkstra gives dist[u]=2, true answer is dist[u]=-1.

- Bellman-Ford Algorithm (handles negative weights, detects negative cycles):
    Initialize: dist[s]=0, dist[v]=inf.
    Relax ALL E edges, V-1 times.
    Why V-1? Shortest path uses at most V-1 edges (if no negative cycles).
    After iteration k, dist[v] = shortest path using at most k edges.
    Negative cycle detection: run one more (V-th) iteration. If any dist improves → negative cycle.
    Time: O(V*E). Space: O(V).

- APSP (All-Pairs Shortest Paths):
    Run Dijkstra from every vertex: O(V * E log V).
    Floyd-Warshall: O(V^3), handles negative edges (no negative cycles).
    Johnson's Algorithm: reweight to remove negatives, then run Dijkstra from every vertex.

SOCRATIC GUIDANCE:
- "What is relaxation? When do you relax an edge, and what does it mean?"
- "Why is Dijkstra's greedy choice (minimum dist vertex) safe with non-negative weights?"
- "Give me an example where Dijkstra gives the wrong answer with negative edges."
- "After V-1 iterations of Bellman-Ford, what does a successful V-th relaxation imply?"
""",
    ),
]

# ── Ingestion ─────────────────────────────────────────────────────────────────

MIN_CHUNK_WORDS = 20  # drop slide-title-only noise

def ingest(hw_id, display_name, pdf_path, topic_context):
    path = ROOT / pdf_path
    if not path.exists():
        print(f"  SKIP — not found: {path}")
        return 0, 0

    db_path = DB_DIR / hw_id
    if db_path.exists():
        shutil.rmtree(db_path)

    pages  = PyPDFLoader(str(path)).load()
    raw    = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=250
    ).split_documents(pages)

    chunks  = [c for c in raw if len(c.page_content.split()) >= MIN_CHUNK_WORDS]
    dropped = len(raw) - len(chunks)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(db_path),
    )
    return len(chunks), dropped


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    meta = json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}

    total_chunks = total_dropped = 0
    for hw_id, display_name, pdf_path, topic_context in MATERIAL:
        print(f"-> [{hw_id}]  {display_name}")
        n, dropped = ingest(hw_id, display_name, pdf_path, topic_context)
        if n:
            meta[hw_id] = {"display_name": display_name, "topic_context": topic_context}
            total_chunks  += n
            total_dropped += dropped
            print(f"   OK  {n} chunks kept, {dropped} noise chunks removed\n")

    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done. {len(meta)} tutorials, {total_chunks} chunks total "
          f"({total_dropped} noise chunks removed).")


if __name__ == "__main__":
    main()

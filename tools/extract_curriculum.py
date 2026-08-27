"""
extract_curriculum.py
Reads each tutorial PDF (Hebrew slides), combines the slide fragments with known
topic context, and asks gpt-4o-mini to generate comprehensive English curriculum
notes — including worked examples and typical exercises.

Run once (uses ~$0.05 of API tokens total):
    python extract_curriculum.py

Output: material/english/tutorial_N.txt  for each tutorial.
"""
import os, warnings
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

ROOT        = Path(__file__).parent
OUT_DIR     = ROOT / "material" / "english"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM (uses GitHub token already configured) ────────────────────────────────
from langchain_openai import ChatOpenAI

gh_token = os.getenv("GITHUB_TOKEN", "")
llm = ChatOpenAI(
    model      = "gpt-4o-mini",
    api_key    = gh_token if gh_token else os.getenv("OPENAI_API_KEY"),
    base_url   = "https://models.inference.ai.azure.com" if gh_token else None,
    temperature= 0,
    max_tokens = 4000,
)

# ── Topic knowledge (same as in bulk_ingest.py — the ground truth) ────────────
TOPIC_KNOWLEDGE = {
"tutorial_1": """
Tutorial 1 — Algorithm Analysis & Asymptotic Notation
- Big-O: f(n)=O(g(n)) iff ∃c,n₀: f(n)≤c·g(n) ∀n≥n₀
- Omega (Ω): lower bound. Theta (Θ): tight (both O and Ω).
- Hierarchy: O(1)<O(log n)<O(n)<O(n log n)<O(n²)<O(2ⁿ)<O(n!)
- Counting operations: loops multiply; nested loops multiply all levels.
- Insertion sort O(n²) worst, O(n) best. Selection/Bubble always O(n²).
- Formal limit definitions: f=O(g) iff limsup f/g < ∞.
""",
"tutorial_2": """
Tutorial 2 — Divide & Conquer
- Pattern: divide into a subproblems of size n/b, combine in f(n) → T(n)=aT(n/b)+f(n).
- Master Theorem (k=log_b a):
    Case 1: f=O(n^(k-ε))       → T=Θ(n^k)
    Case 2: f=Θ(n^k·log^p n)   → T=Θ(n^k·log^(p+1) n)
    Case 3: f=Ω(n^(k+ε))+reg.  → T=Θ(f(n))
- Merge sort: T=2T(n/2)+O(n) → O(n log n).
- Binary search: T=T(n/2)+O(1) → O(log n).
- Karatsuba: T=3T(n/2)+O(n) → O(n^log₂3)≈O(n^1.585).
""",
"tutorial_3": """
Tutorial 3 — Greedy Algorithms
- Greedy: always take locally optimal choice. Needs: (1) greedy choice property + (2) optimal substructure.
- Exchange argument: show swapping OPT's choice for greedy's choice doesn't hurt.
- Activity selection: sort by finish time → always take earliest-finishing compatible activity. O(n log n).
- Fractional knapsack: sort by value/weight descending. O(n log n). WORKS.
- 0/1 knapsack: greedy FAILS → needs DP.
- Huffman coding: min-heap, merge two smallest frequencies. O(n log n).
- Counterexample for generic greedy: denominations {1,3,4}, target 6 → greedy 4+1+1=3 coins but optimal 3+3=2.
""",
"tutorial_4": """
Tutorial 4 — Dynamic Programming (DP)
- Applies when: overlapping subproblems + optimal substructure.
- Steps: (1) define subproblem, (2) recurrence, (3) base cases, (4) order, (5) extract answer.
- FIBONACCI: F(0)=0,F(1)=1,F(n)=F(n-1)+F(n-2). Naive O(2^n). DP: dp[i]=dp[i-1]+dp[i-2], O(n) time O(n) space. Optimized: two variables, O(1) space.
- ROD CUTTING: dp[i]=max(p[j]+dp[i-j]) for j=1..i. O(n²).
- LCS: dp[i][j]=dp[i-1][j-1]+1 if match, else max(dp[i-1][j],dp[i][j-1]). O(mn).
- 0/1 KNAPSACK: dp[i][w]=max(dp[i-1][w], dp[i-1][w-wt[i]]+val[i]). O(nW).
""",
"tutorial_5": """
Tutorial 5 — Dynamic Programming (continued)
- COIN CHANGE: dp[i]=min(dp[i-coin]+1). O(amount×coins).
- MATRIX CHAIN: dp[i][j]=min over k of dp[i][k]+dp[k+1][j]+p[i-1]·p[k]·p[j]. O(n³).
- EDIT DISTANCE: dp[i][j]=dp[i-1][j-1] if match, else 1+min(del,ins,rep). O(mn).
- LIS: dp[i]=1+max(dp[j] for j<i,A[j]<A[i]). O(n²) naive, O(n log n) with patience.
- Solution reconstruction: parent array traces optimal choices.
""",
"tutorial_6": """
Tutorial 6 — DP: Subsets, Partition, Counting
- SUBSET SUM: dp[i][s]=dp[i-1][s] OR dp[i-1][s-A[i]] (if s≥A[i]). O(nS).
- PARTITION INTO EQUAL SUBSETS: check sum is even; reduce to subset sum with target=sum/2.
- COUNT SUBSETS: dp[i][s]=dp[i-1][s]+dp[i-1][s-A[i]]. O(nS).
- GRID PATHS: dp[i][j]=dp[i-1][j]+dp[i][j-1]. dp[0][j]=dp[i][0]=1.
""",
"tutorial_7": """
Tutorial 7 — Minimum Spanning Trees (MST)
- Cut property: cheapest edge crossing any cut is in some MST.
- Cycle property: most expensive edge in any cycle is NOT in any MST.
- KRUSKAL: sort edges by weight, add if no cycle (Union-Find). O(E log E).
- PRIM: grow tree from vertex, min-heap of candidate edges. O(E log V).
- UNION-FIND: path compression + union by rank → amortized O(α(n))≈O(1).
""",
"tutorial_8": """
Tutorial 8 — Shortest Paths
- RELAXATION: if d[u]+w(u,v)<d[v]: d[v]=d[u]+w(u,v).
- DIJKSTRA: O((V+E)log V), min-heap. NON-NEGATIVE weights only. Once extracted → distance is final.
- Why Dijkstra fails on negative edges: extracted vertex may later get a shorter path.
- BELLMAN-FORD: relax all edges V-1 times. O(VE). Handles negatives. Detects negative cycles.
- Negative cycle detection: if any d[u]+w<d[v] after V-1 rounds → negative cycle.
- DAG shortest path: topological order + relax. O(V+E).
- FLOYD-WARSHALL: dp[k][i][j]=min(dp[k-1][i][j], dp[k-1][i][k]+dp[k-1][k][j]). O(V³).
""",
}

# ── Cumulative prerequisites ───────────────────────────────────────────────────
PREREQUISITES = {
    "tutorial_1": "No prerequisites.",
    "tutorial_2": "Prerequisites covered: Big-O/Omega/Theta notation, O(n²) sorting (Tutorial 1).",
    "tutorial_3": "Prerequisites covered: asymptotic notation (T1), Divide & Conquer, Master Theorem (T2).",
    "tutorial_4": "Prerequisites covered: asymptotic notation (T1), D&C + Master Theorem (T2), Greedy algorithms (T3).",
    "tutorial_5": "Prerequisites covered: T1–T3 + basic DP (Fibonacci, LCS, Knapsack) (Tutorial 4).",
    "tutorial_6": "Prerequisites covered: T1–T4 + advanced DP (coin change, edit distance, LIS) (Tutorial 5).",
    "tutorial_7": "Prerequisites covered: T1–T5 + DP on subsets (Tutorial 6).",
    "tutorial_8": "Prerequisites covered: T1–T6 + MST (Kruskal, Prim) (Tutorial 7).",
}

# ── Tutorials to process ──────────────────────────────────────────────────────
TUTORIALS = [
    ("tutorial_1", "material/lectures/Tutorial 1 (2).pdf"),
    ("tutorial_2", "material/lectures/Tutorial 2 (2).pdf"),
    ("tutorial_3", "material/lectures/Tutorial 3 (2).pdf"),
    ("tutorial_4", "material/lectures/Tutorial 4 (2).pdf"),
    ("tutorial_5", "material/lectures/Tutorial algo 5.pdf"),
    ("tutorial_6", "material/lectures/Tutorial algo 6.pdf"),
    ("tutorial_7", "material/lectures/Tutorial algo 7.pdf"),
    ("tutorial_8", "material/lectures/Tutorial algo 8.pdf"),
]


def extract_slide_text(pdf_path: str) -> str:
    """Extract raw text from all PDF pages, skip blank/very short pages."""
    from langchain_community.document_loaders import PyPDFLoader
    pages = PyPDFLoader(str(ROOT / pdf_path)).load()
    lines = []
    for i, page in enumerate(pages):
        text = page.page_content.strip()
        if len(text) >= 20:
            lines.append(f"[Slide {i+1}] {text}")
    return "\n".join(lines)


def generate_curriculum_notes(hw_id: str, slide_text: str) -> str:
    topic     = TOPIC_KNOWLEDGE[hw_id]
    prereqs   = PREREQUISITES[hw_id]

    prompt = f"""You are building comprehensive English curriculum notes for a university algorithm course.

ALGORITHM KNOWLEDGE FOR THIS TUTORIAL:
{topic}

{prereqs}

SLIDE TEXT (Hebrew + fragments extracted from the actual presentation):
{slide_text[:6000]}

Your task:
1. Using the algorithm knowledge above as the authoritative source, write COMPREHENSIVE English lecture notes.
2. Include ALL algorithms with pseudocode, recurrences, and complexity analysis.
3. Extract and translate any exercise problems or examples visible in the slides.
4. Add 4-6 TYPICAL EXAM/EXERCISE QUESTIONS with worked solutions that a student at this level would face.
5. List key theorems and definitions precisely.
6. Note which concepts from prior tutorials are used as prerequisites.

Format the output as structured lecture notes with clear sections:
# [Tutorial Title]
## Core Concepts
## Algorithms & Complexity
## Theorems & Proofs
## Worked Examples
## Practice Problems (with solutions)
## Common Mistakes to Avoid

Write in clear English. Be comprehensive — this will be the primary reference for an AI tutor."""

    response = llm.invoke(prompt)
    return response.content


def main():
    for hw_id, pdf_path in TUTORIALS:
        out_file = OUT_DIR / f"{hw_id}.txt"
        print(f"\n→ {hw_id} ({pdf_path})")

        print("  Extracting slides...")
        slide_text = extract_slide_text(pdf_path)
        print(f"  {len(slide_text)} chars extracted")

        print("  Generating English curriculum notes (API call)...")
        notes = generate_curriculum_notes(hw_id, slide_text)
        out_file.write_text(notes, encoding="utf-8")
        print(f"  ✓ Saved to {out_file.relative_to(ROOT)} ({len(notes)} chars)")

    print("\n\nAll tutorials processed. Run bulk_ingest.py to rebuild the database.")


if __name__ == "__main__":
    main()

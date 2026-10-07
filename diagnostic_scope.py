"""Comprehensive scope gating diagnostic"""
from rag_engine import HybridRetriever, EMBED_MODEL, SCOPE_SIM_FLOOR, SCOPE_SIM_MARGIN
from curriculum import load_curriculum, covered_topics, named_future_topic, topic_mentions

curriculum = load_curriculum()

print("="*70)
print("SCOPE GATING DIAGNOSTIC")
print("="*70)

print(f"\nConfig:")
print(f"  SCOPE_SIM_FLOOR (min similarity for future match): {SCOPE_SIM_FLOOR}")
print(f"  SCOPE_SIM_MARGIN (future must be this much higher): {SCOPE_SIM_MARGIN}")

week = 1
print(f"\n--- Testing at Week {week} ---")
print(f"Covered topics: {len(covered_topics(week))}")

# Build retriever
retriever = HybridRetriever(EMBED_MODEL)

# Test questions
test_cases = [
    ("What is merge sort?", "Should block: week 2"),
    ("Explain the DFS algorithm", "Should block: week 6"),
    ("Tell me about Dijkstra's algorithm", "Should block: week 8"),
    ("What's the maximum flow problem?", "Should block: week 9"),
    ("How do I prove algorithm correctness?", "Should allow: week 1"),
    ("What is pseudocode?", "Should allow: week 1"),
    ("How do I analyze running time?", "Should allow: week 1"),
]

print("\n" + "="*70)
print("SCOPE CHECK RESULTS")
print("="*70)

for question, expectation in test_cases:
    print(f"\n❓ {question}")
    print(f"   Expected: {expectation}")
    
    # Explicit topic check
    future_week_explicit = named_future_topic(question, week)
    if future_week_explicit:
        print(f"   ✗ BLOCKED by explicit topic: '{[m['name'] for m in topic_mentions(question) if m['week'] > week and not m['excluded']][0]}' (week {future_week_explicit})")
        continue
    
    # Similarity-based check
    is_future, required_week = retriever.scope_check(question, week)
    if is_future:
        print(f"   ✗ BLOCKED by similarity check: closest future material is week {required_week}")
    else:
        print(f"   ✓ ALLOWED: no out-of-scope material detected")

print("\n" + "="*70)

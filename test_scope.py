"""Test scope gating with sample questions"""
import sys
sys.path.insert(0, '/home/user/tutor-bot')

from rag_engine import HybridRetriever, build_index, load_course_chunks, EMBED_MODEL
from curriculum import load_curriculum, covered_topics, named_future_topic

# Load curriculum
curriculum = load_curriculum()
print(f"Curriculum loaded: {len(curriculum['weeks'])} weeks")

# Check week 1 topics
week1_topics = covered_topics(1)
print(f"\n=== Week 1 Topics ({len(week1_topics)}) ===")
for t in sorted(week1_topics)[:10]:
    print(f"  - {t}")

# Test future topic detection
test_questions = [
    "What is Dijkstra's algorithm?",  # Should be future (week 5+)
    "Explain merge sort",  # Should be week 2
    "What is DFS?",  # Should be week 3
    "How do I solve the maximum flow problem?",  # Should be future
]

print("\n=== Scope Gate Test ===")
for q in test_questions:
    future_week = named_future_topic(q, week=1)
    print(f"Q: {q}")
    print(f"  → Future week: {future_week if future_week else 'IN SCOPE (week 1)'}")

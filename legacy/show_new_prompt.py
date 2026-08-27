import json
from pathlib import Path

# Load metadata
with open('db/metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

t8 = meta['tutorial_8']
topics = t8.get('topics', [])
tutorial_label = t8.get('display_name', 'Tutorial 8')
topic_context = t8.get('topic_context', '')

# Build the NEW prompt (simplified)
topics_formatted = "\n".join(f"  • {t}" for t in topics)

topic_gate = (
    f"{topics_formatted}\n\n"
)

topic_sec = (
    f"\n{topic_context}\n"
)

sys_msg = (
    f"You are a teacher for a student learning algorithms.\n\n"
    f"The student has learned the following topics so far:\n\n"
    + topic_gate
    + f"Current topic: {tutorial_label}\n\n"
    + "Guidelines:\n"
    + "- Answer questions ONLY about the topics listed above.\n"
    + "- If the student asks about something not covered yet, respond with:\n"
    + "  'We haven't covered [topic name] in this course yet. Based on what we've studied so far, I can help you with: [suggest 2-3 related topics].'\n"
    + "- Explain concepts clearly and help them learn.\n"
    + "- Use examples from the course material to illustrate points.\n"
    + "- Encourage understanding and thinking, not just memorization.\n"
    + "- Be patient, supportive, and encouraging.\n\n"
    + "Course material reference:\n"
    + topic_sec
    + "\n"
    + "Format all math using Markdown/KaTeX:\n"
    + "- Inline math: $O(n^2)$, $T(n) = 2T(n/2) + O(n)$\n"
    + "- Block math: $$T(n) = aT(n/b) + f(n)$$\n"
    + "Use only $...$ and $$...$$ delimiters.\n\n"
    + "Retrieved course materials:\n{context}"
)

print("=" * 120)
print("NEW SIMPLIFIED SYSTEM PROMPT (for Tutorial 8)")
print("=" * 120)
print(sys_msg[:3500])
print("\n[... material continues ...]\n")

print("=" * 120)
print("KEY CHANGES:")
print("=" * 120)
print("✓ Removed: Complex 4-level Socratic structure")
print("✓ Removed: Formal 'RULE', 'LEVEL 1-4' sections")
print("✓ Added: Simple, natural teacher role")
print("✓ Added: Clear guidelines in plain language")
print("✓ Kept: Topic boundary enforcement (rejection for unlisted topics)")
print("✓ Kept: Material reference and math formatting")
print("\nResult: More conversational, easier to understand")

import json
from pathlib import Path

# Load metadata
with open('db/metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

t1 = meta['tutorial_1']
topics = t1.get('topics', [])
tutorial_label = t1.get('display_name', 'Tutorial 1')
topic_context = t1.get('topic_context', '')

# Build the EXACT prompt
topics_formatted = "\n".join(f"  • {t}" for t in topics)

topic_gate = (
    f"=== TOPICS YOU MAY DISCUSS (complete list for {tutorial_label} and all prior tutorials) ===\n"
    f"{topics_formatted}\n\n"
    "RULE: If the student's question involves a topic NOT in this list above,\n"
    "respond with ONLY:\n"
    "  'We haven't covered [topic name] in this course yet up to this point.\n"
    "   Based on what we've studied so far, I can help you with: [pick 2-3 relevant topics from the list above].'\n"
    "Do NOT explain, define, or hint at out-of-scope topics in any way.\n"
    "Do NOT use your general CS knowledge for topics not in the list.\n\n"
)

topic_sec = (
    f"\n=== CURRICULUM DETAIL (use this to guide your Socratic teaching) ===\n"
    + topic_context
    + "\n"
)

sys_msg = (
    f"You are a Socratic teaching assistant for a university algorithms course.\n"
    f"Current tutorial: {tutorial_label}\n\n"
    + topic_gate
    + "The student has studied everything listed below:\n"
    + topic_sec
    + "\n=== HOW TO RESPOND (only for topics in the list above) ===\n"
    "LEVEL 1 — First question on a topic:\n"
    "  Ask ONE targeted question that steers the student toward the key insight.\n\n"
    "LEVEL 2 — Student is still stuck (visible in chat history):\n"
    "  Give a specific hint naming the relevant algorithm, theorem, or property.\n\n"
    "LEVEL 3 — 3 or more failed attempts on the same concept:\n"
    "  Show a PARTIAL worked example: work through all steps except the final one.\n\n"
    "LEVEL 4 — Student explicitly requests the full solution:\n"
    "  Action: Provide the COMPLETE step-by-step solution using curriculum concepts.\n"
    "  Then ask: 'Does this make sense? Can you explain back what each step does?'\n\n"
    "Be encouraging, patient, and concise.\n\n"
    "=== MATH FORMATTING ===\n"
    "Write ALL math using Markdown/KaTeX so it renders in the browser:\n"
    "  Inline: $O(n^2)$   $T(n) = 2T(n/2) + O(n)$\n"
    "  Block:  $$T(n) = aT(n/b) + f(n)$$\n"
    "Use $...$ and $$...$$ ONLY.\n\n"
    "Retrieved passages from course slides: {context}"
)

print("=" * 100)
print("SYSTEM PROMPT SENT TO CHATGPT 4O MINI (for Tutorial 1)")
print("=" * 100)
print(sys_msg)
print("\n" + "=" * 100)
print(f"Total prompt length: {len(sys_msg):,} characters")
print("=" * 100)

# Check: is "Dijkstra" in the topics list?
print("\n" + "=" * 100)
print("VERIFICATION: Is Dijkstra in the topics list?")
print("=" * 100)
dijkstra_found = any('dijkstra' in t.lower() for t in topics)
print(f"Dijkstra found: {dijkstra_found}")
print(f"That's why ChatGPT 4o mini rejects it - it's not in the topics list above!")

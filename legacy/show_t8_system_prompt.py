import json
from pathlib import Path

# Load metadata
with open('db/metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

t8 = meta['tutorial_8']
topics = t8.get('topics', [])
tutorial_label = t8.get('display_name', 'Tutorial 8')
topic_context = t8.get('topic_context', '')

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
)

print("=" * 120)
print("SYSTEM PROMPT SENT TO CHATGPT 4O MINI (for Tutorial 8)")
print("=" * 120)
print(sys_msg[:5000])  # Print first 5000 chars
print("\n[... CURRICULUM DETAIL SECTION CONTINUES ...]")

print("\n" + "=" * 120)
print("VERIFICATION: Does T8 topics list include Dijkstra?")
print("=" * 120)

dijkstra_found = any('dijkstra' in t.lower() for t in topics)
print(f"✓ Dijkstra found in T8: {dijkstra_found}")

# Show which Dijkstra-related topics are in T8
print("\nDijkstra-related topics in T8:")
dijkstra_topics = [t for t in topics if 'dijkstra' in t.lower() or 'shortest path' in t.lower()]
for topic in dijkstra_topics:
    print(f"  • {topic}")

# Verify cumulative nature - check if T1 topics are also in T8
print("\n" + "=" * 120)
print("VERIFICATION: Is T8 cumulative (includes T1 topics)?")
print("=" * 120)

with open('db/metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

t1_topics = meta['tutorial_1'].get('topics', [])
t1_count = len(t1_topics)
t8_topics = meta['tutorial_8'].get('topics', [])
t8_count = len(t8_topics)

print(f"T1 has {t1_count} topics")
print(f"T8 has {t8_count} topics (cumulative)")

# Check if all T1 topics are in T8
all_t1_in_t8 = all(t in t8_topics for t in t1_topics)
print(f"✓ All T1 topics included in T8: {all_t1_in_t8}")

if all_t1_in_t8:
    print("\nT1 sample topics in T8:")
    for topic in t1_topics[:5]:
        print(f"  • {topic}")

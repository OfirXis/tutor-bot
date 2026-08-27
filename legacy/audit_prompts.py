import json

meta = json.loads(open("db/metadata.json", encoding="utf-8").read())

for tid in [f"tutorial_{i}" for i in range(1, 9)]:
    hw_info = meta[tid]
    topic_context = hw_info["topic_context"]
    disp_name = hw_info["display_name"]
    safe_topic = topic_context.replace("{", "{{").replace("}", "}}")

    topic_sec = (
        f"\n=== CURRICULUM: what this student has studied (up to and including {disp_name}) ===\n"
        + safe_topic
        + "\n"
    )

    # Find all section headers that the LLM sees
    sections = []
    for line in topic_sec.split("\n"):
        s = line.strip()
        if s.startswith("## ") or s.startswith("=== ") or s.startswith("PREREQUISITES"):
            sections.append(s[:90])

    print(f"\n{'='*70}")
    print(f"{disp_name}  [{len(topic_sec)} chars in system prompt]")
    print(f"{'='*70}")
    for sec in sections:
        print(f"  {sec}")

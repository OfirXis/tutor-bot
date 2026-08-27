"""
Step 3: Transform indexed material from ChatGPT into metadata.json format.

This script:
1. Reads indexed_tutorials.json (output from process_with_llm.py)
2. Formats the topics as cumulative lists per tutorial
3. Creates full metadata.json ready for the Streamlit app
"""

import json
from pathlib import Path
from typing import Dict, List

# ─────────────────────────────────────────────────────────────────────────────
# LOAD INDEXED DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_indexed_tutorials(json_path: str) -> Dict:
    """Load the indexed tutorials from LLM output."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# BUILD CUMULATIVE TOPIC LISTS
# ─────────────────────────────────────────────────────────────────────────────

def build_cumulative_topics(indexed_data: Dict) -> Dict[str, List[str]]:
    """
    Build cumulative topic lists for each tutorial.
    
    Each tutorial gets:
    - All topics from previous tutorials (prerequisites)
    - All topics from current tutorial
    
    Returns: {tutorial_id: [list of topic names]}
    """
    cumulative_topics = {}
    all_previous_topics = []
    
    for i in range(1, 9):  # Tutorials 1-8
        tutorial_key = f"tutorial_{i}"
        
        if tutorial_key not in indexed_data:
            print(f"WARNING: {tutorial_key} not found in indexed data")
            continue
        
        data = indexed_data[tutorial_key]
        
        # Collect all topics from this tutorial
        current_topics = data.get("topics", [])
        
        # Combine previous + current (cumulative)
        cumulative = all_previous_topics + current_topics
        
        # Remove duplicates while preserving order
        seen = set()
        cumulative_unique = [t for t in cumulative if not (t in seen or seen.add(t))]
        
        cumulative_topics[tutorial_key] = cumulative_unique
        
        # Update all_previous_topics for next iteration
        all_previous_topics = cumulative_unique
        
        print(f"T{i}: {len(current_topics)} topics → {len(cumulative_unique)} cumulative")
    
    return cumulative_topics


# ─────────────────────────────────────────────────────────────────────────────
# BUILD TOPIC CONTEXT (CURRICULUM DETAIL)
# ─────────────────────────────────────────────────────────────────────────────

def build_topic_context(indexed_data: Dict, tutorial_num: int) -> str:
    """
    Build the curriculum detail section for a tutorial.
    
    This combines all algorithms, theorems, and concepts from that tutorial
    into a readable narrative format for Socratic teaching.
    """
    tutorial_key = f"tutorial_{tutorial_num}"
    data = indexed_data.get(tutorial_key, {})
    
    sections = []
    
    # Add algorithms
    algorithms = data.get("algorithms", [])
    if algorithms:
        sections.append("## Key Algorithms\n")
        for algo in algorithms:
            name = algo.get("name", "Unknown")
            complexity = algo.get("complexity", "Not specified")
            description = algo.get("description", "")
            sections.append(f"- **{name}** (Complexity: {complexity})\n  {description}\n")
    
    # Add theorems and concepts
    theorems = data.get("theorems_and_concepts", [])
    if theorems:
        sections.append("\n## Theorems and Concepts\n")
        for theorem in theorems:
            name = theorem.get("name", "Unknown")
            description = theorem.get("description", "")
            sections.append(f"- **{name}**: {description}\n")
    
    return "\n".join(sections) if sections else f"Tutorial {tutorial_num} curriculum content."


# ─────────────────────────────────────────────────────────────────────────────
# BUILD METADATA
# ─────────────────────────────────────────────────────────────────────────────

def build_metadata(
    indexed_data: Dict,
    cumulative_topics: Dict[str, List[str]]
) -> Dict:
    """Build complete metadata.json structure."""
    
    metadata = {}
    
    display_names = {
        1: "Tutorial 1 — Intro to Algorithm Analysis",
        2: "Tutorial 2 — Divide and Conquer",
        3: "Tutorial 3 — Greedy Algorithms",
        4: "Tutorial 4 — Dynamic Programming",
        5: "Tutorial 5 — Advanced DP",
        6: "Tutorial 6 — DP Optimization",
        7: "Tutorial 7 — Minimum Spanning Trees",
        8: "Tutorial 8 — Shortest Paths",
    }
    
    for i in range(1, 9):
        tutorial_key = f"tutorial_{i}"
        
        if tutorial_key not in indexed_data:
            continue
        
        # Build topic context
        topic_context = build_topic_context(indexed_data, i)
        
        # Get cumulative topics
        topics = cumulative_topics.get(tutorial_key, [])
        
        metadata[tutorial_key] = {
            "display_name": display_names[i],
            "topic_context": topic_context,
            "topics": topics
        }
    
    return metadata


# ─────────────────────────────────────────────────────────────────────────────
# SAVE METADATA
# ─────────────────────────────────────────────────────────────────────────────

def save_metadata(metadata: Dict, output_path: str):
    """Save metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved metadata to: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# BACKUP OLD METADATA
# ─────────────────────────────────────────────────────────────────────────────

def backup_old_metadata(metadata_path: str):
    """Create backup of existing metadata.json if it exists."""
    p = Path(metadata_path)
    if p.exists():
        backup_path = p.parent / f"{p.stem}_backup.json"
        p.rename(backup_path)
        print(f"✓ Backed up old metadata to: {backup_path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 90)
    print("TRANSFORMING INDEXED MATERIAL INTO METADATA.JSON")
    print("=" * 90)
    
    indexed_file = r"C:\Users\stein\tutor-bot\indexed_tutorials.json"
    metadata_file = r"C:\Users\stein\tutor-bot\db\metadata.json"
    
    # Load indexed data
    print("\n1. Loading indexed tutorials...")
    indexed_data = load_indexed_tutorials(indexed_file)
    print(f"   ✓ Loaded {len(indexed_data)} tutorials")
    
    # Build cumulative topics
    print("\n2. Building cumulative topic lists...")
    cumulative_topics = build_cumulative_topics(indexed_data)
    
    # Build metadata
    print("\n3. Building metadata structure...")
    metadata = build_metadata(indexed_data, cumulative_topics)
    print(f"   ✓ Built metadata for {len(metadata)} tutorials")
    
    # Backup old metadata
    print("\n4. Backing up old metadata...")
    backup_old_metadata(metadata_file)
    
    # Save new metadata
    print("\n5. Saving new metadata...")
    save_metadata(metadata, metadata_file)
    
    print("\n" + "=" * 90)
    print("✓ METADATA.JSON SUCCESSFULLY GENERATED")
    print("=" * 90)
    print("\nSummary:")
    for i in range(1, 9):
        key = f"tutorial_{i}"
        if key in metadata:
            topics_count = len(metadata[key]["topics"])
            print(f"  T{i}: {topics_count} cumulative topics")
    
    print("\n✓ Ready to restart the Streamlit app with new metadata!")

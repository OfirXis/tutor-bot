"""
Efficient processing of failed tutorials (T6, T7) by splitting into chunks.
Only processes tutorials that are MISSING from indexed_tutorials.json
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional
from openai import AzureOpenAI

# ─────────────────────────────────────────────────────────────────────────────
# LOAD EXISTING RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def load_existing_results() -> Dict:
    """Load already-processed tutorials from indexed_tutorials.json"""
    indexed_file = Path("indexed_tutorials.json")
    if indexed_file.exists():
        with open(indexed_file, 'r') as f:
            return json.load(f)
    return {}


def get_missing_tutorials(existing: Dict) -> list:
    """Return list of tutorial numbers that haven't been processed yet"""
    missing = []
    for i in range(1, 9):
        key = f"tutorial_{i}"
        if key not in existing:
            missing.append(i)
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# SMART TEXT CHUNKING
# ─────────────────────────────────────────────────────────────────────────────

def split_by_pages(text: str, max_chars: int = 25000) -> list:
    """
    Split text by page markers first, then by size if needed.
    This preserves semantic structure (pages = logical sections).
    """
    pages = text.split("--- Page ")
    chunks = []
    
    current_chunk = ""
    for page in pages:
        if len(current_chunk) + len(page) < max_chars:
            current_chunk += "--- Page " + page
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = "--- Page " + page
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# LLM PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def get_llm_client():
    """Initialize Azure OpenAI client"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    return AzureOpenAI(
        api_key=token,
        api_version="2024-05-01-preview",
        azure_endpoint="https://models.inference.ai.azure.com"
    )


def process_chunk_with_llm(
    client: AzureOpenAI,
    tutorial_num: int,
    chunk_num: int,
    chunk_text: str,
    total_chunks: int
) -> Optional[Dict]:
    """Send a single chunk to ChatGPT for processing"""
    
    prompt = f"""You are analyzing Tutorial {tutorial_num} (chunk {chunk_num}/{total_chunks}).

TEXT CHUNK:
{chunk_text}

EXTRACT ONLY topics, algorithms, and concepts mentioned in THIS CHUNK.
Return ONLY valid JSON (no markdown, no code blocks):

{{
  "topics": ["topic1", "topic2", ...],
  "algorithms": [{{"name": "name", "complexity": "if mentioned", "description": "brief"}}],
  "theorems_and_concepts": [{{"name": "name", "description": "brief"}}]
}}

If a section is empty, use empty arrays [].
Return ONLY JSON."""

    try:
        print(f"    [Chunk {chunk_num}/{total_chunks}] Sending to ChatGPT...", end="", flush=True)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract indexed material from tutorial chunks efficiently."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Remove markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        data = json.loads(response_text)
        print(" ✓")
        return data
        
    except json.JSONDecodeError as e:
        print(f" ✗ (JSON error)")
        return None
    except Exception as e:
        print(f" ✗ (API error: {str(e)[:30]})")
        return None


def merge_chunk_results(chunks_results: list) -> Dict:
    """Merge results from multiple chunks, removing duplicates"""
    
    merged = {
        "topics": [],
        "algorithms": [],
        "theorems_and_concepts": []
    }
    
    seen_topics = set()
    seen_algorithms = set()
    seen_theorems = set()
    
    for chunk_data in chunks_results:
        if not chunk_data:
            continue
        
        # Merge topics (deduplicate)
        for topic in chunk_data.get("topics", []):
            topic_lower = topic.lower()
            if topic_lower not in seen_topics:
                merged["topics"].append(topic)
                seen_topics.add(topic_lower)
        
        # Merge algorithms (deduplicate by name)
        for algo in chunk_data.get("algorithms", []):
            algo_name = algo.get("name", "").lower()
            if algo_name and algo_name not in seen_algorithms:
                merged["algorithms"].append(algo)
                seen_algorithms.add(algo_name)
        
        # Merge theorems (deduplicate by name)
        for theorem in chunk_data.get("theorems_and_concepts", []):
            theorem_name = theorem.get("name", "").lower()
            if theorem_name and theorem_name not in seen_theorems:
                merged["theorems_and_concepts"].append(theorem)
                seen_theorems.add(theorem_name)
    
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS MISSING TUTORIALS
# ─────────────────────────────────────────────────────────────────────────────

def process_missing_tutorials():
    """Process only the tutorials that failed (T6, T7)"""
    
    print("=" * 90)
    print("PROCESSING FAILED TUTORIALS (T6, T7) - SPLIT INTO CHUNKS")
    print("=" * 90)
    
    # Load existing
    existing = load_existing_results()
    missing = get_missing_tutorials(existing)
    
    if not missing:
        print("\n✓ All tutorials already processed!")
        return existing
    
    print(f"\n✓ Found {len(existing)} completed tutorials")
    print(f"⚠ Processing {len(missing)} missing tutorials: {missing}")
    
    client = get_llm_client()
    raw_texts_dir = Path("raw_tutorial_texts")
    
    tutorial_names = {
        6: "Tutorial 6 — DP Optimization",
        7: "Tutorial 7 — Minimum Spanning Trees",
    }
    
    # Process each missing tutorial
    for tut_num in missing:
        display_name = tutorial_names.get(tut_num, f"Tutorial {tut_num}")
        raw_file = raw_texts_dir / f"tutorial_{tut_num}_raw.txt"
        
        if not raw_file.exists():
            print(f"\n[T{tut_num}] ERROR: Raw file not found")
            continue
        
        # Load and clean text
        tutorial_text = raw_file.read_text(encoding='utf-8')
        lines = tutorial_text.split('\n')
        content_start = next((i for i, line in enumerate(lines) if line.startswith('===')), 2) + 2
        tutorial_text = '\n'.join(lines[content_start:])
        
        print(f"\n[T{tut_num}] {display_name}")
        print(f"    Size: {len(tutorial_text):,} characters")
        
        # Split into chunks
        chunks = split_by_pages(tutorial_text, max_chars=25000)
        print(f"    Chunks: {len(chunks)}")
        
        # Process each chunk
        chunk_results = []
        for chunk_num, chunk in enumerate(chunks, 1):
            result = process_chunk_with_llm(client, tut_num, chunk_num, chunk, len(chunks))
            if result:
                chunk_results.append(result)
            time.sleep(0.5)  # Rate limiting
        
        # Merge results
        merged = merge_chunk_results(chunk_results)
        
        # Add to results
        existing[f"tutorial_{tut_num}"] = {
            "tutorial_number": tut_num,
            "tutorial_name": display_name,
            "topics": merged["topics"],
            "algorithms": merged["algorithms"],
            "theorems_and_concepts": merged["theorems_and_concepts"]
        }
        
        print(f"    ✓ Merged: {len(merged['topics'])} topics, "
              f"{len(merged['algorithms'])} algorithms, "
              f"{len(merged['theorems_and_concepts'])} concepts")
        
        # Rate limiting between tutorials
        if tut_num < 8:
            time.sleep(1)
    
    return existing


# ─────────────────────────────────────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def save_results(results: Dict):
    """Save updated indexed_tutorials.json"""
    with open("indexed_tutorials.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved updated indexed_tutorials.json")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN not set")
        exit(1)
    
    results = process_missing_tutorials()
    save_results(results)
    
    print("\n" + "=" * 90)
    print("STATUS: All tutorials now indexed")
    print("=" * 90)
    for i in range(1, 9):
        key = f"tutorial_{i}"
        if key in results:
            topics = len(results[key].get("topics", []))
            print(f"  T{i}: ✓ {topics} topics")
    
    print("\nNext step: Run transform_to_metadata.py")

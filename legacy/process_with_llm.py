"""
Step 2: Send extracted tutorials to ChatGPT 4o mini for topic indexing.

This script:
1. Reads raw tutorial texts
2. Sends to gpt-4o-mini via GitHub Copilot API
3. Parses structured responses
4. Saves indexed material by tutorial number
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional
from openai import AzureOpenAI

# ─────────────────────────────────────────────────────────────────────────────
# INITIALIZE LLM CLIENT
# ─────────────────────────────────────────────────────────────────────────────

def get_llm_client():
    """Initialize Azure OpenAI client (GitHub Copilot backend)."""
    return AzureOpenAI(
        api_key=os.environ.get("GITHUB_TOKEN"),
        api_version="2024-05-01-preview",
        azure_endpoint="https://models.inference.ai.azure.com"
    )


# ─────────────────────────────────────────────────────────────────────────────
# INDEXING PROMPT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def get_indexing_prompt(tutorial_num: int, display_name: str, tutorial_text: str) -> str:
    """Create a structured prompt for extracting indexed material."""
    
    # Aggressively reduce text to fit within token limits
    # Aim for ~25k characters which is safer for 4o-mini (8k tokens max)
    limited_text = tutorial_text[:25000]
    if len(tutorial_text) > 25000:
        limited_text += f"\n[Content continues...]"
    
    return f"""Extract topics and algorithms from Tutorial {tutorial_num}.

MATERIAL:
{limited_text}

Return ONLY this JSON (no markdown, no extra text):
{{
  "tutorial_number": {tutorial_num},
  "topics": ["topic1", "topic2", ...],
  "algorithms": [{{"name": "algo", "complexity": "O(n)", "description": "brief"}}],
  "theorems_and_concepts": [{{"name": "concept", "description": "brief"}}]
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def process_tutorial_with_llm(
    client: AzureOpenAI,
    tutorial_num: int,
    display_name: str,
    tutorial_text: str,
    retry_count: int = 3
) -> Optional[Dict]:
    """Send tutorial to ChatGPT 4o mini and get indexed material."""
    
    prompt = get_indexing_prompt(tutorial_num, display_name, tutorial_text)
    
    for attempt in range(retry_count):
        try:
            print(f"\n[T{tutorial_num}] Sending to ChatGPT 4o mini (attempt {attempt + 1})...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract topics and algorithms. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from response
            # Sometimes the LLM wraps JSON in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            indexed_data = json.loads(response_text)
            print(f"      ✓ Successfully indexed {len(indexed_data.get('topics', []))} topics")
            return indexed_data
            
        except json.JSONDecodeError as e:
            print(f"      ✗ JSON parse error (attempt {attempt + 1}): {e}")
            if attempt == retry_count - 1:
                print(f"      Failed to parse response for T{tutorial_num}")
                return None
            time.sleep(2)
            
        except Exception as e:
            print(f"      ✗ API error: {e}")
            if attempt == retry_count - 1:
                return None
            time.sleep(3)
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PROCESSING LOOP
# ─────────────────────────────────────────────────────────────────────────────

def process_all_tutorials() -> Dict:
    """Process all 8 tutorials with ChatGPT 4o mini."""
    
    print("=" * 90)
    print("SENDING TUTORIALS TO CHATGPT 4O MINI FOR INDEXING")
    print("=" * 90)
    
    # Load raw texts
    raw_texts_dir = Path(r"C:\Users\stein\tutor-bot\raw_tutorial_texts")
    
    tutorial_files = [
        (1, "Tutorial 1 — Intro to Algorithm Analysis"),
        (2, "Tutorial 2 — Divide and Conquer"),
        (3, "Tutorial 3 — Greedy Algorithms"),
        (4, "Tutorial 4 — Dynamic Programming"),
        (5, "Tutorial 5 — Advanced DP"),
        (6, "Tutorial 6 — DP Optimization"),
        (7, "Tutorial 7 — Minimum Spanning Trees"),
        (8, "Tutorial 8 — Shortest Paths"),
    ]
    
    client = get_llm_client()
    indexed_results = {}
    
    for tut_num, display_name in tutorial_files:
        # Read raw text
        raw_file = raw_texts_dir / f"tutorial_{tut_num}_raw.txt"
        if not raw_file.exists():
            print(f"\n[T{tut_num}] ERROR: Raw text file not found: {raw_file}")
            continue
        
        tutorial_text = raw_file.read_text(encoding='utf-8')
        
        # Remove header to get just the content
        lines = tutorial_text.split('\n')
        content_start = next((i for i, line in enumerate(lines) if line.startswith('===')), 2) + 2
        tutorial_text = '\n'.join(lines[content_start:])
        
        # Process with LLM
        result = process_tutorial_with_llm(client, tut_num, display_name, tutorial_text)
        
        if result:
            indexed_results[f"tutorial_{tut_num}"] = result
        else:
            print(f"      ⚠ Skipping T{tut_num} due to processing error")
        
        # Rate limiting
        if tut_num < 8:
            time.sleep(1)
    
    return indexed_results


# ─────────────────────────────────────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def save_indexed_results(results: Dict, output_path: str):
    """Save indexed material to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved indexed results to: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nChecking GitHub token...")
    if not os.environ.get("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN not set. Cannot proceed.")
        print("Set the environment variable: $env:GITHUB_TOKEN = 'your_token'")
        exit(1)
    
    results = process_all_tutorials()
    
    output_file = r"C:\Users\stein\tutor-bot\indexed_tutorials.json"
    save_indexed_results(results, output_file)
    
    print("\n" + "=" * 90)
    print(f"COMPLETED: Indexed {len(results)} tutorials")
    print("=" * 90)
    print(f"✓ Results saved to: indexed_tutorials.json")
    print("\nNext step: Transform indexed data into metadata.json format")

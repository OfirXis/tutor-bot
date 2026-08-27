"""
Pipeline to extract all tutorials from PDFs and generate indexed material via ChatGPT 4o mini.

Process:
1. Extract text from each PDF
2. Send to ChatGPT 4o mini for structured topic extraction
3. Store indexed material by tutorial number
4. Save to metadata.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import PyPDF2

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: PDF EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                text.append(f"--- Page {page_num + 1} ---")
                text.append(page.extract_text())
        return "\n".join(text)
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
        return ""


def get_tutorial_files() -> List[Tuple[int, str, str]]:
    """
    Return list of (tutorial_number, display_name, pdf_path) for all 8 tutorials.
    Scans the extracted zip directory.
    """
    extracted_dir = Path(r"C:\Users\stein\Downloads\algolectures_extracted")
    
    # Map file names to tutorial numbers
    file_mapping = {
        "Tutorial 1 (2).pdf": (1, "Tutorial 1 — Intro to Algorithm Analysis"),
        "Tutorial 2 (2).pdf": (2, "Tutorial 2 — Divide and Conquer"),
        "Tutorial 3 (2).pdf": (3, "Tutorial 3 — Greedy Algorithms"),
        "Tutorial 4 (2).pdf": (4, "Tutorial 4 — Dynamic Programming"),
        "Tutorial algo 5.pdf": (5, "Tutorial 5 — Advanced DP"),
        "Tutorial algo 6.pdf": (6, "Tutorial 6 — DP Optimization"),
        "Tutorial algo 7.pdf": (7, "Tutorial 7 — Minimum Spanning Trees"),
        "Tutorial algo 8.pdf": (8, "Tutorial 8 — Shortest Paths"),
    }
    
    tutorials = []
    for filename, (num, display_name) in file_mapping.items():
        pdf_path = extracted_dir / filename
        if pdf_path.exists():
            tutorials.append((num, display_name, str(pdf_path)))
    
    return sorted(tutorials, key=lambda x: x[0])


def extract_all_tutorials() -> Dict[int, Dict[str, str]]:
    """Extract text from all 8 tutorials and return indexed by tutorial number."""
    tutorials_data = {}
    
    print("=" * 90)
    print("EXTRACTING TEXT FROM ALL TUTORIALS")
    print("=" * 90)
    
    for tut_num, display_name, pdf_path in get_tutorial_files():
        print(f"\n[T{tut_num}] Extracting: {display_name}")
        print(f"     File: {Path(pdf_path).name}")
        
        text = extract_text_from_pdf(pdf_path)
        char_count = len(text)
        line_count = text.count('\n')
        
        tutorials_data[tut_num] = {
            "display_name": display_name,
            "raw_text": text,
            "char_count": char_count,
            "line_count": line_count,
        }
        
        print(f"     ✓ Extracted {char_count:,} characters, {line_count} lines")
    
    print("\n" + "=" * 90)
    print(f"Successfully extracted {len(tutorials_data)} tutorials")
    print("=" * 90)
    
    return tutorials_data


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: SAVE EXTRACTED DATA
# ─────────────────────────────────────────────────────────────────────────────

def save_extracted_texts(tutorials_data: Dict[int, Dict], output_path: str):
    """Save raw extracted texts to a JSON file for inspection."""
    output = {
        f"tutorial_{num}": {
            "display_name": data["display_name"],
            "char_count": data["char_count"],
            "line_count": data["line_count"],
            "raw_text": data["raw_text"][:500] + "..." if len(data["raw_text"]) > 500 else data["raw_text"],
        }
        for num, data in tutorials_data.items()
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved extracted texts preview to: {output_path}")


def save_raw_texts_for_llm(tutorials_data: Dict[int, Dict], output_dir: str):
    """Save individual text files for each tutorial (for LLM processing)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for tut_num, data in tutorials_data.items():
        output_file = Path(output_dir) / f"tutorial_{tut_num}_raw.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"TUTORIAL {tut_num}: {data['display_name']}\n")
            f.write("=" * 90 + "\n\n")
            f.write(data["raw_text"])
        
        print(f"✓ Saved tutorial {tut_num} raw text: {output_file.name}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: PREPARE PROMPTS FOR LLM
# ─────────────────────────────────────────────────────────────────────────────

def create_indexing_prompts(tutorials_data: Dict[int, Dict]) -> Dict[int, str]:
    """Create prompts for ChatGPT 4o mini to extract indexed material."""
    prompts = {}
    
    base_prompt = """You are analyzing a university algorithms course tutorial. 
Your task is to extract and index all key concepts, algorithms, theorems, and topics taught in this material.

TUTORIAL TEXT:
{tutorial_text}

TASK:
1. Identify ALL unique topics, concepts, algorithms, theorems, and techniques taught in this tutorial
2. Organize them in a hierarchical structure if possible (e.g., "Sorting Algorithms" with subsections)
3. For each topic, provide a 1-2 sentence summary of what students should understand
4. Mark which topics are PREREQUISITE (must be learned before this tutorial) vs CORE (main topics of this tutorial)

OUTPUT FORMAT (JSON):
{{
  "tutorial_number": {num},
  "tutorial_name": "{display_name}",
  "prerequisite_topics": [
    {{"name": "topic_name", "description": "brief description"}}
  ],
  "core_topics": [
    {{"name": "topic_name", "description": "brief description", "subtopics": ["sub1", "sub2"]}}
  ],
  "key_algorithms": [
    {{"name": "algorithm_name", "description": "what it does", "complexity": "time/space complexity if applicable"}}
  ],
  "important_theorems": [
    {{"name": "theorem_name", "description": "what it states"}}
  ]
}}
"""
    
    for tut_num, data in tutorials_data.items():
        # Limit text to first 50k characters to fit in context
        limited_text = data["raw_text"][:50000]
        if len(data["raw_text"]) > 50000:
            limited_text += f"\n... [TEXT TRUNCATED - {len(data['raw_text']) - 50000} more characters] ..."
        
        prompt = base_prompt.format(
            num=tut_num,
            display_name=data["display_name"],
            tutorial_text=limited_text
        )
        prompts[tut_num] = prompt
    
    return prompts


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Step 1: Extract all PDF texts
    tutorials_data = extract_all_tutorials()
    
    # Step 2: Save extracted texts
    save_extracted_texts(
        tutorials_data,
        r"C:\Users\stein\tutor-bot\extracted_tutorials_preview.json"
    )
    
    save_raw_texts_for_llm(
        tutorials_data,
        r"C:\Users\stein\tutor-bot\raw_tutorial_texts"
    )
    
    # Step 3: Create LLM prompts
    prompts = create_indexing_prompts(tutorials_data)
    
    # Save prompts for inspection
    with open(r"C:\Users\stein\tutor-bot\llm_prompts.json", 'w', encoding='utf-8') as f:
        prompt_preview = {
            num: prompt[:500] + "..." for num, prompt in prompts.items()
        }
        json.dump(prompt_preview, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 90)
    print("PIPELINE READY FOR NEXT STEP: Send prompts to ChatGPT 4o mini")
    print("=" * 90)
    print(f"\n✓ Generated {len(prompts)} LLM prompts")
    print("✓ Raw texts saved in: raw_tutorial_texts/")
    print("✓ Next: Call ChatGPT API for each prompt to extract indexed material")

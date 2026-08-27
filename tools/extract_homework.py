"""
extract_homework.py — Extract homework problems and solutions from PDFs

This script reads the homework PDFs from the algo.zip extraction folder
and builds a structured homework.json database that the tutoring bot can use.

Usage: python extract_homework.py
"""

import json
import os
from pathlib import Path
import subprocess
import sys

# Paths
EXTRACTED_DIR = Path(r"C:\Users\stein\Downloads\algo_extracted")
HW_DIR = EXTRACTED_DIR / "hw"
OUTPUT_FILE = Path(__file__).parent / "db" / "homework.json"

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber or PyPDF2"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return text
    except ImportError:
        # Fallback to PyPDF2
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = "\n".join(page.extract_text() for page in reader.pages)
            return text
        except Exception as e:
            print(f"⚠️ Could not extract {pdf_path}: {e}")
            return f"[PDF extraction failed: {pdf_path}]"

def split_problem_and_solution(full_text: str, hw_num: int) -> tuple:
    """
    Extract problem statement and expected solution.
    Assumes PDFs have problems in first part, solutions in second.
    """
    lines = full_text.split("\n")
    
    # Find "Solution" marker or assume 50/50 split
    solution_idx = -1
    for i, line in enumerate(lines):
        if "solution" in line.lower() or "answer" in line.lower():
            solution_idx = i
            break
    
    if solution_idx > 0:
        problem_text = "\n".join(lines[:solution_idx])
        solution_text = "\n".join(lines[solution_idx:])
    else:
        # Rough split if no marker found
        mid = len(lines) // 2
        problem_text = "\n".join(lines[:mid])
        solution_text = "\n".join(lines[mid:])
    
    return problem_text.strip(), solution_text.strip()

def extract_problems_from_pdf(pdf_path: Path, hw_num: int) -> dict:
    """Extract structured problem data from homework PDF"""
    print(f"  📄 Extracting {pdf_path.name}...", end=" ")
    
    text = extract_pdf_text(str(pdf_path))
    problem_text, _ = split_problem_and_solution(text, hw_num)
    
    # Count estimated problems (look for "Problem 1", "1.", etc.)
    problem_count = max(
        problem_text.count("Problem"),
        problem_text.count("\n1."),
        problem_text.count("\n2."),
    )
    
    # Get first 500 chars of problem as preview
    preview = (problem_text[:500] + "...") if len(problem_text) > 500 else problem_text
    
    result = {
        "hw_number": hw_num,
        "pdf_path": str(pdf_path),
        "problem_count": max(1, problem_count),
        "preview": preview,
        "full_text": problem_text[:2000],  # First 2000 chars for context
    }
    print(f"✓ ({problem_count} problems)")
    return result

def build_homework_database() -> dict:
    """Build complete homework database"""
    
    if not HW_DIR.exists():
        print(f"❌ Homework directory not found: {HW_DIR}")
        print(f"Make sure algo.zip is extracted to: {EXTRACTED_DIR}")
        return {}
    
    homework_data = {}
    
    # Process each homework PDF
    for i in range(1, 6):
        hw_pdf = HW_DIR / f"hw{i}.pdf"
        sol_pdf = HW_DIR / f"hw{i}__Sol.pdf"
        
        if not hw_pdf.exists():
            print(f"⚠️ Not found: {hw_pdf}")
            continue
        
        print(f"\n📚 Homework {i}:")
        
        # Extract problems
        hw_data = extract_problems_from_pdf(hw_pdf, i)
        
        # Extract solutions
        if sol_pdf.exists():
            print(f"  📄 Extracting {sol_pdf.name}...", end=" ")
            sol_text = extract_pdf_text(str(sol_pdf))
            hw_data["solution_text"] = sol_text[:3000]  # First 3000 chars
            print("✓")
        else:
            hw_data["solution_text"] = "[Solution PDF not found]"
        
        # Build homework entry
        homework_data[f"hw_{i}"] = {
            "week": i,
            "title": f"Homework {i}",
            "problem_pdf": str(hw_pdf),
            "solution_pdf": str(sol_pdf),
            "problems": hw_data["problem_count"],
            "problem_preview": hw_data["preview"],
            "full_problem_text": hw_data["full_text"],
            "full_solution_text": hw_data["solution_text"],
        }
    
    return homework_data

def main():
    print("=" * 60)
    print("🎓 HOMEWORK EXTRACTION PIPELINE")
    print("=" * 60)
    
    # Check if pdfplumber/PyPDF2 is installed
    try:
        import pdfplumber
        print("✓ pdfplumber available")
    except ImportError:
        print("⚠️ pdfplumber not installed, trying PyPDF2...")
        try:
            from pypdf import PdfReader
            print("✓ PyPDF2 available")
        except ImportError:
            print("❌ No PDF library found!")
            print("Install with: pip install pdfplumber pypdf")
            sys.exit(1)
    
    print(f"\n📁 Extracted folder: {EXTRACTED_DIR}")
    print(f"📁 Homework folder: {HW_DIR}")
    
    if not HW_DIR.exists():
        print(f"\n❌ ERROR: {HW_DIR} does not exist")
        print("Please ensure algo.zip is extracted first.")
        sys.exit(1)
    
    # Build database
    homework_data = build_homework_database()
    
    if not homework_data:
        print("\n❌ No homework found!")
        sys.exit(1)
    
    # Save to JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(homework_data, indent=2, ensure_ascii=False))
    
    print(f"\n" + "=" * 60)
    print(f"✅ Homework database created!")
    print(f"📄 Location: {OUTPUT_FILE}")
    print(f"📊 Homeworks extracted: {len(homework_data)}")
    print("=" * 60)
    
    # Show summary
    for hw_key, hw_info in homework_data.items():
        print(f"\n{hw_key.upper()}:")
        print(f"  Week: {hw_info['week']}")
        print(f"  Problems: {hw_info['problems']}")
        print(f"  Preview: {hw_info['problem_preview'][:100]}...")

if __name__ == "__main__":
    main()

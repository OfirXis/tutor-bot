"""Locations of the active course pack. Set COURSE_ROOT to serve or build another course."""
from __future__ import annotations

import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
COURSE_ROOT = Path(os.getenv("COURSE_ROOT") or APP_ROOT).resolve()

MATERIAL_DIR = COURSE_ROOT / "material"
LECTURES_DIR = MATERIAL_DIR / "lectures"
HOMEWORK_DIR = MATERIAL_DIR / "Homework"
NOTES_DIR = MATERIAL_DIR / "english"
REVIEW_DIR = MATERIAL_DIR / "curriculum_review"
COURSE_FILE = MATERIAL_DIR / "course.json"

DB_DIR = COURSE_ROOT / "db"
CURRICULUM_FILE = DB_DIR / "curriculum.json"
HOMEWORK_FILE = DB_DIR / "homework.json"
INDEX_DIR = DB_DIR / "index"
CHUNKS_FILE = DB_DIR / "chunks.jsonl"

"""Cross-platform setup and launcher for Course Tutor.

Usage:
    python run.py
    python run.py --setup-only

Any unrecognized arguments are forwarded to ``streamlit run``.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
REQUIREMENTS_STAMP = VENV_DIR / ".tutor-requirements.sha256"


def venv_python() -> Path:
    """Return the virtual-environment Python path for the current platform."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run_checked(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def requirements_digest() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def ensure_environment() -> Path:
    python = venv_python()
    if not python.exists():
        print("Creating virtual environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    digest = requirements_digest()
    installed_digest = (
        REQUIREMENTS_STAMP.read_text(encoding="utf-8").strip()
        if REQUIREMENTS_STAMP.exists()
        else ""
    )
    if installed_digest != digest:
        print("Installing project requirements...", flush=True)
        run_checked([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        REQUIREMENTS_STAMP.write_text(digest + "\n", encoding="utf-8")

    return python


def ensure_index(python: Path) -> None:
    from rag_engine import index_needs_rebuild

    if index_needs_rebuild(ROOT / "material" / "english", ROOT / "db" / "index",
                           ROOT / "db" / "chunks.jsonl"):
        print("Building retrieval index for the current course material...", flush=True)
        run_checked([str(python), str(ROOT / "build_index.py")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up and launch Course Tutor.")
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="install dependencies and build the index without launching Streamlit",
    )
    args, streamlit_args = parser.parse_known_args()

    if sys.version_info < (3, 11):
        parser.error("Course Tutor requires Python 3.11 or newer.")

    python = ensure_environment()
    ensure_index(python)

    if args.setup_only:
        print("Course Tutor setup is complete.")
        return 0

    print("Starting Course Tutor...", flush=True)
    try:
        return subprocess.call(
            [str(python), "-m", "streamlit", "run", str(ROOT / "app.py"), *streamlit_args],
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

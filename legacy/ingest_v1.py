"""
ingest.py — CLI alternative to the sidebar uploader.
Embeddings are 100% local (no API key needed).

Usage:
    python ingest.py --pdf "slides/hw1.pdf" --id hw1 --name "HW1 - Automata" --topic "DFA/NFA..."
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_DIR    = Path("./db")
META_FILE = DB_DIR / "metadata.json"


def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def load_meta() -> dict:
    if META_FILE.exists():
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    return {}


def save_meta(meta: dict) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def ingest(pdf_path: str, hw_id: str, display_name: str, topic_context: str) -> None:
    from langchain_chroma import Chroma
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    path = Path(pdf_path)
    if not path.exists():
        print(f"Error: file not found - {path}")
        sys.exit(1)

    db_path = DB_DIR / hw_id
    if db_path.exists():
        shutil.rmtree(db_path)
        print(f"Replaced existing database for '{hw_id}'.")

    print(f"Loading {path} ...")
    pages  = PyPDFLoader(str(path)).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200
    ).split_documents(pages)
    print(f"  {len(pages)} pages -> {len(chunks)} chunks")

    print("Embedding with local model (all-MiniLM-L6-v2)...")
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(db_path),
    )

    meta = load_meta()
    meta[hw_id] = {
        "display_name":  display_name or hw_id,
        "topic_context": topic_context,
    }
    save_meta(meta)
    print(f"Done. '{hw_id}' is ready - launch the app and select it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a PDF (no API key needed).")
    parser.add_argument("--pdf",   required=True, help="Path to PDF")
    parser.add_argument("--id",    required=True, help="Short ID, e.g. hw1")
    parser.add_argument("--name",  default="",    help="Display name shown in UI")
    parser.add_argument("--topic", default="",    help="Topic context / Socratic guidance prompt")
    args = parser.parse_args()
    ingest(args.pdf, args.id.replace(" ", "_"), args.name, args.topic)

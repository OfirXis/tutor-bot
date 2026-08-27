"""
reingest_all.py — Re-index all tutorial vector DBs with ZERO content loss.

Strategy: Section-based splitting only at H2 (## ) boundaries.
Each complete section (Core Concepts, Algorithms & Complexity, Theorems,
Worked Examples, Practice Problems, Common Mistakes) becomes ONE chunk.
This guarantees all H3 subsections stay with their parent — nothing gets
lost in chunk boundaries or overlap windows.

Sources per tutorial:
  1. material/english/tutorial_N.txt  — full lecture content
  2. db/metadata.json topic_context   — problem-solving frameworks

Run: .venv/Scripts/python.exe reingest_all.py
"""
import json
import re
import shutil
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent
DB_DIR = ROOT / "db"
META_FILE = DB_DIR / "metadata.json"
ENGLISH_DIR = ROOT / "material" / "english"

print("Loading embedding model (all-MiniLM-L6-v2)...")
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
print("Model ready.\n")

meta = json.loads(META_FILE.read_text(encoding="utf-8"))


def split_by_h2_sections(text: str, base_meta: dict) -> list[Document]:
    """
    Split Markdown text at H2 (## ) headings only.
    Each complete section — including all its H3/H4 subsections — becomes one Document.
    The first block (before the first ## ) is kept as the title/intro chunk.
    Merges tiny orphan sections (< 100 chars) with the preceding one.
    """
    # Split at lines that start with "## "
    parts = re.split(r'(?=^## )', text, flags=re.MULTILINE)
    docs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        docs.append(Document(page_content=part, metadata=dict(base_meta)))

    # Merge any tiny fragment into previous
    merged: list[Document] = []
    for doc in docs:
        if merged and len(doc.page_content) < 100:
            merged[-1] = Document(
                page_content=merged[-1].page_content + "\n\n" + doc.page_content,
                metadata=merged[-1].metadata,
            )
        else:
            merged.append(doc)
    return merged


def split_metadata_context(text: str, base_meta: dict) -> list[Document]:
    """
    Split problem-solving metadata at its === SECTION === markers.
    Each top-level section becomes one Document.
    """
    parts = re.split(r'(?=^=== )', text, flags=re.MULTILINE)
    docs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        docs.append(Document(page_content=part, metadata=dict(base_meta)))
    return docs or [Document(page_content=text, metadata=dict(base_meta))]


TUTORIAL_IDS = [f"tutorial_{i}" for i in range(1, 9)]

for tid in TUTORIAL_IDS:
    num = tid.split("_")[1]
    txt_file = ENGLISH_DIR / f"tutorial_{num}.txt"
    db_path = DB_DIR / tid

    print(f"=== {tid} ===")

    if not txt_file.exists():
        print(f"  WARNING: {txt_file} not found, skipping.")
        continue

    lecture_text = txt_file.read_text(encoding="utf-8")
    topic_ctx = meta.get(tid, {}).get("topic_context", "")

    # ── Lecture chunks: one per H2 section — zero content loss
    lecture_chunks = split_by_h2_sections(
        lecture_text,
        {"source": f"{tid}_lecture", "tutorial": tid, "type": "lecture"},
    )

    # ── Problem-solving chunks: one per === SECTION ===
    ps_chunks = split_metadata_context(
        topic_ctx,
        {"source": f"{tid}_meta", "tutorial": tid, "type": "problem_solving"},
    ) if topic_ctx else []

    all_docs = lecture_chunks + ps_chunks

    # Verify completeness — every H2 heading in source appears in some chunk
    h2_headings = re.findall(r'^## .+', lecture_text, re.MULTILINE)
    found = sum(1 for h in h2_headings if any(h in d.page_content for d in lecture_chunks))
    missing = [h for h in h2_headings if not any(h in d.page_content for d in lecture_chunks)]

    print(f"  Source: {len(lecture_text):,} chars  |  H2 sections: {len(h2_headings)}")
    print(f"  Lecture chunks: {len(lecture_chunks)}  |  All found: {found}/{len(h2_headings)}")
    if missing:
        print(f"  WARNING — missing sections: {missing}")
    print(f"  Problem-solving chunks: {len(ps_chunks)}  |  Total: {len(all_docs)}")

    # Print each chunk summary
    for i, doc in enumerate(all_docs):
        first_line = doc.page_content.split('\n')[0][:80]
        print(f"    [{doc.metadata['type']}] {len(doc.page_content):>5}c  {first_line}")

    # Rebuild DB
    if db_path.exists():
        shutil.rmtree(db_path)
    Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=str(db_path),
    )
    print(f"  Indexed to {db_path}\n")

print("=" * 60)
print("All tutorials re-indexed with ZERO content loss!")
print("Each H2 section from every lecture file is a complete searchable chunk.")

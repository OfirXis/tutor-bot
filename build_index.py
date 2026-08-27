"""
build_index.py — Build the single-collection hybrid course index.

Usage:
    python build_index.py                 # default embedding model (bge-small-en-v1.5)
    python build_index.py --model intfloat/e5-small-v2
"""
import argparse

from rag_engine import EMBED_MODEL, build_index

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=EMBED_MODEL, help="sentence-transformers model name")
    args = ap.parse_args()
    build_index(embed_model=args.model)
    print("\nDone. Run:  streamlit run app.py")

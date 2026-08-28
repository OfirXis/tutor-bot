"""
rag_engine.py — Core RAG engine for the Course Tutor.

Design (2026 rebuild):
  • ONE Chroma collection for the whole course; every chunk carries a
    `tutorial` integer so the curriculum boundary is enforced AT RETRIEVAL
    TIME with a metadata filter (tutorial <= current week) — future material
    physically cannot leak into the context.
  • Header-aware markdown chunking: each chunk is a coherent section with a
    breadcrumb ("Tutorial 4 › Worked Examples › Fibonacci") prepended, which
    measurably improves both dense and lexical retrieval.
  • Hybrid retrieval: dense (sentence-transformers) + BM25, fused with
    Reciprocal Rank Fusion, then optionally reranked with a cross-encoder.
    All models are free and run locally.
  • LLM is provider-agnostic: ollama | github | openai | compatible
    (any OpenAI-compatible endpoint: LM Studio, vLLM, Groq, OpenRouter...).
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).parent
DB_DIR = HERE / "db"
INDEX_DIR = DB_DIR / "index"
CHUNKS_FILE = DB_DIR / "chunks.jsonl"
META_FILE = DB_DIR / "metadata.json"
HOMEWORK_FILE = DB_DIR / "homework.json"
MATERIAL_DIR = HERE / "material" / "english"

COLLECTION_NAME = "course"

# ── Config (env-overridable) ─────────────────────────────────────────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
# dense | hybrid | hybrid+rerank — default per BENCHMARK_RESULTS.md (dense bge-small wins)
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "dense")
# scope gate thresholds: refuse when the question matches future material this much
# better than covered material (cosine sims; tuned on the golden set + leak probes)
SCOPE_SIM_FLOOR = float(os.getenv("SCOPE_SIM_FLOOR", "0.55"))
SCOPE_SIM_MARGIN = float(os.getenv("SCOPE_SIM_MARGIN", "0.05"))

# Query prefixes some embedding families need (passages are indexed raw).
_QUERY_PREFIXES = {
    "bge": "Represent this sentence for searching relevant passages: ",
    "e5": "query: ",
}
_PASSAGE_PREFIXES = {
    "e5": "passage: ",
}


def _prefix_for(model_name: str, table: dict) -> str:
    name = model_name.lower()
    for key, prefix in table.items():
        if key in name:
            return prefix
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────────────────────────────────────

MAX_CHUNK_CHARS = 1800
MIN_CHUNK_CHARS = 80
PART_OVERLAP_PARAS = 1


@dataclass
class Chunk:
    id: str
    text: str          # breadcrumb + section body (indexed & shown to the LLM)
    tutorial: int
    source: str        # e.g. "tutorial_4"
    section: str       # e.g. "Worked Examples › Example 1: Fibonacci"

    def meta(self) -> dict:
        return {"tutorial": self.tutorial, "source": self.source, "section": self.section}


def _split_long(paras: list[str]) -> list[list[str]]:
    """Greedy paragraph packing so no part exceeds MAX_CHUNK_CHARS."""
    parts, cur, size = [], [], 0
    for p in paras:
        if cur and size + len(p) > MAX_CHUNK_CHARS:
            parts.append(cur)
            cur = cur[-PART_OVERLAP_PARAS:] if PART_OVERLAP_PARAS else []
            size = sum(len(x) for x in cur)
        cur.append(p)
        size += len(p)
    if cur:
        parts.append(cur)
    return parts


def chunk_markdown(text: str, source: str, tutorial: int) -> list[Chunk]:
    """Split a markdown document into header-scoped chunks with breadcrumbs."""
    doc_title = source
    h2 = h3 = ""
    sections: list[tuple[str, list[str]]] = []  # (breadcrumb, lines)
    lines_buf: list[str] = []

    def flush():
        nonlocal lines_buf
        body = "\n".join(lines_buf).strip()
        lines_buf = []
        if len(body) < MIN_CHUNK_CHARS:
            return
        crumb = " › ".join(x for x in (doc_title, h2, h3) if x)
        sections.append((crumb, body.split("\n\n")))

    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 1:
                doc_title, h2, h3 = title, "", ""
            elif level == 2:
                h2, h3 = title, ""
            else:
                h3 = title
        else:
            lines_buf.append(line)
    flush()

    chunks: list[Chunk] = []
    for crumb, paras in sections:
        paras = [p for p in ("\n\n".join(paras)).split("\n\n") if p.strip()]
        parts = _split_long(paras) if sum(len(p) for p in paras) > MAX_CHUNK_CHARS else [paras]
        for i, part in enumerate(parts):
            label = crumb if len(parts) == 1 else f"{crumb} (part {i + 1})"
            body = "\n\n".join(part).strip()
            chunks.append(Chunk(
                id=f"{source}::{len(chunks):03d}",
                text=f"[{label}]\n{body}",
                tutorial=tutorial,
                source=source,
                section=label,
            ))
    return chunks


def load_course_chunks() -> list[Chunk]:
    """Chunk every tutorial markdown file in material/english."""
    chunks: list[Chunk] = []
    for path in sorted(MATERIAL_DIR.glob("tutorial_*.txt")):
        m = re.search(r"tutorial_(\d+)", path.stem)
        if not m:
            continue
        n = int(m.group(1))
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), f"tutorial_{n}", n))
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Embeddings / models (cached singletons)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=2)
def get_embedder(model_name: str = EMBED_MODEL):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name, device=os.getenv("EMBED_DEVICE", "cpu"))


@lru_cache(maxsize=1)
def get_reranker(model_name: str = RERANKER_MODEL):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name, device=os.getenv("EMBED_DEVICE", "cpu"))


def embed_texts(texts: list[str], model_name: str = EMBED_MODEL, queries: bool = False):
    model = get_embedder(model_name)
    prefix = _prefix_for(model_name, _QUERY_PREFIXES if queries else _PASSAGE_PREFIXES)
    return model.encode(
        [prefix + t for t in texts],
        normalize_embeddings=True,
        batch_size=64,
        show_progress_bar=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hybrid retriever  (dense + BM25 → RRF → optional cross-encoder rerank)
# ─────────────────────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class Hit:
    chunk: Chunk
    score: float


RRF_K = 60


def rrf_fuse(rankings: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return scores


class HybridRetriever:
    def __init__(self, index_dir: Path = INDEX_DIR, chunks_file: Path = CHUNKS_FILE,
                 embed_model: str = EMBED_MODEL):
        import chromadb
        from rank_bm25 import BM25Okapi

        self.embed_model = embed_model
        self.client = chromadb.PersistentClient(path=str(index_dir))
        self.collection = self.client.get_collection(COLLECTION_NAME)

        self.chunks: dict[str, Chunk] = {}
        order: list[str] = []
        with chunks_file.open(encoding="utf-8") as f:
            for line in f:
                c = Chunk(**json.loads(line))
                self.chunks[c.id] = c
                order.append(c.id)
        self._bm25_ids = order
        self._bm25 = BM25Okapi([_tokenize(self.chunks[cid].text) for cid in order])

    # -- individual channels -------------------------------------------------
    def _dense(self, query: str, max_tutorial: int, k: int) -> list[str]:
        emb = embed_texts([query], self.embed_model, queries=True)
        res = self.collection.query(
            query_embeddings=emb.tolist(),
            n_results=k,
            where={"tutorial": {"$lte": max_tutorial}},
            include=[],
        )
        return res["ids"][0]

    def _lexical(self, query: str, max_tutorial: int, k: int) -> list[str]:
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            (
                (cid, s)
                for cid, s in zip(self._bm25_ids, scores)
                if self.chunks[cid].tutorial <= max_tutorial and s > 0
            ),
            key=lambda x: -x[1],
        )
        return [cid for cid, _ in ranked[:k]]

    # -- public API ------------------------------------------------------------
    def retrieve(self, query: str, max_tutorial: int = 99, k: int = 5,
                 pool: int = 20, rerank: bool | None = None,
                 mode: str | None = None) -> list[Hit]:
        mode = mode or ("hybrid+rerank" if rerank else "hybrid" if rerank is not None else RETRIEVAL_MODE)
        if mode == "dense":
            ids = self._dense(query, max_tutorial, k)
            return [Hit(self.chunks[cid], 1.0 / (i + 1)) for i, cid in enumerate(ids)]

        rerank = mode == "hybrid+rerank"
        fused = rrf_fuse([
            self._dense(query, max_tutorial, pool),
            self._lexical(query, max_tutorial, pool),
        ])
        candidates = sorted(fused, key=lambda cid: -fused[cid])[: max(k * 3, 12) if rerank else k]

        if rerank and candidates:
            ce = get_reranker()
            pairs = [(query, self.chunks[cid].text) for cid in candidates]
            ce_scores = ce.predict(pairs, show_progress_bar=False)
            ranked = sorted(zip(candidates, ce_scores), key=lambda x: -x[1])[:k]
            return [Hit(self.chunks[cid], float(s)) for cid, s in ranked]

        return [Hit(self.chunks[cid], fused[cid]) for cid in candidates[:k]]

    def scope_check(self, query: str, week: int,
                    floor: float = SCOPE_SIM_FLOOR,
                    margin: float = SCOPE_SIM_MARGIN) -> tuple[bool, int]:
        """Deterministic curriculum gate: does the question target future material?

        Compares the query's best cosine similarity against not-yet-covered chunks
        (tutorial > week) vs covered ones (tutorial <= week). Returns
        (is_future, best_future_tutorial). LLM prompts alone are unreliable for
        refusal (see BENCHMARK_LLM.md) — this runs before the LLM is ever called.
        """
        emb = embed_texts([query], self.embed_model, queries=True).tolist()
        future = self.collection.query(
            query_embeddings=emb, n_results=1,
            where={"tutorial": {"$gt": week}}, include=["distances", "metadatas"],
        )
        if not future["ids"][0]:
            return False, 0
        allowed = self.collection.query(
            query_embeddings=emb, n_results=1,
            where={"tutorial": {"$lte": week}}, include=["distances"],
        )
        sim_future = 1.0 - future["distances"][0][0]
        sim_allowed = 1.0 - allowed["distances"][0][0] if allowed["ids"][0] else 0.0
        if sim_future > floor and (sim_future - sim_allowed) > margin:
            return True, int(future["metadatas"][0][0]["tutorial"])
        return False, 0


# ─────────────────────────────────────────────────────────────────────────────
# Index build
# ─────────────────────────────────────────────────────────────────────────────

def build_index(embed_model: str = EMBED_MODEL, index_dir: Path = INDEX_DIR,
                chunks_file: Path = CHUNKS_FILE, quiet: bool = False) -> int:
    import shutil
    import chromadb

    chunks = load_course_chunks()
    if not chunks:
        raise SystemExit(f"No material found in {MATERIAL_DIR}")

    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks_file.parent.mkdir(parents=True, exist_ok=True)
    with chunks_file.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    if not quiet:
        print(f"Embedding {len(chunks)} chunks with {embed_model} ...")
    embs = embed_texts([c.text for c in chunks], embed_model)

    client = chromadb.PersistentClient(path=str(index_dir))
    col = client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[c.id for c in chunks],
        embeddings=embs.tolist(),
        documents=[c.text for c in chunks],
        metadatas=[c.meta() for c in chunks],
    )
    if not quiet:
        per_tut: dict[int, int] = {}
        for c in chunks:
            per_tut[c.tutorial] = per_tut.get(c.tutorial, 0) + 1
        print(f"Indexed {len(chunks)} chunks into {index_dir}")
        for t in sorted(per_tut):
            print(f"  tutorial_{t}: {per_tut[t]} chunks")
    return len(chunks)


# ─────────────────────────────────────────────────────────────────────────────
# LLM factory — swap providers with env vars, no code changes
# ─────────────────────────────────────────────────────────────────────────────

def get_llm(streaming: bool = True):
    """LLM_PROVIDER: ollama (default) | github | openai | compatible."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
        )

    from langchain_openai import ChatOpenAI
    if provider == "github":
        return ChatOpenAI(
            model=os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini"),
            api_key=os.getenv("GITHUB_TOKEN", ""),
            base_url="https://models.github.ai/inference",
            temperature=temperature, streaming=streaming,
        )
    if provider == "compatible":
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", ""),
            api_key=os.getenv("LLM_API_KEY", "not-needed"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
            temperature=temperature, streaming=streaming,
        )
    return ChatOpenAI(  # provider == "openai"
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature, streaming=streaming,
    )


def llm_label() -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    return {
        "ollama": f"Ollama · {os.getenv('OLLAMA_LLM_MODEL', 'llama3.2:3b')}",
        "github": f"GitHub Models · {os.getenv('GITHUB_MODEL', 'openai/gpt-4o-mini')}",
        "openai": f"OpenAI · {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}",
        "compatible": f"Custom · {os.getenv('LLM_MODEL', '?')}",
    }.get(provider, provider)


# ─────────────────────────────────────────────────────────────────────────────
# Language / translation
#
# The course material, embeddings (bge-small-en-v1.5) and BM25 tokenizer are
# English-only — retrieval quality and the curriculum gate depend on the
# benchmarked English pipeline. Rather than re-embedding everything in Hebrew,
# a Hebrew question is translated to English before it touches retrieval or
# the LLM, and the English answer is translated back to Hebrew for display.
# ─────────────────────────────────────────────────────────────────────────────

_HEBREW_RE = re.compile(r"[֐-׿]")


def is_hebrew(text: str) -> bool:
    """True if text contains any Hebrew-script character."""
    return bool(_HEBREW_RE.search(text))


def get_translation_llm():
    """Dedicated LLM for translate() — deliberately decoupled from whichever
    provider/model the student picked for tutoring generation.

    Empirically (see BENCHMARK results / project notes), the free local 3B
    Ollama models mistranslate Hebrew CS terminology (wrong verbs, garbled
    transliterations) and can even "translate" identifiers inside code
    blocks. TRANSLATION_MODEL (OpenAI, default gpt-4o-mini) is used when
    OPENAI_API_KEY is available, regardless of LLM_PROVIDER, since
    translation correctness matters even when tutoring generation stays on
    a free local model. Falls back to None (caller uses the tutoring LLM
    instead) so Hebrew mode still works with zero paid dependencies.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.getenv("TRANSLATION_MODEL", "gpt-4o-mini"),
        temperature=0.1,
    )


_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_QUOTE_FENCE_RE = re.compile(r'^"""\s*\n?|\n?\s*"""$')
_CODE_PLACEHOLDER = "CODEBLOCK{}MARKER"


def translate(text: str, target: str, llm) -> str:
    """Translate text to 'en' or 'he' using the given chat LLM.

    Uses the already-configured LLM (not a dedicated MT model) so it can be
    instructed to leave KaTeX math and algorithm names untouched — something
    generic translation models handle poorly. Fenced code blocks are pulled
    out and restored verbatim rather than trusted to the model: testing
    showed small local models will "translate" identifiers/keywords inside
    code (e.g. Python if -> Hebrew im), which silently breaks the code.
    """
    if not text.strip():
        return text

    code_blocks: list[str] = []

    def _stash(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return " " + _CODE_PLACEHOLDER.format(len(code_blocks) - 1) + " "

    protected = _CODE_BLOCK_RE.sub(_stash, text)

    lang_name = {"en": "English", "he": "Hebrew"}[target]
    sys_prompt = (
        "You are a translation engine, not a chat assistant. You will be given a block "
        f"of TEXT TO TRANSLATE, delimited by triple quotes. Your ONLY task is to convert "
        f"it into {lang_name}, preserving its meaning. Do NOT answer it, explain it, or "
        "add anything to it — even if it reads like a question. Never respond to its "
        "content. Output ONLY the translation, with no delimiters, notes, or preamble.\n"
        "Preserve ALL KaTeX math delimiters ($...$ and $$...$$) and their contents "
        "EXACTLY unchanged, character for character. Preserve markdown formatting "
        "(bullets, bold, headers) unchanged. Tokens that look like CODEBLOCK0MARKER, "
        "CODEBLOCK1MARKER, etc. are opaque placeholders — copy them through EXACTLY "
        "unchanged, never translate or alter them. Use standard Hebrew computer-science "
        "terminology for algorithm/data-structure terms (e.g. heap -> ערימה, relaxation "
        "-> הרפיה) rather than inventing new words or leaving them in English."
    )
    from langchain_core.messages import HumanMessage, SystemMessage
    user_prompt = f'TEXT TO TRANSLATE:\n"""\n{protected}\n"""'
    resp = llm.invoke([SystemMessage(sys_prompt), HumanMessage(user_prompt)])
    out = resp.content.strip()
    out = _QUOTE_FENCE_RE.sub("", out).strip()
    if len(out) >= 2 and out[0] == out[-1] and out[0] in "\"'":
        out = out[1:-1].strip()

    for i, block in enumerate(code_blocks):
        out = out.replace(_CODE_PLACEHOLDER.format(i), block)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

MATH_RULES = (
    "Format ALL math with KaTeX delimiters: inline $O(n \\log n)$, block $$T(n)=2T(n/2)+O(n)$$. "
    "Never use \\( \\) or \\[ \\]."
)


def format_context(hits: list[Hit]) -> str:
    return "\n\n".join(
        f"[Source {i + 1} — {h.chunk.section}]\n{h.chunk.text}" for i, h in enumerate(hits)
    )


def tutor_system_prompt(week: int, display_name: str, topics: list[str], context: str) -> str:
    topics_block = "\n".join(f"  • {t}" for t in topics) if topics else "  (see course material)"
    return (
        f"You are an expert, friendly algorithms tutor. The student is on week {week}: "
        f"{display_name}.\n\n"
        f"CURRICULUM BOUNDARY — the student has ONLY learned these topics so far:\n{topics_block}\n\n"
        "Rules:\n"
        "1. Answer ONLY with concepts from the topics above. If the question needs a "
        "not-yet-covered topic, say: \"We haven't covered that yet — we'll get there in a later "
        "week. From what you already know, I can help with…\" and suggest 2-3 related covered topics.\n"
        "2. GROUND every answer in the course material excerpts below. Prefer the course's "
        "definitions, notation and examples over generic knowledge. Cite excerpts as (Source N).\n"
        "3. If the material doesn't contain the answer but it IS within the covered topics, say so, "
        "then answer from general knowledge of those topics ONLY. NEVER introduce algorithms, "
        "data structures or theorems from later weeks — not even as an aside or 'better way'.\n"
        "4. Teach for understanding: short explanation → worked example → check-in question back "
        "to the student.\n"
        "5. Be concise. Use bullet points and short paragraphs, not walls of text.\n\n"
        f"{MATH_RULES}\n\n"
        f"COURSE MATERIAL EXCERPTS:\n{context}\n"
    )


def homework_system_prompt(hw: dict, week: int, known_topics: list[str], context: str) -> str:
    topics_block = "\n".join(f"  • {t}" for t in known_topics) if known_topics else "  (basics)"
    key_concepts = "\n".join(f"  • {c}" for c in hw.get("key_concepts", []))
    return (
        f"You are a Socratic tutor for \"{hw.get('title', f'Homework {week}')}\" "
        f"(week {week}).\n\n"
        f"Assignment: {hw.get('description', '')}\n"
        f"Key concepts:\n{key_concepts}\n\n"
        f"The student knows only these topics:\n{topics_block}\n\n"
        "STRICT RULES:\n"
        "1. NEVER give the final answer, full pseudocode, or complete proof.\n"
        "2. Guide with leading questions and small hints, one step at a time.\n"
        "3. When the student makes a claim, ask them to justify it.\n"
        "4. If they're stuck, point them to the relevant covered concept and ask how it might apply.\n"
        "5. Celebrate correct steps briefly, then push to the next step.\n"
        "6. Stay within the covered topics; the excerpts below are your ground truth.\n\n"
        f"{MATH_RULES}\n\n"
        f"COURSE MATERIAL EXCERPTS:\n{context}\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Metadata helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_meta() -> dict:
    return json.loads(META_FILE.read_text(encoding="utf-8")) if META_FILE.exists() else {}


def load_homework() -> dict:
    return json.loads(HOMEWORK_FILE.read_text(encoding="utf-8")) if HOMEWORK_FILE.exists() else {}


def tutorial_week(tutorial_id: str) -> int:
    m = re.search(r"(\d+)", tutorial_id)
    return int(m.group(1)) if m else 1


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Query the course index from the CLI (debug).")
    ap.add_argument("query")
    ap.add_argument("--week", type=int, default=99)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--no-rerank", action="store_true")
    args = ap.parse_args()
    r = HybridRetriever()
    for h in r.retrieve(args.query, args.week, k=args.k, rerank=not args.no_rerank):
        print(f"{h.score:8.3f}  [{h.chunk.section}]")

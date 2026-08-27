"""Offline unit tests for the RAG engine (no models, no network needed).

Run:  pytest tests/ -v
Integration tests that need the built index are skipped automatically if
db/index does not exist yet.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_engine import (  # noqa: E402
    INDEX_DIR,
    Chunk,
    chunk_markdown,
    format_context,
    Hit,
    load_course_chunks,
    rrf_fuse,
    tutor_system_prompt,
    tutorial_week,
    _tokenize,
)

SAMPLE_MD = """# Tutorial 9 — Sample
## Core Concepts
### Definition A
An algorithm is a systematic method for computing outputs from inputs. It must be
unambiguous and it must terminate on every valid input.

### Definition B
Complexity measures resource usage as a function of input size, e.g. time or space.

## Worked Examples
### Example 1
""" + ("Step one of the example. " * 45) + """

""" + ("Step two of the example. " * 45) + """
"""


class TestChunker:
    def test_sections_become_chunks_with_breadcrumbs(self):
        chunks = chunk_markdown(SAMPLE_MD, "tutorial_9", 9)
        assert chunks, "should produce chunks"
        crumbs = [c.section for c in chunks]
        assert any("Core Concepts › Definition A" in s for s in crumbs)
        # breadcrumb is prepended to the indexed text
        assert all(c.text.startswith("[") for c in chunks)

    def test_metadata_carries_tutorial_number(self):
        chunks = chunk_markdown(SAMPLE_MD, "tutorial_9", 9)
        assert all(c.tutorial == 9 for c in chunks)
        assert all(c.meta()["tutorial"] == 9 for c in chunks)

    def test_long_sections_are_split_with_part_labels(self):
        chunks = chunk_markdown(SAMPLE_MD, "tutorial_9", 9)
        example_parts = [c for c in chunks if "Example 1" in c.section]
        assert len(example_parts) >= 2
        assert any("(part 1)" in c.section for c in example_parts)
        assert all(len(c.text) < 2600 for c in chunks)

    def test_tiny_fragments_are_dropped(self):
        md = "# T\n## Short\nok\n## Real\n" + "Real content here. " * 10
        chunks = chunk_markdown(md, "t", 1)
        assert all("Short" not in c.section for c in chunks)

    def test_real_course_material_loads(self):
        chunks = load_course_chunks()
        assert len(chunks) > 50
        assert {c.tutorial for c in chunks} == set(range(1, 9))


class TestRRF:
    def test_agreement_wins(self):
        fused = rrf_fuse([["a", "b", "c"], ["b", "a", "d"]])
        assert fused["a"] > fused["c"]
        assert fused["b"] > fused["c"]
        assert set(fused) == {"a", "b", "c", "d"}

    def test_single_list_preserves_order(self):
        fused = rrf_fuse([["x", "y", "z"]])
        assert fused["x"] > fused["y"] > fused["z"]

    def test_item_in_both_beats_top_of_one(self):
        # 'b' ranked 2nd in both lists should beat 'a' ranked 1st in only one
        fused = rrf_fuse([["a", "b"], ["c", "b"]])
        assert fused["b"] > fused["a"]


class TestHelpers:
    def test_tokenize(self):
        assert _tokenize("Big-O of n^2, O(n log n)!") == ["big", "o", "of", "n", "2", "o", "n", "log", "n"]

    def test_tutorial_week(self):
        assert tutorial_week("tutorial_7") == 7
        assert tutorial_week("hw_3") == 3
        assert tutorial_week("nonsense") == 1

    def test_prompt_contains_boundary_and_context(self):
        hit = Hit(Chunk(id="t::0", text="[T1 › X]\nBody", tutorial=1, source="tutorial_1", section="T1 › X"), 1.0)
        prompt = tutor_system_prompt(2, "Divide & Conquer", ["Merge Sort"], format_context([hit]))
        assert "Merge Sort" in prompt
        assert "Source 1" in prompt
        assert "haven't covered" in prompt.lower()


@pytest.mark.skipif(not INDEX_DIR.exists(), reason="index not built (run build_index.py)")
class TestRetrieverIntegration:
    @pytest.fixture(scope="class")
    def retriever(self):
        from rag_engine import HybridRetriever
        return HybridRetriever()

    def test_finds_relevant_tutorial(self, retriever):
        hits = retriever.retrieve("formal definition of Big-O notation", 8, k=5, rerank=False)
        assert hits and hits[0].chunk.tutorial == 1

    def test_curriculum_filter_blocks_future_material(self, retriever):
        hits = retriever.retrieve("Dijkstra shortest path algorithm", 3, k=8, rerank=False)
        assert all(h.chunk.tutorial <= 3 for h in hits)

    def test_bm25_respects_filter_too(self, retriever):
        ids = retriever._lexical("Dijkstra shortest path negative weights", 3, 10)
        assert all(retriever.chunks[cid].tutorial <= 3 for cid in ids)

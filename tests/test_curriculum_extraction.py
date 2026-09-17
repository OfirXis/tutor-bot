"""The extraction workflow must use the current syllabus and every source page."""
from types import SimpleNamespace

from curriculum import load_curriculum
from tools import extract_curriculum as extractor


def test_extraction_uses_project_root_and_full_pdf():
    week = load_curriculum()['weeks'][-1]
    assert week['week'] == 9
    text = extractor.extract_slide_text(week['source_pdf'])
    assert '[PDF page 1]' in text
    assert '[PDF page 181]' in text
    assert ''.join(extractor.source_batches(text)) == text


def test_generation_uses_shared_topics_and_no_truncated_source():
    week = load_curriculum()['weeks'][5]
    source = 'x' * 13000 + 'LATE PAGE CONTENT'
    calls = []
    class LLM:
        def invoke(self, messages):
            calls.append(messages)
            return SimpleNamespace(content='## Extracted topic\nSource-based notes.')
    notes = extractor.generate_curriculum_notes(week, source, LLM())
    assert len(calls) == 2
    assert 'Breadth-first search' in calls[0][0].content
    assert 'Depth-first search' in calls[0][0].content
    assert 'Dynamic programming' in calls[0][0].content
    assert 'LATE PAGE CONTENT' in calls[-1][-1].content
    assert week['title'] in notes

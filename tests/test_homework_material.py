"""Source integrity and course boundary regression tests for the supplied PDFs."""
import json
from pathlib import Path

import pytest

import rag_engine as rag
from homework_material import (
    homework_context, homework_retrieval_query, extract_problem_statements,
)
from tools import extract_homework


def test_all_actual_pdfs_are_mapped_and_complete():
    homework = rag.load_homework()
    assert [hw['problems'] for hw in homework.values()] == [5, 5, 6, 5, 5]
    assert {Path(hw['problem_pdf']).name for hw in homework.values()} == {
        p.name for p in (rag.HERE / 'material/Homework').glob('*.pdf')
    }
    for hw in homework.values():
        assert 'source_error' not in hw
        assert len(hw['full_problem_text']) > 2000
        assert hw['problem_statements'][-1]['number'] == hw['problems']
    # A problem that continues onto a second page must keep its final subquestions.
    hw1 = homework['hw_1']
    assert 'graph' in hw1['problem_statements'][-1]['text']
    hw3 = homework['hw_3']
    assert hw3['problem_statements'][1]['pages'] == [1, 2]
    assert 'asymptotically equal' in hw3['problem_statements'][1]['text']


def test_homework_context_contains_only_selected_assignment_and_problem():
    hw = rag.load_homework()['hw_2']
    text = homework_context(hw, 'רמז לשאלה 3')
    assert 'HW2_algo.pdf, Problem 3, PDF pages 2' in text
    assert 'bias' in text
    assert 'Ford' not in text
    assert 'Problem 1' not in text
    query = homework_retrieval_query(hw, 'Help me with question 3')
    assert 'bias' in query
    assert homework_context(hw, 'Problem 999') == ''


def test_extractor_preserves_explicit_week_limits(tmp_path, monkeypatch):
    metadata = json.loads(rag.HOMEWORK_FILE.read_text())
    metadata['hw_1']['week'] = 2
    target = tmp_path / 'homework.json'
    target.write_text(json.dumps(metadata))
    monkeypatch.setattr(extract_homework, 'OUTPUT_FILE', target)
    rebuilt = extract_homework.build_homework_database()
    assert rebuilt['hw_1']['week'] == 2
    assert rebuilt['hw_1']['problems'] == 5


def test_missing_pdf_disables_stale_assignment_content(tmp_path, monkeypatch):
    target = tmp_path / 'homework.json'
    target.write_text(json.dumps({'hw_1': {
        'week': 3, 'problem_pdf': 'material/Homework/missing.pdf',
        'full_problem_text': 'stale placeholder',
    }}))
    monkeypatch.setattr(rag, 'HOMEWORK_FILE', target)
    hw = rag.load_homework()['hw_1']
    assert hw['source_error']
    assert hw['full_problem_text'] == ''


@pytest.mark.parametrize('query', [
    'Explain maximum flow', 'Ford-Fulkerson', 'What is a residual graph?',
    'Use Edmonds-Karp', 'הסבר רשתות זרימה', 'מהו חתך מינימלי?',
    "Explain Hall's theorem", "Explain Dilworth's theorem",
])
def test_flow_topics_are_future_until_nine(query):
    assert rag.named_future_topic(query, 8) == 9
    assert rag.named_future_topic(query, 9) == 0


def test_graph_traversal_is_available_for_hw3():
    assert rag.named_future_topic('Explain BFS and DFS', 5) == 6
    assert rag.named_future_topic('Explain BFS and DFS', 6) == 0
    assert 'Breadth-first search' in rag.covered_topics(6)


def test_changed_or_added_tutorial_invalidates_index(tmp_path):
    material = tmp_path / 'english'
    material.mkdir()
    (material / 'tutorial_1.txt').write_text('Original lesson')
    index = tmp_path / 'index'
    index.mkdir()
    chunks = tmp_path / 'chunks.jsonl'
    chunks.touch()
    stamp = index / 'material.sha256'
    stamp.write_text(rag.course_material_digest(material))
    assert not rag.index_needs_rebuild(material, index, chunks)
    (material / 'tutorial_9.txt').write_text('Maximum flow')
    assert rag.index_needs_rebuild(material, index, chunks)


@pytest.mark.skipif(not rag.INDEX_DIR.exists(), reason='course index not built')
def test_real_index_contains_flow_and_filters_it_by_week():
    retriever = rag.HybridRetriever()
    assert any(h.chunk.tutorial == 9 for h in retriever.retrieve(
        'Ford-Fulkerson maximum flow residual network', 9, k=4))
    assert all(h.chunk.tutorial <= 8 for h in retriever.retrieve(
        'Ford-Fulkerson maximum flow residual network', 8, k=8))
    assert retriever.scope_check('Explain max flow', 8) == (True, 9)
    assert not retriever.scope_check('Explain max flow', 9)[0]
    assert not retriever.scope_check('How does BFS find unweighted shortest paths?', 6)[0]


@pytest.mark.parametrize('question', [
    'What is in the homework?', 'Help me solve the homework',
    'Show all the questions', 'מה יש במטלה?',
])
def test_assignment_overview_supplies_real_statements(question):
    from homework_material import selected_statements, homework_clarification
    hw = rag.load_homework()['hw_1']
    assert len(selected_statements(hw, question)) == hw['problems']
    assert homework_clarification(hw, question) is None
    assert 'Problem 1' in homework_context(hw, question)


@pytest.mark.parametrize(('question', 'number'), [
    ('Help me with the first question', 1), ('Explain question two', 2),
    ('הסבר את השאלה הראשונה', 1), ('3', 3),
])
def test_ordinary_problem_references(question, number):
    from homework_material import problem_numbers
    assert problem_numbers(question) == {number}


def test_followup_requires_explicit_selection_and_preserves_new_topics():
    from homework_material import resolve_homework_followup
    assert resolve_homework_followup('What next?', []) == 'What next?'
    assert 'problem: 3' in resolve_homework_followup('What next?', [3])
    for question in ['Explain Dijkstra', 'Help with problem 2', 'What is in the homework?']:
        assert resolve_homework_followup(question, [3]) == question


class NoLectureEvidence:
    def scope_check(self, question, week):
        required = rag.named_future_topic(question, week)
        return bool(required), required

    def retrieve(self, *args, **kwargs):
        return []


@pytest.mark.parametrize('question', [
    'What is in the homework?', 'Guide me through problem 1', 'What does question 3 ask?',
])
def test_assignment_is_evidence_even_without_lecture_hits(question):
    hw = rag.load_homework()['hw_1']
    decision = rag.prepare_retrieval(question, hw['week'], NoLectureEvidence(), hw)
    assert decision.status == 'answer'
    assert decision.assignment_count > 0
    assert decision.hits == []


def test_assignment_evidence_cannot_unlock_future_or_unrelated_requests():
    hw = rag.load_homework()['hw_1']
    retriever = NoLectureEvidence()
    assert rag.prepare_retrieval('Use Dijkstra for problem 1', 3, retriever, hw).status == 'future'
    assert rag.prepare_retrieval('Explain blockchain mining', 3, retriever, hw).status == 'insufficient'
    assert rag.prepare_retrieval('What is in the homework?', 2, retriever, hw).status == 'future'
    assert rag.prepare_retrieval('Problem 99', 3, retriever, hw).clarification == 'unknown_problem'
    unavailable = {**hw, 'source_error': 'missing PDF', 'problem_statements': []}
    assert rag.prepare_retrieval('What is in the homework?', 3, retriever, unavailable).status == 'insufficient'


def test_uncited_homework_reply_gets_one_checked_retry():
    from types import SimpleNamespace
    class LLM:
        calls = 0
        def stream(self, messages):
            self.calls += 1
            yield SimpleNamespace(content='Identify the inputs.' if self.calls == 1 else
                                  'Identify the inputs described in the problem. (Assignment 1)')
    llm = LLM()
    answer = rag.generate_scoped_answer(llm, [], NoLectureEvidence(), 3, 0, 1)
    assert '(Assignment 1)' in answer
    assert llm.calls == 2


def test_homework_retry_cannot_introduce_future_material():
    from types import SimpleNamespace
    class LLM:
        calls = 0
        def stream(self, messages):
            self.calls += 1
            yield SimpleNamespace(content='Identify the inputs.' if self.calls == 1 else
                                  'Use Dijkstra. (Assignment 1)')
    with pytest.raises(rag.FutureMaterialError):
        rag.generate_scoped_answer(LLM(), [], NoLectureEvidence(), 3, 0, 1)


def test_failed_homework_citation_retry_is_still_withheld():
    from types import SimpleNamespace
    class LLM:
        calls = 0
        def stream(self, messages):
            self.calls += 1
            yield SimpleNamespace(content='Uncited explanation.')
    llm = LLM()
    with pytest.raises(rag.EvidenceError):
        rag.generate_scoped_answer(llm, [], NoLectureEvidence(), 3, 0, 1)
    assert llm.calls == 2


def test_weak_homework_retrieval_fetches_mapped_prerequisites():
    class Retriever(NoLectureEvidence):
        queries = []
        def retrieve(self, query, max_tutorial, **kwargs):
            self.queries.append(query)
            if 'Selected problem concepts' in query:
                return []
            assert max_tutorial == 3
            return [rag.Hit(rag.Chunk('prerequisite', 'Algorithm analysis and divide and conquer.',
                                     2, 'tutorial_2', 'Divide and conquer'), 0.9, 0.9)]
    retriever = Retriever()
    decision = rag.prepare_retrieval('Guide me through problem 1', 3, retriever, rag.load_homework()['hw_1'])
    assert decision.status == 'answer'
    assert len(retriever.queries) == 2
    assert decision.hits[0].chunk.id == 'prerequisite'


def test_hw5_concept_answer_retries_with_source_citation_not_assignment():
    from types import SimpleNamespace
    class LLM:
        calls = 0
        def stream(self, messages):
            self.calls += 1
            if self.calls == 2:
                assert '(Source 1)' in messages[-1].content
                assert 'Assignment 1' not in messages[-1].content
            yield SimpleNamespace(content='Dijkstra finds shortest paths.' if self.calls == 1 else
                                  'Dijkstra finds shortest paths. (Source 1)')
    llm = LLM()
    answer = rag.generate_scoped_answer(llm, [], NoLectureEvidence(), 9, 1, 0, retry_citations=True)
    assert '(Source 1)' in answer
    assert llm.calls == 2


def test_topic_specific_help_does_not_require_a_homework_problem_number():
    from homework_material import homework_clarification
    hw = rag.load_homework()['hw_5']
    for question in ['Help me with flow', 'Guide me through flow conservation']:
        assert homework_clarification(hw, question) is None
    for question in ['Help me', 'I am stuck', 'Give me a hint', 'Help with this problem']:
        assert homework_clarification(hw, question) == 'choose_problem'

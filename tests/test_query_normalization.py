"""Term cleanup must help retrieval without changing constraints or code."""
import json
from types import SimpleNamespace

import pytest

import rag_engine as rag
from query_normalization import normalize_question


class ApproveEdits:
    def invoke(self, messages):
        candidates = json.loads(messages[-1].content)['candidates']
        return SimpleNamespace(content=json.dumps({'accept': [c['id'] for c in candidates]}))


@pytest.mark.parametrize(('question', 'expected'), [
    ('Explain dc', 'Explain Divide and conquer'),
    ('How does D&C work?', 'How does Divide and conquer work?'),
    ('Explain devide and conqer', 'Explain divide and conquer'),
    ('Explain dijsktra', 'Explain dijkstra'),
    ('Explain dynamic programing', 'Explain dynamic programming'),
    ('Compare DP and dc', 'Compare Dynamic programming and Divide and conquer'),
    ('Problem 4: without dijsktra, give only a hint.',
     'Problem 4: without dijkstra, give only a hint.'),
])
def test_small_term_edits(question, expected):
    assert normalize_question(question, ApproveEdits()) == expected


def test_formatted_code_math_urls_and_identifiers_are_untouched():
    question = ('Explain devide: `dc`, ```python\ndc = dijsktra()\n``` '
                '$dc + 4$ $$dc = 2$$ \\(dc\\) \\[dc\\] '
                'https://example.org/dc my_dc dc2 _dc')
    assert normalize_question(question, ApproveEdits()) == question.replace('devide', 'divide')


@pytest.mark.parametrize('question', ['What is an algorithm?', 'Why does that work?',
                                     'Explain blockchain mining', 'Explain `dc', '',
                                     'Explain DC voltage', 'Where is Washington DC?'])
def test_clean_or_unknown_questions_do_not_call_model(question):
    class MustNotCall:
        def invoke(self, messages):
            pytest.fail('No candidate means no model call')
    assert normalize_question(question, MustNotCall()) == question


@pytest.mark.parametrize('response', [
    'Here is a completely different question', '{"accept": [99]}',
    '{"accept": [-1]}', '{"accept": [true]}', '{"accept": [0, 0]}',
    '{"accept": "0"}', '{"question": "Explain Dijkstra"}', 'null',
])
def test_invalid_output_preserves_original(response):
    llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content=response))
    assert normalize_question('Explain dc without code', llm) == 'Explain dc without code'


def test_model_can_leave_ambiguous_or_non_course_terms_alone():
    llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content='{"accept": []}'))
    assert normalize_question('Explain DC voltage', llm) == 'Explain DC voltage'


def test_missing_or_failed_model_preserves_original():
    class Broken:
        def invoke(self, messages):
            raise ConnectionError('offline')
    assert normalize_question('Explain dc') == 'Explain dc'
    assert normalize_question('Explain dc', Broken()) == 'Explain dc'


class Retriever:
    def scope_check(self, question, week):
        required = rag.named_future_topic(question, week)
        return bool(required), required

    def retrieve(self, query, max_tutorial, **kwargs):
        self.query = query
        return [rag.Hit(rag.Chunk('dc', 'Divide and conquer splits a problem into subproblems.',
                                  2, 'tutorial_2', 'Divide and conquer'), 0.9, 0.9)]


def test_corrected_terms_reach_retrieval_and_evidence_filter():
    retriever = Retriever()
    decision = rag.prepare_retrieval('Explain devide and conqer', 2, retriever,
                                     normalization_llm=ApproveEdits())
    assert decision.status == 'answer'
    assert retriever.query == decision.normalized_question == 'Explain divide and conquer'


@pytest.mark.parametrize(('question', 'week', 'future_week'), [
    ('Explain dc', 1, 2), ('Explain dijsktra', 6, 8),
    ('Explain dynamic programing', 2, 4),
])
def test_corrected_future_topics_are_still_blocked(question, week, future_week):
    decision = rag.prepare_retrieval(question, week, Retriever(), normalization_llm=ApproveEdits())
    assert decision.status == 'future'
    assert decision.future_week == future_week
    assert not decision.hits


def test_correcting_exclusion_does_not_request_future_method():
    decision = rag.prepare_retrieval('Explain dc without dijsktra', 2, Retriever(),
                                     normalization_llm=ApproveEdits())
    assert decision.status == 'answer'
    assert decision.normalized_question == 'Explain Divide and conquer without dijkstra'


def test_original_is_retained_in_generation_message():
    original = 'Explain dc without code'
    message = rag.question_message(original, 'Explain Divide and conquer without code')
    assert message.startswith(original + '\n')
    assert 'Divide and conquer without code' in message
    assert rag.question_message(original, original) == original

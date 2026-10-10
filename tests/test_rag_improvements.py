"""Evidence, intent and curriculum regressions; no generation or translation APIs."""

import pytest

import curriculum
import rag_engine as rag
from homework_material import homework_retrieval_query, problem_topic_names, homework_clarification


@pytest.mark.parametrize('question', [
    'Find an unweighted shortest path without Dijkstra',
    'Do not use Dijkstra. Explain BFS.',
    "Don't use Dijkstra; use BFS",
    'Explain BFS rather than Dijkstra',
    'Explain BFS without using Dijkstra or Bellman-Ford',
    'הסבר חיפוש לרוחב בלי להשתמש בדייקסטרה',
    'אל תשתמש בדייקסטרה',
])
def test_excluding_a_future_method_is_not_requesting_it(question):
    assert rag.named_future_topic(question, 6) == 0


@pytest.mark.parametrize('question', [
    'Why does Dijkstra not work with negative weights?',
    'Explain Dijkstra without proofs',
    "Without Dijkstra's code, explain its idea",
    'Without Dijkstra, explain how it works',
    'Without Dijkstra, explain Bellman-Ford',
    'Without Dijkstra first; then explain Dijkstra',
    'Solve it, but not without Dijkstra',
    'למה דייקסטרה לא עובד עם משקלים שליליים?',
])
def test_negation_cannot_unlock_requests_for_future_material(question):
    assert rag.named_future_topic(question, 6) == 8


def test_json_is_the_shared_curriculum_source():
    data=curriculum.load_curriculum()
    metadata=rag.load_meta()
    for week in data['weeks']:
        assert metadata[f"tutorial_{week['week']}"]['topics']==rag.covered_topics(week['week'])
        assert (rag.HERE / week['source_pdf']).is_file()
    assert "Dijkstra's algorithm" not in rag.covered_topics(6)
    assert "Dijkstra's algorithm" in rag.covered_topics(8)
    for hw in rag.load_homework().values():
        for ids in hw['problem_topics'].values():
            assert all(data['topics_by_id'][key]['week'] <= hw['week'] for key in ids)


def test_homework_uses_only_referenced_problem_concepts():
    hw=rag.load_homework()['hw_5']
    q='Please help with problem 4 without giving me the solution.'
    query=homework_retrieval_query(hw,q)
    assert query.startswith(q)
    assert 'Bipartite matching' in query
    assert 'Ford-Fulkerson' not in query
    assert problem_topic_names(hw,q)==['Bipartite matching','Flow networks']
    direct='Why do residual networks have reverse edges?'
    assert homework_retrieval_query(hw,direct)==direct
    assert homework_clarification(hw,'Give me a hint')=='choose_problem'
    assert homework_clarification(hw,'Problem 99')=='unknown_problem'


def hit(text, similarity, score=1.0, week=1):
    return rag.Hit(rag.Chunk('test',text,week,'tutorial_1','Algorithm Definition'),score,similarity)


def test_rank_scores_cannot_pass_as_relevance():
    assert not rag.supported_hits([hit('unrelated',0.1,score=1.0)],1)
    assert rag.supported_hits([hit('relevant',0.8,score=0.001)],1)
    assert not rag.supported_hits([hit('unknown',None,score=1.0)],1)
    assert not rag.supported_hits([hit('future',0.9,week=9)],1)


def test_unrelated_technical_vocabulary_is_not_supporting_evidence():
    candidate=hit("Prim grows a minimum spanning tree using a priority queue.",0.64)
    assert not rag.supported_hits([candidate],9,query='Explain blockchain mining')


@pytest.mark.parametrize('answer', ['Answer (Source 99)', 'Answer (Source 0)',
                                   'Answer (Assignment 2)', 'An uncited explanation.'])
def test_missing_or_fabricated_citations_are_rejected(answer):
    with pytest.raises(rag.EvidenceError):
        rag.validate_citations(answer,source_count=2,assignment_count=1)


@pytest.mark.parametrize(('grouped', 'single'), [
    ('Trees (Source 2, Source 3).', 'Trees (Source 2) (Source 3).'),
    ('Trees (Sources 1 and 2).', 'Trees (Source 1) (Source 2).'),
    ('Mixed (Source 1; Assignment 1).', 'Mixed (Source 1) (Assignment 1).'),
    ('עצים (מקור 2, מקור 3).', 'עצים (מקור 2) (מקור 3).'),
    ('Single (Source 1) stays.', 'Single (Source 1) stays.'),
])
def test_grouped_citations_are_split_into_single_ids(grouped, single):
    assert rag.split_grouped_citations(grouped) == single


def test_every_id_in_a_grouped_citation_is_validated():
    rag.validate_citations('Trees (Source 2, Source 3).', 3)
    with pytest.raises(rag.EvidenceError):
        rag.validate_citations('Trees (Source 2, Source 9).', 3)


def test_hebrew_answers_show_hebrew_citation_labels():
    text = 'BFS (Source 1 — Tutorial 6) ותרגיל (Assignment 2).'
    assert rag.localize_citations(text, 'he') == 'BFS (מקור 1 — Tutorial 6) ותרגיל (מטלה 2).'
    assert rag.localize_citations(text, 'en') == text
    rag.validate_citations(rag.localize_citations(text, 'he'), 1, 2)


def test_valid_citations_do_not_claim_entailment():
    rag.validate_citations('Hint (Source 2). Problem statement (Assignment 1).',2,1)
    rag.validate_citations('רמז (מקור 2). שאלה (מטלה 1).',2,1)


@pytest.mark.skipif(not rag.INDEX_DIR.exists(),reason='index not built')
def test_actual_cosine_scores_and_safe_exclusion():
    retriever=rag.HybridRetriever()
    hits=retriever.retrieve('What is the formal definition of Big-O?',1,k=2)
    assert all(-1 <= h.similarity <= 1 for h in hits)
    assert all(h.score==h.similarity for h in hits)
    assert hits[0].score != 1.0
    decision=rag.prepare_retrieval('Find a shortest path in an unweighted graph without Dijkstra',6,retriever)
    assert decision.status=='answer'
    assert any('BFS' in h.chunk.section for h in decision.hits)
    assert all(h.chunk.tutorial<=6 for h in decision.hits)
    assert rag.prepare_retrieval('Explain blockchain mining',9,retriever).status=='insufficient'


def test_named_course_problem_does_not_require_homework_number():
    assert homework_clarification(rag.load_homework()['hw_2'], 'Explain the coin change problem') is None


def test_hint_constraints_are_not_mistaken_for_missing_topic_evidence():
    question='Give me one small hint for problem 4. Do not give the full solution.'
    candidate=hit('A bipartite matching can be represented as a flow network.',0.8,week=9)
    assert rag.supported_hits([candidate],9,query=question)


@pytest.mark.parametrize('question', ['Explain Dijkstra to a beginner',
                                     'Teach me about Dijkstra',
                                     'Explain Dijkstra in simple terms'])
def test_delivery_instructions_do_not_discard_topic_evidence(question):
    candidate = hit('Dijkstra finds shortest paths with nonnegative weights.', 0.78, week=8)
    assert rag.supported_hits([candidate], 9, query=question)


def test_named_topic_fallback_keeps_unrelated_content_constraints():
    class Retriever:
        def scope_check(self, question, week):
            return False, 0
        def retrieve(self, query, max_tutorial, **kwargs):
            return [hit('Dijkstra finds shortest paths with nonnegative weights.', 0.78, week=8)]
    assert rag.prepare_retrieval('Explain Dijkstra blockchain mining', 9, Retriever()).status == 'insufficient'


@pytest.mark.skipif(not rag.INDEX_DIR.exists(), reason='index not built')
@pytest.mark.parametrize(('question', 'week', 'source'), [
    ('Explain Dijkstra to a beginner', 9, 'tutorial_8'),
    ('what is dijkstra', 9, 'tutorial_8'),
    ('Teach me about greedy algorithms', 3, 'tutorial_3'),
    ('What is big o?', 1, 'tutorial_1'),
])
def test_real_index_accepts_common_english_phrasings(question, week, source):
    decision = rag.prepare_retrieval(question, week, rag.HybridRetriever())
    assert decision.status == 'answer'
    assert any(h.chunk.source == source for h in decision.hits)


@pytest.mark.skipif(not rag.INDEX_DIR.exists(), reason='index not built')
@pytest.mark.parametrize('homework_mode', [False, True])
@pytest.mark.parametrize(('question', 'source'), [
    ('what is flow', 'tutorial_9'),
    ('what is dp', 'tutorial_4'),
    ('give me a dc example', 'tutorial_2'),
    ('Help me understand dc', 'tutorial_2'),
])
def test_week_nine_questions_work_without_normalization_model(question, source, homework_mode):
    homework = rag.load_homework()['hw_5'] if homework_mode else None
    result = rag.prepare_retrieval(question, 9, rag.HybridRetriever(), homework)
    assert result.status == 'answer'
    assert any(h.chunk.source == source for h in result.hits)
    if 'example' in question:
        assert 'Worked Examples' in result.hits[0].chunk.section


@pytest.mark.parametrize(('question', 'week', 'future_week'), [
    ('give me a dc example', 1, 2), ('what is dp', 3, 4),
])
def test_shorthand_cannot_bypass_week_boundary_without_model(question, week, future_week):
    result = rag.prepare_retrieval(question, week, object())
    assert result.status == 'future'
    assert result.future_week == future_week

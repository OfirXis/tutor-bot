"""Tests for Hebrew detection and translation safety."""
from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from rag_engine import is_hebrew, translate, translate_with_fallback


class PassthroughLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        prompt = messages[-1].content
        protected = prompt.split('"""\n', 1)[1].rsplit('\n"""', 1)[0]
        return AIMessage(content=protected)


class FailingLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        raise ConnectionError("translator unavailable")


class DroppingPlaceholderLLM:
    def invoke(self, messages):
        return AIMessage(content="translated text without its protected marker")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("איך עובד האלגוריתם של דייקסטרה?", True),
        ("איך Dijkstra עובד?", True),
        ("Explain ערימה in English", False),
        ("How does Dijkstra work?", False),
        ("123!?", False),
        ("שׁ", True),  # Hebrew presentation form, normalized to ש + shin dot.
    ],
)
def test_predominant_language_detection(text, expected):
    assert is_hebrew(text) is expected


def test_translation_preserves_fenced_inline_code_and_math():
    fenced = "```python\nif x < 3:\n    print(x)\n```"
    inline = "`heapq.heappush(queue, item)`"
    inline_math = "$O(n \\log n)$"
    block_math = "$$T(n)=2T(n/2)+n$$"
    text = f"הסבר {inline} ואת {inline_math}:\n{fenced}\n{block_math}"

    result = translate(text, "en", PassthroughLLM())

    for protected_part in (fenced, inline, inline_math, block_math):
        assert protected_part in result


def test_translation_rejects_dropped_protected_content():
    with pytest.raises(ValueError, match="dropped protected"):
        translate("הסבר `value`", "en", DroppingPlaceholderLLM())


def test_translation_uses_fallback_model():
    primary = FailingLLM()
    fallback = PassthroughLLM()

    # Neutral text: a curriculum alias would trip the lost-course-term check.
    result = translate_with_fallback("יש לי שאלה", "en", primary, fallback)

    assert result == "יש לי שאלה"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_translation_reports_when_both_models_fail():
    with pytest.raises(RuntimeError, match="both translation models failed"):
        translate_with_fallback("מהו אלגוריתם?", "en", FailingLLM(), FailingLLM())


def test_translation_validates_target_language():
    with pytest.raises(ValueError, match="target"):
        translate("text", "fr", PassthroughLLM())



def test_local_translator_is_independent_of_tutor_and_openai(monkeypatch):
    import langchain_ollama
    import rag_engine as rag
    calls = []
    monkeypatch.setenv('OPENAI_API_KEY', 'test-unused')
    monkeypatch.setenv('OLLAMA_LLM_MODEL', 'english-tutor')
    monkeypatch.setenv('TRANSLATION_PROVIDER', 'ollama')
    monkeypatch.setenv('TRANSLATION_OLLAMA_MODEL', 'hebrew-translator')
    monkeypatch.setenv('TRANSLATION_OLLAMA_BASE_URL', 'http://localhost:11435')
    monkeypatch.setattr(langchain_ollama, 'ChatOllama', lambda **kw: calls.append(kw) or kw)
    result = rag.get_translation_llm()
    assert result['model'] == 'hebrew-translator'
    assert result['base_url'] == 'http://localhost:11435'
    assert result['temperature'] == 0
    assert result['reasoning'] is False
    assert result['num_predict'] > 0
    assert result['client_kwargs']['timeout'] > 0
    assert len(calls) == 1


def test_openrouter_serves_tutor_and_translator(monkeypatch):
    import rag_engine as rag
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-test')
    monkeypatch.setenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
    monkeypatch.delenv('TRANSLATION_OPENROUTER_MODEL', raising=False)
    tutor = rag.get_llm(provider='openrouter')
    translator = rag.get_translation_llm('openrouter')
    for llm in (tutor, translator):
        assert llm.model_name == 'openai/gpt-4o-mini'
        assert str(llm.openai_api_base) == rag.OPENROUTER_BASE_URL
        assert llm.openai_api_key.get_secret_value() == 'sk-or-test'
    assert translator.temperature == 0
    monkeypatch.delenv('OPENROUTER_API_KEY')
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        rag.get_llm(provider='openrouter')
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        rag.get_translation_llm('openrouter')


def test_translation_provider_validation_and_tutor_mode(monkeypatch):
    import rag_engine as rag
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert rag.get_translation_llm('tutor') is None
    assert rag.get_translation_llm('auto') is None
    with pytest.raises(ValueError, match='requires OPENAI_API_KEY'):
        rag.get_translation_llm('openai')
    with pytest.raises(ValueError, match='Unknown translation provider'):
        rag.get_translation_llm('invalid')


def test_hebrew_prose_fallback_keeps_math_code_and_citations_exact():
    class SmallTranslator:
        def invoke(self, messages):
            if 'TEXT TO TRANSLATE' in messages[-1].content:
                return AIMessage(content='תרגום ללא סימונים')
            return AIMessage(content='קטע מתורגם')
    original = 'A flow obeys $0 \\le f(e) \\le c(e)$ and uses `flow`. (Source 1)'
    translated = translate(original, 'he', SmallTranslator())
    for protected in ['$0 \\le f(e) \\le c(e)$', '`flow`', '(Source 1)']:
        assert translated.count(protected) == 1
    assert 'קטע מתורגם' in translated


def test_hebrew_fallback_rejects_untranslated_prose():
    class Broken:
        def invoke(self, messages):
            return AIMessage(content='Untranslated prose')
    with pytest.raises(ValueError, match='did not return Hebrew'):
        translate('A flow obeys $f(e)$ (Source 1)', 'he', Broken())


class StructuredLocal:
    model = 'local-translator'
    format = {'type': 'object'}

    def __init__(self, translations, done_reason=None):
        self.translations = translations
        self.done_reason = done_reason
        self.calls = 0

    def stream(self, messages, **kwargs):
        import json
        self.calls += 1
        yield AIMessage(content=json.dumps({'translation': self.translations}, ensure_ascii=False),
                        response_metadata={'done_reason': self.done_reason})


def test_local_topic_question_avoids_model_topic_drift():
    llm = StructuredLocal([])
    assert translate('ספר לי על הפרד ומשול', 'en', llm) == 'Explain Divide and conquer.'
    assert llm.calls == 0


def test_local_batch_preserves_protected_spans_in_one_call():
    llm = StructuredLocal('זרימה מקיימת ⟦0⟧ על כל קשת. (מקור 1)')
    progress = []
    result = translate('A flow satisfies $f(e)$ on every edge. (Source 1)', 'he', llm,
                       progress=lambda *args: progress.append(args))
    assert result == 'זרימה מקיימת $f(e)$ על כל קשת. (Source 1)'
    assert llm.calls == 1
    assert progress


@pytest.mark.parametrize('output', [
    'להלן התרגום: הפרד ומשול',
    'פ-ר-ד-ו-מ-ש-ו-ל',
    'Dynamic programming solves the problem.',
    'תכנות דינמי פותר בעיות.',
])
def test_local_rejects_corrupt_or_wrong_topic_translation(output):
    with pytest.raises(ValueError):
        translate('Divide and conquer solves problems.', 'he', StructuredLocal(output))


def test_local_rejects_partial_output_and_does_not_retry_fragments():
    llm = StructuredLocal('זרימה', done_reason='length')
    with pytest.raises(ValueError, match='token limit'):
        translate('A flow satisfies $f(e)$ on every edge.', 'he', llm)
    assert llm.calls == 1


def test_local_translation_deadline(monkeypatch):
    import rag_engine
    readings = iter([0, 46])
    monkeypatch.setattr(rag_engine.time, 'monotonic', lambda: next(readings))
    monkeypatch.setenv('TRANSLATION_TIMEOUT_SECONDS', '45')
    with pytest.raises(TimeoutError, match='time limit'):
        translate('A problem.', 'he', StructuredLocal('בעיה.'))


@pytest.mark.parametrize(('source', 'expected'), [
    ('מה זה זרימה?', 'Explain flow.'),
    ('מה זה dp?', 'Explain Dynamic programming.'),
    ('תן לי דוגמה להפרד ומשול', 'Give an example of Divide and conquer.'),
])
def test_short_hebrew_requests_preserve_topic_and_intent(source, expected):
    from translation_support import course_question_translation
    assert course_question_translation(source) == expected


def test_translation_accepts_hebrew_for_topic_without_curated_hebrew_alias():
    from translation_support import validate_translation
    validate_translation('Merge sort sorts an array.', 'מיון מיזוג ממיין מערך.', 'he')
    validate_translation('Dynamic programming saves work.', 'התכנות הדינמי חוסך עבודה.', 'he')


def test_translation_rejects_json_leak_and_changed_homework_number():
    from translation_support import validate_translation
    with pytest.raises(ValueError, match='JSON'):
        validate_translation('A flow.', '{"text": "זרימה"}', 'he')
    with pytest.raises(ValueError, match='numbers'):
        validate_translation('עזרה בשאלה 4', 'Help with question 2', 'en')


def test_local_translation_repairs_invalid_output_once():
    class Repair(StructuredLocal):
        def stream(self, messages, **kwargs):
            self.translations = 'Untranslated text' if self.calls == 0 else 'בעיה.'
            yield from super().stream(messages, **kwargs)
    llm = Repair('')
    assert translate('A problem.', 'he', llm) == 'בעיה.'
    assert llm.calls == 2


class CloudTranslator:
    """Chat translator with no Ollama format: replies with each queued output in turn."""
    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return AIMessage(content=self.outputs.pop(0))


def test_cloud_hebrew_answer_is_validated_and_repaired_once():
    llm = CloudTranslator('A problem.', 'בעיה.')
    assert translate('A problem.', 'he', llm) == 'בעיה.'
    assert llm.calls == 2
    with pytest.raises(ValueError, match='Hebrew prose'):
        translate('A problem.', 'he', CloudTranslator('A problem.', 'Still English.'))


def test_tutor_ollama_model_reused_as_translator_takes_the_local_path():
    class ChatOllama(StructuredLocal):
        format = None  # The tutor model has no translation JSON schema of its own.
    llm = ChatOllama('בעיה.')
    assert translate('A problem.', 'he', llm) == 'בעיה.'
    assert llm.calls == 1


def test_local_fallback_is_only_an_installed_translation_preset():
    from local_models import TRANSLATION_MODELS, translation_fallback_model
    small = next(model for model in TRANSLATION_MODELS if '1.7B' in model)
    large = next(model for model in TRANSLATION_MODELS if '12B' in model)
    assert translation_fallback_model(small, [small, large]) == large
    assert translation_fallback_model(small, [small]) is None
    assert translation_fallback_model(large, [small, large]) is None


def test_long_translation_preserves_all_input_and_protected_content():
    import json
    class Echo(StructuredLocal):
        def stream(self, messages, **kwargs):
            source = messages[-1].content
            assert len(source) <= 700
            self.translations = source
            yield from super().stream(messages, **kwargs)
    source = ('A complete paragraph with a long explanation. ' * 15 + '\n\n') * 4
    source += '```python\n' + 'value = 1\n' * 100 + '```\n(Source 1)'
    llm = Echo('')
    assert translate(source, 'en', llm) == source
    assert llm.calls > 1


@pytest.mark.parametrize('output', ['בעיה. (מקור 99)', 'בעיה.', 'בעיה. (מקור 1) (מקור 2)'])
def test_local_citation_drift_keeps_translation_and_restores_originals(output):
    llm = StructuredLocal(output)
    result = translate('A problem. (Source 1)', 'he', llm)
    assert result == 'בעיה.\n\n(Source 1)'
    assert llm.calls == 1


def test_local_invented_citation_is_removed():
    llm = StructuredLocal('בעיה. (מקור 99)')
    assert translate('A problem.', 'he', llm) == 'בעיה.'


def test_local_reordered_citations_restore_original_block_references():
    llm = StructuredLocal('בעיה (משימה 2) והסבר (מקור 1).')
    result = translate('A problem (Source 1) and explanation (Assignment 2).', 'he', llm)
    assert result.endswith('\n\n(Source 1) (Assignment 2)')
    assert 'בעיה' in result
    assert llm.calls == 1


def test_translategemma_uses_native_single_user_prompt_and_plain_output():
    class Native:
        model = 'translategemma:4b'
        format = ''
        def stream(self, messages, **kwargs):
            assert len(messages) == 1
            assert messages[0].type == 'human'
            assert 'English (en) to Hebrew (he)' in messages[0].content
            assert '\n\n\nA flow satisfies ⟦0⟧. (Source 1)' in messages[0].content
            assert kwargs['format'] == ''
            yield AIMessage(content='זרימה מקיימת ⟦0⟧. (מקור 1)')
    assert translate('A flow satisfies $f(e)$. (Source 1)', 'he', Native()) == 'זרימה מקיימת $f(e)$. (Source 1)'


def test_translategemma_prompt_sets_hebrew_source_for_english_output():
    from translation_support import translategemma_prompt
    prompt = translategemma_prompt('עזור לי בשאלה 4', 'en')
    assert 'Hebrew (he) to English (en)' in prompt
    assert prompt.endswith('\n\n\nעזור לי בשאלה 4')


def test_installer_aliases_keep_existing_models_and_add_four_billion_model():
    from tools.install_translation_models import MODELS
    assert MODELS['4b'] == 'translategemma:4b'
    assert '1.7B' in MODELS['1.7b']
    assert '12B' in MODELS['12b']


def test_translation_restores_assignment_citation_from_hebrew_synonym():
    llm = StructuredLocal('הסבר המטלה. (משימה 1)')
    assert translate('Explain the assignment. (Assignment 1)', 'he', llm) == 'הסבר המטלה. (Assignment 1)'


def test_translation_glossary_only_normalizes_explicit_source_concept():
    from translation_support import normalize_translation_terms
    assert normalize_translation_terms('Divide and conquer', 'חלוק ושליטה', 'he') == 'הפרד ומשול'
    assert normalize_translation_terms('An unrelated phrase', 'חלוק ושליטה', 'he') == 'חלוק ושליטה'
    assert normalize_translation_terms('הפרד ומשול', 'Divide and conquer', 'en') == 'Divide and conquer'


def test_translategemma_preserves_course_glossary_and_restores_bare_citation():
    class Native:
        model = 'translategemma:4b'
        format = ''
        def stream(self, messages, **kwargs):
            assert 'Merge Sort' in messages[-1].content
            yield AIMessage(content='דוגמה של מיזוג ממוין מופיעה במקור 2.')
    assert translate('An example of Merge Sort is in (Source 2).', 'he', Native()) == 'דוגמה של מיון מיזוג מופיעה ב(Source 2).'


def test_translategemma_bare_citation_drift_is_repaired():
    class Native:
        model = 'translategemma:4b'
        format = ''
        def stream(self, messages, **kwargs):
            yield AIMessage(content='הסבר במקור 99.')
    result = translate('Explanation in (Source 2).', 'he', Native())
    assert result.endswith('\n\n(Source 2)')
    assert '99' not in result
    assert 'הסבר' in result


def test_native_translator_repairs_dropped_math_with_identical_original_formula():
    class Native:
        model = 'translategemma:4b'
        format = ''
        calls = 0
        def stream(self, messages, **kwargs):
            self.calls += 1
            if self.calls == 1:
                yield AIMessage(content='זמן הריצה הוא ללא הנוסחה.')
            else:
                assert '$T(n)$' in messages[0].content
                yield AIMessage(content='זמן הריצה הוא $T(n)$.')
    llm = Native()
    assert translate('The running time is $T(n)$.', 'he', llm) == 'זמן הריצה הוא $T(n)$.'
    assert llm.calls == 2


def test_native_math_repair_rejects_changed_formula():
    class Native:
        model = 'translategemma:4b'
        format = ''
        calls = 0
        def stream(self, messages, **kwargs):
            self.calls += 1
            yield AIMessage(content='זמן הריצה הוא $T(n+1)$.')
    llm = Native()
    with pytest.raises(ValueError, match='changed protected code or math'):
        translate('The running time is $T(n)$.', 'he', llm)
    assert llm.calls == 2


def test_hebrew_wording_is_not_restricted_to_curriculum_alias_list():
    from translation_support import validate_translation
    validate_translation('Divide and conquer solves subproblems.', 'פיצול הבעיה ופתרון רקורסיבי של תת הבעיות.', 'he')
    with pytest.raises(ValueError, match='different course concept'):
        validate_translation('Divide and conquer solves subproblems.', 'תכנות דינמי פותר בעיות.', 'he')
    with pytest.raises(ValueError, match='lost the requested course term'):
        validate_translation('הסבר הפרד ומשול', 'Explain dynamic programming', 'en')


def test_translation_error_reason_distinguishes_output_from_model_availability():
    from translation_support import translation_error_kind
    assert translation_error_kind(ValueError('Translator changed source citations')) == 'invalid'
    assert translation_error_kind(TimeoutError('slow')) == 'timeout'
    assert translation_error_kind(ConnectionError('offline')) == 'connection'
    assert translation_error_kind(RuntimeError('model not found')) == 'missing'


def test_full_source_titles_use_the_same_citation_validation_as_translation():
    from rag_engine import validate_citations, EvidenceError
    validate_citations('(Source 1 — Tutorial 2 — Divide & Conquer › Core Concepts) An explanation.', 1)
    with pytest.raises(EvidenceError, match='not supplied'):
        validate_citations('(Source 99 — Tutorial 2 — Core Concepts) An explanation.', 1)

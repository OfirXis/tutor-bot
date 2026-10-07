"""Validation and conservative fast paths for local Hebrew translation."""
from __future__ import annotations
import re
from curriculum import course_info, load_curriculum

# Code and math are restored verbatim, so they are excluded from prose checks.
_PROTECTED_SPANS = re.compile(r'```[\s\S]*?```|`[^`]*`|\$\$[\s\S]*?\$\$|\$[^$\n]*\$')


def course_question_translation(text: str) -> str | None:
    """Translate only a complete, unambiguous short course-topic request."""
    match = re.fullmatch(r'\s*(תן(?: לי)? דוגמ[הא](?: ל| של)?|תני(?: לי)? דוגמ[הא](?: ל| של)?|ספר(?:י)? לי על|הסבר(?:י)?(?: לי)?(?: את)?|מה (?:זה|הוא|היא)|איך עובד(?:ת)?)\s*(.+?)\s*[?.!]?\s*', text)
    if not match:
        return None
    topic_text = match[2].rstrip('?.!').strip()
    example = match[1].startswith(('תן', 'תני'))
    if example:
        topic_text = re.sub(r'^ל(?=[א-תA-Za-z])', '', topic_text)
    from query_normalization import expand_course_abbreviations
    topic_text = expand_course_abbreviations(topic_text)
    for topic in load_curriculum()['topics_by_id'].values():
        for alias in (topic['name'], *topic['aliases']):
            if topic_text.casefold() == alias.casefold():
                prefix = ('Give an example of {}.' if example else
                          'How does {} work?' if match[1].startswith('איך') else 'Explain {}.')
                return prefix.format(topic['name'])
    english = {he: en for en, he in course_info()['glossary'].items()}.get(topic_text)
    if english:
        return f'Give an example of {english}.' if example else f'Explain {english}.'
    return None


def validate_translation(source: str, translated: str, target: str,
                         allow_source_script: bool = False) -> None:
    """Reject visible corruption and lost explicit topic names, not prove fidelity."""
    if not translated.strip():
        raise ValueError('Translator returned an empty answer')
    if re.search(r'[\{\[]\s*\"(?:text|translation|translations|translated_text)\"\s*:', translated):
        raise ValueError('Translator leaked JSON into the answer')
    if len(translated) > max(180, len(source) * 3):
        raise ValueError('Translator added excessive text instead of translating')
    if re.search(r'(?:[א-ת]-){6,}[א-ת]', translated):
        raise ValueError('Translator produced garbled letter sequences')
    if re.search(r'(?:התרגומים אינם מדויקים|להלן התרגום|here is the translation|translations are not accurate)', translated, re.I):
        raise ValueError('Translator added commentary instead of a translation')
    plain = _PROTECTED_SPANS.sub('', translated)
    if target == 'he' and re.search(r'[A-Za-zא-ת]{3}', source) and not re.search(r'[א-ת]', plain):
        raise ValueError('Translator did not produce Hebrew prose')
    if target == 'en' and not allow_source_script and re.search(r'[א-ת]', plain):
        raise ValueError('Translator left Hebrew text in the English question')
    # Keep assignment/problem references exact before retrieval. Hebrew output
    # may legitimately spell out prose numbers (one -> אחד).
    if target == 'en' and sorted(re.findall(r'\d+(?:[.,]\d+)?', _PROTECTED_SPANS.sub('', source))) != sorted(re.findall(r'\d+(?:[.,]\d+)?', plain)):
        raise ValueError('Translator changed numbers in the text')
    topics = load_curriculum()['topics_by_id']
    confusable = [pair for pair in course_info()['confusable_topics'] if set(pair) <= set(topics)]

    def english_names(topic):
        return [alias for alias in (topic['name'], *topic['aliases']) if not re.search(r'[א-ת]', alias)]

    def contains(names, text):
        patterns = []
        for name in names:
            pattern = re.escape(name)
            if re.search(r'[א-ת]', name):
                pattern = '[ובכלמשה]{0,2}' + pattern.replace(r'\ ', r'\s+[ובכלמשה]{0,2}')
            patterns.append(r'(?<!\w)' + pattern + r'(?!\w)')
        return any(re.search(pattern, text, re.I) for pattern in patterns)

    for topic in topics.values():
        hebrew = [alias for alias in topic['aliases'] if re.search(r'[א-ת]', alias)]
        english = english_names(topic)
        expected = english if target == 'en' else [*hebrew, *english]
        original = hebrew if target == 'en' else english
        # An alias list is not a complete Hebrew dictionary. Enforce explicit
        # topic preservation on the English retrieval query, not exact wording
        # in a Hebrew answer. Still reject swapping configured confusable topics.
        if target == 'he':
            for pair in confusable:
                for other_id in pair:
                    if topic['id'] in pair and other_id != topic['id'] and contains(
                            english_names(topics[other_id]), source) and not contains(
                            english, source) and contains(expected, translated):
                        raise ValueError('Translator introduced a different course concept')
            continue
        if contains(original, source) and not contains(expected, translated):
            raise ValueError(f'Translator lost the requested course term: {topic["name"]}')


def translategemma_prompt(text: str, target: str) -> str:
    """Native single-user translation prompt documented by Ollama/Google."""
    source_name, source_code, target_name = (
        ('English', 'en', 'Hebrew') if target == 'he' else ('Hebrew', 'he', 'English'))
    return (
        f'You are a professional {source_name} ({source_code}) to {target_name} ({target}) translator. '
        f'Your goal is to accurately convey the meaning and nuances of the original {source_name} text '
        f'while adhering to {target_name} grammar, vocabulary, and cultural sensitivities.\n'
        f'Produce only the {target_name} translation, without any additional explanations or commentary. '
        f'Please translate the following {source_name} text into {target_name}:\n\n\n{text}')


def normalize_translation_terms(source: str, translated: str, target: str) -> str:
    """Normalize known literal translations only for explicit source concepts.

    Course-specific fixes come from the course "translation_fixes" setting:
    {"en": English term, "variants": [wrong Hebrew renderings], "he": preferred term}.
    """
    if target != 'he':
        return translated
    fixes = [*course_info()['translation_fixes'],
             {'en': 'check-in question', 'variants': ['שאלת רישום'], 'he': 'שאלת בדיקה'}]
    for fix in fixes:
        english = r'\s+'.join(r'(?:and|&)' if word.casefold() == 'and' else re.escape(word)
                              for word in fix['en'].split())
        if fix['variants'] and re.search(r'\b' + english + r'\b', source, re.I):
            variants = '|'.join(re.escape(variant) for variant in fix['variants'])
            translated = re.sub(r'(?<![א-ת])(?:' + variants + r')(?![א-ת])', fix['he'], translated)
    return translated


def translation_error_kind(error: Exception) -> str:
    """Distinguish output validation from unavailable models in the UI."""
    seen = set()
    while error.__cause__ is not None and id(error) not in seen:
        seen.add(id(error))
        error = error.__cause__
    message = str(error).casefold()
    name = type(error).__name__.casefold()
    if isinstance(error, TimeoutError) or 'timeout' in name or 'time limit' in message:
        return 'timeout'
    if getattr(error, 'status_code', None) == 404 or ('model' in message and 'not found' in message):
        return 'missing'
    if isinstance(error, ConnectionError) or 'connect' in name:
        return 'connection'
    if isinstance(error, (ValueError, TypeError)):
        return 'invalid'
    return 'unknown'


def translation_error_details(error: Exception) -> str:
    details = []
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        details.append(f'{type(error).__name__}: {error}')
        error = error.__cause__
    return '\n'.join(details)

"""Single course schedule shared by scope checks, prompts and homework mappings."""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from course_paths import CURRICULUM_FILE

# Course-level settings; every value can be overridden by the "course" block of curriculum.json.
COURSE_DEFAULTS = {
    'name': 'Course',
    'name_he': '',
    'subject': 'course',
    'unit_label': 'Week',
    'source_language': 'en',
    'glossary': {},
    'translation_fixes': [],
    'confusable_topics': [],
    'evidence_synonyms': {},
}


@lru_cache(maxsize=4)
def _read_curriculum(path: str, modified: int) -> dict:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    weeks = [w['week'] for w in data['weeks']]
    if len(set(weeks)) != len(weeks) or any(w < 1 for w in weeks):
        raise ValueError('Curriculum weeks must be unique positive integers')
    topics = {}
    for week in data['weeks']:
        for topic in week['topics']:
            if topic['id'] in topics:
                raise ValueError(f"Duplicate curriculum topic: {topic['id']}")
            topics[topic['id']] = {'aliases': [], 'prerequisites': [], **topic, 'week': week['week']}
    for topic in topics.values():
        for dep in topic['prerequisites']:
            if dep not in topics or topics[dep]['week'] > topic['week']:
                raise ValueError(f"Invalid prerequisite {dep} for {topic['id']}")
    data['topics_by_id'] = topics
    data['course'] = {**COURSE_DEFAULTS, **data.get('course', {})}
    return data


def load_curriculum() -> dict:
    return _read_curriculum(str(CURRICULUM_FILE), CURRICULUM_FILE.stat().st_mtime_ns)


def course_info() -> dict:
    return load_curriculum()['course']


def course_name(language: str = 'en') -> str:
    course = course_info()
    return (course['name_he'] or course['name']) if language == 'he' else course['name']


def glossary_hint(text: str = '', limit: int = 12) -> str:
    """Preferred English = Hebrew term pairs, favouring those that occur in the text."""
    glossary = course_info()['glossary']
    relevant = [(en, he) for en, he in glossary.items()
                if re.search(r'(?<!\w)' + re.escape(en) + r'(?!\w)', text, re.I) or he in text]
    chosen = relevant or list(glossary.items())
    return '; '.join(f'{en} = {he}' for en, he in chosen[:limit])


def covered_topics(week: int) -> list[str]:
    return [t['name'] for t in load_curriculum()['topics_by_id'].values() if t['week'] <= week]


def topic_names(ids: list[str]) -> list[str]:
    topics = load_curriculum()['topics_by_id']
    return [topics[topic_id]['name'] for topic_id in dict.fromkeys(ids)]


def tutorial_metadata() -> dict:
    return {f"tutorial_{w['week']}": {
        'display_name': w['title'], 'display_name_he': w.get('title_he') or w['title'],
        'source_pdf': w.get('source_pdf', ''), 'topics': covered_topics(w['week']),
    } for w in load_curriculum()['weeks']}


def normalized_text(text: str) -> str:
    text = unicodedata.normalize('NFKC', text).casefold().replace('&', ' and ')
    # Keep clause boundaries, while normalizing hyphens and apostrophes in names.
    return re.sub(r"[^\w.,;!?\n]+", ' ', text)


_EXCLUSION = re.compile(
    r"(?:without(?: using)?|do not (?:use|mention)|don t (?:use|mention)|"
    r"will not (?:use|mention)|won t (?:use|mention)|avoid(?: using| mentioning)?|instead of(?: using)?|rather than(?: using)?|"
    r"not using|בלי(?: להשתמש(?: ב)?)?|ללא(?: שימוש(?: ב)?)?|אל תשתמש(?:ו)? ב?)\s*(?:the\s+)?$"
)


def topic_mentions(text: str) -> list[dict]:
    """Recognize explicit names and narrow method exclusions, without rewriting text.

    Exclusions apply only to the named method. An affirmative later occurrence
    still counts. Negating a property ('Dijkstra does not work') is not exclusion.
    """
    normalized = normalized_text(text)
    mentions = []
    for topic in load_curriculum()['topics_by_id'].values():
        for name in (topic['name'], *topic['aliases']):
            prefix = r'[ובכלמשה]{0,2}' if re.search(r'[א-ת]', name) else ''
            pattern = r'(?<!\w)' + prefix + re.escape(normalized_text(name).strip()).replace(r'\ ', r'\s+') + r'(?!\w)'
            for match in re.finditer(pattern, normalized):
                before = normalized[:match.start()]
                exclusion = _EXCLUSION.search(before)
                excluded = bool(exclusion)
                if exclusion and re.search(r"(?:not|don t|do not|לא)\s*$", before[:exclusion.start()]):
                    excluded = False
                # "without Dijkstra's code, explain its idea" still asks about it.
                after = normalized[match.end():]
                if re.match(r'\s*(?:s\s+)?(?:code|implementation|pseudocode|proof)\b', after):
                    excluded = False
                if re.match(r'\s*[,;]?\s*(?:but\s+|and\s+)?(?:explain|describe|teach)\s+(?:it|its|how it)\b', after):
                    excluded = False
                mentions.append({**topic, 'start':match.start(), 'end':match.end(), 'excluded':excluded})
    # Aliases may match the same occurrence; prefer the longest name.
    unique = {}
    for m in sorted(mentions, key=lambda m: -(m['end'] - m['start'])):
        key = (m['id'], m['start'])
        unique.setdefault(key, m)
    ordered = sorted(unique.values(), key=lambda m: m['start'])
    for previous, current in zip(ordered, ordered[1:]):
        if previous['excluded'] and current['start'] >= previous['end']:
            bridge = normalized[previous['end']:current['start']]
            if re.fullmatch(r'\s*(?:,|and|or|או|ו)\s*', bridge):
                current['excluded'] = True
    return ordered


def named_future_topic(text: str, week: int) -> int:
    return max((m['week'] for m in topic_mentions(text)
                if m['week'] > week and not m['excluded']), default=0)


def scope_comparison_text(text: str) -> str:
    """Omit explicitly excluded names ONLY from the internal similarity comparison.

    The actual retrieval query, displayed question and LLM user message stay intact.
    This stops 'without Dijkstra' from making that name dominate the scope score.
    """
    normalized = normalized_text(text)
    chars = list(normalized)
    for mention in topic_mentions(text):
        if mention['excluded']:
            chars[mention['start']:mention['end']] = ' ' * (mention['end'] - mention['start'])
    return ''.join(chars)


def clarification_needed(question: str) -> bool:
    """Ask about bare references instead of guessing or rewriting the user's intent."""
    q = normalized_text(question).strip(' .!?\n')
    return bool(re.fullmatch(
        r'(?:why|how|why does (?:it|that|this) work|how does (?:it|that|this) work|'
        r'explain (?:it|that|this)|give me (?:an example|another example)|'
        r'למה|מדוע|איך זה עובד|למה זה עובד|תסביר את זה|אפשר דוגמה)', q
    ))

"""Read assignment statements from the PDFs mapped in db/homework.json."""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from curriculum import topic_names, topic_mentions
from course_paths import COURSE_ROOT as ROOT, HOMEWORK_DIR

# Numbered problem headings, tried in order: English, Hebrew, then Hebrew extracted in
# visual order ("2 שאלה"); finally English headings followed by text on the same line.
PROBLEM_HEADINGS = (
    re.compile(r'^\s*(?:Problem|Question|Exercise|Task)\s*(?:No\.?\s*)?(\d+)\s*[:.)]?\s*$', re.I | re.M),
    re.compile(r'^\s*(?:שאלה|תרגיל|בעיה)\s*(?:מס\S*\s*)?(\d+)\s*[:.)]?\s*$', re.M),
    re.compile(r'^\s*[:.)]?\s*(\d+)\s*(?:שאלה|תרגיל|בעיה)\s*$', re.M),
    re.compile(r'^\s*(?:Problem|Question|Exercise|Task)\s+(\d+)\s*[:.)]\s*(?=\S)', re.I | re.M),
)
PROBLEM_HEADING = PROBLEM_HEADINGS[0]


def homework_pdf_path(entry: dict) -> Path:
    """Resolve a portable PDF reference inside the course's Homework folder."""
    path = (ROOT / entry['problem_pdf']).resolve()
    if not path.is_relative_to(HOMEWORK_DIR.resolve()) or path.suffix.lower() != '.pdf':
        raise ValueError('Homework PDFs must be inside material/Homework')
    return path


def extract_problem_statements(path: Path) -> list[dict]:
    """Keep every problem and its page references; never guess a solution split."""
    from pypdf import PdfReader

    pages = []
    for page_number, page in enumerate(PdfReader(path).pages, 1):
        text = page.extract_text() or ''
        # Remove only the PDF page footer, preserving numbers inside mathematics.
        pages.append(re.sub(r'\n\s*' + str(page_number) + r'\s*$', '', text))
    errors = []
    for heading in PROBLEM_HEADINGS:
        try:
            return _split_problems(pages, heading, path.name)
        except ValueError as error:
            errors.append(str(error))
    raise ValueError(errors[0])


def _split_problems(pages: list[str], heading: re.Pattern, name: str) -> list[dict]:
    statements: list[dict] = []
    current = None
    for page_number, text in enumerate(pages, 1):
        matches = list(heading.finditer(text))
        if current is not None:
            continuation = text[:matches[0].start()] if matches else text
            if continuation.strip():
                current['text'] += '\n\n' + continuation.strip()
                current['pages'].append(page_number)
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            current = {
                'number': int(match.group(1)),
                'pages': [page_number],
                'text': text[match.end():end].strip(),
            }
            statements.append(current)
    if not statements or any(not p['text'] for p in statements):
        raise ValueError(f'Could not extract complete problem statements from {name}')
    numbers = [p['number'] for p in statements]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ValueError(f'Unexpected problem numbering in {name}: {numbers}')
    return statements


@lru_cache(maxsize=16)
def _pdf_content(path: str, modified_ns: int, size: int,
                 stored_sha256: str = '', stored_json: str = '') -> dict:
    pdf = Path(path)
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    try:
        statements = extract_problem_statements(pdf)
    except ValueError:
        # The course builder may have segmented this PDF with an LLM; trust it only for
        # the exact PDF it was produced from.
        if not stored_json or stored_sha256 != digest:
            raise
        statements = json.loads(stored_json)
    full_text = '\n\n'.join(f"Problem {p['number']}\n{p['text']}" for p in statements)
    return {
        'problems': len(statements),
        'problem_statements': statements,
        'full_problem_text': full_text,
        'problem_preview': full_text[:500],
        'pdf_sha256': digest,
    }


def with_pdf_content(entry: dict) -> dict:
    """JSON controls the week/title; the mapped PDF supplies the actual questions."""
    path = homework_pdf_path(entry)
    stat = path.stat()
    stored = entry.get('problem_statements') if entry.get('statements_source') == 'llm' else None
    content = _pdf_content(str(path), stat.st_mtime_ns, stat.st_size,
                           entry.get('pdf_sha256', '') if stored else '',
                           json.dumps(stored, ensure_ascii=False) if stored else '')
    result = {**entry, **content}
    ids = [topic for topics in result.get('problem_topics', {}).values() for topic in topics]
    result['topics'] = topic_names(ids)
    result['key_concepts'] = result['topics']
    return result


def problem_numbers(question: str) -> set[int]:
    numbers = set()
    for match in re.finditer(
        r'(?:problems?|questions?|שאלה|תרגיל|שאלות|תרגילים)\s*[:#]?\s*(\d+)'
        r'((?:\s*(?:,|and|&|או|ו)\s*\d+)*)', question, re.IGNORECASE
    ):
        numbers.add(int(match.group(1)))
        numbers.update(map(int, re.findall(r'\d+', match.group(2))))
    ordinals = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
                'sixth': 6, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
                'הראשונה': 1, 'השנייה': 2, 'השניה': 2, 'השלישית': 3,
                'הרביעית': 4, 'החמישית': 5, 'השישית': 6}
    for word, number in ordinals.items():
        if re.search(r'\b' + word + r'\s+(?:problem|question)\b|'
                     r'(?:problem|question|שאלה|השאלה)\s+' + word + r'\b', question, re.I):
            numbers.add(number)
    if re.fullmatch(r'\s*#?\d+[.!]?\s*', question):
        numbers.add(int(re.search(r'\d+', question).group()))
    return numbers


def homework_overview(question: str) -> bool:
    """An assignment-wide request needs the actual statements, not lecture hits."""
    if problem_numbers(question) or any(not m['excluded'] for m in topic_mentions(question)):
        return False
    return bool(re.search(r'\b(?:homework|assignment)\b|מטלה|שיעורי בית|'
                          r'\b(?:all|list|summarize) (?:the )?(?:questions|problems)\b|'
                          r'כל השאלות', question, re.I))


def homework_content_request(question: str) -> bool:
    """Requests to read the assignment can be answered directly from its PDF."""
    return homework_overview(question) or bool(problem_numbers(question) and re.search(
        r'\bwhat\b.*\b(?:asks?|says?|statement|about)\b|'
        r'\b(?:show|read|repeat|quote)\b.*\b(?:problem|question)\b|'
        r'מה.*(?:כתוב|מבקש|נדרש)|הצג.*שאלה', question, re.I))


def resolve_homework_followup(question: str, active_numbers: list[int]) -> str:
    """Carry only an explicitly selected problem into a referential follow-up."""
    if not active_numbers or problem_numbers(question) or homework_overview(question):
        return question
    if any(not m['excluded'] for m in topic_mentions(question)):
        return question
    if re.search(r'\b(?:it|this|that|next|continue|hint|stuck|start|help|guide|solve|my|why)\b|'
                 r'רמז|המשך|להמשיך|זה|עזרה|לעזור|לפתור|למה|נתקע', question, re.I):
        return question + '\n\nSelected homework problem: ' + ', '.join(map(str, active_numbers))
    return question


def selected_statements(hw: dict, question: str) -> list[dict]:
    numbers = problem_numbers(question)
    if hw.get('source_error'):
        return []
    return [p for p in hw.get('problem_statements', [])
            if p['number'] in numbers or (not numbers and homework_overview(question))]


def homework_clarification(hw: dict, question: str) -> str | None:
    numbers = problem_numbers(question)
    available = {p['number'] for p in hw.get('problem_statements', [])}
    if numbers - available:
        return 'unknown_problem'
    if homework_overview(question):
        return None
    if not numbers and any(not m['excluded'] for m in topic_mentions(question)):
        return None
    if not numbers and (re.search(r'(?:\bproblem\b|\bquestion\b|שאלה|תרגיל)', question, re.I)
                        or re.fullmatch(r'(?:give me (?:a |a small )?hint[.!]?|where should i start[?]?|'
                                        r'תן לי רמז קטן[.]?|מאיפה כדאי להתחיל[?]?|(?:please )?(?:help|guide)(?: me)?[.!]?|'
                                        r'(?:can you )?check my (?:reasoning|work|answer|solution|proof)(?: so far)?[?.!]?|'
                                        r'אפשר לבדוק את דרך החשיבה שלי[?]?|'
                                        r'(?:i am |i.m )?stuck[.!]?|(?:help me )?solve (?:it|this)[.!]?|עזרה|תעזור לי|תנחה אותי)', question, re.I)):
        return 'choose_problem'
    return None


def problem_topic_names(hw: dict, question: str) -> list[str]:
    numbers = problem_numbers(question)
    ids = [topic for number in sorted(numbers)
           for topic in hw.get('problem_topics', {}).get(str(number), [])]
    return topic_names(ids)


def homework_context(hw: dict, question: str = '') -> str:
    """Supply the explicitly requested problems, with PDF page and citation IDs."""
    name = Path(hw.get('problem_pdf', '')).name
    return '\n\n'.join(
        f"[Assignment {i} — {name}, Problem {p['number']}, PDF pages "
        f"{', '.join(map(str, p['pages']))}]\n{p['text']}"
        for i, p in enumerate(selected_statements(hw, question), 1)
    )


def homework_retrieval_query(hw: dict, question: str) -> str:
    """Keep the original question first; attach context only for explicit problems.

    No LLM rewrite, history inference or assignment-wide keyword injection.
    The generation model receives the original question separately and unchanged.
    """
    if not problem_numbers(question):
        return question
    topics = ', '.join(problem_topic_names(hw, question))
    return (question + f'\n\nSelected problem concepts: {topics}\n'
            + homework_context(hw, question))


def homework_overview_answer(hw: dict, question: str = "What is in the homework?") -> str:
    """Show real problem numbers and text without asking a model to reconstruct them."""
    statements = selected_statements(hw, question)
    if not statements:
        raise ValueError('Assignment statements are unavailable')
    parts = [f"Here are the requested statements from {hw.get('title', 'the homework')} "
             "as extracted from the assignment PDF:"]
    parts.extend(f"**Problem {p['number']}** (Assignment {i})\n\n{p['text']}"
                 for i, p in enumerate(statements, 1))
    parts.append('Which problem would you like to work through? Tell me what you have tried, '
                 'or choose a problem and we can start together. '
                 'If an extracted formula looks unclear, check it against the downloadable PDF.')
    return '\n\n'.join(parts)

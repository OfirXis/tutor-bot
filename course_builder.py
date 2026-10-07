"""Build a course knowledge base from its PDFs with an LLM — for any course.

Stages (each writes a reviewable file to material/curriculum_review/; existing files
are reused unless forced, so any stage can be hand-corrected and the build re-run):

  extract     lecture PDF text, page by page          -> tutorial_N.source.txt
  notes       LLM: faithful English notes per lecture -> tutorial_N.txt
  topics      LLM: topics taught in each lecture      -> tutorial_N.topics.json
  curriculum  deterministic assembly + glossary       -> curriculum.json
  homework    split problems, LLM maps them to topics -> homework.json
  install     copy into material/english + db/, rebuild the retrieval index
  check       every topic answerable in its week and refused the week before

Lecture order comes from the first number in each lecture file name, or from a
"lectures" list in material/course.json. Course name, subject, glossary and other
settings are read from material/course.json; everything else is derived from the PDFs.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path

NOTE_GROUPS = ("Core Concepts", "Methods and Procedures", "Worked Examples", "Theorems and Proofs")
TOPIC_KINDS = ("concept", "method", "problem", "theorem")
BATCH_CHARS = 6000
GENERIC_ALIASES = {"algorithm", "algorithms", "problem", "problems", "method", "theorem",
                   "definition", "example", "proof", "lemma", "technique"}
_LEADING_WORDS = {"the", "a", "an", "of", "is", "are", "called", "and", "or", "in", "on", "to",
                  "for", "with", "by", "its", "their", "this", "that", "these", "as", "from",
                  "into", "at", "be", "we", "it", "named", "term", "known"}
_GLOSSARY_PAIR = re.compile(
    r"((?:[A-Za-z][\w'-]*\s+){0,3}[A-Za-z][\w'-]*)\s*\(([^()]*[\u0590-\u05FF][^()]*)\)")


# ─────────────────────────────────────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────────────────────────────────────

def _json_from_reply(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in the reply")
    return json.loads(text[start:end + 1])


def ask_json(llm, system: str, user: str, schema: dict) -> dict:
    """Structured call. Ollama enforces the schema itself; other models get it in the prompt."""
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    kwargs = {"format": schema} if type(llm).__name__ == "ChatOllama" else {}
    messages = [SystemMessage(system + "\n\nReply with one JSON object matching this JSON schema:\n"
                              + json.dumps(schema)), HumanMessage(user)]
    for _ in range(2):
        reply = llm.invoke(messages, **kwargs).content
        try:
            return _json_from_reply(reply)
        except ValueError as error:
            messages += [AIMessage(reply), HumanMessage(
                f"That was not valid JSON ({error}). Reply with the JSON object only.")]
    raise ValueError("The model did not return valid JSON")


# ─────────────────────────────────────────────────────────────────────────────
# PDF text
# ─────────────────────────────────────────────────────────────────────────────

def extract_pages(pdf: Path) -> list[str]:
    from pypdf import PdfReader
    return [page.extract_text() or "" for page in PdfReader(pdf).pages]


def pages_to_source(pages: list[str]) -> str:
    return "\n\n".join(f"[PDF page {i}]\n{text.strip() or '[No extractable text]'}"
                       for i, text in enumerate(pages, 1))


def source_to_pages(source: str) -> list[str]:
    parts = re.split(r"^\[PDF page (\d+)\]\n?", source, flags=re.M)
    pages = {int(number): text.strip() for number, text in zip(parts[1::2], parts[2::2])}
    return [pages.get(i, "") for i in range(1, max(pages, default=0) + 1)]


def page_batches(pages: list[str], limit: int = BATCH_CHARS):
    """Yield (first_page, last_page, text) groups of whole pages, bounded in size."""
    batch, first, last, size = [], 0, 0, 0
    for number, text in enumerate(pages, 1):
        text = text.strip()
        if not text or text == "[No extractable text]":
            continue
        block = f"[PDF page {number}]\n{text[:limit]}"
        if batch and size + len(block) > limit:
            yield first, last, "\n\n".join(batch)
            batch, size = [], 0
        if not batch:
            first = number
        batch.append(block)
        size += len(block)
        last = number
    if batch:
        yield first, last, "\n\n".join(batch)


def first_number(name: str) -> int | None:
    match = re.search(r"\d+", name)
    return int(match.group()) if match else None


def slug(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.casefold()).strip("_")


_JSON_ESCAPE_DAMAGE = {"\t": "\\t", "\x0c": "\\f", "\x08": "\\b", "\r": "\\r"}


def repair_latex(text: str) -> str:
    """Undo JSON escapes that swallowed LaTeX backslashes (\\text arrives as TAB + 'ext')."""
    return re.sub(r"[\t\x0c\x08\r](?=[A-Za-z])", lambda m: _JSON_ESCAPE_DAMAGE[m.group()], text)


# ─────────────────────────────────────────────────────────────────────────────
# Notes
# ─────────────────────────────────────────────────────────────────────────────

NOTES_SCHEMA = {
    "type": "object",
    "properties": {
        "lecture_title": {"type": "string"},
        "notes": {"type": "array", "items": {"type": "object", "properties": {
            "group": {"type": "string", "enum": list(NOTE_GROUPS)},
            "title": {"type": "string"},
            "first_page": {"type": "integer"},
            "last_page": {"type": "integer"},
            "body": {"type": "string"},
        }, "required": ["group", "title", "first_page", "last_page", "body"]}},
    },
    "required": ["lecture_title", "notes"],
}


def notes_instructions(course: dict) -> str:
    return (
        f"You write faithful English study notes from the lecture slides of the course "
        f"\"{course['name']}\" ({course['subject']}). The slide text may be in another language "
        "and may be garbled by PDF extraction; translate it into clear English. Use ONLY "
        "information that appears in the slides: no outside knowledge and no invented examples, "
        "numbers or steps. Write one note per distinct idea (definition, method, worked example, "
        f"theorem or proof). Each note has a group (one of: {', '.join(NOTE_GROUPS)}), a short "
        "specific title, the first and last PDF page it is based on (from the [PDF page N] "
        "markers) and a body of 2-6 complete sentences. Put examples under Worked Examples. "
        "Write mathematics in LaTeX between $ signs. The first time a key term appears, add the "
        "slides' original term in parentheses when it is not English. If a formula or diagram "
        "cannot be read, say so instead of guessing. lecture_title is the lecture's English title."
    )


def clean_note(note: dict, first: int, last: int) -> dict | None:
    title = repair_latex(" ".join(str(note.get("title", "")).split()))
    title = re.sub(r"\s*[—–-]\s*PDF pages?\b.*$", "", title)[:120].strip(" .:")
    body = repair_latex(re.sub(r"^#+\s*", "", str(note.get("body", "")).strip(), flags=re.M))
    if not title or len(body) < 40:
        return None
    try:
        start, end = int(note["first_page"]), int(note["last_page"])
    except (KeyError, TypeError, ValueError):
        start, end = first, last
    start = min(max(start, first), last)
    end = min(max(end, start), last)
    group = note.get("group") if note.get("group") in NOTE_GROUPS else NOTE_GROUPS[0]
    return {"group": group, "title": title, "first_page": start, "last_page": end, "body": body}


def render_notes(week: int, title: str, unit_label: str, pdf_name: str, page_count: int,
                 notes: list[dict], model_label: str) -> str:
    lines = [f"# {unit_label} {week} — {title}", "", "## Source and Scope",
             f"These English notes were generated automatically by {model_label} from "
             f"`{pdf_name}` (PDF pages 1–{page_count}). Page references point to that PDF; "
             "check formulas and diagrams there.", ""]
    for group in NOTE_GROUPS:
        items = sorted((n for n in notes if n["group"] == group),
                       key=lambda n: (n["first_page"], n["title"]))
        if items:
            lines.append(f"## {group}")
        for n in items:
            pages = (f"PDF page {n['first_page']}" if n["first_page"] == n["last_page"]
                     else f"PDF pages {n['first_page']}–{n['last_page']}")
            lines += [f"### {n['title']} — {pages}", n["body"], ""]
    return "\n".join(lines).rstrip() + "\n"


def generate_notes(week: int, pages: list[str], llm, course: dict, pdf_name: str,
                   model_label: str = "an LLM") -> tuple[str, str]:
    """Return (English lecture title, markdown notes) built from every page batch."""
    notes, seen, titles = [], set(), []
    for first, last, text in page_batches(pages):
        result = ask_json(llm, notes_instructions(course),
                          f"Lecture {week}, PDF pages {first}-{last}:\n\n{text}", NOTES_SCHEMA)
        if str(result.get("lecture_title", "")).strip():
            titles.append(" ".join(str(result["lecture_title"]).split()))
        for raw in result.get("notes", []):
            note = clean_note(raw if isinstance(raw, dict) else {}, first, last)
            key = note and (note["title"].casefold(), note["first_page"])
            if note and key not in seen:
                seen.add(key)
                notes.append(note)
    if not notes:
        raise ValueError(f"No usable notes were generated for lecture {week}")
    title = titles[0] if titles else f"Lecture {week}"
    return title, render_notes(week, title, course["unit_label"], pdf_name, len(pages), notes,
                               model_label)


# ─────────────────────────────────────────────────────────────────────────────
# Topics and curriculum
# ─────────────────────────────────────────────────────────────────────────────

TOPICS_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "title_native": {"type": "string"},
        "topics": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"},
            "aliases": {"type": "array", "items": {"type": "string"}},
            "kind": {"type": "string", "enum": list(TOPIC_KINDS)},
        }, "required": ["name", "aliases", "kind"]}},
    },
    "required": ["topics"],
}

TOPICS_INSTRUCTIONS = (
    "From the study notes of ONE lecture, list the topics it TEACHES: the concepts, methods, "
    "problems and theorems a student would ask about (3 to 15). Use short canonical English "
    "names (\"Merge sort\", not \"The merge sort algorithm for arrays\"). aliases: other names "
    "the notes use for the same topic - English synonyms, an abbreviation if used (e.g. BFS) "
    "and the original-language term shown in parentheses. Skip topics only mentioned in passing "
    "and topics an earlier lecture introduced. title: a short English lecture title naming its "
    "main topics. title_native: the lecture title in the slides' "
    "original language if the notes show it, otherwise an empty string."
)


def clean_topics(raw: dict, week: int, notes: str, earlier: dict[str, str]) -> list[dict]:
    """Ground, deduplicate and normalize LLM topics. `earlier` maps known names to ids."""
    haystack = notes.casefold()
    topics, seen = [], set(earlier.values())
    for item in raw.get("topics", [])[:20]:
        if not isinstance(item, dict):
            continue
        name = " ".join(str(item.get("name", "")).split()).strip(" .")
        if not name or len(name) > 80:
            continue
        name = name[0].upper() + name[1:]
        aliases = []
        for alias in item.get("aliases", []):
            alias = " ".join(str(alias).split()).strip(" .")
            if (2 <= len(alias) <= 60 and alias.casefold() != name.casefold()
                    and alias.casefold() not in GENERIC_ALIASES
                    and alias.casefold() not in earlier and alias not in aliases):
                aliases.append(alias)
        # Grounding: the notes must actually use the name or an alias.
        if not any(term.casefold() in haystack for term in (name, *aliases)):
            continue
        topic_id = slug(name) or f"week{week}_topic{len(topics) + 1}"
        if topic_id in seen or name.casefold() in earlier:
            continue
        seen.add(topic_id)
        kind = item.get("kind") if item.get("kind") in TOPIC_KINDS else "concept"
        topics.append({"id": topic_id, "name": name, "aliases": aliases[:10], "kind": kind})
    return topics


def harvest_glossary(notes_texts: list[str], weeks: list[dict]) -> dict[str, str]:
    """English -> Hebrew term pairs from topic aliases and 'term (מונח)' patterns in the notes."""
    glossary = {}
    for week in weeks:
        for topic in week["topics"]:
            hebrew = [a for a in topic.get("aliases", []) if re.search(r"[\u0590-\u05FF]", a)]
            if hebrew:
                glossary[topic["name"].casefold()] = hebrew[0]
    for text in notes_texts:
        for match in _GLOSSARY_PAIR.finditer(text):
            words = match.group(1).split()
            while words and words[0].casefold() in _LEADING_WORDS:
                words.pop(0)
            hebrew = match.group(2).split(";")[0].split(",")[0].strip()
            if words and len(hebrew) <= 40 and re.search(r"[\u0590-\u05FF]", hebrew):
                glossary.setdefault(" ".join(words).casefold(), hebrew)
    return glossary


def assemble_curriculum(course: dict, weeks: list[dict], glossary: dict[str, str]) -> dict:
    from curriculum import COURSE_DEFAULTS, validate_curriculum

    settings = {key: value for key, value in course.items()
                if key not in ("abbreviations", "lectures", "homework_weeks")}
    settings["glossary"] = {**glossary, **course.get("glossary", {})}
    abbreviations = course.get("abbreviations", {})
    data = {"version": 1, "course": {**COURSE_DEFAULTS, **settings}, "weeks": []}
    introduced: dict[str, dict] = {}
    for week in sorted(weeks, key=lambda w: w["week"]):
        topics = []
        for topic in week["topics"]:
            if topic["id"] in introduced:
                # A topic belongs to the week that introduces it; later mentions add aliases only.
                earlier = introduced[topic["id"]]
                earlier["aliases"] += [a for a in topic.get("aliases", []) if a not in earlier["aliases"]]
                continue
            entry = {"id": topic["id"], "name": topic["name"], "aliases": list(topic.get("aliases", [])),
                     "prerequisites": topic.get("prerequisites", [])}
            if topic["id"] in abbreviations:
                entry["abbreviations"] = abbreviations[topic["id"]]
            introduced[topic["id"]] = entry
            topics.append(entry)
        data["weeks"].append({"week": week["week"], "title": week["title"],
                              "title_he": week.get("title_he") or week["title"],
                              "source_pdf": week["source_pdf"], "topics": topics})
    validate_curriculum(data)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Homework
# ─────────────────────────────────────────────────────────────────────────────

def topic_week_table(curriculum: dict) -> dict[str, dict]:
    return {t["id"]: {**t, "week": w["week"]} for w in curriculum["weeks"] for t in w["topics"]}


def mentioned_topics(text: str, topics: dict[str, dict]) -> list[str]:
    lowered = text.casefold()
    return [tid for tid, topic in topics.items()
            if any(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", lowered)
                   for term in (topic["name"], *topic.get("aliases", [])) if len(term) > 2)]


def map_problem(text: str, number: int, topics: dict[str, dict], llm) -> list[str]:
    ids = sorted(topics, key=lambda tid: topics[tid]["week"])
    schema = {"type": "object", "properties": {"topic_ids": {
        "type": "array", "items": {"type": "string", "enum": ids}}}, "required": ["topic_ids"]}
    listing = "\n".join(f"{tid}: {topics[tid]['name']} (week {topics[tid]['week']})" for tid in ids)
    chosen = []
    if llm is not None:
        try:
            result = ask_json(
                llm, "You map a homework problem to the course topics a student needs to solve it. "
                     "Choose 1-4 topic ids from the list - the most specific ones the problem relies on.",
                f"COURSE TOPICS:\n{listing}\n\nPROBLEM {number}:\n{text[:3500]}", schema)
            chosen = [tid for tid in result.get("topic_ids", []) if tid in topics]
        except (ValueError, KeyError):
            chosen = []
    return list(dict.fromkeys(chosen or mentioned_topics(text, topics)))[:4]


def build_homework_entry(key: str, pdf_rel: str, statements: list[dict], mapping: dict,
                         topics: dict[str, dict], previous: dict, week_override: int | None,
                         digest: str, llm_segmented: bool) -> dict:
    weeks = [topics[tid]["week"] for ids in mapping.values() for tid in ids]
    names = [topics[tid]["name"] for ids in mapping.values() for tid in ids]
    entry = {
        "title": previous.get("title") or f"Homework {key.split('_')[-1]}",
        "problem_pdf": pdf_rel,
        "week": week_override or max(weeks, default=1),
        "week_basis": ("set in material/course.json" if week_override else
                       "automatic: the latest week among the topics its problems need"),
        "description": previous.get("description") or (
            "Problems on " + ", ".join(dict.fromkeys(names))[:300] if names else ""),
        "problem_topics": {str(number): ids for number, ids in mapping.items()},
        "pdf_sha256": digest,
    }
    if llm_segmented:
        entry["statements_source"] = "llm"
        entry["problem_statements"] = statements
    return entry


SEGMENT_SCHEMA = {"type": "object", "properties": {"problems": {"type": "array", "items": {
    "type": "object", "properties": {"number": {"type": "integer"}, "page": {"type": "integer"},
                                     "first_words": {"type": "string"}},
    "required": ["number", "page", "first_words"]}}}, "required": ["problems"]}


def segment_with_llm(pages: list[str], llm) -> list[dict]:
    """Ask only for where each problem starts, then cut the real PDF text there."""
    result = ask_json(llm, "Find where each numbered homework problem starts. For each problem "
                           "give its number, the PDF page it starts on and its first 5-8 words "
                           "copied exactly.", pages_to_source(pages)[:12000], SEGMENT_SCHEMA)
    flat = [re.sub(r"\s+", " ", page) for page in pages]
    starts = []
    for item in sorted(result.get("problems", []), key=lambda p: p.get("number", 0)):
        page = int(item.get("page", 0))
        anchor = " ".join(str(item.get("first_words", "")).split()[:5])
        position = flat[page - 1].find(anchor) if 1 <= page <= len(flat) and anchor else -1
        if position < 0:
            raise ValueError("Problem start not found in the PDF text")
        starts.append((int(item["number"]), page, position))
    if [s[0] for s in starts] != list(range(1, len(starts) + 1)):
        raise ValueError("Problems are not numbered 1..n")
    statements = []
    for i, (number, page, position) in enumerate(starts):
        end_page, end_pos = starts[i + 1][1:] if i + 1 < len(starts) else (len(flat), None)
        text = flat[page - 1][position:end_pos if end_page == page else None]
        for later in range(page + 1, end_page + 1):
            text += "\n\n" + (flat[later - 1][:end_pos] if later == end_page and end_pos is not None
                              else flat[later - 1])
        statements.append({"number": number, "pages": list(range(page, end_page + 1)),
                           "text": text.strip()})
    return statements


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

class CourseBuilder:
    def __init__(self, root: Path | None = None, llm=None, model_label: str = "an LLM", log=print):
        import course_paths
        self.root = Path(root or course_paths.COURSE_ROOT).resolve()
        material = self.root / "material"
        self.lectures_dir = material / "lectures"
        self.homework_dir = material / "Homework"
        self.review_dir = material / "curriculum_review"
        self.notes_dir = material / "english"
        self.course_file = material / "course.json"
        self.db_dir = self.root / "db"
        self.llm, self.model_label, self.log = llm, model_label, log

    # -- inputs ------------------------------------------------------------
    def course(self) -> dict:
        from curriculum import COURSE_DEFAULTS
        settings = (json.loads(self.course_file.read_text(encoding="utf-8"))
                    if self.course_file.exists() else {})
        return {**COURSE_DEFAULTS, "unit_label_he": "", **settings}

    def lectures(self) -> list[tuple[int, Path]]:
        explicit = self.course().get("lectures")
        if explicit:
            return [(i, self.lectures_dir / name) for i, name in enumerate(explicit, 1)]
        numbered = []
        for pdf in sorted(self.lectures_dir.glob("*.pdf")):
            number = first_number(pdf.stem)
            if number is None:
                raise ValueError(f"{pdf.name} has no number in its name; list the lecture "
                                 "order under \"lectures\" in material/course.json")
            numbered.append((number, pdf))
        weeks = [week for week, _ in numbered]
        if len(set(weeks)) != len(weeks):
            raise ValueError("Two lecture PDFs share a number; list the order in material/course.json")
        return sorted(numbered)

    def _rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def _write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _needs_llm(self) -> None:
        if self.llm is None:
            raise RuntimeError("This stage needs an LLM; configure LLM_PROVIDER/OLLAMA_LLM_MODEL")

    # -- stages ------------------------------------------------------------
    def extract(self, weeks=None, force=False) -> None:
        for week, pdf in self.lectures():
            out = self.review_dir / f"tutorial_{week}.source.txt"
            if (weeks and week not in weeks) or (out.exists() and not force):
                continue
            pages = extract_pages(pdf)
            self._write(out, pages_to_source(pages))
            self.log(f"extract  week {week}: {len(pages)} pages from {pdf.name}")

    def notes(self, weeks=None, force=False) -> None:
        course = self.course()
        for week, pdf in self.lectures():
            out = self.review_dir / f"tutorial_{week}.txt"
            if (weeks and week not in weeks) or (out.exists() and not force):
                continue
            self._needs_llm()
            pages = source_to_pages(
                (self.review_dir / f"tutorial_{week}.source.txt").read_text(encoding="utf-8"))
            title, markdown = generate_notes(week, pages, self.llm, course, self._rel(pdf),
                                             self.model_label)
            self._write(out, markdown)
            self.log(f"notes    week {week}: {title} ({markdown.count('### ')} sections)")

    def topics(self, weeks=None, force=False) -> None:
        course = self.course()
        earlier: dict[str, str] = {}
        for week, pdf in self.lectures():
            out = self.review_dir / f"tutorial_{week}.topics.json"
            selected = not weeks or week in weeks
            if out.exists() and not (force and selected):
                data = json.loads(out.read_text(encoding="utf-8"))
            elif not selected:
                continue
            else:
                self._needs_llm()
                notes = (self.review_dir / f"tutorial_{week}.txt").read_text(encoding="utf-8")
                title = re.sub(r"^#\s*(?:\S+\s+\d+\s*[—–-]\s*)?", "", notes.splitlines()[0]).strip()
                known = ", ".join(sorted(earlier)) or "none"
                raw = ask_json(self.llm, TOPICS_INSTRUCTIONS,
                               f"Lecture {week}: {title}\nTopics introduced earlier: {known}\n\n"
                               f"NOTES:\n{notes[:9000]}", TOPICS_SCHEMA)
                native = " ".join(str(raw.get("title_native", "")).split())
                suggested = " ".join(str(raw.get("title", "")).split()).strip(" .")
                generic = {course["name"].casefold(), course["subject"].casefold(), "lecture",
                           "tutorial", "slides", "course"}
                if suggested and (len(title.split()) < 2 or title.casefold() in generic):
                    # The first slide often carries only the course name; name the lecture by its content.
                    title = suggested
                    notes_file = self.review_dir / f"tutorial_{week}.txt"
                    lines = notes.splitlines()
                    lines[0] = f"# {course['unit_label']} {week} — {title}"
                    self._write(notes_file, "\n".join(lines) + "\n")
                data = {
                    "week": week,
                    "title": f"{course['unit_label']} {week} — {title}",
                    "title_he": (f"{course['unit_label_he'] or course['unit_label']} {week} — {native}"
                                 if native else ""),
                    "source_pdf": self._rel(pdf),
                    "topics": clean_topics(raw, week, notes, earlier),
                }
                self._write(out, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
                self.log(f"topics   week {week}: {', '.join(t['name'] for t in data['topics'])}")
            for topic in data["topics"]:
                for term in (topic["name"], *topic.get("aliases", [])):
                    earlier.setdefault(term.casefold(), topic["id"])

    def curriculum(self) -> dict:
        weeks, notes = [], []
        for week, _ in self.lectures():
            weeks.append(json.loads((self.review_dir / f"tutorial_{week}.topics.json")
                                    .read_text(encoding="utf-8")))
            notes.append((self.review_dir / f"tutorial_{week}.txt").read_text(encoding="utf-8"))
        data = assemble_curriculum(self.course(), weeks, harvest_glossary(notes, weeks))
        self._write(self.review_dir / "curriculum.json",
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        self.log(f"curriculum: {len(data['weeks'])} weeks, "
                 f"{sum(len(w['topics']) for w in data['weeks'])} topics, "
                 f"{len(data['course']['glossary'])} glossary terms")
        return data

    def homework(self, force=False) -> dict:
        from homework_material import extract_problem_statements

        out = self.review_dir / "homework.json"
        if out.exists() and not force:
            return json.loads(out.read_text(encoding="utf-8"))
        curriculum = json.loads((self.review_dir / "curriculum.json").read_text(encoding="utf-8"))
        topics = topic_week_table(curriculum)
        previous = {}
        if (self.db_dir / "homework.json").exists():
            previous = json.loads((self.db_dir / "homework.json").read_text(encoding="utf-8"))
        overrides = self.course().get("homework_weeks", {})
        result = {}
        for pdf in sorted(self.homework_dir.glob("*.pdf")) if self.homework_dir.exists() else []:
            number = first_number(pdf.stem)
            if number is None:
                continue
            key = f"hw_{number}"
            llm_segmented = False
            try:
                statements = extract_problem_statements(pdf)
            except ValueError:
                self._needs_llm()
                statements = segment_with_llm(extract_pages(pdf), self.llm)
                llm_segmented = True
            mapping = {p["number"]: map_problem(p["text"], p["number"], topics, self.llm)
                       for p in statements}
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            result[key] = build_homework_entry(key, self._rel(pdf), statements, mapping, topics,
                                               previous.get(key, {}), overrides.get(key), digest,
                                               llm_segmented)
            self.log(f"homework {key}: {len(statements)} problems, week {result[key]['week']}")
        self._write(out, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result

    def install(self) -> None:
        from curriculum import validate_curriculum

        curriculum = json.loads((self.review_dir / "curriculum.json").read_text(encoding="utf-8"))
        validate_curriculum(curriculum)
        weeks = {w["week"] for w in curriculum["weeks"]}
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        for old in self.notes_dir.glob("tutorial_*.txt"):
            if first_number(old.stem) not in weeks:
                old.unlink()
        for week in sorted(weeks):
            shutil.copyfile(self.review_dir / f"tutorial_{week}.txt",
                            self.notes_dir / f"tutorial_{week}.txt")
        self.db_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.review_dir / "curriculum.json", self.db_dir / "curriculum.json")
        if (self.review_dir / "homework.json").exists():
            shutil.copyfile(self.review_dir / "homework.json", self.db_dir / "homework.json")
        self.log(f"install: {len(weeks)} weeks of notes, curriculum and homework copied")

    def check(self, retriever=None) -> dict:
        """Every topic must be answerable in its week and refused in the week before."""
        import rag_engine as rag
        from curriculum import load_curriculum

        retriever = retriever or rag.HybridRetriever()
        rows = []
        for topic in load_curriculum()["topics_by_id"].values():
            question = f"Explain {topic['name']}."
            in_week = rag.prepare_retrieval(question, topic["week"], retriever).status
            before = (rag.prepare_retrieval(question, topic["week"] - 1, retriever).status
                      if topic["week"] > 1 else "n/a")
            rows.append({"topic": topic["name"], "week": topic["week"],
                         "in_week": in_week, "week_before": before})
        answered = [r for r in rows if r["in_week"] in ("answer", "clarify")]
        refused = [r for r in rows if r["week_before"] in ("future", "n/a")]
        report = ["# Course self-check", "",
                  f"- Answerable in their own week: {len(answered)}/{len(rows)} topics",
                  f"- Refused one week earlier: {len(refused)}/{len(rows)} topics", "",
                  "| Topic | Week | In its week | Week before |", "|---|---|---|---|"]
        report += [f"| {r['topic']} | {r['week']} | {r['in_week']} | {r['week_before']} |"
                   for r in rows if r not in answered or r not in refused]
        self._write(self.review_dir / "self_check.md", "\n".join(report) + "\n")
        self.log(f"check: {len(answered)}/{len(rows)} answerable, {len(refused)}/{len(rows)} "
                 f"refused before their week (details: {self.review_dir / 'self_check.md'})")
        return {"rows": rows, "answered": len(answered), "refused": len(refused)}

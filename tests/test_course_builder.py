"""The course builder must turn any course's PDFs into a valid knowledge base."""
import json
from types import SimpleNamespace

import pytest

import course_builder as cb
from curriculum import validate_curriculum


def make_pdf(pages: list[str]) -> bytes:
    """A minimal valid PDF with one Helvetica text line per input line."""
    def escape(line):
        return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    page_ids = [4 + 2 * i for i in range(len(pages))]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>",
               f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] "
               f"/Count {len(pages)} >>",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    for page_id, text in zip(page_ids, pages):
        stream = "BT /F1 12 Tf 72 720 Td 14 TL " + " ".join(
            f"({escape(line)}) Tj T*" for line in text.split("\n")) + " ET"
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                       f"/Contents {page_id + 1} 0 R /Resources << /Font << /F1 3 0 R >> >> >>")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
    out, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n").encode()
    return out


class FakeLLM:
    """Deterministic stand-in that answers each builder prompt from the supplied text."""

    def __init__(self):
        self.calls = []

    def invoke(self, messages, **kwargs):
        system, user = messages[0].content, messages[-1].content
        self.calls.append(system)
        if "study notes from the lecture slides" in system:
            pages = [part.split("\n", 1) for part in user.split("[PDF page ")[1:]]
            notes = [{"group": "Core Concepts", "title": text.split("\n")[0].strip(),
                      "first_page": int(number.rstrip("]")), "last_page": int(number.rstrip("]")),
                      "body": " ".join(text.split()) + " The slide states this explicitly."}
                     for number, text in pages]
            reply = {"lecture_title": pages[0][1].split("\n")[0].strip(), "notes": notes}
        elif "list the topics it TEACHES" in system:
            topics = [{"name": "Quantum sort", "aliases": [], "kind": "method"}]
            if "Bubble sort" in user:
                topics.append({"name": "Bubble sort", "aliases": ["bubblesort", "algorithm"],
                               "kind": "method"})
            if "Breadth-first search" in user:
                topics.append({"name": "Breadth-first search", "aliases": ["BFS"], "kind": "method"})
                topics.append({"name": "Bubble sort", "aliases": [], "kind": "method"})
            reply = {"title_native": "", "topics": topics,
                     "title": "Bubble sort and its cost" if "Bubble sort" in user else "Graph search"}
        elif "map a homework problem" in system:
            problem = user.split("PROBLEM", 1)[1]
            reply = {"topic_ids": ["breadth_first_search"] if "BFS" in problem else ["bubble_sort"]}
        else:
            raise AssertionError(f"unexpected prompt: {system[:80]}")
        return SimpleNamespace(content=json.dumps(reply))


@pytest.fixture
def course_root(tmp_path):
    lectures, homework = tmp_path / "material" / "lectures", tmp_path / "material" / "Homework"
    lectures.mkdir(parents=True)
    homework.mkdir(parents=True)
    (lectures / "Lecture 1 sorting.pdf").write_bytes(make_pdf([
        "Sorting basics\nBubble sort repeatedly swaps adjacent items that are out of order.",
        "Bubble sort analysis\nBubble sort uses O(n^2) comparisons in the worst case."]))
    (lectures / "Lecture 2 graphs.pdf").write_bytes(make_pdf([
        "Graph search\nBreadth-first search (BFS) explores a graph layer by layer from a source."]))
    (homework / "HW1.pdf").write_bytes(make_pdf([
        "Problem 1\nSort the list 3, 1, 2 with bubble sort and count the swaps.",
        "Problem 2\nUse BFS to compute distances from vertex s."]))
    (tmp_path / "material" / "course.json").write_text(json.dumps(
        {"name": "Intro CS", "subject": "computer science", "unit_label": "Lecture"}),
        encoding="utf-8")
    return tmp_path


def test_full_build_from_pdfs(course_root):
    llm = FakeLLM()
    builder = cb.CourseBuilder(root=course_root, llm=llm, model_label="a fake model",
                               log=lambda *args: None)
    builder.extract()
    builder.notes()
    builder.topics()
    curriculum = builder.curriculum()
    homework = builder.homework()
    builder.install()

    review = course_root / "material" / "curriculum_review"
    assert "[PDF page 2]" in (review / "tutorial_1.source.txt").read_text(encoding="utf-8")
    notes = (review / "tutorial_1.txt").read_text(encoding="utf-8")
    assert notes.startswith("# Lecture 1 — Sorting basics")
    assert "### Bubble sort analysis — PDF page 2" in notes
    assert "a fake model" in notes

    topics = validate_curriculum(curriculum)
    assert {t: v["week"] for t, v in topics.items()} == {"bubble_sort": 1, "breadth_first_search": 2}
    assert topics["bubble_sort"]["aliases"] == ["bubblesort"]
    assert curriculum["course"]["name"] == "Intro CS"

    hw = homework["hw_1"]
    assert hw["problem_topics"] == {"1": ["bubble_sort"], "2": ["breadth_first_search"]}
    assert hw["week"] == 2 and hw["problem_pdf"] == "material/Homework/HW1.pdf"

    assert (course_root / "material" / "english" / "tutorial_2.txt").exists()
    assert json.loads((course_root / "db" / "curriculum.json").read_text(encoding="utf-8")) == curriculum
    assert (course_root / "db" / "homework.json").exists()


def test_existing_review_files_are_reused(course_root):
    builder = cb.CourseBuilder(root=course_root, llm=FakeLLM(), log=lambda *args: None)
    builder.extract()
    builder.notes()
    edited = course_root / "material" / "curriculum_review" / "tutorial_1.txt"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nHAND EDIT\n", encoding="utf-8")
    llm = FakeLLM()
    cb.CourseBuilder(root=course_root, llm=llm, log=lambda *args: None).notes()
    assert llm.calls == [] and "HAND EDIT" in edited.read_text(encoding="utf-8")


def test_homework_week_can_be_overridden(course_root):
    settings = course_root / "material" / "course.json"
    settings.write_text(json.dumps({"name": "Intro CS", "homework_weeks": {"hw_1": 1}}),
                        encoding="utf-8")
    builder = cb.CourseBuilder(root=course_root, llm=FakeLLM(), log=lambda *args: None)
    builder.extract()
    builder.notes()
    builder.topics()
    builder.curriculum()
    hw = builder.homework()["hw_1"]
    assert hw["week"] == 1 and "course.json" in hw["week_basis"]


def test_lecture_order_needs_numbers(tmp_path):
    lectures = tmp_path / "material" / "lectures"
    lectures.mkdir(parents=True)
    (lectures / "intro.pdf").write_bytes(make_pdf(["x"]))
    with pytest.raises(ValueError, match="no number"):
        cb.CourseBuilder(root=tmp_path, log=lambda *args: None).lectures()
    (lectures / "intro.pdf").unlink()
    (lectures / "week 1.pdf").write_bytes(make_pdf(["x"]))
    (lectures / "lecture 1 (copy).pdf").write_bytes(make_pdf(["x"]))
    with pytest.raises(ValueError, match="share a number"):
        cb.CourseBuilder(root=tmp_path, log=lambda *args: None).lectures()


def test_page_batches_keep_every_page_once():
    pages = ["a" * 2500, "", "b" * 2500, "c" * 2500, "d"]
    batches = list(cb.page_batches(pages, limit=6000))
    assert [(first, last) for first, last, _ in batches] == [(1, 3), (4, 5)]
    text = "".join(chunk for _, _, chunk in batches)
    assert all(f"[PDF page {n}]" in text for n in (1, 3, 4, 5)) and "[PDF page 2]" not in text


def test_topics_are_grounded_deduplicated_and_cleaned():
    raw = {"topics": [
        {"name": "Merge sort", "aliases": ["mergesort", "algorithm", "Bubble sort"], "kind": "method"},
        {"name": "Invented topic", "aliases": [], "kind": "concept"},
        {"name": "Bubble sort", "aliases": [], "kind": "method"},
        {"name": "merge sort", "aliases": [], "kind": "method"},
    ]}
    topics = cb.clean_topics(raw, 2, "Merge sort splits arrays. Bubble sort swaps.",
                             {"bubble sort": "bubble_sort"})
    assert topics == [{"id": "merge_sort", "name": "Merge sort", "aliases": ["mergesort"],
                       "kind": "method"}]


def test_ask_json_repairs_one_invalid_reply():
    replies = iter(["Sure! Here it is", '```json\n{"topic_ids": ["a"]}\n```'])
    llm = SimpleNamespace(invoke=lambda messages, **kw: SimpleNamespace(content=next(replies)))
    assert cb.ask_json(llm, "system", "user", {"type": "object"}) == {"topic_ids": ["a"]}
    bad = SimpleNamespace(invoke=lambda messages, **kw: SimpleNamespace(content="no json"))
    with pytest.raises(ValueError):
        cb.ask_json(bad, "system", "user", {"type": "object"})


def test_glossary_is_harvested_from_notes_and_aliases():
    weeks = [{"topics": [{"name": "Merge sort", "aliases": ["מיון מיזוג"]}]}]
    notes = ["The recursion tree (עץ הרקורסיה) bounds the work. A heap (ערימה; also ערמה) helps."]
    glossary = cb.harvest_glossary(notes, weeks)
    assert glossary["merge sort"] == "מיון מיזוג"
    assert glossary["recursion tree"] == "עץ הרקורסיה"
    assert glossary["heap"] == "ערימה"


def test_latex_swallowed_by_json_escapes_is_repaired():
    damaged = "$d < \text{inf}$ and $\x0crac{a}{b}$ with \x08eta"
    assert cb.repair_latex(damaged) == "$d < \\text{inf}$ and $\\frac{a}{b}$ with \\beta"
    assert cb.repair_latex("tab\t1") == "tab\t1"


def test_generic_lecture_title_is_replaced_by_topic_title(course_root):
    (course_root / "material" / "course.json").write_text(
        json.dumps({"name": "Sorting basics", "unit_label": "Lecture"}), encoding="utf-8")
    builder = cb.CourseBuilder(root=course_root, llm=FakeLLM(), log=lambda *args: None)
    builder.extract()
    builder.notes()
    builder.topics()
    review = course_root / "material" / "curriculum_review"
    notes = (review / "tutorial_1.txt").read_text(encoding="utf-8")
    topics = json.loads((review / "tutorial_1.topics.json").read_text(encoding="utf-8"))
    assert notes.startswith("# Lecture 1 — Bubble sort and its cost\n")
    assert topics["title"] == "Lecture 1 — Bubble sort and its cost"

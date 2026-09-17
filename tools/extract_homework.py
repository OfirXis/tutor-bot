"""Refresh db/homework.json from material/Homework PDFs, preserving week limits.

Run from any directory: python tools/extract_homework.py
Add a JSON entry with an explicit course week before adding a new assignment.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from homework_material import HOMEWORK_DIR, with_pdf_content  # noqa: E402

OUTPUT_FILE = ROOT / 'db' / 'homework.json'


def build_homework_database() -> dict:
    metadata = json.loads(OUTPUT_FILE.read_text(encoding='utf-8'))
    result = {}
    for pdf in sorted(HOMEWORK_DIR.iterdir()):
        match = re.match(r'HW(\d+)(?:_|$)', pdf.stem, re.IGNORECASE)
        if pdf.suffix.lower() != '.pdf' or not match:
            continue
        key = f'hw_{int(match.group(1))}'
        if key in result:
            raise ValueError(f'Multiple PDFs found for {key}')
        entry = metadata.get(key, {})
        if not isinstance(entry.get('week'), int) or entry['week'] < 1:
            raise ValueError(f'Set an explicit course week for {key} in {OUTPUT_FILE}')
        result[key] = with_pdf_content({
            **entry,
            'title': entry.get('title', f'Homework {int(match.group(1))}'),
            'problem_pdf': pdf.relative_to(ROOT).as_posix(),
        })
    if not result:
        raise ValueError(f'No homework PDFs found in {HOMEWORK_DIR}')
    missing = set(metadata) - set(result)
    if missing:
        raise ValueError(f'Missing PDFs for configured assignments: {sorted(missing)}')
    return result


def main() -> None:
    database = build_homework_database()
    for hw in database.values():
        hw.pop('topics', None)
        hw.pop('key_concepts', None)
    OUTPUT_FILE.write_text(json.dumps(database, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for key, hw in database.items():
        print(f"{key}: {hw['problems']} problems, course week <= {hw['week']}, {hw['problem_pdf']}")


if __name__ == '__main__':
    main()

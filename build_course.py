"""Build (or rebuild) the tutor's knowledge base for the course in COURSE_ROOT.

    python build_course.py --all             # generate, install, index and self-check
    python build_course.py                   # only generate review files
    python build_course.py --install --check # install reviewed files, index, verify
    python build_course.py --stages notes,topics --weeks 3 --force

See course_builder.py for what each stage produces.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from dotenv import load_dotenv

STAGES = ("extract", "notes", "topics", "curriculum", "homework")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stages", default=",".join(STAGES),
                        help=f"comma-separated subset of {', '.join(STAGES)}")
    parser.add_argument("--weeks", help="comma-separated lecture weeks to (re)generate")
    parser.add_argument("--force", action="store_true", help="regenerate existing review files")
    parser.add_argument("--install", action="store_true",
                        help="copy review files into material/english and db/, rebuild the index")
    parser.add_argument("--check", action="store_true", help="run the topic self-check")
    parser.add_argument("--all", action="store_true", help="generate, install and check")
    parser.add_argument("--model", help="model used for generation (default: the tutor model)")
    args = parser.parse_args()

    load_dotenv()
    from course_builder import CourseBuilder
    import rag_engine as rag

    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = set(stages) - set(STAGES)
    if unknown:
        parser.error(f"unknown stage(s): {', '.join(sorted(unknown))}")
    weeks = {int(w) for w in args.weeks.split(",")} if args.weeks else None

    llm, label = None, "an LLM"
    if {"notes", "topics", "homework"} & set(stages):
        # Generation needs long structured replies; give it room and patience.
        llm = rag.get_llm(streaming=False, model=args.model, max_tokens=4096, timeout=600)
        label = f"{os.getenv('LLM_PROVIDER', 'ollama')} model {getattr(llm, 'model', None) or getattr(llm, 'model_name', '?')}"
    builder = CourseBuilder(llm=llm, model_label=label)

    started = time.monotonic()
    if "extract" in stages:
        builder.extract(weeks, args.force)
    if "notes" in stages:
        builder.notes(weeks, args.force)
    if "topics" in stages:
        builder.topics(weeks, args.force)
    if "curriculum" in stages:
        builder.curriculum()
    if "homework" in stages:
        builder.homework(args.force)
    if args.install or args.all:
        builder.install()
        rag.build_index()
    if args.check or args.all:
        builder.check()
    print(f"Done in {time.monotonic() - started:.0f}s. Review files: {builder.review_dir}")
    if not (args.install or args.all):
        print("Review/edit them, then run: python build_course.py --install --check")
    return 0


if __name__ == "__main__":
    sys.exit(main())

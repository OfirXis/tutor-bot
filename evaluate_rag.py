"""Evaluate evidence selection and curriculum decisions, without LLM/API calls.

Run: .venv/bin/python evaluate_rag.py
The report measures passage retrieval, not correctness of generated answers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time

ROOT = Path(__file__).resolve().parent

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
import rag_engine as rag


def evaluate(cases: list[dict], retriever) -> list[dict]:
    homework = rag.load_homework()
    results = []
    for case in cases:
        start = time.perf_counter()
        question = case['question']
        # Match the app's raw-language gate before its existing translation step.
        raw_future = rag.named_future_topic(question, case['week'])
        if raw_future:
            decision = rag.RetrievalDecision('future', future_week=raw_future)
        else:
            decision = rag.prepare_retrieval(
                case.get('reference_translation', question), case['week'], retriever,
                homework.get(case.get('homework')), mode='dense')
        ids = [hit.chunk.id for hit in decision.hits]
        relevant = set(case.get('relevant_chunks', []))
        relevant_rank = next((i for i,cid in enumerate(ids,1) if cid in relevant), None)
        results.append({
            'id':case['id'],'category':case['category'],'question':question,
            'expected_status':case['expected_status'],'status':decision.status,
            'decision_correct':decision.status == case['expected_status'],
            'support_hit':bool(relevant.intersection(ids)),
            'reciprocal_rank':1/relevant_rank if relevant_rank else 0,
            'future_context_leaks':sum(h.chunk.tutorial > case['week'] for h in decision.hits),
            'chunks':ids,'similarities':[round(h.similarity,4) for h in decision.hits],
            'expected_chunks':sorted(relevant),'ms':round((time.perf_counter()-start)*1000,1),
        })
    return results


def write_report(results: list[dict], out: Path) -> None:
    answers = [r for r in results if r['expected_status']=='answer']
    future = [r for r in results if r['expected_status']=='future']
    unnecessary = [r for r in answers if r['status']!='answer']
    misses = [r for r in results if not r['decision_correct'] or (r['expected_chunks'] and not r['support_hit'])]
    lines=[
        '# RAG evidence evaluation', '',
        f'{len(results)} regression cases; dense retrieval; similarity floor {rag.EVIDENCE_MIN_SIMILARITY}.',
        'These are development/regression cases, not an independent held-out benchmark.',
        'Hebrew retrieval uses fixed reference translations; no translation model or external API was called.',
        'A supporting hit means a reviewed passage ID was retrieved, not merely the correct tutorial.', '',
        '| Check | Result |','| --- | --- |',
        f'| Correct answer/refusal/clarification decision | {sum(r["decision_correct"] for r in results)}/{len(results)} |',
        f'| Supporting passage among supplied evidence | {sum(r["support_hit"] for r in answers)}/{len(answers)} |',
        f'| Supporting-passage MRR | {statistics.mean(r["reciprocal_rank"] for r in answers):.3f} |',
        f'| Unnecessary abstentions on answerable cases | {len(unnecessary)}/{len(answers)} |',
        f'| Missed future-topic refusals | {sum(r["status"]!="future" for r in future)}/{len(future)} |',
        f'| Future-week passages supplied | {sum(r["future_context_leaks"] for r in results)} |',
        f'| Median decision time (includes retrieval) | {statistics.median(r["ms"] for r in results):.1f} ms |',
        '', '## Remaining misses', '',
    ]
    lines += [f'- `{r["id"]}`: {r["question"]} — expected {r["expected_status"]}, got {r["status"]}; '
              f'supporting passage found: {r["support_hit"]}; retrieved: {", ".join(r["chunks"]) or "none"}.' for r in misses] or ['None on these cases.']
    lines += ['', '## Limits and answer review', '',
        'This offline run does not invoke the optional model-assisted term normalization used '
        'by the app. Spelling and abbreviation cleanup has separate regression tests; the '
        'retrieval figures above do not measure its live model quality.', '',
        'This run does not generate answers and cannot establish mathematical correctness, factual entailment, '
        'or whether a live tutor gives away homework solutions. Source-ID validation is checked separately by tests; '
        'valid citation IDs alone do not prove the associated claims.',
        'Before a model change, review generated answers for: the exact original request, supported claims and citations, '
        'correct formulas, allowed concepts, and hints rather than full homework solutions. The homework cases include this rubric.',
        'Similarity plus content overlap is a conservative heuristic and can reject unfamiliar paraphrases. '
        'The report records such abstentions rather than counting them as successes.', '']
    out.write_text('\n'.join(lines),encoding='utf-8')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,default=ROOT/'eval/rag_cases.json')
    parser.add_argument('--out',type=Path,default=ROOT/'RAG_EVALUATION.md')
    parser.add_argument('--json-out',type=Path,default=ROOT/'eval/rag_results.json')
    args=parser.parse_args()
    cases=json.loads(args.cases.read_text(encoding='utf-8'))['cases']
    results=evaluate(cases,rag.HybridRetriever())
    write_report(results,args.out)
    args.json_out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{sum(r["decision_correct"] for r in results)}/{len(results)} decisions correct; report: {args.out}')


if __name__=='__main__':
    main()

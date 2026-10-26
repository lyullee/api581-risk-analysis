"""Build a lossless clause-review queue, without claiming mathematical completeness."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SUPPORT=re.compile(r'^(references|normative|informative|nomenclature|definitions(?: and acronyms)?|acronyms|purpose|introduction|organization and use|description of damage|overview|scope)$',re.I)


def _next_evidence(title: str, has_calculations: bool) -> str:
    """Return an actionable review prompt instead of one generic sentence."""
    normalized = title.strip().casefold()
    if normalized in {"references", "normative", "informative"}:
        return "Capture each cited document, edition and normative/informative role; verify that referenced requirements are represented in the calculation ledger."
    if normalized in {"definitions", "definitions and acronyms", "acronyms", "nomenclature"}:
        return "Reconcile source terminology and acronym meaning with standard metadata; record any calculation-affecting interpretation or unit basis."
    if normalized in {"scope", "purpose", "introduction", "organization and use", "overview"}:
        return "Record applicability, exclusions and workflow intent from the clause; link each actionable requirement to a typed API or explicit scope boundary."
    if normalized == "description of damage":
        return "Reconcile the damage-mechanism description with the applicable screening/assessment APIs and record unsupported mechanisms explicitly."
    if has_calculations:
        return "Read the clause and reconcile requirements with existing APIs and validation; linked calculations do not prove full clause coverage."
    return "Read the clause and check whether APIs exist without a clause link, a calculation is missing, or a documentary requirement applies."


def main():
    path=ROOT/'src/api581/data/coverage.json'
    raw=path.read_bytes()
    inventory=json.loads(raw)
    from api581.core import REGISTRY
    sections=inventory['sections']
    assert len({s['id'] for s in sections})==len(sections)
    queue=[]
    totals=defaultdict(Counter)
    for section in sections:
        assert set(section['calculation_ids'])<=REGISTRY.keys(),section['id']
        scope=section['id'].split(' §')[0]
        category='supporting_text_review' if SUPPORT.fullmatch(section['title'].strip()) else 'technical_scope_review'
        entry={**section,'scope':scope,'review_category':category,
            'next_evidence_needed':_next_evidence(section['title'], bool(section['calculation_ids']))}
        queue.append(entry)
        totals[scope][section['status']]+=1
    assert len(queue)==inventory['section_count']
    report=dict(standard_edition=inventory['standard_edition'],coverage_file_sha256=sha256(raw).hexdigest(),
        calculation_count=len(REGISTRY),section_count=len(queue),
        interpretation='Every source heading retained. Review categories are title-based triage only, not exclusions, completion status, calculation counts, effort estimates or implementation percentages. not_implemented can also mean missing linkage. All clauses require source review.',
        status_counts=dict(Counter(s['status'] for s in queue)),
        category_status_counts={category:dict(Counter(s['status'] for s in queue if s['review_category']==category)) for category in ('technical_scope_review','supporting_text_review')},
        scope_status_counts={scope:dict(counts) for scope,counts in totals.items()},clauses=queue)
    (ROOT/'docs/remaining-work.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('calculation_count','section_count','status_counts','category_status_counts')},ensure_ascii=False))


if __name__=='__main__':
    main()

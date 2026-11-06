"""Validate the finite HAS requirement ledger and render its readable overview."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'docs/completion_checklist.json'
OVERVIEW = ROOT / 'docs/completion_checklist.md'

def validate(data):
    assert data['format'] == 'has_completion_checklist_1'
    assert isinstance(data['scoring']['baseline_reviewed'], bool)
    groups = ['requirements', 'optional', 'decisions', 'external_blockers', 'control_requirements']
    records = [item for group in groups for item in data[group]]
    ids = [item['id'] for item in records]
    assert len(ids) == len(set(ids)), 'Duplicate stable requirement ID'
    known = set(ids)
    def file(name):
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts, name
        target = (ROOT / path).resolve()
        assert target.is_relative_to(ROOT) and target.is_file(), name
        return target
    for name in data['source_documents']:
        file(name)
    assert hashlib.sha256(file(data['goal']['path']).read_bytes()).hexdigest() == data['goal']['sha256'], 'Goal copy changed without provenance update'
    for item in data['requirements']:
        assert item['category'] in ['required_implementation', 'required_verification']
        assert item['implementation'] in ['implemented', 'partial', 'missing', 'not_applicable']
        assert item['verification'] in ['scoped_evidence', 'historical_only', 'incomplete', 'external_required', 'verified']
        assert item['acceptance_status'] in ['open', 'verified', 'external_blocked', 'decision_blocked']
        assert item['acceptance'].strip() and item['remaining'].strip() and item['evidence']
        assert item['source_sections']
        for section in item['source_sections']:
            assert re.fullmatch(r'(MD|ADD)\d+(?:\.[A-Za-z0-9-]+)*', section), section
        for evidence in item['evidence']:
            assert evidence['kind'] in ['source', 'recorded_report', 'test_result']
            file(evidence['path'])
        assert set(item['external_dependencies']) <= known
        if item['acceptance_status'] == 'verified':
            assert item['verification'] == 'verified'
            assert any(e['kind'] == 'test_result' and e.get('commit') and e.get('scope') for e in item['evidence']), 'Verified closure needs commit and scoped test evidence'
        if item['acceptance_status'].endswith('_blocked'):
            assert item['external_dependencies'], item['id']
    expected = {f'MD{n}' for n in range(1, 16)} | {f'ADD{n}' for n in range(21)}
    assert set(data['source_section_index']) == expected
    for mappings in [data['source_section_index'], data['acceptance_scenario_index']]:
        for referenced in mappings.values():
            assert referenced and set(referenced) <= known
    for action in data['next_actions']:
        assert action['requirement'] in known and action['priority'] in [0, 1, 2]
    for blocker in data['external_blockers']:
        assert set(blocker['prevents']) <= known and blocker['prerequisite'] and blocker['independent_work']
    for decision in data['decisions']:
        assert set(decision['needed_for']) <= known

def render(data):
    counts = Counter(item['category'] for item in data['requirements'])
    lines = ['# HAS completion checklist', '',
        'The exact active cloud goal is kept in [complete-has.md](goals/complete-has.md). '
        'The machine-readable ledger is [completion_checklist.json](completion_checklist.json). '
        'This is a finite engineering decomposition of the two governing documents, not a claim of product completion.', '',
        f"Baseline: `{data['baseline_commit']}`; {data['baseline_date']}. The addendum governs conflicts. "
        'Later established hold-Alt/MMB/auto-key choices remain resolved.', '',
        f"There are {counts['required_implementation']} required capability groups and {counts['required_verification']} required acceptance gates. "
        'Optional/conditional refinements and unresolved decisions are recorded separately. '
        'The JSON source-section and acceptance-scenario indexes provide the reverse mapping to both documents.', '',
        '## Reading the statuses', '',
        '`implemented` describes code coverage. `partial` and `missing` identify engineering work. '
        '`scoped_evidence` cites documented profile-specific tests; `historical_only` needs current closure. '
        'Neither means these tests were executed during this checklist audit. '
        'Whole-item acceptance closes only after its condition and supporting evidence have been audited.', '',
        'Recorded reports can contain narrower passes alongside native/device skips. '
        'Do not infer native fidelity, physical comfort or clean Windows readiness from procedural cloud tests. '
        'The earlier informal 70% estimate is not a measurement against this ledger.', '',
        '## Next required work', '']
    for action in data['next_actions']:
        lines.append(f"- **P{action['priority']} · {action['requirement']}** — {action['action']}")
    lines += ['', 'Prioritize these required gaps over optional UI/effect polishing. Resolve true owner decisions when needed, '
        'continue independent work while waiting, and do not declare the whole goal blocked merely because one gate is external.', '',
        '## Required implementation', '', '| ID | Capability | Implementation / evidence | Acceptance condition |', '|---|---|---|---|']
    for item in data['requirements']:
        if item['category'] != 'required_implementation':
            continue
        doc = next(e['path'] for e in item['evidence'] if e['kind'] == 'recorded_report')
        link = Path(doc).name if doc.startswith('docs/') else '../' + doc
        lines.append(f"| {item['id']} | {item['title']} | {item['implementation']} / {item['verification']} · [report]({link}) | {item['acceptance']} |")
    lines += ['', 'Detailed remaining work, implementation paths and source-section references are in the JSON ledger. '
        'A group is not closed merely because its menu exists or one fixture passes.', '',
        '## Required external acceptance', '', '| ID | Acceptance | Prerequisites |', '|---|---|---|']
    for item in data['requirements']:
        if item['category'] == 'required_verification':
            lines.append(f"| {item['id']} | {item['acceptance']} | {', '.join(item['external_dependencies'])} |")
    lines += ['', '### Exact missing prerequisites', '']
    for blocker in data['external_blockers']:
        lines += [f"- **{blocker['id']}**: {blocker['prerequisite']} Independent work: {blocker['independent_work']}"]
    lines += ['', '## Optional and conditional scope', '']
    for item in data['optional']:
        lines += [f"- **{item['id']} · {item['title']}** ({item['status']}): {item['rule']}"]
    lines += ['', 'Stage5 refinement is conditional on demonstrated stages1–4 and owner pain. '
        'Simple shadows already satisfy the Stage4 shadow-or-glow choice; optional glow is not a second mandatory acceptance gate. '
        'Native Source/MMD/VRM support is required by the governing addendum even though the earlier MD deferred some importers.', '',
        '## Unresolved decisions', '']
    for item in data['decisions']:
        lines += [f"- **{item['id']} · {item['title']}** ({item['status']}): {item['question']}"]
    lines += ['', 'Only independent native packaging currently has an explicit requirement-level owner-decision dependency. '
        'The other open details do not suspend work on the already decided core behavior. '
        'No new extension, third-party exporter, mandatory AI, public release or settings prompt is authorized by this checklist.', '',
        '## Scoring and closure', '', data['scoring']['method'], '',
        '**No numerical completion score is published while the initial baseline is under acceptance/evidence review.** '
        'This is an engineering audit, not a request for blanket user approval. '
        'Keep stable IDs; split or add requirements only through an explicit documented ledger revision. '
        'Blocked required items remain incomplete and in the acceptance denominator.', '',
        'To close an item, record `acceptance_status: verified`, `verification: verified` and a `test_result` '
        'reference with its commit and exact scope. Preserve failed/skipped/unrun and historical evidence. '
        'Keep a small curated closure receipt in the repository rather than committing incidental render/cache outputs. '
        'Do not close a broad requirement using a narrower procedural test. '
        'This tool checks ledger structure and file references; it does not certify the prose fully implements the source requirements.', '',
        'Validate and regenerate this overview with:', '', '```sh',
        'python tools/check_completion.py --write', 'python tools/check_completion.py', '```', '',
        'An incremental commit is not full completion. Continue with the next actionable required item. '
        'Finish only when required items are verified or explicitly externally blocked and all independent work is complete. '
        'Full product completion still requires all required acceptance conditions to pass.', '']
    return '\n'.join(lines)

def scores(data):
    if not data['scoring']['baseline_reviewed']:
        return None
    implementation = [r for r in data['requirements'] if r['category'] == 'required_implementation']
    required = data['requirements']
    def fraction(numerator, denominator):
        return dict(numerator=numerator, denominator=denominator,
                    checklist_unit_percent=round(100 * numerator / denominator, 2) if denominator else None)
    return dict(implementation_coverage=fraction(sum(r['implementation'] == 'implemented' for r in implementation), len(implementation)),
                acceptance_closure=fraction(sum(r['acceptance_status'] == 'verified' for r in required), len(required)))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='regenerate the readable overview')
    options = parser.parse_args()
    data = json.loads(LEDGER.read_text(encoding='utf-8'))
    validate(data)
    overview = render(data)
    if options.write:
        OVERVIEW.write_text(overview, encoding='utf-8')
    assert OVERVIEW.read_text(encoding='utf-8') == overview, 'Overview drift: regenerate with --write'
    print(json.dumps(dict(requirements=len(data['requirements']), implementation=dict(Counter(r['implementation'] for r in data['requirements'])), acceptance=dict(Counter(r['acceptance_status'] for r in data['requirements'])), completion_score=scores(data), reason=data['scoring']['reason']), indent=2))

if __name__ == '__main__':
    main()

"""Record completed archival/source work without implying active-full success."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
pins = {
    'neon_catalogue_00bf_actual_packet_20261117': '5f8ea1352707c02a914c51dd15c984a86c69e16e3199798ae0a988ecd61b34d7',
    'neon_catalogue_00bf_archive_recipe_20261117': '9678b1901a845e7a3612509530ad4d987b37a8ce498b448a89eb61b70a2db112',
    'neon_owner_cold187_after_qualified_copy_20261117': '7b12445a5c7f49076c5510f7d998c9d285b8d1297c56912a8488786d57f31888',
    'pmx_import_metadata_integration_map_20261117': '474b6bc933c41d869bb32f1cdbf101800f81c5634e886822aff9ba72005c9470',
    'pmx_import_metadata_helper_boundary_20261117': '49ffc77ff5a39f80ae187918f845a4734877fc075212de80c03827c1a9d1c3ae',
}
for folder, pin in pins.items():
    assert hashlib.sha256((ROOT / 'experiments' / folder / 'INDEX.json').read_bytes()).hexdigest() == pin
record = {
    'observed_utc': datetime.now(timezone.utc).isoformat(),
    'sealed_indexes': pins, 'closed_focused_archive': {'bindings': 69, 'objects': 61, 'private_jobs': 8},
    'source_CPU_only': {'archive': 32, 'cold187_adapter': 29, 'PMX_reader_regression': 33},
    'actual_cold187_run': False, 'PMX_native_qualification': False,
    'PMX_importer_integration': False, 'full_result_claimed': False, 'redesign_merged': False,
    'raw_successful_full_report_publication_permitted': False,
}
paragraph = '''
### November 17, 2026 — focused archive and inactive follow-up adapters

The closed 00bf catalogue/comparison/height results now have a compact exact
archive: 69 original bindings, 61 compressed text objects and eight real private
receipts. All 32 source/artifact CPU checks pass; root independently verified
the archive and every current original hash, size and timestamp. This preserves
the previously observed native results; it adds no new native case or full pass.

The fresh-owner startup/cold187 adapter is implemented but inactive. Its source
verifier and 29 CPU methods pass, preserving the original helpers, fixtures,
four cases and nine protection gates. Actual successful full verification,
closure, qualified merge, new copy and separately reviewed activation are still
required before any startup or 187 result. No owner model was opened by it.

The PMX integration map pins the current importer loss boundary and proposes
inert asset-owned preservation before simulation. The reader's 33 synthetic
CPU methods pass again; native PMX qualification and production integration
remain unrun. The master plan links the concrete map and its independent helper
JSON-budget addendum. No new native physics, solver, reconstruction or scale
normalization is claimed.

Source review confirms that a successful full verifier prints its complete
nested report into canonical.log. That raw report/log and the terminal-audit
directory must stay private because they can contain model data. An exact
ignore rule prevents accidental staging of this run's raw terminal directory;
publish only a separately reviewed explicit scalar projection. The active 00bf
full remains root-owned; this preparation claims no terminal outcome or merge.
Acceptance55/62 and implementation52/54 are unchanged; human checks deferred.
'''
for name in ('LLM.md', 'docs/progress_memo.md'):
    with (ROOT / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
path = ROOT / 'docs/benchmarks/neon_review_2026-11-17.json'
bench = json.loads(path.read_bytes())
bench['latest_source_followup'] = record
path.write_text(json.dumps(bench, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/completion_checklist.json'
ledger = json.loads(path.read_bytes())
ledger['next_actions'][0]['action'] = ('Continue frozen00bf full1029; root actual terminal/source/birth/private closure before qualified merge. '
    'Main4ec7b57 public checkpoint independently recovered694/694; preserve private full report/logs, publish only explicit scalar projection. '
    'Closed focused69/61/8 archive verified; cold18729CPU adapter inactive until actual full/merge/copy. PMX33CPU reader/map source-only; native qualification pending. Manual deferred.')
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'docs/NEXT_SESSION_PLAN_2026-11-17.md'
text = path.read_text(encoding='utf-8')
heading = '# HAS continuation — November 17, 2026\n'
assert text.count(heading) == 1
intro = '''
Completed follow-up source work: closed00bf focused archive5f8ea135 has69bindings/
61objects/8privatejobs,32CPU and root exact-original joins pass. Inactive cold187
adapter7b12445a preserves original187 predicates/fourcases/ninegates;29CPU pass,
actual startup/187 remains UNRUN. PMX map474b6bc9 and helper-budget49ffc77f remain
source-only; native qualification/importer integration/solver remain UNRUN.
Master plan section17 links the concrete next PMX increment.

PRIVATE: the full successful report, canonical.log and this run's raw terminal
audit directory can contain native model data. Do not publish them wholesale.
The exact .gitignore rule protects terminal-audit-attempt* under the00bf helper;
only an independently reviewed explicit scalar projection may be selected.

'''
text = text.replace(heading, heading + intro, 1)
path.write_text(text, encoding='utf-8', newline='\n')
print(json.dumps(record))

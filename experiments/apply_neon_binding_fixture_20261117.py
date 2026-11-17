"""Apply only the reviewed CR stripping expression after closed375 evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_source_binding_b64_fixture_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == '375ec05e925159850ff3b0abf2e8f98f9d2ce129'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=REVIEW).strip()
run = REVIEW / 'output/windows-neon-375ec05-20261117T033037'
release = json.loads((run / 'graphics-lease-closed.json').read_bytes())
assert release['released'] is True and release['physical_jobs'] == 51
before = json.loads((run / 'source-before.json').read_bytes())['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before.items())
target = REVIEW / 'tests/source_bone_bindings_unit.gd'
old = target.read_bytes()
new = (PACKET / 'source_bone_bindings_unit.proposed.gd').read_bytes()
assert sha(old) == 'a77d759d512f3bed34599bacccddb00be0ffb94806222261a827bf1cf25ed10d'
assert sha(new) == '80764dea7982a11f1d42a9bcbfb36b74c44edb6e620ddb585fa37dc1c8ab1e09'
first = b'GOLDEN_GLB.replace("\\n", "")'
second = b'GOLDEN_GLB.replace("\\r", "").replace("\\n", "")'
assert old.count(first) == new.count(second) == 1 and new.replace(second, first, 1) == old
target.write_bytes(new)
assert {name for name, pin in before.items() if sha((REVIEW / name).read_bytes()) != pin} == {'tests/source_bone_bindings_unit.gd'}
note = '''\n## Windows authored bone fixture line endings — 2026-11-17\n\nThe375 complete default passed helper208CPU/266graphical and later snapshot/editing
stages, then failed the authored bone fixture40/40 at base64 decoding. Its canonical
Git/main52 source was identical, but the working CRLF literal retained103CRs after
LF-only stripping. The fixture-only successor removes CR andLF before decoding;
9360-byte golden39637fa3 and9364-byte malformed95e0c878 remain exact. One expression
changes; all79+17predicates/wrapper/timeouts/error policy remain. Source10CPU methods
and independent10 pass; actual Foundation167/separate77+96 and full successor are
still required. Root closed51private jobs50exit0+Krita2 and separate headless exit1,
source1029 unchanged, released03:51:37Z. No product change/fullPASS/merge is claimed.
'''
for name in ('LLM.md', 'docs/REDESIGN-PORT.md'):
    with (REVIEW / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(note)
record = {'format': 'has_root_neon_binding_fixture_application_1', 'parent': '375ec05e925159850ff3b0abf2e8f98f9d2ce129',
    'changed_functional_paths': ['tests/source_bone_bindings_unit.gd'], 'old_sha256': sha(old), 'new_sha256': sha(new),
    'exact_one_expression_inverse': True, 'product_source_changed': False, 'actual_foundation': 'UNRUN', 'full_suite_pass_claimed': False}
with (ROOT / 'experiments/neon_binding_fixture_root_application_20261117.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print('Applied exactly one fixture expression; golden bytes and all79+17 checks unchanged.')

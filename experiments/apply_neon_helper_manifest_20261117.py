"""Apply only four reviewed manifest hash strings after closed4ed failure."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_helper_preview_manifest_20261117'
TARGET = REVIEW / 'tests/helper_preview_port_files.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == '4ed3a63b716f696daa1699a76443d6f1abb9b096'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=REVIEW).strip()
run = REVIEW / 'output/windows-neon-4ed3a63-20261117T030209'
state = json.loads((run / 'state.json').read_bytes())
release = json.loads((run / 'graphics-lease-closed.json').read_bytes())
assert state['status'] == 'failed' and release['released'] is True and release['physical_jobs'] == 49
before = json.loads((run / 'source-before.json').read_bytes())['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before.items())
old = TARGET.read_bytes()
new = (PACKET / 'helper_preview_port_files.proposed.json').read_bytes()
proof = json.loads((PACKET / 'SOURCE_PROOF.json').read_bytes())
assert sha(old) == proof['original_candidate_manifest_sha256'] == 'ce456c5ef5901df933946e68a2e47ee17a81e814bc98d072dce906dc713f9094'
assert sha(new) == proof['proposed_manifest_sha256'] == '2c9e483649108b9760aeb96e20c8ac95025a4b595fa0cfbb730308247fb7a8f0'
assert len(proof['changed_rows']) == 2 and proof['membership'] == 25 and proof['unchanged_rows'] == 23
inverse = new
for row in proof['changed_rows']:
    source = (REVIEW / row['path']).read_bytes()
    assert sha(source) == row['new_sha256'] and sha(source.replace(b'\r\n', b'\n')) == row['new_lf_sha256']
    for key in ('sha256', 'lf_sha256'):
        first, second = row['new_' + key].encode(), row['old_' + key].encode()
        assert inverse.count(first) == 1
        inverse = inverse.replace(first, second, 1)
assert inverse == old
TARGET.write_bytes(new)
assert {name for name, pin in before.items() if sha((REVIEW / name).read_bytes()) != pin} == {'tests/helper_preview_port_files.json'}
paragraph = '''\n## Windows helper preview source manifest — 2026-11-17\n\nThe4ed complete Windows run passed36core,Neon12504,scene106+unit12830 and
subsequent readback/fan/wind stages, then stopped03:19:31Z at the helper-preview
CPU source gate. Its old manifest rejected reviewed app.gd before snapshot or
helper engine/worker/graphical launch, with0checks. Root closed49physical jobs
(48exit0+registeredKrita cancel2), exact inline/source1029/birth/scope checks and
released03:19:55Z. No full PASS or merge is claimed. The minimal manifest refresh
changes only app/pose exact+LF hash strings to the reviewed Neon bytes, already
pinned in the wind manifest. Membership25,23other rows and driver/208CPU/266GPU
predicates are unchanged. Source-only18tamper tests and independent peer18 pass;
fresh actual helper profiles and another complete default are still required.
'''
for name in ('LLM.md', 'docs/REDESIGN-PORT.md'):
    with (REVIEW / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(paragraph)
record = {'format': 'has_root_neon_helper_manifest_application_1', 'parent': state['source_commit'],
    'old_manifest_sha256': sha(old), 'new_manifest_sha256': sha(new), 'changed_functional_paths': ['tests/helper_preview_port_files.json'],
    'changed_hash_values': 4, 'product_source_changed': False, 'actual_helper_profiles': 'UNRUN', 'full_suite_pass_claimed': False,
    'physical_jobs_preceding_run_closed': 49, 'main_merged': False}
with (PACKET.parent / 'neon_helper_manifest_root_application_20261117.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print('Applied exactly four reviewed hash strings; product and helper tests unchanged.')

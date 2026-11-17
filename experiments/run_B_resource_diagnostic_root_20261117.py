"""Actual root admission for the narrow read-only diagnostic; no fidelity claim."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
HERE = ROOT / 'experiments/native_normal_resource_diagnostic_failed_full_20261117'
INDEX = '7273d278b77dc9bb12c5763e7993013be717b177ea19c27b625b0649ca62fc5d'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
load = lambda p: json.loads(p.read_bytes())
assert sha((HERE / 'INDEX.json').read_bytes()) == INDEX
spec = importlib.util.spec_from_file_location('root_readonly_B_diagnostic_support', HERE / 'diagnostic_support.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
S.packet(HERE, INDEX)
reader = S.reader()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == 'a41a204bffb98614abfa80e0e6340078b1d719f1'
old = load(ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json')
assert old['commit'] == '52f63c944ded7a651da871524d23a345b606424d'
S.check_snapshot(ROOT, old, old['commit'], 1019)
run = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051'
release_path = run / 'graphics-lease-closed.json'
release = load(release_path)
assert release['released'] is True and release['full_suite_passed'] is False
assert release['receipt_inventory_sha256'] == 'acd509905aed7330636e0300d6ed48b9453ec1d1ed3a121130dba7509b888328'
assert release['functional_sources'] == 1029 and release['suite_exit'] == 1
review_path = run / 'source-after.json'
S.check_snapshot(REVIEW, load(review_path), '00bf0f916a549f5e858cb39dd91a149071fd5181', 1029)
folder = ROOT / 'output/B-resource-diagnostic-root-admission-20261117-attempt1'
folder.mkdir(exist_ok=False)
root_path = folder / 'CURRENT_ROOT_FUNCTIONAL_SNAPSHOT.json'
S.save(root_path, old)
def descriptor(path):
    return {'path': str(path), **reader.identity(path)}
admission = load(HERE / 'ADMISSION.template.json')
admission['expected_metadata_head'] = head
admission['root_native_lane_exclusive'] = True
admission['sourceio_copy'] = str(REVIEW / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
for role, path in [('full_release', release_path), ('functional_snapshot', root_path), ('review_functional_snapshot', review_path)]:
    admission['proofs'][role] = descriptor(path)
for role, row in admission['protected_originals'].items():
    actual = descriptor(Path(row['path']))
    assert actual['bytes'] == row['bytes'] and actual['sha256'] == row['sha256']
    admission['protected_originals'][role] = actual
not_started = load(HERE / 'COLD187-NOT-STARTED.template.json')
not_started.update(root_native_lane_exclusive=True, root_metadata_head=head,
    full_release_sha256=admission['proofs']['full_release']['sha256'],
    root_snapshot_sha256=admission['proofs']['functional_snapshot']['sha256'],
    review_snapshot_sha256=admission['proofs']['review_functional_snapshot']['sha256'],
    observed_utc=datetime.now(timezone.utc).isoformat())
not_started_path = folder / 'COLD187-NOT-STARTED.json'
S.save(not_started_path, not_started)
admission['proofs']['cold187_not_started_root_record'] = descriptor(not_started_path)
issued = datetime.now(timezone.utc)
admission['issued_utc'] = issued.isoformat()
admission['expires_utc'] = (issued + timedelta(seconds=600)).isoformat()
S.validate_admission(admission, issued)
S.validate_failed_full_lane(admission, {'full_release': release, 'cold187_not_started_root_record': not_started})
path = folder / 'ADMISSION.json'
S.save(path, admission)
command = [sys.executable, '-B', str(HERE / 'root_runner.py'), '--admission', str(path),
    '--admission-sha256', sha(path.read_bytes()), '--packet-index-sha256', INDEX, '--root-lane-confirmed']
S.save(folder / 'ROOT_COMMAND.json', command)
subprocess.run(command, cwd=HERE, check=True)

"""Derive the same exact public-text backup recipe for the fixture successor."""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
old_path = ROOT / 'experiments/backup_neon_375_candidate_20261117.py'
raw = old_path.read_bytes()
assert raw == subprocess.check_output(['git', 'show', 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a:experiments/backup_neon_375_candidate_20261117.py'], cwd=ROOT)
source = raw.decode('utf-8')
changes = {
    "DEST = ROOT / 'experiments/neon_375_candidate_reconstruction_20261117'": "DEST = ROOT / 'experiments/neon_fe9_candidate_reconstruction_20261117'",
    "COMMIT = '375ec05e925159850ff3b0abf2e8f98f9d2ce129'": "COMMIT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'",
    "PARENT = '4ed3a63b716f696daa1699a76443d6f1abb9b096'": "PARENT = '375ec05e925159850ff3b0abf2e8f98f9d2ce129'",
    "'tests/helper_preview_port_files.json'": "'tests/source_bone_bindings_unit.gd'",
    "'parent_available_remote': PARENT": "'parent_reconstruction': {'commit': PARENT, 'main_checkpoint': 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a', 'packet': 'experiments/neon_375_candidate_reconstruction_20261117'}",
    "'review_branch_push': 'AUTO_REVIEW_REJECTED_NOT_RETRIED'": "'review_branch_push': 'NOT_ATTEMPTED_AFTER_PRIOR_BRANCH_REJECTION'",
}
for first, second in changes.items():
    assert source.count(first) == 1, first
    source = source.replace(first, second, 1)
lines = source.splitlines(keepends=True)
selected = [i for i, line in enumerate(lines) if line.startswith("(DEST / 'README.md').write_text(")]
assert len(selected) == 1
readme = ('This reconstructs localfe9aace from375ec05 using three exact public Git text blobs, patch, commit/tree identities and tested working-EOL recipes. '
    'Parent375 is reconstructed from experiments/neon_375_candidate_reconstruction_20261117 in independently verified main checkpoint e8cf93ce; its parent4ed is on the remote review branch. '
    'The fe9 review-branch upload was not attempted after the prior branch rejection. Main source/evidence publication does not merge or activate the redesign. '
    'Only the authored base64 line-ending fixture and two review notes differ from375; actual foundation167/separate77+96 pass, complete Windows qualification remains unfinished. '
    'Private native models/art/media/arrays are excluded.\n')
lines[selected[0]] = "(DEST / 'README.md').write_text(" + repr(readme) + ", encoding='utf-8', newline='\\n')\n"
target = ROOT / 'experiments/backup_neon_fe9_candidate_20261117.py'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(''.join(lines))
print({'derived_backup': str(target), 'source_sha256': hashlib.sha256(raw).hexdigest(), 'new_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})

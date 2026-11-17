"""Derive the reviewed public-text backup recipe for the two-selector successor."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'experiments/backup_neon_fe9_candidate_20261117.py'
source = path.read_text(encoding='utf-8')
changes = {
    "DEST = ROOT / 'experiments/neon_fe9_candidate_reconstruction_20261117'": "DEST = ROOT / 'experiments/neon_00bf_candidate_reconstruction_20261117'",
    "COMMIT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'": "COMMIT = '00bf0f916a549f5e858cb39dd91a149071fd5181'",
    "PARENT = '375ec05e925159850ff3b0abf2e8f98f9d2ce129'": "PARENT = 'fe9aace86f7a349c90a951ff26d76f746d1e4701'",
    "{'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/source_bone_bindings_unit.gd'}": "{'LLM.md', 'docs/REDESIGN-PORT.md', 'tests/verify_shape_catalog.py', 'tests/verify_character_height.py'}",
    "'parent_reconstruction': {'commit': PARENT, 'main_checkpoint': 'e8cf93ce25811cbc967b1024a6d2c87ffd9cfb9a', 'packet': 'experiments/neon_375_candidate_reconstruction_20261117'}": "'parent_reconstruction': {'commit': PARENT, 'packet': 'experiments/neon_fe9_candidate_reconstruction_20261117', 'main_publication': 'PENDING_WITH_THIS_INCREMENT'}",
}
for first, second in changes.items():
    assert source.count(first) == 1, first
    source = source.replace(first, second, 1)
lines = source.splitlines(keepends=True)
selected = [i for i, line in enumerate(lines) if line.startswith("(DEST / 'README.md').write_text(")]
assert len(selected) == 1
readme = ('This reconstructs local00bf0f9 fromfe9aace using four exact public Git text blobs, patch, commit/tree identities and tested working-EOL recipes. '
    'Parentfe9 is reconstructed from experiments/neon_fe9_candidate_reconstruction_20261117; parent375 is backed by mainE8 and its parent4ed is on the remote review branch. '
    'The review-branch upload was not attempted after the prior branch rejection. Main evidence publication does not merge or activate the redesign. '
    'Only two test fixture selectors and two review notes differ fromfe9; focused catalogue130/unit34,comparison94,height105/rawVRM9 pass, complete Windows qualification remains unfinished. '
    'Private native models/art/media/arrays are excluded.\n')
lines[selected[0]] = "(DEST / 'README.md').write_text(" + repr(readme) + ", encoding='utf-8', newline='\\n')\n"
target = ROOT / 'experiments/backup_neon_00bf_candidate_20261117.py'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(''.join(lines))
print(str(target))

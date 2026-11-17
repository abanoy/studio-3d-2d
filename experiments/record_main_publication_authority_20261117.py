"""Record the explicitly requested main-checkpoint scope after branch rejection."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
source = Path('C:/a/Programming/HAS/WINDOWS_CODEX_GOAL.md')
raw = source.read_bytes()
text = raw.decode('utf-8')
instruction = 'Commit verified source, tests and compact progress/evidence. Push to main without\n   force; preserve and reconcile concurrent work.'
assert instruction in text
assert 'Repository: https://github.com/abanoy/studio-3d-2d' in text
record = {'format': 'has_explicit_main_checkpoint_publication_scope_1',
    'user_instruction': 'Read START_HERE.md and follow WINDOWS_CODEX_GOAL.md.', 'instruction_source_path': str(source),
    'instruction_source_sha256': hashlib.sha256(raw).hexdigest(), 'exact_instruction': instruction,
    'authorized_repository': 'https://github.com/abanoy/studio-3d-2d', 'authorized_destination_ref': 'refs/heads/main',
    'force_push': False, 'redesign_product_merge': False,
    'payload_scope': 'Completed public source/tests/compact text evidence, explicit failed/unrun/running scope, protected private art/native arrays/media excluded.',
    'review_branch_375_push': 'AUTO_REVIEW_REJECTED_NOT_RETRIED',
    'safer_action': 'Use the separately explicit main source/evidence checkpoint rule; retain optional review branch at4ed remotely. A public text reconstruction packet preserves375 without activating its application changes.',
    'remote_readonly_observation': {'main': '09fb70ed86b5a704caba34e60be6b24e12aa68a6', 'claude/studio-redesign': 'c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2', 'codex/neon-windows-review-20261116': '4ed3a63b716f696daa1699a76443d6f1abb9b096'},
    'cleanup_performed': False}
target = ROOT / 'experiments/neon_main_publication_scope_20261117.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print('Recorded explicit main-only source/evidence scope; rejected branch push not retried.')

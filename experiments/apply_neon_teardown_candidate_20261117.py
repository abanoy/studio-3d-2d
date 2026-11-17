"""Apply only the reviewed lifecycle changes after failed-run closure."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_world_teardown_fix_20261117'
RUN = REVIEW / 'output/windows-neon-f387d0e-20261117T012410'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(PACKET / 'INDEX.json') == '559fe707fdd7668b23e6130c6c596db036ae3eaf141c748fd7e03bf6716a0a6b'
for row in json.loads((PACKET / 'INDEX.json').read_bytes())['files']:
    assert sha(PACKET / row['path']) == row['sha256']
release = json.loads((RUN / 'graphics-lease-closed.json').read_bytes())
assert release['released'] is True and release['release_kind'] == 'closed_failed_partial_run'
assert release['physical_jobs'] == 36 and release['final_full_report_used'] is False
before = json.loads((RUN / 'source-before.json').read_bytes())['source_sha256']
pins = {'src/world_selection.gd': 'fb2cfa70ab94dbf4d9a57c3f041cb10916aed7e828c94af14feee6ade0b790de',
        'src/workspace_layout.gd': '7da378b1147266fbecdabf63422e19b1ee06024c40083d6fcf4ed8e93540bcfd'}
for name, pin in pins.items():
    assert sha(REVIEW / name) == before[name]
    assert sha(PACKET / (Path(name).name + '.proposed')) == pin
script = PACKET / 'neon_world_rail_lifecycle.gd'
assert sha(script) == 'f43e60a6e1c6a6c23b7f3bef0efe43fc1849e24e0f093b1b8fb6628e5474770f'
alias = REVIEW / 'experiments/neon_world_teardown_regression_20261117/neon_world_rail_lifecycle.gd'
assert not alias.exists()
out = ROOT / 'experiments/neon_world_teardown_actual_20261117'
out.mkdir(exist_ok=False)
for name in pins:
    (REVIEW / name).write_bytes((PACKET / (Path(name).name + '.proposed')).read_bytes())
alias.parent.mkdir(parents=True, exist_ok=False)
alias.write_bytes(script.read_bytes())
assert all(sha(REVIEW / name) == pin for name, pin in pins.items())
record = {'format': 'has_root_neon_lifecycle_candidate_applied_1', 'source_packet_index': sha(PACKET / 'INDEX.json'),
          'parent': 'f387d0e9ddfb099140c0699d9f7ed430f5d7b949', 'production_sha256': pins,
          'fixture_alias': str(alias), 'fixture_sha256': sha(alias), 'main_merged': False,
          'font_factory_and_visuals_changed': False, 'actual_fix_qualification': 'UNRUN'}
(out / 'APPLIED.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))

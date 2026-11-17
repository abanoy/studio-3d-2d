"""Apply only the two reviewed test selectors; native cases and all checks retained."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
PACKET = ROOT / 'experiments/neon_shape_catalog_fixture_root_20261117'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW, text=True).strip() == 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=REVIEW).strip()
run = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'
release = json.loads((run / 'graphics-lease-closed.json').read_bytes())
assert release['released'] is True and release['physical_jobs'] == 68
before = json.loads((run / 'source-before.json').read_bytes())['source_sha256']
assert len(before) == 1029 and all(sha((REVIEW / name).read_bytes()) == pin for name, pin in before.items())
prepared = []
for name, pin in [('verify_shape_catalog', '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057'),
                  ('verify_character_height', 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79')]:
    target = REVIEW / 'tests' / (name + '.py')
    old = target.read_bytes()
    assert old == (PACKET / ('original-' + name + '.py')).read_bytes()
    new = (PACKET / (name + '.proposed.py')).read_bytes()
    assert sha(new) == pin
    inverse = new
    if name == 'verify_shape_catalog':
        first, second = b"face=fixture_output()/'sfm-face-pilot.json'", b"face=ROOT/'output/sfm-face-pilot.json'"
    else:
        line = b'from native_fixture_root import fixture_output\r\n'
        assert inverse.count(line) == 1
        inverse = inverse.replace(line, b'', 1)
        first, second = b"native_manifest=fixture_output()/'native-import-verification.json'", b"native_manifest=ROOT/'output/native-import-verification.json'"
    assert inverse.count(first) == 1 and inverse.replace(first, second, 1) == old
    prepared.append((target, new))
for target, raw in prepared:
    target.write_bytes(raw)
changed = {name for name, pin in before.items() if sha((REVIEW / name).read_bytes()) != pin}
assert changed == {'tests/verify_shape_catalog.py', 'tests/verify_character_height.py'}
note = '''\n## Windows native fixture-root selectors — 2026-11-17\n\nThefe9 full passed all earlier corrected stages, then shape catalogue selected a
stale local Mima descriptor instead of the configured fixture root. Root closed
68private jobs(67exit0+Krita2), source1029unchanged, released04:29:31Z. Catalogue
now uses its existing fixture_output helper for that descriptor. Character-height,
another registered later consumer, imports the same helper for its raw VRM manifest
instead of silently missing that native case. Both default paths remain identical
without override; all original native cases/assertions/movie thresholds remain.
Two independent11-method source/AST CPU runs pass. Root currentMima hash/size
matches its own retained descriptor and exact priorMain52 catalogue plan; this
does not recover or substitute the different oldb577bundle. Actual focused checks
and another complete default are required. Product code/look and merge status
remain unchanged; no full PASS or artist fidelity is inferred.
'''
for name in ('LLM.md', 'docs/REDESIGN-PORT.md'):
    with (REVIEW / name).open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(note)
record = {'format': 'has_root_neon_fixture_selector_application_1', 'parent': 'fe9aace86f7a349c90a951ff26d76f746d1e4701',
    'changed_functional_paths': sorted(changed), 'product_source_changed': False,
    'actual_catalogue_and_height': 'UNRUN', 'full_suite_pass_claimed': False}
with (ROOT / 'experiments/neon_fixture_selectors_root_application_20261117.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print('Applied only catalogue/height native fixture selectors; all original cases and assertions retained.')

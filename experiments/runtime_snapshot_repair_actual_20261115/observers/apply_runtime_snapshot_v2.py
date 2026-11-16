"""Apply exactly the reviewed three-file snapshot fix after failed lease closure."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/world_selection_runtime_snapshot_v2_20261115'
EXPECTED_INDEX='d7da7eb2c50457d839266eb72d62e277cf3df53b5efe06ce66a2e6d6830091cd'
TARGETS={'tools/build_owner_review_snapshot.py':'48d6fc852ae16c946431addd39ec152e5db45c7f887bc1ddc941fc332911a0ce',
         'tests/verify_world_selection_teardown.py':'137322921a83fcbb6cee558cb951ede5f3691c4c96e5b1ab7abdb735680f0bfb',
         'tests/test_owner_review_snapshot.py':'d771929e26202724a0c70918be1a90320d156e724eaa1a3b2e8f63ca22f268b8'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(PACKET/'INDEX.json')==EXPECTED_INDEX
for name,row in json.loads((PACKET/'INDEX.json').read_bytes())['files'].items():
    relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts
    path=PACKET/relative
    assert not path.is_symlink() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
release_path=ROOT/'output/windows-canonical-bone-binding-20261116T022132132/graphics-lease-closed-after-failure.json'
release=json.loads(release_path.read_bytes())
assert release['released'] and not release['full_suite_passed'] and release['owned_runtime_commands_absent'] and release['owned_private_helpers_wrappers_absent']
assert release['observed_partial_private_jobs']==46 and release['all_collected_jobs_desktops_closed_private']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='dbf0bc1145f74b5bbff814ec6a417ccd23ce0885'
provenance=json.loads((PACKET/'SOURCE_PROVENANCE.json').read_bytes())
for name,expected in provenance['original_sha256'].items():assert sha(ROOT/name)==expected,'Original changed: '+name
for name,expected in TARGETS.items():assert sha(PACKET/'draft'/name)==expected
before={name:sha(ROOT/name) for name in TARGETS}
for name,expected in TARGETS.items():
    target=ROOT/name;assert target.resolve().is_relative_to(ROOT) and not target.is_symlink()
    target.write_bytes((PACKET/'draft'/name).read_bytes())
    assert sha(target)==expected
result={'format':'has_reviewed_runtime_snapshot_v2_application_1','packet_index_sha256':EXPECTED_INDEX,
        'before':before,'after':TARGETS,'release_sha256':sha(release_path),
        'unchanged_other_source_files':{name:expected for name,expected in provenance['original_sha256'].items() if name not in TARGETS},
        'runtime_executed':False,'timeouts_or_teardown_assertions_changed':False}
with (ROOT/'output/runtime-snapshot-v2-applied.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'applied':list(TARGETS),'runtime_executed':False}))

"""CPU/source-only validation. No engine/GDScript parser or native geometry reads."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACTUAL = ROOT / 'output/source-0x31-native-chains-20261115-attempt1'


def load(name):
    return json.loads((HERE / name).read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    profile = load('PUBLIC_PROFILE.json'); static = load('STATIC_PREPARATION.json'); sources = load('SOURCE_PROVENANCE.json')
    assert profile['status'].endswith('GDSCRIPT_UNPARSED_UNRUN')
    assert profile['native_bones'] == 69 and profile['retained_rules'] == 49 and profile['selected_rule_count'] == 7
    assert profile['selection_descendant_closed'] is True and profile['unselected_world_bones_expected_exact'] == 62
    assert profile['branches'] == [[35,36,37],[60,61,62,63]]
    rows = {row['native_index']:row for row in profile['selected']}
    assert set(rows) == {35,36,37,60,61,62,63}
    parents = {35:34,36:35,37:36,60:59,61:60,62:61,63:62}
    for index,row in rows.items():
        assert row['parent'] == parents[index] and row['raw_flags'] == 0x31
        assert set(row['children']) == {key for key,parent in parents.items() if parent == index}
        assert set(row['descendant_closed_subtree']) <= set(rows)
    assert profile['cross_branch_shared_vertex_count'] == 0
    expected = {'union':(980,158,8681),'branch35_36_37':(326,158,9335),'branch60_61_62_63':(654,0,9007)}
    for key,(affected,shared,unaffected) in expected.items():
        got = profile['influence_counts'][key]
        assert got['vertices'] == 9661 and got['weighted_to_selected'] == affected
        assert got['shared_with_other_bones'] == shared and got['unaffected'] == unaffected
        assert re.fullmatch('[a-f0-9]{64}',got['descendant_closed_mask_sha256'])
    assert 326+654 == 980 and 980+8681 == 9661
    for name,digest in sources['unchanged_donor_sha256'].items():
        assert sha((HERE / name).read_bytes()) == digest
        assert (HERE / name).read_bytes() == (ACTUAL / 'Studio' / name).read_bytes()
    adapter = (HERE / 'model_adapter.gd').read_text(); harness = (HERE / 'chain_harness.gd').read_text()
    donor_adapter = (ACTUAL / 'Studio/model_adapter.gd').read_text()
    donor_harness = (ACTUAL / 'Studio/chain_harness.gd').read_text()
    capture = lambda text,first,last: text[text.index(first):text.index(last,text.index(first))]
    assert capture(adapter,'static func capture_baseline(', 'static func overlay(') == capture(donor_adapter,'static func capture_baseline(', 'static func overlay(')
    overlay = adapter[adapter.index('static func overlay('):].replace('seven-rule','four-rule')
    assert overlay == donor_adapter[donor_adapter.index('static func overlay('):]
    for gate in ('check(error.basis <= EPS,','check(error.origin <= EPS*root_size,',
                 'check(tip_error <= EPS*root_size,','check(var_to_bytes(actor.sample(FRAME,false)) == authored_bytes,',
                 'check(delta.unaffected_exact,','check(exact_snapshot(actor) == snap24,',
                 'check(exact_snapshot(actor) == snap12 and actor.live_pose == null and actor.live_world_transform == null,',
                 'check(restoration.all_points_exact,','check(Bindings.current(actor,resolution),',
                 'check(results.positive12.public.final_weighted_sha256 == results.repeat12.public.final_weighted_sha256,'):
        assert harness.count(gate) == donor_harness.count(gate) == 1
    assert harness.count('difference.affected_max > MOTION_MIN*root_size') == 1
    assert harness.count('difference.affected_max > MOTION_MIN*root_scale') == 1
    assert 'const EPS := 0.00002' in adapter
    leaf = (HERE / 'leaf_harness.gd').read_text()
    for setting in ('const EPS := 0.00002','const MOTION_MIN := 0.00001','const FRAME := 12','const TICKS := 120'):
        assert setting in leaf
    assert 'var context := compatible_import_context(actor,profile.skeleton,resolution.bindings[17])' in harness
    assert 'var final_context := compatible_import_context(actor,profile.skeleton,resolution.bindings[17])' in harness
    assert 'all62 unselected world bones exact' in harness and 'rule_evaluations += 7' in harness
    for path in HERE.glob('*.py'): ast.parse(path.read_text())
    # Source lint only. This is not a GDScript parse or runtime claim.
    for path in HERE.glob('*.gd'):
        assert not re.search(r'(?m)^\s*(class_name\b|@tool\b)',path.read_text())
    budget = static['budget']
    per_profile_base = 69+120*(3*7+2)+1+4
    per_root = 6*per_profile_base+5*2+4*2+1
    expected_checks = 2*per_root+1
    assert expected_checks == 34047 == budget['proposed_assertions']
    assert expected_checks == 21087+12*120*3*3
    assert budget['proposed_actor_ticks'] == 2*6*120 == 1440
    assert budget['proposed_rule_evaluations'] == 1440*7 == 10080
    assert budget['actual_run'] is False
    template = load('ROOT_LEASE_UNAPPROVED_TEMPLATE.json')
    assert template['phase'] == 'UNAPPROVED_SOURCE_ONLY_TEMPLATE' and template['root_closed_all'] is False
    assert template['expires_unix'] == 0
    assert template['files']['source_lock']['sha256'] == '0'*64
    assert template['format'] == 'has_native_deep_chain_readiness_lease_1'
    assert template['pair_status'] == 'UNRUN'
    assert 'ROOT_APPROVED_AFTER_FRESH_FULL_FK_MATH_LEAF_PAIR_AND_CLOSURE' in harness
    assert '"pair_receipt"' in harness
    predecessor = json.loads((ACTUAL / 'verification.json').read_bytes())
    assert predecessor['passed'] and predecessor['math_result']['checks'] == 4012
    assert predecessor['result']['checks'] == 21087 and predecessor['result']['failures'] == 0
    # JSON fields may contain scalar coefficients, names, index topology and
    # hashes. No actual model coordinate/skin/native arrays or media are allowed.
    forbidden = {'positions','normals','uvs','weights','rest','rests','rest_matrices','points','pcm','base64','buffer','buffers','mask','geometry'}
    def privacy(value):
        if isinstance(value,dict):
            for key,child in value.items():
                assert key.lower() not in forbidden
                privacy(child)
        elif isinstance(value,list):
            for child in value: privacy(child)
        elif isinstance(value,str):
            assert len(value) < 2048 and not value.startswith('data:')
        else:
            assert value is None or type(value) in (int,float,bool)
    for path in HERE.glob('*.json'): privacy(json.loads(path.read_bytes()))
    if (HERE / 'INDEX.json').exists():
        index = load('INDEX.json')
        payloads = {path.relative_to(HERE).as_posix() for path in HERE.rglob('*')
                    if path.is_file() and path.name != 'INDEX.json'}
        assert len(index['files']) == index['files_count'] == len(payloads)
        assert {row['path'] for row in index['files']} == payloads
        assert index['bytes'] == sum(row['bytes'] for row in index['files'])
        for row in index['files']:
            relative = Path(row['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            path = HERE / relative
            assert path.suffix in {'.py','.gd','.json','.md','.patch'} and not path.is_symlink()
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    report = {'format':'has_deep_chain_static_source_verification_1','passed':True,
              'GDScript':'UNPARSED_UNRUN','runtime_or_process_or_Git_used':False,
              'selected_rules':7,'descendant_closed_branches':2,'crosswalk69_and_subtree_source_profile':True,
              'unchanged_qualified_sources':len(sources['unchanged_donor_sha256']),
              'unchanged_numeric_Off_motion_repeat_gates':True,
              'proposed_assertions':34047,'proposed_actor_ticks':1440,'proposed_rule_evaluations':10080,
              'actual_motion_or_native_qualification_claimed':False,'media_or_native_coordinate_arrays_published':False}
    print(json.dumps(report,sort_keys=True))


if __name__ == '__main__':
    main()

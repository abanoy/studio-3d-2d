"""Unapplied draft source/hash/privacy checks; no runtime or GDScript parser."""
from pathlib import Path
import ast
import contextlib
import hashlib
import io
import json
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def block(source,start,end):
    return source[source.index(start):source.index(end,source.index(start))]


def main():
    original = (ROOT/'src/source_secondary.gd').read_bytes()
    assert sha(original) == 'd2c04165587ca3bb0f7b9f474b23dc81902cc78c1aa174d593534f0198f689c0'
    old = original.decode('utf-8-sig'); draft = (HERE/'source_secondary.gd').read_text()
    qualified = (ROOT/'output/source-0x31-native-chains-20261115-attempt1/Studio/chain_solver.gd').read_bytes()
    assert sha(qualified) == '01635f84e05abe0ecc998b71117eed9c7afc6f5b15d04e8743cdf1c22efa362f'
    replacement = qualified.decode('utf-8-sig').replace('const Math = preload("res://leaf_candidate.gd")','const Math = preload("res://src/source_jiggle_math.gd")')
    assert replacement.encode() == (HERE/'source_chain_math.gd').read_bytes()
    assert qualified.replace(b'const Math = preload("res://leaf_candidate.gd")',b'const Math = preload("res://src/source_jiggle_math.gd")') == (HERE/'source_chain_math.gd').read_bytes()
    scalar_old = (ROOT/'output/source-0x31-native-chains-20261115-attempt1/Studio/leaf_candidate.gd').read_text()
    scalar_current = (ROOT/'src/source_jiggle_math.gd').read_text()
    without_comments = lambda value: '\n'.join(line for line in value.splitlines() if not line.lstrip().startswith('#'))
    assert without_comments(scalar_old) == without_comments(scalar_current)
    for start,end in [('static func offered(','static func anchors('),
                      ('static func vector64(','static func create('),
                      ('func binding_stamp(','func step(')]:
        if start == 'func binding_stamp(':
            assert block(old,start,end) == block(draft,start,'func configuration_stamp(')
        else:
            assert block(old,start,end) == block(draft,start,end)
    preamble_old = block(old,'func step(','\tvar id: String = chains[0].ids[0]')
    preamble_new = block(draft,'func step(','\tvar scale_token = actor.data.get("scale")')
    assert preamble_old == preamble_new
    # Reproduce the source generator entirely in memory: no output file writes.
    namespace = runpy.run_path(str(HERE/'build_draft.py'))
    generated = {}
    namespace['main'].__globals__['save'] = lambda name,value: generated.__setitem__(name,value)
    with contextlib.redirect_stdout(io.StringIO()): namespace['main']()
    for name in ('source_secondary.gd','source_chain_math.gd','PROVENANCE.json'):
        assert generated[name].encode() == (HERE/name).read_bytes(), name
    assert draft.count('_chain = _trial; _trial = previous; _tick += 1') == 1
    step = draft[draft.index('func step('):draft.index('func dispose()')]
    assert step.index('_trial.step(') < step.index('var q: Quaternion') < step.index('_chain = _trial;')
    assert 'configuration_stamp(_chain) != _configuration_stamp or configuration_stamp(_trial) != _configuration_stamp' in step
    assert step.index('configuration_stamp(_chain)') < step.index('var baseline := capture_baseline()')
    for field in ('_states = committed.states.duplicate(true)','_sizes = committed.sizes.duplicate(true)',
                  '_tick = int(committed.tick); _trial._active = true'):
        assert field in step
    assert 'committed,_tick' in step and 'state_error(_trial.snapshot(),_tick+1)' in step
    assert 'not forces.is_empty() and forces.size() != SELECTED_NATIVE_IDS.size()' in step
    assert 'not force is Vector3 or not force.is_finite() or force.length() > 1000000.0' in step
    assert 'float(scale_token) != _authored_scale_token' in step
    assert '"scale":_prefix_scale' in draft and '"scale":stable' in draft
    assert 'absf(float(observed_prefix.scale)-_prefix_scale) > EPS*_prefix_scale' in draft
    assert 'absf(float(actual.scale)-float(target.scale)) > EPS*float(target.scale)' in draft
    assert 'composed.origin.distance_to(actual.origin) > EPS*float(actual_frame.scale)' in draft
    assert 'origin.distance_to(Vector3(wanted[0],wanted[1],wanted[2])) > EPS*float(target.scale)' in draft
    assert 'static func goal(base: Array = [0.0,0.0,0.0], basis: Array =' in scalar_current
    assert 'const EPS := 0.00002' in draft
    assert 'const SELECTED_NATIVE_IDS := [8,17,18,26,27]' in draft
    assert 'candidate.chains.append({"ids":[binding.has_id]' in draft
    assert 'actor.live_pose.get(id,Model.identity()) if actor.live_pose is Dictionary else Model.identity()' in draft
    assert 'actor.live_pose != null' not in draft and 'actor.live_pose == null' not in draft
    assert 'not actor.live_pose is Dictionary and _skeleton.get_bone_pose(binding.skeleton_bone_index).origin != actor.bones[id].base.origin' in draft
    profile = json.loads((HERE/'PUBLIC_PROFILE.json').read_bytes())
    union = profile['influence_counts']['union']
    assert (union['vertices'],union['weighted_to_selected'],union['shared_with_other_bones'],union['unaffected']) == (9661,694,484,8967)
    assert union['descendant_closed_mask_sha256'] == '3f8abcb718ae1c7567750368ba8d2b5327d4da459b3724fb4feb35c183c34c1e'
    assert profile['selection_descendant_closed'] and profile['unselected_world_bones_expected_exact'] == 64
    assert profile['front8_overlap_with_either_pair_vertices'] == 0
    assert profile['actual_five_rule_motion_tested'] is False
    assert profile['masks_or_points_or_weights_or_rest_arrays_or_native_media_published'] is False
    dependencies = json.loads((HERE/'DEPENDENCIES.json').read_bytes())
    assert len(dependencies['files']) == 8 and dependencies['core_files_modified'] is False
    for row in dependencies['files']:
        source = ROOT/row['path']; raw = source.read_bytes()
        assert source.suffix == '.gd' and len(raw) == row['bytes'] and sha(raw) == row['sha256']
    forbidden = {'positions','normals','uvs','weights','rest','rests','rest_matrices','points','pcm','buffer','buffers','mask','geometry'}
    def privacy(value):
        if isinstance(value,dict):
            for key,child in value.items():
                assert key not in forbidden
                privacy(child)
        elif isinstance(value,list):
            for child in value: privacy(child)
        elif isinstance(value,str): assert len(value)<2048 and not value.startswith('data:')
        else: assert value is None or type(value) in (int,float,bool)
    for path in HERE.glob('*.json'): privacy(json.loads(path.read_bytes()))
    for path in HERE.glob('*.py'): ast.parse(path.read_text())
    if (HERE/'INDEX.json').exists():
        index = json.loads((HERE/'INDEX.json').read_bytes())
        expected = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json'}
        assert {row['path'] for row in index['files']} == expected
        assert len(index['files']) == index['files_count'] == len(expected)
        assert index['bytes'] == sum(row['bytes'] for row in index['files'])
        for row in index['files']:
            path = HERE/row['path']; raw = path.read_bytes()
            assert path.is_relative_to(HERE) and '..' not in Path(row['path']).parts
            assert not path.is_symlink() and path.suffix in {'.gd','.py','.json','.md','.patch'}
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
    print(json.dumps({'format':'has_native_five_draft_source_verification_1','passed':True,
                      'status':'DRAFT_NOT_APPLIED_GDSCRIPT_UNPARSED_UNRUN','qualified_core_only_preload_changed':True,
                      'd2_profile_boundary_context_binding_and_file_guards_exact':True,
                      'generator_reproduced_exactly_in_memory':True,'two_runner_single_commit_source_contract':True,
                      'five_rule_weight_union_measured':694,'unaffected_vertices':8967,'unselected_world_bones':64,
                      'source_math_runtime_or_product_pass_claimed':False,'core_or_frozen_files_modified':False},sort_keys=True))


if __name__ == '__main__':
    main()

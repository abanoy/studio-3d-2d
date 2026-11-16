"""Source/AST/count verification only. Never imports a launcher or runs Godot."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import runpy

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TESTS=HERE/'test_drafts'


def state_names(source):
    negatives=ast.literal_eval(re.search(r'const NEGATIVES := (\[.*?\])\nconst CREATE_REFUSALS',source,re.S).group(1))
    creates=ast.literal_eval(re.search(r'const CREATE_REFUSALS := (\[[^\n]+\])',source).group(1))
    section=source[source.index('func planned_names()'):]
    names=ast.literal_eval(re.search(r'var names: Array = (\[.*?\])\n\tfor name in ',section,re.S).group(1))
    loads=ast.literal_eval(re.search(r'for name in \["a","b","c"\]:\n\t\tfor suffix in (\[[^\n]+\])',section).group(1))
    for actor in ('a','b','c'):
        names.extend('load.'+actor+'.'+suffix for suffix in loads)
    for name in negatives:
        names.extend('negative.'+name+'.'+suffix for suffix in ('seeded','refused','state_atomic','keys_report_unchanged','restored'))
        if name in creates:names.append('negative.'+name+'.create_refused')
    for name in ('header','length','mtime'):
        names.extend('file.'+name+'.'+suffix for suffix in ('isolated_observation','refused','state_atomic','keys_report_unchanged','restored'))
        if name!='mtime':names.append('file.'+name+'.create_refused')
    if 'func direct_null_checks()' in source:
        names.extend('baseline.direct_nonzero_null_'+suffix for suffix in ('refused','atomic','pose_exact'))
        for name in ('half','one','two'):
            names.extend('rotation.'+name+'.'+suffix for suffix in ('fixed_ticks','sizes_exact','authored_preserved','Off_exact'))
    if 'const WRAPPER_INVENTORY_CASES' in source:
        cases=ast.literal_eval(re.search(r'const WRAPPER_INVENTORY_CASES := (\[[^\n]+\])',source).group(1))
        for name in cases:names.extend('wrapper_inventory.'+name+'.'+suffix for suffix in ('refused','atomic','visual_exact','restored'))
    assert len(names)==len(set(names))
    return sorted(names),negatives,creates


def ui_names(source,mode,export=False):
    tree=ast.parse(source)
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='names')
    isolated=ast.Module(body=[function],type_ignores=[])
    namespace={'__builtins__':{}}
    exec(compile(isolated,'source-only-names-contract','exec'),namespace)
    names=namespace['names'](mode,export)
    assert len(names)==len(set(names))
    return sorted(names)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-contract',action='store_true');args=parser.parse_args()
    state=(TESTS/'source_native_five_state_unit.gd').read_text()
    ui=(TESTS/'source_native_five_live_ui.gd').read_text()
    driver=(TESTS/'verify_source_native_five_live.py').read_text()
    oldstate=(ROOT/'tests/source_native_state_unit.gd').read_text()
    oldui=(ROOT/'tests/source_native_live_ui.gd').read_text()
    olddriver=(ROOT/'tests/verify_source_native_live.py').read_text()
    producer=runpy.run_path(str(HERE/'prepare_test_successors.py'))
    assert producer['state_successor'](oldstate)==state
    expected_ui,expected_driver=producer['ui_successors'](oldui,olddriver)
    assert expected_ui==ui and expected_driver==driver
    oldnames,oldnegatives,oldcreates=state_names(oldstate)
    names,negatives,creates=state_names(state)
    assert len(oldnames)==180 and len(names)==266
    assert set(name.replace('wrapper.68_unselected','wrapper.64_unselected') for name in oldnames)<=set(names)
    assert len(negatives)==32 and set(oldnegatives)<=set(negatives) and creates==oldcreates
    state_driver=(TESTS/'run_five_state_owned.py').read_text()
    state_driver_ast=ast.parse(state_driver)
    driver_constants={}
    for node in state_driver_ast.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id in {'SCRIPT_SHA','SCRIPT','EXPECTED_NAMES'}:driver_constants[target.id]=ast.literal_eval(node.value)
    assert driver_constants['SCRIPT']=='tests/source_native_five_state_unit.gd'
    assert driver_constants['SCRIPT_SHA']==hashlib.sha256(state.encode()).hexdigest()
    assert driver_constants['EXPECTED_NAMES']==names
    assert "actual.get('checks') == 266" in state_driver and "len(actual.get('named_checks', {})) == 266" in state_driver
    for legacy in ('"chain_id": runner.chains[0].ids[0] = other',
                   '"cached_index": runner.resolution.bindings[8].skeleton_bone_index = actor.bones[other].index',
                   '"cached_parent": runner.resolution.by_native[7] = other'):
        assert legacy in state
    assert '_chain.snapshot()' in state and '_chain_inventory_stamp' in state
    assert 'runner._state' not in state and 'runner._state' not in ui
    assert 'force_slot_' in state and 'forces[int(kind.get_slice("_",2))] = Vector3(NAN' in state
    assert 'fresh_rest_null' in state and 'fresh_partial_dictionary' in state and 'direct_nonzero_null_refused' in state
    assert '{"name":"half","scale":0.5}' in state and 'sizes_exact' in state
    assert 'func wrapper_inventory_case(' in state and 'model_bytes(actor)==visual' in state
    assert '"binding_shape":sim.runner.chains[0].source.joints[0].binding=[]' in state
    assert '"advance_mean_usec"' in state and '"advance_max_usec"' in state
    assert ui_names(olddriver,'reader')==ui_names(driver,'reader')
    assert ui_names(olddriver,'reader',True)==ui_names(driver,'reader',True)
    writer=ui_names(driver,'writer');oldwriter=ui_names(olddriver,'writer')
    assert len(oldwriter)==77 and len(writer)==82
    assert set(name.replace('authored_and_68_bones','authored_and_64_bones') for name in oldwriter)<=set(writer)
    assert len(ui_names(driver,'reader',True))==11 and len(ui_names(driver,'reader'))==8
    for retained in ('"body.partial_rig_refuses_ragdoll"','"body.independent_primary_started"',
                     '"record.escape_preserves_authored"','"record.undo_exact"','"record.redo_exact"',
                     '"cold.export_frame_"+str(frame)','"generic.existing_backend"'):
        assert retained in ui
    assert 'captured.affected==694 and captured.shared==484 and captured.unaffected==8967' in ui
    assert 'var original_front: Dictionary={}' in ui and 'if index==8:original_front=difference' in ui
    assert 'metrics.speed50.affected_max_vs_disabled>.001 and profile.speed50.span>.00005' in ui
    assert 'error <= .00002*float(runner._size_tokens[id])' in ui
    assert 'gate.maximum_tip_error<=.00002*gate.world_scale' in ui
    assert '"native_step_processing"' in ui and 'simulation.runner.processing_max_usec' in ui
    assert '"last60_tick_span":span,"span_duration_seconds":0.5' in ui
    assert 'Native.offered(actor()) and var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))==aim_rig_before' in ui
    for name in ('fresh_native5_on','fresh_native5_identity_fallback','fresh_native5_off_exact','partial_native5_on_off','keyed_root_rotation_constant_scale'):
        assert '"import.'+name+'"' in ui
    for path in list(HERE.glob('*.py'))+list(TESTS.glob('*.py')):ast.parse(path.read_text())
    capture=(TESTS/'source_native_five_capture.gd').read_bytes()
    assert hashlib.sha256(capture).hexdigest()=='b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'
    contract={'format':'has_native_five_v2_proposed_test_contract_1','status':'SOURCE_ONLY_GDSCRIPT_UNPARSED_UNRUN',
              'state_names':names,'state_proposed_checks':266,'state_negative_contexts':32,'wrapper_inventory_contexts':5,
              'legacy_state180_names_retained_with64_world_bone_generalization':True,
              'writer_names':writer,'writer_proposed_checks':82,
              'cold_packed_names':ui_names(driver,'reader',True),'cold_packed_proposed_checks':11,
              'cold_linked_names':ui_names(driver,'reader'),'cold_linked_proposed_checks':8,
              'legacy_GUI77_writer_predicates_retained_with5_rule_generalization':True,
              'successful_native_steps_if_file_cases_first_attempt':886,
              'retry_steps_policy':'Count observed native steps, including warm steps on any file-isolation retries; do not force886 if retries occur.',
              'processing_mean_max_reported_metrics_only_no_FPS_gate':True,
              'runtime_or_GDScript_parse_or_Git_executed':False,'actual_pass_claimed':False}
    if args.prepare_contract:
        path=HERE/'PROPOSED_TEST_CONTRACT.json'
        if path.exists():assert path.read_bytes()==(HERE/'source_history/PROPOSED_TEST_CONTRACT_246.json').read_bytes()
        with path.open('w' if path.exists() else 'x',encoding='utf-8',newline='\n') as stream:
            json.dump(contract,stream,indent=2);stream.write('\n')
    else:
        assert json.loads((HERE/'PROPOSED_TEST_CONTRACT.json').read_bytes())==contract
    print(json.dumps({'passed_source_checks':True,'state_proposed_checks':266,'state_negative_contexts':32,'wrapper_inventory_contexts':5,
                      'writer_proposed_checks':82,'cold_packed_proposed_checks':11,'cold_linked_proposed_checks':8,
                      'all_legacy_assertion_names_retained_with_explicit_generalization':True,
                      'actual_runtime_or_parse_pass':False}))


if __name__=='__main__':main()

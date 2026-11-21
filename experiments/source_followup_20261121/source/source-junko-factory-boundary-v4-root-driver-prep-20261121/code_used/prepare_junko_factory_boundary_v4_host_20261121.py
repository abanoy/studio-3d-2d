"""Author the next read-only boundary-measurement Root host; no runtime/GPU/Main."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-stage-a-rest-diagnostic-v3c-root-driver-prep-20261121'
C=R/'output/source-junko-factory-boundary-diagnostic-prep-20261121'
D=R/'output/source-junko-factory-boundary-v4-root-driver-prep-20261121'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert pin((S/'SOURCE_PINS.json').read_bytes())['sha256']=='ae92f83c942de6d480190b8197bc541fd8ef8004e33af54292291affd8a2be03'
assert pin((C/'SOURCE_PINS.json').read_bytes())['sha256']=='5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974'
assert not D.exists();D.mkdir()
for p in S.rglob('*'):
 if p.is_file():
  dest=D/'bases/v3c'/p.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
for name in ('root_native_job.py','approved_job_layout.py','BASELINE_SOURCE1109.json'):(D/name).write_bytes((S/name).read_bytes())
for name in ('SOURCE_PINS.json','ROOT_PROTOCOL.md','CHECK_PLAN.json'):(D/('CANDIDATE_'+name)).write_bytes((C/name).read_bytes())
worker=(S/'gated_converter_worker.py').read_text().replace('unit25','unit45').replace('test_junko_part*.py','test_junko*.py')
old="scripts=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py')"
new="scripts=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py','tests/test_junko_factory_boundary.py')"
assert worker.count(old)==1;worker=worker.replace(old,new);ast.parse(worker)
(D/'gated_converter_worker.py').write_text(worker,encoding='utf-8')
source=(S/'run_stage_a.py').read_text()
source=source.replace('source-junko-body-dress-rest-diagnostic-prep-20261121','source-junko-factory-boundary-diagnostic-prep-20261121').replace('8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3','5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974')
source=source.replace("closure['file_count']==116 and len(closure['files'])==116,'TOOLS116_CLOSURE'","closure['file_count']==118 and len(closure['files'])==118,'TOOLS118_CLOSURE'")
source=source.replace('has_junko_body_rest_diagnostic_v3_1','has_junko_factory_boundary_diagnostic_v4_1').replace('has-junko-native-rest-diagnostic-v3-','has-junko-factory-boundary-diagnostic-v4-').replace('junko-native-rest-diagnostic-v3.lock','junko-factory-boundary-diagnostic-v4.lock')
source=source.replace('unit25','unit45').replace('test_junko_part*.py','test_junko*.py').replace('PURE25_EXACT','PURE45_EXACT').replace('Ran 25 tests?','Ran 45 tests?').replace("==25 and not re.search", "==45 and not re.search").replace("result['checks']=25","result['checks']=45")
old="tests=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py')"
new="tests=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py','tests/test_junko_factory_boundary.py')"
assert source.count(old)==1;source=source.replace(old,new)
old="'mathutils_vs_native_local_error','native_quaternion_unit_error'}"
new="'mathutils_vs_native_local_error','native_quaternion_unit_error','factory_assignment_to_edit_error','factory_edit_later_error','factory_edit_to_object_error','factory_object_to_final_error','factory_return_pose_error','factory_assignment_to_reference_error','factory_before_length','factory_after_length'}"
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("type(index)is int and 0<=index<145,'NATIVE_INDEX'","type(index)is int and index==38,'EXACT_PREVIOUS_REFUSAL_INDEX38'")
anchor="    need(recomputed==scalar,'EXACT_SCALAR_RECALCULATION')\n"
assert source.count(anchor)==1
supplement='''    boundary=private.get('factory_boundaries')
    need(type(boundary)is dict and boundary.get('format')=='has_private_factory_boundaries_1' and boundary.get('private_do_not_publish') is True and type(boundary.get('native_index'))is int and boundary['native_index']==38,'EXACT_PRIVATE_FACTORY_BOUNDARY_PROFILE')
    need(type(boundary.get('actual_load_refpose'))is bool and type(boundary.get('actual_refpose_branch_entered'))is bool and (not boundary['actual_refpose_branch_entered'] or boundary['actual_load_refpose']),'PRIVATE_ACTUAL_REFPOSE_FLAGS')
    need(type(boundary.get('factory_calls'))is int and boundary['factory_calls']==1 and type(boundary.get('assignments'))is int and boundary['assignments']==1 and boundary.get('readonly_trace') is True and boundary.get('tolerance_changed') is False and boundary.get('cause_established') is False,'EXACT_READONLY_TRACE_COUNTS')
    def finite_matrix(value):
        need(type(value)is list and len(value)==16 and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=1e9 for x in value),'FINITE_BOUNDARY_MATRIX');return value
    snapshots={}
    for key in ('before_assignment','immediate_edit_getter','before_object_conversion'):
        row=boundary.get(key);need(type(row)is dict and set(row)=={'matrix','head','tail','roll','length'},'EXACT_EDIT_BONE_SNAPSHOT')
        finite_matrix(row['matrix'])
        for field in ('head','tail'):need(type(row[field])is list and len(row[field])==3 and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=1e9 for x in row[field]),'FINITE_PRIVATE_EDIT_ENDPOINTS')
        need(type(row['roll']) in (int,float) and math.isfinite(row['roll']) and type(row['length']) in (int,float) and math.isfinite(row['length']) and row['length']>=0,'FINITE_PRIVATE_EDIT_ROLL_LENGTH');snapshots[key]=row
    assigned=finite_matrix(boundary.get('assigned_matrix'));returned=finite_matrix(boundary.get('object_return_matrix'));pose=finite_matrix(boundary.get('object_return_pose'))
    extra={'factory_assignment_to_edit_error':maximum(assigned,snapshots['immediate_edit_getter']['matrix']),'factory_edit_later_error':maximum(snapshots['immediate_edit_getter']['matrix'],snapshots['before_object_conversion']['matrix']),'factory_edit_to_object_error':maximum(snapshots['before_object_conversion']['matrix'],returned),'factory_object_to_final_error':maximum(returned,actual),'factory_return_pose_error':maximum(pose,returned),'factory_assignment_to_reference_error':maximum(assigned,expected),'factory_before_length':snapshots['before_assignment']['length'],'factory_after_length':snapshots['immediate_edit_getter']['length']}
    need(type(boundary.get('scalar_errors'))is dict and set(boundary['scalar_errors'])==set(extra) and boundary['scalar_errors']==extra,'PRIVATE_BOUNDARY_SCALAR_RECALCULATION')
    recomputed.update(extra)
    need(recomputed==scalar,'EXACT_ALL18_SCALAR_RECALCULATION')
'''
source=source.replace(anchor,supplement)
source=source.replace("'diagnosed_cause_claimed':False,'reference_pose_or_later_factory_writes_ruled_out':False","'diagnosed_cause_claimed':False,'five_factory_boundaries_recorded':True,'private_refpose_flags_recorded':True,'reference_pose_or_later_factory_writes_ruled_out':False")
assert 'Ran 25 tests?' not in source and "result['checks']=25" not in source
ast.parse(source);(D/'run_stage_a.py').write_text(source,encoding='utf-8')
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'README.md').write_text('''# Root-only v4 read-only factory boundary diagnostic

UNRUN source successor. Original StageA FAIL16 and successful expected-refusal25
diagnostic remain unchanged. This binds source candidate5a07872e,118 runtime files
and the same exact Main2f1/1109 baseline23ea7f. It runs two contained Root Jobs:
45 pure controls (16+9+20, three explicitly pinned testfiles via unittest pattern
test_junko*.py), then one Body-only720s background converter expectedexit1. Dress
is never started, noGLB/exportbinding is accepted and allmodel/Godot/54/follow/
simulation/Full success flags remain false. No tolerance/predicate/model changes.

Root must use pinnedPython -I -S -B run_stage_a.py --self-sha256 <driverSHA>
--source-manifest-sha256 <thisSOURCE_PINSSHA> --revision <exact2f1publishedHEAD>
--root-cpu-component-confirmed after source peer. Existing RootJob16process4GiB
gatedSTART/retainedPID+birth/handleclosure/active0beforeadvance is unchanged.

The prior exact original rest-refusal/oneDIAG marker/privateMDLword checks and
compiled pinned unchanged close()==false remain. New private typed snapshots
separate preassignment/intended/immediate EditBone getter/preOBJECT/OBJECTreturn/
finalproof, with actualrefpose flags. Every18 public scalar is independently
recomputed from private matrices and measurements; full matrix/native data remain
private. Any missing stage/different original refusal/capturefailure/othererror,
unexpected success, unproven lifecycle or preservation fails the diagnostic.
The observation's cause_established remains false. Trace does no assignment/mode
switch; the original setter/factory/proof run exactly as before.

All original99,SDK574,installedexporter120/executable/Main1109 and fullnative64
before/after guards, owned114→118tools/SDK/native/referencecopies, isolateduserenv,
rawloghashing and strict source membership remain from reviewed v3c. Public only
counts/hashes/closure/scalars. No private names/matrices/words/pointers or assets
are uploaded. No runtime/Blender/GPU/Main/app/Full execution by this author.
''',encoding='utf-8')
(D/'CHECK_PLAN.json').write_text(json.dumps({'format':'has_junko_factory_boundary_v4_root_plan_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','pure_checks':45,'pure_composition':[16,9,20],'old25_included_not_additional':True,'runtime_sources':118,'Root_jobs':2,'body_native_expected_exit':1,'private_factory_snapshot_boundaries':5,'additional_public_scalars':8,'total_public_scalars':18,'source_candidate_sha256':'5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974','dress_started':False,'qualified_conversions':0,'unchanged_rest_tolerance':True,'Main_or_app_or_source_tools_modified':False,'cause_claimed':False},indent=2)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and p!=D/'SOURCE_PINS.json']
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_factory_boundary_v4_root_source_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':files},indent=2)+'\n',encoding='utf-8')
assert set(row['path'] for row in files)|{'SOURCE_PINS.json'}=={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
for row in files:assert pin((D/row['path']).read_bytes())=={'bytes':row['bytes'],'sha256':row['sha256']}
print(json.dumps({'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin((D/'run_stage_a.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'AST_changed_sources_only':2,'CPU_exact_source_closure':'PASS'},indent=2))

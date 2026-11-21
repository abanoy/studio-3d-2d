"""Versioned source-only Body expected-refusal host; no engine/Main operations."""
from pathlib import Path
import hashlib,json,ast,shutil
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-stage-a-root-driver-v2-prep-20261121'
C=R/'output/source-junko-body-dress-rest-diagnostic-prep-20261121'
D=R/'output/source-junko-stage-a-rest-diagnostic-v3-root-driver-prep-20261121'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(raw):return {'bytes':len(raw),'sha256':sha(raw)}
assert sha((S/'SOURCE_PINS.json').read_bytes())=='d4ab53c3fa5e747e9a59de8a162e867742ff97904b0628eca410146d2f0a3e5c'
assert sha((C/'SOURCE_PINS.json').read_bytes())=='8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3'
assert not D.exists();D.mkdir()
for path in S.rglob('*'):
 if path.is_file():
  dest=D/'bases/v2'/path.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
for name in ('root_native_job.py','approved_job_layout.py','BASELINE_SOURCE1109.json'):(D/name).write_bytes((S/name).read_bytes())
for name in ('SOURCE_PINS.json','ROOT_PROTOCOL.md','DIAGNOSTIC_PLAN.json'):(D/('CANDIDATE_'+name)).write_bytes((C/name).read_bytes())
worker=(S/'gated_converter_worker.py').read_text()
worker=worker.replace("job['name'] in ('unit16','body','dress')","job['name'] in ('unit25','body')")
start=worker.index("    expected=studio/('tests/test_junko_part_probe.py'")
end=worker.index("    receipt={'format':",start)
worker=worker[:start]+'''    need(job['cwd']==str(studio),'EXACT_OWNED_CWD')
    if job['name']=='unit25':
        need(cmd[4:]==['-m','unittest','discover','-s',str(studio/'tests'),'-p','test_junko_part*.py','-v'] and job['timeout_seconds']==90,'EXACT_UNIT25_DISCOVERY')
        expected_exit=0
        scripts=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py')
    else:
        need(cmd[4]==str(studio/'tools/prepare_junko_part_probe.py') and job['timeout_seconds']==720,'EXACT_BODY_DIAGNOSTIC_PREPARER')
        expected_exit=1
        scripts=('tools/prepare_junko_part_probe.py',)
    need(type(job.get('expected_child_exit'))is int and job['expected_child_exit']==expected_exit,'EXACT_EXPECTED_EXIT_SCOPE')
    exe=regular(pin['path'],512*1024*1024);need(len(exe)==pin['bytes'] and sha(exe)==pin['sha256'],'PYTHON_EXE_PIN')
    need(set(job['script_pins'])==set(scripts),'EXACT_SCRIPT_PIN_MEMBERSHIP')
    script_bytes={}
    for name in scripts:
        script=regular(studio/name,1024*1024);expected=job['script_pins'][name]
        need(len(script)==expected['bytes'] and sha(script)==expected['sha256'],'OWNED_SCRIPT_PIN');script_bytes[name]=script
''' +worker[end:]
worker=worker.replace("'child_handle_closed':False}","'child_handle_closed':False,'expected_child_exit':expected_exit}")
worker=worker.replace("regular(a.request)==raw and regular(expected,1024*1024)==script","regular(a.request)==raw and all(regular(studio/name,1024*1024)==b for name,b in script_bytes.items())")
worker=worker.replace("need(receipt['child_exit']==0,'CHILD_NONZERO');receipt['status']='PASS'","need(receipt['child_exit']==expected_exit,'CHILD_UNEXPECTED_EXIT');receipt['status']='EXPECTED_CHILD_REFUSAL' if expected_exit==1 else 'PASS'")
worker=worker.replace("receipt['status']=='PASS' else 1","receipt['status'] in ('PASS','EXPECTED_CHILD_REFUSAL') else 1")
assert "('unit16','body','dress')" not in worker and "regular(expected," not in worker
(D/'gated_converter_worker.py').write_text(worker,encoding='utf-8');ast.parse(worker)
source=(S/'run_stage_a.py').read_text()
source=source.replace('import argparse,hashlib,json,os,re,stat,struct,subprocess,sys,time,types,uuid','import argparse,ast,hashlib,json,math,os,re,stat,struct,subprocess,sys,time,types,uuid')
source=source.replace('source-junko-body-dress-native-binding-prep-20261121','source-junko-body-dress-rest-diagnostic-prep-20261121').replace('9989f3f2746e37666dc541ef44990a71d757f4d4d7eaa035e0525a81eb357913','8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3')
source=source.replace("closure['file_count']==114 and len(closure['files'])==114,'TOOLS114_CLOSURE'","closure['file_count']==116 and len(closure['files'])==116,'TOOLS116_CLOSURE'")
source=source.replace("'has_junko_body_dress_stage_a_1'","'has_junko_body_rest_diagnostic_v3_1'").replace('has-junko-native-stage-a-','has-junko-native-rest-diagnostic-v3-').replace('junko-native-stage-a.lock','junko-native-rest-diagnostic-v3.lock')
source=source.replace("'conversions':{},'graphics_executed'","'conversions':{},'diagnostic':{},'dress_started':False,'graphics_executed'")
source=source.replace("proof.get('status')=='PASS' and proof.get('request_sha256')","proof.get('status')==('EXPECTED_CHILD_REFUSAL' if job['expected_child_exit']==1 else 'PASS') and proof.get('request_sha256')")
source=source.replace("type(proof.get('child_exit'))is int and proof['child_exit']==0","type(proof.get('child_exit'))is int and proof['child_exit']==job['expected_child_exit'] and proof.get('expected_child_exit')==job['expected_child_exit']")
source=source.replace("row.update(status='PASS',worker_receipt_sha256","row.update(status='EXPECTED_CHILD_REFUSAL' if job['expected_child_exit']==1 else 'PASS',worker_receipt_sha256")
start=source.index('def conversion_result(');end=source.index('def main():',start)
diagnostic='''def diagnostic_result(G,stage,facts):
    folder=stage/'Bundles/body';status=parse(G.read(stage/'body-status.json'))
    need(status.get('ok') is False and 'Conversion failed' in str(status.get('error','')),'EXPECTED_ORDINARY_REFUSAL_STATUS')
    need(not (folder/'scene.glb').exists() and not (folder/'PRIVATE_part_export_binding.json').exists(),'NO_EXPORT_OR_BINDING_ACCEPTED')
    raw=G.read(folder/'PRIVATE_first_rest_refusal.json',65536);private=parse(raw)
    need(private.get('format')=='has_private_first_native_rest_refusal_1' and private.get('private_do_not_publish') is True and private.get('native_mdl_sha256')==facts['sha256'] and private.get('original_error_code')=='native_Blender_rest_matrix_mismatch','EXACT_FIRST_REFUSAL_PROFILE')
    need(private.get('diagnostic_reads_only') is True and all(private.get(k) is False for k in ('rest_tolerance_changed','model_repaired','export_binding_qualified','native_runtime_binding_qualified')),'NO_REPAIR_OR_PROMOTION')
    index=private.get('native_index');need(type(index)is int and 0<=index<145,'NATIVE_INDEX')
    scalar=private.get('scalar_errors');need(type(scalar)is dict and set(scalar)=={'first_native_index','global_max_error','global_translation_error','global_basis_error','global_normalized_error','parent_global_error','current_parent_native_local_error','current_parent_mathutils_local_error','mathutils_vs_native_local_error','native_quaternion_unit_error'},'EXACT_PUBLIC_SCALAR_FIELDS')
    need(type(scalar['first_native_index'])is int and scalar['first_native_index']==index and all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in scalar.values()),'FINITE_TYPED_SCALARS')
    vectors={}
    for key in ('actual_global_rest','independent_native_global_rest','actual_parent_global_rest','independent_parent_global_rest','independent_native_local_rest','current_parent_times_native_local','mathutils_local_rest','current_parent_times_mathutils_local','actual_pose_matrix'):
        value=private.get(key);need(type(value)is list and len(value)==16 and all(type(v) in (int,float) and math.isfinite(v) and abs(v)<=1e9 for v in value),'FINITE_PRIVATE_MATRIX');vectors[key]=value
    # Compile ONLY the exact existing pinned close() AST; no module/native hooks.
    helper=G.read(stage/'Studio/tools/source_jiggle_crosswalk.py');nodes=[n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef) and n.name=='close'];need(len(nodes)==1,'PINNED_CLOSE_FUNCTION')
    namespace={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned-source-close-only','exec'),namespace)
    need(namespace['close'](vectors['actual_global_rest'],vectors['independent_native_global_rest']) is False,'ORIGINAL_REST_REFUSAL_MUST_REMAIN_FALSE')
    mdl=G.read(stage/'NativeJunko'/rel(facts['source_relative']));need(sha(mdl)==facts['sha256'] and mdl[:4]==b'IDST' and struct.unpack_from('<i',mdl,4)[0]==49,'EXACT_NATIVE_MDL49')
    count,base=struct.unpack_from('<II',mdl,156);need(count==145 and base>=408 and base+count*216<=len(mdl),'NATIVE_TABLE')
    at=base+index*216;name_offset,parent=struct.unpack_from('<ii',mdl,at);values=struct.unpack_from('<7f',mdl,at+32);words=struct.unpack_from('<7I',mdl,at+32)
    name_at=at+name_offset;end=mdl.find(b'\\0',name_at,min(len(mdl),name_at+63));need(base+count*216<=name_at<end<len(mdl),'NATIVE_NAME_DOMAIN')
    need(private.get('native_name')==mdl[name_at:end].decode('ascii') and private.get('native_parent_index')==parent and private.get('native_rest_words_uint32')==list(words),'FIRST_NATIVE_ROW_IDENTITY')
    position=private.get('native_position');quat=private.get('native_quaternion')
    need(type(position)is list and len(position)==3 and type(quat)is list and len(quat)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in position+quat),'NATIVE_ROW_NUMBERS')
    need(struct.pack('<7f',*position,*quat)==struct.pack('<7I',*words),'EXACT_NATIVE_REST_WORDS')
    for key in ('actual_data_bone_pointer','actual_pose_bone_pointer','actual_armature_pointer'):need(type(private.get(key))is int and private[key]>0,'OBSERVED_POINTERS_PRIVATE')
    def maximum(a,b,indices=range(16)):return max(abs(a[i]-b[i]) for i in indices)
    actual=vectors['actual_global_rest'];expected=vectors['independent_native_global_rest']
    recomputed={'first_native_index':index,'global_max_error':maximum(actual,expected),'global_translation_error':maximum(actual,expected,(3,7,11)),'global_basis_error':maximum(actual,expected,(0,1,2,4,5,6,8,9,10)),'global_normalized_error':max(abs(a-b)/max(1.,abs(b)) for a,b in zip(actual,expected)),'parent_global_error':maximum(vectors['actual_parent_global_rest'],vectors['independent_parent_global_rest']),'current_parent_native_local_error':maximum(actual,vectors['current_parent_times_native_local']),'current_parent_mathutils_local_error':maximum(actual,vectors['current_parent_times_mathutils_local']),'mathutils_vs_native_local_error':maximum(vectors['mathutils_local_rest'],vectors['independent_native_local_rest']),'native_quaternion_unit_error':abs(math.sqrt(sum(v*v for v in quat))-1.)}
    need(recomputed==scalar,'EXACT_SCALAR_RECALCULATION')
    log=G.read(folder/'conversion.log',64*1024*1024).decode('utf-8','replace');prefix='JUNKO_PART_REST_DIAGNOSTIC '
    markers=[parse(line[len(prefix):]) for line in log.splitlines() if line.startswith(prefix)]
    need(len(markers)==1 and markers[0]==scalar and 'JUNKO_PART_REST_DIAGNOSTIC_CAPTURE_FAILED' not in log,'ONE_COMPLETE_DIAGNOSTIC')
    need(log.count('Traceback (most recent call last):')==1 and 'source_jiggle_crosswalk.CrosswalkError: native_Blender_rest_matrix_mismatch' in log and 'JUNKO_PART_EXPORT_IDENTITY ' not in log,'UNCHANGED_ORIGINAL_NATIVE_REFUSAL')
    return {'status':'EXPECTED_REFUSAL_WITH_DIAGNOSTIC','scalar_errors':scalar,'private_diagnostic_sha256':sha(raw),'conversion_log_sha256':sha(log.encode('utf-8')),'original_close_predicate_still_false':True,'source_rest_tolerance_changed':False,'diagnosed_cause_claimed':False,'reference_pose_or_later_factory_writes_ruled_out':False,'export_binding_qualified':False,'Godot_binding_qualified':False,'native_simulation_qualified':False}
'''
source=source[:start]+diagnostic+source[end:]
start=source.index('        def job(name,cmd,timeout,script):');end=source.index('\n    except BaseException as e:primary=e;',start)
source=source[:start]+'''        def job(name,cmd,timeout,scripts,expected_exit):return {'name':name,'command':cmd,'studio':str(studio),'cwd':str(studio),'timeout_seconds':timeout,'environment_overrides':profile_env(stage/'Profiles'/name),'expected_child_exit':expected_exit,'script_pins':{s:{'bytes':len(runtime[s]),'sha256':sha(runtime[s])} for s in scripts}}
        tests=('tests/test_junko_part_probe.py','tests/test_junko_part_rest_diagnostic.py')
        unit=job('unit25',[python['path'],'-I','-S','-B','-m','unittest','discover','-s',str(studio/'tests'),'-p','test_junko_part*.py','-v'],90,tests,0);record=run_job(G,J,L,stage,unit,python,result)
        text=(G.read(record/'child-stdout.log')+G.read(record/'child-stderr.log')).decode('utf-8','replace').replace('\\r\\n','\\n')
        need(re.search(r'Ran 25 tests? in [0-9.]+s\\s+OK\\s*$',text) is not None and len(re.findall(r'^test_.* \\.\\.\\. ok$',text,re.M))==25 and not re.search(r'FAILED|ERROR|Traceback',text),'PURE25_EXACT');result['checks']=25
        model=next(row for row in facts['models'] if row['role']=='body');source=stage/'NativeJunko'/rel(model['source_relative']);need(sha(G.read(source))==model['sha256'],'SELECTED_OWNED_BODY')
        target=stage/'Bundles/body';need(not target.exists(),'FRESH_DIAGNOSTIC_OUTPUT');target.parent.mkdir(exist_ok=True)
        cmd=[python['path'],'-I','-S','-B',str(studio/'tools/prepare_junko_part_probe.py'),str(source),'--output',str(target),'--sourceio',str(stage/'SourceIO'),'--blender',executables['blender']['path'],'--gmod',str(stage/'AbsentGame'),'--workshop',str(stage/'AbsentWorkshop'),'--mount-plan',str(mount),'--scale','0.01905','--status-file',str(stage/'body-status.json'),'--cancel-file',str(stage/'body-cancel')]
        spec=job('body',cmd,720,('tools/prepare_junko_part_probe.py',),1);spec['conversion_log']=str(target/'conversion.log');run_job(G,J,L,stage,spec,python,result)
        result['diagnostic']=diagnostic_result(G,stage,model)
        need(len(result['jobs'])==2 and set(result['jobs'])=={'unit25','body'} and result['conversions']=={} and result['dress_started'] is False,'ONLY_BODY_DIAGNOSTIC_COMPLETE')
        result['status']='EXPECTED_REFUSAL_WITH_DIAGNOSTIC'
''' +source[end:]
source=source.replace("result['status']=='PASS' else 1","result['status']=='EXPECTED_REFUSAL_WITH_DIAGNOSTIC' else 1")
source=source.replace("'conversion_count':len(result['conversions'])","'conversion_count':0,'diagnostic_captured':bool(result['diagnostic'])")
assert 'def conversion_result' not in source and 'PURE16_EXACT' not in source and 'conversion_result(G' not in source
ast.parse(source);(D/'run_stage_a.py').write_text(source,encoding='utf-8')
(D/'code_used').mkdir();shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'README.md').write_text('''# Root-only v3 first Body rest-refusal diagnostic

Source-only UNRUN. Original native StageA actualFAIL16 and all v1/v2 sources remain
unchanged. This explicit successor binds candidate8807fe,116 runtime sources and the
same1109 baseline23ea7f at Root's exact published revision. It does not waive any
failed Full or modify Main/SourceIO/exporter/model/rest tolerance.

Run existing pinned Python -I -S -B run_stage_a.py --self-sha256 <driverSHA>
--source-manifest-sha256 <thisSOURCE_PINSSHA> --revision <actualMain1109HEAD>
--root-cpu-component-confirmed. Root must source-review before execution.

Two Jobs only:25 pure16+9 guards via exact unittest discovery, then one Body-only
720-second background converter expected to exit1 with the original native rest
refusal. Worker status EXPECTED_CHILD_REFUSAL means only a retained exit, never a
successful conversion. Root additionally requires exactly one scalar marker and
one private sidecar, the original named traceback and unchanged close()==false,
exact MDL native row/words plus finite private matrices and independently recomputed
scalar errors. Unexpected success, missing/capture-failed/different diagnostics or
any process/input preservation failure remains FAIL. Dress is never started and no
scene.glb/export crosswalk is accepted; converted/native54/Godot/simulation claims
remain false. Refpose/later factory writes remain an explicit possible branch.

RootJob16process4GiB/gate-before-start/retained-handle/active0/no-breakaway and all
original/copy SDK574/exporter120/native99/executable/currentMain1109/native64/nsmtime
guards remain from reviewed v2. Public result contains only scalar measurements,
metadata hashes and closure flags. Matrices,names,words,pointers,logs,private identity
maps,NativeJunko assets,SDK/ExporterReference and all generated native data staylocal.
No runtime/GPU was executed by the author. This is measurement of an expected
refusal, not a repair, root-cause conclusion, successful native conversion or Full.
''',encoding='utf-8')
plan={'format':'has_junko_body_expected_refusal_v3_check_plan_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','pure_checks':25,'retained_pure_checks':16,'new_pure_checks':9,'Root_jobs':2,'native_body_diagnostic_jobs':1,'native_expected_exit':1,'qualified_conversions':0,'dress_started':False,'runtime_sources':116,'baseline_main_sources':1109,'candidate_source_pins_sha256':'8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3','old_actual_FAIL16_preserved':True,'no_rest_tolerance_or_product_changes':True}
(D/'CHECK_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file()]
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_stage_a_body_refusal_v3_driver_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin((D/'run_stage_a.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'AST_changed_sources_only_pass':2},indent=2))

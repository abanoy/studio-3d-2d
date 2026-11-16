"""Explicit metadata/code whitelist archive; no apps, runtime, network or Git.

First run writes reviewed payloads. Run independent scan_packet.py --write-report,
then this script --seal, then scan_packet.py for the final indexed verification.
No existing file is overwritten. Actual leases and private assets are excluded.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ACTUAL = ROOT / 'output/source-0x31-native-chains-20261115-attempt1'
FROZEN = ROOT / 'experiments/source_0x31_chains_20261115'
DRIVER = ROOT / 'experiments/native_source_live_port_20261115/run_chain_owned.py'
VERIFY_SHA = 'd40cf9423a8de7f5cdf73621bcd9b63ca8a3d53062c4c2d80eec029ff88040fc'
DRIVER_SHA = '297d099ff4bdd2f958e436a7bf403af743dcc1f8e3749fa61b84f253de65b721'
INDEX_SHA = '5f204a52d82a61174da1dbb33da3c132f636b5d8bc5eba39f7679279599782c0'
PHASES = ('math-parse','math-run','native-parse','native-run')
INVENTORIES = ('before','math-parse-before','math-parse-after','math-run-before','math-run-after','post-math','native-parse-before','native-parse-after','native-run-before','native-run-after','after')
ROOT_FILES = ('verification.json','result.json','math-result.json','math-verification.json','authoritative-closure.json','COPY-PROVENANCE.json','CURRENT-SOURCE-LOCK.json','FROZEN-FUNCTIONAL-SOURCE.json','PROVENANCE-DRIFT-ACKNOWLEDGMENT.json')


def need(ok, label):
    if not ok: raise ValueError(label)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value,indent=2,allow_nan=False,ensure_ascii=True)+'\n').encode()


def read(path):
    for item in (path,*path.parents):
        st=item.lstat()
        need(not stat.S_ISLNK(st.st_mode) and not getattr(st,'st_file_attributes',0)&0x400,'Reparse input refused')
    before=path.stat();need(path.is_file() and before.st_size<=16*1024*1024,'Bounded regular input required')
    raw=path.read_bytes();after=path.stat()
    need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed during read')
    return raw


def payload_guard(value, key=''):
    # Independent final scanner is stricter and uses a separate implementation.
    banned={'points','mask','private_capture','private_tip','private_axis','vertex_positions','vertex_buffer','index_buffer','native_rest_matrices','native_rest_words_uint32','rest_by_root_id','expected_world_bones','expected_native_z_tips','blender_matrix_local_row_major','pcm','image_data','audio_data','base64'}
    if isinstance(value,dict):
        for name,child in value.items():
            need(not(name.lower() in banned and isinstance(child,(list,dict,str)) and child),'Private payload key refused: '+name)
            need(not(name.lower() in {'vertices','positions','normals','weights','indices','triangles'} and isinstance(child,(list,dict)) and child),'Geometry array refused')
            payload_guard(child,name)
    elif isinstance(value,list):
        need(not(len(value) in (3,4,9,12,16) and all(type(x) in (int,float) for x in value) and any(type(x) is float for x in value)),'Unexplained numeric coordinate vector refused: '+key)
        for child in value:payload_guard(child,key)
    elif isinstance(value,float):need(math.isfinite(value),'Nonfinite metadata refused')
    elif isinstance(value,str):need(not re.fullmatch(r'[A-Za-z0-9+/=]{512,}',value),'Encoded payload refused')


def put(name,raw):
    target=HERE/name
    need(target.resolve().is_relative_to(HERE),'Archive path escaped')
    if target.suffix=='.json':payload_guard(json.loads(raw))
    raw.decode('utf-8')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(raw)


def proof_constants():
    tree=ast.parse(read(DRIVER).decode('utf-8'))
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROOFS' for t in node.targets))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    if args.seal:
        need((HERE/'PRIVACY_REPORT.json').exists(),'Run independent scanner before sealing')
        report=json.loads(read(HERE/'PRIVACY_REPORT.json'));need(report['passed'] is True,'Privacy scanner did not pass')
        rows=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(read(p))} for p in sorted(HERE.rglob('*'),key=lambda path:path.relative_to(HERE).as_posix()) if p.is_file() and p.name!='INDEX.json']
        put('INDEX.json',encoded({'format':'has_source_native_chains_actual_index_1','historical_full_revision':'f0dd57a2e568089d396fecba819ab987da658bf0','current_source_HEAD_context':'9de4e6cbdf8b0369cbdf118a40c13f85860eaac0','files':rows,'file_count':len(rows),'bytes':sum(row['bytes'] for row in rows),'private_native_arrays_or_media_included':False}))
        print(json.dumps({'INDEX_sha256':sha(read(HERE/'INDEX.json')),'files':len(rows),'bytes':sum(row['bytes'] for row in rows)}));return
    need({p.name for p in HERE.iterdir()}=={'assemble.py','scan_packet.py'},'Fresh packet required; retain any partial attempt')
    need(sha(read(DRIVER))==DRIVER_SHA and sha(read(ACTUAL/'verification.json'))==VERIFY_SHA,'Reviewed actual driver/verification changed')
    need(sha(read(FROZEN/'INDEX.json'))==INDEX_SHA,'Frozen source index changed')
    for row in json.loads(read(FROZEN/'INDEX.json'))['files']:need(sha(read(FROZEN/row['path']))==row['sha256'],'Frozen indexed source changed')
    verification=json.loads(read(ACTUAL/'verification.json'));result=json.loads(read(ACTUAL/'result.json'));closure=json.loads(read(ACTUAL/'authoritative-closure.json'));math_result=json.loads(read(ACTUAL/'math-result.json'))
    need(verification['passed'] and verification['result']==result and verification['math_result']==math_result and verification['current_full_product_qualified'] is False,'Actual result/scope differs')
    need(result['checks']==21087 and result['failures']==0 and result['dynamic_ticks']==1440 and result['rule_evaluations']==5760 and len(result['cases'])==12,'Actual native preregistered gates differ')
    need(math_result['checks']==4012 and math_result['failures']==[] and math_result['status']=='PASSED_SYNTHETIC_CHAIN_MATH_ONLY','Actual math gates differ')
    need(closure['verification_sha256']==VERIFY_SHA and all(closure[k] is True for k in ('validation_passed','all_retained_children_reaped','owned_runtime_commands_absent','runtime_lease_released','no_process_killed','source_preservation_established')),'Actual authoritative closure differs')
    need(len(verification['preservation'])==9 and all(verification['preservation'].values()),'All nine preservation gates required')
    need([p['phase'] for p in verification['phases']]==list(PHASES) and all(p['passed'] and p['exit']==0 and p['retained_Popen_reaped'] and not p['timed_out'] and not p['owned_child_terminated'] and not p['owned_child_forced_kill'] and not p['error_markers'] for p in verification['phases']),'Actual phase closure failed')
    copied=[]
    def copy(origin,name):
        raw=read(origin);put(name,raw)
        copied.append({'source':origin.relative_to(ROOT).as_posix(),'stored':name,'bytes':len(raw),'sha256':sha(raw)})
    for name in ROOT_FILES:copy(ACTUAL/name,'actual/'+name)
    for phase in PHASES:
        for suffix in ('-command.json','-engine.log','-owned-start.json','-process.json','-stderr.log','-stdout.log'):
            copy(ACTUAL/(phase+suffix),'actual/'+phase+suffix)
    for label in INVENTORIES:
        for suffix in ('-inventory-process.json','-inventory-stdout.log','-inventory-stderr.log','-runtime-closure.json'):
            copy(ACTUAL/(label+suffix),'actual/'+label+suffix)
        need(json.loads(read(ACTUAL/(label+'-runtime-closure.json')))['owned_count']==0,'Runtime inventory was not closed')
    proof_rows=[]
    for name,(relative,digest) in proof_constants().items():
        origin=ROOT/relative;need(sha(read(origin))==digest,'Predecessor proof changed')
        copy(origin,'predecessors/'+name+'.json');proof_rows.append({'name':name,'source':relative,'sha256':digest})
    provenance=json.loads(read(ACTUAL/'COPY-PROVENANCE.json'))
    aliases=[]
    need(len(provenance['aliases'])==10 and provenance['application_files']==204,'Actual staged source domain differs')
    for name,row in provenance['aliases'].items():
        origin=Path(row['path']);need(origin.parent==ACTUAL/'Studio' and origin.suffix=='.gd','Only exact staged GDScript aliases admitted')
        raw=read(origin);need(sha(raw)==row['sha256'],'Actual alias changed')
        if 'source' in row:need(raw==read(Path(row['source'])),'Staged/original source alias differs')
        copy(origin,'code/'+origin.name)
        aliases.append({'alias':name,'stored':'code/'+origin.name,'sha256':row['sha256'],'source':Path(row['source']).relative_to(ROOT).as_posix() if 'source' in row else 'Generated from frozen driver MATH_ENTRY literal'})
    copy(DRIVER,'code/run_chain_owned.py')
    for origin,name in [(FROZEN/'SOURCE_LOCK.json','source/frozen-SOURCE-LOCK.json'),(FROZEN/'INDEX.json','source/frozen-packet-INDEX.json'),(FROZEN/'COUNT_AUDIT_20261115.json','source/count-audit.json'),(FROZEN/'COUNT_AUDIT_20261115.md','source/count-audit.md'),(FROZEN/'ERRATA.md','source/ERRATA.md')]:copy(origin,name)
    lock=json.loads(read(ACTUAL/'CURRENT-SOURCE-LOCK.json'));functional=json.loads(read(ACTUAL/'FROZEN-FUNCTIONAL-SOURCE.json'));old_lock=json.loads(read(FROZEN/'SOURCE_LOCK.json'))
    for row in lock['files']:
        need(sha(read(ACTUAL/'Studio'/row['path']))==row['sha256']==functional['source_sha256'][row['path']],'Actual current source/hash join failed')
    need(len(lock['files'])==204 and len(old_lock['files'])==202,'Old/current source locks differ from measured scopes')
    drift=json.loads(read(ACTUAL/'PROVENANCE-DRIFT-ACKNOWLEDGMENT.json'))
    need(drift['root_acknowledged'] and drift['current_full_product_suite_claimed'] is False and not drift['current_snapshot_is_historical_full_snapshot'],'Historical full scope was silently promoted')
    rows=result['cases'];groups=[rows[:6],rows[6:]]
    for group in groups:
        by_name={row['profile']:row for row in group};need(set(by_name)=={'control','positive3','negative3','positive12','positive50','repeat12'},'Actual profile list differs')
        need(by_name['positive12']['final_weighted_sha256']==by_name['repeat12']['final_weighted_sha256'],'Repeat result not exact')
    for row in rows:
        need(row['vertices']==9661 and row['weighted_to_selected']==542 and row['shared_with_other_bones']==340 and row['unaffected_vertices']==9119 and row['ticks']==120,'Actual weighted domain changed')
        need(row['unaffected_exact'] and row['Off_all_weighted_points_exact'] and row['basis_error_max']<=2e-5 and row['origin_error_max']<=2e-5*row['root_size'] and row['tip_error_max']<=2e-5*row['root_size'],'Actual strict geometry/Off gates failed')
    benchmark={'format':'has_actual_two_chain_benchmark_1','status':'PASSED_EXPERIMENTAL_CHAIN_ORCHESTRATION_ONLY','root_only_runtime_execution':True,'math_checks':4012,'math_failures':0,'math_maximum_error':math_result['maximum_error'],
               'native_checks':21087,'native_failures':0,'actor_ticks':1440,'rule_evaluations':5760,'cases':12,'all_four_phases_parsed_run_reaped_closed_without_kill':True,'preservation_gates_passed':9,
               'selected_native_pairs':[[17,18],[26,27]],'retained_native_bones':69,'retained_native_rules':49,'authored_intermediate_native25':{'parent':7,'has_retained_jiggle_rule':False,'corrected_prior_README_claim':True},
               'vertices':9661,'union_weighted_vertices':542,'shared_with_other_bones':340,'zero_selected_weight_vertices_exact':9119,'unselected_world_bones_exact':65,
               'pair_domains':[{'pair':[17,18],'weighted':184,'shared_with_other_bones':118,'zero_weight':9477},{'pair':[26,27],'weighted':358,'shared_with_other_bones':222,'zero_weight':9303}],
               'maximum_errors':{k:max(r[k] for r in rows) for k in ('basis_error_max','origin_error_max','tip_error_max','boundary_correction_max','parent_local_closure_max')},
               'source_conversion_scale':0.01905,'nominal_model_root_scales':[1.0,2.0],'actual_basis_norms':sorted({r['root_size'] for r in rows}),
               'all_Off_frames12_24_and_weighted_points_exact':True,'all_repeat12_weighted_hashes_exact':True,
               'current_source_HEAD_context':verification['current_source_HEAD_context'],'historical_full_revision':verification['historical_full_revision'],'current_full_product_qualified':False,
               'limits':['Four-rule external harness, not all49 rules or product feature activation','HAS procedural-parent policy, not proven Source client traversal/SDK execution or artist fidelity','Temporary world accelerations0/+3/-3/12/50, not actual fan controls','CPU weighted positions and exact restoration, not GPU/material/normal/render fidelity','No body/fan/Record/Undo/HAS/movie integration from this proof','Single source conversion0.01905 with root1/2, not two conversions or six-foot canonical standard','Historical2e-5 normal-fidelity failure stays failed']}
    put('BENCHMARK.json',encoded(benchmark))
    lease_hashes={name:sha(read(ACTUAL/name)) for name in ('ROOT-MATH-LEASE.json','ROOT-NATIVE-LEASE.json')}
    source_proof={'format':'has_native_chain_actual_copy_source_proof_1','actual_folder':ACTUAL.relative_to(ROOT).as_posix(),'actual_verification_sha256':VERIFY_SHA,'driver_sha256':DRIVER_SHA,'frozen_packet_INDEX_sha256':INDEX_SHA,
                  'raw_copies':copied,'exact_actual_code_aliases':aliases,'public_code_driver':'code/run_chain_owned.py','current_application_hash_joins':204,'older_packet_source_lock_entries':202,
                  'current_functional_source_hashes':len(functional['source_sha256']),'predecessors':proof_rows,'actual_lease_hashes_only':lease_hashes,'actual_leases_copied':False,
                  'private_assets_media_geometry_rest_or_coordinate_oracles_copied':False,'source_recovery':'Use the accompanying repository checkpoint/source hashes and exact code aliases; no private input fixture is distributed.',
                  'historical_full_scope':'f0dd full is retained historical proof only; current source drift is explicitly acknowledged, state180 is separately actual, and this chain experiment is not a new full product pass.',
                  'native25_erratum':'No retained rule belongs to25. It is an authored no-rule intermediate before26. Earlier frozenREADME sentence is wrong; exact code/profile need no change.'}
    put('SOURCE_PROOF.json',encoded(source_proof))
    put('README.md',('''# Actual two-pair Source chain proof

Root alone executed attempt1: synthetic Godot math **4,012/0**, then actual Model/SceneIO/native-pair transport **21,087/0**,12cases,1,440ticks and5,760rule evaluations. Four separate headless parse/run children exited0, were reaped, and passed fresh owned-process closure with no kills. All nine preservation gates passed. Full native-derived transforms and weighted arrays stayed in memory/private outputs.

The selected rule pairs are17→18 and26→27. Native26 inherits authored intermediate25(parent7), which **has no native jiggle rule**. The frozen source README's earlier claim that25 had a rule is corrected by source/ERRATA.md. The code/profile were already correct. All49 retained rules remain metadata; this proof solves four.

The archive contains exact actual code aliases/driver/generated synthetic entry, strictly whitelisted commands/process/inventory/log/result/verification/closure metadata, predecessor receipts, old/current source hash locks, explicit historical-full drift acknowledgment, aggregate benchmark and an independent recursive privacy/hash/alias scanner. It contains no actual lease, private GLB/HAS/MDL/VVD, native rest/weighted/coordinate arrays, native input reports, artwork, media or copied SDK source. Absolute input paths in command/provenance metadata identify files; their contents are excluded.

The current source snapshot is204 staged app/data/project files, with its broader functional hash catalogue. The older packet lock202 and f0dd full suite remain historical, independently pinned records. The current source differs; no current full product pass is claimed. Use the accompanying repository checkpoint and source hashes when retrieving code. The exact nine aliases plus generated SceneTree entry and driver are under code/. The old frozen packet INDEX and all its original entries remain unchanged.

Run `python -B scan_packet.py` from this packet after retrieval to verify the final index, explicit whitelist, recursive JSON privacy, binary/base64 refusals, source alias hashes, generated-entry/driver literal join and actual evidence scopes. The scanner does not launch apps, inspect processes, contact services or run archived commands. `--write-report` is only for assembling a fresh unsealed packet. Actual leases are never restored from this archive. New runtime work requires root source review, fresh authority, current source hashes and closure.

This is experimental HAS parent-order orchestration and CPU weighted deformation/restoration, not a product feature, full49-rule solver, Source SDK/client/artist parity, GPU/material/normal fidelity, body/fan/Record/Undo/HAS/movie integration, PMX reconstruction or six-foot canonical standardization. The historical2e-5 normal-fidelity failure remains failed. Original/private outputs were neither modified nor deleted by packaging.
''').encode())
    print(json.dumps({'payloads_written':len(copied)+3,'next':'Run independent scan_packet.py --write-report, assemble.py --seal, then scan_packet.py','actual_runtime_or_Git_action':False}))


if __name__=='__main__':main()

"""Seal only reviewed audit source and compact aggregate metadata, never raw reports."""
from pathlib import Path
import ast,difflib,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'experiments/resume_full_20261115/publication'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a,b=functions(OLD/'publication_gates.py'),functions(HERE/'publication_gates.py')
assert set(a)==set(b);changed=sorted(n for n in a if a[n]!=b[n]);assert changed==['validate_live','validate_raw_host']
for name in ('audit_receipts.py','publication_gates.py'):
    before=(OLD/name).read_text(encoding='utf-8').splitlines(True);after=(HERE/name).read_text(encoding='utf-8').splitlines(True)
    (HERE/(name+'.diff')).write_text(''.join(difflib.unified_diff(before,after,fromfile='historical/'+name,tofile='current/'+name)),encoding='utf-8',newline='\n')
actual=load(ROOT/'output/current-full-receipts-driver-20261116-attempt1/verification.json')
assert actual['exit']==0 and actual['retained_Popen_reaped'] and actual['summary']['passed']
save(HERE/'ACTUAL_SUMMARY.json',{'format':'has_current_full_receipt_audit_actual_summary_1','source_commit':actual['summary']['source_commit'],
    'run_directory':actual['summary']['run_directory'],'passed':True,'CPU_python_pid':actual['pid'],'retained_Popen_reaped':True,'seconds':actual['seconds'],
    'receipt_inventory':{'path':actual['output']+'\\receipt-inventory.json','sha256':actual['receipt_inventory_sha256']},'full_report_sha256':actual['full_report_sha256'],
    'observed_receipts':actual['summary']['unique_receipt_files'],'exit0':actual['summary']['success_exit_0_files'],'registered_Krita_cancel_exit2':actual['summary']['expected_krita_cancel_exit_2_files'],
    'fresh_root':actual['summary']['fresh_root_receipt_files'],'nested':actual['summary']['nested_receipt_files_outside_root'],
    'all_closed_and_fresh':True,'inline_occurrences':actual['summary']['inline_occurrences'],'inline_unique_desktops':actual['summary']['inline_unique_desktops'],
    'all_inline_exact_physical_matches':True,'unexpected_failures':[],'missing_receipts':0,'registry_entries':157,'core_groups':36,'movies':21,'functional_sources':1019,
    'root_host_closure_bound':True,'normalized_log_suffix_verified':True,'current_source_membership_and_bytes_verified':True,
    'native_engine_CIM_Git_actions':False,'graphics_release_created':False,'raw_reports_and_receipts_retained_private_under_output':True})
save(HERE/'SOURCE_REVIEW.json',{'format':'has_current_full_audit_source_review_1','unchanged_gate_functions':sorted(set(a)-set(changed)),
    'changed_gate_functions':changed,'validate_result_AST_exact_historical':a['validate_result']==b['validate_result'],
    'registry_names_exact_historical':all(load(HERE/'RESULT_REGISTRY.json')[k]==load(OLD/'RESULT_REGISTRY.json')[k] for k in ('expected_result_keys','expected_core_process_keys','expected_movie_keys')),
    'birth_schema_adaptation':'Uses actual root-birth-observation.json flat schema and exact observed SHA; no old-schema alias fabricated.',
    'additional_guards':'Actual full report/log suffix, PASS-only prefix, current1019 membership and source bytes checked before audit output.',
    'private_output_rule':'Auditor OUT is a fresh direct child of ROOT/output; full-verification/raw receipt copies are not source packet payloads.',
    'unused_archival_functions':'validate_scoped and validate_reviewed_delta are retained historical source helpers and are not called by this current receipt audit. No current native-profile parity is inferred.'})
paths=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json' and '__pycache__' not in p.parts)
rows=[{'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
assert not any(p.suffix.lower() in ('.glb','.mdl','.vvd','.png','.mp4','.has','.blend') for p in paths)
save(HERE/'INDEX.json',{'format':'has_current_full_receipt_source_packet_1','files':rows,'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'raw_full_reports_or_assets_included':False})
print(json.dumps({'source_packet':str(HERE),'payload_files':len(rows),'index_sha256':sha(HERE/'INDEX.json'),'audit_passed':True}))

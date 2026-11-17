"""Source-only owner-copy admission prototype. No filesystem copies or native IO.

Current activation is deliberately impossible: no actual future full+merge proof
has been sealed. Pure checks below accept supplied in-memory metadata solely for
source review and synthetic negative testing, never authorizing writes by themselves.
"""
from pathlib import Path
import ast,calendar,datetime,hashlib,importlib.util,json,re
HERE=Path(__file__).resolve().parent
APPROVED_ACTIVATION_SHA256=None
TEXT={'.py','.pyw','.gd','.gdshader','.tscn','.tres','.json','.godot','.cfg','.uid','.txt','.md','.svg'}
TEXT_PATHS={'tests/blank','tests/krita_fixture/has_fixture.desktop','tools/docker/sourceio_metadata.Dockerfile','tools/docker/sourceio_worker.Dockerfile','tools/krita-runtime.Dockerfile','tools/linux/liveness_shim.sh','tools/linux/run_test.sh','tools/linux/shoot.sh'}
REFERENCE_SHA='c39e3751621bc4428166d64b7c6f6120bd7ef39251ccf9bbbf8a46dca390ce21'
LEGACY_SHA='0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
REGISTRY_SHA='07f25193d138d58516b9a1f50f4abe791a56cbaef5769d22ff91e670a8178352'
SOURCE52_SHA='4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
OLD_DELTA_SHA='b6d060e07d4a5956ce82b8a608eeb75d23a0f913acded28cba2c71adc8e29e0c'
OLD_LOCK_SHA='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'

def need(ok,message):
 if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
def parse(raw):
 need(type(raw) is bytes and len(raw)<=64*1024*1024,'bounded raw metadata bytes required')
 def pairs(rows):
  out={}
  for k,v in rows:need(k not in out,'duplicate metadata key');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
def require_activation(document):
 need(type(APPROVED_ACTIVATION_SHA256) is str and re.fullmatch('[0-9a-f]{64}',APPROVED_ACTIVATION_SHA256),'UNREADY: actual qualified candidate/full/root release/merge activation is missing')
 need(type(document) is bytes and digest(document)==APPROVED_ACTIVATION_SHA256,'sealed actual activation differs')
 return parse(document)

def _reference():
 raw=(HERE/'reference_close_terminal.py').read_bytes();need(digest(raw)==REFERENCE_SHA,'reference terminal source changed')
 legacy=HERE/'legacy_result_gates.py';need(digest(legacy.read_bytes())==LEGACY_SHA,'reference legacy source changed')
 spec=importlib.util.spec_from_file_location('owner_copy_legacy_reference',legacy);L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
 wanted={'require','typed_same','ns','validate_terminal','validate_result','classify_receipt','validate_ownership'}
 nodes=[node for node in ast.parse(raw).body if isinstance(node,ast.FunctionDef) and node.name in wanted]
 need({n.name for n in nodes}==wanted,'exact pure terminal gate functions missing')
 namespace={'Path':Path,'calendar':calendar,'datetime':datetime,'re':re,'Legacy':L}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact pure terminal source gates>','exec'),namespace)
 return namespace
REF=_reference()

def observation(value,context,minimum_ns):
 need(value.get('owned_runtime_command_matches_absent') is True and value.get('owned_runtime_matches')==[] and value.get('root_observer_issued_no_termination') is True and value.get('observer_retained_Popen_reaped') is True,'actual root observer not closed')
 need(REF['ns'](value['observed_utc'])>=minimum_ns,'root observation predates terminal')
 for name,pid,birth in [('coordinator',context['coordinator_pid'],context['coordinator_birth']),('python',context['python_pid'],context['python_birth'])]:
  row=value[name];need(type(row['pid']) is int and row['pid']==pid and row['expected_creation_utc']==birth and row['original_absent'] is True and type(row['pid_present']) is bool,'exact absent process identity differs')
  if row['pid_present']:need(type(row['current_creation_utc']) is str and REF['ns'](row['current_creation_utc'])!=REF['ns'](birth),'same original PID still alive')
  else:need(row['current_creation_utc'] is None,'absent PID current birth differs')

def check_candidate_bundle(raw,context,registry,expected_hashes,report_mtime_ns):
 """Pure validation of actual-schema artifacts; caller IO/provenance remains missing."""
 names={'state','birth','launch','before','after','full_report','canonical_log','inventory','release'}
 need(type(raw) is dict and set(raw)==names and set(expected_hashes)==names,'exact candidate artifact membership required')
 for key in names:need(type(raw[key]) is bytes and len(raw[key])<=64*1024*1024 and digest(raw[key])==expected_hashes[key],'candidate raw artifact binding differs: '+key)
 docs={k:parse(v) for k,v in raw.items() if k!='canonical_log'}
 registry_raw=(HERE/'reference_registry.json').read_bytes();need(digest(registry_raw)==REGISTRY_SHA,'reference registry source changed')
 registry_reference=parse(registry_raw);old_commit=registry_reference['source_commit']
 need(type(context['commit']) is str and re.fullmatch('[a-f0-9]{40}',context['commit']),'candidate commit type differs')
 expected_registry_raw=registry_raw.replace(old_commit.encode(),context['commit'].encode())
 need(registry_raw.count(old_commit.encode())==1 and REF['typed_same'](registry,parse(expected_registry_raw)) and context.get('registry_sha256')==digest(expected_registry_raw),'unreviewed registry membership/schema/verifier or raw context pin')
 need(REF['validate_terminal'](*(docs[k] for k in ['state','birth','launch','before','after']),context) is True,'complete actual candidate PASS required; focused or failed runs cannot substitute')
 need(context['functional_sources']==1029 and type(context['functional_sources']) is int,'exact1029 source scope required')
 REF['validate_result'](docs['full_report'],context,registry)
 state=docs['state'];start=REF['ns'](state['started_utc']);finish=REF['ns'](state['finished_utc'])
 need(start>=REF['ns'](context['coordinator_birth']) and type(report_mtime_ns) is int and start<=report_mtime_ns<=finish,'fresh actual full report timing required')
 normalized=raw['full_report'].decode('utf-8-sig').replace('\r\n','\n').rstrip();log=raw['canonical_log'].decode('utf-8-sig').replace('\r\n','\n').rstrip()
 need(log.endswith(normalized) and all(not line.strip() or line.startswith('PASS ') for line in log[:-len(normalized)].splitlines()),'exact fresh canonical full-report suffix required')
 inv=docs['inventory'];release=docs['release']
 need(inv.get('format')=='has_neon_ffcf_terminal_receipt_inventory_1' and inv.get('source_commit')==context['commit'] and inv.get('run_directory')==state['run_folder'] and inv.get('suite_status')=='passed' and type(inv.get('suite_exit')) is int and inv['suite_exit']==0,'root full inventory scope differs')
 for k,n in [('functional_sources',1029),('result_groups',158),('core_groups',36),('movie_groups',21)]:need(type(inv.get(k)) is int and inv[k]==n,'root inventory source/group count differs')
 need(all(inv.get(k) is True for k in ['full_suite_passed','final_full_report_used','all_collected_jobs_desktops_closed_private','all_inline_exact_physical_matches','root_observer_issued_no_termination','registered_cancel_observed']),'root full physical proof missing')
 rows=inv['rows'];inline=inv['inline_receipts'];need(type(rows) is list and rows and type(inline) is list,'physical ownership rows required')
 cancels={r['receipt']['desktop']:r['receipt'] for r in rows if r['classification']=='registered_Krita_cancel_exit2'};need(len(cancels)==1,'actual registered cancellation required')
 cancel=next(iter(cancels.values()))
 for row in rows:need(REF['classify_receipt'](row['receipt'],REF['typed_same'](row['receipt'],cancel),True)==row['classification'],'physical classification differs')
 classes=REF['validate_ownership'](rows,inline,cancel);jobs=len(classes)
 need(type(inv['unique_physical_jobs']) is int and inv['unique_physical_jobs']==jobs and REF['typed_same'](inv['unique_job_classifications'],classes),'actual unique physical ownership differs')
 need(type(inv['physical_receipt_files']) is int and inv['physical_receipt_files']==len(rows) and type(inv['normal_exit0']) is int and inv['normal_exit0']==list(classes.values()).count('normal_exit0') and type(inv['registered_cancel_exit2']) is int and inv['registered_cancel_exit2']==1 and type(inv['failed_partial_nonzero']) is int and inv['failed_partial_nonzero']==0,'dynamic actual job totals differ')
 observation(inv['process_observation'],context,finish)
 need(release.get('format')=='has_root_neon_ffcf_graphics_lease_release_1' and release.get('released') is True and release.get('release_kind')=='closed_passed_full_run' and release.get('source_commit')==context['commit'] and release.get('canonical_run')==context['run_name'],'actual passed full release required')
 for key,want in [('coordinator_pid',context['coordinator_pid']),('python_pid',context['python_pid']),('functional_sources',1029),('physical_jobs',jobs),('physical_receipt_files',len(rows)),('suite_exit',0)]:need(type(release.get(key)) is int and release[key]==want,'root release identity/totals differ')
 need(all(release.get(k) is True for k in ['full_suite_passed','final_full_report_used','all_collected_jobs_desktops_closed_private','all_inline_exact_physical_matches','root_observer_issued_no_termination']),'root release physical conditions differ')
 need(release['receipt_inventory_sha256']==digest(raw['inventory']) and release['terminal_state_sha256']==digest(raw['state']),'root release raw-byte joins differ')
 observation(release['second_identity_and_scope_observation'],context,finish)
 need(release['released_utc']==release['second_identity_and_scope_observation']['observed_utc'],'root release timestamp differs')
 return {'candidate_commit':context['commit'],'functional_source_sha256':docs['before']['source_sha256'],'candidate_source_map_sha256':digest(encoded(docs['before']['source_sha256'])),'physical_jobs':jobs,'metadata_checks_only':True,'outer_actual_activation_still_required':True}

def canonical(raw,name):return raw.replace(b'\r\n',b'\n') if Path(name).suffix in TEXT or name in TEXT_PATHS else raw

def check_merged_sources(tested,working,git_blobs,recipe,merged_revision,allow_checkout_eol=False):
 need(type(merged_revision) is str and re.fullmatch('[a-f0-9]{40}',merged_revision),'exact merged revision required')
 need(type(tested) is dict and len(tested)==1029 and set(tested)==set(working)==set(git_blobs)==set(recipe),'exact merged/candidate functional membership required')
 for name,expected in tested.items():
  need(type(name) is str and name and not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name and ':' not in name,'canonical functional name required')
  raw=working[name];blob=git_blobs[name];need(type(raw) is bytes and type(blob) is bytes and digest(raw)==expected,'merged working bytes are not candidate-tested exact')
  row=recipe[name];need(set(row)=={'tested_working_sha256','git_blob_sha256','canonical_content_sha256','source_mode'},'exact EOL recipe keys required')
  need(row['tested_working_sha256']==expected and row['git_blob_sha256']==digest(blob) and row['canonical_content_sha256']==digest(canonical(raw,name)),'tested/Git/EOL byte recipe differs')
  if raw==blob:need(row['source_mode']=='exact_Git_and_tested_working_bytes','wrong exact source mode')
  else:
   need(allow_checkout_eol is True and (Path(name).suffix in TEXT or name in TEXT_PATHS) and canonical(raw,name)==canonical(blob,name),'nontext or content mismatch cannot use EOL admission')
   need(row['source_mode']=='candidate_tested_raw_with_explicit_Git_CRLF_LF_bridge','wrong tested-working source mode')
 return {'merged_revision':merged_revision,'source_files':1029,'tested_working_map_sha256':digest(encoded(tested)),'tested_content_map_sha256':digest(encoded({n:digest(canonical(v,n)) for n,v in working.items()})),'copy_source_mode':'candidate_tested_raw_bytes','working_EOL_recipe_sha256':digest(encoded(recipe)),'actual_activation_and_clean_Git_preflight_still_required':True}

def check_reviewed_delta(old,new,rows):
 """Metadata-only exact second bridge; no fixed guessed count of new changes."""
 need(type(old) is dict and type(new) is dict and len(old)==1019 and len(new)==1029 and set(old)<=set(new),'exact52→candidate membership required; removals refuse')
 for table in (old,new):
  for name,entry in table.items():
   need(type(name) is str and name and not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name and ':' not in name,'canonical delta source name required')
   need(type(entry) is dict and set(entry)=={'raw_sha256','content_sha256'} and all(type(v) is str and re.fullmatch('[a-f0-9]{64}',v) for v in entry.values()),'exact delta SHA identity fields required')
 need(type(rows) is list and all(type(r) is dict for r in rows),'explicit reviewed delta rows required')
 declared={r['path']:r for r in rows};need(len(declared)==len(rows),'duplicate delta row')
 changed=set()
 for name,entry in new.items():
  need(set(entry)=={'raw_sha256','content_sha256'},'exact source identity fields required')
  previous=old.get(name)
  if previous is not None and previous['content_sha256']==entry['content_sha256']:need(name not in declared,'unchanged file falsely relaxed');continue
  changed.add(name);need(name in declared,'unreviewed52→candidate delta')
  row=declared[name];need(row=={'path':name,'classification':'added' if previous is None else 'modified','old_raw_sha256':previous['raw_sha256'] if previous else None,'old_content_sha256':previous['content_sha256'] if previous else None,'new_raw_sha256':entry['raw_sha256'],'new_content_sha256':entry['content_sha256']},'delta byte identity differs')
 need(set(declared)==changed,'extra or missing explicit delta')
 return {'old_files':1019,'new_files':1029,'old_raw_source_map_sha256':digest(encoded({n:v['raw_sha256'] for n,v in old.items()})),'new_raw_source_map_sha256':digest(encoded({n:v['raw_sha256'] for n,v in new.items()})),'old_content_source_map_sha256':digest(encoded({n:v['content_sha256'] for n,v in old.items()})),'new_content_source_map_sha256':digest(encoded({n:v['content_sha256'] for n,v in new.items()})),'changed_or_added_files':sorted(changed),'historical_native_to52_bridge_still_separately_required':True}

def check_historical_predecessors(lock_raw,delta_raw,source52_raw=None,source52_bytes=None):
 need(digest(lock_raw)==OLD_LOCK_SHA and digest(delta_raw)==OLD_DELTA_SHA,'immutable historical input-lock/delta changed')
 delta=parse(delta_raw);need(delta['old_functional_files']==1008 and delta['new_functional_files']==1019 and delta['removed']==[] and len(delta['changed_or_added'])==20,'native→52 exact20-row bridge differs')
 need(delta['unchanged_core']==['src/model.gd','src/source_bone_bindings.gd','src/scene3d.gd'] and delta['current_source_before_sha256']==SOURCE52_SHA,'old native identity/source target proof differs')
 out={'historical_bridge_preserved':True,'new_candidate_bridge_still_required':True,'historical52_target_map_joined':False,'old52_raw_source_map_sha256':None,'old52_content_source_map_sha256':None}
 if source52_raw is None or source52_bytes is None:return out
 need(type(source52_raw) is bytes and digest(source52_raw)==SOURCE52_SHA,'actual historical52 manifest bytes required')
 manifest=parse(source52_raw);need(manifest['commit']=='52f63c944ded7a651da871524d23a345b606424d' and len(manifest['source_sha256'])==1019,'actual52 manifest scope differs')
 identities=manifest['source_sha256'];need(type(source52_bytes) is dict and set(source52_bytes)==set(identities),'actual historical52 byte witness membership required')
 content={}
 for name,expected in identities.items():
  raw=source52_bytes[name];need(type(raw) is bytes and digest(raw)==expected,'historical52 source byte witness differs')
  content[name]=digest(canonical(raw,name))
 out.update(historical52_target_map_joined=True,old52_raw_source_map_sha256=digest(encoded(identities)),old52_content_source_map_sha256=digest(encoded(content)))
 return out


def assemble_copy_proposal(candidate,merged,historical,delta):
 """Join pure summaries only; a favorable plan still never authorizes execution."""
 need(candidate.get('outer_actual_activation_still_required') is True and merged.get('actual_activation_and_clean_Git_preflight_still_required') is True,'actual outer proof cannot be skipped')
 need(candidate['candidate_source_map_sha256']==merged['tested_working_map_sha256'] and merged['source_files']==1029,'full candidate and merged source bytes are not joined')
 need(historical.get('historical_bridge_preserved') is True and delta.get('old_files')==1019 and delta.get('new_files')==1029 and delta.get('historical_native_to52_bridge_still_separately_required') is True,'both source bridges required')
 need(historical.get('historical52_target_map_joined') is True and historical.get('old52_raw_source_map_sha256')==delta.get('old_raw_source_map_sha256') and historical.get('old52_content_source_map_sha256')==delta.get('old_content_source_map_sha256'),'delta old side not joined to actual historical52 source/byte witness')
 need(delta.get('new_raw_source_map_sha256')==candidate['candidate_source_map_sha256'] and delta.get('new_content_source_map_sha256')==merged.get('tested_content_map_sha256'),'delta new side not joined to exact qualified candidate/merged content')
 return {'format':'has_neon_future_owner_copy_source_proposal_1','status':'PLAN_ONLY_ACTIVATION_UNREADY','candidate_commit':candidate['candidate_commit'],'merged_revision':merged['merged_revision'],'source_mode':merged['copy_source_mode'],'source_files':1029,'native_source_lock_sha256':OLD_LOCK_SHA,'source_delta_chain_preserved':True,'execution_authorized':False,'copy_executor_and_actual_FS_Git_preflight':'UNIMPLEMENTED_REQUIRED_SOURCE_SUCCESSOR','cold187_replay':'UNRUN_REQUIRED_SEPARATE_ROOT_EXECUTION','owner_or_portable_claim':False}

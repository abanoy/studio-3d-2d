from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
EXP=HERE.parent
identity=json.loads((HERE/'SOURCE_IDENTITIES.json').read_bytes())
verified={}
for key in ['candidate_reader','decoded_capture_reference','layout_design']:
 row=identity[key];base=EXP/Path(row['packet']).name
 assert hashlib.sha256((base/'INDEX.json').read_bytes()).hexdigest()==row['index_sha256']
 verified[key+'.INDEX']=row['index_sha256']
 if 'source' in row:
  digest=hashlib.sha256((base/row['source']).read_bytes()).hexdigest();assert digest==row['source_sha256'];verified[key+'.source']=digest
 if 'current_contract_sha256' in row:
  assert hashlib.sha256((base/'CURRENT_CONTRACT.md').read_bytes()).hexdigest()==row['current_contract_sha256']
recipe=json.loads((HERE/'PROPOSED_RECIPE.json').read_bytes());readiness=json.loads((HERE/'READINESS.json').read_bytes());privacy=json.loads((HERE/'PUBLIC_PROJECTION_POLICY.json').read_bytes())
assert recipe['execution_status']=='UNRUN_PLAN_ONLY' and recipe['executable_commands'] is None and recipe['stager_or_native_wrapper_implemented'] is False
assert readiness['status']=='NOT_EXECUTABLE_SOURCE_PROTOCOL_ONLY' and readiness['native_inputs_read'] is False and readiness['actual_native_qualification_performed'] is False
assert readiness['no_native_command_or_stager_provided'] is True and len(readiness['missing_required_gates'])==9
assert readiness['candidate_claims']['synthetic_source_CPU_pass'] is True
assert all(v is False for k,v in readiness['candidate_claims'].items() if k!='synthetic_source_CPU_pass')
assert identity['native_input_manifest']=='UNSELECTED_PRIVATE_ONLY_NOT_READ'
assert identity['future_tools']['native_oracle']['source_sha256'] is None
assert privacy['public_raw_logs_or_private_artifact_hashes_allowed'] is False and privacy['fixed_public_adoption_value']=='NONE'
for field in ['source_path','source_sha256','table_counts','names','native_indices_or_references','F32_words_or_values','raw_stdout_stderr_or_exceptions','private_manifest_or_asset_record_hashes']:assert field in privacy['forbidden_public_native_asset_fields']
assert all(v is False for k,v in recipe['scope'].items() if k!='native_sources')
report={'format':'has_pmx_native_read_protocol_source_consistency_1','status':'PASS_SOURCE_PROPOSAL_CONSISTENCY_ONLY_NOT_EXECUTABLE','source_identities_verified':verified,'native_inputs_read':False,'active_full_outputs_read':False,'process_observers_engines_CIM_Git_run':False,'native_wrapper_oracle_comparator_or_stager_executed':False,'actual_native_or_portable_qualification':False,'remaining_required_gates':len(readiness['missing_required_gates'])}
(HERE/'CPU_SOURCE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))

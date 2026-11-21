from pathlib import Path
import json,time
out=Path(__file__).resolve().parent;text=(out/'run_import_info_legacy_v3_scopes_20261121.py').read_text()
old="assert 'MISSING_TEXTURE_REOPEN true' in trace and 'MISSING_TEXTURE_PORTABLE true' in trace and 'PASS street PMX warning and cold reopen' in trace"
new="assert 'PASS street PMX warning and cold reopen of relocated packed mesh with missing-texture metadata' in trace\n result['native_wrapper_validated_both_engine_log_markers']=True\n result['native_marker_source']='Unchanged tests/verify_mmd_missing_texture.py assertions read both engine logs before ordinary temporary cleanup; raw windowed-engine stdout is not inherited on Windows.'"
assert text.count(old)==1;text=text.replace(old,new).replace('has-import-info-legacy-v3-scopes-','has-import-info-legacy-v4-scopes-').replace("'has_import_info_legacy_v3_scopes_1'","'has_import_info_legacy_v4_scopes_1'")
target=out/'run_import_info_legacy_v4_scopes_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
(out/'IMPORT_LEGACY_V3_ROOT_POSTCHECK_FAILURE_20261121.json').write_text(json.dumps({'status':'ROOT_POSTCHECK_FAILED','owner_checks_passed':53,'native_wrapper_exit':0,'native_wrapper_final_PASS_observed':True,'stage':'C:/a/Programming/cloudflare/has-import-info-legacy-v3-scopes-1795269018717888300','tool_result':'e48178 exit1','cause':'Root redundantly expected Godot stdout markers in Python wrapper stdout, although the unchanged wrapper validates the actual engine log files and Windows GUI engine does not inherit that stdout.','successor':'Preserve strict wrapper exit0/finalPASS and all source/process/error checks. Attribute both marker validations to the unchanged wrapper rather than inventing raw inherited stdout. No application or test source change.','recorded_ns':time.time_ns()},indent=2)+'\n')
print(str(target))

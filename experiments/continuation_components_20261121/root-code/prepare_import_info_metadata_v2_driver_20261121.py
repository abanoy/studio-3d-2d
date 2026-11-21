from pathlib import Path
import json,time
out=Path(__file__).resolve().parent;text=(out/'run_import_info_metadata163_20261121.py').read_text()
anchor="for row in json.loads((META/'TARGETS.json').read_bytes())['targets']:"
assert text.count(anchor)==1
extra='''for name in F.FILES:
 if not name.startswith('experiments/'):continue
 raw=(ROOT/name).read_bytes();assert sha(raw)==before[name]['sha256'];protected[ROOT/name]=raw
 p=studio/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
'''
text=text.replace(anchor,extra+anchor).replace('has-import-info-metadata163-','has-import-info-metadata163-v2-').replace('len(runtime)==1113','len(runtime)==1119').replace("'runtime_input_files':1113","'runtime_input_files':1119").replace("'has_import_info_metadata163_root_1'","'has_import_info_metadata163_root_v2_1'")
target=out/'run_import_info_metadata163_v2_20261121.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
(out/'IMPORT_METADATA_INITIAL_PREFLIGHT_REFUSAL_20261121.json').write_text(json.dumps({'status':'PREFLIGHT_REFUSED','checks':0,'processes_started':0,'stage':'C:/a/Programming/cloudflare/has-import-info-metadata163-1795268888761316700','tool_result':'0be0b6 exit1','error_type':'FileNotFoundError','cause':'Owned runtime freeze intentionally excludes experiments; required coordinator files were not copied before overlay. Main and original packet preserved.','successor':'Explicit copy of six exact current committed coordinator source files before applying reviewed three-target overlay.','recorded_ns':time.time_ns()},indent=2)+'\n')
print(str(target))

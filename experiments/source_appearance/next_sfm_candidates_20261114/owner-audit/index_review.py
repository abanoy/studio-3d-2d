"""Read-only source stamps for the pinned Windows ownership review."""
from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
def stamp(path):
 data=Path(path).read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
value={'format':'has_source_import_process_ownership_readonly_audit_1','finding':'Completed preparation mapping is not explicitly released before SourceImport discards pid','scope':'Session-lifetime retained handles, not a demonstrated live-process/native-workflow failure','engine_revision':'89cea143987d564363e15d207438530651d943ac','primary_source':'https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/platform/windows/os_windows.cpp#L1449-L1566','reviewed_primary_functions':{'create_process':[1449,1489],'kill':[1491,1510],'is_process_running':[1517,1540],'get_process_exit_code':[1542,1565]},'local_sources':{name:stamp(ROOT/name) for name in ('src/source_import.gd','src/source_choice_dialog.gd','src/app.gd','tools/prepare_source.py')},'runtime_or_WinAPI_probe':False,'source_or_Git_mutation':False,'future_test_plan':'REVIEW.md','normal_WM_close':'Cooperative cancel then wait via pid; no ordinary-close orphan reproduced','direct_teardown':'No importer teardown hook/quit guard; uncovered path, no runtime repro'}
(BASE/'AUDIT.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
index={'format':'has_metadata_source_packet_index_1','files':[{'path':p.name,**stamp(p)} for p in sorted(BASE.iterdir()) if p.is_file() and p.name!='INDEX.json']}
(BASE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(BASE),'files':len(index['files']),'index_sha256':stamp(BASE/'INDEX.json')['sha256']},indent=2))

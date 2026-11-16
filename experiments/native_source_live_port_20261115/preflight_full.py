"""Read-only current-source and approved shared-tool preflight; no cleanup."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT=Path(__file__).resolve().parents[2]
HEAD='dbf0bc1145f74b5bbff814ec6a417ccd23ce0885'
LOCK=ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json'
assert hashlib.sha256(LOCK.read_bytes()).hexdigest()=='3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
spec=importlib.util.spec_from_file_location('has_stable_read_identity',ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
lock=json.loads(LOCK.read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
assert len(lock['runtime_executables'])==6
for name,expected in lock['runtime_executables'].items():
    assert reader.identity(Path(name))==expected,'Approved runtime identity differs: '+name
assert len(lock['sourceio_files'])==574 and reader.metadata_map(reader.SOURCEIO)==lock['sourceio_files']
assert len(lock['exporter_noncache_sources'])==120 and reader.metadata_map(Path(lock['exporter_root']),'exporter')==lock['exporter_noncache_sources']
files=[p for name in ('src','tests','tools','data','examples') for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
files += [ROOT/name for name in ('project.godot','main.tscn','run.py','launch.pyw')]
assert len(files)==1014
sources={p.relative_to(ROOT).as_posix():reader.identity(p)['sha256'] for p in sorted(files)}
result={'format':'has_native_leaf_increment_full_preflight_1','passed':True,'source_commit':HEAD,
        'functional_files':len(sources),'source_sha256':sources,'runtimes':6,'SourceIO_files':574,'exporter_sources':120,
        'all_shared_tool_identity_fields_preserved':True,'approved_lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
        'owner_review_or_original_inputs_modified':False,'process_query_or_runtime_launched':False,'cleanup_authorized':False,
        'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
target=ROOT/'output/native-leaf-dbf0bc1-full-preflight.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))

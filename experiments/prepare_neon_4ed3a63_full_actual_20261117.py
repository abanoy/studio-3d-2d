"""Read-only current candidate/tool preflight and a fresh canonical-run reservation."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
REV='4ed3a63b716f696daa1699a76443d6f1abb9b096'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW,text=True).strip()==REV
files=[p for d in ('src','tests','tools','data','examples') for p in (REVIEW/d).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
files += [REVIEW/n for n in ('project.godot','main.tscn','run.py','launch.pyw')]
assert len(files)==1029
assert subprocess.check_output(['git','diff','--name-only','--','src','tests','tools','data','examples','project.godot','main.tscn','run.py','launch.pyw'],cwd=REVIEW)==b''
lock=json.loads((ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json').read_bytes())
reader=ROOT/'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
spec=importlib.util.spec_from_file_location('neon_approved_input_reader',reader);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
for name,expected in lock['runtime_executables'].items():assert r.identity(Path(name))==expected,name
sourceio=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
assert r.metadata_map(sourceio)==lock['sourceio_files']
assert r.metadata_map(REVIEW/'output/dependencies'/sourceio.name)==lock['sourceio_files']
assert r.metadata_map(Path(lock['exporter_root']),'exporter')==lock['exporter_noncache_sources']
stage=json.loads((ROOT/'experiments/neon_windows_original_20261116/NATIVE_FIXTURE_STAGE.json').read_bytes())
for name,expected in stage['source_projects'].items():
    assert r.identity(ROOT/'output'/name)==expected and r.identity(REVIEW/'output'/name)==expected
runner=ROOT/'experiments/neon_windows_original_20261116/run_canonical_owned.ps1'
assert sha(runner)=='8a1c2195db1c06cf91910778a48182c825a4ad0ad3a7b3acde9f940ca68e3dc4'
folder=REVIEW/'output'/('windows-neon-4ed3a63-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
folder.mkdir(exist_ok=False)
packet=ROOT/'experiments/neon_windows_4ed3a63_20261117';packet.mkdir(exist_ok=False)
record={'format':'has_neon_corrected_full_windows_preparation_1','revision':REV,'checkout':str(REVIEW),'run_folder':str(folder),'runner':str(runner),'runner_sha256':sha(runner),'functional_source_files':1029,'approved_runtime_executables':6,'original_SourceIO574_and_owned_copy_preserved':True,'exporter120_preserved':True,'retained_native_fixture_files':36,'native_fixture_bytes':31109803,'expected_groups':158,'core_groups':36,'new_neon_workspace_checks':12504,'original_failed_full_preserved':True,'main_merged':False,'result':'UNRUN'}
sources={p.relative_to(REVIEW).as_posix():sha(p) for p in sorted(files)}
(folder/'preflight-source.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
(packet/'PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(folder/'preparation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))

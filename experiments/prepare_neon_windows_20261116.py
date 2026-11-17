"""Prepare a separate exact redesign checkout for the unchanged Windows verifier."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
REV='c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW,text=True).strip()==REV
assert subprocess.check_output(['git','diff','52f63c9..HEAD','--','tests'],cwd=REVIEW)==b''
lock=json.loads((ROOT/'experiments/replay_audio_fix_20261115/builder/input-lock.json').read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,row in lock['runtime_executables'].items():
    p=Path(name);assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
sourceio=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
target=REVIEW/'output/dependencies'/sourceio.name
assert not target.exists() and len(lock['sourceio_files'])==574
for name,row in lock['sourceio_files'].items():
    original=sourceio/name;destination=target/name
    assert sha(original)==row['sha256'] and original.stat().st_size==row['bytes']
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,destination)
    assert sha(destination)==row['sha256']
hecatia=ROOT/'output/owner-fixtures/hecatia.kra'
assert sha(hecatia)=='fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758'
folder=REVIEW/'output'/('windows-neon-c2d52ff-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
folder.mkdir(exist_ok=False)
packet=ROOT/'experiments/neon_windows_original_20261116';packet.mkdir(exist_ok=False)
body=(ROOT/'experiments/verification_runner/run_canonical_owned.ps1').read_text(encoding='utf-8-sig')
body=body.replace("$checkout='C:\\a\\Programming\\cloudflare\\has-acceptance-session-20261111'",f"$checkout='{REVIEW}'")
body=body.replace("$env:HYBRID_HECATIA_KRA=(Resolve-Path -LiteralPath 'output/owner-fixtures/hecatia.kra').Path",f"$env:HYBRID_HECATIA_KRA='{hecatia}'\n$env:HYBRID_NATIVE_FIXTURES='{ROOT/'output'}'\n$env:HYBRID_SOURCEIO='{target}'\n$env:HYBRID_GODOT='C:\\a\\tools\\Godot\\Godot_v4.6-stable_win64.exe'")
runner=packet/'run_canonical_owned.ps1';runner.write_text(body,encoding='utf-8',newline='\n')
record={'format':'has_neon_original_windows_preparation_1','revision':REV,'checkout':str(REVIEW),'run_folder':str(folder),'runner':str(runner),'runner_sha256':sha(runner),'SourceIO_copied_files':574,'native_fixtures_read_from':str(ROOT/'output'),'hecatia_sha256':sha(hecatia),'tests_changed':False,'branch_source_changed':False,'full_windows_result':'UNRUN','known_source_review_findings':'Simple simulation entry points hidden and F11 shortcut precedence; no fix applied before this original-branch run.'}
(packet/'PREPARATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(folder/'preparation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))

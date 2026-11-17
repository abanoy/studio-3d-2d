"""Stage exact retained native fixture projects for the redesign's full suite."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
roles=('pose-smoke/miku-project','source-smoke/source-project','sfm-smoke/project')
rows=[]
def identity(p):return {'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for role in roles:
    source=ROOT/'output'/role;assert source.is_dir() and (source/'project.json').is_file()
    for original in sorted(source.rglob('*')):
        if not original.is_file():continue
        assert not original.is_symlink()
        name=original.relative_to(ROOT/'output').as_posix();target=REVIEW/'output'/name
        assert target.resolve().is_relative_to((REVIEW/'output').resolve()) and not target.exists()
        rows.append((name,original,target,identity(original)))
assert len(rows)==36 and sum(r[3]['bytes'] for r in rows)==31109803
for name,original,target,before in rows:
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
    assert identity(original)==before and identity(target)==before
record={'format':'has_neon_retained_native_fixture_stage_1','roles':list(roles),'files':36,'bytes':31109803,'source_preserved':True,'exact_size_mtime_sha_copies':True,'source_projects':{n:r for n,_,_,r in rows},'private_art_publication':False,'original_first_full_optional_skips_preserved':True}
target=ROOT/'experiments/neon_windows_original_20261116/NATIVE_FIXTURE_STAGE.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in record.items() if k!='source_projects'}))

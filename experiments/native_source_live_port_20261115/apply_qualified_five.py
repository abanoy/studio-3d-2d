"""Promote the reviewed qualified five-rule runtime and its exact test successors."""
from pathlib import Path
import datetime,hashlib,json,stat
ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/source_native_five_promotion_review_20261116'
STAGE=ROOT/'output/native-five-stage-attempt3/Studio'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def code(p):return '\n'.join(x for x in p.read_text(encoding='utf-8').splitlines() if x.strip() and not x.lstrip().startswith('#'))
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def functional():
    paths=[p for n in ('src','tests','tools','data','examples') for p in (ROOT/n).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts]
    paths += [ROOT/n for n in ('main.tscn','project.godot','run.py','launch.pyw')]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
assert sha(PACKET/'INDEX.json')=='0450b2d840b2a7ba91f95b5f1b97329d2eb7deeafcadb32f2000317b382d0e9f'
index=load(PACKET/'INDEX.json');rows=index['files']
entries=rows.items() if isinstance(rows,dict) else ((x['path'],x) for x in rows)
for name,row in entries:
    p=PACKET/name;assert p.resolve().is_relative_to(PACKET.resolve()) and not p.is_symlink()
    assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
review=load(PACKET/'REVIEW.json');assert len(review['promotion_files'])==10
assert load(STAGE.parent/'TRANSVERSE-ROOT-EXECUTION/verification.json')['passed']
assert sha(STAGE.parent/'ROOT-PRESERVATION-qualified-102.json')=='6f0d28ad749dfef5d72dc4174e9f2f755124ce4e73bc0b7a928bf8fdf3f044f1'
before=functional();assert len(before)==1014
for row in review['promotion_files']:
    name=row['path'];p=ROOT/name;source=PACKET/'proposed'/name
    assert p.resolve().is_relative_to(ROOT.resolve()) and sha(source)==row['proposed_sha256'] and source.stat().st_size==row['bytes']
    old=review['source_before'][name]
    if old is None:assert not p.exists()
    else:
        assert p.is_file() and not p.is_symlink() and p.stat().st_nlink==1
        assert sha(p)==old['sha256'] and p.stat().st_size==old['bytes']
    if 'qualified_stage_sha256' in row:
        assert sha(STAGE/name)==row['qualified_stage_sha256']
        assert (code(source)==code(STAGE/name)) if row['runtime_equivalent_comment_only'] else (source.read_bytes()==(STAGE/name).read_bytes())
for name in ('tests/helper_preview_port_files.json','tests/wind_review_port_files.json'):
    old=(ROOT/name).read_bytes();new=(PACKET/'proposed'/name).read_bytes()
    a=b'e351c0f5e2be18c33793a0ae6234b049095c923b35ca8ec1c6c7aaeb36bb8b6a';b=b'3a76f0c72ad72ef0d5c6762fe293f25b23bb61f8b19f72dfeaaf4cec95001801'
    assert old.count(a)==2 and old.replace(a,b)==new
folder=ROOT/'output/native-five-promotion-applied';folder.mkdir()
save(folder/'source-before.json',before)
for row in review['promotion_files']:(ROOT/row['path']).write_bytes((PACKET/'proposed'/row['path']).read_bytes())
after=functional();assert len(after)==1019
changed={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
assert changed=={r['path'] for r in review['promotion_files']}
assert all(after[r['path']]==r['proposed_sha256'] for r in review['promotion_files'])
save(folder/'source-after.json',after)
record={'format':'has_qualified_five_main_promotion_1','passed':True,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'packet_index_sha256':sha(PACKET/'INDEX.json'),'promoted_paths':sorted(changed),'functional_files_before':1014,'functional_files_after':1019,
    'runtime_equivalent_to_qualified_stage':True,'qualified_state_checks':266,'qualified_GUI_checks':102,
    'main_UI_and_full_test_rerun_claimed':False,'fresh_full_default_required':True,'source_before_sha256':sha(folder/'source-before.json'),'source_after_sha256':sha(folder/'source-after.json')}
save(folder/'verification.json',record);print(json.dumps(record))

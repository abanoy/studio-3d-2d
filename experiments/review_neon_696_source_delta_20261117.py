"""Record root's bounded source review; never qualifies a full run or merge."""
from pathlib import Path
import hashlib,json,datetime,subprocess
ROOT=Path(__file__).resolve().parent.parent
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel):return (ROOT/rel).read_bytes()
oldraw=read('experiments/neon_source52_to_00bf_root_review_20261117/REVIEWED52_TO_CANDIDATE_DELTA.json')
assert sha(oldraw)=='c90ed31bc8fd9b9d753661e666c3e7b618e52f3cdec178a4bd4cde1a58fc1614'
old=json.loads(oldraw)
draftpath='experiments/neon_source52_to_696_delta_draft_20261117/DRAFT52_TO_696_DELTA.json'
raw=read(draftpath);d=json.loads(raw)
assert sha(raw)=='9bd1763a50922d5e3a025e99066e6eb07fadec8278df5d880ca3fc861eea2db7'
assert d['candidate_manifest_commit']=='696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
three={'src/app.gd','tests/helper_preview_port_files.json','tests/wind_review_port_files.json'}
prior={r['path']:r for r in old['rows']};now={r['path']:r for r in d['rows']}
assert set(prior)==set(now) and len(now)==38
assert {p for p in now if now[p]!=prior[p]}==three
for p in now:
    assert d['reasons'][p].startswith('DRAFT: ')
    if p not in three:assert d['reasons'][p][7:]==old['reasons'][p]
assert d['raw_EOL_only_differences_excluded_from_delta_rows']==old['raw_EOL_only_differences_excluded_from_delta_rows']
git=['git','-C',str(REVIEW)]
app0=subprocess.check_output(git+['show','00bf0f916a549f5e858cb39dd91a149071fd5181:src/app.gd'])
app1=subprocess.check_output(git+['show','696ca7f1491a43b1a2267a53f8ca0f62b7c211a9:src/app.gd'])
anchor=b'\tif scene_view:scene_view.sync()\r\n'
assert app0.count(anchor)==1 and app1==app0.replace(anchor,anchor+b'\trefresh_camera_inspector()\r\n')
for name in ('tests/helper_preview_port_files.json','tests/wind_review_port_files.json'):
    a=json.loads(subprocess.check_output(git+['show','00bf0f916a549f5e858cb39dd91a149071fd5181:'+name]))
    b=json.loads(subprocess.check_output(git+['show','696ca7f1491a43b1a2267a53f8ca0f62b7c211a9:'+name]))
    row=next(r for r in a['files'] if r['path']=='src/app.gd')
    row['sha256']='79b34e7d591f433e060edf72888d22443d1a0fc5e22dd2a246eb77c83fcad1b6'
    row['lf_sha256']='79f340cc797738d205a3030f12339b1e74ed765edb557235a98c42282056328a'
    assert a==b
d['review_status']='ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA'
d['activation_status']='UNREADY_FULL_RELEASE_AND_MERGE_REQUIRED'
d['reasons_status']='ROOT_CONTENT_REVIEWED'
d['root_metadata_checkpoint_label_root_reported']='4fd'
d['reasons']={p:s[7:] for p,s in d['reasons'].items()}
d['root_review']={
 'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_delta_review_only':True,
 'review_basis':'Prior root-reviewed 00bf per-file reasons remain exact for 35 paths. Independently inspected 696 Git diff and proved exact single synchronous camera-inspector refresh plus only two app raw/LF pin replacements. Focused camera 60/0, Neon 12504/0 and controls 48/0 already passed. Current full remains required.',
 'draft_sha256':sha(raw),'prior_review_sha256':sha(oldraw),
 'full_PASS_release_merge_owner_copy_or187_supplied':False,
 'native_core_distinction':'Model and SceneIO raw exact; SourceBindings canonical exact with EOL-only raw difference. Native-to52 exact-core witness remains separate.'}
out=ROOT/'experiments/neon_source52_to_696_root_review_20261117'
out.mkdir(exist_ok=False)
def write(n,b):(out/n).write_bytes(b)
write('REVIEWED52_TO_CANDIDATE_DELTA.json',(json.dumps(d,indent=2)+'\n').encode())
write('README.md',b'# Root source review for candidate 696\n\nThe 38 explicit source changes are reviewed. The 107 EOL-only differences remain separate. This does not supply full PASS, release, merge, owner-copy or 187-check qualification.\n')
files=[]
for p in sorted(out.iterdir()):files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
write('INDEX.json',(json.dumps({'format':'has_source_review_packet_1','files':files},indent=2)+'\n').encode())
print(json.dumps({'files':len(files),'INDEX_sha256':sha((out/'INDEX.json').read_bytes()),'review_sha256':sha((out/'REVIEWED52_TO_CANDIDATE_DELTA.json').read_bytes()),'full_or_merge_qualified':False}))

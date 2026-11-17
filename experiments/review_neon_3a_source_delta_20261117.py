"""Root source review only; full result, merge and copy remain separate gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
sha=lambda b:hashlib.sha256(b).hexdigest()
oldraw=(ROOT/'experiments/neon_source52_to_696_root_review_20261117/REVIEWED52_TO_CANDIDATE_DELTA.json').read_bytes()
assert sha(oldraw)=='4ae44f24c02fc0fb801dc792e1b2025541e478beea6387c51f0fdefacf072ff6'
folder=ROOT/'experiments/neon_source52_to_3a_delta_draft_20261117'
assert sha((folder/'INDEX.json').read_bytes())=='b0ce3924dcab5d34bacd661753f24431b552b1e7ebaf056712fe2450aade20aa'
raw=(folder/'DRAFT52_TO_3A_DELTA.json').read_bytes();assert sha(raw)=='5222bc45dd75aabe8c8f3385f6f909aab73e52d00e51fe42c1483481111bc020'
old=json.loads(oldraw);d=json.loads(raw);name='tests/color_sampler_smoke.gd'
previous={r['path']:r for r in old['rows']};current={r['path']:r for r in d['rows']}
assert len(previous)==38 and len(current)==39 and set(current)-set(previous)=={name}
for p in previous:
 assert current[p]==previous[p] and d['reasons'][p]=='DRAFT: '+old['reasons'][p]
assert d['raw_EOL_only_differences_excluded_from_delta_rows']==old['raw_EOL_only_differences_excluded_from_delta_rows']
git=['git','-C',str(REVIEW),'show']
a=subprocess.check_output(git+['696ca7f1491a43b1a2267a53f8ca0f62b7c211a9:'+name])
b=subprocess.check_output(git+['3a3701ab6edfa81dc883759403c170b8555aab07:'+name])
anchor=b'picker.arm();click(native_point);await settled()'
assert a.count(anchor)==1 and b==a.replace(anchor,b'picker.arm();click(native_point+Vector2(.5,.5));await settled()',1)
assert [x for x in a.splitlines() if b'check(' in x]==[x for x in b.splitlines() if b'check(' in x]
assert d['candidate_manifest_commit']=='3a3701ab6edfa81dc883759403c170b8555aab07'
d['review_status']='ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA';d['reasons_status']='ROOT_CONTENT_REVIEWED'
d['activation_status']='UNREADY_FULL_RELEASE_AND_MERGE_REQUIRED'
d['reasons']={p:s.removeprefix('DRAFT: ') for p,s in d['reasons'].items()}
d['root_review']={'observed_utc':datetime.now(timezone.utc).isoformat(),'source_delta_review_only':True,
 'basis':'Prior 38 root-reviewed rows/reasons and EOL-only list are exact. The new color-fixture row is the independently measured same-pixel center correction: exact one Git call-site delta and identical assertion lines; original44/0 and three-case passive diagnostic passed. Full3a remains running.',
 'draft_sha256':sha(raw),'prior_review_sha256':sha(oldraw),'full_PASS_release_merge_owner_copy_or187_supplied':False}
out=ROOT/'experiments/neon_source52_to_3a_root_review_20261117';out.mkdir(exist_ok=False)
(out/'REVIEWED52_TO_CANDIDATE_DELTA.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
(out/'README.md').write_text('Root reviewed the explicit39 canonical source changes and separate107 EOL-only differences. This source review supplies no full PASS, release, merge, copy or187 result.\n',encoding='utf-8')
rows=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(out.iterdir())]
(out/'INDEX.json').write_text(json.dumps({'format':'has_root_source_review_packet_1','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'INDEX_sha256':sha((out/'INDEX.json').read_bytes()),'review_sha256':sha((out/'REVIEWED52_TO_CANDIDATE_DELTA.json').read_bytes()),'canonical_rows':39,'full_or_merge_claimed':False}))

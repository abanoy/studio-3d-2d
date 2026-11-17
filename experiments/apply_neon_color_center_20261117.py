"""Root applies one reviewed test-input correction; application code is unchanged."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[1];REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
packet=ROOT/'experiments/neon_color_sampler_pixel_center_proposal_20261117'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(packet/'INDEX.json')=='46d8ac7d77f5af550cef292e52d01f6d2bfa4ad69a62e556492a406c659a58e6'
for row in json.loads((packet/'INDEX.json').read_bytes())['files']:
 assert sha(packet/row['path'])==row['sha256'] and (packet/row['path']).stat().st_size==row['bytes']
spec=importlib.util.spec_from_file_location('root_center_proposal',packet/'proposal.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
target=REVIEW/'tests/color_sampler_smoke.gd';raw=target.read_bytes();new=p.corrected_test(raw)
assert hashlib.sha256(new).hexdigest()=='102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
target.write_bytes(new)
paragraph='''
### November 17, 2026 — native color fixture targets pixel centers

The 696 full passed camera60/0 then failed color44/1. Root closed93 private jobs,
source1029 unchanged, release17:42:05Z. An unchanged-assertion diagnostic reproduced
the color failure: all capture/view/world/source operands passed, while float
mapping put the intended integer-boundary click one row above the expected pixel.
The picked color exactly matched that actual neighboring pixel. The Source case
also shifted one row, hidden by matching neighbor color; the third case was exact.

Only the native fixture click now aims half a pixel inside the SAME expected
pixel. Expected image indices, all44 runtime assertions, thresholds, three native
cases and application source remain unchanged. The source inverse and independent
peer review pass. Actual corrected focus and a new frozen full remain required;
no full PASS, product merge or new owner copy is claimed.
'''
for name in ('LLM.md','docs/REDESIGN-PORT.md'):
 with (REVIEW/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
record={'test_before_sha256':hashlib.sha256(raw).hexdigest(),'test_after_sha256':sha(target),'proposal_INDEX_sha256':sha(packet/'INDEX.json'),'application_code_changed':False,'original_checks_and_thresholds_preserved':True,'actual_focus_unrun':True,'full_PASS_or_merge_claimed':False}
(ROOT/'experiments/neon_color_center_root_application_20261117.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))

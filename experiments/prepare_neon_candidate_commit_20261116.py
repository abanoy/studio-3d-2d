"""Install the sealed standard regressions and commit the reviewed candidate only."""
from pathlib import Path
import ast,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
PACKET=ROOT/'experiments/neon_workspace_suite_integration_20261117'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PACKET/'INDEX.json')=='c0ce762dbb8bf01754a028adb73351a27cfac3d8b67b6cce679a3f5ee2ef18f8'
rows=json.loads((PACKET/'INDEX.json').read_bytes())['files']
if isinstance(rows,dict):rows=[{'path':n,**v} for n,v in rows.items()]
for row in rows:assert sha(PACKET/row['path'])==row['sha256']
assert sha(REVIEW/'src/app.gd')=='88871ebd831d5a466b31336282a9bb53f264653dd5ff299fb10dc90a3080dd67'
assert sha(REVIEW/'src/workspace_layout.gd')=='7d194eaf03d03b909fa0caaf84c197f91e8fb29af95f2978ae5f8d798e3dfe8b'
production=['tests/verify_neon_workspace.py','tests/neon_behavior_regression.gd','tests/neon_inset_scene_regression.gd','tests/neon_compact_timeline_reveal_smoke.gd','tests/neon_rail_placement_smoke.gd']
for name in production:
    if (REVIEW/name).exists():assert (REVIEW/name).read_bytes()==(PACKET/name).read_bytes()
    else:(REVIEW/name).write_bytes((PACKET/name).read_bytes())
old_verify=(REVIEW/'tests/verify.py').read_bytes()
new_verify=(PACKET/'tests/verify.proposed.py').read_bytes()
assert hashlib.sha256(new_verify).hexdigest()=='14e6fc7b7e8c914b301e8e5d4d590ca0b2398a7abbd65cac0f6159f99de96048'
ast.parse(new_verify.decode('utf-8-sig'));(REVIEW/'tests/verify.py').write_bytes(new_verify)
note='''\n## Windows review — November 16, 2026

The owner requested this review before merging. Original branch commit
`c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2` was tested on Windows with the approved
Godot4.6/private-desktop runner. The first complete verifier stopped at object
timing:28 checks,2 failures. Its old input scrolled to the end of all lanes,
putting the last model above the new62px track viewport. The successor reveals
the requested model row by its geometry; every original assertion remains.
The failed run, unchanged source map and24 physically closed jobs are retained.

Source review and real input checks found and corrected four regressions:
idle Simple simulation tools were hidden; unmodified F11 overrode a saved user
shortcut; a faded toast intercepted canvas clicks; the timeline cache retained
deleted/prior-project model dictionaries. The original focused probe executed
32 checks with13 failures. Corrections preserve the neon look and restore the
existing Simple simulation strip, including fan/loose-parts/wind/recording access.
Assigned F11 has priority; unassigned F11 still toggles fullscreen. Faded toast
input is ignored without clearing status text. Cache entries are bounded to live rows.

World's icon rail is now limited to its supported solitary left placement.
Right, nested, tabbed and floating placements retain the full hierarchy list.
The narrow-right/nested/floating/persisted-layout regression passes45 checks.
Inset camera mapping passes12384 checks across576 configurations, with maximum
projection error0.000790571px and ray error2.25e-7. Compact first/middle/last model
clicks with drawing/audio lanes below them pass14 checks. The corrected existing
Windows UI smoke passes23 checks and preserves Simple/Advanced render identity.

The final32-check behavior probe passes. Two intermediate32/1 fixture results
and a diagnostic are preserved: a successful empty-scene click publishes a NEW
Camera hint, and a later click can publish another. The final test measures
refresh's faded-message state before the click, then independently requires the
actual canvas event; it never waits after refresh to mask a resurrection.

The strict wind manifest updates only the reviewed app/pose hash rows. Its
16-file scope,14 other rows and original94/845 predicates remain unchanged.
The standard verifier gains one guarded `neon_workspace` group with all four
regressions (12475 checks). Existing36 core entries remain unchanged.

This is a reviewed candidate, not yet merged. The fresh complete corrected
Windows verifier remains the final gate. Original native fixtures and earlier
review builds are protected; no human acceptance result is inferred.
'''
for name in ('docs/REDESIGN-PORT.md','LLM.md'):
    if '## Windows review — November 16, 2026' not in (REVIEW/name).read_text(encoding='utf-8'):
        with (REVIEW/name).open('a',encoding='utf-8',newline='\n') as f:f.write(note)
files=['src/app.gd','src/workspace_layout.gd','tests/object_timing_smoke.gd','tests/wind_review_port_files.json','tests/verify.py','docs/REDESIGN-PORT.md','LLM.md',*production]
existing=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=REVIEW).decode().strip('\0').split('\0'))-{''}
assert existing.issubset(set(files))
subprocess.run(['git','add','--',*files],cwd=REVIEW,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
actual=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=REVIEW).decode().strip('\0').split('\0'))
assert actual==set(files)
subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=REVIEW,check=True)
subprocess.run(['git','commit','-q','-m','Preserve studio controls and input in the Neon Pro redesign'],cwd=REVIEW,check=True)
record={'format':'has_reviewed_neon_windows_candidate_1','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW,text=True).strip(),'base':'c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2','changed_files':len(files),'main_merged':False,'full_corrected_windows_suite':'UNRUN'}
target=ROOT/'experiments/neon_windows_original_20261116/CANDIDATE_COMMIT.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))

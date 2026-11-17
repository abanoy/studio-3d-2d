from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
expected={'tests/animated_channels_smoke.gd':'2714a15589dfe9175518ea04e002b9898ab160eb4fe9dac760b790957a546e4a','tests/movement_path_smoke.gd':'b2c7d1131d291df99290f1ad5bd2327ff6716c8cbbeb903041fcd32544676ae4','tests/waveform_levels_smoke.gd':'847279d94ad0b42b3efc733b34ca4ff9538b0501e5d6268597c1039b9b739fab'}
for name,digest in expected.items():assert hashlib.sha256((REVIEW/name).read_bytes()).hexdigest()==digest
note='''\n### Windows focused fixture follow-up (November17UTC)

The381 complete verifier stopped at animated native channels47/1; all1028
functional files stayed unchanged. Root audited27 closed private jobs and the
exact coordinator/Python birth identities, then released only the failed lease.
Its raw failure and all three executed MMD/GMod/SFM fixtures remain recorded.

The native-channel successor scrolls the requested channel into view and adds
a pre-click visibility assertion. All original assertions remain;48/0 passes
with all three native rigs. Older standalone movement fixtures also assumed
lower channels were already visible and used a stale eager cel.image field.
Those original errors are retained. Revealing each channel and using the current
mutable drawing accessor passes both legacy/component profiles:34UI+13unit each.
The Drawing API and original test were already identical in main52f; this was
preexisting focused fixture code, not a new production Drawing change.

Waveform checks reveal Audio before pixel capture and keep Classic467d45,
four transients and RGB tolerance.02. A first Neon palette expectation failed
14/1 because a fractional clip border is antialiased, rather than opaque.
Diagnostic-only output preserved every predicate and identified the unmatched
first transient. The source-derived Godot4.6 straight-edge feather expectation
uses live geometry, with explicit unscaled/non-HDR/non-MSAA/raster guards.
Both Neon and Classic now pass15/0, four visible bars; all13 original checks
remain and bounds/raster guards add2. No expected color was taken from pixels,
no tolerance/count was widened, and production colors/layout did not change.

These focused results do not replace a complete default. The next frozen commit
must run all158groups before merge; manual owner review remains deferred.
'''
for name in ('docs/REDESIGN-PORT.md','LLM.md'):
    if '### Windows focused fixture follow-up (November17UTC)' not in (REVIEW/name).read_text(encoding='utf-8'):
        with (REVIEW/name).open('a',encoding='utf-8',newline='\n') as f:f.write(note)
files=[*expected,'docs/REDESIGN-PORT.md','LLM.md']
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REVIEW)==b''
subprocess.run(['git','add','--',*files],cwd=REVIEW,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
staged=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=REVIEW).decode().strip('\0').split('\0'));assert staged==set(files)
subprocess.run(['git','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],cwd=REVIEW,check=True)
subprocess.run(['git','commit','-q','-m','Reveal compact timeline test targets and validate themed waveform pixels'],cwd=REVIEW,check=True)
record={'format':'has_neon_focused_fixture_followup_commit_1','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REVIEW,text=True).strip(),'parent':'381d5a974d34eb4dc10208a44c1a54d178c72fbb','changed_fixture_sha256':expected,'production_source_changed_by_followup':False,'full_successor':'UNRUN','main_merged':False}
target=ROOT/'experiments/neon_windows_candidate_20261117/FIXTURE_FOLLOWUP_COMMIT.json'
with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))

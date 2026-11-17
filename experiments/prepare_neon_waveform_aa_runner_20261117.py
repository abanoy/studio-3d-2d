from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
body=(ROOT/'experiments/run_neon_waveform_palette_profiles_20261117.py').read_text(encoding='utf-8')
for before,after in {
 "FOLDER=REVIEW/'output/neon-waveform-palette-profiles-20261117-attempt1'":"FOLDER=REVIEW/'output/neon-waveform-aa-profiles-20261117-attempt1'",
 "neon_waveform_palette_successor_20261117/waveform_levels_smoke.proposed.gd":"neon_waveform_aa_successor_20261117/waveform_levels_smoke.proposed.gd",
 "assert sha(source)=='9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66'":"assert sha(source)=='847279d94ad0b42b3efc733b34ca4ff9538b0501e5d6268597c1039b9b739fab'",
 "assert sha(target)=='2333fb6e213e2d74d7aa71fb845d6bb23e2038f034b6dd98ee94958d18964b2f'":"assert sha(target)=='9775d5a497b64025fc93d958aa1a900316288b5fb2fb7fb34f77f3340ec3aa66'",
 "'has_waveform_palette_profile_execution_1'":"'has_waveform_aa_profile_execution_1'"}.items():
    assert body.count(before)==1;body=body.replace(before,after)
target=ROOT/'experiments/run_neon_waveform_aa_profiles_20261117.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(json.dumps({'driver':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))

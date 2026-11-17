from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
original=ROOT/'experiments/run_neon_timeline_successors_20261117.py'
body=original.read_text(encoding='utf-8')
for before,after in {
 "FOLDER=REVIEW/'output/neon-timeline-successors-20261117-attempt1'":"FOLDER=REVIEW/'output/neon-timeline-successors-20261117-attempt2'",
 "neon_movement_fixture_managed_raster_20261117/movement_path_smoke.proposed.gd":"neon_movement_fixture_managed_raster_20261117/movement_path_smoke.gd",
 "    for name,source in replacements.items():":"    assert sha(replacements['tests/waveform_levels_smoke.gd'])==proof['proposed_sha256']\n    for name,source in replacements.items():"}.items():
    assert body.count(before)==1;body=body.replace(before,after)
target=ROOT/'experiments/run_neon_timeline_successors_v2_20261117.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
print(json.dumps({'driver':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'prior_pre_native_refusal':'Wrong movement draft filename; prior before-closure evidence retained; no source or engine mutation before refusal'}))

"""Stage only the explicit reviewed source/evidence increment; preserve dirty outputs."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
files=['LLM.md','docs/NEXT_SESSION_PLAN_2026-11-15.md','docs/RESUME_MASTER_PLAN.md','docs/completion_checklist.json','docs/completion_checklist.md','docs/progress_memo.md',
    'docs/benchmarks/native_source_chains_2026-11-15.json','docs/benchmarks/native_five_initial_2026-11-15.json','docs/benchmarks/native_five_qualified_2026-11-15.json',
    'docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json','docs/benchmarks/world_selection_runtime_snapshot_2026-11-15.json',
    'src/physics_editor.gd','src/secondary_live.gd','src/source_secondary.gd','src/source_chain_math.gd',
    'tests/helper_preview_port_files.json','tests/wind_review_port_files.json','tests/test_owner_review_snapshot.py','tests/verify_world_selection_teardown.py',
    'tests/source_native_five_capture.gd','tests/source_native_five_live_ui.gd','tests/source_native_five_state_unit.gd','tests/verify_source_native_five_live.py','tools/build_owner_review_snapshot.py']
folders=['native_five_initial_actual_20261116','native_five_performance_candidate_20261115','native_five_performance_followup_20261115',
    'native_five_promotion_actual_20261116','native_five_qualified_actual_20261116','native_five_full_preflight_20261116','native_source_live_port_20261115',
    'runtime_snapshot_repair_actual_20261115','six_foot_import_basis_plan_20261115','source_native_chains_actual_20261115','source_native_chains_packaging_audit_20261115',
    'source_native_deep_chains_20261115','source_native_five_opposite_diagnostic_20261116','source_native_five_port_candidate_20261115','source_native_five_port_candidate_v2_20261115',
    'source_native_five_promotion_review_20261116','source_native_five_transverse_fixture_20261116','source_normal_followup_plan_20261115',
    'world_selection_runtime_snapshot_20261115','world_selection_runtime_snapshot_v2_20261115']
for folder in folders:
    base=ROOT/'experiments'/folder;assert base.is_dir()
    files.extend(p.relative_to(ROOT).as_posix() for p in base.rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts)
files=sorted(set(files));assert all(not n.startswith('output/') and '__pycache__' not in n and not n.endswith('.pyc') for n in files)
records={n:{'bytes':(ROOT/n).stat().st_size,'sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest()} for n in files}
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()=='dbf0bc1145f74b5bbff814ec6a417ccd23ce0885'
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip(),'Pre-existing staged changes refused'
for start in range(0,len(files),100):subprocess.run(['git','add','--',*files[start:start+100]],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==r['sha256'] for n,r in records.items()),'Working bytes changed during staging'
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')[:-1]
assert set(staged)<=set(files) and not any(n.startswith('output/') or n.endswith('.pyc') for n in staged)
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
with (ROOT/'output/native-five-checkpoint-staged.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump({'format':'has_explicit_five_checkpoint_staging_1','staged_files':len(staged),'reviewed_paths':records,'staged_paths':staged,'dirty_outputs_preserved':True},f,indent=2);f.write('\n')
print(json.dumps({'staged_files':len(staged),'reviewed_files':len(files),'dirty_outputs_preserved':True}))

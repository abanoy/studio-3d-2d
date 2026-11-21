from pathlib import Path
import hashlib,json,stat
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';DEST=ROOT/'experiments/continuation_sources_20261121'
assert (DEST/'BUILDING.json').is_file()
rows=[]
def copy(path,name):
    info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not getattr(info,'st_file_attributes',0)&0x400
    raw=path.read_bytes();raw.decode('utf-8-sig')
    target=DEST/name;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert target.read_bytes()==raw
    else:
        with target.open('xb') as stream:assert stream.write(raw)==len(raw)
    assert path.read_bytes()==raw and target.read_bytes()==raw
    rows.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
sources=[
 'verify_ui_camera_remote_20261121.py','verify_full182_root_20261121.py',
 'remove_verified_first_headless_stage_20261121.ps1','retire_miku171_prelaunch_lock_20261121.ps1',
 'prepare_editor_camera_review_20261121.py','run_easing_headless_20261121.py','prepare_easing435_port_20261121.py',
 'easing435_app_headless.gd','easing435_app_headless_v2.gd','easing435_graphical_smoke.gd',
 'run_easing435_app_headless_20261121.py','run_easing435_app_headless_v2_20261121.py',
 'prepare_easing435_undo_fix_20261121.py','run_easing435_app_headless_v3_20261121.py','run_easing_undo_fix_headless_20261121.py',
 'append_live_pickup_20261121.py','prepare_import_off_followup_20261121.py','prepare_import_off_followup_v2_20261121.py',
 'prepare_import_off_followup_v3_20261121.py','preserve_failed_full435_20261121.py','apply_import_off_followup_20261121.py',
 'run_import_off_followup_scoped_20261121.py','fix_first_movie_repeat_off_20261121.py',
 'run_import_off_followup_remaining_20261121.py','fix_scenario_d_mask_coordinates_20261121.py',
 'run_import_off_scenario_d_scoped_20261121.py','diagnose_scenario_d_cold_20261121.py',
 'scenario_d_cold_diagnostic_20261121.gd','scenario_d_wire_probe_20261121.gd','apply_scenario_d_wire_20261121.py',
 'run_import_off_scenario_d_wire_scoped_20261121.py','collect_continuation_archive_20261121.py',
 'collect_continuation_archive_v2_20261121.py']
for name in sources:copy(OUT/name,'root-source/'+name)
proofs=[
 'UI_CAMERA_REMOTE_VERIFIED_20261121.json','UI_CAMERA_FULL_LAUNCH_ROOT_20261121.json','UI_CAMERA_REVIEW_PREPARED_20261121.json',
 'MIKU171_LOCK_RETIREMENT_FIRST_GUARD_REFUSAL_20261121.json','MIKU171_PRELAUNCH_LOCK_RETIRED_20261121.json',
 'HEADLESS_FIRST_VERIFIED_REMOVAL_20261121.json','IMPORT_OFF_FOLLOWUP_ADOPTION_20261121.json','SCENARIO_D_WIRE_ADOPTION_20261121.json',
 'FULL182_REGISTRATION_AUDIT_20261121.json','FULL182_AND_OWNER_REVIEW_READINESS_20261121.md',
 'LIVE_PICKUP_APPEND_20261121.json','FULL435_FAILURE_PICKUP_APPEND_20261121.json',
 'SCENARIO_D_COLD_INDEPENDENT_BITS_20261121.json','SCENARIO_D_COLD_INDEPENDENT_CHILD_BITS_20261121.json',
 'SCENARIO_D_COLD_SAMPLE_SOURCE_INSPECTION_20261121.json','JUNKO105_PREFLIGHT_IDENTITY_REFUSAL_20261121.json',
 'CONTINUATION_ARCHIVE_FIRST_REFUSAL_20261121.json']
for name in proofs:copy(OUT/name,'root-evidence/'+name)
for label,path in [
 ('easing69-original',ROOT.parent/'has-easing-headless-1795254145851799500/PUBLIC_RESULT.json'),
 ('easing88-original',ROOT.parent/'has-easing435-app-cpu-1795254384845561100/PUBLIC_RESULT.json'),
 ('easing-undo-reproduction-failed',ROOT.parent/'has-easing435-app-cpu-1795254695259497400/PUBLIC_RESULT.json'),
 ('easing96-fixed',ROOT.parent/'has-easing435-app-cpu-1795254761995523000/PUBLIC_RESULT.json'),
 ('easing69-fixed',ROOT.parent/'has-easing-headless-1795254831934151300/PUBLIC_RESULT.json'),
 ('easing-graphics-parse-only',ROOT.parent/'has-easing435-graphics-parse-1795258322734840400/RESULT.json'),
 ('bounds43-root-repeat',OUT/'source-posed-head-render-bounds-prep-20261121/cpu-stage-1795254562029164300/CPU_RESULT.json'),
 ('off-scoped-first-failed',OUT/'import-off-followup-scoped-1795256301357827900/completion.json'),
 ('off-scoped-second-failed',OUT/'import-off-followup-scoped-1795256474017879900/completion.json'),
 ('scenario-d-cold-first-failed',OUT/'import-off-followup-scoped-1795256798459581600/completion.json'),
 ('scenario-d-final-pass',OUT/'import-off-followup-scoped-1795258730224048700/completion.json'),
 ('scenario-d-cold-diagnostic',OUT/'scenario-d-cold-diagnostic-1795257075012458600/completion.json')]:
    copy(path,'root-evidence/results/'+label+'.json')
case=OUT/'import-off-followup-scoped-1795256798459581600/scenario-d-artifacts'
for name in ('cold-differences-diagnostic.json','wire-probe-result.json'):
    copy(case/name,'root-evidence/results/'+name)
for name in ('scenario-d-wire-probe-owned-20261121.log','scenario-d-wire-probe-owned-stdout-20261121.log','scenario-d-wire-probe-owned-stderr-20261121.log'):
    copy(OUT/name,'root-evidence/results/'+name)
for label,casepath in [
 ('off-first',OUT/'import-off-followup-scoped-1795256301357827900'),
 ('off-second',OUT/'import-off-followup-scoped-1795256474017879900'),
 ('scenario-d-mapping-fixed-cold-failed',OUT/'import-off-followup-scoped-1795256798459581600'),
 ('scenario-d-wire-pass',OUT/'import-off-followup-scoped-1795258730224048700')]:
    for path in sorted(casepath.rglob('*.log')):
        # Only explicit coordinator case logs and final wire unit; no native worker logs.
        relative=path.relative_to(casepath).as_posix()
        if relative in ('height/stdout.log','height/stderr.log','import-physics/stdout.log','import-physics/stderr.log',
          'first-movie/stdout.log','first-movie/stderr.log','scenario-d/stdout.log','scenario-d/stderr.log','scenario-d-artifacts/wire-unit.log'):
            copy(path,'root-evidence/scoped/'+label+'/'+relative)
result={'format':'has_continuation_root_evidence_collection_1','status':'COLLECTED_NOT_FINALIZED','files':rows,'count':len(rows),'bytes':sum(r['bytes'] for r in rows)}
(OUT/'CONTINUATION_ROOT_EVIDENCE_COLLECTION_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='files'}))

"""CPU/source audit and packet seal; never import or launch the GDScript/app."""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REVIEW=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff')
sha=lambda data:hashlib.sha256(data).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists(),'Never rewrite a sealed packet'
    proof=json.loads((HERE/'SOURCE_PROOF.json').read_bytes())
    checks={}
    def mark(name,ok):
        assert name not in checks
        checks[name]=bool(ok)
        assert ok,name
    draft=(HERE/'draft/src/app.gd').read_bytes()
    source=(REVIEW/'src/app.gd').read_bytes()
    test=(HERE/'neon_behavior_regression.gd').read_text(encoding='utf-8')
    names=re.findall(r'\bcheck\("([^"]+)"',test)
    mark('32_unique_preregistered_regression_checks',len(names)==32 and len(set(names))==32)
    mark('regression_expected32', 'const EXPECTED_CHECKS := 32' in test)
    mark('regression_Gd_unrun',proof['gd_candidate_executed'] is False and proof['gd_candidate_parsed'] is False)
    mark('original_checkout_app_unchanged',sha(source)==proof['original_app_sha256'])
    mark('draft_app_exact_pin',sha(draft)==proof['candidate_app_sha256'])
    mark('draft_retains_CRLF_only',b'\r\n' in draft and b'\n' not in draft.replace(b'\r\n',b''))
    mark('only_six_narrow_edits',len(proof['edits'])==6)
    manifest=json.loads((HERE/'draft/tests/wind_review_port_files.json').read_bytes())
    original=json.loads((REVIEW/'tests/wind_review_port_files.json').read_bytes())
    mark('same16_ordered_paths_categories',[(x['path'],x['category']) for x in manifest['files']]==[(x['path'],x['category']) for x in original['files']] and len(manifest['files'])==16)
    changed=[new['path'] for old,new in zip(original['files'],manifest['files']) if old!=new]
    mark('only_app_pose_hash_rows_replaced',changed==['src/app.gd','src/pose_editor.gd'])
    for old,new in zip(original['files'],manifest['files']):
        if old['path'] not in changed:mark('unchanged_wind_manifest_row.'+old['path'],old==new)
    mark('all21_wind_lifecycle_methods_preserved',len(proof['unchanged_app_wind_lifecycle_methods'])==21 and all(proof['unchanged_app_wind_lifecycle_methods'].values()))
    mark('all41_old_pose_methods_preserved',len(proof['unchanged_pose_methods_except_setup'])==41 and all(proof['unchanged_pose_methods_except_setup'].values()))
    mark('original_wind_verifier_and_predicates_preserved',proof['wind_verifier_bytes_unchanged'] and not proof['old94unit_and845graphics_predicates_changed'])
    mark('original_runtime_hash_gate_accepts_successor',proof['pure_original_runtime_hash_gate_accepts_all16_candidate_rows'])
    mark('hash_gate_still_rejects_tamper',proof['same_hash_gate_rejects_unreviewed_byte'])
    for name,digest in proof['reviewed_files'].items():mark('review_source_unchanged.'+name,sha((REVIEW/name).read_bytes())==digest)
    mark('regression_checks_real_clicks','root.push_input(event,true)' in test and 'faded_toast_allows_real_canvas_click' in test)
    mark('regression_uses_real_timeout','await create_timer(6.3).timeout' in test)
    mark('regression_instruments_only_external_save_and_fullscreen', 'func save() -> void: observed_save_calls += 1' in test and 'func toggle_fullscreen() -> void: observed_fullscreen_calls += 1' in test and 'func _ready()' not in test)
    mark('regression_exercises_actual_world_delete_reset','app.remove_world_object(fan_id)' in test and 'app.new_project()' in test)
    audit={'format':'has_neon_redesign_source_review_audit_1','passed':all(checks.values()),'checks':len(checks),
        'named_checks':checks,'regression_names':names,'regression_gd_parsed':False,'regression_gd_run':False,
        'root_original_full_run_is_separate':True,'engine_or_CIM_run_by_child':False,'review_checkout_edited':False,'main_source_edited':False}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    rows=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.gd','.py','.json','.md','.patch'} and '__pycache__' not in path.parts,path
        rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':rows,'file_count':len(rows),
        'bytes':sum(r['bytes'] for r in rows),'excludes':['INDEX.json'],'owner_art_or_media_included':False,
        'review_revision':proof['reviewed_revision'],'candidate_not_applied':True,'runtime_execution_claimed':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'source_checks':len(checks),'regression_checks_planned':len(names),'index_sha256':sha((HERE/'INDEX.json').read_bytes()),
        'regression_sha256':sha((HERE/'neon_behavior_regression.gd').read_bytes()),'files':len(rows),'bytes':index['bytes']}))


if __name__=='__main__':main()

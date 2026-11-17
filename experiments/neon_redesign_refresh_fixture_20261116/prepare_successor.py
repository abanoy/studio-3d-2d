"""Prepare diagnostics and a strict fixture successor; do not run an engine."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/neon_redesign_review_20261116'
ACTUAL=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff/output/neon-behavior-candidate-20261116-attempt1')
sha=lambda data:hashlib.sha256(data).hexdigest()

HELPER='''func trace_toast(label: String, point: Vector2) -> void:
\tvar hovered := root.gui_get_hovered_control()
\tvar row := {"label":label,"status_text":app.status.text,"status_serial":app.status_serial,"status_faded":app.status_faded,"toast_alpha":app.toast.modulate.a,"toast_mouse_filter":app.toast.mouse_filter,"toast_visible":app.toast.is_visible_in_tree(),"toast_rect":str(app.toast.get_global_rect()),"canvas_rect":str(app.canvas.get_global_rect()),"scene_rect":str(app.canvas.scene_rect()),"sample_point":str(point),"point_inside_toast":app.toast.get_global_rect().has_point(point),"point_inside_canvas":app.canvas.get_global_rect().has_point(point),"hovered_control":str(hovered.get_path()) if hovered else "","pointer_presses":pointer_presses}
\ttoast_diagnostics.append(row)
\tprint("NEON_TOAST_DIAGNOSTIC "+JSON.stringify(row))

'''


def write(name,data):
    (HERE/name).write_text(data,encoding='utf-8',newline='\n')


def main():
    original=(OLD/'neon_behavior_regression.gd').read_text(encoding='utf-8')
    assert sha((OLD/'neon_behavior_regression.gd').read_bytes())=='40a2fae5485cdf08feb7abd2a3303a1cd92650a3785fcd842d7e94ea55a3a020'
    assert sha((OLD/'INDEX.json').read_bytes())=='f7a9f4f3a73155395aaf4ad4699b2d7df875757f9169132dee9afef0b298e873'
    diagnostic=original.replace('var pointer_presses := 0','var pointer_presses := 0\nvar toast_diagnostics: Array = []')
    diagnostic=diagnostic.replace('func run() -> void:',HELPER+'func run() -> void:')
    old='''\tvar observed := pointer_presses
\tawait click_point(point)
\tcheck("faded_toast_allows_real_canvas_click",pointer_presses == observed+1)
\tapp.refresh_workspace(); await settled()
\tobserved = pointer_presses
\tawait click_point(app.toast.get_global_rect().get_center())
\tcheck("workspace_refresh_keeps_canvas_clickthrough",pointer_presses == observed+1)'''
    new='''\tvar observed := pointer_presses
\tvar first_click_serial: int = app.status_serial
\ttrace_toast("before_first_faded_click",point)
\tawait click_point(point)
\ttrace_toast("after_first_faded_click",point)
\tprint("NEON_FIRST_CLICK_CONTEXT "+JSON.stringify({"before_serial":first_click_serial,"after_serial":app.status_serial,"new_message":app.status_serial != first_click_serial}))
\tcheck("faded_toast_allows_real_canvas_click",pointer_presses == observed+1)
\ttrace_toast("before_workspace_refresh",app.toast.get_global_rect().get_center())
\tapp.refresh_workspace(); await settled()
\ttrace_toast("after_workspace_refresh",app.toast.get_global_rect().get_center())
\tobserved = pointer_presses
\tawait click_point(app.toast.get_global_rect().get_center())
\ttrace_toast("after_second_click",app.toast.get_global_rect().get_center())
\tcheck("workspace_refresh_keeps_canvas_clickthrough",pointer_presses == observed+1)'''
    assert diagnostic.count(old)==1
    diagnostic=diagnostic.replace(old,new)
    diagnostic=diagnostic.replace('"save_and_fullscreen_actions_instrumented":true,','"save_and_fullscreen_actions_instrumented":true,"toast_diagnostics":toast_diagnostics,')
    diagnostic=diagnostic.replace('res://experiments/neon_redesign_review_20261116/neon_behavior_regression.gd',f'res://experiments/{HERE.name}/neon_behavior_diagnostic.gd')
    write('neon_behavior_diagnostic.gd',diagnostic)
    corrected=diagnostic.replace(f'{HERE.name}/neon_behavior_diagnostic.gd',f'{HERE.name}/neon_behavior_regression.gd')
    before='\ttrace_toast("before_workspace_refresh",app.toast.get_global_rect().get_center())'
    after='''\t# A successful empty-scene selection can publish a NEW camera hint through change_mode.
\t# Let that new message finish its own normal fade BEFORE testing refresh on faded state.
\tif app.status_serial != first_click_serial:
\t\ttrace_toast("new_context_message_after_first_click",app.toast.get_global_rect().get_center())
\t\tawait create_timer(6.3).timeout
\t\tawait settled()
\tvar before_refresh_serial: int = app.status_serial
\tvar before_refresh_text: String = app.status.text
\tvar before_refresh_faded: bool = app.status_faded and app.toast.modulate.a == 0.0
\ttrace_toast("before_workspace_refresh",app.toast.get_global_rect().get_center())'''
    assert corrected.count(before)==1
    corrected=corrected.replace(before,after)
    old_check='\tcheck("workspace_refresh_keeps_canvas_clickthrough",pointer_presses == observed+1)'
    strengthened='\tcheck("workspace_refresh_keeps_canvas_clickthrough",before_refresh_faded and app.status_faded and app.toast.modulate.a == 0.0 and app.status_serial == before_refresh_serial and app.status.text == before_refresh_text and pointer_presses == observed+1)'
    assert corrected.count(old_check)==1
    corrected=corrected.replace(old_check,strengthened)
    write('neon_behavior_regression.gd',corrected)
    statements=lambda text:re.findall(r'^\tcheck\((.*)\)$',text,re.M)
    original_checks=statements(original)
    diagnostic_checks=statements(diagnostic)
    corrected_checks=statements(corrected)
    assert len(original_checks)==len(diagnostic_checks)==len(corrected_checks)==32
    assert original_checks==diagnostic_checks
    differences=[(a,b) for a,b in zip(original_checks,corrected_checks) if a!=b]
    assert len(differences)==1 and differences[0][0].startswith('"workspace_refresh_keeps_canvas_clickthrough"')
    assert 'pointer_presses == observed+1' in differences[0][1]
    write('DIAGNOSTIC_ONLY_DIFF.patch',''.join(difflib.unified_diff(original.splitlines(True),diagnostic.splitlines(True),fromfile='original/neon_behavior_regression.gd',tofile='neon_behavior_diagnostic.gd')))
    write('FIXTURE_CORRECTION_DIFF.patch',''.join(difflib.unified_diff(diagnostic.splitlines(True),corrected.splitlines(True),fromfile='neon_behavior_diagnostic.gd',tofile='neon_behavior_regression.gd')))
    failed=HERE/'failed_predecessor';failed.mkdir(exist_ok=True)
    for name in ['verification.json','app-process.json','parse-process.json','after-closure.json','app-stdout.log']:
        shutil.copyfile(ACTUAL/name,failed/name)
    shutil.copyfile(ACTUAL/'app-result/result.json',failed/'result.json')
    actual=json.loads((failed/'result.json').read_bytes())
    assert actual['checks']==32 and actual['failures']==1
    assert [name for name,value in actual['named_checks'].items() if not value]==['workspace_refresh_keeps_canvas_clickthrough']
    proof={'format':'has_neon_refresh_fixture_successor_source_1','old_index_sha256':sha((OLD/'INDEX.json').read_bytes()),
        'old_script_sha256':sha((OLD/'neon_behavior_regression.gd').read_bytes()),
        'diagnostic_script_sha256':sha((HERE/'neon_behavior_diagnostic.gd').read_bytes()),
        'corrected_fixture_script_sha256':sha((HERE/'neon_behavior_regression.gd').read_bytes()),
        'diagnostic_predicates32_byte_text_identical':original_checks==diagnostic_checks,
        'corrected_31_predicates_byte_text_identical':len(differences)==1,
        'remaining_predicate_strengthened_retaining_actual_click':True,
        'extra_wait_precedes_refresh_not_follows_refresh':corrected.index('if app.status_serial != first_click_serial:')<corrected.index('app.refresh_workspace(); await settled()'),
        'actual_old_candidate_checks':32,'actual_old_candidate_failures':1,
        'actual_old_result_sha256':sha((failed/'result.json').read_bytes()),
        'actual_old_status_payload_available':False,'new_gd_parsed':False,'new_gd_executed':False,
        'product_source_edited':False,'main_source_edited':False}
    write('SOURCE_PROOF.json',json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()

"""Move status assertions to the refresh boundary; no product/engine operation."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/neon_redesign_refresh_fixture_20261116'
ACTUAL=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff/output/neon-behavior-fixture-20261116-attempt1')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists(),'Do not mutate a sealed successor'
    assert sha(OLD/'INDEX.json')=='1cb0ad92edf90d414354943c9790311d0c31261bf733c7725caae25b2d540711'
    assert sha(OLD/'neon_behavior_regression.gd')=='8ee51d41d0719f5a5a29281d50c9be594d35c1c1534d0790b855fe16cbc0fc1c'
    original=(OLD/'neon_behavior_regression.gd').read_text(encoding='utf-8')
    source=original.replace(OLD.name,HERE.name)
    boundary='\tapp.refresh_workspace(); await settled()\n\ttrace_toast("after_workspace_refresh",app.toast.get_global_rect().get_center())'
    captured='''\tapp.refresh_workspace(); await settled()
\t# Snapshot refresh invariants BEFORE another real click legitimately publishes a new hint.
\tvar refresh_preserved_faded_context: bool = app.status_faded and app.toast.modulate.a == 0.0 and app.status_serial == before_refresh_serial and app.status.text == before_refresh_text
\ttrace_toast("after_workspace_refresh",app.toast.get_global_rect().get_center())'''
    assert source.count(boundary)==1
    source=source.replace(boundary,captured)
    old_check='\tcheck("workspace_refresh_keeps_canvas_clickthrough",before_refresh_faded and app.status_faded and app.toast.modulate.a == 0.0 and app.status_serial == before_refresh_serial and app.status.text == before_refresh_text and pointer_presses == observed+1)'
    new_check='\tcheck("workspace_refresh_keeps_canvas_clickthrough",before_refresh_faded and refresh_preserved_faded_context and pointer_presses == observed+1)'
    assert source.count(old_check)==1
    source=source.replace(old_check,new_check)
    source=source.replace('"toast_diagnostics":toast_diagnostics,','"toast_diagnostics":toast_diagnostics,"refresh_preserved_faded_context":refresh_preserved_faded_context,')
    (HERE/'neon_behavior_regression.gd').write_text(source,encoding='utf-8',newline='\n')
    (HERE/'V3_BOUNDARY_DIFF.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),source.splitlines(True),fromfile='v2/neon_behavior_regression.gd',tofile='v3/neon_behavior_regression.gd')),encoding='utf-8',newline='\n')
    predicates=lambda text:re.findall(r'^\tcheck\((.*)\)$',text,re.M)
    a,b=predicates(original),predicates(source)
    assert len(a)==len(b)==32
    changed=[(x,y) for x,y in zip(a,b) if x!=y]
    assert len(changed)==1 and changed[0]==(old_check.strip()[6:-1],new_check.strip()[6:-1])
    capture_at=source.index('var refresh_preserved_faded_context: bool')
    refresh_at=source.index('app.refresh_workspace(); await settled()')
    second_click_at=source.index('await click_point(app.toast.get_global_rect().get_center())')
    assert refresh_at<capture_at<second_click_at
    assert 'create_timer' not in source[refresh_at:second_click_at]
    result=json.loads((ACTUAL/'app-result/result.json').read_bytes())
    assert result['checks']==32 and result['failures']==1 and result['script_sha256']=='8ee51d41d0719f5a5a29281d50c9be594d35c1c1534d0790b855fe16cbc0fc1c'
    observations={row['label']:row for row in result['toast_diagnostics']}
    before=observations['before_workspace_refresh'];after=observations['after_workspace_refresh'];clicked=observations['after_second_click']
    preserved=(before['status_faded'] is True and after['status_faded'] is True and before['toast_alpha']==after['toast_alpha']==0 and
        before['status_serial']==after['status_serial'] and before['status_text']==after['status_text'])
    actual_click=clicked['pointer_presses']==after['pointer_presses']+1
    assert preserved and actual_click and clicked['status_serial']==after['status_serial']+1 and clicked['status_faded'] is False
    failed=HERE/'failed_v2';failed.mkdir(exist_ok=True)
    for name in ['verification.json','app-process.json','parse-process.json','after-closure.json','app-stdout.log']:
        shutil.copyfile(ACTUAL/name,failed/name)
    shutil.copyfile(ACTUAL/'app-result/result.json',failed/'result.json')
    proof={'format':'has_neon_refresh_boundary_v3_source_proof_1','v2_index_sha256':sha(OLD/'INDEX.json'),
        'v2_script_sha256':sha(OLD/'neon_behavior_regression.gd'),'v3_script_sha256':sha(HERE/'neon_behavior_regression.gd'),
        'named_check_count_unchanged':32,'other31_predicates_exact':True,
        'all_v2_refresh_invariants_captured_at_correct_boundary':True,'actual_canvas_increment_predicate_unchanged':True,
        'capture_after_refresh_before_second_click':refresh_at<capture_at<second_click_at,'no_wait_after_refresh':True,
        'actual_v2_result_sha256':sha(failed/'result.json'),'actual_v2_refresh_invariants_passed':preserved,
        'actual_v2_second_canvas_click_reached':actual_click,'actual_v2_second_click_authored_new_hint':True,
        'actual_v2_serial_before_refresh':before['status_serial'],'actual_v2_serial_after_refresh':after['status_serial'],
        'actual_v2_serial_after_click':clicked['status_serial'],'v3_parsed':False,'v3_run':False,
        'product_source_edits':False,'main_edits':False}
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    rows=[]
    for path in sorted(HERE.rglob('*')):
        if not path.is_file():continue
        assert path.suffix in {'.py','.gd','.md','.json','.patch','.log'} and '__pycache__' not in path.parts
        rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':rows,'file_count':len(rows),
        'bytes':sum(r['bytes'] for r in rows),'excludes':['INDEX.json'],'new_engine_execution_claimed':False,
        'main_or_product_edits':False,'owner_art_or_native_assets_included':False}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'script_sha256':sha(HERE/'neon_behavior_regression.gd'),
        'files':len(rows),'bytes':index['bytes'],'actual_v2_boundary_and_click_passed':preserved and actual_click}))


if __name__=='__main__':main()

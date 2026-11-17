"""Read-only review of c2d52ff; write proposed fixes only inside this experiment."""
from pathlib import Path
from copy import deepcopy
import ast
import difflib
import hashlib
import json
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REVIEW=Path(r'C:\a\Programming\cloudflare\has-neon-review-20261116-c2d52ff')
BASE='52f63c944ded7a651da871524d23a345b606424d'
HEAD='c2d52ff5fd0f9aeffae6a343f6d4b71698ed9ff2'
sha=lambda data:hashlib.sha256(data).hexdigest()


def committed(revision,path):
    # Git blob read only. Never checkout, reset, stage, commit or run an engine.
    return subprocess.check_output(['git','show',revision+':'+path],cwd=REVIEW)


def functions(data):
    lines=data.decode('utf-8').replace('\r\n','\n').splitlines()
    starts=[(i,re.match(r'^(?:static )?func (\w+)\(',line).group(1)) for i,line in enumerate(lines) if re.match(r'^(?:static )?func (\w+)\(',line)]
    result={}
    for index,(start,name) in enumerate(starts):
        end=starts[index+1][0] if index+1<len(starts) else len(lines)
        for at in range(start+1,end):
            if lines[at].strip() and not lines[at][0].isspace() and not lines[at].startswith('#'):
                end=at;break
        result[name]='\n'.join(line for line in lines[start:end] if line.strip() and not line.lstrip().startswith('#'))
    return result


def main():
    original=(REVIEW/'src/app.gd').read_bytes()
    assert original==committed(HEAD,'src/app.gd')
    current=original
    edits=[]
    def edit(name,before,after):
        nonlocal current
        # Preserve the branch's CRLF byte convention.
        old=before.replace('\n','\r\n').encode()
        new=after.replace('\n','\r\n').encode()
        assert current.count(old)==1,name
        current=current.replace(old,new)
        edits.append({'name':name,'before_sha256':sha(old),'after_sha256':sha(new)})
    edit('restore_existing_simple_simulation_entry_points',
        '\t# Codex\'s simulation strip: always in Advanced (and in classic Simple, as before). Neon Simple shows\n'
        '\t# it only while a simulation or recording runs, so the switches that stop it never disappear;\n'
        '\t# otherwise Pose\'s inspector mirrors Physics / Hair & clothes and the stage keeps one pill row.\n'
        '\t# The strip\'s recording, fans / wind and loose-parts controls are Advanced-only in neon Simple\n'
        '\t# (documented in docs/REDESIGN-PORT.md; showing the row shrinks the frame and the tool pill).\n'
        '\tif physics_bar == null: return\n'
        '\tvar show: bool = advanced_mode or stage_overlay == null or physics_live()\n'
        '\tif physics_bar.visible != show: physics_bar.visible = show',
        '\t# Preserve the existing Simple simulation entry points even while idle.\n'
        '\t# The neon stage inset already reserves space when this strip is visible.\n'
        '\tif physics_bar != null and not physics_bar.visible: physics_bar.visible = true')
    edit('respect_persisted_F11_binding_before_fullscreen',
        '\tif event.keycode == KEY_F11 and not event.ctrl_pressed and not event.alt_pressed and not event.shift_pressed:',
        '\tif event.keycode == KEY_F11 and not event.ctrl_pressed and not event.alt_pressed and not event.shift_pressed and not event.meta_pressed and preload("res://src/shortcut_bindings.gd").action(keyboard_shortcuts.bindings,event).is_empty():')
    edit('toast_refresh_input_matches_display_state',
        '\tstatus.visible = advanced_mode\n\ttoast_icon.visible = not advanced_mode',
        '\tstatus.visible = advanced_mode\n'
        '\t# Alpha does not remove a Control from hit testing. Only a displayed Simple toast needs a tooltip.\n'
        '\ttoast.mouse_filter = Control.MOUSE_FILTER_PASS if not advanced_mode and not status.text.is_empty() and not status_faded else Control.MOUSE_FILTER_IGNORE\n'
        '\ttoast_icon.visible = not advanced_mode')
    edit('toast_timeout_releases_canvas_input',
        '\t\t\tif toast: toast.modulate.a = 0.0\n\t\t\telse: status.self_modulate.a = 0.0)',
        '\t\t\tif toast:\n\t\t\t\ttoast.modulate.a = 0.0\n\t\t\t\ttoast.mouse_filter = Control.MOUSE_FILTER_IGNORE\n'
        '\t\t\telse: status.self_modulate.a = 0.0)')
    edit('timeline_cache_empty_world_clear',
        '\tif not renderer.world_runtime: return result\n\tfor row in renderer.world_runtime.data.objects:',
        '\tif not renderer.world_runtime:\n\t\ttimeline_key_cache.clear()\n\t\treturn result\n'
        '\tfor row in renderer.world_runtime.data.objects:')
    edit('timeline_cache_retains_only_current_world_rows',
        '\t\tresult[row.id] = cached[1]\n\treturn result\n\nfunc refresh_transport_text()',
        '\t\tresult[row.id] = cached[1]\n'
        '\t# Removed objects and old projects must not retain their complete data dictionaries here.\n'
        '\tfor id in timeline_key_cache.keys():\n\t\tif not result.has(id): timeline_key_cache.erase(id)\n'
        '\treturn result\n\nfunc refresh_transport_text()')
    draft=HERE/'draft/src/app.gd'
    draft.parent.mkdir(parents=True,exist_ok=True)
    draft.write_bytes(current)
    patch=''.join(difflib.unified_diff(original.decode().splitlines(True),current.decode().splitlines(True),fromfile='a/src/app.gd',tofile='b/src/app.gd'))
    (HERE/'PROPOSED_APP_FIXES.patch').write_bytes(patch.encode())
    proof=json.loads((REVIEW/'tests/wind_review_port_files.json').read_bytes())
    successor=deepcopy(proof)
    changed=[]
    rows=[]
    for row in successor['files']:
        name=row['path']
        old=committed(BASE,name)
        actual=(REVIEW/name).read_bytes()
        branch_blob=committed(HEAD,name)
        assert actual.replace(b'\r\n',b'\n')==branch_blob.replace(b'\r\n',b'\n'),name
        data=current if name=='src/app.gd' else actual
        old_row=next(item for item in proof['files'] if item['path']==name)
        assert sha(old)==old_row['sha256'] or sha(old.replace(b'\r\n',b'\n'))==old_row['lf_sha256'],name
        if sha(data)!=old_row['sha256'] and sha(data.replace(b'\r\n',b'\n'))!=old_row['lf_sha256']:
            changed.append(name)
            row['sha256']=sha(data)
            row['lf_sha256']=sha(data.replace(b'\r\n',b'\n'))
        rows.append({'path':name,'category':row['category'],'base_sha256':sha(old),'redesign_sha256':sha(actual),
            'candidate_sha256':sha(data),'unchanged_base_bytes':data==old,
            'unchanged_base_lf_bytes':data.replace(b'\r\n',b'\n')==old.replace(b'\r\n',b'\n')})
    assert changed==['src/app.gd','src/pose_editor.gd'] and len(rows)==16
    successor['neon_redesign_runtime_successor_provenance']='experiments/neon_redesign_review_20261116/SOURCE_PROOF.json'
    manifest=HERE/'draft/tests/wind_review_port_files.json'
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(successor,indent=2)+'\n',encoding='utf-8')
    manifest_patch=''.join(difflib.unified_diff((REVIEW/'tests/wind_review_port_files.json').read_text().splitlines(True),manifest.read_text().splitlines(True),fromfile='a/tests/wind_review_port_files.json',tofile='b/tests/wind_review_port_files.json'))
    (HERE/'PROPOSED_WIND_MANIFEST.patch').write_text(manifest_patch,encoding='utf-8',newline='\n')
    before=functions(committed(BASE,'src/app.gd'))
    after=functions(current)
    protected=['stop_local_wind','local_wind_display_active','local_wind_active','canvas_input','finish_stroke',
        'finish_camera_capture','release_mouse','project_snapshot','current_world','restore_world','append_object',
        'append_object_data','remove_world_object','reset_document','save','open_project','install_project_data',
        'export_frames','autosave_tick','complete_recovery_preview','_exit_tree']
    protected_checks={name:before[name]==after[name] for name in protected}
    assert all(protected_checks.values()),[name for name,ok in protected_checks.items() if not ok]
    pose_before=functions(committed(BASE,'src/pose_editor.gd'))
    pose_after=functions((REVIEW/'src/pose_editor.gd').read_bytes())
    pose_checks={name:body==pose_after[name] for name,body in pose_before.items() if name!='setup'}
    assert all(pose_checks.values()),[name for name,ok in pose_checks.items() if not ok]
    verifier=(REVIEW/'tests/verify_wind_review.py').read_bytes()
    assert verifier.replace(b'\r\n',b'\n')==committed(BASE,'tests/verify_wind_review.py').replace(b'\r\n',b'\n')
    # Execute only the verifier's unchanged pure hash gate against an in-memory candidate.
    class MemoryPath:
        def __init__(self,name=''):self.name=name
        def __truediv__(self,name):return MemoryPath(self.name+'/'+name if self.name else name)
        def read_bytes(self):return payloads[self.name]
    payloads={row['path']:(current if row['path']=='src/app.gd' else (REVIEW/row['path']).read_bytes()) for row in rows}
    payloads['tests/wind_review_port_files.json']=manifest.read_bytes()
    def require(ok,message):
        if not ok:raise RuntimeError(message)
    function=next(n for n in ast.parse(verifier).body if isinstance(n,ast.FunctionDef) and n.name=='runtime_hashes')
    environment={'ROOT':MemoryPath(),'json':json,'hashlib':hashlib,'ALLOW_EOL':True,'require':require}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'<unchanged hash gate>','exec'),environment)
    qualified=environment['runtime_hashes']()
    assert len(qualified)==16
    payloads['src/app.gd']+=b'\n# injected unreviewed byte\n'
    rejected=False
    try:environment['runtime_hashes']()
    except RuntimeError:rejected=True
    assert rejected
    delta={'format':'has_neon_redesign_source_review_proof_1','base_revision':BASE,'reviewed_revision':HEAD,
        'original_app_sha256':sha(original),'candidate_app_sha256':sha(current),'edits':edits,
        'original_wind_manifest_sha256':sha((REVIEW/'tests/wind_review_port_files.json').read_bytes()),
        'successor_wind_manifest_sha256':sha(manifest.read_bytes()),'wind_rows':rows,
        'wind_scope16_unchanged':True,'only_changed_wind_rows':changed,'wind_verifier_bytes_unchanged':True,
        'unchanged_app_wind_lifecycle_methods':protected_checks,'unchanged_pose_methods_except_setup':pose_checks,
        'pure_original_runtime_hash_gate_accepts_all16_candidate_rows':len(qualified)==16,
        'qualification_uses_existing_explicit_allow_checkout_eol':True,
        'same_hash_gate_rejects_unreviewed_byte':rejected,
        'old94unit_and845graphics_predicates_changed':False,'gd_candidate_parsed':False,'gd_candidate_executed':False,
        'review_checkout_edited':False,'main_source_edited':False,
        'reviewed_files':{name:sha((REVIEW/name).read_bytes()) for name in ['docs/REDESIGN-PORT.md','src/app.gd','src/studio_theme.gd','src/pose_editor.gd','tests/verify_wind_review.py']}}
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(delta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_app_sha256':sha(current),'manifest_sha256':sha(manifest.read_bytes()),
        'app_protected_methods':len(protected_checks),'pose_preserved_methods':len(pose_checks),'wind_rows':16,'tamper_refused':rejected}))


if __name__=='__main__':main()

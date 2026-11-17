"""Source-only two-file lifecycle proposal; never edits the review checkout."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
REVIEW=HERE.parents[1].parent/'has-neon-review-20261116-c2d52ff'
PINS={'world_selection.gd':'f37ef0081de1637025a129ab3e4d651bbb9915658555bc98837be3c6bea193d5',
      'workspace_layout.gd':'7d194eaf03d03b909fa0caaf84c197f91e8fb29af95f2978ae5f8d798e3dfe8b'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    proof={'format':'has_neon_world_teardown_source_proposal_1','status':'SOURCE_ONLY_UNPARSED_UNRUN','files':{}}
    for name,pin in PINS.items():
        raw=(REVIEW/'src'/name).read_bytes();assert sha(raw)==pin
        text=raw.decode();newline='\r\n' if b'\r\n' in raw else '\n';text=text.replace('\r\n','\n')
        replacements=[]
        def replace(before,after):
            nonlocal text
            assert text.count(before)==1,before
            position=text.index(before);text=text.replace(before,after,1);replacements.append((before,after,position))
        if name=='world_selection.gd':
            replace('var rail_end: Control\n','var rail_end: Control\nvar rail_ui_active := false\n')
            replace('func setup(parent: Node) -> void:\n','func _enter_tree() -> void:\n\trail_ui_active = true\n\nfunc setup(parent: Node) -> void:\n')
            anchor='func set_rail(on: bool, force := false) -> void:\n'
            replace(anchor,anchor+'\t# A dock resize may be delivered while its owner or Tree is leaving the scene.\n\tif not rail_ui_active or not is_inside_tree() or is_queued_for_deletion() or not is_instance_valid(app) or not app.is_inside_tree() or app.is_queued_for_deletion(): return\n\tif not is_instance_valid(tree) or not tree.is_inside_tree() or tree.is_queued_for_deletion(): return\n\tvar holder: Control = tree.get_parent()\n\tfor control in [holder,rail,rail_divider,rail_end,help_label] + actions:\n\t\tif not is_instance_valid(control) or not control.is_inside_tree() or control.is_queued_for_deletion(): return\n')
            replace('\tvar neon := StudioTheme.is_neon()\n\tvar holder: Control = tree.get_parent()\n','\tvar neon := StudioTheme.is_neon()\n')
            replace('func _exit_tree() -> void:\n\tserial+=1','func _exit_tree() -> void:\n\trail_ui_active = false\n\tserial+=1')
        else:
            replace('var world_rail := false\n','var world_rail := false\nvar world_mode_active := false\n')
            anchor='func refresh_world_mode(force:=false) -> void:\n\tif not panels.has("world") or not app or not app.world_selection:return\n'
            replace(anchor,'func refresh_world_mode(force:=false) -> void:\n\t# Sibling controls can still emit resized while their application is being dismantled.\n\tif not world_mode_active or not is_inside_tree() or is_queued_for_deletion() or not is_instance_valid(app) or not app.is_inside_tree() or app.is_queued_for_deletion():return\n\tif not panels.has("world") or not is_instance_valid(panels.world) or not panels.world.is_inside_tree() or panels.world.is_queued_for_deletion() or not is_instance_valid(app.world_selection) or not app.world_selection.is_inside_tree() or app.world_selection.is_queued_for_deletion():return\n')
            anchor='func _exit_tree() -> void:\n\tif timer and not timer.is_stopped():save()'
            connect='\tif panels.has("world") and is_instance_valid(panels.world) and not panels.world.is_queued_for_deletion() and not panels.world.resized.is_connected(refresh_world_mode):panels.world.resized.connect(refresh_world_mode)'
            disconnect='\tif panels.has("world") and is_instance_valid(panels.world) and panels.world.resized.is_connected(refresh_world_mode):panels.world.resized.disconnect(refresh_world_mode)'
            replace(anchor,'func _enter_tree() -> void:\n\tworld_mode_active = true\n\t# Reparenting a live application/layout restores its presentation signal exactly once.\n'+connect+'\n\tif panels.has("world"):call_deferred("refresh_world_mode",true)\n\nfunc _exit_tree() -> void:\n\tworld_mode_active = false\n\t# Disconnect before save() or later sibling removal can resize the old World panel.\n'+disconnect+'\n\tif timer and not timer.is_stopped():save()')
        inverse=text
        for before,after,position in reversed(replacements):
            assert inverse[position:position+len(after)]==after
            inverse=inverse[:position]+before+inverse[position+len(after):]
        assert inverse.replace('\n',newline).encode()==raw
        result=text.replace('\n',newline).encode()
        (HERE/(name+'.proposed')).write_bytes(result)
        diff=''.join(difflib.unified_diff(raw.decode().splitlines(True),result.decode().splitlines(True),fromfile='a/src/'+name,tofile='b/src/'+name))
        (HERE/(name+'.patch')).write_text(diff,encoding='utf-8',newline='')
        proof['files'][name]={'before_sha256':pin,'proposed_sha256':sha(result),'before_bytes':len(raw),'proposed_bytes':len(result),'original_line_endings_preserved':True,'exact_inverse_to_original':True,'replacement_blocks':len(replacements)}
    proof.update({'font_definitions_and_every_visual_setting_unchanged':True,'world_selection_pick_cleanup_unchanged':True,'workspace_exit_save_line_unchanged':True,
                  'wind_manifest_16_rows_unchanged_no_changed_runtime_row':True,'review_source_modified':False,'engines_CIM_Git_executed':False})
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof))


if __name__=='__main__':main()

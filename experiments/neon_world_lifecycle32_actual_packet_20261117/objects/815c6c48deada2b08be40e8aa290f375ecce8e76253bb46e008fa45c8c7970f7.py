"""Derive a standalone 32-check lifecycle source; no engine or review writes."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1]
SOURCE = MAIN / 'experiments/neon_world_lifecycle_integration_20261117/tests/neon_world_rail_lifecycle.gd'
PIN = 'f033f975735efe5089dbadb478661f620dceeca4a1328ce090638747c03df202'
ADDITION = '''func withheld_control_transaction() -> void:
	var app=await fresh_app("withheld")
	var ws=app.workspace_layout
	var selection=app.world_selection
	ws.reset();await settled()
	ws.horizontal.clamp_split_offset()
	ws.horizontal.split_offset+=int(roundf(64.0-ws.slots.left.size.x))
	ws.horizontal.clamp_split_offset();await settled()
	ws.refresh_world_mode(true)
	var before_layout: bool=ws.world_rail
	var before_selection: bool=selection.rail_mode
	var kept_help: Label=selection.help_label
	var saved_parent: Node=kept_help.get_parent()
	var saved_index: int=kept_help.get_index()
	saved_parent.remove_child(kept_help)
	var accepted: bool=selection.set_rail(false,true)
	check(before_layout and before_selection and not kept_help.is_inside_tree() and not accepted,"withheld help control makes the different-mode setter refuse explicitly")
	ws.dock("world","right")
	ws.refresh_world_mode(true)
	check(not ws.want_full_left() and ws.world_rail==before_layout and selection.rail_mode==before_selection,"refused right-dock transition preserves both accepted mode caches")
	print("NEON_WORLD_RAIL_TRANSACTION_STATE ",JSON.stringify({"phase":"withheld","setter_accepted":accepted,"requested_rail":false,"layout_rail":ws.world_rail,"selection_rail":selection.rail_mode,"help_inside":kept_help.is_inside_tree()}))
	saved_parent.add_child(kept_help);saved_parent.move_child(kept_help,saved_index)
	ws.refresh_world_mode(true)
	check(kept_help==selection.help_label and kept_help.get_parent()==saved_parent and kept_help.get_index()==saved_index and kept_help.is_inside_tree() and not ws.world_rail and not selection.rail_mode and selection.tree.visible,"same help control and index restored: one explicit refresh reaches the full World list")
	print("NEON_WORLD_RAIL_TRANSACTION_STATE ",JSON.stringify({"phase":"restored","requested_rail":false,"layout_rail":ws.world_rail,"selection_rail":selection.rail_mode,"tree_visible":selection.tree.visible,"help_inside":kept_help.is_inside_tree()}))
	app.free();await settled()

'''


def sha(raw):return hashlib.sha256(raw).hexdigest()


def functions(text):
    matches=list(re.finditer(r'^func (\w+)\(',text,re.M))
    return {match[1]:text[match.start():matches[i+1].start() if i+1<len(matches) else len(text)] for i,match in enumerate(matches)}


def main():
    assert not (HERE/'INDEX.json').exists()
    raw=SOURCE.read_bytes();assert sha(raw)==PIN
    text=raw.decode('utf-8').replace('\r\n','\n');proposed=text;changes=[]
    def replace(before,after):
        nonlocal proposed
        assert proposed.count(before)==1
        offset=proposed.index(before);proposed=proposed.replace(before,after,1);changes.append((before,after,offset))
    replace('func run() -> void:\n',ADDITION+'func run() -> void:\n')
    replace('\tawait reentry_and_fonts();await queued_owner();await immediate_owner()\n',
            '\tawait reentry_and_fonts();await queued_owner();await immediate_owner();await withheld_control_transaction()\n')
    replace('"format":"has_neon_world_rail_lifecycle_1"','"format":"has_neon_world_rail_transaction_lifecycle_1"')
    replace('"immediate-free-resize"],','"immediate-free-resize","withheld-control-transaction"],')
    replace('\tvar file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()\n\tprint("NEON_WORLD_RAIL_LIFECYCLE ",JSON.stringify(report));quit(0 if failures==0 else 1)\n',
            '\tvar encoded:=JSON.stringify(report,"",true,true)\n\tvar file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(encoded);file.close()\n\tprint("NEON_WORLD_RAIL_TRANSACTION_LIFECYCLE ",encoded);quit(0 if failures==0 else 1)\n')
    inverse=proposed
    for before,after,offset in reversed(changes):
        assert inverse[offset:offset+len(after)]==after
        inverse=inverse[:offset]+before+inverse[offset+len(after):]
    assert inverse==text
    old_functions=functions(text);new_functions=functions(proposed)
    assert set(new_functions)==set(old_functions)|{'withheld_control_transaction'}
    unchanged=[]
    for name,body in old_functions.items():
        if name!='run':assert new_functions[name]==body;unchanged.append(name)
    old_checks=[line for line in text.splitlines() if re.match(r'^\s*check\(',line)]
    assert all(proposed.splitlines().count(line)>=text.splitlines().count(line) for line in old_checks)
    assert len(re.findall(r'^\s*check\(',new_functions['withheld_control_transaction'],re.M))==3
    output=proposed.replace('\n','\r\n').encode('utf-8');assert b'\r\r\n' not in output
    target=HERE/'neon_world_rail_transaction_lifecycle.gd';assert not target.exists();target.write_bytes(output)
    proof={'status':'SOURCE_ONLY_STANDALONE_32_UNRUN','source_path':str(SOURCE),'source_sha256':PIN,
           'proposed_sha256':sha(output),'proposed_bytes':len(output),'exact_inverse_to_typed29':True,
           'old29_predicates_and_nonrun_functions_unchanged':unchanged,'old_check_lines_preserved':len(old_checks),
           'new_check_call_sites':3,'expected_runtime_checks':32,'formal_12504_integration_changed':False,
           'new_marker':'NEON_WORLD_RAIL_TRANSACTION_LIFECYCLE ',
           'new_format':'has_neon_world_rail_transaction_lifecycle_1',
           'same_child_parent_index_restored':True,'setter_boolean_result_checked':True,
           'cache_refusal_then_one_explicit_refresh_checked':True,'native_models_used':False,
           'engines_cim_git_run':False,'review_or_main_runtime_written':False}
    assert sha(SOURCE.read_bytes())==PIN
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()

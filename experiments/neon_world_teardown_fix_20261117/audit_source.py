"""CPU/source checks only; does not parse or execute GDScript."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REVIEW=HERE.parents[1].parent/'has-neon-review-20261116-c2d52ff'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def functions(text):
    matches=list(re.finditer(r'^func (\w+)\(',text,re.M));result={}
    for index,match in enumerate(matches):result[match[1]]=text[match.start():matches[index+1].start() if index+1<len(matches) else len(text)]
    return result


def main():
    assert not (HERE/'INDEX.json').exists(),'Do not regenerate sealed source evidence'
    proof=json.loads((HERE/'SOURCE_PROOF.json').read_bytes());unchanged={}
    for name,row in proof['files'].items():
        original=(REVIEW/'src'/name).read_bytes();proposed=(HERE/(name+'.proposed')).read_bytes()
        assert sha(original)==row['before_sha256'] and sha(proposed)==row['proposed_sha256']
        assert proposed.count(b'\r\n')==proposed.count(b'\r')==proposed.count(b'\n') and b'\r\r\n' not in proposed
        old=functions(original.decode().replace('\r\n','\n'));new=functions(proposed.decode().replace('\r\n','\n'))
        changed={'set_rail','_exit_tree'} if name=='world_selection.gd' else {'refresh_world_mode','_exit_tree'}
        assert set(new)==set(old)|{'_enter_tree'}
        retained=[key for key in old if key not in changed]
        assert all(old[key]==new[key] for key in retained)
        unchanged[name]=retained
        if name=='world_selection.gd':
            assert new['tree_font']==old['tree_font']
            assert new['_exit_tree'].replace('\trail_ui_active = false\n','',1)==old['_exit_tree']
            assert new['set_rail'].index('if not rail_ui_active')<new['set_rail'].index('rail_mode = on')
        else:
            assert new['_exit_tree'].index('world_mode_active = false')<new['_exit_tree'].index('.disconnect(')<new['_exit_tree'].index('save()\n')
            assert '.is_connected(refresh_world_mode)' in new['_enter_tree'] and 'call_deferred("refresh_world_mode",true)' in new['_enter_tree']
    fixture=(HERE/'neon_world_rail_lifecycle.gd').read_text()
    blocks=functions(fixture)
    count=lambda name:len(re.findall(r'\bcheck\(',blocks[name]))
    planned=count('font_profile')*4+sum(count(name) for name in ('reentry_and_fonts','queued_owner','immediate_owner'))
    assert planned==29
    ast.parse((HERE/'prepare.py').read_bytes());ast.parse(Path(__file__).read_bytes())
    result={'format':'has_neon_world_teardown_source_audit_1','status':'PASS_SOURCE_CHECKS_ONLY','unmodified_function_bodies':unchanged,'font_factory_byte_exact':True,'pick_cleanup_statements_byte_exact':True,'line_endings_and_exact_inverse_passed_by_preparation':True,'fixture_sha256':sha(fixture.encode()),'planned_Godot_checks':29,'Godot_parse_or_runtime_executed':False,'review_source_modified':False,'engines_CIM_Git_executed':False}
    (HERE/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_audit':'PASS','planned_checks':planned,'fixture_sha256':result['fixture_sha256']}))


if __name__=='__main__':main()

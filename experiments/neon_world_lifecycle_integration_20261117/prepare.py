"""Source-only fifth-case integration proposal; never writes the active checkout."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re
import gzip

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
FIXTURE=MAIN/'experiments/neon_world_lifecycle_typing_20261117/neon_world_rail_lifecycle.gd'
OLD_TEST=MAIN/'experiments/neon_workspace_suite_integration_20261117/cpu_tests/test_verify_neon_workspace.py'
PINS={'verify_neon_workspace.py':'45dbea477bf9445290fe6a5f52ad254f9dfb0178214037560570072cfe677cdb',
      'verify.py':'14e6fc7b7e8c914b301e8e5d4d590ca0b2398a7abbd65cac0f6159f99de96048',
      'neon_inset_scene_regression.gd':'1c7647a9f6b2a675759c54e8da902ccae2b642e522a087876514f448998c11dd',
      'neon_compact_timeline_reveal_smoke.gd':'bb7d14c88129ccfcc092eec5d7e1c0f73592b0f69d806f29a87aad374f05bd8c'}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    (HERE/'tests').mkdir(exist_ok=True);(HERE/'cpu_tests').mkdir(exist_ok=True)
    proof={'format':'has_neon_lifecycle_case_integration_source_1','status':'SOURCE_ONLY_ROOT_ACTUAL_LIFECYCLE_PENDING','files':{}}
    for name,pin in PINS.items():
        raw=(REVIEW/'tests'/name).read_bytes();assert sha(raw)==pin
        newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode().replace('\r\n','\n');changes=[]
        def replace(before,after):
            nonlocal text
            assert text.count(before)==1,before
            position=text.index(before);text=text.replace(before,after,1);changes.append((before,after,position))
        if name=='verify_neon_workspace.py':
            replace('The four standard\n','The five standard\n')
            anchor="    ('rail', 'tests/neon_rail_placement_smoke.gd', False, 45, 150),\n"
            replace(anchor,anchor+"    ('lifecycle', 'tests/neon_world_rail_lifecycle.gd', False, 29, 130),\n")
            replace("           'rail': 'NEON_RAIL_PLACEMENT '}","           'rail': 'NEON_RAIL_PLACEMENT ', 'lifecycle': 'NEON_WORLD_RAIL_LIFECYCLE '}")
            anchor="                'Rail fixture/output scope differs')\n"
            replace(anchor,anchor+"    elif name=='lifecycle':\n        required_cases=['theme-detach-reentry-reparent-free','queued-owner','immediate-free-resize']\n        required_keys={'format','checks','failures','cases','source_only_fixture_uses_native_models'}\n        # Validate both physical JSON and stdout independently: ordinary dict equality aliases bool/int.\n        for observed in (report,json.loads(lines[0])):\n            require(type(observed) is dict and set(observed)==required_keys and\n                    observed['format']=='has_neon_world_rail_lifecycle_1' and\n                    type(observed['checks']) is int and observed['checks']==29 and\n                    type(observed['failures']) is int and observed['failures']==0 and\n                    type(observed['cases']) is list and observed['cases']==required_cases and\n                    observed['source_only_fixture_uses_native_models'] is False,\n                    'Lifecycle format/case/native/result scope differs')\n")
            replace("require(set(reports)=={'inset','behavior','compact','rail'}, 'Incomplete workspace suite')","require(set(reports)=={row[0] for row in CASES}, 'Incomplete workspace suite')")
            replace('after all four actual results','after all five actual results')
        elif name=='verify.py':
            replace("'tests/verify_neon_workspace.py', '--lease-confirmed', '--parse-scripts'], timeout=960)","'tests/verify_neon_workspace.py', '--lease-confirmed', '--parse-scripts'], timeout=1200)")
            replace("{'inset':12384, 'behavior':32, 'compact':14, 'rail':45} and neon_result['checks'] == 12475","{'inset':12384, 'behavior':32, 'compact':14, 'rail':45, 'lifecycle':29} and neon_result['checks'] == 12504")
            replace("set(neon_result['reports']) == {'inset', 'behavior', 'compact', 'rail'}","set(neon_result['reports']) == {'inset', 'behavior', 'compact', 'rail', 'lifecycle'}")
        elif name=='neon_inset_scene_regression.gd':
            replace('\t\tif file: file.store_string(JSON.stringify(report,"",true,true)); file.close()','\t\tif file: file.store_string(encoded); file.close()')
            replace('\tprint("INSET_SCENE_REGRESSION " + JSON.stringify(report))','\tprint("INSET_SCENE_REGRESSION " + encoded)')
            anchor='\tvar args := OS.get_cmdline_user_args()\n'
            replace(anchor,'\tvar encoded := JSON.stringify(report,"",true,true)\n'+anchor)
        else:
            replace('\tfile.store_string(JSON.stringify(result,"",true,true));file.close()','\tfile.store_string(encoded);file.close()')
            replace('\tprint("COMPACT_TIMELINE_REVEAL " + JSON.stringify(result))','\tprint("COMPACT_TIMELINE_REVEAL " + encoded)')
            anchor='\tvar file := FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)\n'
            replace(anchor,'\tvar encoded := JSON.stringify(result,"",true,true)\n'+anchor)
        inverse=text
        for before,after,position in reversed(changes):
            assert inverse[position:position+len(after)]==after
            inverse=inverse[:position]+before+inverse[position+len(after):]
        assert inverse.replace('\n',newline).encode()==raw
        output=text.replace('\n',newline).encode()
        if name.endswith('.py'):ast.parse(output)
        else:
            assert [line for line in raw.decode().splitlines() if re.search(r'\bcheck\(',line)]==[line for line in output.decode().splitlines() if re.search(r'\bcheck\(',line)]
        (HERE/'tests'/name).write_bytes(output)
        (HERE/(name+'.patch')).write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),output.decode().splitlines(True),fromfile='a/tests/'+name,tofile='b/tests/'+name)),encoding='utf-8',newline='')
        proof['files'][name]={'before_sha256':pin,'proposed_sha256':sha(output),'before_bytes':len(raw),'proposed_bytes':len(output),'exact_inverse':True,'line_endings_preserved':True,'replacement_blocks':len(changes)}
    fixture=FIXTURE.read_bytes();assert sha(fixture)=='f033f975735efe5089dbadb478661f620dceeca4a1328ce090638747c03df202'
    original_fixture=(MAIN/'experiments/neon_world_teardown_fix_20261117/neon_world_rail_lifecycle.gd').read_bytes()
    assert fixture.count(b': WeakRef=weakref(')==6 and fixture.replace(b': WeakRef=weakref(',b':=weakref(')==original_fixture
    (HERE/'tests/neon_world_rail_lifecycle.gd').write_bytes(fixture)
    (HERE/'LIFECYCLE_TYPING_PROOF.json').write_bytes((FIXTURE.parent/'SOURCE_PROOF.json').read_bytes())
    old_tests=OLD_TEST.read_bytes();(HERE/'cpu_tests/test_verify_neon_workspace.py').write_bytes(old_tests)
    proof.update({'lifecycle_fixture_sha256':sha(fixture),'original_fixture_sha256':sha(original_fixture),'six_explicit_WeakRef_annotations_exact_inverse':True,'original29_lifecycle_predicates_unchanged':True,'original_20_CPU_tests_byte_exact':True,'old_CPU_test_sha256':sha(old_tests),'new_expected_checks':{'inset':12384,'behavior':32,'compact':14,'rail':45,'lifecycle':29},'new_total':12504,'original_four_CASE_rows_and_predicates_preserved':True,'aggregate_timeout_seconds':1200,'sum_of_all_parse_and_case_outer_bounds_seconds':1145,'full_result_groups_unchanged':158,'core_groups_unchanged':36,'movie_groups_unchanged':21,'new_functional_source_count_after_root_stage':1029,'product_runtime_files_changed_by_proposal':False,'REVIEW_modified_by_preparer':False,'engines_CIM_Git_executed':False})
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof))


if __name__=='__main__':main()

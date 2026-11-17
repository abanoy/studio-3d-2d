"""Prepare exact source/registry successor only; no run output is read here."""
from pathlib import Path
import ast
import copy
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
OLD=MAIN/'experiments/neon_f387_terminal_20261117'
BASE=MAIN/'experiments/current_full_receipts_20261116'
COMMIT='ffcf4c54ab9ab7af7cb01329a5b3b5b6f4589865'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def write(name,raw):
    with (HERE/name).open('xb') as stream:stream.write(raw)


def main():
    assert not (HERE/'INDEX.json').exists() and not (HERE/'CONTEXT.json').exists()
    original=(OLD/'close_terminal.py').read_bytes()
    assert sha(original)=='9b17e69f888e7866b8b4de03087de8cb76d14d56eeb29d006716508e8d7b19d5'
    legacy=(OLD/'legacy_result_gates.py').read_bytes()
    assert sha(legacy)=='0e5041bba2dd135c7580d32c46bbe3c02b3032fb072e0b64c9a3b918a6e11460'
    registry=json.loads((BASE/'RESULT_REGISTRY.json').read_bytes())
    old_verifier=(MAIN/'tests/verify.py').read_bytes()
    verifier=(REVIEW/'tests/verify.py').read_bytes()
    assert sha(old_verifier)==registry['verifier_sha256']
    assert sha(verifier)=='192aa4b889a367787f2368f58c95de5813628dbff80b01a5f7e640efdf1f2f0f'
    tree=ast.parse(verifier);stripped=copy.deepcopy(tree)
    body=next(n for n in stripped.body if isinstance(n,ast.FunctionDef) and n.name=='main').body
    start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='neon_started' for t in n.targets))
    removed=body[start:start+10];assert len(removed)==10
    del body[start:start+10]
    assert ast.dump(stripped,include_attributes=False)==ast.dump(ast.parse(old_verifier),include_attributes=False)
    registry.update(source_commit=COMMIT,verifier_sha256=sha(verifier),
                    derivation='Exact10-statement Neon AST inverse retains every original gate and157 keys; add neon_workspace only. Neon12504 includes lifecycle29.')
    registry['expected_result_keys']=sorted([*registry['expected_result_keys'],'neon_workspace'])
    assert len(registry['expected_result_keys'])==len(set(registry['expected_result_keys']))==158
    assert len(registry['expected_core_process_keys'])==36 and len(registry['expected_movie_keys'])==21
    changed=original;replacements=[]
    def replace(before,after):
        nonlocal changed
        assert changed.count(before)==1,before
        offset=changed.index(before);changed=changed.replace(before,after,1);replacements.append((before,after,offset))
    replace(b"counts={'inset':12384,'behavior':32,'compact':14,'rail':45}",b"counts={'inset':12384,'behavior':32,'compact':14,'rail':45,'lifecycle':29}")
    replace(b"row['checks']==12475",b"row['checks']==12504")
    replace(b"'has_neon_f387_terminal_receipt_inventory_1'",b"'has_neon_ffcf_terminal_receipt_inventory_1'")
    replace(b"'has_root_neon_f387_graphics_lease_release_1'",b"'has_root_neon_ffcf_graphics_lease_release_1'")
    replace(b"'launch.json','root-birth-observation.json','canonical.log')",b"'launch.json','root-birth-observation.json','root-birth-api-detail.json','canonical.log')")
    inverse=changed
    for before,after,offset in reversed(replacements):
        assert inverse[offset:offset+len(after)]==after
        inverse=inverse[:offset]+before+inverse[offset+len(after):]
    assert inverse==original;ast.parse(changed)
    tests=(OLD/'test_terminal.py').read_bytes()
    assert sha(tests)=='eb78c56a04199b847f0e608b2a50d0ed7fbff8c03459130167fe7e9597e7ff5d'
    tests=tests.replace(b"'rail':45},'checks':12475",b"'rail':45,'lifecycle':29},'checks':12504")
    tests=tests.replace(b"'compact':{},'rail':{}",b"'compact':{},'rail':{},'lifecycle':{}")
    tests=tests.replace(b"('checks',12474),('checks',12475.0)",b"('checks',12503),('checks',12504.0)")
    ast.parse(tests)
    write('close_terminal.py',changed);write('legacy_result_gates.py',legacy)
    write('test_terminal.py',tests)
    write('RESULT_REGISTRY.json',(json.dumps(registry,indent=2)+'\n').encode())
    proof={'status':'STATIC_SOURCE_SUCCESSOR_CONTEXT_NOT_YET_BOUND','old_helper_sha256':sha(original),
           'new_helper_sha256':sha(changed),'helper_five_splice_exact_inverse':True,
           'legacy_result_gates_sha256':sha(legacy),'legacy_entire_file_exact':True,
           'original157_registry_sha256':sha((BASE/'RESULT_REGISTRY.json').read_bytes()),
           'old_verifier_sha256':sha(old_verifier),'new_verifier_sha256':sha(verifier),
           'Neon10statement_AST_inverse_exact':True,'registry158_core36_movie21':True,
           'new_neon_checks':12504,'new_lifecycle_checks':29,'physical_job_count':'DERIVE_ACTUAL_NO_ASSUMPTION',
           'source_snapshot_expected':1029,'run_state_report_log_read':False,'engines_CIM_Git_executed':False}
    write('SOURCE_DERIVATION.json',(json.dumps(proof,indent=2)+'\n').encode())
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()

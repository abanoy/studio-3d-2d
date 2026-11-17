"""Hash and source-audit this packet without engine/process or main mutations."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=ROOT/'experiments/six_foot_import_basis_gd_candidate_20261116'
FAILED=ROOT/'output/six-foot-domain-20261116-attempt1'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists(), 'Never rewrite a sealed packet'
    old=(OLD/'basis_domain_unit.gd').read_text(encoding='utf-8')
    new=(HERE/'basis_domain_unit.gd').read_text(encoding='utf-8')
    ten=lambda text:text[text.index('\tvar sha :='):text.index('\tvar result :=')]
    auth=lambda text:text[text.index('func checked_job()'):text.index('func _initialize()')]
    dispatch=lambda text:text[text.index('\tfor row in corpus.rows:'):text.index('\t\tvar '+('raw_ok' if 'var raw_ok' in text else 'ok')+': bool')]
    checks={
        'old_index_exact':sha(OLD/'INDEX.json')=='921579101eb9e97feeb62e8f7b0f22a392fe6536fa8fa9006ecb58650ead7125',
        'encoder_entire_file_exact':(OLD/'import_basis_domain.gd').read_bytes()==(HERE/'import_basis_domain.gd').read_bytes(),
        'corpus_entire_file_exact':(OLD/'PARITY_CORPUS_v3.json').read_bytes()==(HERE/'PARITY_CORPUS_v3.json').read_bytes(),
        'ten_transform_checks_exact':ten(old)==ten(new),
        'root_authorization_checks_exact':auth(old)==auth(new),
        'all_operation_dispatch_exact':dispatch(old)==dispatch(new),
        'cpu59_pass':json.loads((HERE/'CPU_DIAGNOSIS.json').read_text(encoding='utf-8'))['checks']==59,
        'cpu_actual_success':json.loads((HERE/'CPU_DIAGNOSIS.json').read_text(encoding='utf-8'))['passed'] is True,
        'inline_comparator_matches_review_input':(HERE/'comparison_functions.gd.txt').read_text(encoding='utf-8') in new,
        'no_old_preload':OLD.name+'/' not in new,
        'new_same_folder_domain_preload':f'res://experiments/{HERE.name}/import_basis_domain.gd' in new,
    }
    old_index=json.loads((OLD/'INDEX.json').read_text(encoding='utf-8'))
    for row in old_index['files']:
        checks['old_payload_exact.'+row['path']]=sha(OLD/row['path'])==row['sha256']
    for path in (HERE/'failed_predecessor').iterdir():
        source=FAILED/'Studio/output/domain/result.json' if path.name=='result.json' else FAILED/path.name
        checks['failed_raw_copy_exact.'+path.name]=path.read_bytes()==source.read_bytes()
    assert all(checks.values()), [k for k,v in checks.items() if not v]
    diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile=str((OLD/'basis_domain_unit.gd').relative_to(ROOT)).replace('\\','/'),
        tofile=str((HERE/'basis_domain_unit.gd').relative_to(ROOT)).replace('\\','/')))
    (HERE/'HARNESS_ONLY_DIFF.patch').write_text(diff,encoding='utf-8',newline='\n')
    proof={'format':'has_six_foot_transport_source_proof_1','passed':True,'checks':len(checks),'named_checks':checks,
        'old_transform_check_block_sha256':hashlib.sha256(ten(old).encode()).hexdigest(),
        'new_transform_check_block_sha256':hashlib.sha256(ten(new).encode()).hexdigest(),
        'actual_gd_successor_execution_claimed':False,'main_source_edits':False}
    (HERE/'SOURCE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    files=[]
    allowed={'.py','.gd','.txt','.json','.md','.patch','.log'}
    for path in sorted(HERE.rglob('*')):
        if not path.is_file(): continue
        assert path.suffix in allowed, path
        assert '__pycache__' not in path.parts, path
        files.append({'path':str(path.relative_to(HERE)).replace('\\','/'),'bytes':path.stat().st_size,'sha256':sha(path)})
    index={'format':'has_source_experiment_index_1','packet':HERE.name,'files':files,'file_count':len(files),
        'bytes':sum(row['bytes'] for row in files),'excludes':['INDEX.json'],
        'owner_native_geometry_media_or_binary_assets_included':False,
        'actual_new_gd_execution':False,'main_edits':False,'source_proof_checks':len(checks)}
    (HERE/'INDEX.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'index_sha256':sha(HERE/'INDEX.json'),'files':len(files),'bytes':index['bytes'],'source_checks':len(checks),'passed':True}))


if __name__=='__main__': main()

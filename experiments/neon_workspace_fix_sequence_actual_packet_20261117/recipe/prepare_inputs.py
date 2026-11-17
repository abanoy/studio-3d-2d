"""Pin completed public UI metadata only; never inspect an active or future run."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
ROOTS={'main':MAIN,'review':REVIEW}
COMPLETED=(
 'neon-workspace-f387-baseline-20261117-attempt1',
 'neon-workspace-teardown-fixed-20261117-attempt1',
 'neon-workspace-font-cache-20261117-attempt1',
 'neon-world-lifecycle-20261117-attempt1',
 'neon-world-lifecycle-20261117-attempt2',
 'neon-workspace-font-cache-resize-20261117-attempt1',
 'neon-workspace-font-cache-docking-20261117-attempt1',
 'neon-workspace-font-cache-nested-20261117-attempt1',
 'neon-workspace-standard-12504-20261117-attempt1',
 'neon-rail-transaction-diagnostic-20261117-attempt1',
 'neon-workspace-transaction-20261117-attempt1',
)
NESTED=('neon-workspace/1794880616296073900-6ea8692c','neon-workspace/1794881110957686200-c64de60f','neon-workspace/1794881601549860200-0a4b7568')
CONTROL_CASES=('1794880124836778200','1794880375954100900','1794880601233539200')
CONTROL_RECEIPTS=('workspace_controls_smoke_dfe4f265026a40d88ad8a813a24aad0a.json',
 'workspace_controls_smoke_77671800f00448538ba348b51cea2950.json',
 'workspace_controls_smoke_3f2c1f0ab32a4329b4da771e8545cc76.json')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    assert not (HERE/'INDEX.json').exists()
    rows={};phases=[];receipts={}
    def add(path,label):
        path=Path(path).resolve();assert path.is_file() and not path.is_symlink()
        root_name=next(key for key,root in ROOTS.items() if path.is_relative_to(root.resolve()))
        assert path.suffix.lower() in ('.json','.log','.py','.gd','.md','.patch') and not path.name.startswith('PRIVATE')
        raw=path.read_bytes();assert len(raw)<=4*1024*1024;raw.decode('utf-8','strict')
        key=str(path)
        if key not in rows:rows[key]={'root':root_name,'path':path.relative_to(ROOTS[root_name]).as_posix(),'bytes':len(raw),'sha256':sha(raw),'gzip_exact_original':len(raw)>32768,'labels':[]}
        if label not in rows[key]['labels']:rows[key]['labels'].append(label)
        return raw
    def walk(value,label):
        if type(value) is dict:
            for key,item in value.items():
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]',item):
                    candidate=Path(item)
                    if candidate.suffix=='.json' and ('receipt' in key.lower() or candidate.name in ('private-receipt.json','private-desktop.json')):
                        raw=add(candidate,label+'.'+key);r=json.loads(raw)
                        if r.get('format')=='studio_private_desktop_1':receipts[str(candidate.resolve())]=r
                walk(item,label+'.'+key)
        elif type(value) is list:
            for index,item in enumerate(value):
                if item=='--receipt' and index+1<len(value):
                    raw=add(Path(value[index+1]),label+'.command_receipt');receipts[str(Path(value[index+1]).resolve())]=json.loads(raw)
                if type(item) is str and re.match(r'^[A-Za-z]:[\\/]',item) and Path(item).suffix=='.json' and 'receipt' in label.lower():
                    raw=add(Path(item),label+'.receipt_list');r=json.loads(raw)
                    if r.get('format')=='studio_private_desktop_1':receipts[str(Path(item).resolve())]=r
                walk(item,label+'['+str(index)+']')
    def metadata_tree(folder,label,recursive=False):
        for path in sorted(folder.rglob('*') if recursive else folder.iterdir()):
            if not path.is_file() or path.suffix.lower() not in ('.json','.log'):continue
            raw=add(path,label)
            if path.suffix=='.json':walk(json.loads(raw),label+'.'+path.name)
    for name in COMPLETED:
        folder=REVIEW/'output'/name;verification=json.loads((folder/'verification.json').read_bytes())
        assert any(verification.get(key) is True for key in ('all_functional_source_unchanged','source_unchanged'))
        assert verification.get('full_suite_pass_claimed',verification.get('full_pass_claimed',False)) is False
        for path in folder.glob('*closure.json'):
            value=json.loads(path.read_bytes());assert value['owned_count']==0 and value['termination_issued'] is False
            assert value['matcher_positive_cases']==4 and value['matcher_negative_cases']==3
        metadata_tree(folder,name)
        if (folder/'source-before.json').exists():assert (folder/'source-before.json').read_bytes()==(folder/'source-after.json').read_bytes()
        phases.append({'name':name,'verification_sha256':sha((folder/'verification.json').read_bytes()),'verification':verification})
    for name in NESTED:
        folder=REVIEW/'output'/name;attempt=json.loads((folder/'attempt.json').read_bytes())
        assert attempt['all_functional_sources_hash_size_mtime_unchanged'] is True
        if name.endswith('1794881601549860200-0a4b7568'):
            assert attempt['error'] is None and set(attempt['completed_cases'])=={'inset','behavior','compact','rail','lifecycle'}
            result=json.loads((folder/'verification.json').read_bytes())
            assert result['passed'] is True and result['checks']==12504 and result['failures']==0
        else:assert attempt['error'] is not None
        assert (folder/'source-before.json').read_bytes()==(folder/'source-after.json').read_bytes()
        metadata_tree(folder,name,True)
    for name in CONTROL_CASES:
        folder=REVIEW/'output/workspace-controls'/name
        result=json.loads(add(folder/'result.json','raw_controls48'))
        assert result=={'checks':48,'failures':0}
        add(folder/'app.log','concatenated_controls_log_not_chronological')
    for name in CONTROL_RECEIPTS:
        path=REVIEW/'output/private-desktop'/name;raw=add(path,'exact_controls_physical_receipt');receipts[str(path.resolve())]=json.loads(raw)
    for path in list(rows):
        candidate=Path(path)
        if candidate.name=='private-receipt.json':
            value=json.loads(candidate.read_bytes())
            if value.get('format')=='studio_private_desktop_1':receipts[path]=value
    desktops={}
    for path,value in receipts.items():
        assert value['format']=='studio_private_desktop_1' and type(value['exit']) is int and value['exit'] in (0,1)
        assert all(value.get(key) is True for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'))
        assert all(value.get(key) is False for key in ('foreground_child_observed','desktop_switch_requested'))
        assert not any(value.get(key) for key in ('monitor_error','desktop_enumeration_error','error','cancelled'))
        identity=(value['desktop'],value['child_pid'])
        if identity in desktops:assert desktops[identity]==value
        desktops[identity]=value
    old_packet=MAIN/'experiments/neon_failed_f387_actual_packet_20261117'
    assert sha((old_packet/'INDEX.json').read_bytes())=='a96f39ab1962d819ec3396c50f9c539385938255eb8dc8a7d3c154566fd0a6ab'
    for name in ('INDEX.json','ACTUAL_RESULT.json','README.md'):add(old_packet/name,'preserved_old_f387_archive_with_retracted_timing_claim')
    diagnosis=MAIN/'experiments/neon_workspace_font_diagnosis_20261117'
    ordered=add(diagnosis/'first-lifecycle-fix-ordered-engine.log','decisive_chronological_engine_log').decode().splitlines()
    assert ordered[26].startswith('PASS real workspace splitters') and 'ERROR: Parameter "fd" is null.' in ordered[27]
    assert next(i for i,line in enumerate(ordered) if line.startswith('PASS docking swaps'))>27
    add(diagnosis/'DIAGNOSIS.json','root_diagnosis_retraction_observation')
    aliases=[MAIN/'experiments/run_neon_workspace_followup_20261117.py',MAIN/'experiments/run_neon_behavior_original_20261116.py',
      MAIN/'experiments/run_neon_world_lifecycle_20261117.py',MAIN/'experiments/run_neon_world_lifecycle_typed_20261117.py',
      REVIEW/'experiments/neon_rail_transaction_diagnostic_20261117/rail_diagnostic.gd']
    for path in aliases:add(path,'source_driver_or_diagnostic_alias')
    for folder in ('neon_f387_terminal_20261117','neon_world_teardown_fix_20261117','neon_world_font_cache_20261117','neon_world_lifecycle_integration_20261117','neon_world_rail_transaction_20261117'):
        for name in ('INDEX.json','SOURCE_PROOF.json','SOURCE_DERIVATION.json','README.md','PEER_REVIEW.md','TRANSPORT_AUDIT.md'):
            path=MAIN/'experiments'/folder/name
            if path.is_file():add(path,'sealed_source_context')
    inputs={'format':'has_neon_fix_sequence_archive_inputs_1','roots':{name:str(root) for name,root in ROOTS.items()},'files':list(rows.values()),'completed_phases':phases,
      'physical_receipt_files':len(receipts),'unique_physical_jobs':len(desktops),'latest_standard_attempt':'PASS12504_ALL5_CASES_AFTER_TRANSACTION','current_full_PASS_or_merge_claimed':False,
      'future_complete_canonical_full':'PENDING_UNOBSERVED_NOT_INCLUDED','native_art_arrays_media_or_projects_selected':False,'agent_engines_CIM_Git_executed':False}
    (HERE/'INPUTS.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pinned_inputs':len(rows),'physical_receipt_files':len(receipts),'unique_physical_jobs':len(desktops),'input_bytes':sum(row['bytes'] for row in rows.values())}))


if __name__=='__main__':main()

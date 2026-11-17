"""Read-only standalone full packet/alias/privacy verifier; no native runtime."""
from pathlib import Path
import gzip,hashlib,json,math,re,calendar,datetime
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):
    p=HERE/n;assert p.resolve().is_relative_to(HERE.resolve()) and not p.is_symlink();return p.read_bytes()
def load(n):return json.loads(read(n))
def privacy(v,path='$'):
    if isinstance(v,dict):
        for k,x in v.items():
            assert k not in {'Blender_matrix_local_row_major','native_rest_words_uint32','native_rest_matrices','vertex_positions','vertex_buffer','index_buffer','image_data','audio_data','base64','rest_matrices','world_vertices','PCM'}
            core_pose=path=='$.core_process_groups' and k=='pose' and isinstance(x,dict) and set(x)=={'exit','seconds'} and type(x['exit']) is int and x['exit']==0 and type(x['seconds']) in (int,float) and math.isfinite(x['seconds']) and x['seconds']>=0
            assert core_pose or not(k in {'vertices','indices','triangles','pose','poses','normal','normals','basis','transform','transforms'} and isinstance(x,(list,dict)))
            privacy(x,path+'.'+k)
    elif isinstance(v,list):
        assert not(v and all(type(x) in (int,float) for x in v))
        for i,x in enumerate(v):privacy(x,path+'['+str(i)+']')
    elif isinstance(v,float):assert math.isfinite(v)
idx=load('INDEX.json');expected={r['path'] for r in idx['files']};actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='INDEX.json' and '__pycache__' not in p.parts}
assert expected==actual and len(expected)==idx['payload_files'];checks=0
for row in idx['files']:
    raw=read(row['path']);assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];checks+=1
    if row['path'].endswith('.json'):privacy(json.loads(raw))
    if row['path'].endswith('.gz'):privacy(json.loads(gzip.decompress(raw)))
manifest=load('SOURCE_MANIFEST.json');assert manifest['raw_full_report_not_copied']
for row in manifest['copies']:
    packed=read(row['payload']);assert len(packed)==row['payload_bytes'] and sha(packed)==row['payload_sha256']
    raw=gzip.decompress(packed) if row['codec']=='gzip' else packed
    assert len(raw)==row['raw_bytes'] and sha(raw)==row['raw_sha256'];checks+=1
assert read('run/source-before.json.gz')==read('run/source-after.json.gz')
source=json.loads(gzip.decompress(read('run/source-before.json.gz')));assert len(source['source_sha256'])==1019
state=load('run/state.json');host=load('run/authoritative-host-termination.json');rawhost=load('run/authoritative-host-terminal.json');release=load('run/graphics-lease-released.json')
assert state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged']
assert host['raw_observation_sha256']==sha(read('run/authoritative-host-terminal.json'))
assert release['canonical_state_sha256']==sha(read('run/state.json')) and release['host_proof_sha256']==sha(read('run/authoritative-host-termination.json'))
assert release['released'] and release['all_private_jobs_closed'] and release['source_commit']==state['source_commit']==source['commit']
inv=json.loads(gzip.decompress(read('audit/receipt-inventory.json.gz')));assert release['receipt_inventory_sha256']==sha(gzip.decompress(read('audit/receipt-inventory.json.gz')))
assert inv['summary']['passed'] and inv['summary']['unique_receipt_files']==release['private_jobs']
rows=load('RECEIPT_INDEX.json')['rows'];assert len(rows)==release['private_jobs'] and len({r['desktop'] for r in rows})==len(rows)
physical={};cancel=normal=0
for row in rows:
    receipt=load(row['payload']);assert sha(read(row['payload']))==row['sha256']
    assert all(receipt.get(k) is True for k in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'))
    assert all(receipt.get(k) is False for k in ('desktop_switch_requested','foreground_child_observed'))
    physical[row['original']]=receipt
    if receipt['exit']==0:normal+=1;assert not receipt.get('error') and not receipt.get('monitor_error')
    else:
        cancel+=1;assert receipt['exit']==2 and receipt.get('cancelled') is True and receipt['error']=='Owned converter cancelled' and row['original']==inv['expected_cancellation_support']['receipt_path']
    checks+=1
assert normal==release['normal_exit_0'] and cancel==release['expected_Krita_cancellation_exit_2']==1
for inline in inv['inline_receipts']:assert any(physical.get(p)==inline['receipt'] for p in inline['physical_exact_matches']);checks+=1
extract=load('RESULT_EXTRACT.json');registry=load('audit-source/RESULT_REGISTRY.json')
assert set(extract['result_keys'])==set(registry['expected_result_keys']) and len(extract['result_keys'])==157
assert set(extract['core_process_groups'])==set(registry['expected_core_process_keys']) and len(extract['core_process_groups'])==36
assert set(extract['movie_groups'])==set(registry['expected_movie_keys']) and len(extract['movie_groups'])==21
assert all(r['exit']==0 for r in extract['core_process_groups'].values())
assert all(r['frames']==48 and r['fps']=='24/1' and r['codec_name']=='h264' and r['width']==1920 and r['height']==1080 for r in extract['movie_groups'].values())
assert extract['raw_private_report_sha256']==release['full_report_sha256'] and not extract['raw_full_report_copied']
assert not any(p.lower().endswith(('.glb','.mdl','.vvd','.blend','.has','.png','.jpg','.wav','.mp4')) for p in expected)
for bad in ({'pose':{}},{'normal':[0,0,1]},{'vertices':[[0,0,0]]},{'core_process_groups':{'pose':{'exit':0,'seconds':[1,2,3]}}}):
    try:privacy(bad)
    except AssertionError:pass
    else:raise AssertionError('Privacy negative control admitted')
print(json.dumps({'archive_audit_passed':True,'checks':checks,'payload_files':len(expected),'exact_copies':len(manifest['copies']),'physical_receipts':len(rows),'privacy_negative_controls':4,'product_tests_run':0,'index_sha256':sha(read('INDEX.json'))}))

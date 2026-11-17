"""Archive whitelisted actual full-run metadata; never copy the raw full report or media."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,math,stat
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=ROOT/'output/windows-canonical-bone-binding-20261116T041518335'
AUDIT=ROOT/'output/current-full-receipts-20261116-attempt1'
DRIVER=ROOT/'output/current-full-receipts-driver-20261116-attempt1'
COMMIT='52f63c944ded7a651da871524d23a345b606424d'
MAX=16*1024*1024
parser=argparse.ArgumentParser();parser.add_argument('--resume-after-retained-privacy-refusal',action='store_true');RESUME=parser.parse_args().resume_after_retained_privacy_refusal
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    path=Path(path);assert path.is_file() and path.stat().st_size<=MAX
    for p in (path,*path.parents):assert not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400
    before=path.stat();data=path.read_bytes();after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    return data
def load(path):return json.loads(read(path))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    if RESUME and path.exists():
        assert read(path)==(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();return
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def privacy(value,path='$'):
    if isinstance(value,dict):
        for k,v in value.items():
            assert k not in {'Blender_matrix_local_row_major','native_rest_words_uint32','native_rest_matrices','vertex_positions','vertex_buffer','index_buffer','image_data','audio_data','base64','rest_matrices','world_vertices','PCM'},path+'.'+k
            core_pose=(path=='$.core_process_groups' and k=='pose' and isinstance(v,dict) and set(v)=={'exit','seconds'} and type(v['exit']) is int and v['exit']==0 and type(v['seconds']) in (int,float) and math.isfinite(v['seconds']) and v['seconds']>=0)
            assert core_pose or not(k in {'vertices','indices','triangles','pose','poses','normal','normals','basis','transform','transforms'} and isinstance(v,(list,dict))),path+'.'+k
            privacy(v,path+'.'+k)
    elif isinstance(value,list):
        assert not(value and all(type(x) in (int,float) for x in value)),path+' numeric list'
        for i,v in enumerate(value):privacy(v,path+'['+str(i)+']')
    elif isinstance(value,float):assert math.isfinite(value),path
copies=[]
def copy(source,name,compressed=False):
    raw=read(source);target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True)
    if source.suffix=='.json':privacy(json.loads(raw))
    payload=gzip.compress(raw,mtime=0) if compressed else raw
    if RESUME and target.exists():assert read(target)==payload
    else:assert not target.exists();target.write_bytes(payload)
    copies.append({'original':str(source),'payload':name,'codec':'gzip' if compressed else 'identity','raw_bytes':len(raw),'raw_sha256':sha(raw),'payload_bytes':len(payload),'payload_sha256':sha(payload)})
    assert read(source)==raw
state=load(RUN/'state.json');release=load(RUN/'graphics-lease-released.json');inventory=load(AUDIT/'receipt-inventory.json')
summary=inventory['summary'];report_path=ROOT/'output/verification.json';report_raw=read(report_path);report=json.loads(report_raw)
assert state['status']=='passed' and state['suite_exit']==0 and state['source_unchanged'] and state['source_commit']==COMMIT
assert release['released'] and release['source_commit']==COMMIT and release['functional_source_entries']==1019
assert release['receipt_inventory_sha256']==sha(read(AUDIT/'receipt-inventory.json')) and release['full_report_sha256']==sha(report_raw)
assert summary['passed'] and not summary['unexpected_failures'] and summary['unique_receipt_files']==release['private_jobs']
assert summary['success_exit_0_files']==release['normal_exit_0'] and summary['expected_krita_cancel_exit_2_files']==release['expected_Krita_cancellation_exit_2']==1
assert len(report)==157 and len(inventory['receipts'])==release['private_jobs']
for name in ('state.json','launch.json','root-birth-observation.json','authoritative-host-terminal.json','authoritative-host-termination.json','graphics-lease-released.json'):
    copy(RUN/name,'run/'+name)
for name in ('source-before.json','source-after.json'):copy(RUN/name,'run/'+name+'.gz',True)
assert read(RUN/'source-before.json')==read(RUN/'source-after.json')
copy(AUDIT/'receipt-inventory.json','audit/receipt-inventory.json.gz',True)
copy(AUDIT/'receipt-ready-final.json','audit/receipt-ready-final.json')
for name in ('command.json','start.json','process.json','verification.json'):copy(DRIVER/name,'audit-driver/'+name)
receipt_rows=[]
for index,row in enumerate(inventory['receipts']):
    source=Path(row['file']['path']);raw=read(source);assert sha(raw)==row['file']['sha256']
    assert row['within_run_interval'] and row['isolation_and_closure_passed']
    receipt=json.loads(raw);assert receipt==row['receipt']
    for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'):assert receipt[key] is True
    for key in ('desktop_switch_requested','foreground_child_observed'):assert receipt[key] is False
    assert row['classification'] in ('success_exit_0','expected_krita_cancel_exit_2')
    name=f'receipts/{index:03d}-'+sha(str(source).encode())[:12]+'.json';copy(source,name)
    receipt_rows.append({'payload':name,'original':str(source),'sha256':sha(raw),'classification':row['classification'],'desktop':receipt['desktop'],'fresh_root':row['fresh_root']})
save(HERE/'RECEIPT_INDEX.json',{'format':'has_current_full_physical_receipt_index_1','observed_count':len(receipt_rows),'rows':receipt_rows})
for folder,index_sha,target in [('experiments/current_full_receipts_20261116','017f989526f67669148a2073890037b519f50eb2d233994eebb3e571631a8782','audit-source'),('experiments/full_native_five_20261116','29730b54dd20e86fa43783c3b295aa0f66443b5095f0fa0529418eac1879ddf5','terminal-source')]:
    source=ROOT/folder;assert sha(read(source/'INDEX.json'))==index_sha
    doc=load(source/'INDEX.json');rows=doc['files'];entries=rows.items() if isinstance(rows,dict) else ((r['path'],r) for r in rows)
    copy(source/'INDEX.json',target+'/INDEX.json')
    for name,row in entries:
        p=source/name;assert len(read(p))==row['bytes'] and sha(read(p))==row['sha256'];copy(p,target+'/'+name)
for name in ('experiments/verification_runner/run_canonical_owned.ps1','experiments/owner_pause_20261114/start_canonical_bone_binding_owned.ps1','tests/verify.py','tests/verify_krita_import.py'):
    copy(ROOT/name,'code/'+name)
registry=load(ROOT/'experiments/current_full_receipts_20261116/RESULT_REGISTRY.json')
core={name:report[name] for name in registry['expected_core_process_keys']}
assert len(core)==36 and all(set(v)=={'exit','seconds'} and v['exit']==0 for v in core.values())
movies={}
for name in registry['expected_movie_keys']:
    row=report[name];assert set(row)=={'frames','fps','duration'} and row['frames']==48 and row['fps']=='24/1'
    item=dict(row)
    if name.startswith('posed_model_video_'):
        item.update(codec_name='h264',width=1920,height=1080,codec_evidence='Explicit assertions in pinned verify_media source and actual complete PASS; no saved separate ffprobe JSON for these two rows.')
    else:
        path=ROOT/'output'/(name.removesuffix('_video')+'-ffprobe.json');meta=load(path);video=next(v for v in meta['streams'] if v['codec_type']=='video')
        assert video['codec_name']=='h264' and video['nb_read_frames']=='48' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='24/1'
        assert meta['format']['duration']==row['duration']
        item.update(codec_name=video['codec_name'],width=video['width'],height=video['height'],pixel_format=video['pix_fmt'],audio_codecs=[v['codec_name'] for v in meta['streams'] if v['codec_type']=='audio'],metadata_file_sha256=sha(read(path)),codec_evidence='Exact saved ffprobe scalar extraction; full metadata body not copied.')
    movies[name]=item
assert len(movies)==21
extract={'format':'has_current_full_safe_result_extract_1','source_commit':COMMIT,'raw_private_report_sha256':sha(report_raw),'raw_private_report_bytes':len(report_raw),
    'result_keys':sorted(report),'core_process_groups':core,'movie_groups':movies,'actual_mmd_tested':report['actual_mmd_tested'],
    'source_choice_foundation_checks':report['source_choice_foundation']['checks'],'source_import_owner_checks':report['source_import_owner']['result']['checks'],
    'raw_full_report_copied':False,'private_native_or_pose_or_media_payloads_copied':False}
privacy(extract);save(HERE/'RESULT_EXTRACT.json',extract)
elapsed=summary['elapsed_seconds']
benchmark={'format':'has_native_five_current_full_actual_1','status':'PASSED_COMPLETE_DEFAULT_AND_ROOT_GRAPHICS_RELEASE','source_commit':COMMIT,
    'run_name':RUN.name,'started_utc':state['started_utc'],'finished_utc':state['finished_utc'],'elapsed_seconds':elapsed,
    'full_result_entries':157,'core_groups':36,'root_movie_groups':21,'functional_source_files':1019,'functional_source_unchanged':True,
    'private_jobs':release['private_jobs'],'exit0':release['normal_exit_0'],'source_registered_Krita_cancellation_exit2':release['expected_Krita_cancellation_exit_2'],
    'all_private_jobs_closed':True,'all_inline_receipts_match':True,'root_authoritative_close_utc':load(RUN/'authoritative-host-termination.json')['observed_utc'],'root_graphics_release_utc':release['released_utc'],
    'root_termination_claim':'Root observer issued no termination; the registered test-controlled cancellation is counted separately.',
    'full_report_sha256':sha(report_raw),'receipt_inventory_sha256':sha(read(AUDIT/'receipt-inventory.json')),
    'native_five_scope':'Main runtime supports five joints in three strands on one qualified Junko GLB. Separate266state+102GUI qualification remains separate from this complete default. Other44 rules, SDK/client/artist fidelity and same-actor native ragdoll remain unqualified.',
    'separate_native_five_qualification_packet':{'path':'experiments/native_five_qualified_actual_20261116/INDEX.json','sha256':sha(read(ROOT/'experiments/native_five_qualified_actual_20261116/INDEX.json'))},
    'earlier_failed_full_preserved':{'path':'docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json','sha256':sha(read(ROOT/'docs/benchmarks/windows_native_leaf_full_timeout_2026-11-15.json'))},
    'normal_fidelity':'Prior raw2e-5 gate remains FAILED/UNQUALIFIED; full PASS does not upgrade it.','manual_hair_review':'OWNER_DEFERRED_NO_RESULT','formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED',
    'private_art_or_native_arrays_uploaded':False,'cleanup_performed_by_this_archive':False}
privacy(benchmark);save(HERE/'BENCHMARK.json',benchmark)
save(HERE/'SOURCE_MANIFEST.json',{'format':'has_native_five_full_exact_copy_manifest_1','copies':copies,'raw_full_report_not_copied':True})
assert sha(read(report_path))==release['full_report_sha256']
rows=[]
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or path.name=='INDEX.json' or '__pycache__' in path.parts:continue
    raw=read(path)
    if path.suffix=='.json':privacy(json.loads(raw))
    elif path.suffix=='.gz':privacy(json.loads(gzip.decompress(raw)))
    assert path.suffix.lower() in ('.py','.ps1','.json','.gz','.md','.diff')
    rows.append({'path':path.relative_to(HERE).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
save(HERE/'INDEX.json',{'format':'has_native_five_full_actual_index_1','files':rows,'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'raw_full_report_or_private_assets_included':False})
print(json.dumps({'passed':True,'packet':str(HERE),'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'exact_copies':len(copies),'physical_receipts':len(receipt_rows),'index_sha256':sha(read(HERE/'INDEX.json'))}))

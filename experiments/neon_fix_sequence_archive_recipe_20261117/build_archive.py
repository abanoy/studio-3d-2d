"""ROOT ONLY compact metadata/source archive builder. No engines, process queries or Git."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def safe(path):
    path=Path(path).absolute();assert '..' not in path.parts
    for part in (path,*path.parents):
        if part.exists():assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400
    return path.resolve()


def privacy(value):
    if type(value) is dict:
        forbidden={'image_data','audio_data','pcm','base64','vertex_positions','vertex_buffer','index_buffer','native_rest_matrices','native_rest_words_uint32'}
        for key,item in value.items():
            assert not (key in forbidden and item),'Private media/native payload refused: '+key
            assert not (key in ('vertices','indices','triangles','normals','weights') and type(item) in (dict,list) and item),'Native array payload refused: '+key
            privacy(item)
    elif type(value) is list:
        for item in value:privacy(item)


def prepare_payloads(plan):
    roots={name:safe(path) for name,path in plan['roots'].items()}
    payloads={};bindings=[];physical_files=[];physical_jobs={}
    for row in plan['files']:
        source=safe(roots[row['root']]/row['path']);assert source.is_relative_to(roots[row['root']])
        assert source.suffix in ('.json','.log','.py','.gd','.md','.patch') and not source.name.startswith('PRIVATE')
        before=source.stat();raw=source.read_bytes();after=source.stat()
        assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256'] and len(raw)<=4*1024*1024
        text=raw.decode('utf-8','strict');assert 'data:image/' not in text and 'base64,' not in text
        if source.suffix=='.json':
            value=json.loads(text);privacy(value)
            if type(value) is dict and value.get('format')=='studio_private_desktop_1':
                assert value['exit'] in (0,1) and type(value['exit']) is int
                assert all(value.get(key) is True for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed'))
                assert all(value.get(key) is False for key in ('foreground_child_observed','desktop_switch_requested'))
                assert not any(value.get(key) for key in ('error','monitor_error','desktop_enumeration_error','cancelled'))
                identity=(value['desktop'],value['child_pid'])
                if identity in physical_jobs:assert physical_jobs[identity]==value
                physical_jobs[identity]=value;physical_files.append(str(source))
        body=gzip.compress(raw,compresslevel=9,mtime=0) if row['gzip_exact_original'] else raw
        if row['gzip_exact_original']:assert gzip.decompress(body)==raw
        name='objects/'+row['sha256']+source.suffix+('.gz' if row['gzip_exact_original'] else '')
        if name in payloads:assert payloads[name]==body
        payloads[name]=body
        bindings.append({**row,'source_absolute_path':str(source),'archive_path':name,'archive_sha256':sha(body),'archive_bytes':len(body)})
    assert len(physical_files)==plan['physical_receipt_files'] and len(physical_jobs)==plan['unique_physical_jobs']
    return payloads,bindings,physical_jobs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe-index-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    index_raw=(HERE/'INDEX.json').read_bytes();assert sha(index_raw)==args.recipe_index_sha256
    index=json.loads(index_raw)
    for row in index['files']:
        raw=(HERE/row['path']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    target=safe(args.output)
    assert target.parent==safe(MAIN/'experiments') and target.name.startswith('neon_workspace_fix_sequence_actual_packet_') and not target.exists()
    plan=json.loads((HERE/'INPUTS.json').read_bytes());payloads,bindings,jobs=prepare_payloads(plan)
    # Every source, privacy, receipt and compressed-byte gate precedes the first output write.
    target.mkdir(exist_ok=False)
    for name,raw in payloads.items():
        path=target/name;path.parent.mkdir(exist_ok=True,parents=True)
        with path.open('xb') as handle:handle.write(raw)
    for row in index['files']:
        path=target/'recipe'/row['path'];path.parent.mkdir(exist_ok=True,parents=True)
        with path.open('xb') as handle:handle.write((HERE/row['path']).read_bytes())
    (target/'recipe/INDEX.json').write_bytes(index_raw)
    def save(name,value):(target/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    save('EXACT_SOURCE_BINDINGS.json',{'format':'has_neon_fix_sequence_exact_bindings_1','files':bindings})
    save('ACTUAL_SEQUENCE.json',{'format':'has_neon_workspace_fix_sequence_actual_1','completed_root_phases':plan['completed_phases'],
      'physical_receipt_files':plan['physical_receipt_files'],
      'unique_physical_jobs':len(jobs),'normal_exit0_jobs':sum(value['exit']==0 for value in jobs.values()),'assertion_exit1_jobs':sum(value['exit']==1 for value in jobs.values()),
      'all_selected_physical_jobs_private_closed':True,'old_failed_full_archive_mutated':False,'after_free_attribution':'RETRACTED','old_regex_overescape_attribution':'RETRACTED_FOR_CURRENT9f604_BYTES_PATTERN_IS_VALID',
      'first_standard12504':'FAILED_RAIL45_1_AFTER_INSET_BEHAVIOR_COMPACT_PASS_LIFECYCLE_GUI_UNRUN','transaction_standard12504':'PASS_ALL5_CASES',
      'standalone_typed_lifecycle29':'PASS_SEPARATE_ROOT_SCOPE','future_complete_canonical_full':'PENDING_NOT_INCLUDED','full_Windows_PASS_or_merge_claimed':False,'native_art_arrays_media_or_projects_included':False})
    for name in ('CORRECTIONS.json','README.md'):(target/name).write_bytes((HERE/name).read_bytes())
    files=[]
    for path in sorted(target.rglob('*')):
        if path.is_file():files.append({'path':path.relative_to(target).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())})
    save('INDEX.json',{'format':'has_neon_workspace_fix_sequence_actual_packet_1','files':files,'file_count':len(files),'bytes':sum(row['bytes'] for row in files),'exact_original_bindings':len(bindings),'content_addressed_payloads':len(payloads),'unique_physical_jobs':len(jobs),'excludes':['INDEX.json'],'full_PASS_claimed':False})
    for row in bindings:
        raw=(target/row['archive_path']).read_bytes();raw=gzip.decompress(raw) if row['gzip_exact_original'] else raw
        assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
    print(json.dumps({'output':str(target),'INDEX_sha256':sha((target/'INDEX.json').read_bytes()),'bindings':len(bindings),'unique_payloads':len(payloads),'physical_jobs':len(jobs),'files':len(files)}))


if __name__=='__main__':main()

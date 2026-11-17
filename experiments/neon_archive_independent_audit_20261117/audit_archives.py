"""Independent read-only archive/original audit; does not import either archive builder."""
from pathlib import Path
import ast
import calendar
import datetime
import gzip
import hashlib
import io
import json
import os
import re

HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[1]
REVIEW=MAIN.parent/'has-neon-review-20261116-c2d52ff'
ROOTS={'main':MAIN,'review':REVIEW}
PACKETS=(
 ('sequence','neon_workspace_fix_sequence_actual_packet_20261117','e8a7f25ed780eaac2b6d0611fcbc7c7d388945fd82e7f23df6979cf0147060c9',305,417,23),
 ('standalone32','neon_world_lifecycle32_actual_packet_20261117','db32fd9398c358a74b455d26e074482c717c456b812b17fd43a3d5233e41618e',36,33,1),
)
ALLOWED={'.json','.log','.py','.gd','.md','.patch'}


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def safe(path):
    path=Path(path).absolute();require('..' not in path.parts,'Traversal refused')
    for item in (path,*path.parents):
        if item.exists():require(not item.is_symlink() and not getattr(item.lstat(),'st_file_attributes',0)&0x400,'Reparse path refused')
    return path.resolve()


def read(path,limit=8*1024*1024):
    path=safe(path);before=path.stat();require(path.is_file() and before.st_size<=limit,'Bounded regular file required')
    raw=path.read_bytes();after=path.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'File changed during audit')
    return raw


def unique_keys(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Duplicate JSON key');result[key]=value
    return result


def parse(raw):
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique_keys,
                      parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Nonfinite JSON refused')))


def same(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(same(value,b[key]) for key,value in a.items())
    if type(a) in (list,tuple):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b


def private_payload_check(value):
    if type(value) is dict:
        names={'image_data','audio_data','pcm','base64','data_uri','vertex_positions','vertex_buffer','index_buffer',
               'native_rest_words_uint32','native_rest_matrices','Blender_matrix_local_row_major'}
        for key,item in value.items():
            require(not (key in names and item),'Private/media/native payload field: '+key)
            require(not (key in {'vertices','indices','triangles','normals','weights'} and type(item) in (list,dict) and item),'Geometry array field: '+key)
            private_payload_check(item)
    elif type(value) is list:
        for item in value:private_payload_check(item)


def metadata_bytes(raw,suffix):
    require(not raw.startswith((b'glTF',b'BLENDER',b'RIFF',b'\x89PNG',b'PK\x03\x04')),'Binary asset header refused')
    text=raw.decode('utf-8','strict')
    if suffix in {'.json','.log'}:require('data:image/' not in text and 'base64,' not in text,'Encoded image payload refused')
    if suffix=='.json':private_payload_check(parse(raw))


def receipt(value):
    require(value.get('format')=='studio_private_desktop_1','Private receipt format')
    require(type(value.get('exit')) is int and value['exit'] in (0,1),'Observed UI receipt exit')
    require(type(value.get('desktop')) is str and type(value.get('child_pid')) is int and value['child_pid']>0,'Physical identity')
    require(all(value.get(key) is True for key in ('private_window_seen','child_desktop_confirmed','job_closed','desktop_closed')),'Placement/job/desktop closure')
    require(all(value.get(key) is False for key in ('foreground_child_observed','desktop_switch_requested')),'Foreground/switch')
    require(not any(value.get(key) for key in ('error','monitor_error','desktop_enumeration_error','cancelled')),'Monitor/error/cancel')
    return value['desktop'],value['child_pid']


def audit_packet(label,name,pin,expected_files,expected_bindings,expected_jobs):
    folder=safe(MAIN/'experiments'/name);index_raw=read(folder/'INDEX.json');require(sha(index_raw)==pin,'Root supplied INDEX pin')
    index=parse(index_raw);entries=index['files'];require(len(entries)==index['file_count']==expected_files,'Payload count')
    declared={};actual=set()
    for row in entries:
        rel=Path(row['path']);require(not rel.is_absolute() and '..' not in rel.parts,'Relative payload path')
        require(row['path'].casefold() not in declared,'Case-alias/duplicate payload')
        declared[row['path'].casefold()]=row
        raw=read(folder/rel);require(type(row['bytes']) is int and len(raw)==row['bytes'] and sha(raw)==row['sha256'],'Payload identity: '+row['path'])
        suffix=Path(rel.stem).suffix if rel.suffix=='.gz' else rel.suffix
        require(suffix in ALLOWED and not rel.name.startswith('PRIVATE'),'Non-art metadata/source kind')
        if rel.suffix!='.gz':metadata_bytes(raw,suffix)
    for directory,names,files in os.walk(folder,followlinks=False):
        for part in [*names,*files]:safe(Path(directory)/part)
        for filename in files:actual.add((Path(directory)/filename).relative_to(folder).as_posix())
    require(actual=={row['path'] for row in entries}|{'INDEX.json'},'Exact physical membership')
    require(sum(row['bytes'] for row in entries)==index['bytes'],'Total index bytes')
    bindings=parse(read(folder/'EXACT_SOURCE_BINDINGS.json'))['files']
    plan=parse(read(folder/'recipe/INPUTS.json'));require(len(bindings)==len(plan['files'])==expected_bindings,'Exact binding count')
    require({key:safe(value) for key,value in plan['roots'].items()}=={key:safe(value) for key,value in ROOTS.items()},'Fixed allowed source roots')
    expected_rows={(row['root'],row['path']):row for row in plan['files']};require(len(expected_rows)==len(plan['files']),'Unique source aliases')
    payload_objects=set();jobs={};physical_files=[];inline=[];bound_by_source={};raw_cache={};gzip_count=0
    for row in bindings:
        key=row['root'],row['path'];require(key in expected_rows,'Unplanned binding')
        require(all(same(row[field],value) for field,value in expected_rows[key].items()),'Exact plan row')
        rel=Path(row['path']);require(not rel.is_absolute() and '..' not in rel.parts and rel.suffix in ALLOWED,'Source path/kind')
        source=safe(ROOTS[row['root']]/rel);require(source.is_relative_to(safe(ROOTS[row['root']])) and source==safe(row['source_absolute_path']),'Source-root/absolute alias')
        require(not source.name.startswith('PRIVATE'),'PRIVATE source excluded')
        archive_rel=Path(row['archive_path']);require(archive_rel.parts[0]=='objects' and '..' not in archive_rel.parts and not archive_rel.is_absolute(),'Content payload path')
        archived=read(folder/archive_rel);require(sha(archived)==row['archive_sha256'] and len(archived)==row['archive_bytes'],'Archived byte pin')
        if row['archive_path'] not in raw_cache:
            if row['gzip_exact_original']:
                require(archive_rel.suffix=='.gz','Compressed suffix')
                with gzip.GzipFile(fileobj=io.BytesIO(archived)) as stream:
                    raw=stream.read(row['bytes']+1);require(not stream.read(1),'Gzip output bound')
                gzip_count+=1
            else:raw=archived
            raw_cache[row['archive_path']]=raw
        raw=raw_cache[row['archive_path']];require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'Exact decompressed original')
        require(read(source)==raw,'Current preserved original equality')
        metadata_bytes(raw,rel.suffix);payload_objects.add(row['archive_path']);bound_by_source[str(source)]=raw
        if rel.suffix=='.json':
            value=parse(raw)
            if type(value) is dict and value.get('format')=='studio_private_desktop_1':
                identity=receipt(value)
                if identity in jobs:require(same(jobs[identity],value),'Conflicting physical copies')
                jobs[identity]=value;physical_files.append(str(source))
            def collect(item,nested=False):
                if type(item) is dict:
                    if nested and item.get('format')=='studio_private_desktop_1':inline.append(item)
                    for child in item.values():collect(child,True)
                elif type(item) is list:
                    for child in item:collect(child,True)
            collect(value)
    require(len(jobs)==expected_jobs==plan['unique_physical_jobs'] and len(physical_files)==plan['physical_receipt_files'],'Actual physical job/file counts')
    for item in inline:require(same(jobs.get((item['desktop'],item['child_pid'])),item),'Inline exact physical join')
    require(payload_objects=={row['path'] for row in entries if row['path'].startswith('objects/')},'No unbound object payload')
    recipe_index_raw=read(folder/'recipe/INDEX.json');recipe_index=parse(recipe_index_raw)
    for row in recipe_index['files']:
        raw=read(folder/'recipe'/row['path']);require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'Preserved recipe seal payload')
    if label=='sequence':
        require(sha(recipe_index_raw)=='eda61664e18d73d630820d44a3d7a63cb9d5e9710772f5516fc4e4e06d74621b','Sequence recipe seal')
        summary=parse(read(folder/'ACTUAL_SEQUENCE.json'));correction=parse(read(folder/'CORRECTIONS.json'))
        require(summary['full_Windows_PASS_or_merge_claimed'] is False and summary['transaction_standard12504']=='PASS_ALL5_CASES','Bounded result scope')
        require(summary['first_standard12504']=='FAILED_RAIL45_1_AFTER_INSET_BEHAVIOR_COMPACT_PASS_LIFECYCLE_GUI_UNRUN','Original45/1 retained')
        require(correction['timing']['old_after_app_free_attribution']=='RETRACTED' and correction['matcher']['old_zero_counts_invalidated_by_regex'] is False,'Both interpretation corrections')
        old_index=MAIN/'experiments/neon_failed_f387_actual_packet_20261117/INDEX.json'
        require(sha(read(old_index))==correction['old_f387_archive_index_sha256']=='a96f39ab1962d819ec3396c50f9c539385938255eb8dc8a7d3c154566fd0a6ab','Old immutable failed archive seal')
        chronological=bound_by_source[str(safe(MAIN/'experiments/neon_workspace_font_diagnosis_20261117/first-lifecycle-fix-ordered-engine.log'))].decode().splitlines()
        require(chronological[26].startswith('PASS real workspace splitters') and chronological[27].startswith('ERROR: Parameter "fd" is null.'),'Ordered error position')
        require(next(i for i,line in enumerate(chronological) if line.startswith('PASS docking swaps'))>27,'Error precedes docking assertion')
    else:
        require(sha(recipe_index_raw)=='2169aa86a1564eef9cc91be281c547a97503ad196834abadeb394d0901a25bf6','Append recipe seal')
        summary=parse(read(folder/'ACTUAL_RESULT.json'))
        require(summary['report']['checks']==32 and summary['report']['failures']==0 and summary['ROOT_verification']['passed'] is True,'Standalone32 observed')
        require(summary['full_Windows_PASS_claimed'] is False and summary['formal12504_changed'] is False,'Standalone scope separation')
    require(sha(read(folder/'INDEX.json'))==pin,'INDEX unchanged after audit')
    return {'packet':name,'INDEX_sha256':pin,'payload_files_verified':len(entries),'exact_original_bindings':len(bindings),
            'unique_payload_objects':len(payload_objects),'gzip_objects_exactly_reversed':gzip_count,'physical_receipt_files':len(physical_files),
            'unique_physical_jobs':len(jobs),'normal_exit0_jobs':sum(row['exit']==0 for row in jobs.values()),'assertion_exit1_jobs':sum(row['exit']==1 for row in jobs.values()),
            'nested_inline_receipt_occurrences_joined':len(inline),'membership_root_alias_privacy_and_outcome_gates':'PASS','archive_unchanged':True},jobs


def matcher_correction():
    folder=MAIN/'experiments/neon_matcher_source_correction_20261117';record=parse(read(folder/'CORRECTION.json'))
    before=read(folder/'driver-before-comment-correction.py');after=read(MAIN/'experiments/run_neon_workspace_followup_20261117.py')
    require(sha(before)==record['before_driver_sha256']=='1ffd784ad6be5c0704a72f6116ac2a15a20e3e30811634ef27c2ebdcffe640ec','Exact as-executed driver before comment')
    require(sha(after)==record['after_driver_sha256']=='234a3f6aa3f76ee65ce1c6fd35a410326c4f01068f3a0bf81667481e4ec2af89','Corrected current driver')
    require(ast.dump(ast.parse(before),include_attributes=False)==ast.dump(ast.parse(after),include_attributes=False),'Comment-only AST inverse')
    old=read(MAIN/'experiments/run_neon_behavior_original_20261116.py');require(sha(old)==record['old_helper_sha256'],'Exact old source')
    node=next(node for node in ast.parse(old).body if isinstance(node,ast.FunctionDef) and node.name=='closed')
    code=next(node.value for node in ast.walk(node) if isinstance(node,ast.Constant) and type(node.value) is str and 'Get-CimInstance' in node.value)
    pattern=re.search(r"Name -match '([^']+)'",code)[1]
    require(pattern==record['decoded_native_regex'] and pattern.count('\\')==1,'Decoded native regex')
    require(all(re.fullmatch(pattern,name) for name in ('Godot_v4.6-stable_win64.exe','blender.exe','ffmpeg.exe','ffprobe.exe')),'Four positive source cases')
    require(record['old_regex_invalidated'] is False and record['actual_runtime_receipt_or_closure_results_changed'] is False,'No false closure invalidation')
    return {'old_source_sha256':sha(old),'preserved_before_comment_sha256':sha(before),'current_after_comment_sha256':sha(after),'comment_only_AST_exact':True,'old_native_pattern_valid_for_all4_positive_names':True,'host_query_executed':False}


def source_filesystem_attribution():
    """Supplemental original-file metadata, explicitly separate from archived byte proof."""
    def utc_ns(value):
        match=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(?:Z|\+00:00)',value)
        require(match is not None,'UTC phase bound')
        return calendar.timegm(datetime.datetime.strptime(match[1],'%Y-%m-%dT%H:%M:%S').timetuple())*10**9+int((match[2] or '').ljust(9,'0'))
    result=[]
    for phase,filename in [('neon-workspace-f387-baseline-20261117-attempt1','workspace_controls_smoke_dfe4f265026a40d88ad8a813a24aad0a.json'),('neon-workspace-teardown-fixed-20261117-attempt1','workspace_controls_smoke_77671800f00448538ba348b51cea2950.json')]:
        folder=REVIEW/'output'/phase;start=parse(read(folder/'controls-start.json'))['started_utc'];end=parse(read(folder/'controls-after-closure.json'))['observed_utc']
        source=REVIEW/'output/private-desktop'/filename;raw=read(source);mtime=source.stat().st_mtime_ns
        require(utc_ns(start)<=mtime<=utc_ns(end),'Failed-control original receipt mtime outside phase interval')
        result.append({'phase':phase,'receipt_source_path':str(safe(source)),'receipt_sha256':sha(raw),'original_current_mtime_ns':mtime,
                       'phase_started_utc':start,'phase_closed_observed_utc':end,'mtime_within_phase_interval':True,
                       'basis':'Additional current original-filesystem metadata, not information encoded in receipt JSON or the existing archive.'})
    return result


def main():
    require(not (HERE/'INDEX.json').exists() and not (HERE/'CPU_REPORT.json').exists(),'Fresh separate audit output required')
    results=[];all_jobs={}
    for entry in PACKETS:
        result,jobs=audit_packet(*entry);results.append(result)
        for identity,value in jobs.items():require(identity not in all_jobs,'Cross-packet job counted twice');all_jobs[identity]=value
    negatives=[{'image_data':'synthetic'},{'vertex_positions':[[1,2,3]]},{'normals':[[0,1,0]]},{'base64':'synthetic'},{'audio_data':[0,1]},{'native_rest_matrices':[[1,0]]}]
    for item in negatives:
        try:private_payload_check(item)
        except ValueError:pass
        else:raise ValueError('Private payload negative accepted')
    report={'format':'has_neon_archives_independent_CPU_audit_1','status':'PASS_INDEPENDENT_ARCHIVE_AUDIT','packets':results,'total_exact_original_bindings':sum(row['exact_original_bindings'] for row in results),'unique_actual_jobs_across_both':len(all_jobs),'matcher_source_correction':matcher_correction(),'privacy_negative_controls':len(negatives),
            'attribution_limit':'Two failed-control wrappers emit no receipt path. Their archive selection labels and closed receipt bytes do not independently prove phase assignment; original mtime was not included in those archive bindings. Other jobs have command/report references. No incorrect assignment was observed.',
            'supplemental_original_filesystem_attribution':source_filesystem_attribution(),'archive_builders_imported_or_executed':False,'archives_or_REVIEW_mutated':False,'engines_CIM_Git_or_active_full_state_report_log_accessed':False,'full_Windows_PASS_claimed':False}
    (HERE/'CPU_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

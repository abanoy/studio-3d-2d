"""Build once from exact closed-run text/source allowlist; no runtime execution."""
from pathlib import Path
import gzip
import hashlib
import json
import sys
from archive_checks import check,load,require

HERE=Path(__file__).resolve().parent
DEST=HERE.parent/'neon_helper375_actual_packet_20261117'
ALLOWED_SUFFIXES={'.json','.log','.py','.gd','.md','.txt','.cfg','.godot'}
INPUTS_SHA='f793f505db95097a27e2f9dac845e5bec6d012b7a4ae4610140ad4f64e927af1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe(path):
    path=Path(path).absolute();require('..' not in path.parts,'Traversal refused')
    for p in (path,*path.parents):
        if p.exists():require(not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'Reparse refused')
    return path.resolve()
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def main():
    require(not DEST.exists(),'Never overwrite an existing archive')
    spec_raw=(HERE/'INPUTS.json').read_bytes();require(sha(spec_raw)==INPUTS_SHA,'Frozen input recipe changed');spec=load(spec_raw);raw={};bindings={}
    require(spec['scope']=='EXPLICIT_COMPLETED_HELPER375_ROOT_DERIVED_CHILD_QA_OWNED_LAUNCH_OUTCOME_AND_PUBLIC_SOURCE','Wrong recipe scope')
    for row in spec['inputs']:
        key=row['root']+':'+row['path'];require(key not in raw,'Duplicate original binding')
        path=safe(safe(spec['roots'][row['root']])/row['path']);require(path.is_relative_to(safe(spec['roots'][row['root']])) and path.suffix in ALLOWED_SUFFIXES,'Input domain refused')
        require(path.stat().st_size==row['bytes'] and path.stat().st_mtime_ns==row['mtime_ns'],'Original metadata changed')
        data=path.read_bytes();require(len(data)<=2*1024*1024 and sha(data)==row['sha256'],'Original bytes changed')
        data.decode('utf-8-sig',errors='strict')
        raw[key]=data;bindings[key]=row
    summary=check(raw,bindings,spec['roots']['REVIEW'])
    require(summary==spec['expected_summary'],'Scalar evidence changed')
    objects={sha(data):data for data in raw.values()}
    DEST.mkdir();(DEST/'objects').mkdir()
    object_rows=[]
    for digest,data in sorted(objects.items()):
        packed=gzip.compress(data,compresslevel=9,mtime=0);name='objects/'+digest+'.gz'
        with (DEST/name).open('xb') as stream:stream.write(packed)
        object_rows.append({'path':name,'sha256':sha(packed),'bytes':len(packed),'decoded_sha256':digest,'decoded_bytes':len(data)})
    save(DEST/'BINDINGS.json',{'format':'has_helper375_original_text_bindings_1','roots':spec['roots'],'bindings':spec['inputs'],'note':'Original mtime fields are supplemental current read-only filesystem evidence. Original files are not altered or removed.'})
    save(DEST/'ACTUAL_RESULT.json',summary)
    with (DEST/'README.md').open('x',encoding='utf-8',newline='\n') as stream:stream.write((HERE/'PACKET_README.md').read_text(encoding='utf-8'))
    plain=[]
    for name in ('BINDINGS.json','ACTUAL_RESULT.json','README.md'):
        data=(DEST/name).read_bytes();plain.append({'path':name,'bytes':len(data),'sha256':sha(data)})
    index={'format':'has_helper375_compact_exact_actual_packet_1','qualification':summary['qualification'],'recipe_inputs_sha256':sha(spec_raw),'builder_sha256':sha(Path(__file__).read_bytes()),'verifier_sha256':sha((HERE/'verify_packet.py').read_bytes()),'check_source_sha256':sha((HERE/'archive_checks.py').read_bytes()),'original_bindings':len(raw),'unique_decoded_objects':len(objects),'objects':object_rows,'files':plain,'uncompressed_original_bytes':sum(len(x) for x in raw.values()),'physical_jobs':2,'full_suite_pass_claimed':False,'active_full_output_read':False,'media_native_geometry_binary_arrays_included':False}
    save(DEST/'INDEX.json',index)
    print(json.dumps({'archive':str(DEST),'INDEX_sha256':sha((DEST/'INDEX.json').read_bytes()),'original_bindings':len(raw),'unique_objects':len(objects),'compressed_object_bytes':sum(r['bytes'] for r in object_rows)},indent=2))
if __name__=='__main__':main()

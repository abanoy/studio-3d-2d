"""Apply this UNRUN candidate only to a pristine disposable runtime snapshot.

Never targets the active checkout, installed Studio or an existing owner review.
No engine, subprocess, Git, native asset or test execution is performed here.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = ROOT / 'output'
NEW_FILES = ('src/model_variants.gd','src/model_variant_runtime.gd',
             'src/model_variant_editor.gd','tools/model_variant_plan.py',
             'tools/model_variant_project.py','tests/model_variant_runtime_unit.gd',
             'tests/test_model_variant_project.py')

def need(ok,code):
    if not ok: raise ValueError(code)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def safe(path):
    path=Path(os.path.abspath(path))
    for node in (path,*path.parents):
        try: info=node.lstat()
        except FileNotFoundError: continue
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'LINK_OR_REPARSE_REFUSED')
        need(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),'SPECIAL_PATH_REFUSED')
        if stat.S_ISREG(info.st_mode): need(info.st_nlink==1,'HARDLINK_REFUSED')
    return path
def read(path):
    path=safe(path); before=path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=2*1024*1024,'SOURCE_SIZE_OR_TYPE')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno())
        need((opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns),'SOURCE_IDENTITY')
        raw=stream.read(before.st_size+1)
        after=os.fstat(stream.fileno())
    final=path.lstat()
    need(len(raw)==before.st_size and all((v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns) for v in (after,final)),'SOURCE_CHANGED')
    return raw

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--studio',type=Path,required=True)
    options=parser.parse_args()
    target=safe(options.studio)
    relative=target.relative_to(OUTPUT)
    need(target.name=='Studio' and len(relative.parts)==2 and relative.parts[0].startswith('variant-runtime-snapshot-'),'DISPOSABLE_SNAPSHOT_REQUIRED')
    need(target.is_dir() and not (target/'VARIANT_CANDIDATE_APPLIED.json').exists(),'PRISTINE_SNAPSHOT_REQUIRED')
    pins=json.loads(read(HERE/'SOURCE_PINS.json'))
    for row in pins['files']:
        raw=read(HERE/row['path'])
        need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'CANDIDATE_SOURCE_PIN_DIFFERS')
    patch=json.loads(read(HERE/'PATCHES.json'))
    writes=[]; before={}
    for item in patch['patches']:
        path=target/item['path']; raw=read(path)
        need(len(raw)==item['base_bytes'] and sha(raw)==item['base_sha256'],'SNAPSHOT_BASE_DIFFERS')
        text=raw.decode('utf-8')
        for operation in item['operations']:
            need(text.count(operation['anchor'])==1,'PATCH_ANCHOR_DIFFERS')
            text=text.replace(operation['anchor'],operation['replacement'])
        new=text.encode('utf-8')
        need(len(new)==item['successor_bytes'] and sha(new)==item['successor_sha256'],'PATCH_RESULT_DIFFERS')
        writes.append((path,new,True)); before[str(path)]=sha(raw)
    for name in NEW_FILES:
        path=safe(target/name)
        need(not path.exists(),'NEW_TARGET_ALREADY_EXISTS')
        writes.append((path,read(HERE/name),False))
    results=[]
    for path,raw,replace in writes:
        path.parent.mkdir(parents=True,exist_ok=True); safe(path.parent)
        if replace:
            need(sha(read(path))==before[str(path)],'SNAPSHOT_CHANGED_BEFORE_WRITE')
            temporary=path.with_name(path.name+'.variant-'+uuid.uuid4().hex)
            with temporary.open('xb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
            safe(path);os.replace(temporary,path)
        else:
            with path.open('xb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
        need(read(path)==raw,'WRITTEN_SOURCE_READBACK_DIFFERS')
        results.append({'path':path.relative_to(target).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    report={'format':'has_static_model_variant_runtime_candidate_applied_1','status':'SOURCE_APPLIED_UNRUN',
            'files':results,'engine_or_native_executed':False,'application_adoption_qualified':False}
    with (target/'VARIANT_CANDIDATE_APPLIED.json').open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'source_applied':True,'files':len(results),'engine_executed':False}))
    return 0
if __name__=='__main__':raise SystemExit(main())

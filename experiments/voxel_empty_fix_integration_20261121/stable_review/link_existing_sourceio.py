"""Complete prepared review shortcuts using existing authorized runtime paths only."""
from pathlib import Path
import ast,hashlib,importlib.util,json,stat,subprocess,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stable_review_recipe',HERE/'prepare_stable_review.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
before_raw=M.read(HERE/'PREPARATION-before-sourceio.json');before=json.loads(before_raw)
M.need(M.read(M.TARGET/'PREPARATION.json')==before_raw,'Unexpected receipt change')
M.need(M.git('rev-parse','HEAD').decode().strip()==M.REVISION,'Immutable source revision differs')
dependency=M.external_runtime_requirements()
runtime_before={}
for row in dependency['sourceio']['required_members']:
    path=M.SOURCEIO/row['path'];value=path.lstat()
    M.need(not stat.S_ISLNK(value.st_mode) and not getattr(value,'st_file_attributes',0)&0x400,'Linked required runtime member refused')
    runtime_before[str(path)]=M.identity(value)
blender_raw=M.read(M.BLENDER);blender_before=M.identity(M.BLENDER.lstat())
for row in before['source_inventory']:
    raw=M.read(M.TARGET/'Studio'/row['path'])
    M.need(len(raw)==row['bytes'] and M.sha(raw)==row['sha256'],'Pinned Studio source changed')
    M.need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob'] and row['mode'] in ('100644','100755'),'Copied source Git blob/mode mismatch')
changes=[]
for name in ['Open Studio discovery.bat','Open Direct lights.bat','Open Environment bounce.bat']:
    path=M.TARGET/name;raw=M.read(path);text=raw.decode('ascii')
    anchor='set "HYBRID_GODOT='+str(M.GODOT)+'"\r\n'
    M.need(text.count(anchor)==1 and 'HYBRID_SOURCEIO' not in text,'Unexpected launcher source')
    new=text.replace(anchor,anchor+'set "HYBRID_SOURCEIO='+str(M.SOURCEIO)+'"\r\n').encode('ascii')
    path.write_bytes(new);M.need(M.read(path)==new,'Launcher readback differs')
    changes.append({'path':name,'before_sha256':M.sha(raw),'after_sha256':M.sha(new),'only_added_environment_variable':'HYBRID_SOURCEIO'})
note=('The three shortcuts set HYBRID_SOURCEIO to the existing approved pinned runtime.\n'
      'That external directory and the existing Blender5.1 default executable must remain\n'
      'available while this review exists. They were checked read-only, not copied,\n'
      'installed or launched. USERPROFILE and the existing MMDTools discovery stay unchanged.\n\n')
path=M.TARGET/'README.md';text=M.read(path).decode();M.need(text.count('This is source-pinned review material')==1,'Unexpected README')
path.write_text(text.replace('This is source-pinned review material',note+'This is source-pinned review material'),encoding='utf-8',newline='\n')
result=json.loads(before_raw)
result['external_runtime_dependencies']=dependency
result['existing_runtimes'].append({'path':str(M.BLENDER),'bytes':len(blender_raw),'sha256':M.sha(blender_raw)})
result['previous_receipt_sha256']=M.sha(before_raw)
result['update_scope']='Three launcher HYBRID_SOURCEIO environment lines plus external-runtime metadata/README; Studio source and two projects unchanged.'
result['launcher_changes']=changes
result['external_runtime_metadata_preserved']=True
for path,stamp in runtime_before.items():M.need(M.identity(Path(path).lstat())==stamp,'Runtime member changed')
M.need(M.identity(M.BLENDER.lstat())==blender_before and M.sha(M.read(M.BLENDER))==M.sha(blender_raw),'Existing Blender changed')
M.need(M.git('rev-parse','HEAD').decode().strip()==M.REVISION,'Source HEAD changed')
for record in result['projects']:
    raw=M.read(M.TARGET/'Projects'/record['name']);M.need(len(raw)==record['bytes'] and M.sha(raw)==record['sha256'],'Prepared project changed')
files=[]
for path in sorted(M.TARGET.rglob('*')):
    if path.is_file() and path.name!='PREPARATION.json':
        raw=M.read(path);files.append({'path':path.relative_to(M.TARGET).as_posix(),'bytes':len(raw),'sha256':M.sha(raw)})
result['files']=files;result['total_files_excluding_this_receipt']=len(files)
result['total_bytes_excluding_this_receipt']=sum(x['bytes'] for x in files)
raw=(json.dumps(result,indent=2)+'\n').encode()
for path in [M.TARGET/'PREPARATION.json',HERE/'PREPARATION.json']:path.write_bytes(raw);M.need(M.read(path)==raw,'Receipt readback differs')
ast.parse(M.read(HERE/'prepare_stable_review.py'))
print(json.dumps({'status':result['status'],'source_files_unchanged':len(result['source_inventory']),'total_files':len(files)+1,'total_bytes':result['total_bytes_excluding_this_receipt']+len(raw),'receipt_sha256':M.sha(raw),'sourceio_members':len(runtime_before),'blender_sha256':M.sha(blender_raw),'studio_launched':False,'runtime_installed_or_modified':False}))

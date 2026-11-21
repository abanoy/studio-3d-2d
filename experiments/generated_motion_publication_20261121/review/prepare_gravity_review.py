"""Metadata/copy-only stable review preparation. Never launches Studio or tools."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,re,stat,struct,subprocess,zipfile

HERE=Path(__file__).resolve().parent
INTEGRATION=HERE.parent.parent
SOURCE=INTEGRATION
TARGET=INTEGRATION.parent/'HAS-Review-Gravity-43dbdecc'
REVISION='43dbdecc759e971a80f0d1e468e1e7d1e3b9ed2b'
PYTHON=Path('C:/Program Files/Python313/python.exe')
PYTHONW=PYTHON.with_name('pythonw.exe')
GODOT=Path('C:/a/tools/Godot/Godot_v4.6-stable_win64.exe')
SOURCEIO=INTEGRATION.parent/'has-neon-review-20261116-c2d52ff/output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 5.1/blender.exe')
SELECTED=['src','tools','data','examples','web','tests','project.godot','main.tscn','run.py','launch.pyw','dependencies.json','THIRD_PARTY_NOTICES.md','CREDITS.md','docs/licenses.md']

def need(ok,message):
    if not ok:raise RuntimeError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode,s.st_nlink,getattr(s,'st_file_attributes',0))
def read(path):
    for parent in (path,*path.parents):
        s=parent.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Alias refused: '+str(parent))
    before=identity(path.lstat());need(stat.S_ISREG(path.lstat().st_mode) and path.lstat().st_nlink==1,'Single-link regular file required')
    raw=path.read_bytes();need(identity(path.lstat())==before,'Input changed: '+str(path));return raw
def git(*args):return subprocess.check_output(['git','-c','core.quotePath=false',*args],cwd=SOURCE)
def new(path,raw):
    need(path.is_relative_to(TARGET) or path.is_relative_to(HERE),'Owned destination required')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as file:file.write(raw)
    need(read(path)==raw,'Copy readback differs')

def geometry(raw):
    need(len(raw)>=28 and struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'GLB header differs')
    count,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a and count%4==0,'GLB JSON required')
    document=json.loads(raw[20:20+count]);length,kind=struct.unpack_from('<II',raw,20+count)
    need(kind==0x004e4942 and 28+count+length==len(raw),'Embedded GLB binary required')
    def inspect(value):
        if isinstance(value,dict):
            need('uri' not in value,'External asset URI refused')
            for child in value.values():inspect(child)
        elif isinstance(value,list):
            for child in value:inspect(child)
    inspect(document)
    need(not document.get('images') and not document.get('textures'),'Generated review geometry must have no images/textures')
    return {'nodes':len(document.get('nodes',[])),'meshes':len(document.get('meshes',[])),'images':0,'external_uris':0,'bytes':len(raw),'sha256':sha(raw)}

def project(path,record):
    raw=read(path);need(len(raw)==record['bytes'] and sha(raw)==record['sha256'],'Prepared project checksum differs')
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        need(len(names)==4 and len({n.casefold() for n in names})==4,'Exact generated packed project expected')
        for info in infos:
            name=PurePosixPath(info.filename)
            need(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename and not info.is_dir() and not info.flag_bits&1 and not stat.S_ISLNK(info.external_attr>>16),'Unsafe packed member')
        header=json.loads(archive.read('has.json'));data=json.loads(archive.read('project.json'))
        need(header['format']=='hybrid_animation_studio' and header['version']==1 and header['storage']=='packed','Packed HAS required')
        payload={row['path']:row for row in header['payload']}
        need(len(payload)==3 and set(names)=={'has.json',*payload},'Closed packed inventory expected')
        for name,pin in payload.items():
            member=archive.read(name);need(len(member)==pin['bytes'] and sha(member)==pin['sha256'],'Packed payload checksum differs')
        expected={row['path']:row for row in record['embedded_assets']};actual=[]
        need(len(data['world']['objects'])==2 and len(expected)==2,'Two generated actors expected')
        for actor in data['world']['objects']:
            need(actor['path'] in expected and actor.get('reference_only') is False,'Embedded actor required')
            member=archive.read(actor['path']);pin=expected[actor['path']]
            need(sha(member)==actor['sha256']==pin['sha256'],'Embedded asset identity differs')
            actual.append(geometry(member))
        need(data['video']['lighting_mode']=='lit' and not data.get('audio'),'Lit project without external audio required')
    return raw,{'name':path.name,'bytes':len(raw),'sha256':sha(raw),'storage':'packed','embedded_generated_assets':actual,'native_or_original_art':False,'runtime_verified_here':False}

def moving_project():
    source=INTEGRATION/'output/scene-voxel-1795292706459440800/neon.has'
    raw=read(source)
    need(len(raw)==4534 and sha(raw)=='5f098ed683718dc82cf9c0057ceec0d5dde5af5eb0020e16795de79eba912c21','Qualified moving project differs')
    with zipfile.ZipFile(source) as archive:
        header=json.loads(archive.read('has.json'));data=json.loads(archive.read('project.json'))
        expected={'room.glb','actor.glb'};assets=[]
        need({row['name'] for row in data['world']['objects']}==expected,'Moving fixture actor names differ')
        for actor in data['world']['objects']:
            member=archive.read(actor['path']);assets.append({'path':actor['path'],**geometry(member)})
        gi=data['video']['scene_lighting']['indirect']
        need(data['video']['duration_frames']==4 and data['video']['fps_num']==24 and data['video']['fps_den']==1,'Qualified four-frame movie recipe required')
        need(gi.get('enabled') is True and gi.get('method')=='voxelgi','Bounded-room VoxelGI recipe required')
        model=next(row for row in data['world']['objects'] if row['name']=='actor.glb')
        need([row['frame'] for row in model['pose_keys']]==[0,1,2,3],'Qualified moving root keys required')
    _raw,audit=project(source,{'bytes':len(raw),'sha256':sha(raw),'embedded_assets':assets})
    audit.update(name='Moving room.has',frames=4,fps='24/1',review_frames=[0,1,3],indirect_method='voxelgi',baked_data_regenerated_on_open=True,qualified_origin='Primary GPU68 at28db; stable source4c contains the same runtime increment')
    return 'Moving room.has',raw,audit

def private_junko():
    source=INTEGRATION.parent/'has-hair-settling-20261121/output/generated-settling-1795291866824959600/existing/Data/prepared-junko-natural.has'
    raw=read(source)
    need(len(raw)==4983624 and sha(raw)=='40a1b48305b1bef55bfd8e74637e596bbf29e1b979edd5dd2364efe3ce468382','Expected limited private Junko project differs')
    with zipfile.ZipFile(source) as archive:
        infos=archive.infolist();names=[row.filename for row in infos]
        need(len(infos)==3 and len({name.casefold() for name in names})==3,'Exact private packed inventory required')
        need(sum(row.file_size for row in infos)<20000000,'Bounded private project required')
        for info in infos:
            name=PurePosixPath(info.filename)
            need(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename and not info.is_dir() and not info.flag_bits&1 and not stat.S_ISLNK(info.external_attr>>16),'Unsafe private member')
        header=json.loads(archive.read('has.json'));data=json.loads(archive.read('project.json'))
        need(header.get('format')=='hybrid_animation_studio' and header.get('version')==1 and header.get('storage')=='packed','Private packed format differs')
        payload=header['payload'];need(len(payload)==2 and {row['path'] for row in payload}==set(names)-{'has.json'},'Private payload closure differs')
        for row in payload:
            member=archive.read(row['path']);need(len(member)==row['bytes'] and sha(member)==row['sha256'],'Private payload hash differs')
        actors=data['world']['objects'];need(len(actors)==1 and not data.get('audio'),'One private model without audio required')
        actor=actors[0];need(actor.get('kind')=='model' and actor.get('reference_only') is False and actor['path'] in names,'Embedded private model required')
        need(actor.get('pose')=={} and actor.get('pose_keys')==[],'No baked or authored pose expected')
        metadata=actor.get('metadata',{});need(metadata.get('generated_secondary_motion')=={'format':'studio_generated_secondary_motion_1','mode':'natural'} and isinstance(metadata.get('generated_helpers'),dict),'Expected limited Natural helpers required')
        model=archive.read(actor['path']);need(sha(model)==actor['sha256'],'Private model hash differs')
        need(struct.unpack_from('<III',model)==(0x46546c67,2,len(model)),'Private GLB header differs')
        count,kind=struct.unpack_from('<II',model,12);need(kind==0x4e4f534a and count%4==0,'Private GLB JSON differs')
        doc=json.loads(model[20:20+count]);length,kind=struct.unpack_from('<II',model,20+count)
        need(kind==0x004e4942 and 28+count+length==len(model),'Private embedded binary required')
        def no_uri(value):
            if isinstance(value,dict):
                need('uri' not in value,'External private asset URI refused')
                for child in value.values():no_uri(child)
            elif isinstance(value,list):
                for child in value:no_uri(child)
        no_uri(doc)
        need(len(doc.get('images',[]))==17 and all('bufferView' in image for image in doc['images']),'Expected embedded private textures required')
    return 'Junko limited hair.has',raw,{'name':'Junko limited hair.has','bytes':len(raw),'sha256':sha(raw),'storage':'packed','generated':False,'native_or_original_art':True,'private_owner_art_local_only':True,'embedded_asset_count':1,'embedded_image_count':17,'external_uris':0,'baked_pose':False,'natural_mode':True,'supported_hair_vertices':903,'total_hair_vertices':5600,'native_quality_checks_passed':13,'native_quality_checks_total':14,'complete_hair_settling_qualified':False,'runtime_verified_here':False}


def external_runtime_requirements():
    members=[]
    for name in ['__init__.py','library/utils/pylib','blender_bindings/models/__init__.py','library/shared/content_manager/__init__.py']:
        path=SOURCEIO/name
        need(path.exists(),'Required SourceIO member missing: '+name)
        row={'path':name,'kind':'directory' if path.is_dir() else 'file'}
        if path.is_file():raw=read(path);row.update(bytes=len(raw),sha256=sha(raw))
        members.append(row)
    need(BLENDER.is_file(),'Existing Blender5.1 executable is missing')
    return {'sourceio':{'path':str(SOURCEIO),'environment_variable':'HYBRID_SOURCEIO','declared_pinned_revision':'fe24260b97ac03b899d9b5d4f0fd7b34772f3647','required_members':members,'protected_while_review_exists':True,'copied_or_installed':False,'full_sdk_commit_reverified':False},'blender_default':{'path':str(BLENDER),'protected_while_review_exists':True,'copied_or_installed':False}}

def launcher(profile,project_name=None,forward=False):
    args=(' --forward-plus' if forward else '')+(' "%~dp0Projects\\'+project_name+'.has"' if project_name else '')
    lines=['@echo off','setlocal','set "APPDATA=%~dp0Profiles\\'+profile+'\\Roaming"','set "LOCALAPPDATA=%~dp0Profiles\\'+profile+'\\Local"','set "TEMP=%~dp0Profiles\\'+profile+'\\Temp"','set "TMP=%TEMP%"','set "PYTHONDONTWRITEBYTECODE=1"','set "PYTHONNOUSERSITE=1"','set "PYTHONPATH="','set "PYTHONHOME="','set "PYTHONPYCACHEPREFIX="','set "HYBRID_PYTHON='+str(PYTHON)+'"','set "HYBRID_GODOT='+str(GODOT)+'"','set "HYBRID_SOURCEIO='+str(SOURCEIO)+'"','if not exist "%APPDATA%" mkdir "%APPDATA%"','if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%"','if not exist "%TEMP%" mkdir "%TEMP%"','pushd "%~dp0Studio"','start "" "'+str(PYTHONW)+'" "%~dp0Studio\\launch.pyw"'+args,'popd','endlocal']
    return ('\r\n'.join(lines)+'\r\n').encode('ascii')

def main():
    need(git('rev-parse','HEAD').decode().strip()==REVISION,'Source revision differs')
    need(not TARGET.exists(),'Fresh review target required')
    before={};rows=[]
    catalogue=git('ls-tree','-r','-z','HEAD','--',*SELECTED)
    for item in catalogue.split(b'\0'):
        if not item:continue
        meta,path=item.split(b'\t',1);mode,kind,blob=meta.decode().split();name=path.decode()
        if '__pycache__' in PurePosixPath(name).parts or name.endswith(('.pyc','.pyo')):continue
        need(mode in ('100644','100755') and kind=='blob','Nonregular Git source refused')
        need(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts,'Unsafe Git path')
        origin=SOURCE/name;raw=read(origin)
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob,'Current source bytes differ from committed Git blob: '+name)
        before[name]=(identity(origin.lstat()),sha(raw));rows.append({'path':name,'mode':mode,'git_blob':blob,'bytes':len(raw),'sha256':sha(raw)})
    need(len(rows)>500 and all(any(row['path']==name for row in rows) for name in ['src/app.gd','run.py','launch.pyw','tests/app_smoke.gd']),'Required source closure absent')
    # Product compile-time preloads must resolve within the copied source set.
    names={row['path'] for row in rows}
    references=set()
    for row in rows:
        if row['path'].startswith('src/') and row['path'].endswith('.gd'):
            text=read(SOURCE/row['path']).decode('utf-8')
            references.update(re.findall(r'preload\(\s*["\']res://([^"\']+)["\']\s*\)',text))
    need(references<=names,'Uncopied compile-time references: '+str(sorted(references-names)))
    prior=INTEGRATION.parent/'HAS-Review-Moving-Lights-4c0371ad'
    prep_path=prior/'PREPARATION.json';prep_raw=read(prep_path);prepared=json.loads(prep_raw)
    need(prepared['source_revision']=='4c0371ad96488c32c2e9f924967b984ab8a31884','Prior independent review required')
    records={row['sha256']:row for row in prepared['projects']};projects=[]
    for name in ['Direct lights.has','Environment bounce.has','Moving room.has']:
        origin=prior/'Projects'/name;raw=read(origin)
        need(sha(raw) in records,'Unknown prepared project')
        record=records[sha(raw)]
        embedded=[{'path':row['path'],'sha256':row['sha256']} for row in record['embedded_generated_assets']] if all('path' in row for row in record['embedded_generated_assets']) else None
        # Older generated receipt keeps hashes, not packed actor paths; derive only
        # names from its authenticated packed project and bind every asset hash.
        if embedded is None:
            with zipfile.ZipFile(origin) as archive:
                actors=json.loads(archive.read('project.json'))['world']['objects']
            allowed={row['sha256'] for row in record['embedded_generated_assets']}
            need(len(actors)==2 and all(row['sha256'] in allowed for row in actors),'Prior generated assets differ')
            embedded=[{'path':row['path'],'sha256':row['sha256']} for row in actors]
        payload,audit=project(origin,{'bytes':record['bytes'],'sha256':record['sha256'],'embedded_assets':embedded})
        audit['generated']=True;projects.append((name,payload,audit))
    projects.append(private_junko())
    for row in rows:new(TARGET/'Studio'/row['path'],read(SOURCE/row['path']))
    for name,raw,_ in projects:new(TARGET/'Projects'/name,raw)
    for name,profile,project_name,forward in [('Open Studio discovery.bat','Discovery',None,False),('Open Direct lights.bat','Direct lights','Direct lights',False),('Open Environment bounce.bat','Environment bounce','Environment bounce',True),('Open Moving room.bat','Moving room','Moving room',True),('Open Junko limited hair.bat','Junko limited hair','Junko limited hair',False)]:new(TARGET/name,launcher(profile,project_name,forward))
    readme='''# Stable HAS additions review

Source is pinned to published main 43dbdecc759e971a80f0d1e468e1e7d1e3b9ed2b
in Studio/. Evolving development and Full-verification checkouts are not used.
Prepared only: no shortcut or Studio instance was launched during preparation.

- Open Studio discovery.bat: choose New scene, then Simple Add > Asset discovery
  or Advanced Discover. Local stays offline; online metadata and thumbnail access
  require separate opt-in. Listings open the source website, not model downloads.
- Open Direct lights.bat: generated room/model/reflective prop, default renderer.
  Choose Lit, then Lights; add/edit lights and Apply. Try Undo/Redo.
- Open Environment bounce.bat: generated red-wall room, optional Forward+ SDFGI.
  In Lights, open Environment bounce. Models receive approximate bounced light;
  this shortcut uses the open-scene SDFGI method.
- Open Junko limited hair.bat: choose Natural gravity beside Hair & clothes, then
  turn Hair & clothes On. This limited existing helper chain supports 903 of 5,600
  hair vertices. Native quality remains 13/14 with the full-hair request open;
  expect a small downward response, not dramatic settling or complete hair coverage.
  Original art, shapes and skin weights are unchanged; no simulated pose is baked.
- Open Moving room.bat: qualified generated bounded-room VoxelGI example. Scrub
  Frames 0, 1 and 3 to compare the black blocker out of the bounce path, in it,
  and out again. This is a four-frame test example, not a long animation demo.
  Forward+ rebakes the room in memory on opening; give it time to settle.
  Models participate dynamically in this optional room-lighting approximation.

Each shortcut uses its own Profiles directory. Studio may also write logs/caches
under Studio/output. USERPROFILE is unchanged. Three Projects files contain self-contained generated shapes. Junko limited hair.has
is private owner-provided artwork retained only in this local review; do not publish
this review folder or its private project. All four projects have embedded assets
and no required external asset links.
Historical import paths are informational. Public procedural tutorial examples
are retained with source; they are separate from the three additions review projects.
Save edits to a new project to preserve these starting examples.

The five shortcuts set HYBRID_SOURCEIO to the existing approved pinned runtime.
That external directory and the existing Blender5.1 default executable must remain
available while this review exists. They were checked read-only, not copied,
installed or launched. USERPROFILE and the existing MMDTools discovery stay unchanged.

This is source-pinned review material using the existing Python/Godot/FFmpeg
installations, not a clean-install or standalone distribution. No runtime or
visual acceptance of these shortcuts is claimed. PREPARATION.json records the
source Git blobs/raw hashes, packed-payload checks and unchanged-source audit.
'''
    new(TARGET/'README.md',readme.encode())
    tools=[]
    for path in [PYTHON,PYTHONW,GODOT,BLENDER]:raw=read(path);tools.append({'path':str(path),'bytes':len(raw),'sha256':sha(raw)})
    for name,(stamp,digest) in before.items():need(identity((SOURCE/name).lstat())==stamp and sha(read(SOURCE/name))==digest,'Source changed during preparation: '+name)
    need(git('rev-parse','HEAD').decode().strip()==REVISION,'Source HEAD changed')
    files=[]
    for path in sorted(TARGET.rglob('*')):
        if path.is_file():raw=read(path);files.append({'path':path.relative_to(TARGET).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    result={'status':'PREPARED_NOT_RUNTIME_VERIFIED','studio_launched':False,'graphics_or_engine_requested':False,'network_requested':False,'source_revision':REVISION,'source_root':str(SOURCE),'target':str(TARGET),'source_files':len(rows),'source_bytes':sum(x['bytes'] for x in rows),'source_inventory':rows,'git_blob_modes_checked':True,'compile_time_res_preloads_resolve':True,'source_identity_and_head_preserved':True,'external_runtime_dependencies':external_runtime_requirements(),'original_prepared_metadata_sha256':sha(prep_raw),'projects':[x[2] for x in projects],'existing_runtimes':tools,'files':files,'total_files_excluding_this_receipt':len(files),'total_bytes_excluding_this_receipt':sum(x['bytes'] for x in files),'isolated_profiles_per_shortcut':True,'userprofile_changed':False,'no_git_or_archive_or_cache_tree_copied':True}
    raw=(json.dumps(result,indent=2)+'\n').encode();new(TARGET/'PREPARATION.json',raw);new(HERE/'PREPARATION.json',raw)
    new(HERE/'README.md',('Stable owner review preparation only. See PREPARATION.json. No engines/apps launched. Source '+REVISION+'; source files and Git HEAD were preserved; writes were limited to this new preparation and review folder. Only source/recipe/hash metadata is archived here; prepared projects remain at '+str(TARGET)+'.\n').encode())
    print(json.dumps({'status':result['status'],'path':str(TARGET),'source_files':len(rows),'total_files':len(files)+1,'total_bytes':result['total_bytes_excluding_this_receipt']+len(raw)}))

if __name__=='__main__':main()

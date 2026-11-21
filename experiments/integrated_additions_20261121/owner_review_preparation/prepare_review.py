"""Prepare small owner-operated launchers and audit generated packed projects.
Does not run Studio,Godot,converters or a browser. Writes only beside this file.
"""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,os,stat,struct,zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PYTHONW=Path('C:/Program Files/Python313/pythonw.exe')
PYTHON=PYTHONW.with_name('python.exe')
SPECS=[('Direct lights','scene-lighting-1795285771388820600',False,
        {'environment.glb','model.glb'}),
       ('Environment bounce','scene-indirect-1795285826348840900',True,
        {'room.glb','actor.glb'})]


def need(ok,message):
    if not ok:raise RuntimeError(message)


def identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode,s.st_nlink,getattr(s,'st_file_attributes',0))


def read(path):
    for part in (path,*path.parents):
        s=part.lstat();need(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'Alias refused')
    before=identity(path.stat());raw=path.read_bytes();need(before==identity(path.stat()),'Input changed')
    need(stat.S_ISREG(path.stat().st_mode) and path.stat().st_nlink==1,'Regular single-link input required')
    return raw


def sha(raw):return hashlib.sha256(raw).hexdigest()


def glb(raw):
    need(len(raw)>=28 and struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Invalid GLB header')
    size,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a and size%4==0,'Embedded JSON required')
    doc=json.loads(raw[20:20+size]);binary_size,binary_kind=struct.unpack_from('<II',raw,20+size)
    need(binary_kind==0x004e4942 and 28+size+binary_size==len(raw),'Embedded binary required')
    need(not doc.get('images') and not doc.get('textures'),'Generated fixtures must contain no image artwork')
    def no_uri(value):
        if isinstance(value,dict):
            need('uri' not in value,'External or image URI refused')
            for child in value.values():no_uri(child)
        elif isinstance(value,list):
            for child in value:no_uri(child)
    no_uri(doc)
    need(len(doc.get('buffers',[]))==1 and doc['buffers'][0]['byteLength']<=binary_size,'Self-contained GLB buffer required')
    return {'nodes':len(doc.get('nodes',[])),'meshes':len(doc.get('meshes',[])),
            'images':0,'textures':0,'external_uris':0,'bytes':len(raw),'sha256':sha(raw)}


def inspect(source,expected_names,indirect):
    before=identity(source.stat());raw=read(source)
    with zipfile.ZipFile(source) as archive:
        names=archive.namelist();need(len(names)==4 and len({n.casefold() for n in names})==4,'Exact two-asset HAS required')
        for info in archive.infolist():
            p=PurePosixPath(info.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                 and not info.is_dir() and not info.flag_bits&1
                 and not stat.S_ISLNK(info.external_attr>>16),'Unsafe archive member')
        header=json.loads(archive.read('has.json'));project=json.loads(archive.read('project.json'))
        need(header.get('format')=='hybrid_animation_studio' and header.get('version')==1
             and header.get('storage')=='packed','Project must be packed,not linked')
        need(project.get('schema_version')==4 and project.get('audio')=={}
             and all(not row.get('cels') for row in project.get('layers',[])),'Only generated3D fixture content allowed')
        actors=project['world']['objects'];need(len(actors)==2 and {a['name'] for a in actors}==expected_names,'Unexpected fixture objects')
        assets={row['path']:row for row in header['assets']};payload={row['path']:row for row in header['payload']}
        need(len(assets)==2 and set(payload)=={'project.json',*assets}
             and set(names)=={'has.json',*payload},'Packed inventory closure required')
        for name,row in payload.items():
            member=archive.read(name);need(len(member)==row['bytes'] and sha(member)==row['sha256'],'Payload checksum differs')
        rows=[]
        for actor in actors:
            need(actor.get('reference_only') is False and actor['path'] in assets,'Embedded actor reference required')
            record=assets[actor['path']];need('reference' not in record and record['sha256']==actor['sha256'],'Linked reference refused')
            metadata=actor.get('metadata',{});need(set(metadata)<= {'import_source','source_shape'},'Unexpected original/native provenance')
            original=Path(metadata['import_source']).resolve(strict=True)
            need(original.parent==source.parent and original.name==actor['name'],'Fixture source path differs')
            member=archive.read(actor['path']);need(sha(read(original))==sha(member),'Generated stage source and packed asset differ')
            rows.append({'name':actor['name'],'path':actor['path'],**glb(member)})
        light=project['video']['scene_lighting'];need(project['video']['lighting_mode']=='lit','Lit starting view required')
        need(bool(light.get('indirect',{}).get('enabled',False))==indirect,'Requested lighting mode differs')
    need(identity(source.stat())==before,'Original project changed during inspection')
    return raw,{'source':str(source),'bytes':len(raw),'sha256':sha(raw),'storage':'packed',
                'embedded_assets':rows,'linked_assets':0,'portable_playback_references':True,
                'historical_import_source_metadata_is_informational':True,'generated_shapes_only':True,
                'original_art_or_textures':False,'runtime_verified_here':False}


def write(name,raw):
    target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(raw)
    need(read(target)==raw,'Review artifact readback differs')


def launcher(profile,project=None,forward=False):
    args=(' --forward-plus' if forward else '')+(' "%~dp0Projects\\'+project+'.has"' if project else '')
    lines=['@echo off','setlocal',
           'set "APPDATA=%~dp0Profiles\\'+profile+'\\Roaming"',
           'set "LOCALAPPDATA=%~dp0Profiles\\'+profile+'\\Local"',
           'set "TEMP=%~dp0Profiles\\'+profile+'\\Temp"','set "TMP=%TEMP%"',
           'set "PYTHONDONTWRITEBYTECODE=1"','set "PYTHONNOUSERSITE=1"',
           'set "PYTHONPATH="','set "PYTHONHOME="','set "PYTHONPYCACHEPREFIX="',
           'set "HYBRID_PYTHON='+str(PYTHON)+'"',
           'if not exist "%APPDATA%" mkdir "%APPDATA%"',
           'if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%"',
           'if not exist "%TEMP%" mkdir "%TEMP%"',
           'start "" "'+str(PYTHONW)+'" "'+str(ROOT/'launch.pyw')+'"'+args,'endlocal']
    return ('\r\n'.join(lines)+'\r\n').encode('ascii')


def main():
    need(HERE==Path('C:/a/Programming/cloudflare/has-discovery-lights-integration-20261121/output/owner-review-integrated'), 'Exact owned review folder required')
    need({p.name for p in HERE.iterdir()}=={'prepare_review.py'},'Review folder must be fresh')
    for path in (PYTHONW,PYTHON,ROOT/'launch.pyw',ROOT/'run.py',ROOT/'project.godot'):read(path)
    ast.parse(read(ROOT/'run.py').decode('utf-8'))
    originals=[];projects=[]
    # Complete portability/art checks before copying either generated project.
    for title,stage,forward,names in SPECS:
        source=ROOT/'output'/stage/'neon.has';raw,audit=inspect(source,names,forward)
        originals.append((source,identity(source.stat()),sha(raw)));projects.append((title,raw,audit))
    for title,raw,_audit in projects:write('Projects/'+title+'.has',raw)
    write('Open Studio discovery.bat',launcher('Discovery'))
    write('Open Direct lights.bat',launcher('Direct lights','Direct lights'))
    write('Open Environment bounce.bat',launcher('Environment bounce','Environment bounce',True))
    readme='''# Integrated Studio review

Prepared only; Studio has not been launched from these shortcuts.

- **Open Studio discovery.bat** starts an empty Studio. Choose New scene, then Simple **Add > Asset discovery…**, or Advanced **Discover**. Local stays offline: choose directories and filter filenames. Online access and thumbnail previews require separate opt-in; online listings open their source website in your default browser, rather than downloading models.
- **Open Direct lights.bat** opens a generated room, model and reflective prop with the default Compatibility renderer. Choose **Lit**, then **Lights…** beside the lighting menu. Advanced exposes the full workspace. Add Directional, Point or Spot lights, select a row, edit color/intensity/shadows and **Apply light**. Expand Placement and beam to move or aim a lamp. Presets and edits support Undo/Redo.
- **Open Environment bounce.bat** uses optional Forward+ for a generated red-wall room and skinned panel. In Lights, expand **Environment bounce (SDFGI prototype, Forward+)**. Static environment geometry contributes bounced color; models receive it but do not provide dynamic indirect shadows. Rebuild after moving the room. The settling-frame budget spends rendering time; it is not path tracing or a guarantee for arbitrary scenes. Forward+ can cost more GPU time.

Each shortcut has its own Windows user-data profile under Profiles. Normal project work and launch logs can also appear in the source checkout output folder. USERPROFILE is unchanged. The two Projects/*.has files are packed, self-contained generated shapes with no original model artwork or external asset links. Their historical import-source paths are provenance only. Save any edits to a new project if you want to retain these starting examples.

These launchers use the current integration source checkout and existing Python installation. This folder is not a standalone packaged Studio build; keep the source checkout available. PREPARATION.json records the portability checks and artifact hashes.
'''
    write('README.md',readme.encode('utf-8'))
    for path,stamp,digest in originals:need(identity(path.stat())==stamp and sha(read(path))==digest,'Original generated project changed')
    files=[]
    for path in sorted(HERE.rglob('*')):
        if path.is_file():raw=read(path);files.append({'path':path.relative_to(HERE).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
    source_names=['launch.pyw','run.py','project.godot','tests/scene_lighting_smoke.gd','tests/scene_indirect_smoke.gd','tests/posed_bounds_fixture.gd']
    result={'status':'PREPARED_NOT_RUNTIME_VERIFIED','studio_launched':False,'network_requested':False,
            'source_mode':'current_integration_checkout_not_standalone','source_root':str(ROOT),
            'pythonw':{'path':str(PYTHONW),'bytes':len(read(PYTHONW)),'sha256':sha(read(PYTHONW))},
            'projects':[audit for _title,_raw,audit in projects],
            'launch_semantics':{'entry':'launch.pyw -> run.main(quiet=True)','project_argument':'positional .has',
                    'direct_renderer':'default gl_compatibility','indirect_renderer':'--forward-plus',
                    'test_headless_script_or_private_desktop_flags':False,'interactive_owner_launch':True,
                    'appdata_and_localappdata_separate_per_shortcut':True,'userprofile_changed':False},
            'source_pins':[{'path':name,'sha256':sha(read(ROOT/name))} for name in source_names],
            'files':files,'total_artifact_bytes_excluding_manifest':sum(row['bytes'] for row in files)}
    write('PREPARATION.json',(json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({'status':result['status'],'projects':2,'launchers':3,'bytes':result['total_artifact_bytes_excluding_manifest']}))


if __name__=='__main__':main()

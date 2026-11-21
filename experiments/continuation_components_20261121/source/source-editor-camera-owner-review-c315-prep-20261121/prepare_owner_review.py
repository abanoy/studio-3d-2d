"""Prepare or audit one exact c315 owner review; never launch Studio or converters."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,stat,subprocess,sys,time,uuid
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REVIEW=ROOT.parent/'HAS-Review-Editor-Camera-c31576d'
OLD=ROOT.parent/'HAS-Review-Editor-Camera-435dc02'
REV='c31576d0c1d84030d51ec886f2f3976a60a70c7b'
OLD_PIN=(118999,'6d9d453e0d2d23b425245f318a130440f0f9841bfdbdf6804c8aa6c22dc758d4')
CAT_PIN=(270172,'d671a5e2dc73851ce34692cf07def321e12a1a13a8445f6ae9b86782dc752c01')
BUILDER_PIN=(11389,'48d6fc852ae16c946431addd39ec152e5db45c7f887bc1ddc941fc332911a0ce')
PYTHONW=Path('C:/Program Files/Python313/pythonw.exe')
LABELS=('Junko hair review','Saved face scene','Saved fan scene')
README='''PREPARED_NOT_RUNTIME_VERIFIED

This separate review contains the committed c315 editor and camera changes.
It has not been opened or privately replayed yet. The complete c315 Full run
was still pending at preparation; no Full qualification is claimed here.

When the review has been cleared for use, Open Junko hair review.bat opens the
hair scene. Open Saved face scene.bat and Open Saved fan scene.bat open copies
of your earlier saved scenes. Start review.bat starts an empty Studio.
Nothing here replaces the installed Studio or changes the original projects.

Included editor changes have separate scoped evidence:111 editor controls and
515 camera controls. Shapes can be resized. Settings has a pose-handle size
control independent of interface zoom. Camera keys can be double-clicked and
moved; Ctrl+wheel changes the timeline scale. RMB+wheel changes the temporary
camera lens; save a camera key explicitly when you want to keep that lens.

The saved face and fan scenes remain useful issue examples. Their presence
does not mean the face-distance or hair-collision problems have been fixed.
This baseline has no experimental posed-bounds, easing or Miku-contact overlay.

This folder uses a new independent preferences profile. Save your edits under a
new name if you want to preserve the supplied review copy. Older reviews stay
where they were. This preparation has not asked for any manual check.
'''

def need(value,label):
    if not value:raise RuntimeError(label)
def identity(path):
    value=path.lstat()
    return tuple(str(v) for v in (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_nlink,value.st_mode,getattr(value,'st_file_attributes',0)))
def safe(path,missing=False):
    for part in reversed((path,*path.parents)):
        if missing and not os.path.lexists(part):continue
        value=part.lstat()
        need(not stat.S_ISLNK(value.st_mode) and not getattr(value,'st_file_attributes',0)&0x400,'ALIAS_PATH')
    return path
def raw(path):
    safe(path);before=identity(path);info=path.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'REGULAR_SINGLE_LINK_REQUIRED')
    data=path.read_bytes();need(identity(path)==before,'INPUT_CHANGED_DURING_READ');return data
def sha(data):return hashlib.sha256(data).hexdigest()
def pin(path):
    before=identity(path);data=raw(path);need(identity(path)==before,'PIN_CHANGED')
    return {'bytes':len(data),'sha256':sha(data),'identity':list(before)}
def pinned(path,expected):
    data=raw(path);need((len(data),sha(data))==expected,'FROZEN_INPUT_PIN_CHANGED');return data

def new(path,data):
    safe(path,missing=True)
    with path.open('xb') as stream:stream.write(data)
def json_new(path,value):new(path,(json.dumps(value,indent=2)+'\n').encode())
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
def source_module(path,pin_value):
    data=pinned(path,pin_value);name='_owner_review_c315_snapshot'
    module=importlib.util.module_from_spec(importlib.util.spec_from_loader(name,loader=None))
    module.__file__=str(path);sys.modules[name]=module;exec(compile(data,str(path),'exec'),module.__dict__);return module

def old_inputs():
    old_manifest_pin=pin(OLD/'PREPARATION.json')
    document=json.loads(pinned(OLD/'PREPARATION.json',OLD_PIN))
    need(document['source_commit']=='435dc02426a7cdd313e43fe674c9008520845428' and len(document['projects'])==3,'EXACT_OLD_REVIEW_SCOPE')
    projects=[]
    for index,entry in enumerate(document['projects']):
        source=Path(entry['source']);before=pin(source);old_pin=entry['source_pin']
        need((before['bytes'],before['sha256'])==(old_pin['bytes'],old_pin['sha256']),'PROTECTED_PROJECT_BYTES_CHANGED')
        need(before['identity'][:5]==[str(v) for v in old_pin['identity']],'PROTECTED_PROJECT_STAMPS_CHANGED')
        legacy_copy=Path(entry['copy']);legacy_pin=pin(legacy_copy)
        need((legacy_pin['bytes'],legacy_pin['sha256'])==(old_pin['bytes'],old_pin['sha256']),'OLDER_REVIEW_COPY_CHANGED')
        projects.append({'label':LABELS[index],'source':str(source),'source_pin':before,'older_review_copy':str(legacy_copy),'older_review_copy_pin':legacy_pin})
    return old_manifest_pin,projects

def preserve_old(old_pin,projects):
    need(pin(OLD/'PREPARATION.json')==old_pin,'OLDER_PREPARATION_CHANGED')
    for row in projects:
        need(pin(Path(row['source']))==row['source_pin'],'ORIGINAL_PROJECT_CHANGED')
        need(pin(Path(row['older_review_copy']))==row['older_review_copy_pin'],'OLDER_PROJECT_COPY_CHANGED')

def catalogue():
    doc=json.loads(pinned(ROOT/'output/IMPORT_OFF_FINAL_FUNCTIONAL_CATALOGUE_20261121.json',CAT_PIN))
    need(type(doc) is dict and len(doc)==1103,'EXACT_MAIN_SOURCE_COUNT')
    for name,row in doc.items():
        data=raw(ROOT/name)
        need((len(data),sha(data))==(row['bytes'],row['sha256']),'MAIN_SOURCE_CHANGED')
        need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1'],'MAIN_SOURCE_GIT_BYTES')
    return {name:pin(ROOT/name) for name in doc}
def preserve_main(values):
    need(git('rev-parse','HEAD').decode().strip()==REV,'MAIN_REVISION_CHANGED')
    for name,row in values.items():need(pin(ROOT/name)==row,'MAIN_SOURCE_NOT_PRESERVED')

def bat_text(label=None):
    project=(' "%~dp0Examples/'+label+'.has"') if label else ''
    return ('@echo off\r\nsetlocal\r\nset "PYTHONDONTWRITEBYTECODE=1"\r\n'
            'cd /d "%~dp0Studio"\r\nstart "" "'+str(PYTHONW)+'" "%~dp0Studio/launch.pyw"'+project+'\r\n').encode('utf-8')

def tree(folder):
    found=set()
    for directory,dirs,files in os.walk(safe(folder),followlinks=False):
        for leaf in dirs:safe(Path(directory)/leaf)
        for leaf in files:
            target=Path(directory)/leaf;raw(target);found.add(target.relative_to(folder).as_posix())
    return found

def audit(snapshot,preflight):
    manifest=json.loads(raw(REVIEW/'PREPARATION.json'))
    need(manifest['status']=='PREPARED_NOT_RUNTIME_VERIFIED' and manifest['source_commit']==REV and manifest['source_mode']=='git_revision_runtime_scope','REVIEW_SCOPE_CHANGED')
    hashes=manifest['source_hashes'];need(len(hashes)==1106,'EXACT1106_SOURCE_FILES')
    for name,digest in hashes.items():snapshot.validate_name(name);need(sha(raw(REVIEW/'Studio'/name))==digest,'REVIEW_SOURCE_BYTES_CHANGED')
    need(raw(REVIEW/'Studio/override.cfg')==('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(manifest['profile'])+'\n').encode(),'REVIEW_PROFILE_CHANGED')
    need(manifest['graphics_launched'] is False and manifest['normal_startup_verified'] is False and manifest['package_replay_verified'] is False,'NO_RUNTIME_VERIFICATION_CLAIM')
    for row in manifest['projects']:
        need(pin(Path(row['source']))==row['source_pin'] and pin(Path(row['copy']))==row['copy_pin'],'REVIEW_PROJECT_CHANGED')
        preflight(Path(row['source']));preflight(Path(row['copy']))
    for row in manifest['launchers']:
        data=raw(REVIEW/row['path']);need((len(data),sha(data))==(row['bytes'],row['sha256']) and data==bat_text(row['project_label']),'REVIEW_LAUNCHER_CHANGED')
    need(raw(REVIEW/'README.txt')==README.encode(),'REVIEW_README_CHANGED')
    expected={'Studio/'+name for name in hashes}|{'Studio/override.cfg','README.txt','PREPARATION.json'}
    expected|={'Examples/'+label+'.has' for label in LABELS}|{row['path'] for row in manifest['launchers']}
    need(tree(REVIEW)==expected,'UNEXPECTED_REVIEW_FILES_OR_RUNTIME_CACHE')
    return {'status':'PREPARED_NOT_RUNTIME_VERIFIED','review':str(REVIEW),'source_files':1106,'source_exact':True,'projects':3,'launchers':4,'total_files':len(expected),'graphics_launched':False,'startup_verified':False,'package_replay_verified':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare-no-launch',action='store_true');mode.add_argument('--audit-only',action='store_true')
    options=parser.parse_args()
    need(os.name=='nt' and sys.version_info[:2]==(3,13) and not sys.flags.optimize,'WINDOWS313_NORMAL_ASSERTIONS')
    before_env=dict(os.environ);need(git('rev-parse','HEAD').decode().strip()==REV,'EXACT_C315_MAIN_REQUIRED')
    main_pins=catalogue();old_pin,projects=old_inputs();pythonw_pin=pin(PYTHONW)
    snapshot=source_module(ROOT/'tools/build_owner_review_snapshot.py',BUILDER_PIN)
    need(snapshot.ROOT==ROOT,'SNAPSHOT_ROOT_CHANGED')
    sys.path.insert(0,str(ROOT));from tools.has_project import preflight_archive
    if options.prepare_no_launch:
        safe(REVIEW,missing=True);need(not os.path.lexists(REVIEW),'FRESH_REVIEW_ONLY')
        for row in projects:preflight_archive(Path(row['source']))
        REVIEW.mkdir(exist_ok=False)
        revision,hashes=snapshot.freeze_source(ROOT,REVIEW/'Studio',REV,runtime_scope=True)
        need(revision==REV and len(hashes)==1106,'EXACT_COMMITTED1106_RUNTIME')
        profile='HAS Editor Camera c315 Review '+uuid.uuid4().hex
        new(REVIEW/'Studio/override.cfg',('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
        (REVIEW/'Examples').mkdir()
        for row in projects:
            target=REVIEW/'Examples'/(row['label']+'.has');new(target,raw(Path(row['source'])))
            need(pin(target)['sha256']==row['source_pin']['sha256'],'COPIED_PROJECT_BYTES_DIFFER')
            preflight_archive(target);row.update(copy=str(target),copy_pin=pin(target),original_preflight_passed=True,copy_preflight_passed=True)
        launchers=[]
        for label in (None,*LABELS):
            name='Start review.bat' if label is None else 'Open '+label+'.bat';data=bat_text(label);new(REVIEW/name,data)
            launchers.append({'path':name,'project_label':label,'bytes':len(data),'sha256':sha(data),'owner_operated_only':True})
        new(REVIEW/'README.txt',README.encode())
        result={'format':'has_editor_camera_c315_owner_review_prepared_1','status':'PREPARED_NOT_RUNTIME_VERIFIED','source_commit':revision,'source_mode':'git_revision_runtime_scope','source_hashes':hashes,'source_file_count':1106,'profile':profile,'projects':projects,'launchers':launchers,'pythonw':{'path':str(PYTHONW),'pin':pythonw_pin},'builder_pin':{'bytes':BUILDER_PIN[0],'sha256':BUILDER_PIN[1]},'preparation_script_pin':pin(Path(__file__)),'older_review_preparation_pin':old_pin,'scoped_validation':{'editor_controls':111,'camera_interactions':515,'Full_qualified':False},'experimental_overlays':False,'graphics_launched':False,'normal_startup_verified':False,'package_replay_verified':False,'launchers_created':True,'private_art_uploaded':False,'installed_studio_replaced':False,'owner_originals_modified':False,'retention':'Preserve this review, older reviews and original projects until runtime validation and owner observations.'}
        json_new(REVIEW/'PREPARATION.json',result)
    value=audit(snapshot,preflight_archive)
    preserve_old(old_pin,projects);preserve_main(main_pins);need(pin(PYTHONW)==pythonw_pin,'INSTALLED_PYTHONW_CHANGED')
    need(dict(os.environ)==before_env,'PARENT_ENVIRONMENT_CHANGED')
    print(json.dumps(value,indent=2))
if __name__=='__main__':main()

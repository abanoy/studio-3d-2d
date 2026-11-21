"""Prepare exact committed runtime and copied packed projects; no app launch."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys,time

ROOT=Path(__file__).resolve().parents[1]
REVIEW=Path('C:/a/Programming/cloudflare/HAS-Review-Editor-Camera-435dc02')
REV='435dc02426a7cdd313e43fe674c9008520845428'
spec=importlib.util.spec_from_file_location('review_snapshot',ROOT/'tools/build_owner_review_snapshot.py')
snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)
sys.path.insert(0,str(ROOT))
from tools.has_project import preflight_archive

def identity(path):
    s=path.stat()
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink)
def pin(path):
    before=identity(path);raw=path.read_bytes()
    assert identity(path)==before
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':list(before)}
assert not REVIEW.exists()
REVIEW.mkdir()
revision,hashes=snapshot.freeze_source(ROOT,REVIEW/'Studio',REV,runtime_scope=True)
assert revision==REV and not (REVIEW/'Studio/.godot').exists() and not (REVIEW/'Studio/output').exists()
profile='HAS Editor Camera Review '+str(time.time_ns())
(REVIEW/'Studio/override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
projects=[
 ('Junko hair joints',Path('C:/a/Programming/cloudflare/HAS-Review-Neon-973039e-native/Examples/Junko imported hair joints.has')),
 ('Close-up face',ROOT/'output/owner-stuff-project-1795238638994/stuff.has'),
 ('Miku fan',ROOT/'output/owner-stuff2-project-1795240462119/stuff2.has')]
(REVIEW/'Examples').mkdir()
copied=[]
for label,source in projects:
    before=pin(source);preflight_archive(source)
    target=REVIEW/'Examples'/(label+'.has')
    shutil.copy2(source,target)
    assert pin(source)==before and pin(target)['sha256']==before['sha256']
    preflight_archive(target)
    copied.append({'label':label,'source':str(source),'copy':str(target),'source_pin':before})
assert all(hashlib.sha256((REVIEW/'Studio'/name).read_bytes()).hexdigest()==digest for name,digest in hashes.items())
result={'format':'has_editor_camera_review_prepared_1','status':'PREPARED_NOT_RUNTIME_VERIFIED',
 'source_commit':revision,'source_mode':'git_revision_runtime_scope','source_hashes':hashes,
 'profile':profile,'projects':copied,'private_art_uploaded':False,'installed_studio_replaced':False,
 'normal_startup_verified':False,'package_replay_verified':False,'launchers_created':False,
 'retention':'Keep review and private packages pending runtime validation and owner observations.'}
(REVIEW/'PREPARATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(ROOT/'output/UI_CAMERA_REVIEW_PREPARED_20261121.json').write_text(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','projects')},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'folder':str(REVIEW),'source_files':len(hashes),'projects':len(copied),'graphics_launched':False}))

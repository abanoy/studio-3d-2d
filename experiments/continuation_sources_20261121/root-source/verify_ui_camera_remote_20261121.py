from pathlib import Path
import hashlib,json,subprocess,time

CONTROL=Path(__file__).resolve().parent
ROOT=Path('C:/a/Programming/cloudflare/has-ui-camera-full-20261121-435dc02')
REV='435dc02426a7cdd313e43fe674c9008520845428'
def git(*args):
    return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT)
def remote():
    return git('ls-remote','origin','refs/heads/main').decode().split()[0]
started=time.time_ns()
assert remote()==REV
assert git('rev-parse','HEAD').decode().strip()==REV
assert git('rev-parse','HEAD^').decode().strip()=='59a112a08373f12dcf771c21734b35391b757d4e'
assert git('rev-parse','HEAD^{tree}').decode().strip()=='1a9172086254bf9f93c99a708f5794131af384f9'
assert git('config','--local','core.autocrlf').decode().strip()=='false'
expected=json.loads((CONTROL/'UI_CAMERA_FINAL_INDEX_VERIFIED_20261121.json').read_bytes())['paths']
selected={r['path']:r for r in expected}
changed=set(git('diff-tree','--no-commit-id','--name-only','-r','-z','HEAD').decode().rstrip('\0').split('\0'))
assert len(selected)==1094 and changed==set(selected)
tree={}
for raw in git('ls-tree','-rz','HEAD').split(b'\0'):
    if not raw: continue
    meta,name=raw.split(b'\t',1)
    mode,kind,oid=meta.decode().split()
    tree[name.decode()]={'mode':mode,'kind':kind,'oid':oid}
def check(row,mode=False):
    path=row['path'];raw=(ROOT/path).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],path
    oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert oid==row['git_sha1']==tree[path]['oid'] and tree[path]['kind']=='blob',path
    if mode: assert row['mode']==tree[path]['mode'],path
for row in expected: check(row,True)
source=json.loads((CONTROL/'UI_CAMERA_FINAL_SOURCE_20261121.json').read_bytes())['files']
assert len(source)==1102
for row in source: check(row)
assert not git('status','--porcelain')
assert remote()==REV
result={'format':'has_ui_camera_fresh_remote_verification_1','status':'PASS','revision':REV,
 'tree':'1a9172086254bf9f93c99a708f5794131af384f9','fresh_clone':str(ROOT),
 'selected_paths':len(expected),'functional_sources':len(source),
 'selected_bytes':sum(r['bytes'] for r in expected),'all_raw_sizes_sha256_git_blobs_and_modes_verified':True,
 'remote_main_before_and_after':REV,'clean_checkout_before_staging_fixtures':True,
 'seconds':(time.time_ns()-started)/1e9,'paths':expected}
(CONTROL/'UI_CAMERA_REMOTE_VERIFIED_20261121.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='paths'}))

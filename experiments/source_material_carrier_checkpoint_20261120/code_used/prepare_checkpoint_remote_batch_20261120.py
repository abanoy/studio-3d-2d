"""Root: prepare exact immutable Git bytes without one Git process per file."""
from pathlib import Path, PurePosixPath
import hashlib,json,os,stat,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REV,OUTPUT=sys.argv[1:]
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def git(*args):
    return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT,creationflags=FLAGS)
names=[raw.decode('utf8') for raw in git('diff-tree','--no-commit-id','--name-only','-z','-r',REV).split(b'\0') if raw]
assert names and len(set(names))==len(names)
for name in names:
    p=PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts and not any(ord(c)<32 for c in name)
requests=''.join(REV+':'+name+'\n' for name in names).encode('utf8')
process=subprocess.Popen(['git','-c','core.autocrlf=false','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=FLAGS)
try:
    raw,stderr=process.communicate(requests,timeout=120)
except BaseException:
    if process.poll() is None:process.kill()
    process.wait()
    raise
assert process.returncode==0 and len(raw)<=128*1024*1024,('cat_file_refused',process.returncode)
rows=[]; pos=0
for name in names:
    end=raw.index(b'\n',pos); header=raw[pos:end].split(); assert len(header)==3 and header[1]==b'blob'
    oid=header[0].decode('ascii'); size=int(header[2]); assert len(oid)==40 and 0<=size<=16*1024*1024
    pos=end+1; payload=raw[pos:pos+size]; pos+=size
    assert len(payload)==size and raw[pos:pos+1]==b'\n'; pos+=1
    p=ROOT/name; before=p.lstat(); assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and not getattr(before,'st_file_attributes',0)&0x400
    actual=p.read_bytes(); after=p.lstat(); assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and actual==payload,name
    digest=hashlib.sha256(payload).hexdigest(); blob=hashlib.sha1(b'blob '+str(size).encode()+b'\0'+payload).hexdigest(); assert oid==blob
    rows.append({'path':name,'bytes':size,'sha256':digest,'git_sha1':blob})
assert pos==len(raw)
result={'commit':REV,'parent':git('rev-parse',REV+'^').decode().strip(),'files':rows,'count':len(rows),'total_bytes':sum(row['bytes'] for row in rows),'git_batch_process_reaped':True}
p=ROOT/OUTPUT; assert p.resolve().is_relative_to(ROOT/'output') and not p.exists()
encoded=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode('utf8'); p.write_bytes(encoded)
print(json.dumps({'commit':REV,'parent':result['parent'],'count':len(rows),'total_bytes':result['total_bytes'],'expected_bytes':len(encoded),'expected_sha256':hashlib.sha256(encoded).hexdigest(),'git_batch_process_reaped':True}))
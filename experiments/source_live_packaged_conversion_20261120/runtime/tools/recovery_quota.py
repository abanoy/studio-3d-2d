"""Cross-process recovery admission. Reservations protect writes, never delete data."""
from pathlib import Path
import base64
import json
import os
import re
import stat
import sys
import tempfile
try:
    from .has_project import save_lock
    from .recovery_processes import details
except ImportError:
    from has_project import save_lock
    from recovery_processes import details

MAX_BYTES=512*1024*1024
MAX_REGISTRY=131072
MAX_RESERVATIONS=64

def identity(value):
    if not isinstance(value,dict) or type(value.get('pid')) is not int or not 1<=value['pid']<=2147483647:
        raise ValueError('Invalid recovery quota owner')
    field='linux_start' if sys.platform=='linux' else 'created_100ns' if os.name=='nt' else ''
    if not field or not isinstance(value.get(field),str) or len(value[field])>80:
        raise ValueError('Recovery quota needs a verified process incarnation')
    pattern=r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}:[1-9][0-9]{0,19}' if field=='linux_start' else r'[1-9][0-9]{0,19}'
    if not re.fullmatch(pattern,value[field]) or int(value[field].split(':')[-1])>18446744073709551615:
        raise ValueError('Invalid recovery process incarnation')
    return {'pid':value['pid'],field:value[field]}

def matches(owner,observed):
    key=str(owner['pid'])
    field='linux_start' if 'linux_start' in owner else 'created_100ns'
    return observed['owners'].get(key)=='alive' and observed.get(field,{}).get(key)==owner[field]

def expired(owner,observed):
    key=str(owner['pid']);field='linux_start' if 'linux_start' in owner else 'created_100ns'
    current=observed.get(field,{}).get(key)
    return observed['owners'].get(key)=='exited' or observed['owners'].get(key)=='alive' and isinstance(current,str) and current!=owner[field]

def occupied(root,depth=0):
    if depth>4:raise ValueError('Recovery quota cannot inspect an excessively deep cache')
    total=0
    for path in root.iterdir():
        row=path.lstat()
        if stat.S_ISLNK(row.st_mode):raise ValueError('Linked recovery cache entry refused; previous checkpoint preserved')
        if stat.S_ISDIR(row.st_mode):total+=occupied(path,depth+1)
        elif stat.S_ISREG(row.st_mode):total+=row.st_size
        else:raise ValueError('Unsupported recovery cache entry')
        if total>MAX_BYTES:return total
    return total

def operation(root,action,token,owner,reserve=0):
    root=Path(root).absolute()
    for part in [root,*root.parents]:
        if part.is_symlink():raise ValueError('Linked recovery root refused')
    root.mkdir(parents=True,exist_ok=True)
    owner=identity(owner)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',token):raise ValueError('Invalid recovery reservation token')
    if action not in ('reserve','release') or type(reserve) is not int or not 0<=reserve<=MAX_BYTES:raise ValueError('Invalid recovery quota request')
    index=root/'.quota.json'
    with save_lock(root/'.quota','recovery quota'):
        rows={}
        if index.exists() or index.is_symlink():
            row=index.lstat()
            if not stat.S_ISREG(row.st_mode) or row.st_nlink!=1 or row.st_size>MAX_REGISTRY:raise ValueError('Unsafe recovery reservation registry')
            parsed=json.loads(index.read_bytes())
            if not isinstance(parsed,dict) or parsed.get('format')!='studio_recovery_quota_1' or not isinstance(parsed.get('reservations'),dict):raise ValueError('Invalid recovery reservation registry')
            rows=parsed['reservations']
            if len(rows)>MAX_RESERVATIONS:raise ValueError('Too many recovery reservations')
            for name,value in rows.items():
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',name) or not isinstance(value,dict) or type(value.get('bytes')) is not int or not 0<value['bytes']<=MAX_BYTES:raise ValueError('Invalid recovery reservation')
                if identity(value.get('owner'))!=value['owner']:raise ValueError('Invalid recovery reservation identity')
        observed=details(list({owner['pid'],*(v['owner']['pid'] for v in rows.values())}))
        if not matches(owner,observed):raise ValueError('Cannot verify recovery reservation owner; previous checkpoint preserved')
        rows={key:value for key,value in rows.items() if not expired(value['owner'],observed)}
        if token in rows and rows[token]['owner']!=owner:raise ValueError('Recovery reservation belongs to another process')
        if action=='reserve':
            if token in rows:raise ValueError('Recovery reservation already exists')
            if not reserve or len(rows)>=MAX_RESERVATIONS:raise ValueError('Recovery reservation capacity reached')
            used=occupied(root)
            # Actual bytes plus full outstanding reservations deliberately overcount
            # writes already in progress. Registry publication has a bounded reserve.
            if used+sum(v['bytes'] for v in rows.values())+reserve+2*MAX_REGISTRY>MAX_BYTES:
                raise ValueError('Recovery cache budget reached (512 MiB), including concurrent checkpoints. Save manually; previous checkpoint preserved.')
            rows[token]={'owner':owner,'bytes':reserve}
        else:rows.pop(token,None)
        blob=json.dumps({'format':'studio_recovery_quota_1','reservations':rows},sort_keys=True).encode()
        if len(blob)>MAX_REGISTRY:raise ValueError('Recovery reservation registry exceeds its bound')
        fd,name=tempfile.mkstemp(prefix='.quota-',suffix='.tmp',dir=root)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(blob);stream.flush();os.fsync(stream.fileno())
            os.replace(name,index)
        finally:
            try:os.unlink(name)
            except FileNotFoundError:pass
        return {'ok':True,'token':token,'reserved_bytes':reserve if action=='reserve' else 0}

def main():
    try:
        if len(sys.argv)!=6:raise ValueError('Expected recovery quota root/action/token/owner/bytes')
        result=operation(sys.argv[1],sys.argv[2],sys.argv[3],json.loads(base64.b64decode(sys.argv[4],validate=True)),int(sys.argv[5]))
    except (OSError,ValueError,KeyError,TypeError) as error:result={'ok':False,'error':str(error)}
    print(json.dumps(result))
if __name__=='__main__':main()

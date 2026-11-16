from pathlib import Path
import ctypes,ctypes.wintypes as W,json,time
R=Path.cwd().resolve();O=R/'output/source-choices-native-independent-cleanup-audit-20261114';k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE;k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
bad=[];checked=0
for phase in ['core14','wider11']:
 d=json.loads((O/(phase+'-fresh-inventory.json')).read_bytes());root=Path(d['absolute_root']);rows=[(root,True)]+[(root/n,True) for n in d['directories']]+[(root/r['path'],False) for r in d['files']]
 for p,isdir in rows:
  assert p==root or p.is_relative_to(root)
  handle=k.CreateFileW('\\\\?\\'+str(p),0x00010000|0x80,7,None,3,0x02000000|0x00200000,None)
  if handle==ctypes.c_void_p(-1).value:bad.append({'path':str(p),'winerror':ctypes.get_last_error(),'directory':isdir})
  else:
   if not k.CloseHandle(handle):bad.append({'path':str(p),'close_winerror':ctypes.get_last_error()})
  checked+=1
proof={'format':'has_readonly_delete_access_handle_probe_1','checked_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'entries':checked,'failures':bad,'passed':not bad,'actual_delete_attempted':False,'handle_flags':'DELETE|FILE_READ_ATTRIBUTES, FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE, OPEN_EXISTING, BACKUP_SEMANTICS|OPEN_REPARSE_POINT. No disposition API called.','limit':'A successful handle open does not prove absence of arbitrary shared readers, does not reserve deletion access for later, and does not clear unknown-process nonuse.'}
p=O/'delete-access-readonly-proof.json';p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'entries':checked,'failures':len(bad),'first_failures':bad[:3],'proof':str(p)}))

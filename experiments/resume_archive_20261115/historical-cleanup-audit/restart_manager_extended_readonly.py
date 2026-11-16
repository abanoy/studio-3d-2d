from pathlib import Path
import ctypes,ctypes.wintypes as W,json,hashlib,time
ROOT=Path.cwd().resolve();OUT=ROOT/'output/source-choices-native-independent-cleanup-audit-20261114'
all_paths=[]
for phase in ['core14','wider11']:
 inv=json.loads((OUT/(phase+'-fresh-inventory.json')).read_bytes());all_paths.extend(str(Path(inv['absolute_root'])/r['path']) for r in inv['files'])
all_paths=["\\\\?\\"+path for path in all_paths]
class RM_UNIQUE_PROCESS(ctypes.Structure):_fields_=[('pid',W.DWORD),('start',W.FILETIME)]
class RM_PROCESS_INFO(ctypes.Structure):_fields_=[('process',RM_UNIQUE_PROCESS),('app',W.WCHAR*256),('service',W.WCHAR*64),('type',ctypes.c_int),('status',W.ULONG),('session',W.DWORD),('restartable',W.BOOL)]
rmproof={'format':'has_readonly_restart_manager_resource_audit_1','files_registered':0,'applications':[],'status':'unavailable','limitations':'Point-in-time Windows Restart Manager resource report; it does not prove no arbitrary shared readers or transient future use.'}
try:
 rm=ctypes.WinDLL('rstrtmgr');session=W.DWORD();key=ctypes.create_unicode_buffer(33)
 rm.RmStartSession.argtypes=[ctypes.POINTER(W.DWORD),W.DWORD,W.LPWSTR];rm.RmRegisterResources.argtypes=[W.DWORD,W.UINT,ctypes.POINTER(W.LPCWSTR),W.UINT,ctypes.c_void_p,W.UINT,ctypes.c_void_p];rm.RmGetList.argtypes=[W.DWORD,ctypes.POINTER(W.UINT),ctypes.POINTER(W.UINT),ctypes.POINTER(RM_PROCESS_INFO),ctypes.POINTER(W.DWORD)]
 result=rm.RmStartSession(ctypes.byref(session),0,key);rmproof['start_result']=result
 if result:raise OSError('RmStartSession='+str(result))
 try:
  for offset in range(0,len(all_paths),500):
   chunk=all_paths[offset:offset+500];values=(W.LPCWSTR*len(chunk))(*chunk);result=rm.RmRegisterResources(session,len(chunk),values,0,None,0,None)
   if result:raise OSError('RmRegisterResources='+str(result))
   rmproof['files_registered']+=len(chunk)
  need=W.UINT();count=W.UINT();reasons=W.DWORD();result=rm.RmGetList(session,ctypes.byref(need),ctypes.byref(count),None,ctypes.byref(reasons))
  if result==234:
   count=W.UINT(need.value);items=(RM_PROCESS_INFO*count.value)();result=rm.RmGetList(session,ctypes.byref(need),ctypes.byref(count),items,ctypes.byref(reasons))
   if result:raise OSError('RmGetList='+str(result))
   rmproof['applications']=[{'pid':p.process.pid,'name':p.app,'service':p.service,'session':p.session,'type':p.type} for p in items[:count.value]]
  elif result:raise OSError('RmGetList='+str(result))
  rmproof.update(status='observed',get_list_result=result,reboot_reason=reasons.value)
 finally:rm.RmEndSession(session)
except Exception as e:rmproof['error']=str(e)

rmproof['checked_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());p=OUT/'restart-manager-extended-host-proof.json';p.write_text(json.dumps(rmproof,indent=2)+'\n',encoding='utf-8');print(json.dumps(rmproof))

"""No-process controls against the installed main transport source only."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'tools')]
import wind_helper_preview as protocol
import wind_preview_owned as owner
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHON_SHA='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
def stamp(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 if len(sys.argv)!=2:raise ValueError('One fresh main-owned result folder required')
 folder=Path(sys.argv[1]).absolute()
 if '..'in folder.parts or not folder.resolve().is_relative_to((ROOT/'output').resolve()):raise ValueError('Main-owned result folder required')
 for part in(folder,*folder.parents):
  if part.exists()and(part.is_symlink()or getattr(part.lstat(),'st_file_attributes',0)&0x400):raise ValueError('Link/reparse result refused')
  if part==ROOT:break
 if not folder.is_dir()or(folder/'result.json').exists():raise ValueError('Caller must create fresh empty-result folder')
 for module,name in[(protocol,'wind_helper_preview.py'),(owner,'wind_preview_owned.py')]:
  if Path(module.__file__).resolve()!=(ROOT/'tools'/name).resolve():raise ValueError('Different main transport module loaded')
 context=json.loads((ROOT/'helper-preview-source-context.json').read_bytes())
 if context.get('source_context')not in('main_source_snapshot','main_working_source_snapshot')or Path(context.get('project_root','')).resolve()!=ROOT.resolve()or Path(context.get('main_root','')).resolve()==ROOT.resolve():raise ValueError('Actual main-source snapshot context required')
 sources=[stamp(ROOT/'tools'/name)for name in['wind_helper_preview.py','wind_preview_owned.py','wind_preview_worker.py','wind_preview_controller.py']]+[stamp(PYTHON)]
 checks=[];failures=[]
 def need(value,label):
  checks.append(label)
  if not value:failures.append(label)
 def refusal(call,label):
  try:call()
  except(ValueError,OSError):need(True,label)
  else:need(False,label)
 work=folder/'profile space';work.mkdir();code=folder/'code space';code.mkdir();(code/'project.godot').write_text('config_version=5\n')
 lease=protocol.DraftLease(work/'session')
 build=lambda root:owner.OwnedPreviewJob(lease,code,PYTHON,approved_python_sha256=PYTHON_SHA,work_root=root)
 for value,label in[(None,'missing explicit work root refuses'),(Path('relative'),'relative work root refuses'),(lease.owned_root,'owned root equal to work root refuses'),(work/'different-family','owned root outside work root refuses')]:refusal(lambda value=value:build(value),label)
 job=build(work);command=job.command(lease.owned_root/'job')
 need(command[0]==str(PYTHON.resolve())and command[1:4]==['-I','-B','-u'],'worker command pins absolute approved executable and isolated mode')
 need(command[command.index('--main-root')+1]==str(code)and command[command.index('--work-root')+1]==str(work),'worker command separates code root from writable profile work root')
 need(job.process is None and job.native is None and not lease.owned_root.exists(),'configuration alone launches nothing and publishes no worker root')
 refusal(lambda:owner.OwnedPreviewJob(lease,code,PYTHON,approved_python_sha256='0'*64,work_root=work),'changed approved runtime digest refuses before launch')
 refusal(lambda:protocol.owned(work/'../outside',work),'lexical traversal cannot escape owned family')
 need(protocol.owned(lease.owned_root/'candidate/scene.glb',work)==lease.owned_root/'candidate/scene.glb','owned nested fixed candidate path remains inside explicit work family')
 preserved=all(stamp(row['path'])==row for row in sources);need(preserved,'all main transport sources and approved runtime preserved exactly')
 result=dict(checks=checks,failures=failures,preservation=preserved,controller_launches=0,model_imports=0,gpu=False,mode="transport",source_context=context["source_context"],main_root=context["main_root"],project_root=str(ROOT),source_manifest_sha256=context["source_manifest_sha256"],main_revision=context["main_revision"])
 with(folder/'result.json').open('x',encoding='utf-8')as f:json.dump(result,f,indent=2);f.write('\n')
 print('HELPER_PREVIEW_TRANSPORT '+json.dumps(dict(checks=len(checks),failures=len(failures))))
 return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())

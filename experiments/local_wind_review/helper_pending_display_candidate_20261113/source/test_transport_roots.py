"""CPU boundary controls. Does not launch controllers, helpers, or model imports."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,types
ROOT=Path(__file__).resolve().parents[4];TASK=ROOT/'output/helper-preview-integration-20261113/display-v2'
TOOLS=TASK/'overlay/tools';sys.path[:0]=[str(TOOLS),str(ROOT/'tools')]
import wind_helper_preview as protocol
import wind_preview_owned as owner
PYTHON=Path(r'C:\Program Files\Python313\python.exe')
PYTHON_SHA='03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
def stamp(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 folder=TASK/'transport-unit'/str(time.time_ns());folder.mkdir(parents=True,exist_ok=False)
 sources=[stamp(p)for p in TOOLS.glob('*.py')]+[stamp(PYTHON)];checks=[];failures=[]
 def need(value,label):
  checks.append(label)
  if not value:failures.append(label)
 def refusal(call,label):
  try:call()
  except (ValueError,OSError):need(True,label)
  else:need(False,label)
 work=folder/'profile space';work.mkdir();code=folder/'code space';code.mkdir();(code/'project.godot').write_text('config_version=5\n')
 lease=protocol.DraftLease(work/'session')
 build=lambda root:owner.OwnedPreviewJob(lease,code,PYTHON,approved_python_sha256=PYTHON_SHA,work_root=root)
 refused=[(None,'missing explicit work root refuses'),(Path('relative'),'relative work root refuses'),(lease.owned_root,'owned root equal to work root refuses'),(work/'different-family','owned root outside work root refuses')]
 for value,label in refused:refusal(lambda value=value:build(value),label)
 job=build(work)
 command=job.command(lease.owned_root/'job')
 need(command[0]==str(PYTHON.resolve())and command[1:4]==['-I','-B','-u'],'worker command pins absolute approved executable and isolated mode')
 need(command[command.index('--main-root')+1]==str(code)and command[command.index('--work-root')+1]==str(work),'worker command separates code root from writable profile work root')
 need(job.process is None and job.native is None and not lease.owned_root.exists(),'configuration alone launches nothing and publishes no worker root')
 refusal(lambda:owner.OwnedPreviewJob(lease,code,PYTHON,approved_python_sha256='0'*64,work_root=work),'changed approved runtime digest refuses before launch')
 refusal(lambda:protocol.owned(work/'../outside',work),'lexical traversal cannot escape owned family')
 need(protocol.owned(lease.owned_root/'candidate/scene.glb',work)==lease.owned_root/'candidate/scene.glb','owned nested fixed candidate path remains inside explicit work family')
 preservation=all(stamp(r['path'])==r for r in sources)
 need(preservation,'all transport sources and approved runtime preserved exactly')
 result=dict(checks=checks,failures=failures,preservation=preservation,controller_launches=0,model_imports=0,gpu=False)
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(folder=str(folder),checks=len(checks),failures=failures)),flush=True)
 return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())

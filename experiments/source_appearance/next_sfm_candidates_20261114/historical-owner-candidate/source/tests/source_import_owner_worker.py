"""Harmless authored single-process fixture; no asset/runtime/converter imports."""
from pathlib import Path
import argparse,json,time

p=argparse.ArgumentParser()
p.add_argument('--status-file',required=True,type=Path)
p.add_argument('--cancel-file',required=True,type=Path)
p.add_argument('--gate-file',required=True,type=Path)
p.add_argument('--folder',required=True,type=Path)
p.add_argument('--mode',choices=('normal','refusal','cancel'),required=True)
args=p.parse_args()
folder=args.folder.resolve()
assert all(path.resolve().parent==folder.parent for path in (args.status_file,args.cancel_file,args.gate_file))
assert not args.status_file.exists() and not folder.exists()
folder.mkdir()
(folder/'parameters.json').write_text(json.dumps({'warnings':[],'mount_warnings':[]}),encoding='utf-8')
started=time.monotonic();code=3;value={'ok':False,'error':'Authored owner fixture timed out'}
while time.monotonic()-started<6:
 if args.mode=='cancel' and args.cancel_file.exists():
  code=2;value={'ok':False,'error':'Authored preparation cancelled'};break
 if args.mode!='cancel' and args.gate_file.exists():
  code=0 if args.mode=='normal' else 1
  value={'ok':True,'glb':str(folder/'status-only.glb')} if code==0 else {'ok':False,'error':'Authored preparation refused'}
  break
 time.sleep(.01)
with args.status_file.open('x',encoding='utf-8') as stream:json.dump(value,stream)
raise SystemExit(code)

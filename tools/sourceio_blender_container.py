#!/usr/bin/env python3
"""Optional Linux cloud adapter: run Blender in the verified local worker image."""
import json,os,sys
from pathlib import Path
args=sys.argv[1:]
request_path=Path(args[args.index('--')+1]).resolve(strict=True)
request=json.loads(request_path.read_text())
output=Path(request['output']).resolve(strict=True)
paths=[Path(args[args.index('--python')+1]).resolve().parent,Path(request['sourceio']).resolve(),*map(Path,request['mounts'])]
roots=[]
for path in sorted(set(p.resolve(strict=True) for p in paths),key=lambda p:len(p.parts)):
 if path==output or path.is_relative_to(output):continue
 if any(path==root or path.is_relative_to(root) for root in roots):continue
 roots.append(path)
command=['docker','--host=unix:///var/run/docker.sock','run','--rm','--network','none','--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','6g','--cpus','2','--tmpfs','/tmp:size=536870912']
for key,value in {'BLENDER_USER_CONFIG':'/tmp/blender-config','BLENDER_USER_EXTENSIONS':'/tmp/blender-extensions','XDG_CONFIG_HOME':'/tmp/xdg-config','XDG_CACHE_HOME':'/tmp/xdg-cache','XDG_DATA_HOME':'/tmp/xdg-data'}.items():command+=['-e',key+'='+value]
for path in roots:command+=['--mount',f'type=bind,src={path},dst={path},readonly']
command+=['--mount',f'type=bind,src={output},dst={output}','sha256:920ce476fe22608deb971d51c152ee67cc4072c0e2781ce5c1c164ece0d0966e','blender','-noaudio',*args]
env=os.environ.copy()
for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
os.execvpe('docker',command,env)

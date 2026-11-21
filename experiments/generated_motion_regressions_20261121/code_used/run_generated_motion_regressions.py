from pathlib import Path
import json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[1]
out=root/'output'/('generated-motion-regressions-'+str(time.time_ns()));out.mkdir()
jobs=[('wind',['tests/verify_wind_review.py','--mode','graphical','--lease-confirmed']),('helper',['tests/verify_helper_preview.py','--mode','graphical','--lease-confirmed','--allow-working-source'])]
print(str(out),flush=True);results=[]
for name,args in jobs:
 env=dict(os.environ);env.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_NATIVE_FIXTURES=str(root.parent/'has-acceptance-session-20261111/output'))
 for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('USERPROFILE','User')]:
  path=out/name/leaf;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
 start=time.monotonic()
 with (out/(name+'-stdout.log')).open('wb') as stdout,(out/(name+'-stderr.log')).open('wb') as stderr:
  with subprocess.Popen([sys.executable,'-B','-u',*args],cwd=root,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW) as child:
   (out/'current.json').write_bytes((json.dumps({'name':name,'pid':child.pid})+'\n').encode());code=child.wait()
 row={'name':name,'pid':child.pid,'exit':code,'child_reaped':True,'seconds':time.monotonic()-start};results.append(row)
 (out/'completion.json').write_bytes((json.dumps({'status':'FAIL' if code else 'PASS' if len(results)==len(jobs) else 'RUNNING','results':results},indent=2)+'\n').encode());print(json.dumps(row),flush=True)
 if code:break
raise SystemExit(code)

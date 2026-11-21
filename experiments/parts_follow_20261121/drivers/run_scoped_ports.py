"""Run the existing two graphical scopes serially with disposable user settings."""
from pathlib import Path
import json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[1]
folder=root/'output'/('following-port-graphical-'+str(time.time_ns()))
folder.mkdir()
results=[]
for name,args in [('wind',['tests/verify_wind_review.py','--mode','graphical','--lease-confirmed']),('helper',['tests/verify_helper_preview.py','--mode','graphical','--lease-confirmed','--allow-working-source'])]:
    env=dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['HYBRID_NATIVE_FIXTURES']=str(root.parent/'has-acceptance-session-20261111/output')
    for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
        target=folder/'User'/name/leaf;target.mkdir(parents=True,exist_ok=True);env[key]=str(target)
    started=time.monotonic()
    with (folder/(name+'-stdout.log')).open('wb') as out,(folder/(name+'-stderr.log')).open('wb') as err:
        with subprocess.Popen([sys.executable,'-B','-u',*args],cwd=root,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW) as process:
            code=process.wait()
            row={'name':name,'pid':process.pid,'exit':code,'child_reaped':True,'seconds':time.monotonic()-started}
    results.append(row)
    (folder/'completion.json').write_bytes((json.dumps({'results':results,'status':'PASS' if code==0 and len(results)==2 else 'RUNNING' if code==0 else 'FAIL'},indent=2)+'\n').encode())
    print(json.dumps(row),flush=True)
    if code:break
print(str(folder),flush=True)
raise SystemExit(code)

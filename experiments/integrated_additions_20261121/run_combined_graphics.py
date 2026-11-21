"""Serial private-desktop verification of the actual integrated source."""
from pathlib import Path
import json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[1]
folder=root/'output'/('combined-graphics-'+str(time.time_ns()));folder.mkdir()
model=root.parent/'has-acceptance-session-20261111/output/compatibility/source-1794448074-759-4936706/scene.glb'
environment=root.parent/'has-acceptance-session-20261111/output/compatibility/source-1794448085-512-15689586/scene.glb'
owner=root.parent/'has-body-addition-20261120/output'
protected=['--project',str(owner/'owner-stuff2-project-1795240462119/stuff2.has'),'--collider-input',str(owner/'private-miku-collider-derivation-20261121/PRIVATE_COLLIDER_INPUT.json'),'--alignment',str(owner/'private-miku-collider-derivation-20261121/PRIVATE_RUNTIME_ALIGNMENT.json')]
native=['--native-model',str(model),'--native-environment',str(environment)]
jobs=[('lights_compatibility',['tests/verify_scene_lighting.py',*native]),('lights_forward',['tests/verify_scene_lighting.py','--forward-plus',*native]),('indirect',['tests/verify_scene_lighting.py','--indirect']),('interaction',['tests/verify_discovery_lighting_interaction.py','--graphical']),('discovery',['tests/verify_asset_discovery_additions.py','--graphical']),('contact',['tests/verify_secondary_body_contact_visual.py',*protected]),('wind',['tests/verify_wind_review.py','--mode','graphical','--lease-confirmed']),('helper',['tests/verify_helper_preview.py','--mode','graphical','--lease-confirmed','--allow-working-source'])]
results=[];print(str(folder),flush=True)
for label,args in jobs:
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['HYBRID_NATIVE_FIXTURES']=str(root.parent/'has-acceptance-session-20261111/output')
    for key,leaf in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('USERPROFILE','User')]:
        profile=folder/'Profiles'/label/leaf;profile.mkdir(parents=True,exist_ok=True);env[key]=str(profile)
    command=[sys.executable,'-B','-u',*args]
    started=time.monotonic()
    with (folder/(label+'-stdout.log')).open('wb') as out,(folder/(label+'-stderr.log')).open('wb') as err:
        with subprocess.Popen(command,cwd=root,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW) as child:
            (folder/'current.json').write_bytes((json.dumps({'label':label,'pid':child.pid,'args':command},indent=2)+'\n').encode())
            code=child.wait();row={'label':label,'pid':child.pid,'exit':code,'child_reaped':True,'seconds':time.monotonic()-started}
    results.append(row)
    status='FAIL' if code else 'PASS' if len(results)==len(jobs) else 'RUNNING'
    (folder/'completion.json').write_bytes((json.dumps({'status':status,'results':results},indent=2)+'\n').encode())
    print(json.dumps(row),flush=True)
    if code:break
raise SystemExit(code)

from pathlib import Path
import importlib.util,json,hashlib,subprocess,sys,time
root=Path.cwd();sys.path.insert(0,str(root));from tools.build_owner_review_snapshot import freeze_source
folder=root/'output'/('wind-canvas-teardown-'+str(time.time_ns()));folder.mkdir();rows=[]
for label in ['old-wind-review','fixed']:
 case=folder/label;case.mkdir();project=case/'Studio';head,hashes=freeze_source(root,project)
 if label=='old-wind-review':
  raw=(root/'output/wind-main-port-1794549185267571200/before-canvas-guard/src/wind_review.gd').read_bytes();(project/'src/wind_review.gd').write_bytes(raw);hashes['src/wind_review.gd']=hashlib.sha256(raw).hexdigest()
 (project/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Wind Canvas '+str(time.time_ns()))+'\n',encoding='utf-8')
 request=case/'request.json';request.write_text(json.dumps({'mode':'lifecycle','folder':str(case).replace('\\','/'),'project_root':str(project).replace('\\','/')}),encoding='utf-8')
 spec=importlib.util.spec_from_file_location('wind_canvas_runner_'+label.replace('-','_'),project/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
 args=runner.command('tests/wind_review_gpu_lifecycle.gd',extra=['--verbose','--log-file',str(case/'engine.log'),'--',str(request),'--dormant-canvas-close-only']);(case/'command.json').write_text(json.dumps(args,indent=2),encoding='utf-8')
 p=subprocess.run(args,cwd=project,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);log=p.stdout+p.stderr;(case/'process.log').write_text(log,encoding='utf-8');receipt=json.loads(Path(args[args.index('--receipt')+1]).read_bytes());result=json.loads((case/'result.json').read_bytes())
 same=all(hashlib.sha256((project/n).read_bytes()).hexdigest()==h for n,h in hashes.items());row={'case':label,'base_commit':head,'working_source_plus_old_wind_only':label=='old-wind-review','exit':p.returncode,'result':result,'receipt':receipt,'source_unchanged':same,'wind_review_sha256':hashes['src/wind_review.gd'],'shared_test_sha256':hashes['tests/wind_review_gpu_lifecycle.gd'],'observed_script_error':"Invalid access to property or key 'pose_lines'" in log,'clean_log':not any(s in log for s in ['ERROR:','SCRIPT ERROR','FAIL ','ObjectDB instances leaked','unclaimed string names'])};rows.append(row);(folder/'verification.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
 assert p.returncode==0 and receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'] and same
 assert result['checks']==5 and result['failures']==0
 assert row['observed_script_error'] if label=='old-wind-review' else row['clean_log']
print(json.dumps({'folder':str(folder),'old_script_error':rows[0]['observed_script_error'],'fixed_clean':rows[1]['clean_log'],'checks_each':5}))

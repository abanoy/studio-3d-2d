"""Freeze an owner-operated review app away from automated test output/profile."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'output/owner-review';target=folder/'Studio'
assert folder.is_dir() and not target.exists()
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
names=sorted(set(n for n in names if n and Path(n).parts[0] not in ['output','.git','.godot','__pycache__'] and '__pycache__' not in Path(n).parts and not n.endswith('.pyc')))
assert 'main.tscn' in names and 'project.godot' in names and 'run.py' in names
hashes={}
for name in names:
    source=ROOT/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
    data=source.read_bytes();destination.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
assert not (target/'output').exists() and not (target/'.godot').exists()
profile='HAS Owner Acceptance '+str(time.time_ns())
(target/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('owner_review_run',target/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result_path=folder/'source-snapshot-startup.json'
args=module.command(extra=['res://tests/current_candidate_startup.tscn','--',str(result_path)])
p=subprocess.run(args,cwd=target,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
log=p.stdout+p.stderr;(folder/'source-snapshot-startup.log').write_text(log,encoding='utf-8')
assert p.returncode==0 and 'CURRENT_REVIEW_STARTUP ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
startup=json.loads(result_path.read_bytes());assert startup['home_visible'] and startup['simple'] and startup['empty'] and profile in startup['profile'],startup
receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes())
assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
assert all(hashlib.sha256((target/n).read_bytes()).hexdigest()==digest for n,digest in hashes.items())
pythonw=Path(sys.executable).with_name('pythonw.exe');assert pythonw.is_file()
runtime=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
for name in ['Flatgrass','Avatar','Street']:
    assert (folder/(name+'.has')).is_file()
    text=f'@echo off\r\nsetlocal\r\nset "HYBRID_SOURCEIO={runtime}"\r\nstart "" "{pythonw}" "%~dp0Studio\\launch.pyw" "%~dp0{name}.has"\r\n'
    (folder/('Open '+name+'.bat')).write_bytes(text.encode('utf-8'))
(folder/'Start review.bat').write_bytes(f'@echo off\r\nsetlocal\r\nset "HYBRID_SOURCEIO={runtime}"\r\nstart "" "{pythonw}" "%~dp0Studio\\launch.pyw"\r\n'.encode('utf-8'))
result={'format':'has_owner_review_source_snapshot_1','target':str(target),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_source_hashes':hashes,'profile':profile,'normal_startup':startup,'private_receipt':receipt,'no_development_cache_copied':True,'automated_tests_separate_from_owner_output_and_preferences':True,'installation_replaced':False,'retention':'Keep this review source/project folder while actual owner observations are pending. Private review artwork is not uploaded.'}
(folder/'source-snapshot-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='working_source_hashes'},indent=2))

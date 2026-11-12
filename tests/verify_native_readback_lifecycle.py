"""Exact committed native-readback teardown, on a private real-GPU desktop."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.build_owner_review_snapshot import freeze_source

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--revision',help='Exact committed counterfactual; default freezes current working source');parser.add_argument('--overlay-runtime',type=Path,help='Explicit candidate root: overlay only src/app.gd and src/renderer.gd on the committed baseline');parser.add_argument('--case',action='append',choices=['focus-free','focus-queue_free','focus-remove_from_tree','setup-free','setup-queue_free','setup-remove_from_tree','renderer-free','renderer-queue_free','capture-free','capture-queue_free','capture-remove_from_tree','capture-close-app-focus','capture-close-app-setup']);options=parser.parse_args()
    revision=subprocess.check_output(['git','rev-parse',options.revision+'^{commit}'],cwd=ROOT,text=True).strip() if options.revision else None
    folder=ROOT/'output/native-readback-lifecycle'/str(time.time_ns());project=folder/'shipped-source';folder.mkdir(parents=True)
    commit,frozen=freeze_source(ROOT,project,revision)
    if revision:assert commit==revision
    baseline_hashes=frozen.copy()
    if options.overlay_runtime:
        for name in ['src/app.gd','src/renderer.gd']:
            data=(options.overlay_runtime/name).read_bytes();(project/name).write_bytes(data);frozen[name]=hashlib.sha256(data).hexdigest()
    profile='HAS Readback Safety '+str(time.time_ns())
    (project/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
    test=ROOT/'tests/native_readback_lifecycle_smoke.gd';target=project/'tests'/test.name;target.parent.mkdir(exist_ok=True);target.write_bytes(test.read_bytes())
    frozen[str(target.relative_to(project))]=hashlib.sha256(target.read_bytes()).hexdigest()
    spec=importlib.util.spec_from_file_location('readback_shipped_runner',project/'run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    mode='git_revision' if revision else 'working_tree'
    proof={'revision':commit,'source_mode':mode+'_plus_explicit_runtime_overlay' if options.overlay_runtime else mode,'folder':str(folder),'source_sha256':frozen,'baseline_source_sha256':baseline_hashes,'runtime_overlay':str(options.overlay_runtime.resolve()) if options.overlay_runtime else None,'shared_test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'profile':profile}
    (folder/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    startup_path=folder/'normal-startup.json';startup_args=runner.command(extra=['res://tests/current_candidate_startup.tscn','--',str(startup_path)])
    (folder/'normal-startup-command.json').write_text(json.dumps(startup_args,indent=2)+'\n',encoding='utf-8')
    started=subprocess.run(startup_args,cwd=project,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    startup_log=started.stdout+started.stderr;(folder/'normal-startup.log').write_text(startup_log,encoding='utf-8')
    startup=json.loads(startup_path.read_bytes());startup_receipt_path=Path(startup_args[startup_args.index('--receipt')+1]);startup_receipt=json.loads(startup_receipt_path.read_bytes())
    proof.update(normal_startup=startup,startup_receipt=startup_receipt,startup_receipt_path=str(startup_receipt_path))
    (folder/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    assert started.returncode==0 and 'CURRENT_REVIEW_STARTUP ' in startup_log and not any(s in startup_log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),startup_log
    assert startup['home_visible'] and startup['simple'] and startup['empty'] and profile in startup['profile'],startup
    assert startup_receipt['exit']==0 and startup_receipt['child_desktop_confirmed'] and not startup_receipt['foreground_child_observed'] and startup_receipt['job_closed'] and startup_receipt['desktop_closed'],startup_receipt
    assert all(hashlib.sha256((project/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    args=runner.command('tests/'+test.name,extra=['--verbose','--log-file',str(folder/'engine.log'),'--',str(folder),*(options.case or [])])
    (folder/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
    process=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=110)
    log=process.stdout+process.stderr;(folder/'console.log').write_text(log,encoding='utf-8')
    receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes());proof.update(exit=process.returncode,receipt=receipt,receipt_path=str(receipt_path))
    if (folder/'result.json').exists():proof['result']=json.loads((folder/'result.json').read_bytes())
    proof['unchanged_source']=all(hashlib.sha256((project/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    assert process.returncode==0 and 'NATIVE_READBACK_LIFECYCLE ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','unclaimed string names at exit','_set_transient_exclusive_child']),log
    assert proof['result']['failures']==0 and len(proof['result']['cases'])==(len(options.case) if options.case else 13) and proof['unchanged_source'],proof
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
    (ROOT/'output/native-readback-lifecycle-latest.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

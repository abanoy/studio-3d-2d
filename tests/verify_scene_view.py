"""Full-area editor view, native ray mapping and unchanged output capture."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command

def main():
    folder=ROOT/'output/scene-view'/str(time.time_ns());folder.mkdir(parents=True)
    sources=[*sorted((ROOT/'src').rglob('*.gd')),*sorted((ROOT/'src').rglob('*.gdshader')),Path(__file__),ROOT/'tests/scene_view_unit.gd',ROOT/'tests/scene_view_smoke.gd']
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (folder/'source-sha256.json').write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    reports={}
    for name,headless in [('scene_view_unit',True),('scene_view_smoke',False)]:
        args=command('tests/'+name+'.gd',headless=headless,extra=['--log-file',str(folder/(name+'-engine.log')),'--',str(folder)])
        (folder/(name+'-command.json')).write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
        result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=140)
        log=result.stdout+result.stderr;(folder/(name+'.log')).write_text(log,encoding='utf-8')
        assert result.returncode==0 and ('SCENE_VIEW_UNIT ' if headless else 'SCENE_VIEW ') in log and not any(x in log for x in ['SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','_set_transient_exclusive_child']),log
        report=json.loads((folder/('unit.json' if headless else 'result.json')).read_bytes())
        assert report['failures']==0,report
        if not headless and os.name=='nt':
            receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes())
            assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
            report['private_receipt']=receipt;report['private_receipt_path']=str(receipt_path)
        reports[name]=report
    changed=[name for name,digest in frozen.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    assert not changed,changed
    reports['source_sha256']=frozen;reports['folder']=str(folder)
    (ROOT/'output/scene-view-verification.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(reports,indent=2))
if __name__=='__main__':main()

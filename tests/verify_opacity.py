from pathlib import Path
import json,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command
def run(args,timeout,path):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    log=p.stdout+p.stderr
    path.write_text(log,encoding='utf-8')
    assert p.returncode==0 and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
    return log
def main():
    folder=ROOT/'output/opacity'/str(time.time_ns());folder.mkdir(parents=True)
    unit=run(command('tests/opacity_unit.gd',headless=True),50,folder/'unit.log');domain=json.loads(unit.split('OPACITY_UNIT ')[-1].splitlines()[0]);assert domain['failures']==0
    args=command('tests/opacity_smoke.gd',extra=['--',str(folder),'--demo-room']);log=run(args,160,folder/'app.log');result=json.loads(log.split('OPACITY_SMOKE ')[-1].splitlines()[0]);assert result['failures']==0
    receipt=Path(args[args.index('--receipt')+1]);r=json.loads(receipt.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];result['private_receipt']=str(receipt)
    with zipfile.ZipFile(result['project']) as z:
        data=json.loads(z.read('project.json'));assert data['layers'][1]['opacity']==.25
        assert not any(k.startswith('studio_') for layer in data['layers'] for cel in layer['cels'] for k in cel)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    result['domain']=domain;(ROOT/'output/opacity-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()

from pathlib import Path
import argparse,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Linux requires an explicitly owned private display')
        configure_private_display(options.isolated_display)
    folder=(options.output or ROOT/'output/onion'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    args=command('tests/onion_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder),'--demo-room']);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    log=p.stdout+p.stderr;(folder/'app.log').write_text(log,encoding='utf-8');assert p.returncode==0 and 'ONION_SMOKE ' in log and '"failures":0' in log and not any(x in log for x in ('ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child')),log
    result=json.loads(log.split('ONION_SMOKE ')[-1].splitlines()[0])
    if os.name=='nt':
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_text());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];result['private_receipt']=str(path)
    def check_keys(value):
        if isinstance(value,dict):
            assert not any(k.startswith('onion') or k=='studio_pixels_revision' for k in value)
            for v in value.values():check_keys(v)
        elif isinstance(value,list):
            for v in value:check_keys(v)
    with zipfile.ZipFile(result['project']) as z:check_keys(json.loads(z.read('project.json')))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(v['duration'])-2)<.001
    summary=json.dumps(result,indent=2)
    (folder/'verification.json').write_text(summary,encoding='utf-8')
    (ROOT/'output/onion-verification.json').write_text(summary,encoding='utf-8');print(summary)
if __name__=='__main__':main()

import argparse,hashlib,os,time
"""Bounded near-camera placement, grounding, overlap fallback and native map checks."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command as private_command,configure_private_display

EVIDENCE=None
RECEIPTS=[]
def command(script=None,headless=False,extra=()):
    return private_command(script,headless,extra=(["--audio-driver","Dummy"] if os.name!='nt' else [])+list(extra))
def desktop_receipt(args):
    if os.name=='nt' and '--receipt' in args:
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes())
        assert r['exit']==0 and r['private_window_seen'] and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and not r['desktop_switch_requested'] and r['job_closed'] and r['desktop_closed'];RECEIPTS.append(str(path))



def main():
    global EVIDENCE
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    EVIDENCE=(options.output or ROOT/'output/private-world-tests'/str(time.time_ns())).resolve();EVIDENCE.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))

    bad=('ERROR:','SCRIPT ERROR','SHADER ERROR','FAIL ','ObjectDB instances leaked','another exclusive child')
    bounds_args=command('tests/import_placement_smoke.gd',headless=True,extra=['--log-file',str(EVIDENCE/'bounds-engine.log'),'--','--bounds-only'])
    bounds_process=subprocess.run(bounds_args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=35)
    bounds_text=bounds_process.stdout+bounds_process.stderr
    (EVIDENCE/'bounds-console.log').write_text(bounds_text,encoding='utf-8')
    bounds_engine=(EVIDENCE/'bounds-engine.log').read_text(encoding='utf-8',errors='replace')
    assert bounds_process.returncode==0 and not any(s in bounds_text+bounds_engine for s in bad),bounds_text+bounds_engine
    bounds=json.loads(next(line[len('IMPORT_PLACEMENT_BOUNDS '):] for line in bounds_text.splitlines() if line.startswith('IMPORT_PLACEMENT_BOUNDS ')))
    assert bounds['checks']==20 and bounds['failures']==0 and bounds['thin_planar_actual_plan']
    args=command('tests/import_placement_smoke.gd',extra=['--log-file',str(EVIDENCE/'engine.log')])
    (EVIDENCE/'private-command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=110)
    text=p.stdout+p.stderr
    (ROOT/'output/import-placement-verification.log').write_text(text,encoding='utf-8')
    (EVIDENCE/'console.log').write_text(text,encoding='utf-8')
    engine=(EVIDENCE/'engine.log').read_text(encoding='utf-8',errors='replace') if (EVIDENCE/'engine.log').exists() else ''
    receipt={}
    if os.name=='nt' and '--receipt' in args:
        path=Path(args[args.index('--receipt')+1])
        if path.is_file():
            receipt=json.loads(path.read_bytes());(EVIDENCE/'private-desktop.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    if p.returncode or not (EVIDENCE/'engine.log').exists() or '"failures":0' not in text or any(s in text+engine for s in bad):raise RuntimeError(text+engine+'\n'+json.dumps(receipt))
    desktop_receipt(args)
    report=json.loads((ROOT/'output/import-placement-result.json').read_text(encoding='utf-8'))
    p=subprocess.run([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']],capture_output=True,text=True,check=True)
    probe=json.loads(p.stdout);video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<.001
    report['video']={'codec':'h264','size':[1920,1080],'fps':'24/1','frames':48,'duration':'2.000000'}
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    report.update(source_sha256=frozen,headless_bounds=bounds,isolated_display=options.isolated_display,private_receipts=RECEIPTS,scope='Original authored world and rig fixtures plus actual thin/planar placement bounds; native coverage only for explicitly available prepared samples, never inferred from generated fixtures.')
    (EVIDENCE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'output/import-placement-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()

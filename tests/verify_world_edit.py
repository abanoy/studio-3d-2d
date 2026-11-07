import argparse,hashlib,os,time
"""Exercise multi-object editor controls, stable-ID Undo, all-object saves and native rigs."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run import command as private_command,configure_private_display

EVIDENCE=None
RECEIPTS=[]
def command(script=None,headless=False,extra=()):
    return private_command(script,headless,extra=(["--audio-driver","Dummy"] if os.name!='nt' else [])+list(extra))
def desktop_receipt(args):
    if os.name=='nt' and '--receipt' in args:
        path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];RECEIPTS.append(str(path))

import has_project as has


def run(args,timeout=140):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    if p.returncode or any(error in text for error in ('ERROR:','SCRIPT ERROR','SHADER ERROR','Shader compilation failed','FAIL ','ObjectDB instances leaked')):
        raise RuntimeError(text)
    desktop_receipt(args)
    if EVIDENCE and '--script' in args:(EVIDENCE/(Path(args[args.index('--script')+1]).stem+'-'+str(time.time_ns())+'.log')).write_text(text,encoding='utf-8')
    return text


def main():
    global EVIDENCE
    parser=argparse.ArgumentParser();parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no shared fallback')
        configure_private_display(options.isolated_display)
    EVIDENCE=(options.output or ROOT/'output/private-world-tests'/str(time.time_ns())).resolve();EVIDENCE.mkdir(parents=True,exist_ok=False)
    frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for part in ['src','tests','tools','examples','data'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');ffprobe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))

    sys.stdout.reconfigure(encoding='utf-8')
    run(command('tests/world_runtime_smoke.gd'))  # Authored assets/snapshot prerequisite.
    text=run(command('tests/world_edit_smoke.gd'))
    (ROOT/'output/world-edit-verification.log').write_text(text,encoding='utf-8')
    if 'WORLD_EDIT_SMOKE ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/world-edit-result.json').read_text(encoding='utf-8'))
    folder=Path(report['folder']);packages={}
    for name,project,reference in [('authored',report['project'],Path(report['movie']).parent/'frame_000025.png'),
                                    ('linked',report['linked_project'],Path(report['movie']).parent/'frame_000025.png'),
                                    ('native',report['native_project'],folder/'native-reference.png')]:
        if not project:continue
        opened=folder/(name+'-open');unpacked=has.unpack({'path':project,'folder':str(opened)})
        if name=='linked':assert len(unpacked['origins'])==3
        text=run(command('tests/world_runtime_read.gd',False,['--',str(opened),str(reference)]))
        marker=next(line for line in text.splitlines() if line.startswith('WORLD_RUNTIME_READ '))
        packages[name]=json.loads(marker.removeprefix('WORLD_RUNTIME_READ '))
    probe=json.loads(run([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<0.01
    assert report['palette_picks']==64
    report['packed_reopen']=packages
    report['video']={'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':probe['format']['duration']}
    assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha for path,sha in frozen.items())
    report.update(source_sha256=frozen,isolated_display=options.isolated_display,private_receipts=RECEIPTS,scope='Original authored world and rig fixtures; native coverage only for explicitly available prepared samples, never inferred from generated fixtures.')
    (EVIDENCE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'output/world-edit-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))


if __name__=='__main__':main()

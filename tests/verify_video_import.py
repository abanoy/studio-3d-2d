"""Procedural video integration. Windows private desktop or explicit isolated X display."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command
from test_video_import import FFMPEG, fixture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display',help='Linux only: an already provisioned private dummy X display')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if os.name!='nt' and not args.isolated_display:
        parser.error('Provide --isolated-display for a private dummy display; no shared-desktop fallback')
    if not FFMPEG:parser.error('Install FFmpeg/FFprobe and configure HYBRID_FFMPEG')
    folder=(args.output or ROOT/'output/video-verification'/str(time.time_ns())).resolve()
    folder.mkdir(parents=True,exist_ok=False)
    source=fixture(folder/'source.mov');reports={};receipts=[]
    env=dict(os.environ)
    env['HYBRID_FFMPEG']=FFMPEG
    if os.name!='nt':env['DISPLAY']=args.isolated_display
    for label,extra in [('writer',[]),('reader',['--read'])]:
        argv=command('tests/video_import_smoke.gd',extra=['--audio-driver','Dummy','--',str(folder),*extra])
        p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=150,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        raw=p.stdout+p.stderr;(folder/(label+'.log')).write_bytes(raw)
        if p.returncode or any(s in raw for s in [b'SCRIPT ERROR',b'SHADER ERROR',b'FAIL ',b'ObjectDB instances leaked']):
            raise RuntimeError(raw.decode(errors='replace'))
        if os.name=='nt':
            receipt=Path(argv[argv.index('--receipt')+1]);r=json.loads(receipt.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed']
            receipts.append(str(receipt))
        marker='VIDEO_IMPORT_'+('SMOKE ' if label=='writer' else 'READ ')
        line=next(s for s in raw.decode(errors='replace').splitlines() if s.startswith(marker))
        reports[label]=json.loads(line[len(marker):]);assert reports[label]['failures']==0
        # Reopening must not need the original video, even for a linked HAS.
        if label=='writer':source.rename(folder/'source-preserved.mov')
    probe=Path(FFMPEG).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe')
    metadata=json.loads(subprocess.check_output([str(probe),'-v','error','-count_frames','-show_streams','-show_format','-of','json',reports['writer']['movie']],
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0))
    v=next(s for s in metadata['streams'] if s['codec_type']=='video')
    assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(metadata['format']['duration'])-2)<.001
    for name in ['Video scene.has','Video scene linked.has']:
        with zipfile.ZipFile(folder/name) as z:
            manifest=json.loads(z.read('project.json'));layer=manifest['layers'][2]
            assert layer['origin']['format']=='studio_drawing_origin_2' and 'path' not in layer['origin']
            assert len(layer['cels'])==2 and all(c['path'] in z.namelist() for c in layer['cels'])
    result=dict(reports=reports,private_receipts=receipts,display=args.isolated_display,media=metadata)
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(folder=str(folder),reports=reports),indent=2))


if __name__=='__main__':main()

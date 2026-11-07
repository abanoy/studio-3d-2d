"""Cold whole-layer history retention and existing layer UI/save/recovery/media regression."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not args.isolated_display:parser.error('Linux requires an explicitly owned private display')
        configure_private_display(args.isolated_display)
    folder=(args.output or ROOT/'output/layer-retention'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    reports={};receipts=[]
    for label,script,marker in [('retention','layer_retention_smoke','LAYER_RETENTION_SMOKE '),('ordinary','layers_smoke','LAYERS_SMOKE ')]:
        case=folder/label;case.mkdir()
        argv=command('tests/'+script+'.gd',extra=['--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(case),*(['--demo-room'] if label=='ordinary' else [])])
        result=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        log=result.stdout+result.stderr;(case/'console.log').write_text(log,encoding='utf-8')
        assert result.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked','another exclusive child']),log
        report=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert report['failures']==0
        reports[label]=report
        if os.name=='nt':
            receipt=Path(argv[argv.index('--receipt')+1]);proof=json.loads(receipt.read_text())
            assert proof['exit']==0 and proof['child_desktop_confirmed'] and not proof['foreground_child_observed'] and proof['job_closed'] and proof['desktop_closed'];receipts.append(str(receipt))
    ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',reports['ordinary']['movie']]))
    video=next(s for s in media['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48') and abs(float(video['duration'])-2)<.001
    proof=dict(reports=reports,video=video,private_receipts=receipts,isolated_display=args.isolated_display,scope='Owned cold-layer history and ordinary layer workflow; no global RSS/admission/native-platform certification.',source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/layer_editor.gd','tests/layer_retention_smoke.gd','tests/layers_smoke.gd','tests/verify_layer_retention.py']})
    (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))

if __name__=='__main__':main()

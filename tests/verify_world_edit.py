"""Exercise multi-object editor controls, stable-ID Undo, all-object saves and native rigs."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run import command
import has_project as has


def run(args,timeout=140):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    if p.returncode or any(error in text for error in ('SCRIPT ERROR','SHADER ERROR','Shader compilation failed','FAIL ','ObjectDB instances leaked')):
        raise RuntimeError(text)
    return text


def main():
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
    probe=json.loads(run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<0.01
    assert report['palette_picks']==64
    report['packed_reopen']=packages
    report['video']={'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':probe['format']['duration']}
    (ROOT/'output/world-edit-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

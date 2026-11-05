"""Render multiple native instances, export MP4, and reopen packed HAS in another process."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run import command
import has_project as has


def run(args,timeout=120):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    text=p.stdout+p.stderr
    if p.returncode or any(error in text for error in ('SCRIPT ERROR','SHADER ERROR','Shader compilation failed','FAIL ','ObjectDB instances leaked')):
        raise RuntimeError(text)
    return text


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    text=run(command('tests/world_runtime_smoke.gd'))
    (ROOT/'output/world-runtime-verification.log').write_text(text,encoding='utf-8')
    if 'WORLD_RUNTIME_SMOKE ' not in text or '"failures":0' not in text:raise RuntimeError(text)
    report=json.loads((ROOT/'output/world-runtime-result.json').read_text(encoding='utf-8'))
    folder=Path(report['folder']);inputs=folder/'inputs';moved=folder/'moved-inputs'
    output=(ROOT/'output').resolve()
    assert inputs.resolve().is_relative_to(output) and moved.resolve().is_relative_to(output) and inputs.parent==moved.parent
    package=folder/'combined-world.has';opened=folder/'packed-open'
    has.pack({'folder':report['snapshot'],'path':str(package),'storage':'packed','references':{},'cache_root':str(folder/'cache')})
    inputs.rename(moved)
    try:
        has.unpack({'path':str(package),'folder':str(opened)})
        text=run(command('tests/world_runtime_read.gd',False,['--',str(opened),str(folder/'package-reference.png')]))
        marker=next(line for line in text.splitlines() if line.startswith('WORLD_RUNTIME_READ '))
        report['packed_reopen']=json.loads(marker.removeprefix('WORLD_RUNTIME_READ '))
    finally:
        moved.rename(inputs)
    probe=json.loads(run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-show_format','-of','json',report['movie']]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    assert abs(float(probe['format']['duration'])-2)<0.01
    for path,digest in report['originals'].items():assert has.sha(Path(path))==digest
    report['video']={'codec':'h264','width':1920,'height':1080,'fps':'24/1','frames':48,'duration':probe['format']['duration']}
    report['original_inputs_unchanged']=True
    (ROOT/'output/world-runtime-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='originals'},indent=2))


if __name__=='__main__':main()

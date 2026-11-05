"""Actual offline Blender/VTF/PNG orientation boundary, no visible GUI or assets."""
from pathlib import Path
import json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=ROOT/'output/source-texture'/str(time.time_ns());folder.mkdir(parents=True)
    args=[r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe','--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(ROOT/'tests/source_texture_probe.py'),'--',str(folder)]
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',NO_BPY='1',BLENDER_USER_CONFIG=str(folder/'blender-config'))
    process=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    (folder/'probe.log').write_text(process.stdout+process.stderr,encoding='utf-8');assert process.returncode==0,process.stdout+process.stderr
    result=json.loads((folder/'result.json').read_text(encoding='utf-8'));assert len(result['cases'])==3 and result['invalid_channels_refused']and all(r['max_pixel_delta']<1e-6 for r in result['cases'])
    result['folder']=str(folder);(ROOT/'output/source-texture-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

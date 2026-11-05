from pathlib import Path
import hashlib
import base64
import json
import os
import subprocess
import sys
import struct
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run import command


def run(args,env=None,timeout=240):
    p=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p.stdout+p.stderr


def main():
    print(run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_generic_assets.py']))
    fixtures=ROOT/'output/generic-fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update(BLENDER_USER_CONFIG=str(ROOT/'output/generic-fixture-config'),PYTHONDONTWRITEBYTECODE='1')
    text=run([os.environ.get('HYBRID_BLENDER',r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'),'--background','--factory-startup','--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(ROOT/'tests/make_generic_fixtures.py'),'--',str(fixtures)],env)
    if 'GENERIC_FIXTURES_READY' not in text:raise RuntimeError(text)
    doc=json.loads((fixtures/'rig.gltf').read_text())
    for item in doc.get('buffers',[])+doc.get('images',[]):
        if 'uri' not in item:continue
        path=fixtures/unquote(item['uri'])
        mime='image/png' if path.suffix.lower()=='.png' else 'application/octet-stream'
        item['uri']='data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()
    embedded=fixtures/'embedded-gltf';embedded.mkdir(exist_ok=True);(embedded/'rig.gltf').write_text(json.dumps(doc))
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures.rglob('*') if p.is_file()}
    text=run(command('tests/generic_smoke.gd'))
    (ROOT/'output/generic-verification.log').write_text(text,encoding='utf-8')
    if 'GENERIC_SMOKE ' not in text or '"failures":0' not in text or any(x in text for x in ('SCRIPT ERROR','FAIL ','ObjectDB instances leaked','another exclusive child')):raise RuntimeError(text)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in before.items())
    assert set(before)=={p for p in fixtures.rglob('*') if p.is_file()}
    r=json.loads((ROOT/'output/generic-result.json').read_text())
    for folder in r['bundles'].values():
        with (Path(folder)/'scene.glb').open('rb') as stream:
            head=stream.read(20);size=struct.unpack_from('<I',head,12)[0];doc=json.loads(stream.read(size))
        assert len(doc.get('meshes',[]))==1,'Editor helper leaked into exported geometry'
    video=json.loads(run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',r['movie']]))['streams'][0]
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','48')
    r['video']=video;r['original_inputs_unchanged']=True
    (ROOT/'output/generic-verification.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({k:v for k,v in r.items() if k!='video'},indent=2))


if __name__=='__main__':main()

"""Exact decoded brush boundary through Blender, Studio, packed/recovery and media."""
from pathlib import Path
import argparse,hashlib,json,os,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display');o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False);frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_source_lightmaps.py'],cwd=ROOT,capture_output=True,text=True,timeout=30);(folder/'python.log').write_text(r.stdout+r.stderr);n=re.search(r'Ran ([1-9][0-9]*) tests',r.stderr);assert r.returncode==0 and n,r.stdout+r.stderr
 r=subprocess.run([os.environ.get('HYBRID_BLENDER','blender'),'--background','--factory-startup','--python','tests/source_lightmaps_blender.py','--',str(folder)],cwd=ROOT,capture_output=True,text=True,timeout=90);(folder/'blender.log').write_text(r.stdout+r.stderr);assert r.returncode==0 and 'SOURCE_LIGHTMAPS_BLENDER_READY' in r.stdout,r.stdout+r.stderr
 blob=(folder/'scene.glb').read_bytes();length,kind=struct.unpack_from('<II',blob,12);assert kind==0x4e4f534a;gltf=json.loads(blob[20:20+length]);baked=[m for m in gltf['materials'] if 'emissiveTexture' in m];assert len(baked)==1 and baked[0]['emissiveTexture']['texCoord']==1 and baked[0]['extensions']['KHR_materials_emissive_strength']['emissiveStrength']>1,gltf
 original={name:digest(folder/name) for name in ['scene.glb','original-lighting.bin','parameters.json','original-lightmap.blend']}
 args=command('tests/source_lightmaps_smoke.gd',extra=(['--audio-driver','Dummy'] if os.name!='nt' else [])+['--log-file',str(folder/'engine.log'),'--',str(folder)]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=150);log=r.stdout+r.stderr;(folder/'app.log').write_text(log);assert r.returncode==0 and 'SOURCE_LIGHTMAPS ' in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log;report=json.loads(next(s[len('SOURCE_LIGHTMAPS '):] for s in log.splitlines() if s.startswith('SOURCE_LIGHTMAPS ')));assert report['failures']==0
 probe=str(Path(os.environ.get('HYBRID_FFMPEG','ffmpeg')).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'));media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',report['movie']]));video=next(v for v in media['streams'] if v['codec_type']=='video');assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1')
 assert all(digest(folder/name)==sha for name,sha in original.items());assert all(digest(ROOT/name)==sha for name,sha in frozen.items())
 result=dict(python={'checks':int(n.group(1)),'failures':0},app=report,lightmaps=json.loads((folder/'lightmaps.json').read_bytes()),video=video,source_sha256=frozen,original_sha256=original,isolated_display=o.isolated_display,scope='Original decoded brush records exercise exact capture/bake API, real Blender GLB UV1/emission strength, actual Studio, source-offline packed Open, recovery and exact48frame1080p24H264 input. Full SourceIO/BSP/GMod installed-game path unrun; no native ecosystem certification.')
 if os.name=='nt':
  receipt=Path(args[args.index('--receipt')+1]);proof=json.loads(receipt.read_bytes());assert proof['exit']==0 and proof['child_desktop_confirmed'] and not proof['foreground_child_observed'] and proof['job_closed'] and proof['desktop_closed'];result['private_receipt']=str(receipt)
 (folder/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

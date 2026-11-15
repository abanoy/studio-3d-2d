"""Original Source-entity light records through actual Blender GLB, Studio and movie."""
from pathlib import Path
import argparse,hashlib,json,math,os,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotate(q,v):
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 a=cross(q[:3],v);b=cross(q[:3],a);return [v[i]+2*(q[3]*a[i]+b[i]) for i in range(3)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display');o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 unit=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_source_lights.py'],cwd=ROOT,capture_output=True,text=True);(folder/'unit.log').write_text(unit.stdout+unit.stderr);assert unit.returncode==0
 blender=subprocess.run([os.environ.get('HYBRID_BLENDER','blender'),'--background','--factory-startup','--python',str(ROOT/'tests/source_lights_blender.py'),'--',str(folder)],cwd=ROOT,capture_output=True,text=True,timeout=90);(folder/'blender.log').write_text(blender.stdout+blender.stderr);assert blender.returncode==0 and 'SOURCE_LIGHTS_BLENDER_READY' in blender.stdout,blender.stdout+blender.stderr
 raw=(folder/'scene.glb').read_bytes();size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a;doc=json.loads(raw[20:20+size]);light_data=doc['extensions']['KHR_lights_punctual']['lights'];planned=json.loads((folder/'lights.json').read_text())['lights'];by_name={'HAS '+row['name']:row for row in planned};assert len(light_data)==3 and {q['type'] for q in light_data}=={'point','spot','directional'}
 for node in doc['nodes']:
  extension=node.get('extensions',{}).get('KHR_lights_punctual')
  if extension is None:continue
  row=by_name[node['name']];light=light_data[extension['light']];assert light['intensity']>0 and math.isfinite(light['intensity'])
  expected=[row['position'][0],row['position'][2],-row['position'][1]];assert max(abs(a-b) for a,b in zip(node.get('translation',[0,0,0]),expected))<1e-6
  assert max(abs(a-b) for a,b in zip(light.get('color',[1,1,1]),row['color']))<1e-6
  if row['type']!='POINT':
   expected=[row['direction'][0],row['direction'][2],-row['direction'][1]];actual=rotate(node.get('rotation',[0,0,0,1]),[0,0,-1]);assert sum(a*b for a,b in zip(actual,expected))>.99999,(actual,expected)
  if row['type']=='SPOT':assert abs(light['spot']['outerConeAngle']-row['spot_size']/2)<1e-6
 before={str(folder/n):digest(folder/n) for n in ['scene.glb','entities.json','lights.json']}
 args=command('tests/source_lights_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder)]);app=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=165);log=app.stdout+app.stderr;(folder/'console.log').write_text(log);marker='SOURCE_LIGHTS ';assert app.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
 result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['checks']==9 and result['failures']==0
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe');v=json.loads(subprocess.check_output([str(probe),'-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True))['streams'][0];assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')
 assert all(digest(Path(q))==sha for q,sha in before.items()) and all(digest(ROOT/q)==sha for q,sha in frozen.items())
 receipts=[]
 if os.name=='nt':
  path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
 proof=dict(unit_checks=9,app=result,exported_lights=light_data,video=v,input_sha256=before,source_sha256=frozen,isolated_display=o.isolated_display,private_receipts=receipts,scope='Exact entity planner/emitter and actual Blender/Studio/media with original fixtures. Full native BSP/SourceIO/GMod fixture remains externally unrun; baked lightmaps and engine photometry unsupported.')
 (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

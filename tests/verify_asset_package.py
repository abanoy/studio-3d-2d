"""Independent existing-HAS model/map sharing, real UI, Undo, cold import and media."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--isolated-display');o=p.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
 for pattern in ['test_asset_package.py','test_has_project.py','test_has_save_faults.py']:
  r=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern],cwd=ROOT,capture_output=True,text=True,timeout=90);(folder/(pattern+'.log')).write_text(r.stdout+r.stderr);n=re.search(r'Ran ([1-9][0-9]*) tests',r.stderr);assert r.returncode==0 and n,r.stdout+r.stderr;reports[pattern]={'checks':int(n.group(1)),'failures':0}
 def execute(label,extra,marker):
  args=command('tests/asset_package_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=195);log=r.stdout+r.stderr;(folder/(label+'.log')).write_text(log);assert r.returncode==0 and marker in log and not any(s in log for s in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['checks']>0 and reports[label]['failures']==0
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
  print(label+': PASS',flush=True)
 execute('writer',[],'ASSET_PACKAGE ');manual={n:digest(folder/n) for n in ['Figure.has','Map.has','Main.has','Combined.has']};inventory={}
 for name in ['Figure.has','Map.has']:
  with zipfile.ZipFile(folder/name) as archive:
   header=json.loads(archive.read('has.json'));manifest=json.loads(archive.read('project.json'));assert len(manifest['world']['objects'])==1 and manifest['layers']==[] and manifest['audio']=={} and len(header['assets'])==1 and len(archive.namelist())==3
   inventory[name]=header['asset_package']
 moved=[]
 try:
  for name in ['original.glb','original.glb.original.glb','room.glb','cache','parameters.json']:
   path=folder/name
   if not path.exists():continue
   offline=path.with_name(path.name+'.offline');assert not offline.exists();path.rename(offline);moved.append((path,offline))
  execute('reader',['--read'],'ASSET_PACKAGE_READ ')
 finally:
  for path,offline in reversed(moved):offline.rename(path)
 ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe');v=json.loads(subprocess.check_output([str(probe),'-v','error','-count_frames','-show_streams','-of','json',reports['writer']['movie']],text=True))['streams'][0];assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],v['nb_read_frames'])==('h264',1920,1080,'24/1','48')
 assert all(digest(folder/n)==sha for n,sha in manual.items()) and all(digest(ROOT/n)==sha for n,sha in frozen.items())
 proof=dict(reports=reports,packages=inventory,manual_sha256=manual,video=v,source_sha256=frozen,isolated_display=o.isolated_display,private_receipts=receipts,scope='Existing .has asset-container variation chosen by owner; independent canonical model/map plus inline dependencies/provenance, UI/export identity, append Undo, source/cache-offline fresh reader and exact media input. Not external-format export or redistribution/native fidelity certification.')
 (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

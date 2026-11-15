"""Mapped helper-joint IK and direct-chain regression through private live app and media."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path,required=True);o=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
 for label,extra in [('helper',[]),('direct',['--direct'])]:
  case=folder/label;case.mkdir();args=command('tests/helper_limb_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(case/'engine.log'),'--',str(case),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=145);log=p.stdout+p.stderr;(case/'console.log').write_text(log);marker='HELPER_LIMB '
  assert p.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  result=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert result['checks']>=35 and result['failures']==0,result
  ffmpeg=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=Path(ffmpeg).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe');video=json.loads(subprocess.check_output([str(probe),'-v','error','-count_frames','-show_streams','-of','json',result['movie']],text=True));v=next(s for s in video['streams'] if s['codec_type']=='video');assert (v['codec_name'],v['width'],v['height'],v['nb_read_frames'],v['r_frame_rate'])==('h264',1920,1080,'48','24/1'),v
  reports[label]={'app':result,'video':v};print(label+': PASS',flush=True)
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
 assert all(digest(ROOT/path)==sha for path,sha in frozen.items())
 proof=dict(reports=reports,source_sha256=frozen,isolated_display=o.isolated_display,private_receipts=receipts,scope='Original skinned helper and direct-chain fixtures; actual hand drag/crouch/Undo/Redo/cold packed/recovery/exact export input. No native ecosystem fidelity claim.')
 (folder/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

"""Actual400drawing manual save responsiveness, verified backup and fresh packed reader."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--isolated-display');o=p.parse_args();source=o.input.resolve();assert source.is_file()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:p.error('Explicit private display required; no shared fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/has-background-large'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False);source_sha=digest(source)
 frozen={str(q.relative_to(ROOT)):digest(q) for part in ['src','tests','tools','examples'] for q in (ROOT/part).rglob('*') if q.is_file() and q.suffix!='.pyc' and '__pycache__' not in q.parts};reports={};memory={};receipts=[]
 def execute(label,extra,marker):
  args=command('tests/has_background_large_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);started=time.monotonic();peak=0;hwm=0
  with (folder/(label+'.log')).open('wb') as out:
   process=subprocess.Popen(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
   while process.poll() is None:
    if time.monotonic()-started>305:process.terminate();process.wait(timeout=15);raise TimeoutError(label)
    if sys.platform=='linux':
     try:
      for line in Path(f'/proc/{process.pid}/status').read_text().splitlines():
       if line.startswith('VmRSS:'):peak=max(peak,int(line.split()[1])*1024)
       if line.startswith('VmHWM:'):hwm=max(hwm,int(line.split()[1])*1024)
     except FileNotFoundError:pass
    time.sleep(.05)
  log=(folder/(label+'.log')).read_text(errors='replace');assert process.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['checks']>0 and reports[label]['failures']==0;memory[label]={'Godot_RSS_sample_peak_bytes':peak or None,'Godot_HWM_observed_bytes':hwm or None,'wall_seconds':time.monotonic()-started,'scope':'Godot process only; not process family, GPU or whole-app hard admission'}
  if os.name=='nt':
   path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
  print(label+': PASS',flush=True)
 execute('writer',[str(source)],'HAS_BACKGROUND_LARGE_WRITE ');target=folder/'Background400.has';manual=digest(target);moved=[]
 try:
  cache=folder/'writer-cache';offline=folder/'writer-cache.offline';assert not offline.exists();cache.rename(offline);moved.append((cache,offline))
  execute('reader',['--read'],'HAS_BACKGROUND_LARGE_READ ')
 finally:
  for path,offline in reversed(moved):offline.rename(path)
 assert digest(source)==source_sha and digest(target)==manual and all(digest(ROOT/path)==sha for path,sha in frozen.items())
 result=dict(reports=reports,process_memory=memory,input=str(source),input_sha256=source_sha,input_and_manual_unchanged=True,writer_cache_offline_for_reader=True,all400cold_pixels_exact=True,source_sha256=frozen,isolated_display=o.isolated_display,private_receipts=receipts,scope='Actual400prepared-video project background manual snapshot and packed save; pixel/metadata/backup/input/frame responsiveness evidence only, not universal save latency or wholeRAM/native-device certification.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

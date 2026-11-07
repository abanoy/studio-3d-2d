"""Detached manual HAS snapshot worker, actual private cancellation, late edits and cold reader."""
from pathlib import Path
import argparse,hashlib,json,math,os,re,struct,subprocess,sys,time,wave
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--isolated-display');parser.add_argument('--output',type=Path);o=parser.parse_args()
 if os.name!='nt':
  if sys.platform!='linux' or not o.isolated_display:parser.error('An existing private X display is required; no visible fallback')
  configure_private_display(o.isolated_display)
 folder=(o.output or ROOT/'output/has-background'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
 with wave.open(str(folder/'tone.wav'),'wb') as f:
  f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(b''.join(struct.pack('<h',int(12000*math.sin(2*math.pi*1000*i/48000))) for i in range(24000)))
 frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools','examples'] for p in (ROOT/part).rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts};reports={};receipts=[]
 def execute(label,script,marker,headless=False,extra=()):
  args=command('tests/'+script+'.gd',headless=headless,extra=([] if headless else ['--audio-driver','Dummy'])+['--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra]);p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=195);log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log)
  assert p.returncode==0 and marker in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
  reports[label]=json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)));assert reports[label]['checks']>0 and reports[label]['failures']==0
  if os.name=='nt' and not headless:
   path=Path(args[args.index('--receipt')+1]);r=json.loads(path.read_bytes());assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'];receipts.append(str(path))
  print(label+': PASS',flush=True)
 execute('domain','has_snapshot_writer_unit','HAS_SNAPSHOT_WRITER_UNIT ',True)
 for pattern in ['test_has_project.py','test_has_save_faults.py']:
  p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern],cwd=ROOT,capture_output=True,text=True,timeout=90);(folder/(pattern+'.log')).write_text(p.stdout+p.stderr);count=re.search(r'Ran ([1-9][0-9]*) tests',p.stderr);assert p.returncode==0 and count,p.stdout+p.stderr;reports[pattern]={'checks':int(count.group(1)),'failures':0}
 execute('writer','has_background_save_smoke','HAS_BACKGROUND_WRITE ')
 manual={name:digest(folder/name) for name in ['Background.has','Linked.has']};moved=[]
 try:
  for path in [folder/'tone.wav',folder/'writer-cache']:
   offline=path.with_name(path.name+'.offline');assert not offline.exists();path.rename(offline);moved.append((path,offline))
  execute('reader','has_background_save_smoke','HAS_BACKGROUND_READ ',extra=['--read'])
 finally:
  for path,offline in reversed(moved):offline.rename(path)
 assert all(digest(folder/name)==sha for name,sha in manual.items());assert all(digest(ROOT/path)==sha for path,sha in frozen.items())
 result=dict(reports=reports,source_sha256=frozen,manual_files_unchanged_in_reader=True,owned_source_and_writer_cache_offline=True,frozen_functional_sources=True,isolated_display=o.isolated_display,private_receipts=receipts,scope='Actual detached manual snapshot, ready-gated packer, cancel/fault/newer-edit/stale-document/close/teardown/backup safety and packed/linked cold audio+pixels; large workload and broader compatibility separate.')
 (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()

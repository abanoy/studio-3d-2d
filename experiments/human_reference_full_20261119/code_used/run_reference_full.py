from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'output'/('windows-human-reference-'+str(time.time_ns()))
RUN.mkdir()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot():
    files=[]
    for tree in ('src','tools','tests','data','examples'):
        files.extend(p for p in (ROOT/tree).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files.extend(ROOT/name for name in ('project.godot','main.tscn','run.py','launch.pyw','dependencies.json'))
    return {p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in files}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def write(name,value):(RUN/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
before=snapshot();revision=git('rev-parse','HEAD')
assert revision=='08ad583de735393c5baa75ca9960482243dccff1'
assert not (ROOT/'override.cfg').exists()
write('source-before.json',before)
prior_receipts={str(p.resolve()) for p in (ROOT/'output').rglob('*.json')}
environment=os.environ.copy()
environment.update(PYTHONDONTWRITEBYTECODE='1',HYBRID_PYTHON=sys.executable,HYBRID_GODOT=r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe',HYBRID_NATIVE_FIXTURES=str(ROOT.parent/'has-acceptance-session-20261111'/'output'))
environment.update(HYBRID_HECATIA_KRA=r'C:\a\Programming\HAS\hecatia.kra',HYBRID_SOURCEIO=str(ROOT.parent/'has-neon-review-20261116-c2d52ff'/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'),HYBRID_NATIVE_INPUTS=r'C:\a\dump',HYBRID_FFMPEG=r'C:\Program Files\ffmpeg\bin\ffmpeg.exe')
environment.pop('HYBRID_FAN_PROJECT',None)
assert sha(Path(environment['HYBRID_HECATIA_KRA']))=='fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758'
started=time.time_ns()
with (RUN/'stdout.log').open('wb') as out,(RUN/'stderr.log').open('wb') as err:
    child=subprocess.Popen([sys.executable,'-B','-u','tests/verify.py'],cwd=ROOT,env=environment,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    write('launch.json',{'pid':child.pid,'coordinator_pid':os.getpid(),'started_ns':started,'revision':revision,'command':[sys.executable,'-B','-u','tests/verify.py'],'environment':{key:value for key,value in environment.items() if key.startswith('HYBRID_') or key=='PYTHONDONTWRITEBYTECODE'}})
    print(json.dumps({'folder':str(RUN),'child':child.pid,'coordinator':os.getpid()}),flush=True)
    child.wait()
after=snapshot();write('source-after.json',after)
receipts=[]
for p in (ROOT/'output').rglob('*.json'):
    if str(p.resolve()) not in prior_receipts and p.stat().st_size<=1024*1024:
        try:
            value=json.loads(p.read_bytes())
            if isinstance(value,dict) and 'job_closed' in value and 'desktop_closed' in value:
                keys=('exit','job_closed','desktop_closed','child_desktop_confirmed','foreground_child_observed','desktop_switch_requested','private_window_seen')
                receipts.append({'path':str(p),'sha256':sha(p),**{key:value.get(key) for key in keys}})
        except (ValueError,OSError):pass
report={'format':'has_reference_full_coordinator_1','revision':revision,'exit':child.returncode,'child_reaped':child.poll() is not None,'seconds':(time.time_ns()-started)/1e9,'functional_source_count':len(before),'functional_sources_unchanged':before==after,'revision_unchanged':git('rev-parse','HEAD')==revision,'new_private_receipts':receipts,'whole_verifier_pass':child.returncode==0 and before==after and git('rev-parse','HEAD')==revision,'private_art_uploaded':False}
write('completion.json',report)
print(json.dumps({key:value for key,value in report.items() if key!='new_private_receipts'}),flush=True)
sys.exit(0 if report['whole_verifier_pass'] else 1)

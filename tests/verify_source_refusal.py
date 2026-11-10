"""Actual native Source bound diagnostics and preservation on a private desktop."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True);parser.add_argument('--isolated-display');o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(o.isolated_display)
    source=o.native.resolve(strict=True);before=(digest(source),source.stat().st_mtime_ns)
    folder=ROOT/'output/source-native-refusal'/str(time.time_ns());folder.mkdir(parents=True)
    staged=folder/source.name;shutil.copy2(source,staged)
    argv=command('tests/source_refusal_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/'engine.log'),'--',str(folder),str(staged)])
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=330)
    log=p.stdout+p.stderr;(folder/'stdout.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'SOURCE_NATIVE_REFUSAL ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    result=json.loads((folder/'result.json').read_bytes());assert result['failures']==0
    if os.name=='nt':
        path=Path(argv[argv.index('--receipt')+1]);r=json.loads(path.read_bytes())
        assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
        result['private_receipt']=str(path)
    assert (digest(source),source.stat().st_mtime_ns)==before and digest(staged)==before[0]
    result.update(original_sha256=before[0],original_unchanged=True)
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()

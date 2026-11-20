"""Private GPU verifier. Run only after the coordinator releases its full lane."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import run

def identity(path):
    path=Path(path);info=path.stat()
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=info.st_size,mtime_ns=info.st_mtime_ns)

def no_reparse(path):
    path=Path(path).absolute()
    assert '..' not in path.parts,'Lexical traversal refused'
    for part in (path,*path.parents):
        if part.exists():
            assert not part.is_symlink() and not getattr(part.lstat(),'st_file_attributes',0)&0x400,'Linked/reparse launch path refused'
    return path

def review_artifacts(preparation):
    expected={'PRIVATE_REVIEW.md','Open six-foot VRM review.bat','Studio/override.cfg',*['Studio/review/'+name for name in ('native_reference.gd','owner_launch.pyw','verify_native_reference.py')]}
    records=preparation['review_artifact_hashes'];normalized={name.replace('\\','/'):digest for name,digest in records.items()}
    assert len(normalized)==len(records) and set(normalized)==expected,'Unexpected review artifact membership'
    for name,digest in normalized.items():
        path=no_reparse(ROOT.parent.joinpath(*name.split('/')))
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,'Prepared review artifact changed: '+name

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lease-confirmed',action='store_true')
    parser.add_argument('--body-guard',action='store_true',help='Explicitly verify the current nonunit reference Body Physics refusal; adds two checks')
    options=parser.parse_args()
    assert options.lease_confirmed and os.name=='nt','An available private Windows graphics lane must be confirmed'
    no_reparse(ROOT.parent/'preparation.json')
    preparation=json.loads((ROOT.parent/'preparation.json').read_bytes());review_artifacts(preparation)
    originals=preparation['original_inputs'];staged={ROOT/name:stamp for name,stamp in preparation['staged_inputs'].items()}
    assert all(identity(no_reparse(path))==stamp for path,stamp in originals.items())
    assert all(identity(no_reparse(path))==stamp for path,stamp in staged.items())
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in preparation['source_hashes'].items())
    assert no_reparse(ROOT/'output').is_dir(),'Prepared review output is missing'
    folder=no_reparse(ROOT/'output'/('verify-native-reference-'+str(time.time_ns())));folder.mkdir(exist_ok=False);no_reparse(folder)
    (folder/'display.cfg').write_text('[display]\ntheme="neon"\npercent=100\n',encoding='utf-8')
    env=os.environ.copy();env.update(HYBRID_PYTHON=preparation['python'],HYBRID_GODOT=preparation['godot'],PYTHONDONTWRITEBYTECODE='1')
    os.environ['HYBRID_GODOT']=preparation['godot']
    args=run.command('review/native_reference.gd',extra=['--log-file',str(folder/'engine.log'),'--','--verify',str(folder),*(['--body-guard'] if options.body_guard else [])])
    (folder/'command.json').write_text(json.dumps(args,indent=2)+'\n',encoding='utf-8')
    process=None
    try:
        process=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,timeout=210,creationflags=subprocess.CREATE_NO_WINDOW)
        log=process.stdout+process.stderr;(folder/'console.log').write_bytes(log)
        result=json.loads((folder/'result.json').read_bytes())
        receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes())
        assert process.returncode==0 and b'NATIVE_HUMAN_REFERENCE ' in log and not any(x in log for x in [b'ERROR:',b'FAIL ',b'ObjectDB instances leaked',b'resources still in use']),log[-5000:]
        assert result['mode']=='verify' and result['status']=='passed' and result['checks']==(25 if options.body_guard else 23) and result['failures']==0,result
        assert result['body_guard_requested'] is options.body_guard,result
        assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and not receipt['desktop_switch_requested'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
        assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in preparation['source_hashes'].items())
        print(json.dumps(dict(folder=str(folder),result=result,private_receipt=str(receipt_path)),indent=2))
    finally:
        preservation=dict(original_inputs_preserved=all(identity(no_reparse(path))==stamp for path,stamp in originals.items()),staged_inputs_preserved=all(identity(no_reparse(path))==stamp for path,stamp in staged.items()))
        (folder/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n',encoding='utf-8')
        assert all(preservation.values()),preservation

if __name__=='__main__':main()

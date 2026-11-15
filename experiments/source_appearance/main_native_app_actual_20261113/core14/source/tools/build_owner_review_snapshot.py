"""Freeze an owner-operated review app away from automated test output/profile."""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]


def included(name):
    parts=Path(name).parts
    return bool(parts) and parts[0] not in ['output','.git','.godot','__pycache__'] and '__pycache__' not in parts and not name.endswith('.pyc')


def safe_destination(target,name):
    windows=PureWindowsPath(name);parts=name.split('/')
    reserved={'CON','PRN','AUX','NUL'}|{p+n for p in ['COM','LPT'] for n in '123456789\u00b9\u00b2\u00b3'}
    assert not windows.anchor and not windows.drive and not windows.root,f'Unsafe snapshot path: {name}'
    assert all(part and part not in ['.','..'] and part==part.rstrip(' .') and
               not any(ord(c)<32 or c in '\\:<>"|?*' for c in part) and
               part.split('.')[0].upper() not in reserved for part in parts),f'Unsafe snapshot path: {name}'
    destination=target.joinpath(*parts)
    assert destination.resolve().is_relative_to(target.resolve()),f'Unsafe snapshot path: {name}'
    return destination


def freeze_source(root,target,revision=None):
    """Copy exact Git blobs when a reviewed revision is requested.

    Working-file mode intentionally retains the original builder's behavior.
    Revision mode never reads staged, modified or untracked working files.
    """
    assert not target.exists(),'Studio must not exist'
    commit=subprocess.check_output(['git','rev-parse','--verify','--end-of-options',(revision or 'HEAD')+'^{commit}'],cwd=root,text=True).strip()
    if revision is None:
        names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
        entries=[(n,None) for n in sorted(set(n for n in names if included(n)))]
    else:
        entries=[]
        tree=subprocess.check_output(['git','ls-tree','-rz',commit],cwd=root)
        for row in tree.split(b'\0'):
            if not row:continue
            metadata,path=row.split(b'\t',1);mode,kind,oid=metadata.split()
            name=path.decode('utf-8')
            if not included(name):continue
            assert mode in [b'100644',b'100755'] and kind==b'blob',f'Unsupported snapshot entry: {name}'
            entries.append((name,oid))
    names={n for n,_ in entries}
    assert {'main.tscn','project.godot','run.py'}<=names,'Missing application entry points'
    destinations={name:safe_destination(target,name) for name,_ in entries}
    assert len({name.casefold() for name in destinations})==len(destinations),'Case-colliding snapshot paths'
    # Validate the whole tree before creating anything. A batch reads blob IDs,
    # avoiding per-file processes and path/revision parsing ambiguity.
    batch=None
    if revision is not None:
        batch=subprocess.check_output(['git','cat-file','--batch'],input=b''.join(oid+b'\n' for _,oid in entries),cwd=root)
    # Atomic reservation also refuses a target created while Git was reading.
    target.mkdir(exist_ok=False)
    hashes={};offset=0
    for name,oid in entries:
        if batch is None:data=(root/name).read_bytes()
        else:
            line_end=batch.index(b'\n',offset);actual,kind,size=batch[offset:line_end].split()
            assert actual==oid and kind==b'blob','Unexpected Git blob response'
            start=line_end+1;end=start+int(size);data=batch[start:end]
            assert len(data)==int(size) and batch[end:end+1]==b'\n','Truncated Git blob response'
            offset=end+1
        destination=destinations[name];destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    assert batch is None or offset==len(batch),'Unexpected trailing Git output'
    return commit,hashes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output/owner-review',help='Existing owned project folder; Studio must not exist')
    parser.add_argument('--revision',help='Freeze exact committed files, excluding all working-tree changes')
    options=parser.parse_args();folder=options.output.resolve();target=folder/'Studio'
    assert folder.is_relative_to(ROOT/'output') and folder!=ROOT/'output','Review folder must stay inside this checkout/output'
    assert folder.is_dir() and not target.exists()
    commit,hashes=freeze_source(ROOT,target,options.revision)
    assert not (target/'output').exists() and not (target/'.godot').exists()
    profile='HAS Owner Acceptance '+str(time.time_ns())
    (target/'override.cfg').write_text('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('owner_review_run',target/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result_path=folder/'source-snapshot-startup.json'
    args=module.command(extra=['res://tests/current_candidate_startup.tscn','--',str(result_path)])
    p=subprocess.run(args,cwd=target,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
    log=p.stdout+p.stderr;(folder/'source-snapshot-startup.log').write_text(log,encoding='utf-8')
    assert p.returncode==0 and 'CURRENT_REVIEW_STARTUP ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    startup=json.loads(result_path.read_bytes());assert startup['home_visible'] and startup['simple'] and startup['empty'] and profile in startup['profile'],startup
    receipt_path=Path(args[args.index('--receipt')+1]);receipt=json.loads(receipt_path.read_bytes())
    assert receipt['exit']==0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed'],receipt
    assert all(hashlib.sha256((target/n).read_bytes()).hexdigest()==digest for n,digest in hashes.items())
    pythonw=Path(sys.executable).with_name('pythonw.exe');assert pythonw.is_file()
    runtime=ROOT/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
    for name in ['Flatgrass','Avatar','Street']+[n for n in ['Reimu helpers','Back hair demo','Mima head expressions'] if(folder/(n+'.has')).is_file()]:
        assert (folder/(name+'.has')).is_file()
        text=f'@echo off\r\nsetlocal\r\nset "HYBRID_SOURCEIO={runtime}"\r\nstart "" "{pythonw}" "%~dp0Studio\\launch.pyw" "%~dp0{name}.has"\r\n'
        (folder/('Open '+name+'.bat')).write_bytes(text.encode('utf-8'))
    (folder/'Start review.bat').write_bytes(f'@echo off\r\nsetlocal\r\nset "HYBRID_SOURCEIO={runtime}"\r\nstart "" "{pythonw}" "%~dp0Studio\\launch.pyw"\r\n'.encode('utf-8'))
    result={'format':'has_owner_review_source_snapshot_2','target':str(target),'source_commit':commit,'source_mode':'git_revision' if options.revision is not None else 'working_tree','source_hashes':hashes,'profile':profile,'normal_startup':startup,'private_receipt':receipt,'no_development_cache_copied':True,'automated_tests_separate_from_owner_output_and_preferences':True,'installation_replaced':False,'retention':'Keep this review source/project folder while actual owner observations are pending. Private review artwork is not uploaded.'}
    if options.revision is None:result['working_source_hashes']=hashes
    (folder/'source-snapshot-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['working_source_hashes','source_hashes']},indent=2))


if __name__=='__main__':main()

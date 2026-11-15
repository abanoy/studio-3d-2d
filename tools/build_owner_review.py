"""Create separate native reviewer HAS projects and verify their portable cold pixels.

Prepared GLBs and private review media remain local. This does not certify artist
appearance, physical input, or a clean installation and never launches visible UI.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run import command,configure_private_display

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['flatgrass','avatar','street']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--isolated-display');o=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not o.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(o.isolated_display)
    folder=o.output.resolve();folder.mkdir(parents=True,exist_ok=False)
    plan=[{'name':name.title(),'kind':'model' if name=='avatar' else 'environment','glb':str(getattr(o,name).resolve(strict=True))} for name in ['flatgrass','avatar','street']]
    assert all(Path(row['glb']).suffix.lower()=='.glb' for row in plan)
    inputs={Path(row['glb']):sha(Path(row['glb'])) for row in plan}
    (folder/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    receipts=[]
    def execute(label,extra):
        argv=command('tools/build_owner_review.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra])
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=210)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and 'OWNER_REVIEW ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        if os.name=='nt':
            path=Path(argv[argv.index('--receipt')+1]);r=json.loads(path.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append({'path':str(path),'receipt':r})
    execute('writer',[]);writer=json.loads((folder/'writer.json').read_bytes());assert writer['failures']==0
    moved=[]
    try:
        for row in writer['observations']:
            path=Path(row['source']).resolve(strict=True);assert path.is_relative_to(ROOT/'output/imports') and sha(path)==row['sha256']
            offline=path.with_name(path.name+'.owner-review-offline');assert not offline.exists();path.rename(offline);moved.append((path,offline))
        for path in inputs:
            offline=path.with_name(path.name+'.owner-review-offline');assert not offline.exists();path.rename(offline);moved.append((path,offline))
        path=folder/'writer-cache';offline=folder/'writer-cache.offline';path.rename(offline);moved.append((path,offline))
        execute('reader',['--read'])
    finally:
        for path,offline in reversed(moved):offline.rename(path)
    assert all(sha(p)==digest for p,digest in inputs.items())
    projects={}
    for row in plan:
        name=row['name'];p=folder/(name+'.has')
        with zipfile.ZipFile(p) as z:
            manifest=json.loads(z.read('project.json'))
            assert len(manifest['world']['objects'])==1
            for asset in manifest['world']['objects']:
                assert hashlib.sha256(z.read(asset['path'])).hexdigest()==asset['sha256']
        projects[name]={'path':str(p),'sha256':sha(p)}
        if os.name=='nt':
            pythonw=Path(sys.executable).with_name('pythonw.exe');assert pythonw.is_file()
            text=f'@echo off\r\nstart "" "{pythonw}" "{ROOT / "launch.pyw"}" "%~dp0{name}.has"\r\n'
            (folder/('Open '+name+'.bat')).write_bytes(text.encode('utf-8'))
    result={'format':'has_owner_review_pack_1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'projects':projects,'writer':writer,'reader':json.loads((folder/'reader.json').read_bytes()),'private_receipts':receipts,'cold_source_managed_import_and_writer_cache_withheld':True,'scope':'Runnable isolated native projects for actual owner review; exact self-replay is not artist/source-fidelity approval.'}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()

"""Actual installed PCF names/material preparation; no GPU or missing-data pass."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from source_content import discover
from source_paths import DEFAULT_GMOD,DEFAULT_WORKSHOP
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    sys.stdout.reconfigure(encoding='utf-8');reference=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else ROOT
    baseline=read(reference/'output/particle-sprite-verification.json');sourceio=reference/'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
    folder=ROOT/'output/particle-browser-data'/str(time.time_ns());folder.mkdir(parents=True);cases=[];originals={}
    def worker(request,name,ok=True):
        p=folder/(name+'-request.json');result=folder/(name+'-result.json');request={**request,'result':str(result)};p.write_text(json.dumps(request),encoding='utf-8')
        run=subprocess.run([sys.executable,'tools/particle_browser.py',str(p)],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=65,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt'else 0)
        (folder/(name+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8');r=read(result);assert r['ok']==ok and run.returncode==(0 if ok else 1),(r,run.stdout,run.stderr);return r
    for i,row in enumerate(baseline['plans']):
        report=read(Path(row['bundle'])/'report.json');first=report['resources'][0];provider=Path(first['provider']);source=provider/first['resource']if provider.is_dir()else provider
        originals[str(source)]={'sha256':sha(source),'mtime_ns':source.stat().st_mtime_ns}
        req={'provider':str(provider),'member':first['resource'],'system':report['system']['name'],'duration':2,'seed':17,'sourceio':str(sourceio)}
        listing=worker({**req,'action':'list'},str(i)+'-list');selected=[s for s in listing['systems']if s['name']==req['system']];assert len(selected)==1 and selected[0]['candidate']and any(not s['candidate']for s in listing['systems'])
        bundle=folder/('effect-'+str(i));prepared=worker({**req,'action':'prepare','output':str(bundle)},str(i)+'-prepare')
        assert sha(bundle/'effect.json')==row['effect_sha256']and sha(bundle/'sprite.png')==row['texture_sha256']
        cases.append({'name':req['system'],'systems':len(listing['systems']),'unavailable':sum(not s['candidate']for s in listing['systems']),'bundle':str(bundle),'effect_sha256':sha(bundle/'effect.json'),'texture_sha256':sha(bundle/'sprite.png')})
        if i==0:
            disabled={p['path']:False for p in discover(DEFAULT_GMOD,DEFAULT_WORKSHOP,[])['providers']}
            failed=worker({**req,'action':'prepare','output':str(folder/'disabled'),'mount_overrides':disabled},'disabled-mounts',False);assert 'Missing installed particle resource'in failed['error']
            extra=folder/'extra'
            own_report=read(bundle/'report.json')
            for asset in own_report['resources'][1:]:
                target=extra/asset['resource'];assert target.resolve().is_relative_to(extra.resolve());target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((bundle/('material.vmt'if target.suffix=='.vmt'else'source.vtf')).read_bytes())
            rebuilt=folder/'extra-rebuild';worker({**req,'action':'prepare','output':str(rebuilt),'mount_overrides':disabled,'extra':[str(extra)]},'extra-mount')
            assert sha(rebuilt/'effect.json')==row['effect_sha256']and sha(rebuilt/'sprite.png')==row['texture_sha256']
            assert all(Path(r['provider'])==extra for r in read(rebuilt/'report.json')['resources'][1:])
    assert all(sha(p)==r['sha256']and Path(p).stat().st_mtime_ns==r['mtime_ns']for p,r in originals.items())
    result={'folder':str(folder),'cases':cases,'disabled_mounts_refused':True,'additional_mount_resolved':True,'originals_unchanged':True,'ui_tested':False}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/particle-browser-data-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

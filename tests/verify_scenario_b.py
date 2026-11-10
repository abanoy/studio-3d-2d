"""Native BSP + VRM + complete street PMX, multiple roots, cold packed replay and MP4."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from run import command,configure_private_display
from asset_audit import inspect

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['bsp','vrm','pmx']:parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--output',type=Path);parser.add_argument('--isolated-display')
    options=parser.parse_args()
    if os.name!='nt':
        if sys.platform!='linux' or not options.isolated_display:parser.error('Explicit private display required; no visible fallback')
        configure_private_display(options.isolated_display)
    sources={name:getattr(options,name).resolve(strict=True) for name in ['bsp','vrm','pmx']}
    assert all(p.is_file() and p.suffix.lower()=='.'+name for name,p in sources.items())
    originals={p:(digest(p),p.stat().st_mtime_ns) for p in sources.values()}
    audit=inspect(sources['pmx'])
    for item in audit['texture_dependencies']:
        assert item['present'] and not item.get('unsafe'),item
        p=(sources['pmx'].parent/item['name']).resolve(strict=True)
        assert p.is_relative_to(sources['pmx'].parent)
        originals[p]=(digest(p),p.stat().st_mtime_ns)
    folder=(options.output or ROOT/'output/scenario-b'/str(time.time_ns())).resolve();folder.mkdir(parents=True,exist_ok=False)
    inputs=folder/'inputs';inputs.mkdir();plan={}
    for name,p in sources.items():
        destination=inputs/name/p.name;destination.parent.mkdir();shutil.copy2(p,destination);plan[name]=str(destination)
    for item in audit['texture_dependencies']:
        destination=Path(plan['pmx']).parent/item['name'];destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(sources['pmx'].parent/item['name'],destination)
    (folder/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
    frozen={str(p.relative_to(ROOT)):digest(p) for part in ['src','tests','tools'] for p in (ROOT/part).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    reports={};receipts=[]
    def launch(label,extra):
        argv=command('tests/scenario_b_smoke.gd',extra=['--audio-driver','Dummy','--log-file',str(folder/(label+'-engine.log')),'--',str(folder),*extra])
        p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=330)
        log=p.stdout+p.stderr;(folder/(label+'.log')).write_text(log,encoding='utf-8')
        assert p.returncode==0 and 'SCENARIO_B ' in log and not any(x in log for x in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
        report=json.loads(next(line[len('SCENARIO_B '):] for line in log.splitlines() if line.startswith('SCENARIO_B ')));assert report['failures']==0
        reports[label]=report
        if os.name=='nt':
            path=Path(argv[argv.index('--receipt')+1]);r=json.loads(path.read_bytes())
            assert r['exit']==0 and r['child_desktop_confirmed'] and not r['foreground_child_observed'] and r['job_closed'] and r['desktop_closed'],r
            receipts.append(str(path))
    launch('writer',[])
    writer=json.loads((folder/'writer.json').read_bytes());project=folder/'Native ecosystems.has';project_sha=digest(project)
    with zipfile.ZipFile(project) as archive:
        manifest=json.loads(archive.read('project.json'))
        assert all(row['path'] in archive.namelist() for row in manifest['world']['objects'])
    moved=[]
    try:
        paths=[inputs,folder/'writer-cache',*[Path(p) for p in writer['bundles']],*[Path(p) for p in writer['managed_sources']]]
        for path in paths:
            path=path.resolve(strict=True);assert path.is_relative_to(ROOT/'output'),path
            if path.is_file():assert digest(path)==writer['managed_sources'][str(path).replace('\\','/')],path
            offline=path.with_name(path.name+'.scenario-b-offline');assert not offline.exists()
            path.rename(offline);moved.append((path,offline))
        launch('reader',['--read'])
    finally:
        for path,offline in reversed(moved):offline.rename(path)
    assert digest(project)==project_sha
    assert all((digest(p),p.stat().st_mtime_ns)==state for p,state in originals.items())
    assert all(digest(ROOT/p)==sha for p,sha in frozen.items())
    encoder=os.environ.get('HYBRID_FFMPEG','ffmpeg');probe=str(Path(encoder).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe'))
    flags={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    media=json.loads(subprocess.check_output([probe,'-v','error','-count_frames','-show_streams','-of','json',writer['movie']],**flags))
    video=next(row for row in media['streams'] if row['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['r_frame_rate'],video['nb_read_frames'])==('h264',1920,1080,'24/1','24')
    result=dict(reports=reports,map_report=writer['map_report'],pmx_report=writer['pmx_report'],
                original_sha256={str(p):state[0] for p,state in originals.items()},originals_unchanged=True,
                source_sha256=frozen,private_receipts=receipts,video=video,manual_has_sha256=project_sha,
                source_bundles_managed_imports_writer_cache_offline_for_reader=True,
                scope='Native scenario B supported software route, exact cold Lit/Unshaded pixels, original preservation and actual MP4. Artist fidelity and unsupported native features remain separate.')
    (folder/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','map_report','pmx_report']},indent=2))

if __name__=='__main__':main()

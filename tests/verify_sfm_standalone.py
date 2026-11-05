"""Actual installed SFM browser/model/map/effect with an absent GMod path."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run import command
from source_installation import installed_context
from source_paths import DEFAULT_GMOD,DEFAULT_WORKSHOP

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    folder=ROOT/'output/sfm-standalone'/str(time.time_ns());folder.mkdir(parents=True)
    missing=folder/'Steam/steamapps/common/GarrysMod';workshop=folder/'Steam/steamapps/workshop/content/4000'
    assert not missing.exists() and not workshop.exists()
    context=installed_context(missing,workshop)
    assert context['gmod_installation']=='' and context['sfm_installations']
    sfm=Path(context['sfm_installations'][0])/'game'
    native=[sfm/'tf_movies/models/player/hwm/scout.mdl',sfm/'tf_movies/maps/box.bsp',sfm/'usermod/gameinfo.txt',sfm/'sfm.exe']
    before={str(p):{'sha256':sha(p),'mtime_ns':p.stat().st_mtime_ns}for p in native}
    frozen={str(p.relative_to(ROOT)):sha(p)for d in ['src','tools','tests','data','examples']for p in(ROOT/d).rglob('*')if p.is_file() and '__pycache__'not in p.parts and p.suffix!='.pyc'}
    def worker(script,request,name,success=True):
        request_path=folder/(name+'-request.json');result_path=folder/(name+'-result.json')
        request={**request,'gmod':str(missing),'workshop':str(workshop),'result':str(result_path)}
        request_path.write_text(json.dumps(request),encoding='utf-8')
        process=subprocess.run([sys.executable,'tools/'+script,str(request_path)],cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=70)
        (folder/(name+'.log')).write_text(process.stdout+process.stderr,encoding='utf-8')
        result=read(result_path);assert result['ok']==success and process.returncode==(0 if success else 1),(name,result,process.stdout,process.stderr)
        return result
    discovery=worker('source_browser.py',{'action':'discover'},'browser-discovery')
    assert all(p['origin']not in{'game','addon','workshop','download','gamemode','mount.cfg'}for p in discovery['providers'])
    provider=next(p for p in discovery['providers']if Path(p['path'])==sfm/'tf_movies')
    indexed=worker('source_browser.py',{'action':'index','provider':provider},'browser-index')
    assert any(a['path']=='models/player/hwm/scout.mdl'for a in indexed['assets'])
    found=worker('source_browser.py',{'action':'search','providers':[provider],'query':'player/hwm/scout'},'browser-search')
    assert any(a['path']=='models/player/hwm/scout.mdl'for a in found['assets'])
    baseline=read(ROOT/'output/particle-sprite-verification.json');effect=baseline['plans'][0]
    report=read(Path(effect['bundle'])/'report.json');resource=report['resources'][0]
    req={'provider':resource['provider'],'member':resource['resource'],'system':report['system']['name'],'seed':17,'duration':2}
    listed=worker('particle_browser.py',{**req,'action':'list'},'particle-list')
    assert any(s['name']==req['system']and s['candidate']for s in listed['systems'])
    prepared=folder/'effect'
    worker('particle_browser.py',{**req,'action':'prepare','output':str(prepared)},'particle-prepare')
    assert sha(prepared/'effect.json')==effect['effect_sha256']and sha(prepared/'sprite.png')==effect['texture_sha256']
    particle_report=read(prepared/'report.json')
    assert all('garrysmod'not in r['provider'].lower()for r in particle_report['resources'])
    gmod_report=read(Path(baseline['plans'][1]['bundle'])/'report.json');gmod_source=gmod_report['resources'][0]
    refused=worker('particle_browser.py',{'action':'prepare','provider':gmod_source['provider'],'member':gmod_source['resource'],'system':gmod_report['system']['name'],'output':str(folder/'gmod-must-not-create')},'gmod-refused',False)
    assert 'must already be installed'in refused['error']and not(folder/'gmod-must-not-create').exists()
    plan=folder/'plan.json';plan.write_text(json.dumps({'model':str(native[0]),'map':str(native[1]),'gmod':str(missing),'workshop':str(workshop),'folder':str(folder/'app')}),encoding='utf-8')
    args=command('tests/sfm_render_smoke.gd',extra=['--',str(plan)])
    process=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=240)
    log=process.stdout+process.stderr;(folder/'app.log').write_text(log,encoding='utf-8')
    assert process.returncode==0 and 'SFM_SMOKE 'in log and not any(t in log for t in ['ERROR:','FAIL ','ObjectDB instances leaked']),log
    receipt_path=Path(args[args.index('--receipt')+1]);receipt=read(receipt_path)
    assert receipt['exit']==0 and receipt['child_desktop_confirmed']and not receipt['foreground_child_observed']and receipt['job_closed']and receipt['desktop_closed']
    app=read(folder/'app/result.json');assert app['failures']==0
    for bundle in ['model_bundle','map_bundle']:
        conversion=read(Path(app[bundle])/'conversion-request.json')
        assert conversion['source_profile']=='sfm'and conversion['gmod_installation']==''and conversion['sfm_installations']
        assert all('garrysmod'not in str(p).lower()for p in conversion['mounts'])
    deps=read(Path(app['model_bundle'])/'dependencies.json')
    providers={Path(d['provider']).resolve()for d in deps['resolved']if d['path'].lower().endswith(('.vmt','.vtf'))}
    assert (sfm/'tf').resolve()in providers and (sfm/'tf_movies').resolve()in providers
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',app['movie']],encoding='utf-8'))
    video=next(s for s in probe['streams']if s['codec_type']=='video')
    assert(video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'])==('h264',1920,1080,'48','24/1')
    assert all(sha(p)==v['sha256']and Path(p).stat().st_mtime_ns==v['mtime_ns']for p,v in before.items())
    assert all(sha(ROOT/n)==h for n,h in frozen.items())
    result={'folder':str(folder),'app':app,'private_receipts':[str(receipt_path)],'functional_inputs':frozen,'functional_unchanged':True,'originals_unchanged':True,'gmod_path_absent':True,'gmod_source_refused':True,'native_particle_matches':True,'native_cross_mod_textures':True,'normal_updated':False}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(ROOT/'output/sfm-standalone-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items()if k!='functional_inputs'},indent=2))
if __name__=='__main__':main()

"""Build an isolated browser preview using installed Godot; never deploys."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time

ROOT=Path(__file__).resolve().parents[1]
WASM_SHA='2b558bdb3c3af1f822ce6c43e09e1fa844d82fa440fe40d2d25d6c36ddf95137'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot',type=Path)
    parser.add_argument('--template',type=Path)
    options=parser.parse_args()
    sys.path.insert(0,str(ROOT));from run import engine_path
    godot=options.godot or Path(engine_path())
    version=subprocess.check_output([str(godot),'--version'],text=True).strip()
    if not version.startswith('4.6.stable'):raise RuntimeError('Godot4.6 stable standard is required.')
    template=options.template or Path(os.environ.get('APPDATA',''))/'Godot/export_templates/4.6.stable/web_nothreads_release.zip'
    if not template.is_file():raise RuntimeError('Install the matching Godot4.6 Web export templates, or pass --template. Nothing was downloaded.')
    folder=ROOT/'output/web-builds'/str(time.time_ns());app=folder/'app';raw=folder/'raw-export';site=folder/'site';public=site/'tools/hybrid-animation-studio/app'
    for path in [app,raw,public]:path.mkdir(parents=True)
    sources={}
    def copy(source,relative):
        destination=app/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination);sources[str(relative).replace('\\','/')]=sha(source)
    for name in ['project.godot','main.tscn']:copy(ROOT/name,Path(name))
    for parent in ['src','data','web']:
        for source in (ROOT/parent).rglob('*'):
            if source.is_file() and source.suffix in ('.gd','.gdshader','.json','.svg'):copy(source,source.relative_to(ROOT))
    approved=json.loads((ROOT/'web/procedural-assets.json').read_text())
    for rel,digest in approved.items():
        if not rel.startswith('examples/') or '..' in Path(rel).parts or sha(ROOT/rel)!=digest:raise RuntimeError('Procedural example changed; review its provenance and update the explicit inventory: '+rel)
        copy(ROOT/rel,Path(rel))
    for source in (app/'src').glob('*.gd'):
        text=source.read_text(encoding='utf-8').replace('res://output/','user://output/').replace('res://output"','user://output"')
        source.write_text(text,encoding='utf-8')
    source=app/'src/app.gd';text=source.read_text(encoding='utf-8')
    for old,new in [('res://src/has_project.gd','res://web/web_has_project.gd'),('res://src/source_browser.gd','res://web/web_source_browser.gd'),('res://src/source_import.gd','res://web/web_source_import.gd'),('res://src/fill_editor.gd','res://web/web_fill_editor.gd')]:
        assert text.count(old)==1; text=text.replace(old,new)
    icon='DisplayServer.set_icon(StudioTheme.icon("scene").get_image())';assert text.count(icon)==1
    text=text.replace(icon,'if not OS.has_feature("web"): '+icon);source.write_text(text,encoding='utf-8')
    source=app/'main.tscn';text=source.read_text();assert text.count('res://src/app.gd')==1;source.write_text(text.replace('res://src/app.gd','res://web/web_app.gd'))
    source=app/'project.godot';text=source.read_text();assert 'config/icon=' not in text;text=text.replace('[application]','[application]\nconfig/icon="res://web/studio.svg"');source.write_text(text)
    preset='''[preset.0]
name="Web"
platform="Web"
runnable=true
advanced_options=false
dedicated_server=false
export_filter="all_resources"
include_filter="data/*.json,examples/*.glb,examples/tutorials/*.json,examples/tutorials/*.has,examples/tutorials/*.glb"
exclude_filter="output/*,tests/*,tools/*,docs/*"
export_path=""
script_export_mode=2

[preset.0.options]
custom_template/release="TEMPLATE"
variant/extensions_support=false
variant/thread_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=false
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
progressive_web_app/enabled=false
'''
    (app/'export_presets.cfg').write_text(preset.replace('TEMPLATE',template.resolve().as_posix()))
    env=os.environ.copy();profile=folder/'editor-profile';profile.mkdir();env['APPDATA']=str(profile)
    def invoke(extra,name):
        args=[str(godot),'--headless','--path',str(app),'--log-file',str(folder/(name+'-engine.log')),*extra]
        process=subprocess.run(args,env=env,capture_output=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        log=process.stdout+process.stderr;(folder/(name+'-console.log')).write_bytes(log)
        if process.returncode or b'ERROR:' in log:raise RuntimeError(name+' failed; retained logs: '+str(folder))
    invoke(['--editor','--import','--quit'],'import')
    invoke(['--export-release','Web',str(raw/'index.html')],'export')
    for source in raw.iterdir():
        if source.name!='index.wasm':shutil.copy2(source,public/source.name)
    wasm=(raw/'index.wasm').read_bytes()
    if hashlib.sha256(wasm).hexdigest()!=WASM_SHA:raise RuntimeError('Unexpected Web engine bytes; review the pinned template before changing the loader.')
    manifest={'format':'has_web_engine_chunks_1','bytes':len(wasm),'sha256':WASM_SHA,'parts':[]}
    for index,start in enumerate(range(0,len(wasm),16777216)):
        chunk=wasm[start:start+16777216];name=f'index.wasm.part{index}';(public/name).write_bytes(chunk)
        manifest['parts'].append({'path':name,'bytes':len(chunk),'sha256':hashlib.sha256(chunk).hexdigest()})
    (public/'engine-chunks.json').write_text(json.dumps(manifest,indent=2))
    for name in ['has-files.js','has-engine-loader.js']:shutil.copy2(ROOT/'web'/name,public/name)
    text=(raw/'index.js').read_text();needle='loadPromise = preloader.loadPromise(`${loadPath}.wasm`, size, true);';assert text.count(needle)==1
    (public/'index.js').write_text(text.replace(needle,'loadPromise = window.HASLoadEngine(loadPath); // HAS: verified same-origin chunks.'))
    text=(raw/'index.html').read_text()
    needle='<script src="index.js"></script>';assert text.count(needle)==1
    text=text.replace(needle,'<script src="has-engine-loader.js"></script>\n<script src="has-files.js"></script>\n'+needle)
    text=text.replace('<title>Hybrid Animation Studio</title>','<title>Hybrid Animation Studio</title>\n<link rel="icon" type="image/png" href="index.png">')
    text=text.replace('const engine = new Engine(GODOT_CONFIG);','try {\nif(typeof window.HASLoadEngine!=="function" || !window.HASFiles)throw new Error("A required Studio script did not load.");\nconst engine = new Engine(GODOT_CONFIG);\nwindow.HASEngine = engine;')
    text=text.replace('function displayFailureNotice(err) {','function displayFailureNotice(err) {\n        window.HAS_BOOT_ERROR=String(err);\n        if(parent!==window)parent.postMessage({type:"has:error",message:"Studio could not start. Try loading again."},location.origin);')
    # The pinned loader's init() does not forward a rejected load promise. Preflight
    # it outside init so missing/corrupt parts reach the normal failure notice.
    assert text.count('engine.startGame({')==1;text=text.replace('engine.startGame({','Engine.load(GODOT_CONFIG.executable).then(() => engine.startGame({')
    needle="\t\t}).then(() => {\n\t\t\tsetStatusMode('hidden');";assert text.count(needle)==1
    text=text.replace(needle,"\t\t})).then(async () => {\n            const deadline=performance.now()+30000;\n            while(!window.HAS_STUDIO_READY){if(performance.now()>deadline)throw new Error('Studio did not finish starting.');await new Promise(r=>setTimeout(r,50));}\n            setStatusMode('hidden');\n            window.HAS_BOOT_READY=true;\n            if(parent!==window)parent.postMessage({type:'has:ready'},location.origin);")
    # A rejection thrown in the app-ready continuation also needs the same notice.
    text=text.replace('}, displayFailureNotice);','}).catch(displayFailureNotice);')
    needle='}());';assert text.count(needle)==1
    text=text.replace(needle,'''}());
} catch(error) {
  console.error(error);window.HAS_BOOT_ERROR=String(error);
  const status=document.getElementById('status'),notice=document.getElementById('status-notice'),progress=document.getElementById('status-progress');
  if(status)status.style.display='block';if(progress)progress.style.display='none';
  if(notice){notice.style.display='block';notice.textContent='Studio could not start. Try loading again.';}
  if(parent!==window)parent.postMessage({type:'has:error',message:'Studio could not start. Try loading again.'},location.origin);
}''')
    (public/'index.html').write_text(text)
    shutil.copy2(ROOT/'THIRD_PARTY_NOTICES.md',public/'THIRD_PARTY_NOTICES.txt')
    files=[{'path':str(source.relative_to(site)).replace('\\','/'),'bytes':source.stat().st_size,'sha256':sha(source)}for source in site.rglob('*')if source.is_file()]
    if any(row['bytes']>=25*1024*1024 for row in files):raise RuntimeError('A static file exceeds the25MiB handoff budget.')
    result={'folder':str(folder),'app':str(app),'public':str(public),'site_root':str(site),'godot':version,'template_sha256':sha(template),'source_files':sources,'files':files,'browser_tested':False,'release_ready':False,'deployed':False}
    (folder/'build.json').write_text(json.dumps(result,indent=2));(ROOT/'output/web-build-latest.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'folder':str(folder),'files':len(files),'bytes':sum(row['bytes']for row in files),'deployed':False}))

if __name__=='__main__':main()

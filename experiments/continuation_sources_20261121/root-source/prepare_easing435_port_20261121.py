"""Port exact reviewed anchors to published435 source; do not apply to Main."""
from pathlib import Path
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'output/source-keyframe-easing-editor-prep-20261121'
NEW=ROOT/'output/source-keyframe-easing435-port-prep-20261121'
REV='435dc02426a7cdd313e43fe674c9008520845428'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false',*args],cwd=ROOT)
assert not NEW.exists()
patches=json.loads((OLD/'PATCHES.json').read_bytes())['patches']
targets={}
for name in sorted({r['path'] for r in patches}):
    blob=git('show',REV+':'+name)
    assert (ROOT/name).read_bytes()==blob,'Main differs from immutable proposed baseline'
    result=blob
    for row in [p for p in patches if p['path']==name]:
        old=row['before'].encode();new=row['after'].encode()
        assert result.count(old)==1,'Missing/nonunique anchor '+name
        result=result.replace(old,new,1)
        row['base_sha256']=sha(blob)
    targets[name]=(result,blob)
NEW.mkdir()
for name,(result,base) in targets.items():
    target=NEW/'payload'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
    path=NEW/'bases'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base)
for name in ['src/keyframe_easing.gd','src/camera_easing_editor.gd','tests/keyframe_easing_math_unit.gd','tests/keyframe_easing_unit.gd']:
    path=NEW/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((OLD/'payload'/name).read_bytes())
result_source=ROOT.parent/'has-easing-headless-1795254145851799500/PUBLIC_RESULT.json'
result=json.loads(result_source.read_bytes())
assert result['status']=='PASS' and result['checks']==69 and result['application_adopted'] is False
(NEW/'ROOT_SYNTHETIC_RESULT.json').write_bytes(result_source.read_bytes())
(NEW/'ROOT_SYNTHETIC_HOST.py').write_bytes((ROOT/'output/run_easing_headless_20261121.py').read_bytes())
(NEW/'PATCHES.json').write_text(json.dumps({'format':'has_camera_easing435_source_port_1','baseline_revision':REV,
    'application_adopted':False,'patches':patches},indent=2)+'\n',encoding='utf-8')
(NEW/'README.md').write_text('''# Camera easing port to435dc024

Source-only proposal. The six exact original anchors apply uniquely to immutable435dc024 app and renderer blobs. Current Main and the canonical Full checkout are unchanged. Timeline remains byte-exact. Four standalone payload files are copied unchanged from the reviewed earlier editor preparation; old evidence is preserved separately.

Root actually ran24 math and45 editor transaction controls in an isolated headless six-file synthetic project. Both children exited0 and were reaped, every admitted source/runtime input and parent environment was preserved. The full raw result and exact host are retained. This is69 synthetic checks, not real app Undo, GUI, camera render/export or new Full evidence. The current canonical182-group Full is independently in progress.

The proposed editor stores a session-only Arrive/Leave recipe, offers recalculation and explicit Bake, preserves original key dictionaries and unrelated state, and refuses stale/busy contexts and over241-key plans. Preview changes no project keys or metadata. Bake produces ordinary integer-frame keys in one existing keys-history transaction. Smooth spatial arcs, body-neighbor coordination and actor-driven hair motion are separate.

Before adoption, qualify actual app setup in both themes/workspaces, keyed preview and discard, real Undo/Redo, save/open while recipe is active, authored capture/export bypass, baked preview/export agreement and source preservation. Check busy/motion guards against the current app; the headless spy cannot establish integration. Keep prior failures, skips and unrun conditions. No new runtime, download or native art is needed.
''',encoding='utf-8')
files=[]
for path in sorted(NEW.rglob('*')):
    if path.is_file():
        raw=path.read_bytes();files.append({'path':path.relative_to(NEW).as_posix(),'bytes':len(raw),'sha256':sha(raw)})
manifest={'format':'has_easing435_source_port_pins_1','baseline_revision':REV,'application_adopted':False,
 'real_app_integration_run':False,'synthetic_root_checks':69,'files':files,'file_count':len(files),
 'total_bytes':sum(r['bytes'] for r in files)}
(NEW/'SOURCE_PINS.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'FROZEN_SOURCE_PORT_NOT_ADOPTED','folder':str(NEW),'payload_files':len(files),
 'source_pins_sha256':sha((NEW/'SOURCE_PINS.json').read_bytes()),'root_synthetic_checks':69}))

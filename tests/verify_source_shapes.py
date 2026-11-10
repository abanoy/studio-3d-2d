"""Actual UI/default-shape/review/Undo/HAS/movie integration; hidden Windows GPU."""
from pathlib import Path
from native_fixture_root import fixture_output
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
from run import command
from test_helper_morphs import H, shape_fixture, write_glb


def prepare(folder):
    g = shape_fixture(folder / 'shape.glb')
    (folder / 'positions.json').write_text(json.dumps(g.shaped_skin(3, 1, {'source_morph_defaults': True})[4]), encoding='utf-8')
    g.doc['nodes'][3].pop('weights'); write_glb(folder / 'mesh-default.glb', g.doc, bytes(g.binary))
    g = H.GLB(folder / 'shape.glb'); g.doc['nodes'][3]['children'] = [4]
    g.doc['nodes'] += [{'name': 'Child'}, {'name': 'Surface', 'mesh': 0, 'skin': 0, 'weights': [.3, .9]}]
    g.doc['nodes'][0]['children'].append(5); write_glb(folder / 'shared.glb', g.doc, bytes(g.binary))
    late=H.GLB(folder/'shared.glb')
    for primitive in late.doc['meshes'][0]['primitives']:
        delta=late.accessor(primitive['targets'][0]['POSITION'],'VEC3')
        primitive['targets'][0]['POSITION']=late.append([tuple(v*5000 for v in p) for p in delta],'VEC3')
    write_glb(folder/'late-failure.glb',late.doc,bytes(late.binary))
    g.doc['nodes'] = [{'name': 'RootMesh', 'mesh': 0, 'weights': [.2, .4]}]
    g.doc['scenes'][0]['nodes'] = [0]; g.doc['skins'] = []; write_glb(folder / 'root.glb', g.doc, bytes(g.binary))
    g.doc['nodes'][0]['weights'] = [101., .4]; write_glb(folder / 'bad-default.glb', g.doc, bytes(g.binary))
    positions = [(-10.,0.,-15.), (10.,0.,-15.), (-10.,0.,10.), (10.,0.,10.)]
    attributes = {'POSITION': g.append(positions,'VEC3'), 'NORMAL': g.append([(0.,1.,0.)]*4,'VEC3')}
    g.doc['accessors'][attributes['POSITION']].update(min=[-10,0,-15],max=[10,0,10])
    g.doc['meshes'] = [{'weights':[1.], 'extras':{'targetNames':['Move map']}, 'primitives':[{'attributes':attributes,
        'indices':g.append([(v,) for v in (0,2,1,1,2,3)],'SCALAR',5123), 'material':0,
        'targets':[{'POSITION':g.append([(100.,4.,100.)]*4,'VEC3')}]}]}]
    g.doc['nodes'] = [{'name':'ShapedFloor','mesh':0}]
    g.doc['materials'] = [{'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[.4,.5,.6,1.], 'metallicFactor':0.}}]
    write_glb(folder / 'floor.glb',g.doc,bytes(g.binary))
    native_plans = []
    base = fixture_output()
    for label, relative in [('MMD','pose-smoke/miku-project'),('GMod','source-smoke/source-project'),('SFM','sfm-smoke/project')]:
        project = base / relative
        if not (project / 'project.json').is_file(): continue
        document = json.loads((project / 'project.json').read_text(encoding='utf-8'))
        row = document.get('model',{}) or document['world']['objects'][-1]
        path = project / row['path']; native = H.GLB(path)
        count = sum(bool(native.doc['meshes'][node['mesh']]['primitives'][0].get('targets')) for node in native.doc['nodes'] if 'mesh' in node)
        native_plans.append({'label':label,'source':str(path),'meshes':count,'metadata':row.get('metadata',{})})
    (folder / 'native-plans.json').write_text(json.dumps(native_plans),encoding='utf-8')
    originals = {p: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns) for p in folder.glob('*.glb')}
    for plan in native_plans:
        path = Path(plan['source']); originals[path] = (hashlib.sha256(path.read_bytes()).hexdigest(),path.stat().st_mtime_ns)
    return originals


def main():
    folder = ROOT / 'output/source-shapes' / str(time.time_ns()); folder.mkdir(parents=True)
    originals=prepare(folder)
    cmd = command('tests/source_shapes_smoke.gd', extra=['--', str(folder)])
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=170)
    log = p.stdout + p.stderr; (folder / 'engine.log').write_text(log, encoding='utf-8')
    if p.returncode or 'SOURCE_SHAPES ' not in log or any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']): raise RuntimeError(log)
    result = json.loads((folder / 'result.json').read_text(encoding='utf-8')); assert result['failures'] == 0
    for path, expected in originals.items(): assert (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns) == expected
    p = subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', result['movie']], capture_output=True, text=True, check=True)
    video = next(s for s in json.loads(p.stdout)['streams'] if s['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['nb_read_frames'], video['r_frame_rate']) == ('h264', 1920, 1080, '48', '24/1') and abs(float(video['duration'])-2)<.000001
    receipt = json.loads(Path(cmd[3]).read_text(encoding='utf-8'))
    assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['desktop_closed'] and receipt['job_closed']
    result.update(folder=str(folder), private_receipt=cmd[3])
    (ROOT / 'output/source-shapes-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8'); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

"""Explicit experimental shape-review snapshots; no automatic product defaults yet."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
from run import command
from test_helper_morphs import H, shape_fixture, request, write_glb


def main():
    subprocess.run([sys.executable, '-X', 'utf8', 'tests/test_helper_morphs.py'], cwd=ROOT, check=True)
    folder = ROOT / 'output/helper-morphs' / str(time.time_ns()); folder.mkdir(parents=True)
    source = folder / 'source.glb'; g = shape_fixture(source)
    cases = []
    for label, options in [('node-defaults', {'source_morph_defaults': True}),
                           ('signed-snapshot', {'morph_weights': {'3': [-.4, .6]}})]:
        plan = dict(request(g), **options)
        result = H.build(source, folder / (label + '-derived'), plan)
        cases.append({'name': label, 'source': str(source), 'derived': result['glb'],
                      'weights': g.morph_weights(3, plan), 'positions': [g.shaped_skin(3, i, plan)[4] for i in range(2)]})
    # A real sparse target with an implicit zero base, still rendered by Godot.
    primitive = g.doc['meshes'][0]['primitives'][1]; target = g.doc['accessors'][primitive['targets'][0]['POSITION']]
    target.pop('bufferView'); count = target['count']
    ids = g.append([(i,) for i in (2, 8, 18)], 'SCALAR', 5121)
    values = g.append([(.4, .1, .2), (.5, .2, .1), (.7, .1, .2)], 'VEC3')
    target['sparse'] = {'count': 3, 'indices': {'bufferView': g.doc['accessors'][ids]['bufferView'], 'componentType': 5121},
                        'values': {'bufferView': g.doc['accessors'][values]['bufferView']}}
    sparse = folder / 'sparse.glb'; write_glb(sparse, g.doc, bytes(g.binary)); sg = H.GLB(sparse)
    plan = dict(request(sg), source_morph_defaults=True); result = H.build(sparse, folder / 'sparse-derived', plan)
    cases.append({'name': 'sparse', 'source': str(sparse), 'derived': result['glb'], 'weights': sg.morph_weights(3, plan),
                  'positions': [sg.shaped_skin(3, i, plan)[4] for i in range(2)]})
    # Actual SFM Scout has520targets in one mesh. Exercise a high target index,
    # without increasing the active vertex-target operation budget.
    high = folder / 'many-targets.glb'; hg = shape_fixture(high)
    for primitive in hg.doc['meshes'][0]['primitives']: primitive['targets'] = [primitive['targets'][0]] * 520
    hg.doc['meshes'][0]['extras']['targetNames'] = ['Shape '+str(i) for i in range(520)]
    hg.doc['meshes'][0]['weights'] = [0.]*520; hg.doc['nodes'][3]['weights'] = [0.]*519+[.6]
    write_glb(high,hg.doc,bytes(hg.binary)); hg = H.GLB(high)
    plan = dict(request(hg),source_morph_defaults=True); result = H.build(high,folder/'many-targets-derived',plan)
    cases.append({'name':'many-targets','source':str(high),'derived':result['glb'],'weights':hg.morph_weights(3,plan),
                  'positions':[hg.shaped_skin(3,i,plan)[4] for i in range(2)]})
    originals = {c['source']: (hashlib.sha256(Path(c['source']).read_bytes()).hexdigest(), Path(c['source']).stat().st_mtime_ns) for c in cases}
    (folder / 'plan.json').write_text(json.dumps({'cases': cases}), encoding='utf-8')
    cmd = command('tests/helper_morphs_render.gd', extra=['--', str(folder)])
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=110)
    log = p.stdout + p.stderr; (folder / 'engine.log').write_text(log, encoding='utf-8')
    if p.returncode or 'HELPER_MORPHS ' not in log or any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']):
        raise RuntimeError(log)
    for path, expected in originals.items():
        assert (hashlib.sha256(Path(path).read_bytes()).hexdigest(), Path(path).stat().st_mtime_ns) == expected
    receipt = json.loads(Path(cmd[3]).read_text(encoding='utf-8'))
    assert receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
    result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
    result.update(folder=str(folder), receipt=cmd[3], product_integration=False)
    (ROOT / 'output/helper-morphs-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

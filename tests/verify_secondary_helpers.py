"""Backend generation + real weighted deformation/fan/Record/HAS/MP4 experiment."""
from pathlib import Path
import array
import hashlib
import json
import math
import subprocess
import sys
import time
import wave
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
from run import command
from test_secondary_helpers import fixture, request, mixed_fixture, two_panel_fixture, write_glb
import secondary_helpers as H


def native_checks(folder):
    plans = []; originals = {}; assessments = {}
    base = Path(r'C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output')
    # Explicit test regions exercise native bindings/skin, not a claim that these
    # automatically identified surfaces are physically loose clothing.
    for label, relative, name in [('mmd', 'pose-smoke/miku-project', 'Miku_Hatsune.pmd'),
                                  ('gmod', 'source-smoke/source-project', 'reimu_hakurei_bikini_ragdoll.mdl'),
                                  ('sfm', 'sfm-smoke/project', 'scout.mdl')]:
        project = base / relative
        if not (project / 'project.json').is_file():
            print('SKIP optional prepared native helper fixture: ' + label); continue
        document = json.loads((project / 'project.json').read_text(encoding='utf-8'))
        rows = document.get('world', {}).get('objects', []) or [document.get('model', {})]
        row = next(x for x in rows if x.get('name') == name); source = project / row['path']; g = H.GLB(source)
        originals[source] = (g.sha, source.stat().st_mtime_ns)
        assessment = H.inspect(source); assessments[label] = assessment
        candidates = [r for r in assessment['regions'] if r['suggested']]
        if label == 'sfm' or not candidates: continue
        chosen = next((r for r in candidates if 'ribbon' in r['anchor_name']), candidates[0])
        plan = {key: chosen[key] for key in ['node', 'primitive', 'component', 'anchor_node']}
        plan.update(source_sha256=g.sha, reviewed=True, segments=3)
        value = H.build(source, folder / (label + '-derived'), plan)
        plans.append({'label': label, 'source': str(source), 'sha256': g.sha, 'derived': value['glb'], 'report': value['report']})
    (folder / 'native-assessments.json').write_text(json.dumps(assessments, indent=2), encoding='utf-8')
    result = {'checks': 0, 'failures': 0, 'skipped': not bool(plans)}
    if plans:
        (folder / 'native-plans.json').write_text(json.dumps(plans), encoding='utf-8')
        p = subprocess.run(command('tests/secondary_helpers_native.gd', extra=['--', str(folder)]), cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=100)
        log = p.stdout + p.stderr; (folder / 'native.log').write_text(log, encoding='utf-8')
        if p.returncode or 'HELPER_NATIVE ' not in log or any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']): raise RuntimeError(log)
        result = json.loads((folder / 'native-result.json').read_text(encoding='utf-8')); assert result['failures'] == 0
    for source, before in originals.items():
        assert (hashlib.sha256(source.read_bytes()).hexdigest(), source.stat().st_mtime_ns) == before
    result['assessment_counts'] = {k: {'regions': len(v['regions']), 'suggested': sum(r['suggested'] for r in v['regions']), 'skipped': len(v['skipped']), 'truncated': v['truncated']} for k, v in assessments.items()}
    return result


def main():
    subprocess.run([sys.executable, '-X', 'utf8', 'tests/test_secondary_helpers.py'], cwd=ROOT, check=True)
    folder = ROOT / 'output' / 'secondary-helpers' / ('run_' + str(time.time_ns())); folder.mkdir(parents=True)
    original = folder / 'original.glb'; g = fixture(original); before = (original.read_bytes(), original.stat().st_mtime_ns)
    derived = H.build(original, folder / 'derived', request(g))
    mixed = folder / 'mixed.glb'; mixed_g = mixed_fixture(mixed); mixed_result = H.build(mixed, folder / 'mixed-derived', request(mixed_g))
    (folder / 'assessment.json').write_text(json.dumps(H.inspect(original), indent=2), encoding='utf-8')
    wav = folder / 'voice.wav'; samples = array.array('h', (int(16000 * math.sin(2 * math.pi * 1000 * n / 44100)) for n in range(22050)))
    if sys.byteorder != 'little': samples.byteswap()
    with wave.open(str(wav), 'wb') as f: f.setparams((1, 2, 44100, 0, 'NONE', 'not compressed')); f.writeframes(samples.tobytes())
    p = subprocess.run(command('tests/secondary_helpers_smoke.gd', extra=['--', str(original), derived['glb'], str(folder), str(wav), str(mixed), mixed_result['glb']]), cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=130)
    log = p.stdout + p.stderr; (ROOT / 'output/secondary-helpers-verification.log').write_text(log, encoding='utf-8')
    assert (original.read_bytes(), original.stat().st_mtime_ns) == before
    if p.returncode or 'SECONDARY_HELPERS ' not in log or any(s in log for s in ['SCRIPT ERROR', 'SHADER ERROR', 'FAIL ', 'ERROR:', 'ObjectDB instances leaked', '_set_transient_exclusive_child']): raise RuntimeError(log)
    result = json.loads((ROOT / 'output/secondary-helpers-result.json').read_text(encoding='utf-8')); assert result['failures'] == 0
    p = subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', result['movie']], capture_output=True, text=True, check=True)
    streams = json.loads(p.stdout)['streams']; video = next(s for s in streams if s['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['nb_read_frames'], video['r_frame_rate']) == ('h264', 1920, 1080, '48', '24/1')
    assert abs(float(video['duration']) - 2) < .000001 and any(s['codec_name'] == 'aac' for s in streams)
    decoded = folder / 'decoded.wav'; subprocess.run([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe', '-v', 'error', '-y', '-i', result['movie'], '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le', str(decoded)], check=True)
    with wave.open(str(decoded), 'rb') as f: pcm = array.array('h', f.readframes(f.getnframes()))
    if sys.byteorder != 'little': pcm.byteswap()
    onset = next((n / 48000 for n, value in enumerate(pcm) if abs(value) > 2000), None)
    assert onset is not None and abs(onset - 1) < .002, onset
    result['audio_onset_seconds'] = onset; result['video'] = {k: video[k] for k in ['codec_name', 'width', 'height', 'nb_read_frames', 'r_frame_rate', 'duration']}
    result['source_sha256'] = g.sha
    result['native'] = native_checks(folder)
    panel_paths = []
    for family in [None, 'v0', 'v1']:
        path = folder / ('panels-' + str(family) + '.glb'); two_panel_fixture(path, family); panel_paths.append(str(path))
    old = H.GLB(derived['glb']); old.doc['extensions'] = {'VRMC_springBone': old.doc.pop('extras')['has_secondary_helpers_1']}
    old_path = folder / 'older-generated-layout.glb'; write_glb(old_path, old.doc, bytes(old.binary))
    p = subprocess.run(command('tests/secondary_helpers_multi.gd', extra=['--', str(folder), *panel_paths, str(old_path)]), cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=125)
    log = p.stdout + p.stderr; (folder / 'multi.log').write_text(log, encoding='utf-8')
    if p.returncode or 'HELPER_MULTI ' not in log or any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']): raise RuntimeError(log)
    result['multi'] = json.loads((folder / 'multi-result.json').read_text(encoding='utf-8')); assert result['multi']['failures'] == 0
    for movie in result['multi']['movies']:
        p = subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', movie], capture_output=True, text=True, check=True)
        video = next(s for s in json.loads(p.stdout)['streams'] if s['codec_type'] == 'video')
        assert (video['codec_name'], video['width'], video['height'], video['nb_read_frames'], video['r_frame_rate'], float(video['duration'])) == ('h264',1920,1080,'48','24/1',2.0)
    p = subprocess.run(command('tests/secondary_helpers_patch.gd', extra=['--', str(original), str(folder), str(wav)]), cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=115)
    log = p.stdout + p.stderr; (folder / 'patch.log').write_text(log, encoding='utf-8')
    if p.returncode or 'HELPER_PATCH ' not in log or any(s in log for s in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked']): raise RuntimeError(log)
    result['patch'] = json.loads((folder / 'patch-result.json').read_text(encoding='utf-8')); assert result['patch']['failures'] == 0
    p = subprocess.run([r'C:\Program Files\ffmpeg\bin\ffprobe.exe','-v','error','-count_frames','-show_streams','-of','json',result['patch']['movie']],capture_output=True,text=True,check=True)
    streams = json.loads(p.stdout)['streams']; video = next(s for s in streams if s['codec_type']=='video')
    assert (video['codec_name'],video['width'],video['height'],video['nb_read_frames'],video['r_frame_rate'],float(video['duration']))==('h264',1920,1080,'48','24/1',2.0)
    assert any(s['codec_name']=='aac' for s in streams)
    patch_audio = folder / 'patch-decoded.wav'
    subprocess.run([r'C:\Program Files\ffmpeg\bin\ffmpeg.exe','-v','error','-y','-i',result['patch']['movie'],'-vn','-ac','1','-ar','48000','-c:a','pcm_s16le',str(patch_audio)],check=True)
    with wave.open(str(patch_audio),'rb') as f: patch_pcm=array.array('h',f.readframes(f.getnframes()))
    if sys.byteorder!='little': patch_pcm.byteswap()
    patch_onset=next((i/48000 for i,v in enumerate(patch_pcm) if abs(v)>2000),None)
    assert patch_onset is not None and abs(patch_onset-1)<.002,patch_onset
    result['patch']['audio_onset_seconds']=patch_onset
    (ROOT / 'output/secondary-helpers-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8'); print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

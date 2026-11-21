"""Focused authored-light UI, private GPU pixels, packed reopen and actual movie.
Uses only the approved Godot/Python/FFmpeg runtimes and run.command launcher.
Generated art, videos and receipts remain under ignored output/.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--forward-plus', action='store_true')
    parser.add_argument('--indirect', action='store_true', help='Focused SDFGI prototype; graphics use Forward+')
    parser.add_argument('--native-model', type=Path)
    parser.add_argument('--native-environment', type=Path)
    options = parser.parse_args()
    if options.indirect and not options.cpu:
        options.forward_plus = True
    script = 'tests/scene_indirect_smoke.gd' if options.indirect else 'tests/scene_lighting_smoke.gd'
    folder = ROOT / 'output' / (('scene-indirect-' if options.indirect else 'scene-lighting-') + str(time.time_ns()))
    folder.mkdir(parents=True)
    native = {kind: str(path.resolve(strict=True)) for kind, path in
              [('model', options.native_model), ('environment', options.native_environment)] if path}
    if native:
        (folder / 'native-inputs.json').write_text(json.dumps(native), encoding='utf-8')
    preserved = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in native.values()}
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    for key, child in [('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local'), ('USERPROFILE', 'User')]:
        env[key] = str(folder / child)
        Path(env[key]).mkdir()
    if not options.cpu and os.name != 'nt':
        raise RuntimeError('This focused graphics runner requires the existing Windows private desktop launcher.')
    frozen = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / 'src').glob('*') if p.is_file()}
    results, receipts = [], []
    for phase in ['writer', 'reader']:
        if phase == 'reader' and options.cpu:
            from tools.has_project import pack, unpack, members
            for theme in ['neon', 'light']:
                snapshot = folder / (theme + '-snapshot')
                manifest = json.loads((snapshot / 'project.json').read_bytes())
                assets, _ = members(manifest)
                references = {name: str(snapshot / name) for name in assets}
                for storage in ['packed', 'linked']:
                    archive = folder / (theme + '-' + storage + '.has')
                    saved = pack({'folder': str(snapshot), 'path': str(archive), 'storage': storage,
                                  'references': references, 'cache_root': str(folder / 'cache')})
                    assert saved['ok'], saved
                    opened = unpack({'path': str(archive), 'folder': str(folder / (theme + '-' + storage + '-unpacked'))})
                    assert opened['ok'], opened
        args = command(script, headless=options.cpu,
                       extra= (['--rendering-method', 'forward_plus'] if options.forward_plus else []) + ['--audio-driver', 'Dummy', '--log-file', str(folder / (phase + '-engine.log')),
                              '--', str(folder), *(['--cpu'] if options.cpu else []),
                              *(['--read'] if phase == 'reader' else [])])
        result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=270)
        log = result.stdout + result.stderr
        (folder / (phase + '-launcher.log')).write_text(log, encoding='utf-8')
        engine_log = (folder / (phase + '-engine.log')).read_text(encoding='utf-8') if (folder / (phase + '-engine.log')).exists() else ''
        receipt = None
        if not options.cpu:
            receipt_path = Path(args[args.index('--receipt') + 1])
            receipt = json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else {'error': 'No private desktop receipt'}
            (folder / (phase + '-desktop.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(log, flush=True)
        if result.returncode or 'SCENE_LIGHTING ' not in log + engine_log or any(bad in log + engine_log for bad in ['SCRIPT ERROR', 'SHADER ERROR', 'FAIL ', 'ObjectDB instances leaked', 'ERROR:']):
            raise RuntimeError(f'{phase} failed; evidence: {folder}\n{receipt or ""}\n{engine_log[-12000:]}')
        report = json.loads((folder / (phase + '-result.json')).read_text(encoding='utf-8'))
        assert report['failures'] == 0
        results.append(report)
        if not options.cpu:
            assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
            receipts.append({'path': str(receipt_path), 'receipt': receipt})
    video = None
    if not options.cpu:
        movie = results[0]['measurements']['movie']
        ffmpeg = Path(os.environ.get('HYBRID_FFMPEG', 'C:/Program Files/ffmpeg/bin/ffmpeg.exe'))
        probe = json.loads(subprocess.check_output([str(ffmpeg.with_name('ffprobe.exe')), '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', movie], text=True))
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == ('h264', 1920, 1080, '24/1', '4' if options.indirect else '48')
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in frozen.items())
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in preserved.items())
    result = {'results': results, 'private_desktops': receipts, 'video': video, 'source_sha256': frozen, 'folder': str(folder)}
    (folder / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'checks': sum(x['checks'] for x in results), 'failures': 0, 'graphics': not options.cpu, 'folder': str(folder)}, indent=2))

if __name__ == '__main__':
    main()

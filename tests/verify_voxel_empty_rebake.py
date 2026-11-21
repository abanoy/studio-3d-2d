"""Focused headless regression for empty room bounds after a successful bake."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--graphics', action='store_true', help='Use the existing Windows private desktop and verify real export refusal/recovery')
options = parser.parse_args()
if options.graphics and os.name != 'nt':
    raise RuntimeError('Graphics checks require the existing Windows private-desktop launcher.')

folder = ROOT / 'output' / ('voxel-empty-rebake-' + str(time.time_ns()))
folder.mkdir(parents=True)
names = ['src/scene_voxel_runtime.gd', 'tests/scene_voxel_empty_rebake.gd',
         'tests/scene_voxel_smoke.gd', 'tests/verify_voxel_empty_rebake.py']
hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
for key, part in [('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local'), ('USERPROFILE', 'User')]:
    env[key] = str(folder / part)
    Path(env[key]).mkdir()
args = command('tests/scene_voxel_empty_rebake.gd', headless=not options.graphics,
               extra=(['--rendering-method', 'forward_plus'] if options.graphics else []) +
                     ['--audio-driver', 'Dummy', '--log-file', str(folder / 'engine.log'),
                      '--', str(folder), *([] if options.graphics else ['--cpu'])])
result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
log = result.stdout + result.stderr
(folder / 'launcher.log').write_text(log, encoding='utf-8')
print(log, flush=True)
assert result.returncode == 0, folder
assert not any(token in log for token in ['SCRIPT ERROR', 'ERROR:', 'FAIL ', 'ObjectDB instances leaked']), folder
report = json.loads((folder / 'writer-result.json').read_bytes())
assert report['checks'] == (22 if options.graphics else 18) and report['failures'] == 0
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
receipt = {'checks': report['checks'], 'failures': 0, 'graphics': options.graphics, 'source_sha256': hashes, 'folder': str(folder)}
if options.graphics:
    desktop = json.loads(Path(args[args.index('--receipt') + 1]).read_bytes())
    assert desktop['exit'] == 0 and desktop['child_desktop_confirmed'] and not desktop['foreground_child_observed'] and desktop['job_closed'] and desktop['desktop_closed']
    receipt['private_desktop'] = desktop
    ffprobe = Path(os.environ.get('HYBRID_FFMPEG', 'C:/Program Files/ffmpeg/bin/ffmpeg.exe')).with_name('ffprobe.exe')
    receipt['videos'] = {}
    for theme, movie in report['measurements'].items():
        probe = json.loads(subprocess.check_output([str(ffprobe), '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', movie], text=True))
        video = next(item for item in probe['streams'] if item['codec_type'] == 'video')
        assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == ('h264', 1920, 1080, '24/1', '2')
        receipt['videos'][theme] = video
(folder / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))

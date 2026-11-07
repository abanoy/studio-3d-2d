"""Bounded saved walking: domain, private app, cold packed Open, recovery and MP4."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command, configure_private_display


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--isolated-display', help='Linux: explicitly provisioned private X display')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bend', action='store_true', help='Exercise a flat two-segment bend')
    parser.add_argument('--turn', action='store_true', help='Include smooth authored yaw keys')
    options = parser.parse_args()
    if os.name != 'nt':
        if sys.platform != 'linux' or not options.isolated_display:
            parser.error('Linux requires --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    folder = (options.output or ROOT / 'output/walking-path' / str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    frozen = {p: digest(p) for name in ['src', 'tests', 'tools', 'data', 'examples']
              for p in (ROOT / name).rglob('*')
              if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts}
    reports = {}
    receipts = []

    def execute(label, script, marker, headless=False, extra=()):
        args = command('tests/' + script + '.gd', headless=headless,
                       extra=(['--audio-driver', 'Dummy'] if not headless and os.name != 'nt' else [])
                       + ['--log-file', str(folder / (label + '-engine.log')), '--', str(folder), *extra])
        process = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                 encoding='utf-8', errors='replace', timeout=245 if not headless else 60)
        log = process.stdout + process.stderr
        (folder / (label + '.log')).write_text(log, encoding='utf-8')
        assert process.returncode == 0 and marker in log and not any(
            token in log for token in ['ERROR:', 'FAIL ', 'ObjectDB instances leaked', 'another exclusive child']), log
        report = json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)))
        assert report['failures'] == 0 and report['checks'] > 0, report
        reports[label] = report
        if os.name == 'nt' and not headless:
            receipt = Path(args[args.index('--receipt') + 1])
            evidence = json.loads(receipt.read_bytes())
            assert evidence['exit'] == 0 and evidence['child_desktop_confirmed'] and not evidence['foreground_child_observed'] and evidence['job_closed'] and evidence['desktop_closed'], evidence
            receipts.append(str(receipt))
        print(label + ': PASS', flush=True)

    execute('evaluator', 'path_locomotion_unit', 'PATH_LOCOMOTION_UNIT ', True)
    evaluator = json.loads((folder / 'verification.json').read_bytes())
    assert evaluator['samples'] == 97 and evaluator['maximum_foot_error'] < .0002
    execute('settings', 'walking_animation_unit', 'WALKING_ANIMATION_UNIT ', True)
    mode = (['--bend'] if options.bend else []) + (['--turn'] if options.turn else [])
    execute('writer', 'walking_path_smoke', 'WALKING_PATH_SMOKE ', extra=mode)
    packed = folder / 'Walking.has'
    packed_sha = digest(packed)
    source = folder / 'source-figure.glb'
    source_sha = digest(source)
    originals = [source, folder / 'writer-cache']
    moved = []
    try:
        for path in originals:
            offline = path.with_name(path.name + '.offline')
            assert not offline.exists()
            path.rename(offline)
            moved.append((path, offline))
        execute('reader', 'walking_path_smoke', 'WALKING_PATH_READ ', extra=['--read', *mode])
    finally:
        for path, offline in reversed(moved):
            offline.rename(path)
    assert digest(packed) == packed_sha and digest(source) == source_sha
    probe = str(Path(os.environ.get('HYBRID_FFMPEG', 'ffmpeg')).with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe'))
    media = json.loads(subprocess.check_output(
        [probe, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', reports['writer']['movie']],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))
    video = next(stream for stream in media['streams'] if stream['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['nb_read_frames'], video['r_frame_rate']) == ('h264', 1920, 1080, '48', '24/1'), video
    assert abs(float(media['format']['duration']) - 2) < .001
    assert all(digest(path) == expected for path, expected in frozen.items())
    result = dict(folder=str(folder), reports=reports, evaluator=evaluator, bending_route=options.bend, authored_turn=options.turn,
                  video=video, private_receipts=receipts, isolated_display=options.isolated_display,
                  manual_has_unchanged=True, original_source_unchanged=True,
                  original_and_writer_cache_offline_for_reader=True,
                  cold_reader_uses_new_packed_asset_cache=True, functional_unchanged=True,
                  native_fixtures=0, source_sha256={str(p.relative_to(ROOT)): sha for p, sha in frozen.items()})
    (folder / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()

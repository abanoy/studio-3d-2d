"""Exact native freeform scenario A, private GUI, portable cold replay and MP4."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command, configure_private_display


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True, help='Original self-contained VRM humanoid; read only')
    parser.add_argument('--isolated-display', help='Linux requires an explicitly private X display')
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if os.name != 'nt':
        if sys.platform != 'linux' or not options.isolated_display:
            parser.error('Linux requires a private --isolated-display; no shared-desktop fallback')
        configure_private_display(options.isolated_display)
    source = options.native.resolve(strict=True)
    if source.suffix.lower() != '.vrm' or source.stat().st_size > 128 * 1024 * 1024:
        parser.error('--native requires a self-contained VRM within the existing 128 MiB limit')
    original = (digest(source), source.stat().st_mtime_ns)
    folder = (options.output or ROOT / 'output/scenario-a' / str(time.time_ns())).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    inputs = folder / 'inputs'; inputs.mkdir()
    staged = inputs / source.name; shutil.copy2(source, staged)
    frozen = {p: digest(p) for part in ('src', 'tests', 'tools') for p in (ROOT / part).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    reports = {}; receipts = []

    def launch(label, flags):
        argv = command('tests/scenario_a_smoke.gd', extra=['--audio-driver', 'Dummy', '--log-file',
                       str(folder / (label + '-engine.log')), '--', str(folder), *flags])
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=250)
        log = result.stdout + result.stderr
        (folder / (label + '.log')).write_text(log, encoding='utf-8')
        assert result.returncode == 0 and not any(x in log for x in ('ERROR:', 'FAIL ', 'ObjectDB instances leaked')), log
        marker = 'SCENARIO_A '
        reports[label] = json.loads(next(line[len(marker):] for line in log.splitlines() if line.startswith(marker)))
        assert reports[label]['failures'] == 0
        if os.name == 'nt':
            path = Path(argv[argv.index('--receipt') + 1]); receipt = json.loads(path.read_bytes())
            assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed']
            assert receipt['job_closed'] and receipt['desktop_closed']; receipts.append(str(path))

    started = time.time_ns()
    launch('writer', [str(staged)])
    expected = json.loads((folder / 'expected.json').read_bytes())
    project = folder / 'Freeform animation.has'; project_hash = digest(project)
    with zipfile.ZipFile(project) as archive:
        manifest = json.loads(archive.read('project.json'))
    assert manifest['world'] == expected['world'] and manifest['camera_keys'] == expected['camera']
    conversion = Path(reports['writer']['conversion_folder']).resolve(strict=True)
    assert conversion.is_relative_to((ROOT / 'output/compatibility').resolve())
    assert conversion.stat().st_mtime_ns >= started
    parameters = json.loads((conversion / 'parameters.json').read_bytes())
    assert parameters['kind'] == 'vrm_preparation' and parameters['source_sha256'] == original[0]
    moved = []
    try:
        for path in (inputs, conversion, folder / 'writer-cache'):
            offline = path.with_name(path.name + '.offline')
            assert not offline.exists(); path.rename(offline); moved.append((path, offline))
        launch('reader', ['--read'])
    finally:
        for path, offline in reversed(moved):
            offline.rename(path)
    assert digest(project) == project_hash
    assert (digest(source), source.stat().st_mtime_ns) == original
    assert digest(staged) == original[0] and all(digest(p) == value for p, value in frozen.items())
    encoder = os.environ.get('HYBRID_FFMPEG', 'ffmpeg')
    probe = str(Path(encoder).with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe'))
    flags = dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    media = json.loads(subprocess.check_output([probe, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                       '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames', '-of', 'json',
                       reports['writer']['movie']], **flags))['streams'][0]
    assert (media['codec_name'], media['width'], media['height'], media['r_frame_rate'], media['nb_read_frames']) == ('h264', 1920, 1080, '24/1', '24')
    proof = dict(reports=reports, video=media, original_sha256=original[0], original_unchanged=True,
                 packed_decimal_values_exact=True, conversion_inputs_writer_cache_offline_for_reader=True,
                 manual_has_unchanged=True, private_receipts=receipts, isolated_display=options.isolated_display,
                 scope='Eight software steps on supplied VRM; no five-minute novice, Windows or physical-device certification.')
    (folder / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()

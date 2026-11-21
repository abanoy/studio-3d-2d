"""Focused real-app checks for camera easing and automatic posed bounds.

Uses generated fixtures/repository samples and the existing private desktop
launcher. No owner assets are required. Run after the feature batch is usable.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command, configure_private_display


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--isolated-display')
    parser.add_argument('--classic', action='store_true')
    parser.add_argument('--advanced', action='store_true')
    parser.add_argument('--movies', action='store_true', help='Also render and inspect two easing movies')
    parser.add_argument('--native-snapshot', type=Path, help='Optional privately prepared six-part Junko directory')
    parser.add_argument('--group', choices=['all', 'easing', 'bounds', 'parts', 'native_parts'], default='all')
    options = parser.parse_args()
    if options.group == 'native_parts' and not options.native_snapshot:
        parser.error('The native group requires --native-snapshot')
    if os.name != 'nt':
        if not options.isolated_display:
            parser.error('An explicit private display is required')
        configure_private_display(options.isolated_display)
    folder = (options.output or ROOT / 'output' / ('feature-additions-' + str(time.time_ns()))).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    result = {'status': 'RUNNING', 'groups': {}, 'private_receipts': []}
    try:
        for group, script, markers, counts in [
            ('easing', 'tests/easing_c315_graphical_smoke.gd',
             ['EASING_C315_GRAPHICS ', 'EASING_C315_GRAPHICS_READ '], [23, 8]),
            ('bounds', 'tests/posed_bounds_app_gui.gd',
             ['POSED_BOUNDS_GUI ', 'POSED_BOUNDS_GUI_READ '], [12, 8]),
            ('parts', 'tests/character_parts_gui.gd',
             ['CHARACTER_PARTS_GUI ', 'CHARACTER_PARTS_GUI_READ '], [12, 6]),
            ('native_parts', 'tests/character_parts_native_gui.gd',
             ['CHARACTER_PARTS_NATIVE_GUI ', 'CHARACTER_PARTS_NATIVE_GUI_READ '], [9, 6]),
        ]:
            if options.group not in ['all', group]:
                continue
            if group == 'native_parts' and not options.native_snapshot:
                continue
            data = folder / group
            data.mkdir()
            result['groups'][group] = {}
            for index, label in enumerate(['writer', 'reader']):
                extra = ['--', str(data)]
                if group == 'native_parts':
                    extra = ['--', str(options.native_snapshot.resolve(strict=True)), str(data)]
                if index:
                    extra.append('--read')
                if options.classic:
                    extra.append('--classic')
                if options.advanced:
                    extra.append('--advanced')
                if options.movies and group == 'easing' and not index:
                    extra.append('--movies')
                engine_log = data / (label + '-engine.log')
                args = command(script, extra=['--log-file', str(engine_log), *extra])
                process = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=260,
                                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                raw = process.stdout + process.stderr
                (data / (label + '.log')).write_bytes(raw)
                text = raw.decode('utf-8', errors='replace')
                engine_text = engine_log.read_text(encoding='utf-8', errors='replace') if engine_log.is_file() else ''
                if os.name == 'nt':
                    receipt_path = Path(args[args.index('--receipt') + 1])
                    receipt = json.loads(receipt_path.read_bytes())
                    result['private_receipts'].append(receipt)
                    assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'], text + engine_text
                    assert receipt['private_window_seen'] and not receipt['desktop_switch_requested']
                    assert not receipt['foreground_child_observed'] and receipt['job_closed'] and receipt['desktop_closed']
                assert process.returncode == 0, text
                assert not any(error in text or error in engine_text for error in
                               ['SCRIPT ERROR', 'SHADER ERROR', 'ERROR:', 'FAIL ', 'ObjectDB instances leaked']), text + engine_text
                lines = [line for line in text.splitlines() if line.startswith(markers[index])]
                if not lines:
                    lines = [line for line in engine_text.splitlines() if line.startswith(markers[index])]
                assert len(lines) == 1, text + engine_text
                line = lines[0]
                report = json.loads(line[len(markers[index]):])
                expected_count = counts[index] + (6 if options.movies and group == 'easing' and not index else 0)
                assert report['failures'] == 0 and report['checks'] == expected_count, report
                if options.movies and group == 'easing' and not index:
                    encoder = os.environ.get('HYBRID_FFMPEG') or shutil.which('ffmpeg')
                    assert encoder, 'Movie inspection needs the existing FFmpeg tools'
                    probe = Path(encoder).with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
                    reports = []
                    for movie in report['movies']:
                        inspection = subprocess.run([str(probe), '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', movie],
                                                    capture_output=True, check=True, timeout=30,
                                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        streams = json.loads(inspection.stdout)['streams']
                        video = next(stream for stream in streams if stream['codec_type'] == 'video')
                        assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == ('h264', 1920, 1080, '24/1', '48')
                        assert abs(float(video['duration']) - 2.0) < .001
                        reports.append({key: video[key] for key in ['codec_name', 'width', 'height', 'r_frame_rate', 'nb_read_frames', 'duration']})
                    assert len(reports) == 2
                    report['inspected_movies'] = reports
                result['groups'][group][label] = report
                print(group, label, report['checks'], 'passed', flush=True)
        result['status'] = 'PASS'
    except BaseException as error:
        result['status'] = 'FAIL'
        result['error'] = str(error)
        raise
    finally:
        (folder / 'verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(str(folder), flush=True)


if __name__ == '__main__':
    main()

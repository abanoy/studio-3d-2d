"""Real private-desktop reference-size workflow, cold HAS and movie agreement."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

BAD = (b'SCRIPT ERROR', b'SHADER ERROR', b'ERROR:', b'FAIL ', b'ObjectDB instances leaked')


def snapshot():
    files = [path for name in ('src', 'tests', 'tools', 'data', 'examples')
             for path in (ROOT / name).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    files += [ROOT / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def invoke(folder, reader=False):
    args = command('tests/human_reference_smoke.gd', extra=['--', str(folder), *(['reader'] if reader else [])])
    process = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=230,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    log = process.stdout + process.stderr
    name = 'reader' if reader else 'writer'
    (folder / (name + '.log')).write_bytes(log)
    (folder / (name + '-command.json')).write_text(json.dumps({'args': args, 'exit': process.returncode}), encoding='utf-8')
    assert process.returncode == 0 and b'HUMAN_REFERENCE ' in log and not any(x in log for x in BAD), log[-6000:]
    result = json.loads((folder / ('result-reader.json' if reader else 'result.json')).read_bytes())
    assert result['failures'] == 0 and result['checks'] == (3 if reader else 44), result
    receipt_path = Path(args[args.index('--receipt') + 1])
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'], receipt
    assert not receipt['desktop_switch_requested'] and receipt['job_closed'] and receipt['desktop_closed'], receipt
    result['private_receipt'] = str(receipt_path)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=('neon', 'light'), default='neon')
    options = parser.parse_args()
    folder = ROOT / 'output' / 'human-reference' / (options.theme + '-' + str(time.time_ns()))
    folder.mkdir(parents=True)
    (folder / 'display.cfg').write_text('[display]\ntheme="' + options.theme + '"\npercent=100\n', encoding='utf-8')
    before = snapshot()
    writer = invoke(folder)
    reader = invoke(folder, True)
    assert snapshot() == before, 'Functional source changed during reference checks'
    movies = list(folder.glob('export-*/movie.mp4'))
    # The application chooses its ordinary export directory; validate from the
    # test's actual export marker when its folder has a different prefix.
    if not movies:
        movies = list(folder.rglob('movie.mp4'))
    assert len(movies) == 1, movies
    probe = json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe', '-v', 'error',
        '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(movies[0])]))
    video = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == ('h264', 1920, 1080, '24/1', '48')
    assert abs(float(probe['format']['duration']) - 2) < .001
    result = {'theme': options.theme, 'writer': writer, 'cold_reader': reader,
              'functional_files_unchanged': len(before), 'movie': str(movies[0]), 'folder': str(folder)}
    (ROOT / 'output' / ('human-reference-' + options.theme + '-verification.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

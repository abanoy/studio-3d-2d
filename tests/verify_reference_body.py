"""Private GPU reference-size body workflow, cold packed replay and rational MP4."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command

BAD = (b'SCRIPT ERROR', b'SHADER ERROR', b'ERROR:', b'FAIL ', b'ObjectDB instances leaked')
EXPECTED_CHECKS = {'writer': 72, 'reader': 21, 'parent-writer': 18, 'parent-reader': 6}


def snapshot():
    files = [path for name in ('src', 'tests', 'tools', 'data', 'examples')
             for path in (ROOT / name).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts]
    files += [ROOT / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def invoke(folder, reader=False, parent=False):
    name = 'reader' if reader else 'writer'
    suite_name = 'parent-' + name if parent else name
    script = 'tests/reference_body_parent_smoke.gd' if parent else 'tests/reference_body_smoke.gd'
    args = command(script, extra=['--', str(folder), *(['reader'] if reader else [])])
    process = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=290,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    log = process.stdout + process.stderr
    (folder / (name + '.log')).write_bytes(log)
    (folder / (name + '-command.json')).write_text(json.dumps({'args': args, 'exit': process.returncode}), encoding='utf-8')
    marker = b'REFERENCE_BODY_PARENT ' if parent else b'REFERENCE_BODY_WORKFLOW '
    assert process.returncode == 0 and marker in log and not any(x in log for x in BAD), log[-10000:]
    result = json.loads((folder / ('result-reader.json' if reader else 'result.json')).read_bytes())
    assert result['failures'] == 0 and result['checks'] == EXPECTED_CHECKS[suite_name], result
    if parent:
        assert Path(result['metrics']['project_root']).resolve() == ROOT.resolve(), result
    else:
        assert len(result['labels']) == len(set(result['labels'])) == EXPECTED_CHECKS[suite_name], result
    receipt_path = Path(args[args.index('--receipt') + 1])
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt['exit'] == 0 and receipt['child_desktop_confirmed'] and not receipt['foreground_child_observed'], receipt
    assert not receipt['desktop_switch_requested'] and receipt['job_closed'] and receipt['desktop_closed'], receipt
    result['private_receipt'] = str(receipt_path)
    return result


def verify_packed_authored_data(folder):
    """Check persisted authoring independently of Godot's numeric JSON decoder."""
    expected = json.loads((folder / 'expected.json').read_bytes())
    cases = []
    for item in expected['projects']:
        path = folder / (item['name'] + '.has')
        with zipfile.ZipFile(path) as archive:
            document = json.loads(archive.read('project.json'))
            rows = [row for row in document['world']['objects'] if row['id'] == item['id']]
            assert len(rows) == 1, (path, item['id'], len(rows))
            # source is an absolute managed input; path is its portable archive
            # location. No numeric field, provenance or authored channel is omitted.
            portable = lambda row: {key: value for key, value in row.items() if key not in ('source', 'path')}
            assert portable(rows[0]) == portable(item['definition']), ('Packed authored data differs', path)
            asset = archive.read(rows[0]['path'])
            assert hashlib.sha256(asset).hexdigest() == item['definition']['sha256'], path
        cases.append({'project': str(path), 'id': item['id'],
                      'exact_authored_data_except_source_path': True,
                      'embedded_source_sha256': item['definition']['sha256']})
    assert len(cases) == 4, cases
    report = {'cases': cases, 'numeric_tolerance_used': False,
              'scope': 'Complete persisted model definitions; only source/path location fields differ.'}
    (folder / 'packed-authored-data-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=('neon', 'light'), default='neon')
    options = parser.parse_args()
    folder = ROOT / 'output' / 'reference-body' / (options.theme + '-' + str(time.time_ns()))
    folder.mkdir(parents=True)
    (folder / 'display.cfg').write_text('[display]\ntheme="' + options.theme + '"\npercent=100\n', encoding='utf-8')
    before = snapshot()
    writer = invoke(folder)
    packed_authored_data = verify_packed_authored_data(folder)
    reader = invoke(folder, True)
    parent_folder = folder / 'parent'
    parent_folder.mkdir()
    (parent_folder / 'display.cfg').write_text('[display]\ntheme="' + options.theme + '"\npercent=100\n', encoding='utf-8')
    parent_writer = invoke(parent_folder, parent=True)
    parent_reader = invoke(parent_folder, reader=True, parent=True)
    assert snapshot() == before, 'Functional source changed during reference body checks'
    assert writer['projects'] == 4 and set(writer['metrics']) == {'0.5', '1.0', '2.0'}, writer
    movie = Path(writer['movie'])
    assert movie.is_file() and movie.is_relative_to(folder), movie
    probe = json.loads(subprocess.check_output([r'C:\Program Files\ffmpeg\bin\ffprobe.exe', '-v', 'error',
        '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(movie)]))
    video = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    assert (video['codec_name'], video['width'], video['height'], video['r_frame_rate'], video['nb_read_frames']) == ('h264', 1920, 1080, '25/2', '12'), video
    assert abs(float(probe['format']['duration']) - .96) < .001, probe
    result = {'theme': options.theme, 'writer': writer, 'cold_reader': reader,
              'parent_writer': parent_writer, 'parent_cold_reader': parent_reader,
              'packed_authored_data': packed_authored_data,
              'functional_files_unchanged': len(before), 'movie': str(movie), 'folder': str(folder)}
    (ROOT / 'output' / ('reference-body-' + options.theme + '-verification.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

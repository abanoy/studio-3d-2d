"""ROOT later: read-only exact runtime stamp evidence; never grants admission."""
import argparse, datetime, hashlib, json, os, stat
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
READER = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
READER_SHA = '5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'
FIELDS = ('dev', 'ino', 'size', 'mtime_ns', 'nlink', 'file_attributes')


def need(condition, detail):
    if not condition:
        raise RuntimeError(detail)

def no_links(path):
    for item in (path, *path.parents):
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Reparse or symlink refused: ' + str(item))

def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink,
            getattr(info, 'st_file_attributes', 0))

def observe(path, approved, single_link=False):
    failure = None
    try:
        no_links(path)
        before = path.lstat()
        need(stat.S_ISREG(before.st_mode), 'Regular protected file required')
        need(not single_link or before.st_nlink == 1, 'Original must remain single-link')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = os.fstat(stream.fileno())
        final = path.lstat()
        need(all(stamp(value) == stamp(before) for value in (opened, after, final)),
             'Protected file changed during read: ' + str(path))
    except Exception as error:
        failure = type(error).__name__
    captured = locals()
    phases = {name: dict(zip(FIELDS, stamp(captured[name])))
              for name in ('before', 'opened', 'after', 'final') if name in captured}
    differences = {name: {field: {'before': phases['before'][field], 'observed': value}
                          for field, value in row.items() if value != phases['before'][field]}
                   for name, row in phases.items() if name != 'before'} if 'before' in phases else {}
    actual = ({'bytes': final.st_size, 'mtime_ns': final.st_mtime_ns, 'sha256': digest}
              if 'final' in captured and 'digest' in captured else None)
    return {'path': str(path), 'approved': approved, 'actual_identity': actual,
            'original_read_guard_passed': failure is None, 'read_error_type': failure,
            'exact_approved_identity': actual == approved, 'phases': phases, 'stamp_differences': differences}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    args = parser.parse_args()
    need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == args.source_sha256, 'Probe source changed')
    need(hashlib.sha256(READER.read_bytes()).hexdigest() == READER_SHA, 'Original reader changed')
    raw = LOCK.read_bytes(); need(hashlib.sha256(raw).hexdigest() == LOCK_SHA, 'Approved lock changed')
    approved = json.loads(raw)['runtime_executables']; need(len(approved) == 6, 'Exact six runtimes required')
    output = args.output.absolute(); no_links(output.parent)
    need(output.parent == ROOT / 'output' and output.suffix == '.json' and not output.exists(), 'Fresh direct ROOT/output JSON required')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = [observe(Path(name), expected) for name, expected in approved.items()]
    result = {'format': 'has_readonly_runtime_exact_stamp_probe_1', 'started_utc': started,
              'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'probe_sha256': args.source_sha256, 'reader_sha256': READER_SHA, 'lock_sha256': LOCK_SHA,
              'runtime_count': len(rows), 'rows': rows,
              'all6_approved_and_stable': all(row['original_read_guard_passed'] and row['exact_approved_identity'] for row in rows),
              'admission_authority': False, 'runtime_native_or_process_invoked': False,
              'runtime_files_or_pins_modified': False}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, separators=(',', ':'), allow_nan=False); stream.write('\n')
    print(json.dumps({'metadata_output': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                      'all6_approved_and_stable': result['all6_approved_and_stable'], 'admission_authority': False}))
    return 0


if __name__ == '__main__': raise SystemExit(main())

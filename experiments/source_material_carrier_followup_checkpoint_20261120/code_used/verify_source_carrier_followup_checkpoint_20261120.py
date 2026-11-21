"""Root-only publication candidate; author did not execute it.

Restore/run from ROOT/output after the exclusive native job has closed.
Only two explicit public packets and the seven named docs can enter this checkpoint.
No model input, native application, conversion or cleanup is performed here.
"""
from pathlib import Path, PurePosixPath
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = 'ffed3fc2fe4f078a4c6cd506c5c757b7f46db82b'
PROTECTED_OUTPUT_BASELINE_REVISION = '5f6a0efba5205f2b1ad4dda73271d968993db4c7'
PACKETS = ('source_material_carrier_followup_20261120', 'source_material_carrier_followup_checkpoint_20261120')
DOCS = ('LLM.md', 'docs/NEXT_SESSION_PLAN_2026-11-20.md',
        'docs/RESUME_MASTER_PLAN.md', 'docs/benchmarks/reference_body_2026-11-20.json',
        'docs/completion_checklist.json', 'docs/completion_checklist.md',
        'docs/progress_memo.md')
PROTECTED_OUTPUT_BASELINE = 'experiments/source_material_carrier_checkpoint_20261120/evidence/source-carrier-preserved-tracked-output-baseline-20261120.json'
PROTECTED_OUTPUT_BASELINE_SHA256 = 'c40dfc182df6907acf1be74f46f49441e0c2a5f1ee388bb3a4e0c246f1b448e3'
SOURCE_AFTER = 'experiments/reference_body_full_20261120/source-after.json'
PUBLIC_SUFFIXES = {'.py', '.md', '.json', '.log', '.js', '.ps1', '.txt'}
PRIVATE_NAMES = {'carrier.glb', 'private_primitive_ids.json', 'root_carrier_export_request.json'}
MAX_PUBLIC_FILE = 16 * 1024 * 1024


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.autocrlf=false', *args], cwd=ROOT,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    value = {}
    for key, item in items:
        assert key not in value, 'Duplicate JSON key'
        value[key] = item
    return value


def parse(raw):
    def nonfinite(_value):
        raise ValueError('Nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def stamp(info):
    # The reviewed Windows directory-enumeration recall hint can clear on open.
    # All content/identity/link/mode/reparse and other attribute fields stay exact.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, info.st_mode, getattr(info, 'st_file_attributes', 0) & ~0x40000)


def regular(info):
    return (stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
            info.st_nlink == 1 and not getattr(info, 'st_file_attributes', 0) & 0x400)


def read_stable(path, limit=MAX_PUBLIC_FILE):
    before = path.lstat()
    assert regular(before) and 0 <= before.st_size <= limit, 'Regular bounded file required'
    with path.open('rb') as stream:
        assert stamp(os.fstat(stream.fileno())) == stamp(before), 'File changed before read'
        raw = stream.read(before.st_size + 1)
        opened = os.fstat(stream.fileno())
    assert len(raw) == before.st_size and stamp(before) == stamp(opened) == stamp(path.lstat()), 'File changed during read'
    return raw, before


def packet_files(folder):
    result, pending = set(), [folder]
    while pending:
        current = pending.pop()
        info = current.lstat()
        assert stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
        for path in current.iterdir():
            info = path.lstat()
            assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'Public packet alias'
            if stat.S_ISDIR(info.st_mode):
                pending.append(path)
            else:
                assert regular(info), 'Public packet nonregular file'
                result.add(path.relative_to(folder).as_posix())
    return result


def scores(data):
    implementation = [row for row in data['requirements'] if row['category'] == 'required_implementation']
    return (sum(row['implementation'] == 'implemented' for row in implementation), len(implementation),
            sum(row['acceptance_status'] == 'verified' for row in data['requirements']), len(data['requirements']))


def main():
    if sys.flags.optimize:
        raise RuntimeError('Publication assertions require ordinary unoptimized Python')
    packets = tuple(sys.argv[1:]) or PACKETS
    assert packets == PACKETS, 'Only the explicit carrier followup and Root control packets are authorized'
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    allowed, records = set(DOCS), []
    for name in PACKETS:
        folder = ROOT / 'experiments' / name
        raw_manifest, _ = read_stable(folder / 'CONTENTS.json')
        manifest = parse(raw_manifest)
        rows = manifest['files']
        assert type(rows) is list and 0 < len(rows) <= 10000
        expected = set()
        for row in rows:
            assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
            value = row['path']
            assert type(value) is str and value and '\\' not in value and ':' not in value and '\x00' not in value
            path = PurePosixPath(value)
            assert not path.is_absolute() and path.as_posix() == value and '..' not in path.parts
            assert value not in expected and value != 'CONTENTS.json'
            assert Path(value).suffix.lower() in PUBLIC_SUFFIXES and Path(value).name.casefold() not in PRIVATE_NAMES
            assert not Path(value).name.casefold().startswith('private_'), 'Private payload filename in public manifest'
            assert type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_PUBLIC_FILE
            assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256'])
            target = folder / value
            assert target.resolve().is_relative_to(folder.resolve())
            raw, _ = read_stable(target)
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], value
            expected.add(value)
        expected.add('CONTENTS.json')
        assert len({value.casefold() for value in expected}) == len(expected), 'Case alias in manifest'
        actual = packet_files(folder)
        assert actual == expected, (name, actual ^ expected)
        assert read_stable(folder / 'CONTENTS.json')[0] == raw_manifest
        allowed.update((folder / item).relative_to(ROOT).as_posix() for item in actual)
        records.append(dict(packet=name, files=len(actual),
            bytes=sum((folder / item).stat().st_size for item in actual), CONTENTS_sha256=sha(raw_manifest)))
    changed = {value.decode('utf8') for value in git('diff', '--name-only', '-z', BASE).split(b'\0') if value}
    baseline_raw, _ = read_stable(ROOT / PROTECTED_OUTPUT_BASELINE)
    assert len(baseline_raw) == 33665 and sha(baseline_raw) == PROTECTED_OUTPUT_BASELINE_SHA256
    baseline = parse(baseline_raw)
    assert baseline['format'] == 'has_preserved_preexisting_tracked_output_baseline_1'
    assert baseline['revision'] == PROTECTED_OUTPUT_BASELINE_REVISION and baseline['source_or_application_change_authorized'] is False
    protected = baseline['entries']
    assert type(protected) is dict and baseline['files'] == len(protected) == 171
    assert sum(row['bytes'] for row in protected.values()) == 4411867
    for name, row in protected.items():
        assert type(name) is str and name.startswith('output/') and '\\' not in name and ':' not in name
        path = PurePosixPath(name)
        assert path.as_posix() == name and '..' not in path.parts
        assert type(row) is dict and set(row) == {'bytes', 'mtime_ns', 'sha256'}
        assert type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_PUBLIC_FILE
        assert type(row['mtime_ns']) is int and type(row['sha256']) is str
        assert re.fullmatch('[0-9a-f]{64}', row['sha256'])
        target = ROOT / name
        assert target.resolve().is_relative_to((ROOT / 'output').resolve())
        raw, info = read_stable(target)
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and info.st_mtime_ns == row['mtime_ns'], name
    protected_paths = set(protected)
    assert {name for name in changed if name.startswith('output/')} == protected_paths, 'Preexisting output path set changed'
    assert (changed - protected_paths) <= allowed, ('Unexpected tracked change', changed - protected_paths - allowed)
    staged = {value.decode('utf8') for value in git('diff', '--cached', '--name-only', '-z', BASE).split(b'\0') if value}
    assert not staged.intersection(protected_paths), 'Protected output must never enter the checkpoint index'
    assert not allowed.intersection(protected_paths)
    history = []
    for name in ('LLM.md', 'docs/progress_memo.md'):
        old = git('show', BASE + ':' + name)
        current, _ = read_stable(ROOT / name)
        assert len(current) > len(old) and current.startswith(old), 'Raw history prefix changed or missing append'
        history.append(dict(path=name, base_bytes=len(old), base_sha256=sha(old), appended_bytes=len(current)-len(old)))
    old = parse(git('show', BASE + ':docs/completion_checklist.json'))
    current = parse(read_stable(ROOT / 'docs/completion_checklist.json')[0])
    keys = ('id', 'category', 'implementation', 'verification', 'acceptance_status', 'external_dependencies')
    assert [{key: row[key] for key in keys} for row in old['requirements']] == [
        {key: row[key] for key in keys} for row in current['requirements']]
    assert len(current['requirements']) == 62 and old['scoring'] == current['scoring']
    assert scores(old) == scores(current) == (52, 54, 55, 62)
    full_raw, _ = read_stable(ROOT / SOURCE_AFTER)
    assert full_raw == git('show', BASE + ':' + SOURCE_AFTER), 'Recorded full-source catalogue differs'
    full = parse(full_raw)
    assert len(full) == 1061
    for name, row in full.items():
        raw, info = read_stable(ROOT / name)
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and info.st_mtime_ns == row['mtime_ns'], name
    # Render only after the exact functional checker source has been verified.
    path = ROOT / 'tools/check_completion.py'
    spec = importlib.util.spec_from_file_location('_has_carrier_followup_pure_checklist_renderer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.render(current) == (ROOT / 'docs/completion_checklist.md').read_text(encoding='utf8')
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    result = dict(format='has_source_carrier_followup_checkpoint_preflight_1', base=BASE,
        packets=records, exact_full_source_files=1061, histories=history,
        history_prefixes_exact=True, stable_statuses_unchanged=62,
        implementation_score=[52,54], acceptance_score=[55,62], generated_checklist_matches=True,
        changed_tracked_paths_within_explicit_allowlist_after_exact_protected_inventory=True,
        preserved_preexisting_tracked_output_files=171, preserved_output_bytes=4411867,
        preserved_output_baseline_sha256=PROTECTED_OUTPUT_BASELINE_SHA256,
        preserved_output_content_size_nsmtime_and_path_set_exact=True,
        preserved_output_excluded_from_index_and_allowed_payload=True,
        allowed_files=sorted(allowed), allowed_file_count=len(allowed),
        no_native_model_asset_or_private_capture_payloads_authorized=True)
    target = ROOT / 'output/source-carrier-followup-checkpoint-preflight-20261120.json'
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key != 'allowed_files'}))


if __name__ == '__main__':
    main()

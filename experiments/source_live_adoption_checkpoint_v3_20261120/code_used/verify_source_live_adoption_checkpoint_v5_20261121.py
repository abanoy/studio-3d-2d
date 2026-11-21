"""Root-only publication candidate; author did not execute it.

Restore/run from ROOT/output after the exclusive native job has closed.
Requires a closed successful Full360, exact 26-path adoption/fixture lineage,
153 old generated-content backups and an explicit final 171-path refresh snapshot.
No old 171-original-path byte/nsmtime preservation claim is made.
No model input, native application, conversion or cleanup is performed here.
"""
from pathlib import Path, PurePosixPath
import argparse
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
BASE = '165ebdfb3361e982666aa7355a432ba625f8d96a'
FUNCTIONAL_COMMIT = '1dc267df7bdef6a24e9298ab9d9ff15653f4b507'
FIXTURE_COMMIT = '36044471151a6e561d6d3a404859e76ddd05738d'
FIXTURE_PATH = 'tests/test_source_appearance.py'
FIXTURE_SHA256 = '3c7d19f886fea152ac3ce63672880d69f5a20b74a8a059fce6472475f464f8f7'
FIXTURE_PREDECESSOR_SHA256 = 'e717ba9f0c1d2382a98598355ad8a1981f7205f043f0d39d21294e27317e82bc'
FIXTURE_MANIFEST = 'experiments/source_live_adoption_checkpoint_v3_20261120/EXPECTED_SOURCE_26.json'
FIXTURE_MANIFEST_SHA256 = 'd3a4c6fd569a79609cfab80634fb55102490ce9c8a5270944e52be8ef5e95063'
REFRESH_PACKET = 'experiments/source_live_output_refresh_transition_20261120'
FAILED_TRANSITION = REFRESH_PACKET + '/FAILED_OUTPUT_REFRESH_TRANSITION.json'
FAILED_TRANSITION_SHA256 = '85e749be81d155610410b4732f91e1297cd870128cf6c673c395f9205c0d913f'
INTERMEDIATE_BASELINE = REFRESH_PACKET + '/POST_FAILED_GENERATED_OUTPUT_BASELINE.json'
INTERMEDIATE_BASELINE_SHA256 = '022827d1938f6b6b46f99061cbccd7d5020ffc5ebde8d1cbd0e5aefc7b290535'
FINAL_BASELINE = REFRESH_PACKET + '/POST_FULL_GENERATED_OUTPUT_BASELINE.json'
FULL_PACKET = 'experiments/source_live_full_20261120'
FULL_COMPLETION = FULL_PACKET + '/completion.json'
ORIGINAL_FULL_COMPLETION = 'output/windows-reference-body-1795233568436471500/completion.json'
FULL_SOURCE_BEFORE = FULL_PACKET + '/source-before.json'
FULL_SOURCE_AFTER = FULL_PACKET + '/source-after.json'
FULL_LAUNCH = FULL_PACKET + '/launch.json'
GENERATED_CACHES = frozenset({'tools/__pycache__/asset_audit.cpython-313.pyc',
    'tools/__pycache__/source_archive.cpython-313.pyc',
    'tools/__pycache__/source_content.cpython-313.pyc',
    'tools/__pycache__/source_paths.cpython-313.pyc'})
PROTECTED_OUTPUT_BASELINE_REVISION = '5f6a0efba5205f2b1ad4dda73271d968993db4c7'
PACKETS = ('source_live_native_normal_20261120', 'source_live_application_admission_20261120',
           'source_live_packaged_conversion_20261120', 'source_live_adoption_checkpoint_20261120',
           'source_live_adoption_checkpoint_v2_20261120', 'source_packaged_application_admission_20261120',
           'source_live_first_full_failed_20261120', 'source_live_full_20261120',
           'source_live_output_refresh_transition_20261120', 'source_live_adoption_checkpoint_v3_20261120')
FROZEN_PACKET_CONTENTS = {
    "source_live_native_normal_20261120": "1e51a4c8700b5185dcbcd367171c3975553ad8be6bc54a6b620a67298923b286",
    "source_live_application_admission_20261120": "4ae09ffa8a04d09098b91e1549a7443c7fa398ba6e34c0b65c1953a763489297",
    "source_live_packaged_conversion_20261120": "660e0564602896e8c5698c10f3c41299da5b84114811866089adb37b6e35a125",
    "source_live_adoption_checkpoint_20261120": "3cff397f11c67a87a441ddc7ec280e0a222669270c1b139ef8047ed2b1ae13d9",
    "source_live_adoption_checkpoint_v2_20261120": "a1d1b29524d1abd8e43633e163ec7c4ae53f03de17ea0b88d7d5c00a796a4e3c",
    "source_packaged_application_admission_20261120": "f9eb9a3ba85dbfa86154215b08775f574fab9f86ab6c22eb1e4656848d8c673c",
    "source_live_first_full_failed_20261120": "2e62dccab2120449f71cbfbce87bfe33c7b809443e10dae8ba5895907dfcca7b"
}
ENTRY_MANIFEST_PACKETS = {
    'source_live_application_admission_20261120': ('has_frozen_source_application_admission_contents_1', 29, 197220),
    'source_packaged_application_admission_20261120': ('has_frozen_packaged_editor_admission_contents_1', 19, 64861),
    'source_live_first_full_failed_20261120': ('has_failed_full_safe_contents_1', 72, 710595),
}
PRIVATE_PREFIX_CODE_EXCEPTIONS = {
    ('source_live_packaged_conversion_20261120', 'runtime/tools/private_desktop.py'):
        (12692, 'c3bad5ab1792f7103a9bf31eef283ee8b928bd4557b6e53c18b9c0718d92ae61'),
    ('source_live_packaged_conversion_20261120', 'runtime/tools/private_krita_container.py'):
        (12510, 'c9c1da96e2524f7a38e7ce4dda9df23d53c73a4a745a9e92bfe0987ed63152fe'),
}
DOCS = ('LLM.md', 'docs/NEXT_SESSION_PLAN_2026-11-20.md',
        'docs/RESUME_MASTER_PLAN.md', 'docs/benchmarks/reference_body_2026-11-20.json',
        'docs/completion_checklist.json', 'docs/completion_checklist.md',
        'docs/progress_memo.md')
PROTECTED_OUTPUT_BASELINE = 'experiments/source_material_carrier_checkpoint_20261120/evidence/source-carrier-preserved-tracked-output-baseline-20261120.json'
PROTECTED_OUTPUT_BASELINE_SHA256 = 'c40dfc182df6907acf1be74f46f49441e0c2a5f1ee388bb3a4e0c246f1b448e3'
SOURCE_AFTER = 'experiments/reference_body_full_20261120/source-after.json'
ADOPTION_MANIFEST = 'experiments/source_live_adoption_checkpoint_20261120/PORT_MANIFEST.json'
ADOPTION_MANIFEST_BYTES = 5064
ADOPTION_MANIFEST_SHA256 = '96c45dd7a0524a7809e971d864bfff41528e48db0ac0367d6f909754047d162a'
ADOPTION_FILE_COUNT = 25
PUBLIC_SUFFIXES = {'.py', '.gd', '.md', '.json', '.log', '.js', '.ps1', '.txt', '.sh', '.dockerfile'}
PRIVATE_NAMES = {'carrier.glb', 'private_primitive_ids.json', 'root_carrier_export_request.json',
                 'parameters.json', 'conversion-request.json'}
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


def committed_lineage(head, old_port, port, allowed):
    # Never reinterpret the first failed Full revision as the fixture successor.
    git('merge-base', '--is-ancestor', BASE, head)
    commits = git('rev-list', '--reverse', BASE + '..' + head).decode().splitlines()
    assert len(commits) >= 2 and commits[:2] == [FUNCTIONAL_COMMIT, FIXTURE_COMMIT]
    previous, records = BASE, []
    for ordinal, commit in enumerate(commits):
        assert re.fullmatch('[0-9a-f]{40}', commit)
        parents = git('show', '--no-patch', '--format=%P', commit).decode().strip().split()
        assert parents == [previous], 'Exact linear local lineage required'
        paths = {value.decode('utf8') for value in
                 git('diff', '--no-renames', '--name-only', '-z', previous, commit).split(b'\0') if value}
        if ordinal == 0:
            assert paths == set(old_port), ('First commit must be the exact original production25', paths ^ set(old_port))
            for name, row in old_port.items():
                raw = git('show', commit + ':' + name)
                assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], name
        elif ordinal == 1:
            assert paths == {FIXTURE_PATH}, 'Second commit must be fixture-only360'
            assert sha(git('show', previous + ':' + FIXTURE_PATH)) == FIXTURE_PREDECESSOR_SHA256
            raw = git('show', commit + ':' + FIXTURE_PATH)
            assert len(raw) == port[FIXTURE_PATH]['bytes'] and sha(raw) == FIXTURE_SHA256
        else:
            assert paths and paths <= allowed - set(port), 'Unexpected later committed path'
        for name in paths - set(DOCS) - set(port):
            assert git('show', commit + ':' + name) == read_stable(ROOT / name)[0], name
        records.append(dict(commit=commit, parent=previous, paths=sorted(paths)))
        previous = commit
    assert previous == head
    committed = {value.decode('utf8') for value in
                 git('diff', '--no-renames', '--name-only', '-z', BASE, head).split(b'\0') if value}
    assert committed <= allowed and set(port) <= committed
    return records


def pinned_json(name, expected_sha, expected_bytes=None):
    assert type(expected_sha) is str and re.fullmatch('[0-9a-f]{64}', expected_sha)
    assert expected_sha != '0' * 64, 'A real reviewed digest is mandatory'
    raw, info = read_stable(ROOT / name)
    assert sha(raw) == expected_sha, name
    assert expected_bytes is None or len(raw) == expected_bytes, name
    return parse(raw), raw, info


def refresh_outputs(old_baseline, args, completion, completion_info, launch):
    old = old_baseline['entries']
    transition, _raw, _info = pinned_json(FAILED_TRANSITION, FAILED_TRANSITION_SHA256, 57902)
    assert transition['format'] == 'has_explicit_authorized_failed_full_output_refresh_transition_1'
    assert transition['old_baseline']['sha256'] == PROTECTED_OUTPUT_BASELINE_SHA256
    assert transition['post_failed_and_targeted_baseline']['sha256'] == INTERMEDIATE_BASELINE_SHA256
    assert transition['previous_old_contents_recovered'] == 153
    assert transition['scope']['authorized_generated_output_refresh'] is True
    assert transition['scope']['first_1dc_full_passed'] is False
    assert transition['scope']['retry_360_full_passed'] is False  # Historical pre-retry observation.
    assert transition['scope']['outputs_staged_or_restored'] is False
    assert transition['scope']['owner_assets_modified_by_capture'] is False
    assert transition['scope']['old_frozen_baseline_or_checkers_modified'] is False
    recovered, backup_paths = set(), set()
    for row in transition['old_backup_contents']:
        assert type(row) is dict and set(row) == {'old_path', 'backup_path', 'bytes', 'sha256'}
        name = row['old_path']
        assert name in old and name not in recovered
        assert row['bytes'] == old[name]['bytes'] and row['sha256'] == old[name]['sha256']
        target = Path(row['backup_path'])
        expected_root = ROOT / 'output/pre-full-generated-output-preservation-20261120'
        recovered_root = ROOT / 'output/pre-full-generated-output-recovery-20261120/recovered'
        assert target.is_absolute() and (target.resolve().is_relative_to(expected_root.resolve()) or
               target.resolve().is_relative_to(recovered_root.resolve())), 'Unexpected backup scope'
        assert target.resolve() not in backup_paths and target.resolve() != (ROOT / name).resolve()
        raw, _info = read_stable(target)
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], name
        recovered.add(name); backup_paths.add(target.resolve())
    missing = {}
    for row in transition['old_contents_not_recovered']:
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        name = row['path']
        assert name in old and name not in missing and name not in recovered
        assert row['bytes'] == old[name]['bytes'] and row['sha256'] == old[name]['sha256']
        missing[name] = row
    assert len(recovered) == 153 and len(missing) == 18 and recovered | set(missing) == set(old)
    assert 'output/studio-engine.log' in recovered and 'output/verification.json' in recovered
    intermediate, _raw, _info = pinned_json(INTERMEDIATE_BASELINE, INTERMEDIATE_BASELINE_SHA256, 39784)
    assert intermediate['format'] == 'has_explicit_authorized_generated_output_baseline_1'
    assert intermediate['old_baseline_sha256'] == PROTECTED_OUTPUT_BASELINE_SHA256
    assert intermediate['paths'] == 171 and set(intermediate['entries']) == set(old)
    assert intermediate['complete_set_reread_stable'] is True
    assert intermediate['all_current_contents_copied_before_retry'] is True
    assert intermediate['original_outputs_restored'] is False
    assert intermediate['source_or_owner_inputs_modified_by_capture'] is False
    final, _raw, _info = pinned_json(FINAL_BASELINE, args.post_full_baseline_sha256)
    assert final['format'] == 'has_post_full_authorized_generated_output_baseline_1'
    assert final['revision'] == FIXTURE_COMMIT
    assert final['old_baseline_sha256'] == PROTECTED_OUTPUT_BASELINE_SHA256
    assert final['intermediate_baseline_sha256'] == INTERMEDIATE_BASELINE_SHA256
    assert final['closed_full_completion_sha256'] == args.full_completion_sha256
    assert final['authorizing_full_launch_sha256'] == args.full_launch_sha256
    assert final['full_source_after_sha256'] == args.full_source_after_sha256
    assert final['paths'] == 171 and set(final['entries']) == set(old)
    assert final['complete_set_reread_stable'] is True
    assert type(final['captured_at_ns']) is str and re.fullmatch('[0-9]{1,28}', final['captured_at_ns'])
    assert final['original_completion_path'] == ORIGINAL_FULL_COMPLETION
    assert type(final['original_completion_mtime_ns']) is str and re.fullmatch('[0-9]{1,28}', final['original_completion_mtime_ns'])
    assert int(final['original_completion_mtime_ns']) == completion_info.st_mtime_ns
    assert int(final['captured_at_ns']) >= completion_info.st_mtime_ns
    point = final['closed_process_point']
    assert point['verifier_pid'] == launch['pid'] and type(point['verifier_pid']) is int
    assert point['verifier_reaped'] is True and point['all_private_jobs_closed'] is True
    assert point['root_exclusive_lane_quiescent'] is True and point['owned_processes_remaining'] == 0
    assert type(point['owned_processes_remaining']) is int
    assert completion['child_reaped'] is True and completion['all_private_jobs_isolated_closed'] is True
    logical = 0
    for name, row in final['entries'].items():
        assert type(row) is dict and set(row) == {'bytes', 'mtime_ns', 'sha256'}
        assert type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_PUBLIC_FILE
        assert type(row['mtime_ns']) is str and re.fullmatch('[0-9]{1,28}', row['mtime_ns'])
        assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256'])
        target = ROOT / name
        assert target.resolve().is_relative_to((ROOT / 'output').resolve())
        raw, info = read_stable(target)
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and info.st_mtime_ns == int(row['mtime_ns']), name
        logical += len(raw)
    assert type(final['logical_bytes']) is int and final['logical_bytes'] == logical
    return dict(old_baseline_paths=171, privately_preserved_old_contents=153,
        old_generated_contents_not_recovered=18, unrecovered_paths=sorted(missing),
        original_path_old_171_invariance_claim=False,
        authorized_final_refresh_paths=171, final_generated_bytes=logical,
        final_baseline_sha256=args.post_full_baseline_sha256,
        closed_full_completion_sha256=args.full_completion_sha256,
        no_output_staging_or_restoration_authorized=True)


def full360(args, functional_rows):
    completion, completion_raw, _copy_info = pinned_json(FULL_COMPLETION, args.full_completion_sha256)
    original_raw, info = read_stable(ROOT / ORIGINAL_FULL_COMPLETION)
    assert original_raw == completion_raw, 'Archived completion differs from retained original'
    assert completion['format'] == 'has_reference_body_full_coordinator_1'
    assert completion['revision'] == FIXTURE_COMMIT and completion['functional_source_count'] == 1084
    assert completion['exit'] == 0 and type(completion['exit']) is int
    for key in ('child_reaped', 'functional_sources_unchanged', 'revision_unchanged',
                'fresh_final_report', 'all_private_jobs_isolated_closed',
                'nonzero_jobs_are_expected_cancellations', 'receipt_provenance_verified', 'whole_verifier_pass'):
        assert completion[key] is True, key
    assert type(completion['result_groups']) is int and completion['result_groups'] > 0
    assert type(completion['unique_current_private_jobs']) is int and completion['unique_current_private_jobs'] > 0
    launch, _raw, _info = pinned_json(FULL_LAUNCH, args.full_launch_sha256)
    assert launch['revision'] == FIXTURE_COMMIT and type(launch['pid']) is int and launch['pid'] > 0
    assert launch['args'][-1] == 'tests/verify.py' and '-B' in launch['args']
    assert launch['environment']['PYTHONDONTWRITEBYTECODE'] == '1'
    before, _raw, _info = pinned_json(FULL_SOURCE_BEFORE, args.full_source_before_sha256)
    after, _raw, _info = pinned_json(FULL_SOURCE_AFTER, args.full_source_after_sha256)
    assert type(before) is dict and before == after and set(after) == set(functional_rows) and len(after) == 1084
    for name, row in after.items():
        raw, current = read_stable(ROOT / name)
        assert row['bytes'] == len(raw) and row['sha256'] == sha(raw) and row['mtime_ns'] == current.st_mtime_ns, name
        assert functional_rows[name]['bytes'] == len(raw) and functional_rows[name]['sha256'] == sha(raw), name
    return completion, info, launch


def main():
    if sys.flags.optimize:
        raise RuntimeError('Publication assertions require ordinary unoptimized Python')
    parser = argparse.ArgumentParser()
    for option in ('post-full-baseline', 'full-completion', 'full-launch', 'full-source-before', 'full-source-after'):
        parser.add_argument('--' + option + '-sha256', required=True)
    args = parser.parse_args()
    for value in vars(args).values():
        assert re.fullmatch('[0-9a-f]{64}', value) and value != '0' * 64, 'Real reviewed final evidence SHA256 is required'
    head = git('rev-parse', 'HEAD').decode().strip()
    assert re.fullmatch('[0-9a-f]{40}', head)
    git('merge-base', '--is-ancestor', BASE, head)
    adoption_raw, _ = read_stable(ROOT / ADOPTION_MANIFEST)
    assert len(adoption_raw) == ADOPTION_MANIFEST_BYTES and sha(adoption_raw) == ADOPTION_MANIFEST_SHA256
    adoption = parse(adoption_raw)
    assert adoption['format'] == 'has_exact_live_normal_production_port_1'
    assert adoption['files'] == ADOPTION_FILE_COUNT and type(adoption['entries']) is list
    assert len(adoption['entries']) == ADOPTION_FILE_COUNT
    port = {}
    for row in adoption['entries']:
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        name = row['path']
        assert type(name) is str and name and '\\' not in name and ':' not in name and '\x00' not in name
        path = PurePosixPath(name)
        assert path.as_posix() == name and not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] in {'src', 'tests', 'tools'} and path.suffix in {'.py', '.gd'}
        assert name not in port and type(row['bytes']) is int and 0 < row['bytes'] <= MAX_PUBLIC_FILE
        assert type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256'])
        actual, _ = read_stable(ROOT / name)
        assert len(actual) == row['bytes'] and sha(actual) == row['sha256'], name
        port[name] = row
    assert len({name.casefold() for name in port}) == len(port), 'Port path case alias'
    assert sum(row['bytes'] for row in port.values()) == adoption['logical_bytes']
    old_port = dict(port)
    fixture, _raw, _info = pinned_json(FIXTURE_MANIFEST, FIXTURE_MANIFEST_SHA256, 5676)
    assert fixture['format'] == 'has_exact_live_normal_adoption_fixture_successor_sources_1'
    assert fixture['base_port_manifest_sha256'] == ADOPTION_MANIFEST_SHA256
    assert fixture['first_production_adoption_revision'] == FUNCTIONAL_COMMIT
    assert fixture['fixture_predecessor_sha256'] == FIXTURE_PREDECESSOR_SHA256
    assert fixture['fixture_successor_sha256'] == FIXTURE_SHA256
    assert fixture['files'] == 26 and len(fixture['entries']) == 26
    expected26 = {row['path']: row for row in fixture['entries']}
    assert len(expected26) == 26 and set(expected26) == set(old_port) | {FIXTURE_PATH}
    for name, row in old_port.items(): assert expected26[name] == row
    assert expected26[FIXTURE_PATH] == {'path': FIXTURE_PATH, 'bytes': 24902, 'sha256': FIXTURE_SHA256}
    assert fixture['logical_bytes'] == sum(row['bytes'] for row in expected26.values()) == 668096
    assert fixture['expected_current_functional_files'] == 1084 and fixture['unchanged_pre_port_paths'] == 1058
    raw, _info = read_stable(ROOT / FIXTURE_PATH)
    assert len(raw) == 24902 and sha(raw) == FIXTURE_SHA256
    port = expected26
    allowed, records = set(DOCS) | set(port), []
    for name in PACKETS:
        folder = ROOT / 'experiments' / name
        raw_manifest, _ = read_stable(folder / 'CONTENTS.json')
        if name in FROZEN_PACKET_CONTENTS:
            assert sha(raw_manifest) == FROZEN_PACKET_CONTENTS[name], 'Previously frozen packet manifest changed'
        manifest = parse(raw_manifest)
        if name in ENTRY_MANIFEST_PACKETS:
            expected_format, expected_count, expected_bytes = ENTRY_MANIFEST_PACKETS[name]
            assert manifest['format'] == expected_format
            assert set(manifest) == {'format', 'files_excluding_this_manifest', 'logical_bytes_excluding_this_manifest', 'entries'}
            rows = manifest['entries']
            assert manifest['files_excluding_this_manifest'] == len(rows) == expected_count
            assert manifest['logical_bytes_excluding_this_manifest'] == sum(row['bytes'] for row in rows) == expected_bytes
        else:
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
            if Path(value).name.casefold().startswith('private_'):
                assert (name, value) in PRIVATE_PREFIX_CODE_EXCEPTIONS, 'Private payload filename in public manifest'
                expected_size, expected_sha = PRIVATE_PREFIX_CODE_EXCEPTIONS[(name, value)]
                assert row['bytes'] == expected_size and row['sha256'] == expected_sha, 'Only exact qualified launcher code is admitted'
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
    lineage = committed_lineage(head, old_port, port, allowed)
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
        assert type(row['mtime_ns']) is int and re.fullmatch('[0-9a-f]{64}', row['sha256'])
    protected_paths = set(protected)
    assert {name for name in changed if name.startswith('output/')} <= protected_paths, 'Tracked output change outside the exact authorized171 set'
    changed_caches = {name for name in changed if '__pycache__' in PurePosixPath(name).parts or name.endswith('.pyc')}
    assert changed_caches <= GENERATED_CACHES, 'Unknown tracked generated cache change'
    assert (changed - protected_paths - changed_caches) <= allowed, 'Unexpected tracked change'
    staged = {value.decode('utf8') for value in git('diff', '--cached', '--name-only', '-z', BASE).split(b'\0') if value}
    assert not any(name.startswith('output/') or '__pycache__' in PurePosixPath(name).parts or name.endswith('.pyc') for name in staged), 'Generated outputs or caches cannot be indexed'
    assert not allowed.intersection(protected_paths | GENERATED_CACHES)
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
    unchanged_original = 0
    replaced_original, new_functional = [], []
    for name, row in full.items():
        raw, info = read_stable(ROOT / name)
        if name in port:
            original = git('show', BASE + ':' + name)
            assert len(original) == row['bytes'] and sha(original) == row['sha256'], name
            assert len(raw) == port[name]['bytes'] and sha(raw) == port[name]['sha256'], name
            replaced_original.append(name)
        else:
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and info.st_mtime_ns == row['mtime_ns'], name
            unchanged_original += 1
    for name in sorted(set(port) - set(full)):
        assert not git('ls-tree', BASE, '--', name), 'New functional path already exists at BASE'
        new_functional.append(name)
    current_functional = set()
    for directory in ('src', 'tests', 'tools', 'data', 'examples'):
        for name in packet_files(ROOT / directory):
            path = PurePosixPath(name)
            if '__pycache__' not in path.parts and path.suffix != '.pyc':
                current_functional.add(directory + '/' + name)
    current_functional.update(('main.tscn', 'project.godot', 'run.py', 'launch.pyw'))
    current_functional.update(('dependencies.json',
        'experiments/reference_body_20261120/receipt_provenance.py',
        'experiments/reference_body_20261120/run_full.py',
        'experiments/reference_body_20261120/run_scoped.py',
        'experiments/reference_body_20261120/stage_legacy_inputs.py',
        'experiments/reference_body_20261120/test_receipt_provenance.py',
        'experiments/reference_body_20261120/verify_units.py'))
    assert current_functional == set(full) | set(port), ('Unexpected functional pathset', current_functional ^ (set(full) | set(port)))
    assert unchanged_original == 1058 and set(replaced_original) == {'src/source_secondary.gd', 'tools/blender_source_bridge.py', FIXTURE_PATH}
    assert len(new_functional) == 23 and len(current_functional) == 1084
    functional_rows = dict(full); functional_rows.update(port)
    completion, completion_info, launch = full360(args, functional_rows)
    refresh = refresh_outputs(baseline, args, completion, completion_info, launch)
    # Render only after the exact functional checker source has been verified.
    path = ROOT / 'tools/check_completion.py'
    spec = importlib.util.spec_from_file_location('_has_live_adoption_pure_checklist_renderer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.render(current) == (ROOT / 'docs/completion_checklist.md').read_text(encoding='utf8')
    assert git('rev-parse', 'HEAD').decode().strip() == head
    result = dict(format='has_source_live_adoption_checkpoint_preflight_5', base=BASE, head=head,
        exact_linear_local_functional_then_publication_lineage=lineage,
        pinned_functional_commit=FUNCTIONAL_COMMIT, pinned_fixture_commit=FIXTURE_COMMIT,
        exact_fixture26_manifest_sha256=FIXTURE_MANIFEST_SHA256,
        packets=records, archived_full_source_files=1061,
        archived_full_source_catalogue_byteexact_to_BASE=True,
        original_full_source_files_untouched=unchanged_original,
        replaced_original_functional_paths=sorted(replaced_original),
        new_functional_paths=sorted(new_functional), current_functional_files=len(current_functional),
        exact_adopted_functional_pins=True, adoption_manifest_sha256=ADOPTION_MANIFEST_SHA256,
        current_full_verification_claim=True, current_full_revision=FIXTURE_COMMIT,
        current_full_completion_sha256=args.full_completion_sha256, histories=history,
        history_prefixes_exact=True, stable_statuses_unchanged=62,
        implementation_score=[52,54], acceptance_score=[55,62], generated_checklist_matches=True,
        changed_tracked_paths_within_explicit_allowlist_after_exact_protected_inventory=True,
        historical_output_baseline_sha256=PROTECTED_OUTPUT_BASELINE_SHA256,
        explicit_authorized_generated_output_refresh=refresh,
        old_171_original_path_invariance_claim=False,
        generated_outputs_and_pyc_excluded_from_index_and_allowed_payload=True,
        allowed_files=sorted(allowed), allowed_file_count=len(allowed),
        no_native_model_asset_or_private_capture_payloads_authorized=True)
    target = ROOT / 'output/source-live-adoption-checkpoint-v5-preflight-20261121.json'
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key != 'allowed_files'}))


if __name__ == '__main__':
    main()

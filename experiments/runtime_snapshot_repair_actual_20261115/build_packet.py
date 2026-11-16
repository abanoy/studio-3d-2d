"""Copy an explicit, metadata-only evidence allowlist. Never run runtime helpers."""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FAIL = 'output/windows-canonical-bone-binding-20261116T022132132'
REPLAY = 'output/runtime-snapshot-scope-20261116T030539570843'
OLD_CASE = 'output/world-selection-teardown/1794796856711017300'
NEW_CASE = 'output/world-selection-teardown/1794798340646990000'
OLD_PACKET = 'experiments/native_source_live_port_20261115/failed_dbf0bc1'
V2 = 'experiments/world_selection_runtime_snapshot_v2_20261115'
ROWS = []

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write_json(name, value):
    target = HERE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def copy(source, destination, role, compress=False):
    origin = ROOT / source
    assert origin.resolve().is_relative_to(ROOT.resolve()) and not origin.is_symlink()
    raw = origin.read_bytes()
    stored = gzip.compress(raw, compresslevel=9, mtime=0) if compress else raw
    destination += '.gz' if compress else ''
    target = HERE / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(stored)
    ROWS.append({'path': destination, 'source': source, 'role': role,
                 'encoding': 'deterministic_gzip' if compress else 'raw',
                 'raw_bytes': len(raw), 'raw_sha256': digest(raw),
                 'bytes': len(stored), 'sha256': digest(stored)})

def top_level(source, destination, role, exclude=()):
    # Explicit top-level metadata only. No stage/source-tree traversal.
    for origin in sorted((ROOT / source).iterdir()):
        if origin.is_file() and origin.name not in exclude:
            assert origin.suffix in ('.json', '.log'), origin
            copy(source + '/' + origin.name, destination + '/' + origin.name,
                 role, origin.stat().st_size >= 64000)

def main():
    top_level(FAIL, 'raw/failed_full', 'failed_full_raw_metadata')
    top_level(REPLAY, 'raw/scoped_replay', 'scoped_replay_raw_metadata')
    for source, destination in ((OLD_CASE, 'raw/failed_teardown'),
                                (NEW_CASE, 'raw/scoped_teardown')):
        top_level(source, destination, 'teardown_raw_metadata',
                  ('normal-home.png', 'selection-control.glb'))
    # Copy the prior sealed source-review/46-receipt packet, never native assets.
    prior = json.loads((ROOT / OLD_PACKET / 'INDEX.json').read_bytes())
    for row in prior['files']:
        name = row['path']
        assert Path(name).suffix in ('.json', '.md', '.ps1')
        raw = (ROOT / OLD_PACKET / name).read_bytes()
        assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
        copy(OLD_PACKET + '/' + name, 'prior_failure_review/' + name,
             'sealed_prior_failure_review')
    copy(OLD_PACKET + '/INDEX.json', 'prior_failure_review/INDEX.json',
         'sealed_prior_failure_index')
    for name in ('INDEX.json', 'SOURCE_PROVENANCE.json', 'README.md', 'REVIEW.diff',
                 'CPU_RESULT.json', 'CPU_TESTS.log'):
        copy(V2 + '/' + name, 'reviewed_v2/' + name, 'sealed_v2_review_metadata')
    for name in ('windows_native_leaf_full_timeout_2026-11-15.json',
                 'world_selection_runtime_snapshot_2026-11-15.json'):
        copy('docs/benchmarks/' + name, 'benchmarks/' + name, 'root_recorded_benchmark')
    copy('output/runtime-snapshot-v2-applied.json', 'raw/application.json',
         'actual_reviewed_source_application')
    aliases = {}
    for source in ('tools/build_owner_review_snapshot.py',
                   'tests/verify_world_selection_teardown.py',
                   'tests/test_owner_review_snapshot.py',
                   'tests/world_selection_teardown.gd', 'tests/verify.py'):
        destination = 'source/' + source
        copy(source, destination, 'frozen_explicit_source_alias')
        aliases[source] = {'alias': destination, 'sha256': ROWS[-1]['raw_sha256']}
    for name in ('apply_runtime_snapshot_v2.py', 'run_runtime_snapshot_owned.py',
                 'record_snapshot_repair.py', 'run_state_owned.py', 'close_owned.ps1'):
        source = 'experiments/native_source_live_port_20261115/' + name
        destination = 'observers/' + name
        copy(source, destination, 'frozen_observer_source_not_executed_by_packet')
        aliases[source] = {'alias': destination, 'sha256': ROWS[-1]['raw_sha256']}
    # These four exact receipt paths are derived from recorded commands/replay,
    # rather than walking either actual shipped-source tree.
    receipt_names = (
        (OLD_CASE, 'studio_f428ae6691f54c65abb90c1b9f029ec3.json', 'failed_startup'),
        (OLD_CASE, 'world_selection_teardown_ebb23007e3b2472e9afd5edc185f3a53.json', 'failed_late_child'),
        (NEW_CASE, 'studio_272908dc744341e2b1400bf9d1bd9119.json', 'scoped_startup'),
        (NEW_CASE, 'world_selection_teardown_df6412f5e48443d1912b72cb94a8cbb4.json', 'scoped_child'))
    for case, name, label in receipt_names:
        copy(case + '/shipped-source/output/private-desktop/' + name,
             'receipts/' + label + '.json', 'explicit_private_desktop_receipt')
    write_json('SOURCE_ALIASES.json', {'format': 'has_runtime_snapshot_source_aliases_1',
                                     'aliases': aliases})
    summary = {
        'format': 'has_runtime_snapshot_repair_actual_public_1',
        'classification': 'FAILED_FULL_THEN_PASSED_SCOPED_REPAIR_FULL_RETRY_REQUIRED',
        'original_full_remains_failed': True, 'full_default_pass_claimed': False,
        'source_commit': 'dbf0bc1145f74b5bbff814ec6a417ccd23ce0885',
        'failed_full': {'core_groups_passed': 36, 'functional_source_files': 1014,
                        'outer_timeout_seconds': 180, 'snapshot_files': 6023,
                        'experiment_files': 4551, 'docs_files': 436,
                        'late_child_pid': 71828,
                        'late_receipt_seconds_after_failed_finish': 7.8069579,
                        'assertions': 28, 'failures': 0,
                        'private_jobs_closed': 46, 'release_utc': '2026-11-16T02:55:49.6500273Z'},
        'termination': {'root_manual_or_process_sweep_termination_performed': False,
                        'outer_wrapper_stdlib_termination': 'SOURCE_TRACE_INFERENCE_WRAPPER_PID_NOT_CAPTURED',
                        'global_no_process_termination_claimed': False},
        'application_preflight': {
            'first_attempt': 'ROOT_REPORTED_INDEX_DICTIONARY_TREATED_AS_LIST_TYPEERROR_BEFORE_WRITES',
            'basis': 'Root report and dated LLM/progress record; no retained raw exception trace or PID supplied.',
            'raw_trace_claimed': False},
        'actual_CPU': {'checks': 27, 'real_Git_fixture_cases': 7,
                       'mocked_runtime_cases': 20, 'exit': 0, 'seconds': 4.146,
                       'basis': 'ROOT_REPORTED_OBSERVATION_IN_ROOT_TOOL_TRACE_ONLY',
                       'raw_stdout_or_PID_claimed': False,
                       'note': 'reviewed_v2/CPU_TESTS.log is earlier mock-only20 evidence, not raw stdout for actual27.'},
        'actual_scoped_replay': {'checks': 28, 'failures': 0, 'snapshot_files': 1024,
                                 'functional_observation_entries': 1015,
                                 'seconds': 21.763778000000457,
                                 'wrapper_pid': 86500, 'wrapper_exit': 0,
                                 'wrapper_reaped': True, 'timed_out': False,
                                 'owned_wrapper_terminated': False,
                                 'private_jobs_closed': 2,
                                 'budgets': {'outer': 180, 'startup': 60, 'teardown': 110}},
        'source_catalogue_coverage_note': 'Repaired observation adds dependencies.json coverage; this is not evidence the file was newly created. Only the reviewed3 overlapping source hashes change.',
        'unchanged': {'teardown_GDScript_assertions': True, 'budgets': True,
                      'Source1_native_backend': 'unchanged_between_failed_and_scoped_source_catalogues'},
        'owner_manual_hair_check': 'DEFERRED_BUSY_CONTINUE_INDEPENDENTLY_NO_OBSERVED_RESULT',
        'formal_acceptance': '55/62_UNCHANGED', 'implementation': '52/54_UNCHANGED',
        'privacy': {'payload_scope': 'EXPLICIT_SOURCE_AND_SAFE_METADATA_ONLY',
                    'actual_stage_source_trees_copied': False, 'actual_media_copied': False,
                    'native_geometry_rest_arrays_or_PCM_copied': False,
                    'path_metadata': 'Exact raw records deliberately retain checkout/tool/profile paths already in evidence. Catalogue asset names and SHA256 strings are metadata, not redistributed asset bytes.'},
        'verification_scope': 'Packet verifier is read-only stdlib CPU; source aliases, raw hashes, counts, cases, closure, budgets and privacy contract only. No engine/process/CIM/Git/upload action.'}
    write_json('SUMMARY.json', summary)
    write_json('SOURCE_MANIFEST.json', {'format': 'has_runtime_snapshot_exact_copy_manifest_1',
                                      'files': sorted(ROWS, key=lambda r: r['path'])})
    readme = '''# Failed full and actual scoped snapshot repair

The dbf0bc1 complete default remains **FAILED** on its outer 180-second teardown wrapper timeout. All36 core groups passed. Its separate late child passed28 unchanged checks/all4cases and closed normally; child71828's receipt was7.8069579seconds after the failed full finished. This cannot upgrade the failed full. Snapshot work covered6023files, including4551experiments and436docs, with about70seconds freezing and97seconds rehashing. These are observed approximate stage timings, not an OS-cause claim.

Root closed the failed graphics lease at02:55:49Z using46 actual private receipts, all closed. Its host observer did not terminate processes. Automatic wrapper termination is an inference from the timeout trace and Python stdlib behavior; the failed wrapper PID was not separately captured. No global no-termination claim is made.

Root applied the reviewed v2 three-file source packet, then observed27 actual CPU tests passing in4.146seconds (7 real-Git fixtures plus20 mocked runtime cases). That27-test observation is reported from the root tool trace; no raw stdout or PID is invented. The earlier v2 mock-only20 log is preserved with its own scope. The first application helper's dictionary/list TypeError was reported to refuse before writes; no raw trace was retained in this packet.

The actual scoped replay independently passed28/0/all4cases in21.763778seconds with1024snapshotfiles, unchanged180/60/110budgets,2 closed private jobs and retained wrapper86500 exiting0/reaped. It recorded no timeout or termination, exact before/after functional sources and zero owned commands after completion. This is scoped repair evidence. A fresh complete default remains required. The existing Source1 native backend, manual deferral and55/62,52/54 acceptance states are unchanged.

`SOURCE_MANIFEST.json` binds every exact copy to its original relative path, raw byte count and SHA256. Large catalogue/provenance JSON is deterministic gzip (mtime0); decompressing restores the exact original raw bytes/hash. `INDEX.json` binds all packet files except itself. Source aliases freeze only the explicit reviewed3 files, unchanged shared GDScript/full driver, and source-only observer/application helpers. Raw absolute tool, checkout and temporary profile paths are deliberately retained as evidence metadata.

No PNG/GLB/HAS/MDL/VVD, arbitrary media, native geometry/rest arrays, PCM, or complete actual stage trees are included. Hash catalogue entries may name such assets but contain no asset bytes. The old failed teardown verification is startup-only and lacks a completed process/result field; its standalone late result and receipt have their own classification.

Run the independent read-only CPU verifier with `python -B experiments/runtime_snapshot_repair_actual_20261115/verify_packet.py`. It does not import/run the frozen helpers or production tests, inspect processes, query Git, launch engines or upload anything. The builder copies only explicit safe metadata/source and is not a runtime replay.
'''
    (HERE / 'README.md').write_text(readme, encoding='utf-8', newline='\n')
    files = []
    for path in sorted(HERE.rglob('*')):
        if path.is_file() and path != HERE / 'INDEX.json':
            raw = path.read_bytes()
            files.append({'path': path.relative_to(HERE).as_posix(),
                          'bytes': len(raw), 'sha256': digest(raw)})
    write_json('INDEX.json', {'format': 'has_runtime_snapshot_repair_actual_index_1',
                             'files': files})
    print(json.dumps({'files': len(files), 'bytes': sum(r['bytes'] for r in files),
                      'index_sha256': digest((HERE / 'INDEX.json').read_bytes()),
                      'runtime_executed': False}))

if __name__ == '__main__':
    main()

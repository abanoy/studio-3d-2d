"""Read-only source/metadata audit; no app, parser, process API, Git or cleanup."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import os
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'
OUT = Path(__file__).resolve().parent
IDS = ('1794615194930984000-ae0e0967', '1794615438168999800-42f0686d')
OLD = [ROOT / 'output/source-choices-native' / name for name in IDS]
ARCHIVE = ROOT / 'experiments/resume_archive_20261115/historical-cleanup-audit'
ACTUAL = ROOT / 'experiments/source_appearance/main_native_app_actual_20261113'
TEXT = {'.py', '.pyw', '.gd', '.gdshader', '.tscn', '.tres', '.json', '.cfg',
        '.godot', '.uid', '.txt', '.md', '.svg', '.bat', '.ps1', '.sh', '.xml', '.ini'}
SOURCE = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    row = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
    SOURCE.append(row)
    return raw


def load(path):
    return json.loads(identity(path))


def frozen(name):
    raw = gzip.decompress(identity(ARCHIVE / (name + '.gz')))
    return json.loads(raw), {'archive': str(ARCHIVE / (name + '.gz')),
                             'raw_bytes': len(raw), 'raw_sha256': sha(raw)}


def beneath_old(path):
    absolute = Path(path).absolute()
    return any(absolute == base or absolute.is_relative_to(base) for base in OLD)


def ancestry_clear(path):
    for parent in (path, *path.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            return False
    return True


def scan(label, paths):
    rows, matches = [], []
    for path in sorted(set(paths)):
        if not path.is_file() or path.suffix == '.pyc' or '__pycache__' in path.parts:
            continue
        if path.suffix not in TEXT and path.name not in {'blank', 'Dockerfile'}:
            continue
        raw = path.read_bytes()
        row = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
        rows.append(row)
        found = [name for name in IDS if name.encode('ascii') in raw]
        if found:
            # Names/hashes/line numbers only; no model, PCM or oracle values.
            row = dict(row, matched_run_ids=found,
                       matching_lines=[i for i, line in enumerate(raw.splitlines(), 1)
                                       if any(name.encode('ascii') in line for name in found)])
            matches.append(row)
    return {'scope': label, 'text_files': len(rows), 'bytes': sum(r['bytes'] for r in rows),
            'source_manifest_sha256': sha(json.dumps(rows, sort_keys=True).encode()),
            'literal_root_references': matches}


def paths_in(value, prefix='$'):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from paths_in(item, prefix + '.' + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from paths_in(item, prefix + '[' + str(index) + ']')
    elif isinstance(value, str):
        if any(name in value for name in IDS):
            yield prefix


def main():
    previous, previous_source = frozen('FINAL_AUDIT.json')
    retained, retained_source = frozen('retained-originals-fresh-proof.json')
    dependency, dependency_source = frozen('executable-dependency-scan.json')
    assert previous['totals']['files'] == 9307
    assert previous['totals']['bytes'] == 1442187088
    inventory_sources = []
    for phase in ('core14', 'wider11'):
        inventory, source = frozen(phase + '-fresh-inventory.json')
        assert len(inventory['files']) in (4707, 4600)
        inventory_sources.append(source)

    # Exact old-process identities are closed records, not a current host query.
    closures = []
    for phase, old in zip(('core14', 'wider11'), OLD):
        release = load(ACTUAL / phase / 'actual/root/graphics-lease-released.json')
        raw = gzip.decompress(identity(ACTUAL / phase / 'actual/root/verification.json.gz'))
        assert sha(raw) == release['verification_sha256']
        assert raw == identity(old / 'verification.json')
        verification = json.loads(raw)
        assert Path(verification['folder']) == old and verification['passed']
        assert release['authoritative_coordinator_and_owned_workers_absent']
        assert release['lease_released'] and release['all_private_jobs_clean']
        assert release['preservation_all_eight'] and release['no_process_killed']
        assert all(verification['preservation'].values())
        launch = load(ACTUAL / phase / 'actual/root-launch/launch.json')
        assert launch['pid'] == release['coordinator_pid']
        assert launch['creation_utc'] == release['coordinator_creation_utc']
        jobs = []
        job_paths = sorted((ACTUAL / phase / 'actual/jobs').iterdir())
        assert len(job_paths) == release['private_jobs']
        for folder in job_paths:
            process = load(folder / 'process-verification.json')
            receipt = process['receipt']
            assert process['exit'] == 0 and not process['timed_out']
            assert process['retained_Popen_reaped'] and process['execution_error'] is None
            assert process['strict_result_binding'] and not process['error_markers']
            assert receipt['job_closed'] and receipt['desktop_closed'] and receipt['exit'] == 0
            assert not receipt['desktop_switch_requested'] and not receipt['foreground_child_observed']
            receipt_path = Path(process['receipt_path'])
            assert json.loads(identity(receipt_path)) == receipt
            jobs.append({'name': folder.name, 'exit': process['exit'],
                         'retained_Popen_reaped': True, 'strict_result_binding': True,
                         'child_pid': receipt['child_pid'], 'job_closed': True,
                         'desktop_closed': True, 'receipt_sha256': sha(receipt_path.read_bytes())})
        closures.append({'phase': phase, 'root': str(old),
                         'coordinator_pid': release['coordinator_pid'],
                         'coordinator_creation_utc': release['coordinator_creation_utc'],
                         'closed_observed_utc': release['checked_utc'],
                         'original_verification_sha256': sha(raw),
                         'private_jobs': jobs,
                         'exact_original_coordinator_and_owned_workers_closed': True,
                         'fresh_host_query_performed': False})

    functional = []
    for base, label in ((ROOT, 'current checkout functional source'),
                        (REVIEW / 'Studio', 'current replay2 review functional source')):
        paths = [p for name in ('src', 'tests', 'tools', 'data', 'examples')
                 for p in (base / name).rglob('*')]
        paths += [base / name for name in ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')]
        functional.append(scan(label, paths))
    active_dirs = ['experiments/replay_audio_fix_20261115/builder',
                   'experiments/replay_audio_fix_20261115/replay',
                   'experiments/resume_transport_20261115',
                   'experiments/source_0x31_native_leaf_20261115',
                   'experiments/source_0x31_native_leaf_diagnostic_20261115']
    active_paths = [p for folder in active_dirs for p in (ROOT / folder).rglob('*')]
    active_paths += [OUT / name for name in ('run_native_leaf.py', 'run_native_leaf_attempt1.py',
                                           'run_review_builder2.py', 'start_review_replay2_owned.ps1')]
    active_scan = scan('approved current builder/replay/FK/native-leaf source and public locks', active_paths)
    config_scan = scan('review launch/configuration metadata',
                       list(REVIEW.glob('*.bat')) + list(REVIEW.glob('*.json')) +
                       list((REVIEW / 'Profile').rglob('*.json')))
    assert not any(row['literal_root_references'] for row in functional + [active_scan, config_scan])

    # Read only packed JSON declarations, never a native model or asset member.
    built = load(REVIEW / 'BUILD-VERIFICATION.json')
    packages = []
    for row in built['projects']:
        package = REVIEW / row['file']
        with zipfile.ZipFile(package) as archive:
            metadata = {}
            for name in ('has.json', 'project.json'):
                info = archive.getinfo(name)
                assert info.file_size <= 1024 * 1024
                raw = archive.read(name)
                metadata[name] = {'bytes': len(raw), 'sha256': sha(raw),
                                  'literal_old_root_value_paths': list(paths_in(json.loads(raw)))}
            assert not any(v['literal_old_root_value_paths'] for v in metadata.values())
        packages.append({'file': str(package), 'metadata_only': metadata,
                         'asset_members_read': False,
                         'whole_package_build_sha256': row['sha256'],
                         'whole_package_SHA_freshly_recomputed': False})

    lock = load(ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json')
    assert not list(paths_in(lock))
    family_rows = []
    for family, files in retained.items():
        path = Path(family)
        assert not beneath_old(path)
        # No binary content reads: freshness of original bytes remains a gate.
        existing = sum((path / relative).is_file() for relative in files)
        clear = ancestry_clear(path)
        family_rows.append({'root': family, 'historical_files': len(files),
                            'historical_bytes': sum(v['bytes'] for v in files.values()),
                            'current_expected_files_exist': existing,
                            'root_and_ancestors_no_reparse': clear,
                            'under_either_old_root': False,
                            'included_in_current_4family_review_lock': family in lock['native_families'],
                            'fresh_original_binary_hashes_read': False})
    assert len(family_rows) == 5 and sum(r['historical_files'] for r in family_rows) == 561
    assert all(r['current_expected_files_exist'] == r['historical_files'] and
               r['root_and_ancestors_no_reparse'] for r in family_rows)

    historical = ROOT / 'experiments/source_appearance/inert_metadata_shapes_main_20261114/recipe/check_sfm_extra_baselines.py'
    historical_raw = identity(historical)
    assert sha(historical_raw) == '35ace8dca6eecfb8721e57cbe09696c870eac3e56382add3c6b48cc499421313'
    probe_dir = ROOT / 'experiments/owner_pause_20261114/prepared-unrun/old-native-exclusive-read-prep-20261114'
    for name in ('probe_after_release.py', 'root-release.template.json', 'README.md', 'INDEX.json'):
        identity(probe_dir / name)
    # Source copy in original output must still equal the preserved recipe.
    assert identity(ROOT / 'output/old-native-exclusive-read-prep-20261114/probe_after_release.py') == (probe_dir / 'probe_after_release.py').read_bytes()
    template = load(probe_dir / 'root-release.template.json')
    assert template['root_approved_readonly_probe'] is False
    report = {
        'format': 'has_old_native_current_source_readiness_independent_1',
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Source and compact metadata only. No engine/parser/test/process query/Git/network or deletion.',
        'source_context': 'f0dd57a2e568089d396fecba819ab987da658bf0; live HEAD not queried',
        'literal_roots': [str(p) for p in OLD], 'files': 9307, 'bytes': 1442187088,
        'historical_audit_source': previous_source,
        'historical_inventory_sources': inventory_sources,
        'retained_originals_source': retained_source,
        'old_dependency_scan_source': dependency_source,
        'historical_exact_owned_closure': closures,
        'current_text_dependency_scans': functional + [active_scan, config_scan],
        'current_packed_review_metadata': packages,
        'retained_original_family_path_readiness': family_rows,
        'known_historical_metadata_only_dependency': {
            'path': str(historical), 'sha256': sha(historical_raw),
            'old_roots_required_if_rerun_unmodified': True,
            'reads': 'cases/*/expected.json for catalogue lookup, 3 prior expected records and Nitori conversion-metadata/parameters.json',
            'current_app_review_FK_native_leaf_source_dependency': False,
            'remedy_before_historical_recipe_rerun': 'Restore exact metadata from preserved recovery or explicitly redirect that historical recipe; do not call the old hardcoded recipe relocatable.'},
        'probe_source_review': {
            'prepared_and_preserved_exact': True, 'executed_by_this_audit': False,
            'current_template_is_release': False,
            'preflight': 'Exact 2 inventories/counts/bytes/SHA, membership, file SHA/mtime/size, no reparse, regular single-link.',
            'handle_scope': 'Each file GENERIC_READ/share0/OPEN_EXISTING/FILE_FLAG_OPEN_REPARSE_POINT; exact file identity then immediate close; second inventory equal.',
            'limits': 'Sequential intervals only. Does not clear metadata-only handles, mapped views, directory handles, future reopening or reserve deletion access; does not identify the historical202 unobserved command lines.',
            'cleanup_authorized': False},
        'current_gate_status': {
            'exact_original_coordinator_worker_closure_established_from_preserved_records': True,
            'current_app_review_FK_native_leaf_literal_dependency_found': False,
            'protected_originals_outside_two_roots_with_all561_expected_files_present': True,
            'fresh9307_file_content_and_membership_and_sharing_probe': 'UNRUN by this audit',
            'fresh561_original_binary_content_preservation': 'Not established by this source-only audit; current review covers4families495files, historical Kanako66files requires separate freshness proof.',
            'remote_verified_publication': 'Not queried by this audit; root must bind actual later publication/retrieval proof.',
            'current_global_nonuse': 'NOT_ESTABLISHED; historical Restart Manager error29/202 unknown commandlines remain limitations.',
            'root_probe_release': 'False template only, not a valid current release.',
            'literal_cleanup_decision': 'Not made; retain both roots.'},
        'cleanup_authorized': False, 'deletions': False,
        'source_proofs': sorted({r['path']: r for r in SOURCE}.values(), key=lambda r: r['path'])}
    target = OUT / 'audit_old_native_readiness.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    note = '''# Two old native roots — source readiness audit

Retain both roots. This source-only audit did not execute the sharing probe or authorize cleanup.

The exact original app coordinators have preserved authoritative closure: Core14 PID6924, birth2026-11-14T00:13:14.8293269Z, closure00:17:17.8469651Z; Wider11 PID27444, birth00:17:18.0852224Z, closure00:21:21.2703127Z. Their24 private jobs have exact retained-Popen reaping, exit0, strict result/receipt binding and closed job/desktop evidence. The archived aggregates equal the original two-root verification bytes. This establishes those original owned processes ended; it is not a fresh global process/nonuse scan.

No literal old-root dependency was found in the current checkout/replay2 review functional text, current builder/replay/FK/native-leaf sources/locks or the four packed review projects' JSON declarations. No native model or embedded asset member was read for this audit. The current examples derive from the newer bone-binding four-case run. All561 expected retained-original files are present in five separate stage families, with clear family ancestors. The current review's preservation lock covers495 files/four families; historical Kanako's66 files need separate fresh content preservation.

One historical runnable recipe still depends on both roots: `check_sfm_extra_baselines.py` at SHA25635ace8dca6eecfb8721e57cbe09696c870eac3e56382add3c6b48cc499421313. It reads only old expected/parameters metadata. Those exact bytes have recorded recovery evidence, but the hardcoded recipe requires restore or deliberate redirection before rerun. This is a real historical reproducibility dependency, not an active app/review runtime dependency.

The source-reviewed exclusive-read probe remains UNRUN here. Root still needs an actual current release bound to closed full/review/runtime identities, remote-verified publication/retrieval, protected-source/original freshness, and current dependency/nonuse evidence. Its two inventory passes and9,307 sequential share0 read opens would strengthen current evidence but cannot exclude mapped views, metadata-only/directory handles, later reopening, or reserve deletion access. Historical Restart Manager error29 and202 unavailable commandlines must not be silently converted into a nonuse pass. A successful probe still requires a separate root decision for these two literal roots under current Windows sharing.

The two roots contain9,307 files/1,442,187,088 bytes. The46 public duplicate prep files are a separate cleanup scope. Nothing was deleted, moved, staged, committed, uploaded, launched or stopped.

`audit_old_native_readiness.json` records bounded hashes/counts, exact closure identities and all source proofs. It deliberately contains no private geometry, decoded PCM, native oracle matrices or media payloads.
'''
    (OUT / 'audit_old_native_readiness.md').write_text(note, encoding='utf-8', newline='\n')
    print(json.dumps({'passed_source_metadata_audit': True, 'cleanup_authorized': False,
                      'closure_jobs': sum(len(v['private_jobs']) for v in closures),
                      'retained_original_files_present': 561,
                      'current_dependency_scan_text_files': sum(v['text_files'] for v in report['current_text_dependency_scans']),
                      'json_sha256': sha(target.read_bytes()),
                      'md_sha256': sha((OUT / 'audit_old_native_readiness.md').read_bytes())}))


if __name__ == '__main__':
    main()

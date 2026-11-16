"""Archive exact bounded metadata for the completed four-example review.

No app, parser, process, Git, networking, cleanup or private media operation.
The fixed allowlist deliberately omits observed/request/expected/cache/images.
"""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN = ROOT / 'output/sfm-joints-final-validation-f0dd57a-replay2-20261115'
LAUNCH = ROOT / 'output/sfm-joints-final-replay-launch2-20261116T001109854'
OLD_RUN = ROOT / 'output/sfm-joints-final-validation-f0dd57a-20261115'
OLD_LAUNCH = ROOT / 'output/sfm-joints-final-replay-launch-20261115T235121533'
REVIEW = ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'
PREP = ROOT / 'experiments/replay_audio_fix_20261115'
REVISION = 'f0dd57a2e568089d396fecba819ab987da658bf0'
CASES = ['01-keiki_tools_chisels-groups-000', '02-mima_head-ordinary-shape-ui',
         '03-junko_hair-default-no-appearance', '04-multi_skin_glove-default-no-appearance']
EXPECTED = [44, 46, 49, 41]
FORBIDDEN = {'pcm', 'vertex_positions', 'vertex_buffer', 'index_buffer', 'image_data',
             'audio_data', 'base64', 'native_rest_words_uint32', 'native_rest_matrices',
             'Blender_matrix_local_row_major', 'expected_world_bones', 'expected_native_Z_tips'}


def require(value, detail):
    if not value:
        raise ValueError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = path.absolute()
    for ancestor in (path, *path.parents):
        value = ancestor.lstat()
        require(not stat.S_ISLNK(value.st_mode) and not getattr(value, 'st_file_attributes', 0) & 0x400,
                'Reparse/symlink refused')
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 16 * 1024 * 1024,
            'Single-link bounded metadata required')
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino),
            'Metadata changed while read')
    return raw


def private_scan(value):
    if isinstance(value, dict):
        for key, child in value.items():
            require(not (key in FORBIDDEN and child), 'Private payload key refused: ' + key)
            require(not (key in {'vertices', 'indices', 'triangles'} and isinstance(child, (list, dict))),
                    'Mesh array refused')
            private_scan(child)
    elif isinstance(value, list):
        for child in value:
            private_scan(child)
    elif isinstance(value, str):
        require(len(value) < 16_384, 'Unreviewed large string refused')


def load(path):
    raw = read(path)
    value = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    private_scan(value)
    return value


def write(path, raw):
    require(path.resolve().is_relative_to(HERE), 'Packet boundary')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)


def save(path, value):
    private_scan(value)
    write(path, (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + '\n').encode())


def main():
    require(not (HERE / 'PAYLOAD_INDEX.json').exists(), 'Preserve existing packet')
    verification = load(RUN / 'verification.json')
    build = load(REVIEW / 'BUILD-VERIFICATION.json')
    launch = load(LAUNCH / 'launch.json')
    closed = load(LAUNCH / 'authoritative-closure.json')
    require(verification['passed'] and verification['errors'] == [] and verification['source_commit'] == REVISION,
            'Actual final replay did not pass')
    require(len(verification['preservation']) == 9 and all(verification['preservation'].values()), 'Preservation failure')
    require(verification['graphics_processes_requested'] == 4 and len(verification['results']) == 4,
            'Expected exactly four jobs')
    require(verification['runtime_generated_files_retained'] == {'output': 10, '.godot': 0}, 'Generated-file record drift')
    require(build['passed'] and build['source_commit'] == REVISION and build['native_source_files'] == 495 and
            build['native_source_bytes'] == 451266730 and build['sourceio_files'] == 574 and
            build['installed_exporter_sources_preserved'] == 120, 'Build context drift')
    require(closed['validation_passed'] and closed['root_graphics_lease_released'] and
            closed['coordinator_original_absent'] and closed['owned_runtime_commands_absent'] and
            closed['no_process_killed'] and closed['actual_private_jobs_closed'] == 4 and closed['engine_checks'] == 180,
            'Actual root closure missing')
    require(closed['coordinator_pid'] == launch['pid'] == 80412 and
            closed['expected_creation_utc'] == launch['creation_utc'] == '2026-11-16T00:11:09.8789596Z' and
            closed['verification_sha256'] == sha(read(RUN / 'verification.json')), 'Closure identity differs')

    case_proofs = []
    all_names = []
    for index, name in enumerate(CASES):
        case = RUN / name
        result = load(case / 'result.json')
        process = load(case / 'process-verification.json')
        receipt = load(case / 'private-receipt.json')
        comparison = load(case / 'state-comparison.json')
        require(result['failures'] == 0 and len(result['checks']) == EXPECTED[index] and
                all(row['ok'] is True for row in result['checks']), 'Named engine assertion failed')
        require(process['passed'] and process['strict_result_binding'] and process['expected_checks'] == EXPECTED[index] and
                process['observed_checks'] == EXPECTED[index] and process['retained_Popen_reaped'] and
                process['exit'] == 0 and not process['timed_out'] and process['error_markers'] == [], 'Process failed')
        require(receipt['exit'] == 0 and all(receipt[key] is True for key in
                ['private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed']) and
                all(receipt[key] is False for key in ['desktop_switch_requested', 'foreground_child_observed']),
                'Private receipt failed')
        require(comparison['differences'] == {'before': [], 'after': [], 'extra': []}, 'Saved-state comparison failed')
        extra = result['extra_checks']
        require(len(extra) == process['named_extra_checks'] and all(value is True for value in extra.values()), 'Extra names failed')
        required = {'render.frame_0', 'render.frame_24'} | {'source_binding.relocated.' + suffix for suffix in
                ['report_identity', 'runtime_bindings', 'no_mutation', 'no_simulation']} | {'chooser.' + suffix for suffix in
                ['file_picker', 'dialog', 'metadata', 'native_catalogue', 'default_request', 'cancel', 'unchanged']}
        require(required <= set(extra), 'Required native/chooser/render check absent')
        audio = result['audio_cache_proofs']
        require(set(audio) == {'before', 'after', 'extra'}, 'Audio phase missing')
        for phase in audio.values():
            require(phase['passed'] and phase['expected_clips'] == len(phase['clips']) == 1, 'Audio proof failed')
            clip = phase['clips'][0]
            require(clip['passed'] and clip['cache_confined'] and clip['source_fields_exact'] and
                    clip['file_sha256'] == '5c27ff5c04e1d5f4e8d3c065fbee41b210128f3deb518c7da12c940ffbf255b9' and
                    clip['pcm_sha256'] == 'ac9d77efcea152df2090dacb61dcfd66c279587e90fba7700e5cb43c90f4ccaf' and
                    (clip['channels'], clip['rate'], clip['frames'], clip['pcm_bytes']) == (1, 48000, 24000, 48000),
                    'Audio bytes or sample metadata differ')
        require(result['native_setup']['pixel_sha256'] == result['native_focus']['pixel_sha256'] and
                result['native_readbacks_at_finish'] == 0, 'Native view/readback mismatch')
        if index == 2:
            helper = {key: value for key, value in extra.items() if key.startswith('native_helper.')}
            require(len(helper) == 8 and all(helper.values()), 'Junko helper cancellation/weights failed')
        case_proofs.append({'case': name, 'checks': EXPECTED[index], 'named_extra_checks': len(extra),
                            'named_extra_ledger': extra, 'private_desktop': receipt['desktop'],
                            'engine_pid': receipt['child_pid'], 'audio_phases': 3,
                            'strict_state_comparisons': 3, 'frame_reference_matches': 2,
                            'private_closed': True, 'authored_state_unchanged': True})
        all_names += [name + ':' + row['label'] for row in result['checks']]
    require(len(all_names) == 180 and len(set(all_names)) == 180, 'Assertion registry count/identity drift')
    require(len({row['private_desktop'] for row in case_proofs}) == 4, 'Private desktop reuse')
    prior = load(OLD_RUN / 'verification.json')
    require(prior['passed'] is False and prior['graphics_processes_requested'] == 1 and prior['results'] == [],
            'Prior failed validation must remain FAILED')

    sources = []
    sources += [(REVIEW / 'BUILD-VERIFICATION.json', 'build/BUILD-VERIFICATION.json')]
    for name in ['verification.json', 'runtime-generated-before.json', 'runtime-generated-after.json',
                 'shipped-before.json', 'shipped-after.json', 'harness-before.json', 'reference-inputs-before.json']:
        sources.append((RUN / name, 'replay/' + name))
    for name in ['launch.json', 'authoritative-closure.json', 'stdout.log', 'stderr.log']:
        sources.append((LAUNCH / name, 'closure/' + name))
    for name in ['review-build2-process.json', 'review-build2-stdout.log', 'review-build2-stderr.log']:
        sources.append((ROOT / 'experiments/resume_root_20261115' / name, 'build/' + name))
    for folder in ['builder', 'replay']:
        sources.append((PREP / folder / 'command.json', 'provenance/' + folder + '-approved-command.json'))
    for name in ['CPU_AUDIT.json', 'ORIGINS.json', 'STATIC_REVIEW.json', 'INDEX.json']:
        sources.append((PREP / name, 'provenance/audio-correction-' + name))
    for case_name in CASES:
        for name in ['command.json', 'process-verification.json', 'state-comparison.json', 'result.json',
                     'private-receipt.json', 'engine.log', 'stdout.log', 'stderr.log']:
            sources.append((RUN / case_name / name, 'cases/' + case_name + '/' + name))
    for name in ['verification.json']:
        sources.append((OLD_RUN / name, 'first-failure/' + name))
    for name in ['launch.json', 'authoritative-closure.json', 'stderr.log']:
        sources.append((OLD_LAUNCH / name, 'first-failure/' + name))
    for name in ['engine.log', 'process-verification.json', 'state-comparison.json', 'private-receipt.json']:
        sources.append((OLD_RUN / CASES[0] / name, 'first-failure/case/' + name))

    rows = []
    blobs = {}
    json_scanned = logs_scanned = 0
    for source, destination in sources:
        raw = read(source)
        if source.suffix == '.json':
            private_scan(json.loads(raw)); json_scanned += 1
        else:
            text = raw.decode('utf-8-sig')
            require(not re.search(r'"(?:pcm|vertex_positions|vertex_buffer|image_data|audio_data|base64)"\s*:', text),
                    'Raw payload marker in log')
            logs_scanned += 1
        digest = sha(raw)
        compressed = len(raw) > 32_768
        if digest in blobs:
            stored_path = blobs[digest]
        else:
            stored_path = destination + ('.gz' if compressed else '')
            write(HERE / stored_path, gzip.compress(raw, mtime=0) if compressed else raw)
            blobs[digest] = stored_path
        stored = read(HERE / stored_path)
        restored = gzip.decompress(stored) if compressed else stored
        require(restored == read(source) == raw, 'Copy/decompression source equality failed')
        rows.append({'source': str(source), 'original_relative_path': destination, 'path': stored_path,
                     'encoding': 'gzip' if compressed else 'identity', 'raw_bytes': len(raw), 'raw_sha256': digest,
                     'stored_bytes': len(stored), 'stored_sha256': sha(stored), 'decompression_source_exact': True})
    index = {'format': 'has_actual_sfm_review_metadata_archive_1', 'source_commit': REVISION,
             'files': rows, 'source_aliases': len(rows), 'stored_payloads': len(blobs),
             'raw_alias_bytes': sum(row['raw_bytes'] for row in rows),
             'stored_payload_bytes': sum((HERE / path).stat().st_size for path in blobs.values()),
             'JSON_payloads_scanned': json_scanned, 'logs_scanned': logs_scanned,
             'private_media_or_observed_payloads_copied': False}
    save(HERE / 'PAYLOAD_INDEX.json', index)
    benchmark = {'format': 'has_actual_sfm_final_review_benchmark_1', 'date': '2026-11-15',
        'source_commit': REVISION, 'passed': True, 'review': str(REVIEW), 'runtime': str(RUN),
        'coordinator_pid': launch['pid'], 'coordinator_creation_utc': launch['creation_utc'],
        'authoritative_closure_utc': closed['checked_utc'], 'checks': 180, 'check_split': EXPECTED,
        'named_extra_checks': sum(row['named_extra_checks'] for row in case_proofs),
        'private_jobs': 4, 'private_jobs_exit_0': 4, 'all_closed': True,
        'strict_state_comparisons': 12, 'audio_cache_phase_proofs': 12,
        'native_reference_frame_matches': 8, 'setup_focus_native_pixel_pairs_equal': 4,
        'native_chooser_named_checks': 28, 'source_binding_named_checks': 16,
        'Junko_imported_binding_profile': '69 bones and49 inert rules; helper review/cancel, not native dynamics',
        'native_helper_named_checks': 8, 'shape_availability_and_binding_named_checks': 8,
        'preservation': verification['preservation'], 'generated_retained': verification['runtime_generated_files_retained'],
        'native_source_files': build['native_source_files'], 'native_source_bytes': build['native_source_bytes'],
        'SourceIO_copied_files': build['sourceio_files'], 'exporter_sources_preserved': 120,
        'case_proofs': case_proofs, 'exact_names': all_names,
        'first_validation_status': 'FAILED_STATE_PROJECTION; engine41/41exit0/privateclosed',
        'first_failed_review_retained': True, 'production_source_changed_for_retry': False,
        'comparison_tolerance': 'Original1e-12absolute; allportable fields/order/types preserved',
        'audio_projection': 'Only decoded runtimeclip.source omitted; packageWAV/PCM/sample/cache proof added in3phases',
        'native_Source_solver': 'not_implemented', 'artist_or_human_device_acceptance': False,
        'full_canonical_is_separate': 'f0dd default49m16.8145699s /157keys /36core /21movies /192privatejobs',
        'cleanup': False, 'reclaimed_bytes': 0,
        'packet_payload_index_sha256': sha(read(HERE / 'PAYLOAD_INDEX.json'))}
    save(HERE / 'BENCHMARK.json', benchmark)
    save(HERE / 'ARCHIVE_VERIFICATION.json', {'format': 'has_actual_review_archive_verification_1',
        'passed': True, 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_aliases_verified': len(rows), 'stored_payloads_verified': len(blobs),
        'JSON_payloads_scanned': json_scanned, 'logs_scanned': logs_scanned,
        'all_stored_raw_and_source_bytes_equal': True, 'private_media_copied': False,
        'apps_or_process_queries': False, 'source_or_prior_review_changes': False,
        'deletions': 0, 'remote_verification': 'PENDING_ROOT_PUBLICATION'})
    print(json.dumps({'passed': True, 'checks': 180, 'cases': 4, 'source_aliases': len(rows),
                      'stored_payloads': len(blobs), 'stored_payload_bytes': index['stored_payload_bytes'],
                      'private_payloads': False, 'deletions': 0}))


if __name__ == '__main__':
    main()

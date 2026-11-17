"""One retained CPU child/case. No engine, process discovery or production import."""
from pathlib import Path
import argparse
import json
import struct
import sys
import time
import traceback
import tracemalloc
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as S


def write_bytes(path, raw, cap):
    S.need(type(raw) is bytes and len(raw) <= cap and path.name.startswith('PRIVATE_'), 'bounded private output required')
    with path.open('xb') as stream: stream.write(raw)


def perform(request, ctx, row, case):
    """No candidate/archive code can be imported on the oracle branch."""
    if request['phase'] == 'oracle':
        source, copied = S.read_pair(row)
        folder = S.ROOT / 'experiments' / S.PACKETS['oracle'][0]
        oracle = S.module('_pmx_observation_independent_oracle', folder / 'oracle.py')
        witness = oracle.read_oracle(source)
        raw = oracle.canonical(witness)
        write_bytes(case / 'PRIVATE_ORACLE.json', raw, 8 * 1024 * 1024)
        return {'witness_bytes': len(raw), 'witness_sha256': S.sha(raw), 'candidate_or_archive_imported': False}
    S.need(request['phase'] == 'compare' and request['root_witness_frozen'] is True, 'explicit Root-frozen second phase required')
    manifest = S.frozen_manifest(ctx, request['oracle_manifest'], request['oracle_manifest_sha256'],
                                 request['harness_index_sha256'], request['code_binding'])
    frozen = manifest['cases'][request['case_index']]
    witness_path = Path(request['oracle_manifest']).parent / ('case-' + str(request['case_index'])) / 'PRIVATE_ORACLE.json'
    witness_raw = S.read_stable(witness_path, 8 * 1024 * 1024, expected_sha=frozen['witness_sha256'])
    S.need(len(witness_raw) == frozen['witness_bytes'], 'Root-frozen witness length differs')
    witness = S.parse(witness_raw)
    S.need(witness['source']['sha256'] == row['sha256'] and witness['source']['bytes'] == row['source_identity']['st_size'], 'frozen witness/input source differs')
    source, copied = S.read_pair(row)
    # Candidate import is deliberately after all frozen-witness checks above.
    candidate_root = S.ROOT / 'experiments' / S.PACKETS['candidate'][0]
    reader = S.module('pmx_native_physics', candidate_root / 'pmx_native_physics.py')
    oracle_root = S.ROOT / 'experiments' / S.PACKETS['oracle'][0]
    comparator = S.module('_pmx_observation_typed_comparator', oracle_root / 'compare_tables.py')
    capsule = reader.read_pmx20_physics(copied)
    comparison = comparator.compare(capsule, witness)
    archive_root = S.ROOT / 'experiments' / S.PACKETS['archive'][0]
    archive = S.module('_pmx_observation_inert_archive', archive_root / 'pmx_archive.py')
    document = b'{"asset":{"version":"2.0"}}'
    document += b' ' * (-len(document) % 4)
    carrier = (struct.pack('<4sII', b'glTF', 2, 28 + len(document))
               + struct.pack('<II', len(document), 0x4e4f534a) + document + struct.pack('<II', 0, 0x004e4942))
    result = archive.assemble(carrier, source, copied, {'bytes': len(source), 'sha256': row['sha256']}, {})
    extracted = archive.extract(result['glb'], result['report'][archive.KEY], result['provenance'])
    candidate_raw = archive.canonical(capsule)
    S.need(extracted == candidate_raw, 'candidate/archive exact capsule roundtrip differs')
    S.need(struct.unpack_from('<I', result['glb'], 12)[0] <= 16 * 1024 * 1024, 'whole helper JSON capacity')
    write_bytes(case / 'PRIVATE_CANDIDATE.json', candidate_raw, 2 * 1024 * 1024)
    write_bytes(case / 'PRIVATE_ARCHIVE.glb', result['glb'], 16 * 1024 * 1024 + 28)
    write_bytes(case / 'PRIVATE_REPORT.json', archive.canonical(result['report']), 256 * 1024)
    S.save(case / 'PRIVATE_COMPARISON.json', comparison)
    S.read_stable(witness_path, 8 * 1024 * 1024, expected_sha=frozen['witness_sha256'], keep=False)
    return {'declaration_correspondence_observed': True, 'archive_exact_roundtrip_observed': True,
            'archive_carrier_is_authored_empty_GLB': True, 'actual_model_GLTF_or_HAS_retention_observed': False,
            'frozen_witness_sha256': frozen['witness_sha256'], 'candidate_sha256': S.sha(candidate_raw)}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True); args = parser.parse_args()
    started = time.perf_counter(); tracemalloc.start()
    request_path = S.safe(args.request); request = S.read_json(request_path, 128 * 1024, args.request_sha256)
    ctx = S.context(request['synthetic_root'], request['synthetic_provenance_sha256'])
    batch = S.output_path(ctx, request['batch_output'])
    S.need(type(request['case_index']) is int and 0 <= request['case_index'] < 4, 'exact case index required')
    case = batch / ('case-' + str(request['case_index']))
    S.need(request_path == case / 'PRIVATE_REQUEST.json' and case.is_dir(), 'exact owned case/request path required')
    complete = preserved = False; row = None; detail = {}; error_type = None
    try:
        S.need(ctx['synthetic'] or request['root_graphics_lane_closed'] is True, 'Root must close graphics lane first')
        S.need(Path(sys.executable).resolve() == ctx['python'] and S.sha(ctx['python'].read_bytes()) == ctx['python_sha'], 'approved Python binary required')
        S.verify_code(request)
        provenance = S.load_provenance(ctx); row = provenance['rows'][request['case_index']]
        detail = perform(request, ctx, row, case)
        complete = True
    except BaseException as error:
        error_type = type(error).__name__
        (case / 'PRIVATE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        try:
            S.need(row is not None, 'no observed input pair available')
            S.read_pair(row, keep=False)
            S.load_provenance(ctx); S.verify_code(request)
            if request['phase'] == 'compare':
                S.frozen_manifest(ctx, request['oracle_manifest'], request['oracle_manifest_sha256'],
                                  request['harness_index_sha256'], request['code_binding'])
            preserved = True
        except BaseException as error:
            error_type = error_type or type(error).__name__
            (case / 'PRIVATE_PRESERVATION_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    _current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    receipt = {'format': 'has_private_pmx_readonly_CPU_case_receipt_1', 'phase': request['phase'],
               'case_index': request['case_index'], 'completed': complete and preserved, 'preserved': preserved,
               'error_type': error_type, 'detail': detail, 'child_wall_seconds': time.perf_counter() - started,
               'python_tracemalloc_peak_bytes': peak, 'windows_peak_RSS_bytes': None,
               'measurement_scope': 'worker_main_through_phase_and_preservation_before_receipt_write',
               'hard_memory_enforcement': False, 'denied_write_delete_handles_or_IO_confinement': False,
               'native_protocol_qualified': False, 'simulation_or_production_adoption': False}
    S.save(case / 'PRIVATE_RECEIPT.json', receipt)
    return 0 if receipt['completed'] else 1


if __name__ == '__main__':
    try: raise SystemExit(main())
    except Exception:
        # Only the parent's private stderr stream receives entry failures.
        traceback.print_exc(); raise SystemExit(1)

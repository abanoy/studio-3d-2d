"""One private count diagnostic; no witness file, candidate or archive import."""
from pathlib import Path
import argparse, sys, traceback
sys.path.insert(0, str(Path(__file__).resolve().parent))
import support as B
S = B.S


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True); args = parser.parse_args()
    request = S.read_json(args.request, 128 * 1024, args.request_sha256)
    ctx = S.context(); batch = S.output_path(ctx, request['output'])
    index = request['case_index']; S.need(type(index) is int and 0 <= index < 4, 'exact case index required')
    case = batch / ('case-' + str(index))
    S.need(S.safe(args.request) == case / 'PRIVATE_REQUEST.json', 'exact private request required')
    row = None; completed = preserved = False
    try:
        B.closed_lane(request['closure']['path'], request['closure']['sha256'], request['root_actual_closed_lane'])
        S.need(Path(sys.executable).resolve() == ctx['python'] and S.sha(ctx['python'].read_bytes()) == ctx['python_sha'], 'approved Python required')
        before = B.verify_sources(request['source_index_sha256']); S.save(case / 'PRIVATE_SOURCE_BEFORE.json', before)
        provenance = S.load_provenance(ctx); row = provenance['rows'][index]
        source, copied = S.read_pair(row)
        diagnostic = S.module('_root_sealed_private_table_count_diagnostic', B.DIAGNOSTIC / 'diagnostic.py')
        result = diagnostic.diagnostic_counts(source)
        S.need(result['witness_returned'] is False and result['candidate_imported_or_run'] is False
               and result['original_limits_and_traversal_preserved'] is True, 'passive diagnostic scope differs')
        S.save(case / 'PRIVATE_COUNTS.json', result)
        completed = True
    except BaseException:
        (case / 'PRIVATE_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        try:
            S.need(row is not None, 'no admitted input pair')
            S.read_pair(row, keep=False); S.load_provenance(ctx)
            after = B.verify_sources(request['source_index_sha256']); S.need(after == before, 'source binding changed')
            B.closed_lane(request['closure']['path'], request['closure']['sha256'], request['root_actual_closed_lane'])
            S.save(case / 'PRIVATE_SOURCE_AFTER.json', after); preserved = True
        except BaseException:
            (case / 'PRIVATE_PRESERVATION_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
        S.save(case / 'PRIVATE_RECEIPT.json', {'case_index': index, 'completed': completed and preserved,
               'preserved': preserved, 'diagnostic_only': True, 'native_protocol_qualified': False})
    return 0 if completed and preserved else 1


if __name__ == '__main__':
    try: raise SystemExit(main())
    except Exception: traceback.print_exc(); raise SystemExit(1)

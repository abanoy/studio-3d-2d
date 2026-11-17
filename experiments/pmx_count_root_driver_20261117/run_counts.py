"""Root only: four retained60s private count diagnostics after fresh closed lane."""
from pathlib import Path
import argparse, json, sys, traceback
sys.path.insert(0, str(Path(__file__).resolve().parent))
import support as B
S = B.S


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-index-sha256', required=True)
    parser.add_argument('--root-actual-closed-lane', action='store_true', required=True)
    parser.add_argument('--closure', type=Path, required=True); parser.add_argument('--closure-sha256', required=True)
    args = parser.parse_args(); cases = []; target = None; preserved = False
    try:
        S.need(sys.platform == 'win32', 'actual Root Windows execution required')
        ctx = S.context()
        S.need(Path(sys.executable).resolve() == ctx['python'] and S.sha(ctx['python'].read_bytes()) == ctx['python_sha'], 'approved Python required')
        closure = B.closed_lane(args.closure, args.closure_sha256, args.root_actual_closed_lane)
        before = B.verify_sources(args.source_index_sha256)
        provenance = S.load_provenance(ctx)
        for row in provenance['rows']: S.read_pair(row, keep=False)
        target = S.output_path(ctx, args.output); S.need(not target.exists(), 'fresh private output required'); target.mkdir()
        S.save(target / 'PRIVATE_SOURCE_BEFORE.json', before)
        host = B.retained_host()
        for index in range(4):
            case = target / ('case-' + str(index)); case.mkdir()
            request = {'case_index': index, 'output': str(target), 'closure': closure,
                       'root_actual_closed_lane': True, 'source_index_sha256': args.source_index_sha256}
            S.save(case / 'PRIVATE_REQUEST.json', request)
            command = [str(ctx['python']), '-I', '-S', '-B', '-X', 'utf8', str(B.HERE / 'worker.py'),
                       '--request', str(case / 'PRIVATE_REQUEST.json'), '--request-sha256', S.sha(S.canonical(request))]
            S.save(case / 'PRIVATE_COMMAND.json', {'argv': command})
            process = {}; completed = pair_preserved = False; unconfirmed = False
            try:
                process = host['run_child'](command, case, timeout=60)
                if not process['timed_out'] and process['retained_Popen_reaped']:
                    receipt = S.read_json(case / 'PRIVATE_RECEIPT.json', 128 * 1024)
                    S.need(receipt['case_index'] == index and receipt['diagnostic_only'] is True
                           and receipt['native_protocol_qualified'] is False, 'exact private diagnostic receipt required')
                    pair_preserved = receipt['preserved'] is True
                    completed = process['exit'] == 0 and process['stream_acceptance_cap_passed'] and receipt['completed'] is True and pair_preserved
            except host['UnconfirmedClosure'] as error:
                process = error.record; unconfirmed = True
            except BaseException:
                (case / 'PRIVATE_PARENT_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
            cases.append({'case_index': index, 'completed': completed, 'preserved': pair_preserved,
                          'process': process, 'unconfirmed_child_closure': unconfirmed})
            if unconfirmed: break
        for row in provenance['rows']: S.read_pair(row, keep=False)
        S.load_provenance(ctx); after = B.verify_sources(args.source_index_sha256)
        S.need(after == before, 'source binding changed'); B.closed_lane(args.closure, args.closure_sha256, True)
        S.save(target / 'PRIVATE_SOURCE_AFTER.json', after); preserved = True
    except BaseException:
        if target is not None and target.is_dir():
            (target / 'PRIVATE_BATCH_FAILURE.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        public = {'cases': 4, 'started_cases': len(cases), 'completed_cases': sum(row['completed'] for row in cases),
                  'preserved_cases': sum(row['preserved'] for row in cases),
                  'timed_out_cases': sum(row['process'].get('timed_out') is True for row in cases),
                  'unconfirmed_closure_cases': sum(row['unconfirmed_child_closure'] for row in cases),
                  'all_original_copy_and_source_preserved': preserved}
        if target is not None and target.is_dir(): S.save(target / 'PRIVATE_BATCH.json', {'public_scalars': public, 'cases': cases, 'native_protocol_qualified': False})
        print(json.dumps(public, sort_keys=True))
    return 0 if preserved and len(cases) == 4 and all(row['completed'] for row in cases) else 1


if __name__ == '__main__': raise SystemExit(main())

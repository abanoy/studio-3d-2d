"""Retain metadata from six completed existing wrappers; never run the product."""
from pathlib import Path
import hashlib
import json
import re
import stat

BASE = Path(__file__).resolve().parent
ROOT = next(p for p in BASE.parents if (p / 'project.godot').is_file())
RUN = ROOT / 'output/helper-preview-regressions-20261113'
DEST = BASE / 'packet'
FINAL = ROOT / 'output/helper-preview/graphical-1794599542182978200-657f180d'
ORDER = ['secondary_helpers', 'secondary_existing_ribbon', 'secondary_picking',
         'secondary_batch', 'helper_morphs', 'scene_view']
BAD = ['ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'resources still in use', 'Orphan StringName:',
       'unclaimed string names', 'Pages in use exist at exit']


def require(value, message):
    if not value:
        raise RuntimeError(message)


def bounded(path):
    path = Path(path).absolute()
    require('..' not in path.parts and path != ROOT and path.resolve().is_relative_to(ROOT.resolve()),
            'Outside explicit checkout boundary: ' + str(path))
    for part in (path, *path.parents):
        if part.exists():
            row = part.lstat()
            require(not stat.S_ISLNK(row.st_mode) and not getattr(row, 'st_file_attributes', 0) & 0x400,
                    'Link/reparse metadata refused: ' + str(part))
        if part == ROOT:
            break
    return path


def read(path):
    path = bounded(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= 2 * 1024 * 1024,
            'Expected bounded metadata: ' + str(path))
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            'Metadata changed while reading: ' + str(path))
    return raw, dict(bytes=len(raw), mtime_ns=after.st_mtime_ns,
                     sha256=hashlib.sha256(raw).hexdigest())


def load(path):
    return json.loads(read(path)[0])


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    require(not DEST.exists(), 'Use a fresh packet destination')
    DEST.mkdir()
    provenance = []

    def copy(source, destination):
        source = bounded(source)
        require(source.suffix in ('.json', '.py'), 'Explicit metadata/coordinator source only')
        raw, record = read(source)
        target = DEST / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        require(read(source)[1] == record and read(target)[0] == raw, 'Metadata changed during copy')
        provenance.append(dict(source=source.relative_to(ROOT).as_posix(), destination=destination, **record))
        return json.loads(raw) if source.suffix == '.json' else None

    copy(Path(__file__), 'build_packet.py')
    copy(RUN / 'execute.py', 'coordinator/execute.py')
    report = copy(RUN / 'verification.json', 'coordinator/verification.json')
    copy(RUN / 'progress.json', 'coordinator/progress.json')
    before = copy(RUN / 'source-before.json', 'coordinator/source-before.json')
    after = copy(RUN / 'source-after.json', 'coordinator/source-after.json')
    final_before = load(FINAL / 'main-source-before.json')
    final_report = load(FINAL / 'verification.json')
    require(report['format'] == 'has_pending_helper_existing_regressions_1' and report['passed'] is True
            and report['source_preserved'] is True and report['head_before'] == report['head_after'],
            'Coordinator is not a terminal source-preserved pass')
    require(before == after == final_before and final_report['passed'] is True and final_report['checks'] == 305,
            'Regression source differs from the final helper305 working-source snapshot')
    require([r['label'] for r in report['results']] == ORDER, 'Wrong six-wrapper order')

    fresh_receipt_paths = list((ROOT / 'output/private-desktop').glob('*.json'))
    suites = []
    all_desktops = []
    receipt_records = []
    copied_count = 0
    logs = []

    def count_rows(value, prefix=''):
        result = []
        if isinstance(value, dict):
            if 'checks' in value:
                require(type(value['checks']) is int and value['failures'] == 0, 'Nonzero or malformed wrapper result')
                result.append(dict(path=prefix or '.', checks=value['checks'], failures=value['failures'],
                                   cases=value.get('cases') if isinstance(value.get('cases'), int) else None))
            for name, item in value.items():
                if name not in ('source_sha256', 'originals', 'private_receipt'):
                    result.extend(count_rows(item, (prefix + '.' + name).strip('.')))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                result.extend(count_rows(item, prefix + '.' + str(index)))
        return result

    for row in report['results']:
        label = row['label']
        require(row['passed'] is True and row['exit'] == 0 and row['reaped'] is True
                and not row.get('timed_out', False), 'Wrapper did not exit cleanly: ' + label)
        log_path = RUN / (label + '.log')
        raw_log, log_record = read(log_path)
        text = raw_log.decode('utf-8')
        value, json_end = json.JSONDecoder().raw_decode(text.lstrip())
        expected = value
        if label == 'secondary_helpers':
            actual_path = ROOT / 'output/secondary-helpers-verification.json'
            wrapper_folder = Path(value['folder'])
        elif label == 'secondary_existing_ribbon':
            wrapper_folder = Path(value['result']['movie']).parent.parent
            actual_path = wrapper_folder / 'verification.json'
        elif label in ('secondary_picking', 'secondary_batch'):
            wrapper_folder = Path(value['folder'])
            actual_path = wrapper_folder / 'verification.json'
            expected = {key: item for key, item in value.items() if key != 'folder'}
        elif label == 'helper_morphs':
            wrapper_folder = Path(value['folder'])
            actual_path = ROOT / 'output/helper-morphs-verification.json'
        else:
            wrapper_folder = Path(value['folder'])
            actual_path = ROOT / 'output/scene-view-verification.json'
        actual_raw, actual_record = read(actual_path)
        require(row['started_ns'] <= actual_record['mtime_ns'] <= row['finished_ns'],
                'Wrapper report is outside its fresh coordinator interval: ' + label)
        require(json.loads(actual_raw) == expected, 'Actual wrapper report differs from its captured stdout JSON: ' + label)
        copy(actual_path, 'wrappers/' + label + '/verification.json')

        selected = []
        for path in fresh_receipt_paths:
            if not row['started_ns'] <= path.stat().st_mtime_ns <= row['finished_ns']:
                continue
            _, receipt_identity = read(path)
            if not row['started_ns'] <= receipt_identity['mtime_ns'] <= row['finished_ns']:
                continue
            receipt = copy(path, 'private-receipts/' + label + '/' + path.name)
            clean = receipt.get('format') == 'studio_private_desktop_1' and receipt.get('exit') == 0 and all(
                receipt.get(key) is True for key in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed')) and all(
                receipt.get(key) is False for key in ('foreground_child_observed', 'desktop_switch_requested'))
            require(clean, 'Fresh private receipt is not a closed isolated exit0: ' + str(path))
            all_desktops.append(receipt['desktop'])
            item = dict(wrapper=label, source=path.relative_to(ROOT).as_posix(), **receipt_identity,
                        interval_start_ns=row['started_ns'], interval_end_ns=row['finished_ns'],
                        desktop=receipt['desktop'], child_pid=receipt['child_pid'], clean_exit0_private_closed=True)
            receipt_records.append(item)
            selected.append(item)
            copied_count += 1
        require(selected, 'Graphical wrapper has no fresh root private-desktop receipt: ' + label)

        related_logs = {log_path}
        for path in (ROOT / 'output').glob('*.log'):
            if row['started_ns'] <= path.stat().st_mtime_ns <= row['finished_ns']:
                related_logs.add(path)
        for path in bounded(wrapper_folder).rglob('*.log'):
            if row['started_ns'] <= path.stat().st_mtime_ns <= row['finished_ns']:
                related_logs.add(path)
        markers = []
        for path in sorted(related_logs):
            raw, stamp = read(path)
            content = raw.decode('utf-8', 'replace')
            bad = {marker: content.count(marker) for marker in BAD if marker in content}
            bad_lines = [line[:512] for line in content.splitlines() if any(marker in line for marker in BAD)]
            entry = dict(wrapper=label, path=path.relative_to(ROOT).as_posix(), **stamp,
                         bad_markers=bad, first_bad_lines=bad_lines[:12],
                         pass_line_count=sum(line.startswith('PASS ') for line in content.splitlines()))
            logs.append(entry)
            markers.extend(bad)
        require(not markers, 'Existing wrapper produced unexpected error/warning markers: ' + label)
        python_tests = [{'tests': int(number), 'seconds': float(seconds)}
                        for number, seconds in re.findall(r'Ran (\d+) tests? in ([0-9.]+)s', text)]
        suites.append(dict(label=label, terminal_exit=row['exit'], source_context='literal main_working_source',
                           reports_equal_to_captured_stdout=True, stdout_log=log_record,
                           actual_report=dict(path=actual_path.relative_to(ROOT).as_posix(), **actual_record),
                           result_counts=count_rows(value), python_tests=python_tests,
                           private_receipts=len(selected), scanned_logs=len(related_logs), bad_markers=[]))

    require(copied_count == 9 and len(all_desktops) == len(set(all_desktops)), 'Expected nine fresh unique private desktops')
    final_private = {r['private_receipt']['desktop'] for r in final_report['results']}
    require(not final_private.intersection(all_desktops), 'Receipts overlap the separate helper305 run')
    _, final_source_record = read(FINAL / 'main-source-before.json')
    write(DEST / 'source-context.json', dict(
        source_context='literal main_working_source', head=report['head_before'],
        functional_file_count=len(before), source_before_after_exact=True,
        same_functional_manifest_as_final_helper305=True,
        final_helper305_source_reference=dict(path=(FINAL / 'main-source-before.json').relative_to(ROOT).as_posix(), **final_source_record),
        committed_source_pass=False, full_default_aggregate_pass=False))
    write(DEST / 'wrapper-counts-and-reports.json', suites)
    write(DEST / 'private-receipt-admission.json', dict(
        format='has_existing_regression_private_admission_1', selection='root output/private-desktop file mtime_ns within each exact coordinator row start..end',
        receipt_count=9, unique_desktops=9, all_closed_private_exit0=True,
        separate_from_helper305_desktops=True, records=receipt_records))
    write(DEST / 'log-marker-summary.json', dict(format='has_existing_regression_log_marker_summary_1', logs=logs,
          raw_generated_logs_copied=False, all_scanned_bad_marker_lists_empty=True))
    write(DEST / 'METADATA_SOURCES.json', dict(format='has_existing_regression_metadata_sources_1', files=provenance))
    write(DEST / 'summary.json', dict(format='has_existing_helper_regressions_evidence_1', wrappers=6,
        source_context='literal main_working_source', all_wrappers_passed=True,
        functional_source_and_head_preserved=True, same_source_as_final_helper305=True,
        fresh_private_receipts=9, unique_desktops=9, python_test_count=sum(sum(v['tests'] for v in r['python_tests']) for r in suites),
        wrapper_details=suites, broader_source_fidelity=False, human_or_device_acceptance=False,
        installed_studio_replaced=False, committed_source_pass=False, full_default_aggregate_pass=False,
        private_art_or_media_copied=False))
    (DEST / 'README.md').write_text('''# Existing helper regression evidence

All six existing wrappers passed against literal working main. The complete functional manifest and HEAD stayed unchanged, and the manifest equals the final helper305 run's source. This is targeted pre-commit evidence; a later stable full-default run is separate.

| Wrapper | Actual predicates | Python tests | Fresh private receipts |
|---|---|---:|---:|
| Helpers | 39 main, 14 native, 59 multiple parts, 35 patch | 20 + 9 | 4 |
| Existing native joints with ribbon | 33 | 0 | 1 |
| Part picking | 20 unit, 31 app | 0 | 1 |
| Batch authoring | 5 unit, 34 app | 26 | 1 |
| Helper morphs | 32 render | 10 | 1 |
| Scene view | 12,830 unit across 144 cases; 102 app | 0 | 1 |

All nine root private-desktop receipts were selected by exact coordinator start/end intervals and independently checked for native exit0, private-window/child confirmation, no foreground exposure or desktop switch, and closed Job/desktop. They are unique and separate from the helper305 receipts. Actual wrapper reports match the stdout JSON captured by the coordinator; report hashes and fresh timestamps are retained.

The native-with-ribbon route is the prepared Back hair case and same-process packed replay. Helper-morph render evidence retains its product_integration=false label. These results do not certify broad original Source shader/flex/jiggle appearance, cold-machine installation, artist review, learner/device observations or audible synchronization.

The packet contains coordinator source, exact source maps, terminal metadata, actual wrapper reports, source/report hashes, and compact log marker summaries. It contains no art, GLB/HAS payloads, images, audio or movies. INDEX.json identifies exact retained bytes.
''', encoding='utf-8')
    files = {}
    for path in sorted(DEST.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            files[path.relative_to(DEST).as_posix()] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    write(DEST / 'INDEX.json', dict(format='has_existing_helper_regression_evidence_files_1', files=files,
          indexed_files=len(files), indexed_bytes=sum(v['bytes'] for v in files.values())))
    print(json.dumps(dict(packet=str(DEST), indexed_files=len(files), indexed_bytes=sum(v['bytes'] for v in files.values()),
                          index_sha256=hashlib.sha256((DEST / 'INDEX.json').read_bytes()).hexdigest()), indent=2))


if __name__ == '__main__':
    main()

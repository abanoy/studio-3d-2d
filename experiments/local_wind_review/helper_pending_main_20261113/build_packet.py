"""Copy an explicit compact metadata plan; never copy projects, art or media.

This output-only builder does not run the product, import product modules, change
source, or certify a committed revision. Every copied record retains provenance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import stat

BASE = Path(__file__).resolve().parent
ROOT = next(parent for parent in BASE.parents if (parent / 'project.godot').is_file())
BAD = ('ERROR:', 'WARNING:', 'SCRIPT ERROR', 'SHADER ERROR', 'FAIL ',
       'ObjectDB instances leaked', 'resources still in use', 'Orphan StringName:',
       'unclaimed string names', 'Pages in use exist at exit')
MAIN_FILES = ['src/' + name + '.gd' for name in (
    'app', 'physics_editor', 'pose_editor', 'secondary_helper_editor', 'wind_review',
    'pending_helper_preview', 'pending_helper_wind_player', 'wind_helper_bridge',
    'wind_helper_runtime', 'wind_helper_candidate')]
MAIN_FILES += ['tools/' + name + '.py' for name in (
    'wind_helper_preview', 'wind_preview_controller', 'wind_preview_owned',
    'wind_preview_worker')]
MAX_METADATA = 2 * 1024 * 1024


def require(value, message):
    if not value:
        raise RuntimeError(message)


def bounded(path, boundary=ROOT):
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    require('..' not in path.parts and path != boundary and
            path.resolve().is_relative_to(boundary.resolve()), 'Outside owned boundary: ' + str(path))
    for part in (path, *path.parents):
        if part.exists():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and
                    not getattr(info, 'st_file_attributes', 0) & 0x400,
                    'Link/reparse path refused: ' + str(part))
        if part == boundary:
            break
    return path


def rel(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name
            and all(p not in ('', '.', '..') for p in name.split('/')), 'Explicit canonical relative path required')
    return name


def identity(path):
    path = bounded(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_METADATA,
            'Metadata is missing, nonregular or too large: ' + str(path))
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            'Metadata changed while read: ' + str(path))
    return raw, dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), mtime_ns=after.st_mtime_ns)


def load(path):
    return json.loads(identity(path)[0])


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


class Packet:
    def __init__(self, destination):
        self.destination = bounded(destination, BASE)
        require(not self.destination.exists(), 'Packet destination must be fresh')
        self.destination.mkdir(parents=True)
        self.provenance = []
        self.inventories = set()

    def copy(self, source, destination):
        source = bounded(source)
        destination = bounded(self.destination / rel(destination), self.destination)
        raw, stamp = identity(source)
        require(source.suffix in ('.json', '.md', '.log', '.gd', '.py'),
                'Only explicitly named metadata/probe/builder files may be copied')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(raw)
        require(identity(source)[1] == stamp and identity(destination)[0] == raw,
                'Metadata copy changed: ' + str(source))
        self.provenance.append(dict(source=source.relative_to(ROOT).as_posix(),
                                    destination=destination.relative_to(self.destination).as_posix(), **stamp))
        return json.loads(raw) if source.suffix == '.json' else raw.decode('utf-8', 'replace')

    def source_scope(self, folder, target, names):
        records = {}
        manifests = {}
        for label, name in names.items():
            path = folder / name
            if path.is_file():
                raw, stamp = identity(path)
                value = json.loads(raw)
                require(isinstance(value, dict), 'Source manifest must be an object')
                records[label] = dict(path=path.relative_to(ROOT).as_posix(), entries=len(value), **stamp)
                manifests[label] = value
        require('before' in manifests and 'after' in manifests, 'Terminal source manifests missing')
        before = manifests['before']
        hashes = {name: row['sha256'] for name, row in sorted(before.items())}
        inventory_digest = hashlib.sha256(encoded(hashes)).hexdigest()
        if inventory_digest not in self.inventories:
            write(self.destination / 'source-inventories' / (inventory_digest + '.json'), hashes)
            self.inventories.add(inventory_digest)
        summary = dict(capture_records=records, before_after_exact=before == manifests['after'],
                       functional_file_count=len(before), sha256_inventory=inventory_digest,
                       selected_runtime_files={name: before[name] for name in MAIN_FILES if name in before},
                       status='Captured working-main bytes; this does not certify that HEAD alone contains these edits.')
        if 'snapshot' in manifests:
            summary['snapshot_before_equals_main_before'] = manifests['snapshot'] == before
        write(self.destination / target / 'source-scope.json', summary)
        return summary

    def logs(self, folder, target):
        rows = []
        for path in sorted(folder.rglob('*.log')):
            raw, stamp = identity(path)
            text = raw.decode('utf-8', 'replace')
            lines = text.splitlines()
            bad_lines = [line[:512] for line in lines if any(marker in line for marker in BAD)]
            rows.append(dict(path=path.relative_to(ROOT).as_posix(), **stamp,
                             bad_markers={marker: text.count(marker) for marker in BAD if marker in text},
                             pass_line_count=sum(line.startswith('PASS ') for line in lines),
                             fail_line_count=sum(line.startswith('FAIL ') for line in lines),
                             first_bad_lines=bad_lines[:12]))
        write(self.destination / target / 'log-summary.json', dict(
            format='has_compact_log_marker_summary_1', rows=rows,
            raw_logs_copied=False,
            scope='Marker scan of retained generated logs, not a claim about human/device acceptance.'))
        return rows

    def receipts(self, paths, target, expected_pass):
        rows = []
        for index, path in enumerate(paths):
            receipt = self.copy(path, target + '/private-receipts/' + str(index) + '.json')
            clean = all(receipt.get(key) is True for key in (
                'job_closed', 'desktop_closed', 'child_desktop_confirmed', 'private_window_seen')) and all(
                receipt.get(key) is False for key in ('foreground_child_observed', 'desktop_switch_requested'))
            require(not expected_pass or clean and receipt.get('exit') == 0,
                    'Accepted run has an unclean/failed private receipt: ' + str(path))
            rows.append(dict(path=path.relative_to(ROOT).as_posix(), desktop=receipt.get('desktop'),
                             child_pid=receipt.get('child_pid'), seconds=receipt.get('seconds'),
                             native_exit=receipt.get('exit'), clean=clean))
        return rows

    def worker_receipts(self, folder, target):
        rows = []
        names = ('owned-launch.json', 'owned-outcome.json', 'owned-cleanup-after-failure.json')
        for name in names:
            for path in sorted(folder.rglob(name)):
                raw, stamp = identity(path)
                value = json.loads(raw)
                require(value.get('format') in ('has_wind_owned_launch_1', 'has_wind_owned_outcome_1'),
                        'Unexpected owned-worker receipt format')
                rows.append(dict(path=path.relative_to(ROOT).as_posix(), **stamp, value=value))
        write(self.destination / target / 'worker-receipts.json', dict(
            format='has_compact_owned_worker_receipts_1', records=rows,
            scope='Only fixed launch/outcome metadata. No request, preview receipt, binding proof or candidate payload is copied.'))

    def run(self, descriptor):
        label = rel(descriptor['id'])
        require('/' not in label, 'Case ID must be one path component')
        folder = bounded(ROOT / rel(descriptor['folder']), ROOT / 'output')
        kind = descriptor['kind']
        accepted = descriptor['expected_terminal_pass']
        require(type(accepted) is bool, 'Explicit expected terminal pass is required')
        target = ('accepted/' if accepted else 'failed/') + label
        if kind == 'domain':
            result = self.copy(folder / 'result.json', target + '/result.json')
            require(result.get('format') == 'has_helper_preview_driver_domain_1', 'Wrong domain report format')
            actual_pass = result.get('failures') == []
            require(actual_pass == accepted, 'Domain terminal status differs from plan')
            return dict(id=label, kind=kind, folder=descriptor['folder'], expected_terminal_pass=accepted,
                        checks=len(result.get('checks', [])), failures=len(result.get('failures', [])),
                        scope=descriptor['scope'], status='passed' if actual_pass else 'failed',
                        source_context='Pure mocked no-runtime domain controls; not a product or GPU pass.')
        report = self.copy(folder / 'verification.json', target + '/verification.json')
        require(report.get('passed') is accepted, 'Terminal status differs from explicit plan: ' + label)
        if kind == 'helper':
            require(report.get('format') == 'has_helper_preview_main_verification_1', 'Wrong helper report format')
            try:
                scope = self.source_scope(folder, target, dict(before='main-source-before.json',
                        after='main-source-after.json', snapshot='snapshot-source-before.json'))
            except Exception as error:
                if accepted:
                    raise
                scope = dict(failed_terminal_preserved=True, source_scope_collection_error=str(error))
            if accepted:
                require(scope['before_after_exact'] and scope.get('snapshot_before_equals_main_before')
                        and len(report.get('preservation', {})) == 9
                        and all(report['preservation'].values()), 'Accepted helper source/preservation scope is not complete')
            for name in ('reviewed-main-bindings.json', 'fixture-identities.json'):
                if (folder / name).is_file():
                    self.copy(folder / name, target + '/' + name)
            private = []
            if report.get('actual_res_root'):
                project = bounded(Path(report['actual_res_root']), folder)
                require(project == folder / 'Studio', 'Helper report points outside its exact fresh snapshot')
                manifest = self.copy(project / 'tests/helper_preview_port_files.json',
                                     target + '/reviewed-port-manifest.json')
                bindings = load(folder / 'reviewed-main-bindings.json')
                checked = []
                for item in manifest.get('files', []):
                    name = rel(item['path'])
                    _, actual = identity(bounded(project / name, project))
                    binding = bindings.get(name, {})
                    checked.append(dict(path=name, actual_sha256=actual['sha256'],
                        reviewed_raw_sha256=item['sha256'],
                        matches_raw_manifest=actual['sha256'] == item['sha256'],
                        matches_actual_run_binding=actual['sha256'] == binding.get('actual_sha256'),
                        reconstruction=binding.get('reconstruction')))
                byte_check = dict(format='has_compact_helper_manifest_byte_check_1', rows=checked,
                                  row_count=len(checked),
                                  all_match_actual_run_bindings=len(checked) == 24 and all(
                                      row['matches_actual_run_binding'] for row in checked))
                require(not accepted or byte_check['all_match_actual_run_bindings'],
                        'Accepted helper 24-file byte check differs from actual report bindings')
                write(self.destination / target / 'manifest-byte-check.json', byte_check)
                qa = project / 'output/helper-preview-qa'
                for case in report.get('results', []):
                    case_label = case.get('label')
                    if not case_label:
                        continue
                    rel(case_label)
                    require('/' not in case_label, 'Job label must be one component')
                    result_path = qa / case_label / 'result.json'
                    if result_path.is_file():
                        self.copy(result_path, target + '/results/' + case_label + '.json')
                private = self.receipts(sorted(qa.rglob('private-receipt.json')), target, accepted)
                self.logs(qa, target)
                self.worker_receipts(qa, target)
            return dict(id=label, kind=kind, folder=descriptor['folder'], scope=descriptor['scope'],
                        status='passed' if accepted else 'failed', checks=report.get('checks'),
                        mode=report.get('mode'), native_requested=report.get('native_requested'),
                        source_context=report.get('source_context'), head=report.get('source_state', {}).get('revision'),
                        preservation=report.get('preservation'), source_scope=scope, private_receipts=private)
        require(kind == 'phase1' and report.get('format') == 'has_wind_review_main_1', 'Wrong Phase1 report format')
        scope = self.source_scope(folder, target, dict(before='source-before.json', after='source-after.json'))
        for name in ('headless-verification.json', 'parse-verification.json'):
            if (folder / name).is_file():
                self.copy(folder / name, target + '/' + name)
        private_paths = []
        for row in report.get('results', []):
            case = row['mode']
            rel(case)
            require('/' not in case, 'Phase1 role must be one component')
            path = folder / case / 'result.json'
            if path.is_file():
                self.copy(path, target + '/results/' + case + '.json')
            private_paths.append(folder / case / 'private-receipt.json')
        private = self.receipts(private_paths, target, accepted)
        self.logs(folder, target)
        return dict(id=label, kind=kind, folder=descriptor['folder'], scope=descriptor['scope'],
                    status='passed' if accepted else 'failed',
                    checks=sum(row.get('checks', 0) for row in report.get('results', [])),
                    headless_checks=sum(row.get('result', {}).get('checks', 0) for row in report.get('headless', [])),
                    source_context='actual main with uncommitted pending-helper edits BEFORE popup fix; not a committed-source pass',
                    head=report.get('revision_before'), source_scope=scope, private_receipts=private)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    options = parser.parse_args()
    plan = load(bounded(options.plan, BASE))
    require(plan.get('format') == 'has_helper_main_compact_evidence_plan_1', 'Wrong evidence plan')
    packet = Packet(options.destination)
    packet.copy(Path(__file__), 'build_packet.py')
    source_index_path = bounded(ROOT / rel(plan['source_index']['path']))
    require(identity(source_index_path)[1]['sha256'] == plan['source_index']['sha256'], 'Frozen driver source index changed')
    packet.copy(source_index_path, 'driver/SOURCE_INDEX.json')
    for group in plan['metadata_groups']:
        for name in group['files']:
            packet.copy(ROOT / rel(group['source']) / rel(name), rel(group['target']) + '/' + name)
    rows = [packet.run(descriptor) for descriptor in plan['runs']]
    private = [row for case in rows for row in case.get('private_receipts', [])]
    desktops = [row['desktop'] for row in private]
    require(len(desktops) == len(set(desktops)), 'Private desktop receipt reuse across listed cases')
    summary = dict(format='has_helper_main_compact_evidence_1', cases=rows,
                   pending_cases=plan.get('pending_cases', []),
                   initial_driver_candidate_source_index=plan['source_index'],
                   captured_context='Actual tests on explicit working-main bytes. No blanket committed-source or full-default pass is inferred.',
                   private_receipt_count=len(private), unique_private_desktops=len(set(desktops)),
                   all_listed_private_receipts_clean=all(row['clean'] for row in private),
                   private_art_or_media_copied=False, main_source_or_Git_edited=False,
                   failed_attempt_policy='Failed runs, if listed, remain under failed/. Published prototype failures from earlier checkpoints remain distinct.',
                   formal_acceptance='No change to human, device, native artist-fidelity or clean-install acceptance is inferred.')
    write(packet.destination / 'summary.json', summary)
    packet.copy(options.plan, 'PLAN.json')
    write(packet.destination / 'METADATA_SOURCES.json', dict(format='has_compact_metadata_sources_1', files=packet.provenance))
    text = ('# Pending-helper main integration evidence\n\n'
            'This packet contains terminal metadata, metrics, source hashes, scoped audits and private-desktop cleanup receipts. '
            'It contains no artwork, model payloads, projects, video, images, runtime installation or large Studio source copy.\n\n'
            'Every case is attributed to its actual source context. Phase1 was run before the popup fix; new helper cases use exact '
            'working-main snapshots with no overlay. A recorded HEAD does not imply those uncommitted edits were already in that commit. '
            'The later committed-source aggregate must be recorded separately.\n\n'
            '`driver/SOURCE_INDEX.json` identifies the initial frozen driver candidate. Later cwd/UI changes are identified by '
            'each actual run\'s reviewed-main bindings and full functional SHA inventory; the initial index is not relabeled as the final source.\n\n'
            'See `summary.json` for actual case results and pending cases, `source-inventories/` for deduplicated functional SHA maps, '
            '`METADATA_SOURCES.json` for copied-record provenance and `INDEX.json` for exact packet bytes. '
            'Raw generated logs remain local; compact marker summaries retain their hashes and failures. '
            'Popup Escape probes and regression checks exercise a Window API boundary, not physical keyboard/device acceptance.\n')
    (packet.destination / 'README.md').write_text(text, encoding='utf-8')
    files = {}
    for path in sorted(packet.destination.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            files[path.relative_to(packet.destination).as_posix()] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    write(packet.destination / 'INDEX.json', dict(format='has_helper_main_evidence_files_1', files=files,
          indexed_files=len(files), indexed_bytes=sum(row['bytes'] for row in files.values())))
    print(json.dumps(dict(packet=str(packet.destination), indexed_files=len(files),
                          indexed_bytes=sum(row['bytes'] for row in files.values()),
                          index_sha256=identity(packet.destination / 'INDEX.json')[1]['sha256']), indent=2))


if __name__ == '__main__':
    main()

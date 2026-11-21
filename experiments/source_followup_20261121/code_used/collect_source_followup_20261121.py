"""Copy the fixed safe source/result allowlist; never run or remove its inputs."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import stat

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT.parent / 'has-body-addition-20261120'
FULL = ROOT.parent / 'has-import-info-full-20261121-2f1acbd'
RUN = FULL / 'output/windows-reference-body-1795270518404649600'
OUTER = FULL / 'output/root-full-launch-1795270518224140000'
FACE = ROOT.parent / 'has-posed-head-native-controls-1795274917964725700'
DEST = ROOT / 'experiments/source_followup_20261121'
PACKETS = {
 'source-junko-stage-a-root-driver-v2-prep-20261121': 'd4ab53c3fa5e747e9a59de8a162e867742ff97904b0628eca410146d2f0a3e5c',
 'source-junko-stage-a-failure-evidence-prep-20261121': 'a6a9ae50b8c372b4fc88dda7f513344b8ffeec3ccbd09fe987ab5695f0483551',
 'source-junko-body-dress-rest-diagnostic-prep-20261121': '8807fe151edd136124c8821db4aa8dbd9490f69325c176cce8ef9618a33d54f3',
 'source-junko-stage-a-rest-diagnostic-v3c-root-driver-prep-20261121': 'ae92f83c942de6d480190b8197bc541fd8ef8004e33af54292291affd8a2be03',
 'source-junko-first-rest-diagnostic25-evidence-prep-20261121': '914ad877ab8afae2f8eda219701f7a73b1c8b2f7f63705cc5e5dd13efa435e17',
 'source-junko-factory-boundary-diagnostic-prep-20261121': '5a07872ec538d18835c01f1f11b83ea24ae69858a9ead03fa0f31c9dd1640974',
 'source-junko-factory-boundary-v4-root-driver-prep-20261121': '20f2dcfd7d95127ab3b139b3cc87a99c74e00aa869a21c672027c40c163a1bcc',
 'source-junko-factory-boundary45-evidence-prep-20261121': '345d3ebaad5ed6cc621295ff587520dbd00378d5858e69c5ec63669706d6edad',
 'source-junko-scratch-rest-representation-v2-prep-20261121': 'da54d107aaeddc2684042b9dd0524db0fbcb24ade9235ece108e9a443348054e',
 'source-junko-scratch-v6-root-driver-prep-20261121': '21251ba82f4e27198fcedc8277439d21d437f279648f16412bbddb93da97713d',
 'source-junko-scratch-v5-failure0-evidence-prep-20261121': '98da6950de7f73bc57d6c07611c5c14bf91a7868540a8bf3d78c3504dc667e1a',
 'source-posed-head-native-2f1acbd-1109-qualification-prep-20261121': '72fc1f2f6626db08bb23e3330f39401b0cf0202dc43df01b433342e16d2e5402',
 'source-easing-2f1acbd-1109-graphics-qualification-prep-20261121': 'f45b2ecefec395b516a974d1c913c9fd4063cc0b35f54696fc55c4c744282552',
 'source-miku-contact-2f1acbd-1109-successor-prep-20261121': '2ee265578b4c1a120c8c04a39386ee23b2797a6b434704a819cac6b2127b949d',
 'source-import03-software-audit-2f1acbd-prep-20261121': 'b9437c3f0d93fef267ff055dac9b595588ad35910372baf7c814d616a6cbceb1',
}
ROOT_FILES = [
 'check_easing_cleanup_ready_20261121.py',
 'remove_verified_easing_cpu_stages_20261121.ps1',
 'remove_verified_easing_cpu_stages_v2_20261121.ps1',
 'verify_cleanup_repository_art_20261121.py',
 'prepare_easing_cleanup_v2_20261121.py',
 'EASING_CLEANUP_EXACT_PREFLIGHT_20261121.json',
 'EASING_CLEANUP_INITIAL_PREFLIGHT_API_REFUSAL_20261121.json',
 'EASING_CLEANUP_PROCESS_CHECK_20261121.json',
 'EASING_CLEANUP_REPOSITORY_ART_BINDING_20261121.json',
 '2F1_LIVE_PICKUP_20261121.json',
 'record_2f1_live_pickup_20261121.py',
 'IMPORT_INFO_REMOTE_VERIFIED_20261121.json',
 'IMPORT_INFO_INDEX_VERIFIED_20261121.json',
 'JUNKO_NATIVE_REST_INVERSE_BIND_COMPARISON_20261121.json',
 'run_2f1_face_qualified_20261121.py',
]
ALLOWED = {'.json', '.md', '.py', '.gd', '.log', '.ps1', '.txt'}
ROWS = {}
SOURCES = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    p = PurePosixPath(value)
    assert isinstance(value, str) and not p.is_absolute() and p.parts
    assert all(x not in ('', '.', '..') for x in p.parts) and '\\' not in value
    assert ':' not in value and value == p.as_posix(), value
    return p


def identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, getattr(s, 'st_file_attributes', 0))


def read(path):
    path = Path(path)
    assert path.is_absolute() and path.is_relative_to(ROOT.parent)
    for parent in (path, *path.parents):
        s = parent.lstat()
        assert not stat.S_ISLNK(s.st_mode) and not getattr(s, 'st_file_attributes', 0) & 0x400, path
        if parent == ROOT.parent:
            break
    s = path.stat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1, path
    data = path.read_bytes()
    assert identity(s) == identity(path.stat()), path
    stamp = (identity(s), sha(data))
    assert path not in SOURCES or SOURCES[path] == stamp, path
    SOURCES[path] = stamp
    return data


def text_only(path, data):
    assert Path(path).suffix.lower() in ALLOWED, path
    assert b'\0' not in data, path
    data.decode('utf-8-sig')
    if Path(path).suffix.lower() == '.json':
        value = json.loads(data)
        def scan(item, trail):
            if isinstance(item, list):
                # None of this fixed source/receipt set needs a raw numeric
                # matrix, skin stream, vertex stream or native pose array.
                assert not (len(item) >= 12 and all(type(x) in (int, float) for x in item)), (path, trail)
                for i, child in enumerate(item):
                    scan(child, trail + '/' + str(i))
            elif isinstance(item, dict):
                for key, child in item.items():
                    scan(child, trail + '/' + key)
        scan(value, '')


def put(rel, data, origin):
    relative(rel)
    assert rel not in ROWS and rel.casefold() not in {p.casefold() for p in ROWS}, rel
    text_only(rel, data)
    path = DEST / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(data)
    assert read(path) == data
    ROWS[rel] = {'path': rel, 'source': origin, 'bytes': len(data), 'sha256': sha(data)}


def copy(path, rel):
    data = read(path)
    put(rel, data, Path(path).as_posix())
    return data


def generated(rel, value):
    put(rel, (json.dumps(value, indent=2) + '\n').encode(), 'collector-derived metadata')


def inner_closure(path):
    manifest = json.loads(read(path))
    rows = manifest['files']
    names = [row['path'] for row in rows]
    assert len(set(names)) == len(names) == len({n.casefold() for n in names})
    for row in rows:
        relative(row['path'])
        data = read(path.parent / row['path'])
        assert len(data) == row['bytes'] and sha(data) == row['sha256'], (path, row['path'])
    return len(rows)


def main():
    assert not DEST.exists(), 'Choose a new archive; no overwrite/delete mode exists.'
    DEST.mkdir(parents=True)
    catalogue = []
    for name, expected_sha in PACKETS.items():
        source = PRIMARY / 'output' / name
        manifest_raw = read(source / 'SOURCE_PINS.json')
        assert sha(manifest_raw) == expected_sha, name
        manifest = json.loads(manifest_raw)
        names = [row['path'] for row in manifest['files']]
        assert len(names) == len(set(names)) == len({n.casefold() for n in names})
        for row in manifest['files']:
            relative(row['path'])
            data = read(source / row['path'])
            assert len(data) == row['bytes'] and sha(data) == row['sha256'], (name, row['path'])
            put('source/' + name + '/' + row['path'], data, (source / row['path']).as_posix())
        put('source/' + name + '/SOURCE_PINS.json', manifest_raw, (source / 'SOURCE_PINS.json').as_posix())
        catalogue.append({'packet': name, 'source_manifest_sha256': expected_sha,
                          'payload_files': len(names), 'restoration': 'output/' + name})
    for name in ROOT_FILES:
        copy(PRIMARY / 'output' / name, 'root/' + name)
    # The two baseline scalar receipts are already committed in 243e6a1e.
    already = {}
    for archived, original in [('baseline_full183.json', 'IMPORT_INFO_FULL183_ROOT_POSTFLIGHT_20261121.json'),
                               ('baseline_cleanup.json', 'EASING_CLEANUP_REMOVED_20261121.json')]:
        path = ROOT / 'experiments/feature_pass_20261121' / archived
        data = read(path)
        assert data == read(PRIMARY / 'output' / original)
        already[original] = {'committed_path': path.relative_to(ROOT).as_posix(),
                             'bytes': len(data), 'sha256': sha(data)}
    for name in ['completion.json', 'launch.json', 'source-before.json', 'source-after.json',
                 'committed-source-blobs.json', 'stderr.log']:
        copy(RUN / name, 'evidence/full/coordinator/' + name)
    for name in ['completion.json', 'launch.json', 'coordinator-stdout.log', 'coordinator-stderr.log']:
        copy(OUTER / name, 'evidence/full/outer/' + name)
    complete = json.loads(read(RUN / 'completion.json'))
    assert complete['exit'] == 0 and complete['result_groups'] == 183
    assert complete['functional_source_count'] == 1109 and complete['unique_current_private_jobs'] == 259
    provenance_raw = read(RUN / 'receipt-provenance.json')
    current = json.loads(provenance_raw)['current']
    assert len(current) == 260 and len({r['value']['desktop'] for r in current}) == 259
    for row in current:
        rel = relative(row['path']).as_posix()
        data = read(FULL / rel)
        assert sha(data) == row['sha256'] and json.loads(data) == row['value']
        put('evidence/full/current-receipts/' + rel, data, (FULL / rel).as_posix())
    generated('evidence/full/CURRENT_RECEIPTS.json', {
        'format': 'has_full183_current_receipt_projection_1',
        'origin': (RUN / 'receipt-provenance.json').as_posix(),
        'origin_bytes': len(provenance_raw), 'origin_sha256': sha(provenance_raw),
        'current_paths': 260, 'unique_jobs': 259, 'current': current,
        'unchanged_prior_archive_rows_omitted': 1795,
    })
    copy(FACE / 'PUBLIC_RESULT.json', 'evidence/face114/PUBLIC_RESULT.json')
    face = json.loads(read(FACE / 'PUBLIC_RESULT.json'))
    assert face['status'] == 'CAPTURED_FOR_PRIVATE_REVIEW'
    assert face['pure_checks'] + face['native_cpu_geometry_checks'] + face['native_capture_controls'] == 114
    for index, case in enumerate(['import', 'envelope-unit', 'control-unit', 'native-cpu-geometry', 'native-captures']):
        folder = FACE / 'Verification' / case
        launch_path = folder / ('job-%d-launch.json' % index)
        launch = json.loads(copy(launch_path, 'evidence/face114/' + case + '/' + launch_path.name))
        copy(Path(launch['private_receipt']), 'evidence/face114/' + case + '/private-receipt.json')
        for label in ['stderr', 'stdout']:
            if case == 'import' and label == 'stdout':
                continue  # Repetitive import progress; no additional assertion result.
            name = 'job-%d-%s.log' % (index, label)
            copy(folder / name, 'evidence/face114/' + case + '/' + name)
        if case != 'import':
            copy(folder / 'engine.log', 'evidence/face114/' + case + '/engine.log')
    excluded = []
    for path, reason in [
        (FULL / 'output/verification.json', 'Native-rich aggregate; full postflight and safe physical receipts retained instead.'),
        (RUN / 'stdout.log', 'Native-rich verifier output; compact coordinator result retained instead.'),
        (RUN / 'receipt-provenance.json', 'Prior archived rows omitted; exact current projection and all physical current receipts retained.'),
        (FACE / 'PRIVATE_COORDINATOR_RESULT.json', 'Private detailed capture configuration/results; public scalar result retained instead.'),
    ]:
        data = read(path)
        excluded.append({'origin': path.as_posix(), 'bytes': len(data), 'sha256': sha(data), 'reason': reason})
    generated('CATALOGUE.json', {'base_revision': '243e6a1edf1aee5cd07f107a34775db49a2caa01',
              'source_packets': catalogue, 'already_committed_scalar_receipts': already,
              'excluded_known_reports': excluded, 'originals_or_stages_deleted': False,
              'runtime_or_gpu_executed_by_collector': False})
    copy(Path(__file__).resolve(), 'code_used/collect_source_followup_20261121.py')
    readme = '''# Remaining source and results, 2026-11-21

Source backup after committed feature batch243e6a1e. Original output folders and
runtime stages were read only; nothing was deleted, installed, run or merged.
The source packet names and every frozen SOURCE_PINS closure remain unchanged.
Copy a complete source/<packet> subtree back to output/<packet> in an appropriate
owned checkout to recover it. CATALOGUE.json records those restoration names.
The historical launchers still require their exact original source revisions,
tools, private inputs and admission evidence; these are source backups, not new
launch approvals or a claim that old hosts accept243e6a1e.

## Actual results and unrun work

- The2f1 baseline Full passed183 groups/1109 functional sources,21 movie groups
  and259 unique private jobs in3991.586278 seconds. Its exact coordinator/outer
  records, source catalogues and260 physical receipt paths (one duplicate job)
  are retained. The large native-rich aggregate and verifier stdout are excluded.
  The714-byte independent Root postflight and1592-byte cleanup receipt are
  already committed under experiments/feature_pass_20261121; CATALOGUE binds
  their exact bytes. The older2F1_LIVE_PICKUP note is historical and its running
  status is superseded by this completed result. Prior435/c315 Fulls stay failed.
- StageA: pure16 passed, Body conversion failed the unchanged native-rest
  predicate at index38; Dress did not start. No successful conversion claimed.
- Rest diagnostic25 and factory-boundary45 are expected-refusal diagnostics,
  including their old controls (45 includes25, not70). Their two jobs closed
  each time, with strict refusal unchanged. Scalars, unit logs and ownership
  records are kept; private matrices/names/full conversion logs are excluded.
- Scratchv5 failed its12-test batch (one mock tuple/list expectation); no
  Blender was started. Eleven individual methods passing is not a passing batch.
  Frozen scratchv6/v2 fixture preparation remains unrun in this archive.
- The separate face114 experiment captured16 private images and passed its
  CPU/control assertions. It did not qualify a visual fix. Root's later visual
  assessment identified a head-only result with the rest of the body missing;
  that adverse observation must not be promoted to whole-character restoration.
  The subsequent ordinary Model integration and its separate face/body checks
  are recorded in the already committed feature_pass_20261121 evidence.
- Easing/Miku/IMPORT03 successor preparations keep their original source-only
  states. Later shipping easing/Model changes and their focused results are
  distinct, already committed in243e6a1e. This backup does not rerun or retag them.

## Privacy and recovery scope

Only explicit frozen text sources, source catalogues, safe scalar findings,
test-label logs and process receipts are copied. No HAS/GLB/MDL/VRM/PMX, image,
archive, executable, imported cache, SDK/runtime tree, native vertex/skin/collider
array, private matrix capture or private project configuration is included.
CONTENTS.json binds exact membership/bytes/SHA256, excluding itself; every nested
SOURCE_PINS.json is checked against its archived payload. Git naturally deduplicates
identical historical bytes. This is recoverability/source screening, not another
runtime qualification or general semantic privacy certification.
'''
    put('README.md', readme.encode(), 'collector-authored scope/status note')
    inner_count = 0
    for path in DEST.rglob('SOURCE_PINS.json'):
        inner_closure(path)
        inner_count += 1
    # Final exact membership and repeat identity/hash checks before inventory.
    actual = {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}
    assert actual == set(ROWS)
    for path, expected in list(SOURCES.items()):
        data = read(path)
        assert SOURCES[path] == expected and sha(data) == expected[1], path
    inventory = {'format': 'has_source_followup_archive_1',
                 'base_revision': '243e6a1edf1aee5cd07f107a34775db49a2caa01',
                 'files': [ROWS[p] for p in sorted(ROWS)],
                 'payload_files': len(ROWS), 'payload_bytes': sum(r['bytes'] for r in ROWS.values()),
                 'frozen_top_packets': len(PACKETS), 'verified_inner_source_manifests': inner_count,
                 'native_art_or_private_arrays_included': False,
                 'runtime_or_gpu_executed': False, 'originals_deleted': False}
    data = (json.dumps(inventory, indent=2) + '\n').encode()
    with (DEST / 'CONTENTS.json').open('xb') as f:
        f.write(data)
    assert json.loads((DEST / 'CONTENTS.json').read_bytes()) == inventory
    print(json.dumps({'archive': str(DEST), 'payload_files': len(ROWS),
                      'payload_bytes': inventory['payload_bytes'], 'total_files': len(ROWS)+1,
                      'contents_bytes': len(data), 'contents_sha256': sha(data),
                      'inner_source_manifests': inner_count}, indent=2))


if __name__ == '__main__':
    main()

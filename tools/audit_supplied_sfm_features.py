"""Audit supplied archive identities and optional retained Mima feature metadata.

Reads exact checksum-bound archive names from the committed provenance receipt.
Does not extract archives, execute native readers/model scripts, launch apps or
access the network. Produces a new metadata-only JSON file; never replaces one.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = 'docs/benchmarks/sfm_uploaded_samples_2026-11-07.json'
CORPUS = 'docs/benchmarks/supplied_source_corpus_2026-11-08.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    before = path.stat()
    value = {'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns, 'sha256': digest(path)}
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input changed while reading: ' + str(path))
    return value


def load(path, maximum=16 * 1024 * 1024):
    if path.stat().st_size > maximum:
        raise ValueError('Metadata report exceeds its size budget: ' + str(path))
    return json.loads(path.read_bytes())


def mima_metadata(report_path, inputs):
    pilot = load(report_path)
    inputs[report_path] = identity(report_path)
    native = pilot['parameters']['native_parameters']
    stage = (Path(pilot['folder']) / 'stage').resolve(strict=True)
    staged = []
    for member, expected in pilot['staged_sha256'].items():
        if Path(member).suffix.lower() not in ('.mdl', '.vvd'):
            continue
        path = (stage / member).resolve(strict=True)
        if not path.is_relative_to(stage):
            raise ValueError('Retained Mima member escapes its stage')
        current = identity(path)
        inputs[path] = current
        if current['sha256'] != expected:
            raise ValueError('Retained Mima member hash differs: ' + member)
        staged.append({'member': member, **current, 'matches_recorded_sha256': True})
    glb = (Path(pilot['bundle']) / 'scene.glb').resolve(strict=True)
    if glb.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('Retained Mima GLB exceeds128MiB')
    current = identity(glb)
    inputs[glb] = current
    if current['sha256'] != pilot['glb_sha256']:
        raise ValueError('Retained Mima GLB hash differs')
    with glb.open('rb') as stream:
        header = stream.read(20)
        if len(header) != 20 or struct.unpack('<4sIIII', header)[:3] != (b'glTF', 2, current['bytes']):
            raise ValueError('Invalid retained GLB header')
        length, kind = struct.unpack_from('<II', header, 12)
        if kind != 0x4e4f534a or length > 16 * 1024 * 1024 or length + 20 > current['bytes']:
            raise ValueError('Invalid retained GLB JSON bounds')
        document = json.loads(stream.read(length))
    names = ['Eyebrows raise', ' blink', 'mouth angry open', 'remove eye highlight ',
             'Eyebrows raise L', 'Eyebrows raise R', 'blink L', 'blink R']
    if not all(name in [row['name'] for row in native['flex_controllers']] for name in names):
        raise ValueError('Retained Mima native controller identities differ')
    return {'archive_sha256': pilot['source_sha256'], 'staged_identity': staged,
            'glb': {'path': str(glb), **current}, 'bones': len(native['bones']),
            'flex_controllers': len(native['flex_controllers']), 'flex_descriptors': len(native['flex_names']),
            'bodygroups': native['bodygroups'], 'selected_bodygroups': native['selected_bodygroup_indices'],
            'skin_families': len(native['skin_groups']), 'selected_skin': native['selected_skin'],
            'selected_exact_controller_names': names,
            'hair_named_bone_examples': [{'index': i, **bone} for i, bone in enumerate(native['bones'])
                                         if 'hair' in bone['name'].lower()][:12],
            'prepared_mesh_target_counts': [{'mesh': i, 'name': mesh.get('name'),
                                             'targets': len(mesh['primitives'][0].get('targets', []))}
                                            for i, mesh in enumerate(document['meshes'])],
            'limits': pilot['parameters']['limits'],
            'scope': 'Existing report and GLB JSON inspected; no new native comparison or app test.'}


def audit(archive_root, mima_report=None):
    archive_root = Path(archive_root).resolve(strict=True)
    if not archive_root.is_dir():
        raise ValueError('Archive root must be a directory')
    baseline = load(ROOT / PROVENANCE)
    corpus = load(ROOT / CORPUS)
    inputs, archives = {}, []
    for row in baseline['archives_provenance']:
        if Path(row['name']).name != row['name']:
            raise ValueError('Invalid committed archive basename')
        path = (archive_root / row['name']).resolve(strict=True)
        if path.parent != archive_root:
            raise ValueError('Archive resolves outside the selected root')
        current = identity(path)
        inputs[path] = current
        if current['sha256'] != row['sha256'] or current['bytes'] != row['bytes']:
            raise ValueError('Supplied archive identity differs: ' + row['name'])
        archives.append({'name': row['name'], 'path': str(path), **current,
                         'historical_models': row['models'], 'matches_recorded_hash_and_size': True})
    conversions = []
    for index, row in enumerate(corpus['conversions']):
        source = row.get('source')
        conversions.append({'index': index, 'historical_member': source.removeprefix('/workspace/has-private-sfm/') if source else None,
                            'historical_bundle': row['bundle'], 'source_sha256': row['source_sha256'],
                            'counts': row['counts'], 'warnings': row.get('warnings', [])})
    report = {'format': 'has_sfm_extra_feature_review_1', 'date': datetime.now(timezone.utc).date().isoformat(),
              'scope': 'Read-only local identity and existing-evidence review. No extraction, native decoder execution, conversion, app/GPU run or feature acceptance.',
              'archives': archives,
              'historical_corpus': {'date': '2026-11-08', 'archives': corpus['archives'], 'models': corpus['models'],
                                    'distinct_recorded_mdl_sha256': len({row['source_sha256'] for row in conversions}),
                                    'successful_default_conversions': corpus['successful_conversions'],
                                    'scope': corpus['scope'], 'conversions': conversions}}
    if mima_report is not None:
        report['current_mima_metadata'] = mima_metadata(Path(mima_report).resolve(strict=True), inputs)
    for path, before in inputs.items():
        if identity(path) != before:
            raise ValueError('Reviewed input changed: ' + str(path))
    evidence = [PROVENANCE, CORPUS, 'docs/sfm_sample_corpus.md', 'tools/blender_source_bridge.py']
    report['evidence'] = [{'path': name, 'sha256': digest(ROOT / name)} for name in evidence]
    report['preservation'] = {'archive_checks': len(archives), 'archive_sha256_and_size_match_historical': True,
                              'all_reviewed_input_sha256_bytes_mtime_unchanged': True, 'source_writes': False,
                              'extraction': False, 'app_gpu_runs': False, 'network': False}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mima-report', type=Path)
    args = parser.parse_args()
    source = args.archive_root.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or args.output.is_symlink() or output.is_relative_to(source):
        parser.error('Choose a new JSON file outside the original archive directory')
    report = audit(source, args.mima_report)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output': str(output), 'archives': len(report['archives']),
                      'distinct_mdl_hashes': report['historical_corpus']['distinct_recorded_mdl_sha256'],
                      'inputs_unchanged': True}))


if __name__ == '__main__':
    main()

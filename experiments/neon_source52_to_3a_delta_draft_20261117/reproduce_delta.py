"""Reproduce unreviewed 3a metadata and raw/canonical maps; full is Root-reported running."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
CORE = ROOT / 'experiments/neon_owner_review_executor_20261117/admission_core.py'
CORE_SHA = 'cdad5359f6fe6bf63d93bd95845680dec7f6eb2d041b265d05b05efe3ce1096f'
OLD_MAP = ROOT / 'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
NEW_MAP = ROOT / 'experiments/neon_windows_3a3701a_20261117/active-observation/source-before.json'
OLD_PIN = '4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7'
NEW_PIN = '3ef2e7d8bed6e063afef59c8caccba914663752998761350c882fd4efbc78e9d'
OUTPUT = HERE / 'DRAFT52_TO_3A_DELTA.json'
SCOPE = ('src', 'tests', 'tools', 'data', 'examples')
TOP = ('project.godot', 'main.tscn', 'run.py', 'launch.pyw')
CORES = ('src/model.gd', 'src/source_bone_bindings.gd', 'src/scene3d.gd')
REVIEWED_696 = ROOT / 'experiments/neon_source52_to_696_root_review_20261117/REVIEWED52_TO_CANDIDATE_DELTA.json'
REVIEWED_696_SHA = '4ae44f24c02fc0fb801dc792e1b2025541e478beea6387c51f0fdefacf072ff6'
REVIEWED_696_INDEX_SHA = 'fb1e75534468a71f524fd2c481e45c4a36d5a701de4f762045a612e2a9e3a65d'
REASON_ADDITIONS = {'tests/color_sampler_smoke.gd': 'Aim the native color fixture click at the center of the same expected output pixel using click(native_point+Vector2(.5,.5)). Keep reference_pixel.get_pixel(int(native_point.x),int(native_point.y)) unchanged. This avoids the measured boundary round-trip/floor selecting the neighboring Y pixel; all 44 checks, thresholds and three native fixture cases remain unchanged. Sampler/app/helper/wind code and every other prior696 functional byte remain unchanged.'}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def read(path):
    for item in (path, *path.parents):
        info = item.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return raw


def inventory(folder):
    names = {path.relative_to(folder).as_posix() for part in SCOPE for path in (folder / part).rglob('*')
             if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts}
    return names | set(TOP)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare with the existing draft without writing')
    args = parser.parse_args()
    assert sha(read(CORE)) == CORE_SHA
    spec = importlib.util.spec_from_file_location('unchanged_draft_delta_core', CORE)
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    reviewed_raw = read(REVIEWED_696); assert sha(reviewed_raw) == REVIEWED_696_SHA
    reviewed_index_raw = read(REVIEWED_696.with_name('INDEX.json')); assert sha(reviewed_index_raw) == REVIEWED_696_INDEX_SHA
    reviewed_index = A.parse(reviewed_index_raw)
    reviewed_row, = [row for row in reviewed_index['files'] if row['path'] == REVIEWED_696.name]
    assert reviewed_row['sha256'] == REVIEWED_696_SHA and reviewed_row['bytes'] == len(reviewed_raw)
    reviewed = A.parse(reviewed_raw); assert reviewed['review_status'] == 'ROOT_REVIEWED_EXPLICIT_SOURCE_DELTA'
    assert reviewed['candidate_manifest_commit'] == '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
    reasons = dict(reviewed['reasons'])
    for name, reason in REASON_ADDITIONS.items():
        assert name not in reasons
        reasons[name] = reason
    old_raw, new_raw = read(OLD_MAP), read(NEW_MAP)
    assert sha(old_raw) == OLD_PIN == A.SOURCE52_SHA and sha(new_raw) == NEW_PIN
    old_doc, new_doc = A.parse(old_raw), A.parse(new_raw)
    assert old_doc['commit'] == '52f63c944ded7a651da871524d23a345b606424d'
    assert new_doc['commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07'
    tables = []
    for folder, doc, count in ((ROOT, old_doc, 1019), (REVIEW, new_doc, 1029)):
        manifest = doc['source_sha256']; assert len(manifest) == count and inventory(folder) == set(manifest)
        table = {}
        for name, expected in sorted(manifest.items()):
            assert not Path(name).is_absolute() and '..' not in Path(name).parts and '\\' not in name and ':' not in name
            raw = read(folder / name); assert sha(raw) == expected, name
            table[name] = {'raw_sha256': expected, 'content_sha256': sha(A.canonical(raw, name))}
        tables.append(table)
    old, new = tables; assert set(old) <= set(new)
    rows = []; eol = []
    for name, value in sorted(new.items()):
        previous = old.get(name)
        if previous is not None and previous['content_sha256'] == value['content_sha256']:
            if previous['raw_sha256'] != value['raw_sha256']:
                eol.append({'path': name, 'old_raw_sha256': previous['raw_sha256'], 'new_raw_sha256': value['raw_sha256'], 'content_sha256': value['content_sha256']})
            continue
        rows.append({'path': name, 'classification': 'added' if previous is None else 'modified',
                     'old_raw_sha256': previous['raw_sha256'] if previous else None,
                     'old_content_sha256': previous['content_sha256'] if previous else None,
                     'new_raw_sha256': value['raw_sha256'], 'new_content_sha256': value['content_sha256']})
    assert set(reasons) == {row['path'] for row in rows}
    previous_rows = {row['path']: row for row in reviewed['rows']}
    assert {row['path'] for row in rows if row != previous_rows.get(row['path'])} == set(REASON_ADDITIONS)
    assert {row['path'] for row in rows} == set(previous_rows) | set(REASON_ADDITIONS)
    assert all(next(row for row in rows if row['path'] == name) == previous for name, previous in previous_rows.items())
    assert old['tests/color_sampler_smoke.gd']['raw_sha256'] == '7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
    assert new['tests/color_sampler_smoke.gd']['raw_sha256'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'
    assert eol == reviewed['raw_EOL_only_differences_excluded_from_delta_rows']
    summary = A.check_reviewed_delta(old, new, rows)
    core = {name: {'old_raw_sha256': old[name]['raw_sha256'], 'new_raw_sha256': new[name]['raw_sha256'],
                   'canonical_content_sha256': new[name]['content_sha256'],
                   'raw_byte_exact': old[name]['raw_sha256'] == new[name]['raw_sha256'],
                   'canonical_content_exact': old[name]['content_sha256'] == new[name]['content_sha256']} for name in CORES}
    assert all(value['canonical_content_exact'] for value in core.values())
    assert core['src/model.gd']['raw_byte_exact'] and core['src/scene3d.gd']['raw_byte_exact']
    assert not core['src/source_bone_bindings.gd']['raw_byte_exact']
    encode = lambda value: (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')
    map_docs = {
        'OLD52_RAW_CANONICAL_MAP.json': {'format': 'has_functional_raw_canonical_source_map_1', 'commit': old_doc['commit'],
            'functional_files': len(old), 'raw_manifest_sha256': OLD_PIN, 'canonicalizer_sha256': CORE_SHA, 'files': old},
        'CANDIDATE3A_RAW_CANONICAL_MAP.json': {'format': 'has_functional_raw_canonical_source_map_1', 'commit': new_doc['commit'],
            'functional_files': len(new), 'raw_manifest_sha256': NEW_PIN, 'canonicalizer_sha256': CORE_SHA, 'files': new},
    }
    map_bodies = {name: encode(value) for name, value in map_docs.items()}
    result = {'format': 'has_reviewed52_to_qualified_Neon_delta_1', 'review_status': 'DRAFT_NOT_ROOT_REVIEWED',
        'activation_status': 'NOFULL_OR_MERGE_ACTIVATION', 'reasons_status': 'DRAFT_EACH_REASON_REQUIRES_ROOT_CONTENT_REVIEW',
        'full_run_status': 'FULL_RUNNING', 'full_run_status_source': 'ROOT_REPORTED_AT_PREPARATION_NOT_OBSERVED_HERE',
        'root_metadata_checkpoint_label_root_reported': '855d67fe44868793a29d6c6c75c61c0ba86236d2', 'root_metadata_checkpoint_is_not_runtime_source_identity': True,
        'reason_provenance': {'reviewed696_path': str(REVIEWED_696), 'reviewed696_sha256': REVIEWED_696_SHA,
            'reviewed696_INDEX_sha256': REVIEWED_696_INDEX_SHA, 'prior_review_status_does_not_transfer_to3a': True,
            'new_reason_only': sorted(REASON_ADDITIONS), 'all38_reviewed696_reasons_carried_forward_exactly_as_DRAFT': True},
        'old_manifest_commit': old_doc['commit'], 'candidate_manifest_commit': new_doc['commit'],
        'future_merged_main_revision': None, 'old_manifest_path': str(OLD_MAP), 'old_manifest_sha256': OLD_PIN,
        'candidate_immutable_before_path': str(NEW_MAP), 'candidate_immutable_before_sha256': NEW_PIN,
        'sealed_admission_core_sha256': CORE_SHA, 'canonicalization': 'unchanged admission_core.canonical',
        'raw_canonical_source_map_files': {name: {'bytes': len(body), 'sha256': sha(body)} for name, body in map_bodies.items()},
        'rows': rows, 'reasons': {name: 'DRAFT: ' + reason for name, reason in sorted(reasons.items())},
        'exact_delta_schema_and_byte_map_join': summary, 'raw_EOL_only_differences_excluded_from_delta_rows': eol,
        'counts': {'added': sum(row['classification'] == 'added' for row in rows), 'modified_content': sum(row['classification'] == 'modified' for row in rows),
                   'raw_EOL_only': len(eol), 'unchanged_raw': len(old) - sum(row['classification'] == 'modified' for row in rows) - len(eol)},
        'old52_to_candidate_core_status': core, 'native_to52_exact_core_guard_separate_and_not_reopened_here': True,
        'current_main_functional_bytes_join_actual52_manifest': True, 'candidate_bytes_join_public_immutable_before_copy_only': True,
        'full_result_release_merge_copy_or187_qualified': False, 'original_source_or_guard_mutated': False,
        'other_active_outputs_native_originals_Git_or_processes_read': False, 'reproducer_sha256': sha(read(Path(__file__)))}
    for folder, doc in ((ROOT, old_doc), (REVIEW, new_doc)):
        assert inventory(folder) == set(doc['source_sha256'])
        assert all(sha(read(folder / name)) == expected for name, expected in doc['source_sha256'].items())
    assert sha(read(CORE)) == CORE_SHA and sha(read(OLD_MAP)) == OLD_PIN and sha(read(NEW_MAP)) == NEW_PIN
    assert sha(read(REVIEWED_696)) == REVIEWED_696_SHA and sha(read(REVIEWED_696.with_name('INDEX.json'))) == REVIEWED_696_INDEX_SHA
    expected_files = {**map_bodies, OUTPUT.name: encode(result)}
    if args.check:
        for name, body in expected_files.items():
            assert read(HERE / name) == body, 'Draft/map differs from exact reproduction: ' + name
    else:
        for name, body in expected_files.items():
            with (HERE / name).open('xb') as stream: stream.write(body)
    print(json.dumps({'draft': str(OUTPUT), 'sha256': sha(read(OUTPUT)), 'counts': result['counts'],
                      'delta_rows': len(rows), 'sealed_checker_accepted_exact_schema': True,
                      'review_status': result['review_status'], 'activation_status': result['activation_status']}))


if __name__ == '__main__': main()

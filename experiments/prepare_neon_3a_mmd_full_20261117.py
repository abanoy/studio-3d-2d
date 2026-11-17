"""Reserve a fresh unchanged3a full after the missing owner MMD fixture is restored."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
OLD_RUN = REVIEW / 'output/windows-neon-3a3701a-20261117T185401541257'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-lane-closed', action='store_true', required=True)
    parser.add_argument('--closure', type=Path, required=True)
    parser.add_argument('--closure-sha256', required=True)
    parser.add_argument('--pose-verification', type=Path, required=True)
    parser.add_argument('--pose-verification-sha256', required=True)
    args = parser.parse_args()
    assert args.closure.parent.resolve() == OLD_RUN.resolve()
    assert sha(args.closure) == args.closure_sha256
    closure = json.loads(args.closure.read_bytes())
    assert closure['released'] is True and closure['full_suite_passed'] is False
    assert closure['source_commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07'
    assert closure['canonical_run'] == OLD_RUN.name
    assert closure['all_collected_jobs_desktops_closed_private'] is True
    assert closure['all_inline_exact_physical_matches'] is True
    assert closure['root_observer_issued_no_termination'] is True
    assert args.pose_verification.parent.parent.resolve() == (REVIEW / 'output').resolve()
    assert args.pose_verification.parent.name.startswith('neon-mmd-pose-3a-')
    assert args.pose_verification.name == 'verification.json'
    assert sha(args.pose_verification) == args.pose_verification_sha256
    pose = json.loads(args.pose_verification.read_bytes())
    assert pose['passed'] is True and pose['host_scopes_closed'] is True
    assert pose['all_functional_source_unchanged'] is True and pose['functional_source_files'] == 1029
    assert pose['full_suite_pass_claimed'] is False
    row, = pose['rows']
    assert row['label'] == 'pose' and row['exit'] == 0 and row['retained_Popen_reaped'] is True
    assert row['timed_out'] is False
    assert row['report']['actual_mmd_tested'] is True and row['report']['checks'] == 45
    assert row['report']['failures'] == 0 and len(row['report']['movies']) == 2
    fixture_path = ROOT / 'output/PRIVATE-neon-mmd-pose-fixture-stage-20261117/PROVENANCE.json'
    fixture = json.loads(fixture_path.read_bytes())
    assert fixture['files'] == 18 and fixture['all_originals_preserved'] is True and fixture['all_copies_equal'] is True
    assert fixture['closure_sha256'] == args.closure_sha256
    identities = {}
    for item in fixture['rows']:
        for folder, role in ((Path(fixture['source']), 'source'), (Path(fixture['target']), 'copy')):
            path = folder / item['relative']
            info = path.stat()
            assert all(getattr(info, name) == value for name, value in item[role]['identity'].items())
            assert sha(path) == item[role]['sha256']
            identities[str(path)] = {'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns, 'sha256': sha(path)}
    # The unchanged canonical pose test saves/reopens this owned output project.
    # Only its two generated metadata files differ from the original36-copy stage.
    generated_names = {'pose-smoke/miku-project/project.json',
                       'pose-smoke/miku-project/project.backup.json'}
    stage = json.loads((ROOT / 'experiments/neon_windows_original_20261116/NATIVE_FIXTURE_STAGE.json').read_bytes())
    def identity(path):
        before = path.stat()
        assert not path.is_symlink() and not getattr(before, 'st_file_attributes', 0) & 0x400
        digest = sha(path)
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
        return {'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns, 'sha256': digest}
    generated = {}
    assert stage['files'] == 36
    for name, expected in stage['source_projects'].items():
        assert identity(ROOT / 'output' / name) == expected
        actual = identity(REVIEW / 'output' / name)
        if name in generated_names:
            assert actual['sha256'] != expected['sha256'] and actual['bytes'] <= 1024 * 1024
            generated[name] = actual
        else:
            assert actual == expected
    assert set(generated) == generated_names
    pose_source = REVIEW / 'tests/pose_smoke.gd'
    tested_map = json.loads((OLD_RUN / 'source-before.json').read_bytes())['source_sha256']
    assert sha(pose_source) == tested_map['tests/pose_smoke.gd']
    assert 'app.project_folder = folder.path_join("miku-project"); app.save()' in pose_source.read_text(encoding='utf-8')
    preservation = args.pose_verification.parent / 'root-preserved-generated-mmd-metadata'
    preservation.mkdir(exist_ok=False)
    for name, expected in generated.items():
        source = REVIEW / 'output' / name
        assert identity(source) == expected
        target = preservation / Path(name).name
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        shutil.copystat(source, target, follow_symlinks=False)
        assert identity(source) == identity(target) == expected
    with (preservation / 'PROVENANCE.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'format': 'has_private_canonical_pose_generated_metadata_1',
                   'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'generated_by_canonical_source': 'tests/pose_smoke.gd',
                   'generated_by_source_sha256': sha(pose_source),
                   'focused_verification_sha256': args.pose_verification_sha256,
                   'original36_preserved': True, 'other34_review_copies_unchanged': True,
                   'generated_review_metadata': generated, 'input_reconstruction_or_pin_refresh': False}, stream, indent=2)
        stream.write('\n')
    parent = ROOT / 'experiments/prepare_neon_3a3701a_full_actual_20261117.py'
    original = parent.read_bytes()
    assert hashlib.sha256(original).hexdigest() == 'd1b6cc69e22d79e5d77ce21a34d75a208f97196e1be49b1637d6122b66ec12cf'
    replacements = (
        (b"'windows-neon-3a3701a-'", b"'windows-neon-3a3701a-mmd-'"),
        (b"'experiments/neon_windows_3a3701a_20261117'", b"'experiments/neon_windows_3a3701a_mmd_20261117'"),
        (b"    assert audit.identity(ROOT / 'output' / name) == expected and audit.identity(REVIEW / 'output' / name) == expected",
         b"    assert audit.identity(ROOT / 'output' / name) == expected\n    assert audit.identity(REVIEW / 'output' / name) == ROOT_GENERATED_POSE_METADATA.get(name, expected)"),
        (b"record = {'format':", b"extra.update(ROOT_MMD_FIXTURE_IDENTITIES)\nrecord = {'format':"),
        (b"'result': 'UNRUN'}", b"'result': 'UNRUN', 'restored_owner_mmd_fixture_files': 18, 'focused_native_mmd_checks': 45, 'focused_native_mmd_movies': 2, 'preceding_incomplete_full_qualification': 'UNQUALIFIED_MISSING_OWNER_MMD_FIXTURE', 'preceding_incomplete_closure_sha256': ROOT_MMD_CLOSURE_SHA256, 'focused_native_mmd_verification_sha256': ROOT_MMD_POSE_SHA256, 'declared_generated_pose_project_metadata': ROOT_GENERATED_POSE_METADATA, 'all36_original_fixture_inputs_preserved': True, 'other34_review_fixture_copies_unchanged': True}"),
    )
    modified = original
    for old, new in replacements:
        assert modified.count(old) == 1
        modified = modified.replace(old, new, 1)
    inverse = modified
    for old, new in reversed(replacements):
        assert inverse.count(new) == 1
        inverse = inverse.replace(new, old, 1)
    assert inverse == original
    scope = {'__file__': str(parent), '__name__': 'root_mmd_full_reservation',
             'ROOT_MMD_FIXTURE_IDENTITIES': identities,
             'ROOT_GENERATED_POSE_METADATA': generated,
             'ROOT_MMD_CLOSURE_SHA256': args.closure_sha256,
             'ROOT_MMD_POSE_SHA256': args.pose_verification_sha256}
    exec(compile(modified, str(parent), 'exec'), scope)


if __name__ == '__main__':
    main()

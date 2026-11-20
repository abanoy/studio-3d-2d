from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '9e3b039039833adce4723bbb70681595cd4eef16'
PACKETS = [
    'reference_body_full_20261120',
    'source_export_hook_20261120',
    'source_current_native_ids_20261120',
    'source_current_native_ids_failed_20261120',
    'source_clone_cleanup_20261120',
]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    packets = []
    for name in PACKETS:
        folder = ROOT / 'experiments' / name
        manifests = list(folder.rglob('CONTENTS.json'))
        assert manifests, name
        for manifest in manifests:
            data = json.loads(manifest.read_bytes())
            for row in data['files']:
                target = manifest.parent / row['path']
                assert target.resolve().is_relative_to(folder.resolve()), target
                assert not target.is_symlink(), target
                raw = target.read_bytes()
                assert len(raw) == row['bytes'] and digest(raw) == row['sha256'], str(target)
        root_manifest = json.loads((folder / 'CONTENTS.json').read_bytes())
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        expected = {r['path'] for r in root_manifest['files']} | {'CONTENTS.json'}
        assert actual == expected, {'packet': name, 'extra': sorted(actual-expected), 'missing': sorted(expected-actual)}
        packets.append(dict(path=folder.relative_to(ROOT).as_posix(), files=len(actual),
                            bytes=sum((folder / p).stat().st_size for p in actual),
                            contents_sha256=digest((folder / 'CONTENTS.json').read_bytes())))
    preserved = []
    for name in ('LLM.md', 'docs/progress_memo.md'):
        original = git('show', BASE + ':' + name)
        current = (ROOT / name).read_bytes()
        assert current.startswith(original), name
        preserved.append(dict(path=name, original_bytes=len(original), prefix_exact=True,
                              added_bytes=len(current)-len(original)))
    original = json.loads(git('show', BASE + ':docs/completion_checklist.json'))
    current = json.loads((ROOT / 'docs/completion_checklist.json').read_bytes())
    fields = ('id', 'category', 'implementation', 'verification', 'acceptance_status', 'external_dependencies')
    assert [{k:r[k] for k in fields} for r in original['requirements']] == [{k:r[k] for k in fields} for r in current['requirements']]
    assert len(current['requirements']) == 62
    functional = ['src', 'tools', 'tests', 'data', 'examples', 'project.godot', 'export_presets.cfg',
                  'experiments/reference_body_20261120/run_full.py',
                  'experiments/reference_body_20261120/run_scoped.py',
                  'experiments/reference_body_20261120/run_units.py',
                  'experiments/reference_body_20261120/run_native.py',
                  'experiments/reference_body_20261120/receipt_provenance.py',
                  'experiments/reference_body_20261120/test_receipt_provenance.py']
    assert not git('diff', BASE, '--', *functional).strip(), 'Functional source changed after full Windows pass'
    snapshot = json.loads((ROOT / 'experiments/reference_body_full_20261120/source-after.json').read_bytes())
    committed = json.loads((ROOT / 'experiments/reference_body_full_20261120/committed-source-blobs.json').read_bytes())
    assert set(snapshot) == set(committed) and len(snapshot) == 1061
    for name, row in snapshot.items():
        target = ROOT / name
        before = target.stat()
        raw = target.read_bytes()
        after = target.stat()
        # Reading legitimately changes access time on this Windows filesystem.
        # Preserve the actual content/identity/modification-time contract.
        fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_mode')
        assert tuple(getattr(before, k) for k in fields) == tuple(getattr(after, k) for k in fields), name
        assert len(raw) == row['bytes'] and after.st_mtime_ns == row['mtime_ns'], name
        assert digest(raw) == row['sha256'], name
        git_sha = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert git_sha == row['git_sha1'] == committed[name], name
    result = dict(format='has_body_full_source_publication_preflight_1', base=BASE,
                  packets=packets, history_prefixes=preserved, stable_requirements=62,
                  statuses_unchanged=True, functional_sources_unchanged=True,
                  exact_full_source_files=len(snapshot))
    (ROOT / 'output/body-publication-preflight-20261120.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()

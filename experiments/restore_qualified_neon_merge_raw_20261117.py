"""Root only: restore tested raw text bytes after the qualified three-way merge."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-3a3701a-mmd-20261117T200622956559'
REV = '3a3701ab6edfa81dc883759403c170b8555aab07'
PARENT = 'f21b9ec85ae63006d036ca7a21c5c82e53fda019'
SCOPE = ('src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw')
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=ROOT, **kwargs)


def source_map(folder):
    files = [p for name in SCOPE[:5] for p in (folder / name).rglob('*')
             if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts]
    files += [folder / name for name in SCOPE[5:]]
    return {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in files}


def main():
    release = json.loads((RUN / 'graphics-lease-closed.json').read_bytes())
    assert release['released'] is True and release['full_suite_passed'] is True
    assert release['source_commit'] == REV
    assert git('rev-parse', 'HEAD').strip().decode() == PARENT
    assert git('rev-parse', 'MERGE_HEAD').strip().decode() == REV
    assert git('diff', '--name-only', '--diff-filter=U', '--', 'LLM.md', *SCOPE).strip() == b'LLM.md'
    expected = json.loads((RUN / 'source-before.json').read_bytes())['source_sha256']
    assert len(expected) == 1029 and source_map(REVIEW) == expected
    assert set(source_map(ROOT)) == set(expected)
    core = ROOT / 'experiments/neon_owner_review_after_qualified_merge_20261117'
    index_raw = (core / 'INDEX.json').read_bytes()
    assert sha(index_raw) == '5479aeea2485e6221589e874053e37197d66bc3dc8dd4acb86c8d53ec144715d'
    index = json.loads(index_raw)
    row = next(row for row in index.get('files', index.get('payloads')) if row['path'] == 'admission_core.py')
    code = (core / 'admission_core.py').read_bytes()
    assert len(code) == row['bytes'] and sha(code) == row['sha256']
    tree = ast.parse(code)
    definitions = [node for node in tree.body if
        (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'TEXT', 'TEXT_PATHS'} for t in node.targets))
        or (isinstance(node, ast.FunctionDef) and node.name == 'canonical')]
    assert len(definitions) == 3
    namespace = {'Path': Path}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), '<exact reviewed canonical byte bridge>', 'exec'), namespace)
    # The Windows-tested scripts are CRLF, while their Git blobs remain LF for
    # Linux. Extend only these declared text paths; never rewrite Git as CRLF.
    shell_text_paths = {'tools/linux/liveness_shim.sh', 'tools/linux/run_test.sh', 'tools/linux/shoot.sh'}
    namespace['TEXT_PATHS'] = namespace['TEXT_PATHS'] | shell_text_paths
    canonical = namespace['canonical']
    names = sorted(expected)
    batch = git('cat-file', '--batch', input=''.join(':' + name + '\n' for name in names).encode())
    offset = 0
    changes = []
    raw_before = {}
    for name in names:
        end = batch.index(b'\n', offset)
        oid, kind, size = batch[offset:end].split()
        assert kind == b'blob'
        size = int(size)
        start = end + 1
        blob = batch[start:start + size]
        assert len(blob) == size and batch[start + size:start + size + 1] == b'\n'
        assert hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + blob).hexdigest().encode() == oid
        offset = start + size + 1
        target = ROOT / name
        reference = REVIEW / name
        for path in (target, reference):
            assert path.resolve().is_relative_to(path.parents[len(Path(name).parts)-1].resolve())
            assert path.is_file() and not path.is_symlink() and not path.stat().st_file_attributes & 0x400
        current = target.read_bytes()
        tested = reference.read_bytes()
        assert sha(tested) == expected[name]
        assert canonical(current, name) == canonical(blob, name) == canonical(tested, name), name
        if current != tested:
            assert Path(name).suffix in namespace['TEXT'] or name in namespace['TEXT_PATHS']
            changes.append((name, current, tested, oid.decode()))
        raw_before[name] = sha(current)
    assert offset == len(batch)
    backup = ROOT / 'output/PRIVATE-neon-merge-pretested-raw-before-20261117'
    backup.mkdir(exist_ok=False)
    for name, old, tested, oid in changes:
        target = ROOT / name
        assert target.read_bytes() == old
        stored = backup / name
        stored.parent.mkdir(parents=True, exist_ok=True)
        with stored.open('xb') as stream: stream.write(old)
        assert stored.read_bytes() == old
        target.write_bytes(tested)
        assert sha(target.read_bytes()) == expected[name]
    assert source_map(ROOT) == source_map(REVIEW) == expected
    unstaged = git('diff', '--name-only', '--', *SCOPE).decode().splitlines()
    assert not [name for name in unstaged if '__pycache__' not in Path(name).parts and not name.endswith('.pyc')]
    proof = {'format': 'has_root_qualified_merge_tested_raw_restore_1',
        'candidate': REV, 'main_parent': PARENT, 'functional_files': 1029,
        'all_working_and_index_content_equal_under_reviewed_canonical_bridge': True,
        'restored_raw_text_files': len(changes), 'all_tested_raw_bytes_exact': True,
        'additional_explicit_text_paths': sorted(shell_text_paths),
        'Git_shell_blobs_not_rewritten': True,
        'old_cache_dirt_preserved': True, 'changes': [{'path': name, 'before_sha256': sha(old),
        'tested_sha256': sha(tested), 'index_git_blob': oid} for name, old, tested, oid in changes]}
    with (backup / 'RESTORATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in proof.items() if key != 'changes'}))


if __name__ == '__main__': main()

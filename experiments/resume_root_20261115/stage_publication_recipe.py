"""Stage the reviewed public recipe inside its existing output-only boundary."""
from pathlib import Path
import hashlib
import json
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/resume_full_20261115/publication'
TARGET = ROOT / 'output/resume-full-publication-f0dd57a-20261115'
RUN = ROOT / 'output/windows-canonical-bone-binding-20261115T225514304'
REVISION = 'f0dd57a2e568089d396fecba819ab987da658bf0'
INDEX_SHA = 'f4965594eb313b0ac07ac9d49041cba8cc9f520c99b099115fd5666ae05da873'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    for entry in (path, *path.parents):
        info = entry.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    assert before.st_nlink == 1 and (before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_size, after.st_mtime_ns, after.st_ino)
    return raw


def main():
    state = json.loads(read(RUN / 'state.json'))
    assert state['source_commit'] == REVISION and state['status'] == 'passed'
    assert state['suite_exit'] == 0 and state['source_unchanged'] is True
    host = json.loads(read(RUN / 'authoritative-host-termination.json'))
    assert host['source_commit'] == REVISION and host['canonical_run'] == RUN.name
    assert host['coordinator_absent'] and host['python_absent'] and host['owned_runtime_command_matches_absent']
    assert host['raw_observation_sha256'] == sha(read(RUN / 'authoritative-host-terminal.json'))
    raw_index = read(SOURCE / 'INDEX.json')
    assert sha(raw_index) == INDEX_SHA
    index = json.loads(raw_index)
    assert len(index['files']) == 8 and not TARGET.exists()
    pending = []
    for row in index['files']:
        assert re.fullmatch(r'[A-Za-z0-9_.-]+', row['path'])
        raw = read(SOURCE / row['path'])
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256']
        pending.append((row, raw))
    TARGET.mkdir()
    copied = []
    for row, raw in pending:
        path = TARGET / row['path']
        with path.open('xb') as stream:
            stream.write(raw)
        assert read(path) == read(SOURCE / row['path']) == raw
        copied.append({'source': str(SOURCE / row['path']), 'copied': str(path),
                       'bytes': len(raw), 'sha256': sha(raw), 'byte_identical': True})
    with (TARGET / 'SOURCE-RECIPE-INDEX.json').open('xb') as stream:
        stream.write(raw_index)
    proof = {'format': 'has_publication_recipe_execution_copy_1',
             'source_commit': REVISION, 'canonical_run': str(RUN),
             'source_recipe': str(SOURCE), 'execution_recipe': str(TARGET),
             'source_index_sha256': INDEX_SHA, 'copied_files': copied,
             'recipes_executed': False}
    with (TARGET / 'COPY-PROVENANCE.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'copied_files': len(copied), 'target': str(TARGET),
                      'source_index_sha256': INDEX_SHA, 'recipes_executed': False}))


if __name__ == '__main__':
    main()

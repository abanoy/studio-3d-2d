from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = '0ffadead15d41a098c8ab2248d625486e94f8a39'
DOCS = ('LLM.md', 'docs/NEXT_SESSION_PLAN_2026-11-20.md',
        'docs/RESUME_MASTER_PLAN.md', 'docs/benchmarks/reference_body_2026-11-20.json',
        'docs/completion_checklist.json', 'docs/completion_checklist.md',
        'docs/progress_memo.md')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    packets = sys.argv[1:]
    assert packets and len(packets) == len(set(packets))
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    allowed = set(DOCS)
    records = []
    for name in packets:
        assert name.startswith('source_') and '/' not in name and '\\' not in name
        folder = ROOT / 'experiments' / name
        manifest = json.loads((folder / 'CONTENTS.json').read_bytes())
        expected = {row['path'] for row in manifest['files']} | {'CONTENTS.json'}
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        assert expected == actual, (name, expected ^ actual)
        for row in manifest['files']:
            path = folder / row['path']
            assert path.resolve().is_relative_to(folder.resolve()), str(path)
            raw = path.read_bytes()
            assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], str(path)
        allowed.update((folder / item).relative_to(ROOT).as_posix() for item in actual)
        records.append(dict(packet=name, files=len(actual),
                            bytes=sum((folder / item).stat().st_size for item in actual),
                            CONTENTS_sha256=sha((folder / 'CONTENTS.json').read_bytes())))
    for name in ('LLM.md', 'docs/progress_memo.md'):
        assert (ROOT / name).read_bytes().startswith(git('show', BASE + ':' + name)), name
    old = json.loads(git('show', BASE + ':docs/completion_checklist.json'))
    current = json.loads((ROOT / 'docs/completion_checklist.json').read_bytes())
    keys = ('id', 'category', 'implementation', 'verification', 'acceptance_status', 'external_dependencies')
    assert [{k: row[k] for k in keys} for row in old['requirements']] == [
        {k: row[k] for k in keys} for row in current['requirements']]
    assert len(current['requirements']) == 62
    full = json.loads((ROOT / 'experiments/reference_body_full_20261120/source-after.json').read_bytes())
    assert len(full) == 1061
    for name, row in full.items():
        path = ROOT / name
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), name
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'] and after.st_mtime_ns == row['mtime_ns'], name
    result = dict(format='has_source_combined_checkpoint_preflight_1', base=BASE,
                  packets=records, exact_full_source_files=1061,
                  history_prefixes_exact=True, stable_statuses_unchanged=62,
                  allowed_files=sorted(allowed), allowed_file_count=len(allowed))
    (ROOT / 'output/source-combined-checkpoint-preflight-20261120.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: value for k, value in result.items() if k != 'allowed_files'}))


if __name__ == '__main__':
    main()

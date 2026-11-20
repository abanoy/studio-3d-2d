from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REV = sys.argv[1]
OUTPUT = sys.argv[2]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

rows = []
names = git('diff-tree', '--no-commit-id', '--name-only', '-r', REV).decode().splitlines()
for name in names:
    raw = git('show', REV + ':' + name)
    assert raw == (ROOT / name).read_bytes(), name
    rows.append(dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                     git_sha1=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()))
result = dict(commit=REV, parent=git('rev-parse', REV + '^').decode().strip(),
              files=rows, count=len(rows), total_bytes=sum(row['bytes'] for row in rows))
(ROOT / OUTPUT).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result))

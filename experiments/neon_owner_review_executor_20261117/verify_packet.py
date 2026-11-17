"""Verify this source/CPU packet only; no activation or build is performed."""
from pathlib import Path
import ast
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent


def need(value, message):
    if not value:
        raise RuntimeError(message)


def verify():
    index = json.loads((HERE / 'INDEX.json').read_text(encoding='utf-8'))
    need(index['format'] == 'has_concrete_neon_owner_copy_executor_source_packet_1', 'packet format')
    rows = index['files']
    names = set()
    total = 0
    for row in rows:
        name = row['path']
        need(type(name) is str and name and name not in names and '\\' not in name
             and not Path(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')),
             'unsafe or duplicate packet name')
        names.add(name)
        path = HERE / name
        for item in [path, *path.parents]:
            info = item.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024,
                 'packet link or reparse point')
            if item == HERE:
                break
        raw = path.read_bytes()
        need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
             'packet bytes differ: ' + name)
        total += len(raw)
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()}
    need(actual == names | {'INDEX.json'}, 'extra or missing packet file')
    need(total == index['payload_bytes'] and len(rows) == index['payload_files'], 'packet extent')
    tree = ast.parse((HERE / 'qualified_inputs.py').read_bytes())
    gate = [n.value for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'APPROVED_ACTIVATION_SHA256' for t in n.targets)]
    need(len(gate) == 1 and isinstance(gate[0], ast.Constant) and gate[0].value is None,
         'this source packet must remain inactive')
    need(not (HERE / 'ACTIVATION.json').exists(), 'actual activation is outside this preparation packet')
    result = json.loads((HERE / 'CPU_RESULT.json').read_text(encoding='utf-8'))
    need(result['total_methods'] == 36 and result['failures'] == 0
         and result['positive_actual_activation_or_whole_build_run'] is False,
         'CPU scope or qualification changed')
    print(json.dumps({'passed': True, 'source_CPU_only': True, 'payload_files': len(rows),
                      'payload_bytes': total, 'actual_activation': False}, sort_keys=True))


if __name__ == '__main__':
    verify()

"""Verify only this inactive source/CPU packet. Never runs admission or engines."""
from pathlib import Path
import ast
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent


def need(value, message):
    if not value:
        raise ValueError(message)


def verify():
    index = json.loads((HERE / 'INDEX.json').read_bytes())
    need(index['format'] == 'has_owner_cold187_source_adapter_packet_1', 'Packet format')
    names = set(); total = 0
    for row in index['files']:
        name = row['path']
        need(type(name) is str and name and name not in names and '\\' not in name
             and not Path(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')), 'Packet path')
        path = HERE / name
        for item in (path, *path.parents):
            info = item.lstat()
            need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'Packet reparse')
        raw = path.read_bytes()
        need(type(row['bytes']) is int and len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Exact payload')
        names.add(name); total += len(raw)
    need({p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file()} == names | {'INDEX.json'}, 'Closed source packet membership')
    need(total == index['payload_bytes'] and len(names) == index['payload_files'], 'Exact source packet extent')
    assignments = [node for node in ast.parse((HERE / 'validation_admission.py').read_bytes()).body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'APPROVED_VALIDATION_ACTIVATION_SHA256' for t in node.targets)]
    need(len(assignments) == 1 and isinstance(assignments[0].value, ast.Constant) and assignments[0].value.value is None
         and not (HERE / 'ACTIVATION.json').exists(), 'This source packet must stay inactive')
    result = json.loads((HERE / 'CPU_RESULT.json').read_bytes())
    need(result['methods'] == 29 and result['failures'] == 0 and result['actual_positive_qualification_or_engine_run'] is False, 'CPU evidence domain')
    print(json.dumps({'passed': True, 'source_CPU_only': True, 'payload_files': len(names), 'payload_bytes': total, 'activation_absent': True}))


if __name__ == '__main__':
    verify()

"""Read-only packet hash verifier; no native/runtime or source imports."""
from pathlib import Path
import hashlib
import json


def main():
    root = Path(__file__).resolve().parent
    index = json.loads((root/'INDEX.json').read_bytes())
    if index.get('format') != 'has_sourceio_setter_boundary_source_packet_1': raise ValueError('Wrong packet')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    expected = set(index['files']) | {'INDEX.json'}
    if actual != expected: raise ValueError('Packet membership differs')
    for name, row in index['files'].items():
        path = root/name
        if path.is_symlink() or not path.resolve().is_relative_to(root): raise ValueError('Unsafe packet path')
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']: raise ValueError('Packet payload differs: '+name)
    print(json.dumps({'status':'PASS','payloads':len(index['files']),
                      'native_engine_executed':False,'tests_executed':False,
                      'INDEX_sha256':hashlib.sha256((root/'INDEX.json').read_bytes()).hexdigest()}))


if __name__ == '__main__': main()

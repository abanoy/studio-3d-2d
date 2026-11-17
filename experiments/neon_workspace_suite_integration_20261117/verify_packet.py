"""Read-only source packet hash verifier. Does not import the production wrapper."""
from pathlib import Path
import hashlib
import json


def main():
    root=Path(__file__).resolve().parent
    index=json.loads((root/'INDEX.json').read_bytes())
    if index.get('format')!='has_neon_workspace_suite_integration_source_packet_1': raise ValueError('Wrong source packet')
    expected=set(index['files'])|{'INDEX.json'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=expected: raise ValueError('Packet membership differs')
    for name,row in index['files'].items():
        path=root/name
        if path.is_symlink() or not path.resolve().is_relative_to(root): raise ValueError('Unsafe packet member')
        body=path.read_bytes()
        if len(body)!=row['bytes'] or hashlib.sha256(body).hexdigest()!=row['sha256']: raise ValueError('Packet payload changed: '+name)
    print(json.dumps({'status':'PASS','payloads':len(index['files']),
                      'INDEX_sha256':hashlib.sha256((root/'INDEX.json').read_bytes()).hexdigest(),
                      'engines_executed':False,'tests_executed':False}))


if __name__=='__main__': main()

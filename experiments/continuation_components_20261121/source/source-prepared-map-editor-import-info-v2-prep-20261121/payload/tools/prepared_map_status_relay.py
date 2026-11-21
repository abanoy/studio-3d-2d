"""Replay one already-converted map status; never convert or load native code."""
import hashlib
import json
import pathlib
import sys


def main():
    if len(sys.argv) != 4:
        raise RuntimeError('EXACT_SPEC_HASH_STATUS_ARGUMENTS_REQUIRED')
    spec_path = pathlib.Path(sys.argv[1])
    raw = spec_path.read_bytes()
    if len(raw) > 4096 or hashlib.sha256(raw).hexdigest() != sys.argv[2]:
        raise RuntimeError('SPEC_PIN_REQUIRED')
    spec = json.loads(raw)
    if set(spec) != {'glb', 'sha256', 'owned_root'}:
        raise RuntimeError('EXACT_RELAY_SCHEMA_REQUIRED')
    owned = pathlib.Path(spec['owned_root']).resolve(strict=True)
    glb = pathlib.Path(spec['glb']).resolve(strict=True)
    status = pathlib.Path(sys.argv[3])
    if not glb.is_relative_to(owned) or not status.parent.resolve(strict=True).is_relative_to(owned):
        raise RuntimeError('OWNED_PATH_REQUIRED')
    if not glb.is_file() or glb.stat().st_size > 128 * 1024 * 1024:
        raise RuntimeError('BOUNDED_GLB_REQUIRED')
    if hashlib.sha256(glb.read_bytes()).hexdigest() != spec['sha256']:
        raise RuntimeError('GLB_PIN_REQUIRED')
    with status.open('x', encoding='utf-8', newline='\n') as output:
        json.dump({'ok': True, 'glb': spec['glb'], 'prepared_status_replay_only': True}, output)
        output.write('\n')


if __name__ == '__main__':
    main()

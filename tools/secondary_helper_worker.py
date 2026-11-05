"""One owned local helper-authoring operation with an atomic result receipt."""
from pathlib import Path
import argparse
import json
import os
import secondary_helpers as helpers


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('source'); parser.add_argument('operation', choices=['inspect', 'preview', 'build']); parser.add_argument('folder'); args = parser.parse_args()
    folder = Path(args.folder)
    try:
        request_path = folder / 'request.json'
        if request_path.stat().st_size > 1024 * 1024: raise ValueError('Helper request exceeds1MiB')
        request = json.loads(request_path.read_text(encoding='utf-8'))
        if not isinstance(request, dict): raise ValueError('Expected helper request object')
        if args.operation == 'inspect': value = helpers.inspect(args.source, request)
        elif args.operation == 'preview': value = helpers.preview(args.source, request)
        else: value = helpers.build(args.source, folder / 'derived', request)
        result = {'ok': True, 'value': value}
        encoded = json.dumps(result, allow_nan=False).encode('utf-8')
        if len(encoded) > 4 * 1024 * 1024: raise ValueError('Helper preview exceeds4MiB')
    except Exception as error:
        encoded = json.dumps({'ok': False, 'error': str(error)}).encode('utf-8')
    temporary = folder / 'result.json.tmp'
    with temporary.open('xb') as f: f.write(encoded); f.flush(); os.fsync(f.fileno())
    os.replace(temporary, folder / 'result.json')


if __name__ == '__main__': main()

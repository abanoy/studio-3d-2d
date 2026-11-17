"""Freeze only whitelisted closed-run text identities; never reads model descriptors."""
from pathlib import Path
import json
from archive_checks import check, need, parse, sha

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[1]
REVIEW = MAIN.parent / 'has-neon-review-20261116-c2d52ff'
RUN = REVIEW / 'output/windows-neon-fe9aace-20261117T040348'


def safe(path, root):
    need(path.is_absolute() and path.resolve().is_relative_to(root.resolve()), 'Owned source boundary')
    for part in (path, *path.parents):
        if part == root.parent:
            break
        need(not part.is_symlink() and not getattr(part.lstat(), 'st_file_attributes', 0) & 0x400, 'Reparse input refused')
    need(path.is_file(), 'Regular source required')


def main():
    need(not (HERE / 'INPUTS.json').exists(), 'Never overwrite frozen inputs')
    selections = [(name, RUN / name, 'REVIEW') for name in ('state.json', 'source-before.json', 'source-after.json', 'launch.json', 'root-birth-observation.json', 'root-birth-api-detail.json', 'canonical.log', 'graphics-lease-closed.json', 'preparation.json', 'preflight-source.json', 'coordinator.stdout.log', 'coordinator.stderr.log')]
    selections += [(name, RUN / 'terminal-audit-attempt1' / name, 'REVIEW') for name in ('receipt-inventory.json', 'host-observation.json')]
    inventory = parse((RUN / 'terminal-audit-attempt1/receipt-inventory.json').read_bytes())
    for index, row in enumerate(inventory['rows']):
        path = Path(row['preserved_raw_copy'])
        need(path.parent == RUN / 'terminal-audit-attempt1', 'Exact preserved physical receipt folder')
        selections.append(('receipts/%03d.json' % index, path, 'REVIEW'))
    selections += [(name, HERE / name, 'MAIN') for name in ('original-verify_shape_catalog.py', 'SOURCE_CAPTURE.json')]
    launch = parse((RUN / 'launch.json').read_bytes())
    selections.append(('runner.ps1', Path(launch['runner']), 'MAIN'))
    raw, inputs = {}, []
    for alias, path, label in selections:
        root = {'MAIN': MAIN, 'REVIEW': REVIEW}[label]
        safe(path, root)
        before = path.stat(); data = path.read_bytes(); after = path.stat()
        need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'Input changed during capture')
        need(path.suffix in ('.json', '.log', '.py', '.ps1') and len(data) <= 2 * 1024 * 1024 and b'\0' not in data, 'Bounded text-only scope')
        data.decode('utf-8-sig')
        need(alias not in raw, 'Duplicate alias')
        raw[alias] = data
        inputs.append({'alias': alias, 'root': label, 'path': path.relative_to(root).as_posix(), 'bytes': len(data), 'mtime_ns': before.st_mtime_ns, 'sha256': sha(data)})
    summary = check(raw)
    spec = {'format': 'has_fe9_closed_failure_archive_inputs_1', 'roots': {'MAIN': str(MAIN), 'REVIEW': str(REVIEW)}, 'inputs': inputs, 'expected_summary': summary,
            'scope': 'Fixed closed run and68 preserved physical raw receipts, public source capture and public coordinator only. No sfm-face-pilot descriptor or media/model/native arrays.'}
    with (HERE / 'INPUTS.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(spec, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'inputs': len(inputs), 'INPUTS_sha256': sha((HERE / 'INPUTS.json').read_bytes()), 'summary': summary}, indent=2))


if __name__ == '__main__':
    main()

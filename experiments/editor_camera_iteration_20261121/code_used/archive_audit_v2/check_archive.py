"""Read-only recovery/privacy-boundary audit; no test or application execution."""
import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath


ALLOWED = {'.json', '.gd', '.py', '.md', '.ps1', '.log', '.mjs', '.cpp', '.txt'}
CPP_PINS = {
    'gltf_document.cpp': (298566, 'a33185acc304524e99302244a652c295e9f201fcf9e8269223ea2e8df6fe803e'),
    'rendering_server.cpp': (194067, '688b9023786e30603c95779e29ab21cedf43c7f5e723573df658cbbcd4bc88d7'),
}
LICENSE_PIN = (1149, 'b0435e3b3e4e55238f05f4b306f30524a1b2e20147810d436eaa554fa6855c80')
COMBINED = 'source-combined-ui-v6-camera-shipping-prep-20261121'
PORTS = 'source-ui-camera-port-bindings-prep-20261121'
SHA = re.compile(r'[0-9a-f]{64}\Z')
RAW_KEYS = re.compile(r'^(?:calibration_failure|influence_failure|raw_bones|raw_skin|'
                      r'raw_source_weights|normalized_source_weights|imported_weights|'
                      r'inverse_bind_matrices|vertex_positions|skin_vertices|bone_matrices|'
                      r'joint_indices|source_slot_ids|imported_slot_ids)$', re.I)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe_name(value):
    need(isinstance(value, str) and value and '\\' not in value and ':' not in value,
         'invalid relative path')
    parts = PurePosixPath(value).parts
    need(not value.startswith('/') and parts and all(p not in ('', '.', '..') for p in parts),
         'unsafe relative path')
    need('/'.join(parts) == value and all(not p.endswith((' ', '.')) for p in parts),
         'noncanonical relative path')
    need(all(not re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I)
             for p in parts), 'Windows reserved path')
    need(all(p.upper() != 'PRIVATE' for p in parts), 'PRIVATE payload directory')
    need(not any(p.upper().startswith('PENDING_CONTENTS') for p in parts),
         'draft inventory must stay local')
    return value


def identity(p):
    s = p.lstat()
    need(not stat.S_ISLNK(s.st_mode) and not (getattr(s, 'st_file_attributes', 0) & 0x400),
         'link/reparse path: ' + str(p))
    return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_nlink)


def walk_error(error):
    raise error


def tree(root):
    need(root.is_dir(), 'archive directory missing')
    identity(root)
    rows, names, realnames, ids = {}, set(), set(), set()
    for current, directories, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in directories + files:
            p = Path(current) / name
            rel = safe_name(p.relative_to(root).as_posix())
            folded = rel.casefold()
            need(folded not in names, 'case alias: ' + rel)
            names.add(folded)
            ident = identity(p)
            resolved = p.resolve(strict=True)
            need(resolved.is_relative_to(root), 'resolved path outside archive')
            real = str(resolved).casefold()
            need(real not in realnames, 'resolved alias: ' + rel)
            realnames.add(real)
            if p.is_dir():
                continue
            need(stat.S_ISREG(ident[2]) and ident[5] == 1, 'nonregular/hardlinked file: ' + rel)
            file_id = ident[:2]
            need(file_id not in ids, 'file identity alias: ' + rel)
            ids.add(file_id)
            rows[rel] = ident
    return rows


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(row):
    need(isinstance(row, dict), 'manifest row is not an object')
    name = safe_name(row.get('path'))
    need(type(row.get('bytes')) is int and row['bytes'] >= 0, 'invalid size: ' + name)
    need(isinstance(row.get('sha256'), str) and SHA.fullmatch(row['sha256']),
         'invalid digest: ' + name)
    return name


def table(rows):
    need(isinstance(rows, list), 'manifest files must be an array')
    out, folded = {}, set()
    for row in rows:
        name = pin(row)
        need(name.casefold() not in folded, 'duplicate/aliased manifest row: ' + name)
        folded.add(name.casefold())
        out[name] = row
    return out


def load_json(data):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(data.decode('utf-8-sig'), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def privacy_json(value):
    # Synthetic camera values and UI screen geometry are intentional evidence.
    # Owner mesh/weight dumps are not. This is a bounded structural screen,
    # not a claim that arbitrary prose can be mechanically certified private.
    if isinstance(value, dict):
        for key, item in value.items():
            if RAW_KEYS.fullmatch(key):
                need(item in (None, False, '', [], {}), 'private-data-shaped JSON payload: ' + key)
            privacy_json(item)
    elif isinstance(value, list):
        if len(value) > 512:
            need(not any(type(x) in (int, float) for x in value), 'large numeric data array')
        for item in value:
            privacy_json(item)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--packet', required=True, type=Path)
    ap.add_argument('--contents-sha256', required=True)
    ap.add_argument('--main-root', required=True, type=Path)
    ap.add_argument('--verify-origins', action='store_true')
    args = ap.parse_args()
    need(SHA.fullmatch(args.contents_sha256), 'invalid external CONTENTS pin')
    root = args.packet.absolute()
    need(root.resolve(strict=True) == root, 'archive root must already be resolved')
    before = tree(root)
    need('CONTENTS.json' in before, 'final CONTENTS.json is required')
    contents_data = (root / 'CONTENTS.json').read_bytes()
    need(digest(contents_data) == args.contents_sha256, 'CONTENTS external pin mismatch')
    contents = load_json(contents_data)
    rows = table(contents.get('files'))
    need('CONTENTS.json' not in rows, 'CONTENTS must not self-hash')
    need(set(before) == set(rows) | {'CONTENTS.json'}, 'archive exact file set differs from CONTENTS')
    parsed, total = {}, 0
    for name, row in rows.items():
        data = (root / name).read_bytes()
        need((len(data), digest(data)) == (row['bytes'], row['sha256']), 'payload pin mismatch: ' + name)
        total += len(data)
        suffix = PurePosixPath(name).suffix.lower()
        need(suffix in ALLOWED, 'unapproved source/evidence extension: ' + name)
        text = data.decode('utf-8-sig')
        need('\x00' not in text, 'binary/NUL payload: ' + name)
        need(not re.search(r'data:(?:image|application|model)/[^\s"\']*;base64,[A-Za-z0-9+/=]{256,}', text, re.I),
             'embedded binary data URI: ' + name)
        if suffix == '.cpp':
            need('/upstream/' in '/' + name and PurePosixPath(name).name in CPP_PINS,
                 'unapproved C++ provenance path: ' + name)
            need((len(data), digest(data)) == CPP_PINS[PurePosixPath(name).name], 'upstream C++ pin mismatch')
            license_name = name.split('/upstream/', 1)[0] + '/upstream/LICENSE.txt'
            need(license_name in rows and
                 (rows[license_name]['bytes'], rows[license_name]['sha256']) == LICENSE_PIN,
                 'pinned upstream license missing for C++ source')
        if suffix == '.txt':
            need(name.endswith('/upstream/LICENSE.txt') and
                 (len(data), digest(data)) == LICENSE_PIN, 'unapproved text/license payload')
        if suffix == '.json':
            parsed[name] = load_json(data)
            privacy_json(parsed[name])
        if args.verify_origins and 'source' in row:
            origin = args.main_root / safe_name(row['source'])
            original = origin.read_bytes()
            need((len(original), digest(original)) == (len(data), digest(data)), 'origin differs: ' + name)

    manifests = 0
    for name, document in parsed.items():
        if PurePosixPath(name).name != 'SOURCE_PINS.json':
            continue
        inner = table(document.get('files'))
        prefix = str(PurePosixPath(name).parent) + '/'
        expected = {prefix + item for item in inner} | {name}
        actual = {item for item in rows if item.startswith(prefix)}
        need(expected == actual, 'inner source manifest closure differs: ' + name)
        for child, child_row in inner.items():
            outer = rows[prefix + child]
            need((child_row['bytes'], child_row['sha256']) == (outer['bytes'], outer['sha256']),
                 'inner source pin differs: ' + name + ':' + child)
        manifests += 1
    need(manifests > 0, 'no frozen source manifests found')

    current_before, current_rows = {}, {}
    for packet, count in ((COMBINED, 23), (PORTS, 2)):
        document = parsed.get(packet + '/TARGETS.json')
        need(isinstance(document, dict), 'required adopted target manifest missing: ' + packet)
        targets = table(document.get('targets'))
        need(len(targets) == count, 'target manifest count changed')
        for name, target in targets.items():
            need(name not in current_rows, 'duplicate current target')
            payload = rows.get(packet + '/payload/' + name)
            need(payload is not None and (payload['bytes'], payload['sha256']) ==
                 (target['bytes'], target['sha256']), 'target recovery payload mismatch: ' + name)
            main_path = args.main_root / name
            current_before[name] = identity(main_path)
            data = main_path.read_bytes()
            need((len(data), digest(data)) == (target['bytes'], target['sha256']),
                 'current adopted target differs: ' + name)
            current_rows[name] = target
    need(len(current_rows) == 25, 'expected25 current functional targets')
    need(tree(root) == before, 'archive changed during audit')
    need(digest((root / 'CONTENTS.json').read_bytes()) == args.contents_sha256,
         'CONTENTS changed during audit')
    for name, row in rows.items():
        data = (root / name).read_bytes()
        need((len(data), digest(data)) == (row['bytes'], row['sha256']), 'payload changed during audit')
    for name, target in current_rows.items():
        p = args.main_root / name
        need(identity(p) == current_before[name], 'Main target identity changed during audit')
        data = p.read_bytes()
        need((len(data), digest(data)) == (target['bytes'], target['sha256']), 'Main target changed during audit')
    need(tree(root) == before, 'archive identity changed during final readback')
    print(json.dumps({'format': 'has_editor_camera_archive_audit_1', 'status': 'PASS',
                      'contents_sha256': args.contents_sha256, 'payload_files': len(rows),
                      'payload_bytes': total, 'frozen_inner_manifests': manifests,
                      'current_functional_targets': len(current_rows),
                      'privacy_scope': 'text/extension/signature/structured-private-array screen; source review still required',
                      'origin_readback_requested': args.verify_origins,
                      'archive_and_current_targets_unchanged': True,
                      'native_execution': False, 'Full1102_claimed': False,
                      'historical_preparation_adoption_flags_reinterpreted': False}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'format': 'has_editor_camera_archive_audit_1', 'status': 'FAIL',
                          'error': str(exc), 'native_execution': False, 'Full1102_claimed': False}))
        raise SystemExit(1)

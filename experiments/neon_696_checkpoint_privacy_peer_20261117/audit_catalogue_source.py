"""Read-only public checkpoint selection audit; never executes the preparer."""
from pathlib import Path
import argparse
import ast
import datetime
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREPARER = ROOT / 'experiments/prepare_neon_camera_checkpoint_20261117.py'


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def regular_owned_file(path, boundary):
    need(path.is_absolute() and path.resolve().is_relative_to(boundary.resolve()), 'Owned path boundary')
    for parent in (path, *path.parents):
        if parent == boundary.parent: break
        need(not parent.is_symlink() and not (getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse path refused')
    need(path.is_file(), 'Regular file required')


def static_lists(source):
    unit = ast.parse(source); result = {}
    for node in unit.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('FOLDERS', 'FILES'):
                    need(isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'split', 'Literal selection list required')
                    result[target.id] = ast.literal_eval(node.value.func.value).split()
    need(set(result) == {'FOLDERS', 'FILES'}, 'Complete literal selection')
    return result


def packet_rows(index):
    keys = [key for key in ('files', 'artifacts', 'payloads') if key in index]
    need(len(keys) == 1, 'One packet payload role')
    rows = index[keys[0]]
    rows = [dict(path=path, **row) for path, row in rows.items()] if type(rows) is dict else rows
    need(type(rows) is list, 'Packet row list')
    rows = rows + index.get('objects', [])
    need(len({row['path'] for row in rows}) == len(rows), 'Unique packet row paths')
    return rows


def suspicious_arrays(value, prefix='$'):
    found = []
    if type(value) is dict:
        for key, child in value.items(): found += suspicious_arrays(child, prefix + '.' + key)
    elif type(value) is list:
        if len(value) >= 24 and all(type(x) in (int, float) for x in value):
            found.append({'field': prefix, 'numeric_items': len(value)})
        for i, child in enumerate(value):
            if type(child) in (dict, list): found += suspicious_arrays(child, prefix + '[' + str(i) + ']')
    return found


def numeric_arrays(value, prefix='$'):
    """Report numeric list locations/counts at every size without emitting values."""
    found = []
    if type(value) is dict:
        for key, child in value.items(): found += numeric_arrays(child, prefix + '.' + key)
    elif type(value) is list:
        if value and all(type(x) in (int, float) for x in value):
            found.append({'field': prefix, 'numeric_items': len(value)})
        for i, child in enumerate(value):
            if type(child) in (dict, list): found += numeric_arrays(child, prefix + '[' + str(i) + ']')
    return found


def literal_maps(source):
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('UNSEALED', 'FLAT_SEALS'):
                    need(target.id not in result, 'One literal role-map assignment')
                    result[target.id] = ast.literal_eval(node.value)
    need(set(result) == {'UNSEALED', 'FLAT_SEALS'} and all(type(v) is dict for v in result.values()), 'Exact literal role maps')
    for mapping in result.values():
        for name, paths in mapping.items():
            need(type(name) is str and type(paths) is tuple and paths and len(set(paths)) == len(paths), 'Exact unique role tuple')
            for item in paths:
                need(type(item) is str and not Path(item).is_absolute() and '..' not in Path(item).parts and '\\' not in item,
                     'Literal relative role path')
    need(not(set(result['UNSEALED']) & set(result['FLAT_SEALS'])), 'Disjoint role exceptions')
    return result


def flat_rows(seal, allowed):
    need(type(seal) is dict and seal.get('format') == 'has_neon696_full_preflight_source_seal_1', 'Exact flat source-seal format')
    rows = seal.get('source_files')
    need(type(rows) is list and len(rows) == len(allowed) and len({row['ROOT_relative_path'] for row in rows}) == len(rows)
         and {row['ROOT_relative_path'] for row in rows} == set(allowed), 'Exact two-source flat role set')
    return rows


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--manifest-relative', required=True)
    parser.add_argument('--public-copy-relative', required=True)
    args = parser.parse_args()
    source = PREPARER.read_bytes(); lists = static_lists(source.decode('utf-8-sig'))
    maps = literal_maps(source.decode('utf-8-sig')); unsealed_whitelist = maps['UNSEALED']; flat_whitelist = maps['FLAT_SEALS']
    need(set(unsealed_whitelist) | set(flat_whitelist) <= set(lists['FOLDERS']), 'All exceptions are selected folders')
    need(all(set(v) <= set(lists['FILES']) for v in flat_whitelist.values()), 'Flat sources already explicitly selected')
    selected = set(lists['FILES']); packets = []; unsealed = []; flats = []; array_flags = []; source_maps = []
    original_index_bytes = {}
    for name in lists['FOLDERS']:
        folder = ROOT / 'experiments' / name; need(folder.is_dir(), 'Selected source folder exists')
        index_path = folder / 'INDEX.json'
        if name in unsealed_whitelist:
            names = unsealed_whitelist[name]
            chosen = [folder / item for item in names]
            need(all(path.suffix == '.json' for path in chosen), 'Public observation JSON roles only')
            unsealed.append({'folder': name, 'exact_literal_files': list(names), 'recursive_discovery_used': False})
        elif name in flat_whitelist:
            seal_path = folder / 'SOURCE_SEAL.json'; regular_owned_file(seal_path, ROOT)
            seal_raw = seal_path.read_bytes(); original_index_bytes[str(seal_path)] = seal_raw
            rows = flat_rows(json.loads(seal_raw), flat_whitelist[name])
            for row in rows:
                path = ROOT / row['ROOT_relative_path']; regular_owned_file(path, ROOT / 'experiments'); raw = path.read_bytes()
                need(type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Flat source-seal declared identity')
            chosen = [seal_path] + [ROOT / item for item in flat_whitelist[name]]
            flats.append({'folder': name, 'source_seal_sha256': sha(seal_raw), 'exact_ROOT_source_roles': list(flat_whitelist[name]), 'checked_sources': len(rows)})
        else:
            need(index_path.is_file(), 'Unfinished source packet refused')
            regular_owned_file(index_path, ROOT); index_raw = index_path.read_bytes(); index = json.loads(index_raw)
            rows = packet_rows(index); original_index_bytes[str(index_path)] = index_raw
            for row in rows:
                relative = Path(row['path']); need(not relative.is_absolute() and '..' not in relative.parts, 'Packet relative path')
                path = folder / relative; regular_owned_file(path, folder); raw = path.read_bytes()
                need(type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Declared payload identity')
                if 'decoded_sha256' in row:
                    decoded = gzip.decompress(raw)
                    need(type(row['decoded_bytes']) is int and len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256'], 'Declared decoded identity')
            packets.append({'folder': name, 'INDEX_sha256': sha(index_raw), 'payloads': len(rows), 'selection_is_INDEX_only': True})
            chosen = [index_path] + [folder / row['path'] for row in rows]
        selected.update(p.relative_to(ROOT).as_posix() for p in chosen)
    rows = []; named_private = []; encoded_media = []; hex_files = []; all_numeric_arrays = []
    for relative in sorted(selected):
        path = ROOT / relative; regular_owned_file(path, ROOT)
        need(not relative.startswith('output/') and '__pycache__' not in path.parts, 'No output/cache selection')
        raw = path.read_bytes(); decoded = gzip.decompress(raw) if path.suffix == '.gz' else raw
        need(b'\0' not in decoded, 'No binary NUL in public text'); text = decoded.decode('utf-8-sig')
        if path.name.startswith('PRIVATE_'): named_private.append(relative)
        if any(prefix in text.lower() for prefix in ('data:image/', 'data:audio/', 'data:video/')): encoded_media.append(relative)
        if path.suffix == '.hex': hex_files.append(relative)
        if path.suffix == '.json' or decoded.lstrip().startswith((b'{', b'[')):
            try: parsed = json.loads(decoded)
            except (json.JSONDecodeError, UnicodeError):
                need(path.suffix != '.json', 'All selected .json documents parse')
            else:
                small_flags = numeric_arrays(parsed)
                if small_flags: all_numeric_arrays.append({'path': relative, 'fields': small_flags})
                flags = suspicious_arrays(parsed)
                if flags: array_flags.append({'path': relative, 'fields': flags})
                if type(parsed) is dict and type(parsed.get('source_sha256')) is dict and len(parsed['source_sha256']) in (1019, 1029):
                    source_maps.append({'path': relative, 'source_count': len(parsed['source_sha256'])})
        rows.append({'path': relative, 'bytes': len(raw), 'sha256': sha(raw), 'decoded_bytes': len(decoded)})
    # Use only the already public archived source map, not a native/active run.
    baseline_folder = ROOT / 'experiments/native_five_full_actual_20261116'
    baseline_index_raw = (baseline_folder / 'INDEX.json').read_bytes(); baseline_index = json.loads(baseline_index_raw)
    need(sha(baseline_index_raw) == '757146330ae801d5a2bd11d2f9b594babd665c64291f61f33b0115f048cedd1e', 'Previously sealed qualified52 archive INDEX pin')
    baseline_path = 'run/source-before.json.gz'
    baseline_row = next(r for r in baseline_index['files'] if r['path'] == baseline_path)
    baseline_raw = (baseline_folder / baseline_path).read_bytes()
    need(sha(baseline_raw) == '0ff288cd27a5aaf6230a4cec798c2555371506e072864e8545492a291d5c2512', 'Previously sealed qualified52 source map pin')
    need(len(baseline_raw) == baseline_row['bytes'] and sha(baseline_raw) == baseline_row['sha256'], 'Archived main baseline source map identity')
    state_row = next(r for r in baseline_index['files'] if r['path'] == 'run/state.json')
    state_raw = (baseline_folder / state_row['path']).read_bytes()
    need(len(state_raw) == state_row['bytes'] and sha(state_raw) == state_row['sha256'], 'Archived52 state identity')
    state = json.loads(state_raw)
    need(state['source_commit'] == '52f63c944ded7a651da871524d23a345b606424d' and state['status'] == 'passed'
         and state['source_unchanged'] is True and type(state['suite_exit']) is int and state['suite_exit'] == 0,
         'Exact archived52 source baseline')
    baseline = json.loads(gzip.decompress(baseline_raw)); source_map = baseline['source_sha256']
    need(len(source_map) == 1019, 'Historical main1019 map')
    changed = []
    for name, digest in source_map.items():
        path = ROOT / name; regular_owned_file(path, ROOT)
        if sha(path.read_bytes()) != digest: changed.append(name)
    need(not changed, 'Main functional source changed from retained52 full baseline')
    manifest_facts = None
    arrays_are_EOL_recipes = all(flag['field'].endswith('.working_recipe.zero_based_lines')
                                for row in array_flags for flag in row['fields'])
    media_marker_classification = []
    for relative in encoded_media:
        path = ROOT / relative
        source_text = path.read_text(encoding='utf-8-sig')
        prefixes = ('data:image/', 'data:audio/', 'data:video/')
        constants = [node.value for node in ast.walk(ast.parse(source_text)) if isinstance(node, ast.Constant) and type(node.value) is str] if path.suffix == '.py' else []
        literal_only = all(prefix in constants and source_text.lower().count(prefix) == constants.count(prefix) for prefix in prefixes)
        media_marker_classification.append({'path': relative, 'classification': 'SCANNER_LITERAL_PREFIXES_ONLY' if literal_only else 'UNRESOLVED_MEDIA_MARKER_REVIEW_REQUIRED'})
    if args.manifest_sha256 is not None:
        # This branch may only be invoked after root says the catalogue exists.
        path = ROOT / args.manifest_relative
        regular_owned_file(path, ROOT)
        raw = path.read_bytes(); need(sha(raw) == args.manifest_sha256, 'Exact root catalogue SHA')
        manifest = json.loads(raw)
        need(manifest['format'] == 'has_public_neon_camera_source_checkpoint_catalogue_1'
             and manifest['redesign_merged'] is False and manifest['full_result_claimed'] is False
             and manifest['preceding00bf_replay2_closed_failed_camera'] is True
             and manifest['active696_metadata_not_result'] is True and manifest['camera_visibility_focused_actual_passed'] is True
             and manifest['native_fidelity_or_material_acceptance_claimed'] is False
             and manifest['native_diagnostic_source_and_scalar_metadata_only'] is True
             and manifest['owner_activation_renderer_source_CPU_only'] is True
             and manifest['source_delta_review_is_not_full_or_merge_activation'] is True
             and manifest['raw_full_reports_logs_phase_receipt_arrays_excluded'] is True
             and manifest['private_native_art_arrays_media_excluded'] is True,
             'Exact focused/source-only/current-running/not-result schema')
        need(json.dumps(manifest['actual_focused_checks'], sort_keys=True) == json.dumps({'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48}, sort_keys=True), 'Declared exact focused counts, not a full result')
        actual = manifest['files']
        expected = [{key: row[key] for key in ('path', 'bytes', 'sha256')} for row in rows]
        expected_indexes = [{'packet': p['folder'], 'index_sha256': p['INDEX_sha256'], 'checked_payloads': p['payloads']} for p in packets]
        encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        need(encode(actual) == encode(expected) and encode(manifest['source_indexes']) == encode(expected_indexes), 'Catalogue equals independently selected source/payload identities')
        need(type(manifest['main_functional_unchanged']) is int and manifest['main_functional_unchanged'] == 1019, 'Catalogue main source count')
        copy_path = ROOT / args.public_copy_relative; regular_owned_file(copy_path, ROOT)
        copy_raw = copy_path.read_bytes(); need(copy_raw == raw, 'Additional public manifest copy identity')
        need(args.public_copy_relative not in selected, 'Manifest copy is an intentional extra outside catalogue')
        manifest_facts = {'path': args.manifest_relative, 'sha256': sha(raw), 'bytes': len(raw),
                          'exact_file_rows_and_sealed_indexes_match': True,
                          'additional_public_copy': {'path': args.public_copy_relative, 'bytes': len(copy_raw), 'sha256': sha(copy_raw)}}
    need(PREPARER.read_bytes() == source, 'Preparer source unchanged during audit')
    for path, raw in original_index_bytes.items(): need(Path(path).read_bytes() == raw, 'Selected INDEX unchanged during audit')
    for row in rows:
        path = ROOT / row['path']; regular_owned_file(path, ROOT); raw = path.read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Selected public file changed during audit')
    report = {'format': 'has_camera696_source_checkpoint_public_selection_peer_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'preparer_sha256': sha(source), 'manifest_examined': manifest_facts,
              'files': rows, 'selected_files': len(rows), 'selected_bytes': sum(r['bytes'] for r in rows),
              'sealed_packets': packets, 'explicit_unsealed_folders': unsealed, 'flat_source_seals': flats,
              'private_named_payloads': named_private, 'encoded_media_markers': encoded_media,
              'encoded_media_marker_classification': media_marker_classification,
              'large_numeric_JSON_arrays_for_manual_classification': array_flags, 'hex_payloads_for_manual_classification': hex_files,
              'numeric_array_classification': 'Observed flags are only explicit working_recipe.zero_based_lines EOL recipes' if arrays_are_EOL_recipes else 'UNRESOLVED_NON_EOL_ARRAYS_REQUIRE_MANUAL_REVIEW',
              'all_size_numeric_JSON_arrays_for_manual_classification': all_numeric_arrays,
              'public_archived_source_maps': source_maps, 'main_functional_source_count': 1019,
              'main_functional_sources_match_public_archived52_full_map': True,
              'main_archived_source_map': {'commit': state['source_commit'], 'path': str(baseline_folder.relative_to(ROOT) / baseline_path), 'sha256': sha(baseline_raw), 'archive_INDEX_sha256': sha(baseline_index_raw)},
              'preparer_executed_or_imported_or_native_or_active_run_output_or_CIM_or_Git_executed_or_read': False,
              'limits': ['Selection is a snapshot of the exact preparer source SHA; rerun source audit if its list or selected bytes change.',
                         'Suffix/UTF8 and numeric-array scans do not alone establish privacy; flagged synthetic text and unsealed metadata require source/provenance review.',
                         'Unsealed observations and flat source seals use explicit literal roles, with no recursive selection. All actual full/native outputs remain excluded.',
                         'No remote/push/publication/merge/full-PASS claim is made. Dated closed-failure/B scalar observations and696 running-metadata copies are historical selected data, not live observer reads or full qualification.']}
    with (HERE / 'AUDIT.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'selected_files': len(rows), 'sealed_packets': len(packets), 'unsealed_folders': len(unsealed),
                      'private_names': named_private, 'encoded_media': encoded_media, 'numeric_array_flagged_files': len(array_flags),
                      'hex_files': len(hex_files), 'main1019_unchanged': True, 'manifest_examined': manifest_facts}))


if __name__ == '__main__': main()

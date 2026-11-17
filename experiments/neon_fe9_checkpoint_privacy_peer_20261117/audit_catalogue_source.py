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
PREPARER = ROOT / 'experiments/prepare_neon_fe9_checkpoint_20261117.py'


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


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    source = PREPARER.read_bytes(); lists = static_lists(source.decode('utf-8-sig'))
    unsealed_whitelist = next(ast.literal_eval(node.value) for node in ast.parse(source.decode('utf-8-sig')).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'UNSEALED' for t in node.targets))
    selected = set(lists['FILES']); packets = []; unsealed = []; array_flags = []; source_maps = []
    original_index_bytes = {}
    for name in lists['FOLDERS']:
        folder = ROOT / 'experiments' / name
        need(folder.is_dir(), 'Selected folder exists')
        files = {p.relative_to(folder).as_posix() for p in folder.rglob('*')
                 if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts}
        index_path = folder / 'INDEX.json'
        if index_path.is_file():
            regular_owned_file(index_path, ROOT); index_raw = index_path.read_bytes(); index = json.loads(index_raw)
            rows = packet_rows(index); original_index_bytes[str(index_path)] = index_raw
            for row in rows:
                relative = Path(row['path']); need(not relative.is_absolute() and '..' not in relative.parts, 'Packet relative path')
                path = folder / relative; regular_owned_file(path, folder); raw = path.read_bytes()
                need(type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Declared payload identity')
                if 'decoded_sha256' in row:
                    decoded = gzip.decompress(raw)
                    need(type(row['decoded_bytes']) is int and len(decoded) == row['decoded_bytes'] and sha(decoded) == row['decoded_sha256'], 'Declared decoded identity')
            declared = {row['path'] for row in rows}
            packets.append({'folder': name, 'INDEX_sha256': sha(index_raw), 'payloads': len(rows),
                            'unlisted_files_excluded_by_preparer': sorted(files - declared - {'INDEX.json'})})
            chosen = [index_path] + [folder / row['path'] for row in rows]
        else:
            need(name in unsealed_whitelist, 'Unfinished packet is outside explicit unsealed whitelist')
            unsealed.append({'folder': name, 'all_local_files_selected_by_fallback': sorted(files)})
            chosen = [folder / relative for relative in files]
        selected.update(p.relative_to(ROOT).as_posix() for p in chosen)
    rows = []; named_private = []; encoded_media = []; hex_files = []
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
                flags = suspicious_arrays(parsed)
                if flags: array_flags.append({'path': relative, 'fields': flags})
                if type(parsed) is dict and type(parsed.get('source_sha256')) is dict and len(parsed['source_sha256']) in (1019, 1029):
                    source_maps.append({'path': relative, 'source_count': len(parsed['source_sha256'])})
        rows.append({'path': relative, 'bytes': len(raw), 'sha256': sha(raw), 'decoded_bytes': len(decoded)})
    # Use only the already public archived source map, not a native/active run.
    baseline_folder = ROOT / 'experiments/native_five_full_actual_20261116'
    baseline_index_raw = (baseline_folder / 'INDEX.json').read_bytes(); baseline_index = json.loads(baseline_index_raw)
    baseline_path = 'run/source-before.json.gz'
    baseline_row = next(r for r in baseline_index['files'] if r['path'] == baseline_path)
    baseline_raw = (baseline_folder / baseline_path).read_bytes()
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
        literal_only = all(prefix in constants and source_text.lower().count(prefix) == 1 for prefix in prefixes)
        media_marker_classification.append({'path': relative, 'classification': 'SCANNER_LITERAL_PREFIXES_ONLY' if literal_only else 'UNRESOLVED_MEDIA_MARKER_REVIEW_REQUIRED'})
    if args.manifest_sha256 is not None:
        # This branch may only be invoked after root says the catalogue exists.
        path = ROOT / 'output/neon-fe9-checkpoint-20261117-manifest.json'
        raw = path.read_bytes(); need(sha(raw) == args.manifest_sha256, 'Exact root catalogue SHA')
        manifest = json.loads(raw)
        need(manifest['format'] == 'has_public_neon_fe9_checkpoint_catalogue_1' and manifest['redesign_merged'] is False
             and manifest['historical_running_observation_not_a_full_pass'] is True and manifest['fe9_closed_failed_stale_Mima_descriptor'] is True
             and manifest['latest00bf_dated_full_observation_not_a_pass'] is True and manifest['closed_375_failure_preserved'] is True
             and manifest['exact71_public_cache_cleanup_completed'] is True and manifest['private_native_art_arrays_media_excluded'] is True,
             'Exact current failed/historical/active checkpoint schema')
        actual = manifest['files']
        expected = [{key: row[key] for key in ('path', 'bytes', 'sha256')} for row in rows]
        expected_indexes = [{'packet': p['folder'], 'index_sha256': p['INDEX_sha256'], 'checked_payloads': p['payloads']} for p in packets]
        encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
        need(encode(actual) == encode(expected) and encode(manifest['source_indexes']) == encode(expected_indexes), 'Catalogue equals independently selected source/payload identities')
        need(type(manifest['main_functional_unchanged']) is int and manifest['main_functional_unchanged'] == 1019, 'Catalogue main source count')
        manifest_facts = {'sha256': sha(raw), 'exact_file_rows_and_sealed_indexes_match': True}
    need(PREPARER.read_bytes() == source, 'Preparer source unchanged during audit')
    for path, raw in original_index_bytes.items(): need(Path(path).read_bytes() == raw, 'Selected INDEX unchanged during audit')
    for row in rows:
        path = ROOT / row['path']; regular_owned_file(path, ROOT); raw = path.read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Selected public file changed during audit')
    report = {'format': 'has_fe9_checkpoint_public_selection_peer_audit_1',
              'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'preparer_sha256': sha(source), 'manifest_examined': manifest_facts,
              'files': rows, 'selected_files': len(rows), 'selected_bytes': sum(r['bytes'] for r in rows),
              'sealed_packets': packets, 'unsealed_fallback_folders': unsealed,
              'private_named_payloads': named_private, 'encoded_media_markers': encoded_media,
              'encoded_media_marker_classification': media_marker_classification,
              'large_numeric_JSON_arrays_for_manual_classification': array_flags, 'hex_payloads_for_manual_classification': hex_files,
              'numeric_array_classification': 'Observed flags are only explicit working_recipe.zero_based_lines EOL recipes' if arrays_are_EOL_recipes else 'UNRESOLVED_NON_EOL_ARRAYS_REQUIRE_MANUAL_REVIEW',
              'public_archived_source_maps': source_maps, 'main_functional_source_count': 1019,
              'main_functional_sources_match_public_archived52_full_map': True,
              'main_archived_source_map': {'commit': state['source_commit'], 'path': str(baseline_folder.relative_to(ROOT) / baseline_path), 'sha256': sha(baseline_raw), 'archive_INDEX_sha256': sha(baseline_index_raw)},
              'preparer_or_native_or_active_run_output_or_CIM_or_Git_executed_or_read': False,
              'limits': ['Selection is a snapshot of the exact preparer source SHA; rerun source audit if its list or selected bytes change.',
                         'Suffix/UTF8 and numeric-array scans do not alone establish privacy; flagged synthetic text and unsealed metadata require source/provenance review.',
                         'Unsealed folders use a recursive all-text-file fallback, not an explicit immutable file allowlist. Final exact catalogue review is required.',
                         'No remote/push/publication/merge/full-PASS claim is made. Active-observation copies are historical dated metadata, not live run reads.']}
    (HERE / 'AUDIT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'selected_files': len(rows), 'sealed_packets': len(packets), 'unsealed_folders': len(unsealed),
                      'private_names': named_private, 'encoded_media': encoded_media, 'numeric_array_flagged_files': len(array_flags),
                      'hex_files': len(hex_files), 'main1019_unchanged': True, 'manifest_examined': manifest_facts}))


if __name__ == '__main__': main()

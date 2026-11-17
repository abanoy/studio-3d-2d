"""Public maps plus three tested shell source files; no Git/native/private IO."""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT / 'experiments/neon_source52_to_3a_root_review_20261117'
PARENT_INDEX = 'a91e9f9656238c2df60492dfa024ebcca7f46b7380da643b9a30b0f48d9fee15'
PARENT_DELTA = '9cbb7d3be7745eafff9e5417d455230a811c9ebfb1f3a78cb5cbd34f0822c817'
MAPS = ROOT / 'experiments/neon_source52_to_3a_delta_draft_20261117'
MAPS_INDEX = 'b0ce3924dcab5d34bacd661753f24431b552b1e7ebaf056712fe2450aade20aa'
CORE = ROOT / 'experiments/neon_owner_admission_shell_eol_20261117'
CORE_INDEX = '8ab1c8eb9f576a9c8a315ebf4df433fc4e4b8b4767ac44cdf64a2403467a2d42'
OLD_CORE_SHA = 'cdad5359f6fe6bf63d93bd95845680dec7f6eb2d041b265d05b05efe3ce1096f'
CORE_SHA = 'c6ebc4b6e3999fbdecf13697a2ccb0ca9f0cafe3368beaf9767bd5f247247f76'
SHELLS = ('tools/linux/liveness_shim.sh', 'tools/linux/run_test.sh', 'tools/linux/shoot.sh')
MAP_NAMES = ('OLD52_RAW_CANONICAL_MAP.json', 'CANDIDATE3A_RAW_CANONICAL_MAP.json')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def encoded(value): return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def render():
    assert sha((PARENT / 'INDEX.json').read_bytes()) == PARENT_INDEX
    parent_raw = (PARENT / 'REVIEWED52_TO_CANDIDATE_DELTA.json').read_bytes(); assert sha(parent_raw) == PARENT_DELTA
    parent = json.loads(parent_raw)
    assert sha((MAPS / 'INDEX.json').read_bytes()) == MAPS_INDEX
    assert sha((CORE / 'INDEX.json').read_bytes()) == CORE_INDEX
    core_raw = (CORE / 'admission_core.py').read_bytes(); assert sha(core_raw) == CORE_SHA
    spec = importlib.util.spec_from_file_location('proposed_three_shell_EOL_core', CORE / 'admission_core.py')
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)  # Public source definitions only.
    original_maps = {}; new_maps = {}; map_bytes = {}; observations = {}
    for name in MAP_NAMES:
        raw = (MAPS / name).read_bytes(); pin = parent['raw_canonical_source_map_files'][name]
        assert (len(raw), sha(raw)) == (pin['bytes'], pin['sha256'])
        original_maps[name] = json.loads(raw)
        anchor = ('"canonicalizer_sha256": "' + OLD_CORE_SHA + '"').encode()
        assert raw.count(anchor) == 1
        map_bytes[name] = raw.replace(anchor, ('"canonicalizer_sha256": "' + CORE_SHA + '"').encode(), 1)
    old = original_maps[MAP_NAMES[0]]['files']; candidate = original_maps[MAP_NAMES[1]]['files']
    assert len(old) == 1019 and len(candidate) == 1029 and not set(SHELLS) & set(old)
    proposed_rows = copy.deepcopy(parent['rows']); lookup = {r['path']: r for r in proposed_rows}
    for name in SHELLS:
        raw = (ROOT / name).read_bytes(); entry = candidate[name]
        assert sha(raw) == entry['raw_sha256'] and b'\r\n' in raw
        assert entry['content_sha256'] == sha(raw) == lookup[name]['new_content_sha256']
        assert lookup[name]['classification'] == 'added' and lookup[name]['old_raw_sha256'] is None
        content = sha(A.canonical(raw, name)); lookup[name]['new_content_sha256'] = content
        anchor = ('"content_sha256": "' + entry['content_sha256'] + '"').encode()
        assert map_bytes[MAP_NAMES[1]].count(anchor) == 1
        map_bytes[MAP_NAMES[1]] = map_bytes[MAP_NAMES[1]].replace(anchor, ('"content_sha256": "' + content + '"').encode(), 1)
        observations[name] = {'working_bytes': len(raw), 'tested_raw_sha256': sha(raw),
                              'CRLF_lines': raw.count(b'\r\n'), 'old_content_sha256': entry['content_sha256'],
                              'new_content_sha256': content, 'working_bytes_changed': False}
    for name in MAP_NAMES: new_maps[name] = json.loads(map_bytes[name])
    assert new_maps[MAP_NAMES[0]]['files'] == old
    for name, entry in candidate.items():
        actual = new_maps[MAP_NAMES[1]]['files'][name]
        assert actual['raw_sha256'] == entry['raw_sha256']
        assert actual == entry if name not in SHELLS else actual['content_sha256'] == observations[name]['new_content_sha256']
    result = A.check_reviewed_delta(old, new_maps[MAP_NAMES[1]]['files'], proposed_rows)
    previous = parent['exact_delta_schema_and_byte_map_join']
    assert {k: v for k, v in result.items() if k != 'new_content_source_map_sha256'} == {k: v for k, v in previous.items() if k != 'new_content_source_map_sha256'}
    assert result['new_content_source_map_sha256'] == '8bd2bf19ddfc4d51644924e60ca6446db252c6928ba91427653652d0508cf7ea'
    for before, after in zip(parent['rows'], proposed_rows):
        expected = copy.deepcopy(before)
        if before['path'] in SHELLS: expected['new_content_sha256'] = observations[before['path']]['new_content_sha256']
        assert after == expected
    proposal = copy.deepcopy(parent)
    proposal['review_status'] = 'PROPOSED_EXACT_THREE_SCRIPT_EOL_CANONICALIZATION_ROOT_REVIEW_REQUIRED'
    proposal['reasons_status'] = 'PARENT_REVIEWED_REASONS_EXACT_SUCCESSOR_REVIEW_PENDING'
    proposal['parent_root_review'] = proposal.pop('root_review')
    proposal['sealed_admission_core_sha256'] = CORE_SHA
    proposal['canonicalization'] = 'Parent canonical function unchanged; exact three named shell paths added to TEXT_PATHS'
    proposal['rows'] = proposed_rows
    proposal['exact_delta_schema_and_byte_map_join'] = result
    proposal['raw_canonical_source_map_files'] = {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in map_bytes.items()}
    proposal['reproducer_sha256'] = sha(Path(__file__).read_bytes())
    proposal['proposal_provenance'] = {'parent_INDEX_sha256': PARENT_INDEX, 'parent_reviewed_delta_sha256': PARENT_DELTA,
        'new_core_INDEX_sha256': CORE_INDEX, 'new_core_sha256': CORE_SHA,
        'Root_approval_of_this_proposal_supplied': False,
        'inherited_parent_status_metadata_retains_its_original_historical_preparation_scope': True,
        'three_content_hash_changes_only_in39_rows': list(SHELLS),
        'all39_reasons_raw_hashes_counts107_EOL_old52_and_native_bridge_unchanged': True,
        'functional_working_or_Git_bytes_changed': False, 'current_full_or_private_outputs_read': False}
    assert proposal['reasons'] == parent['reasons'] and proposal['counts'] == parent['counts']
    assert proposal['raw_EOL_only_differences_excluded_from_delta_rows'] == parent['raw_EOL_only_differences_excluded_from_delta_rows']
    evidence = {'format': 'has_three_shell_EOL_delta_proposal_derivation_1', 'parent_INDEX_sha256': PARENT_INDEX,
        'parent_delta_sha256': PARENT_DELTA, 'new_core_INDEX_sha256': CORE_INDEX, 'new_core_sha256': CORE_SHA,
        'source_observations': observations, 'original39_rows_reasons_and_all_other_raw_and_content_identities_preserved': True,
        'new_content_source_map_sha256': result['new_content_source_map_sha256'],
        'old52_file_entries_and_canonical_aggregate_unchanged': True, 'original107_EOL_list_exact': True,
        'raw1029_source_map_aggregate_unchanged': True, 'A_check_reviewed_delta_passed': True,
        'Root_approval_or_actual_activation_claimed': False, 'native_private_full_process_Git_network_access': False}
    return {**map_bytes, 'PROPOSED52_TO_CANDIDATE_DELTA.json': encoded(proposal), 'DERIVATION.json': encoded(evidence)}


def main():
    outputs = render()
    if sys.argv[1:] == ['--check']:
        assert all((HERE / name).read_bytes() == raw for name, raw in outputs.items())
        print(json.dumps({'reproduction': 'EXACT', 'proposal_only': True})); return
    assert not sys.argv[1:]
    for name, raw in outputs.items():
        with (HERE / name).open('xb') as stream: stream.write(raw)
    print(json.dumps({'proposal_sha256': sha(outputs['PROPOSED52_TO_CANDIDATE_DELTA.json']),
                      'changed_row_fields': 3, 'rows': 39, 'Root_review_pending': True}))


if __name__ == '__main__': main()

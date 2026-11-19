"""Finite synthetic source-weight histories and independent event-model oracle.

No Blender, owner input, filesystem or process API is used by this module.
The tested alphabet is bounded evidence, never a universal storage policy.
"""
import hashlib
import itertools
import math
import struct

GROUP_COUNT = 69
GROUP_IDS = (0, 1, 2, 68)
WEIGHT_WORDS = (0x00000000, 0x80000000, 0x00000001,
                0x3DCCCCCD, 0x3E4CCCCD, 0x3E99999A, 0x3F800000)
CASE_COUNT = 21_952
POSITIVE_WRITE_COUNT = 47_040
EXPECTED_GROUP_HISTOGRAM = {0: 512, 1: 6740, 2: 11700, 3: 3000}
MAX_EXAMPLES = 12
SOURCEIO_IMPORTER_SHA256 = '173a34ecae50e0b7a9d467908f238c02d5d7e19df3c7f52387534914d703233b'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def word_float(word):
    require(type(word) is int and word in WEIGHT_WORDS, 'Finite fixture weight word required')
    return struct.unpack('<f', struct.pack('<I', word))[0]


def float_word(value):
    require(type(value) is float and math.isfinite(value), 'Finite RNA float readback required')
    try:
        packed = struct.pack('<f', value)
    except (OverflowError, struct.error) as error:
        raise ValueError('Readback outside F32') from error
    require(struct.unpack('<f', packed)[0] == value, 'Non-binary32 readback refused without rounding')
    return struct.unpack('<I', packed)[0]


def cases():
    """Immutable three-slot cases; zero slots already cover shorter histories."""
    return tuple(tuple(zip(groups, words))
                 for groups in itertools.product(GROUP_IDS, repeat=3)
                 for words in itertools.product(WEIGHT_WORDS, repeat=3))


def expected_row(case):
    """Independent event relation: earliest positive event orders each group;
    latest positive event supplies its value. This is a hypothesis to observe.
    """
    require(type(case) is tuple and len(case) == 3, 'Exact three-slot fixture required')
    events = []
    for slot, pair in enumerate(case):
        require(type(pair) is tuple and len(pair) == 2 and
                type(pair[0]) is int and pair[0] in GROUP_IDS and
                type(pair[1]) is int and pair[1] in WEIGHT_WORDS, 'Fixture alphabet differs')
        group, word = pair
        if word not in (0x00000000, 0x80000000):
            events.append((slot, group, word))
    groups = {group for _, group, _ in events}
    first = {group: min(slot for slot, other, _ in events if other == group) for group in groups}
    last = {group: max((slot, word) for slot, other, word in events if other == group)[1] for group in groups}
    return tuple((group, last[group]) for group in sorted(groups, key=first.get))


def case_digest(catalogue):
    require(type(catalogue) is tuple and len(catalogue) == CASE_COUNT, 'Complete finite case catalogue required')
    digest = hashlib.sha256()
    for case in catalogue:
        expected_row(case)  # Exact domain and type check.
        digest.update(struct.pack('<3B3I', *(group for group, _ in case), *(word for _, word in case)))
    return digest.hexdigest()


def row_digest(rows):
    digest = hashlib.sha256()
    for index, row in enumerate(rows):
        require(type(row) is tuple and len(row) <= GROUP_COUNT, 'Bounded ordered readback row required')
        digest.update(struct.pack('<IH', index, len(row)))
        for pair in row:
            require(type(pair) is tuple and len(pair) == 2 and type(pair[0]) is int and
                    0 <= pair[0] < GROUP_COUNT and type(pair[1]) is int and
                    0 <= pair[1] <= 0xFFFFFFFF, 'Exact readback group/F32 word required')
            digest.update(struct.pack('<BI', *pair))
    return digest.hexdigest()


def compare_readback(catalogue, observed):
    require(type(catalogue) is tuple and len(catalogue) == CASE_COUNT, 'Complete finite catalogue required')
    require(type(observed) is tuple and len(observed) <= CASE_COUNT + 1, 'Bounded observed rows required')
    expected = tuple(expected_row(case) for case in catalogue)
    expected_hash, observed_hash = row_digest(expected), row_digest(observed)
    counts = {'row_missing': 0, 'ordered_group_relation': 0, 'weight_word': 0}
    mismatches, examples = 0, []
    histogram = {index: 0 for index in range(4)}
    for index, want in enumerate(expected):
        histogram[len(want)] += 1
        actual = observed[index] if index < len(observed) else None
        reasons = []
        if actual is None:
            reasons.append('row_missing')
        else:
            if tuple(group for group, _ in actual) != tuple(group for group, _ in want):
                reasons.append('ordered_group_relation')
            if tuple(word for _, word in actual) != tuple(word for _, word in want):
                reasons.append('weight_word')
        if reasons:
            mismatches += 1
            for reason in reasons:
                counts[reason] += 1
            if len(examples) < MAX_EXAMPLES:
                examples.append({'case_index': index,
                                 'slot_groups': [group for group, _ in catalogue[index]],
                                 'slot_weight_words': [f'{word:08x}' for _, word in catalogue[index]],
                                 'expected': [[group, f'{word:08x}'] for group, word in want],
                                 'observed': None if actual is None else [[group, f'{word:08x}'] for group, word in actual],
                                 'reasons': reasons})
    extra = max(0, len(observed) - len(expected))
    return {'observed_rows': len(observed), 'expected_rows': len(expected),
            'mismatch_cases': mismatches, 'extra_observed_rows': extra,
            'mismatch_counts': counts, 'bounded_examples': examples,
            'expected_ordered_rows_sha256': expected_hash,
            'observed_ordered_rows_sha256': observed_hash,
            'expected_group_count_histogram': histogram,
            'all_cases_match': mismatches == 0 and extra == 0}


def qualify_background_receipt(receipt):
    """Check the existing wrapper's background placement evidence; no UI calls.

    A private graphical window is not required for this background API probe.
    Wrapper child-desktop confirmation is mandatory. Its receipt may use thread
    lookup or an owned enumerated window; a headless bypass is not supplied.
    """
    require(type(receipt) is dict and receipt.get('format') == 'studio_private_desktop_1', 'Wrapper receipt schema differs')
    expected = {'exit': 0, 'child_desktop_confirmed': True, 'foreground_child_observed': False,
                'desktop_switch_requested': False, 'job_closed': True, 'desktop_closed': True}
    for name, value in expected.items():
        require(type(receipt.get(name)) is type(value) and receipt[name] == value,
                'Background wrapper receipt refused: ' + name)
    require(type(receipt.get('private_window_seen')) is bool, 'Window observation must remain explicit')
    require(not any(key in receipt for key in ('error', 'monitor_error', 'cancelled')), 'Wrapper reported failure')
    return {'background_private_desktop_confirmed': True,
            'private_window_seen': receipt['private_window_seen'],
            'visible_window_required': False, 'native_storage_rule_qualified': False}


def _typed_equal(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_typed_equal(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(_typed_equal(a, b) for a, b in zip(left, right))
    return left == right


def validate_matching_public_report(report, *, expected_request_sha256, expected_run_id, expected_scripts, expected_runtime):
    """Pure pass-evidence parser; Root separately binds actual execution/receipt.

    Rejects mismatch/failed results rather than rewriting them. Those result
    files remain diagnostic evidence. A valid return is not storage qualification.
    """
    require(type(report) is dict, 'Public observation object required')
    fixed = {'format': 'has_synthetic_blender_weight_storage_observation_1',
             'status': 'BOUNDED_SYNTHETIC_STORAGE_MATCH', 'case_count': CASE_COUNT,
             'run_id': expected_run_id, 'sourceio_importer_rule_sha256': SOURCEIO_IMPORTER_SHA256,
             'group_count': GROUP_COUNT, 'group_alphabet': list(GROUP_IDS),
             'weight_word_alphabet': [f'{word:08x}' for word in WEIGHT_WORDS],
             'expected_positive_add_calls': POSITIVE_WRITE_COUNT, 'positive_add_calls': POSITIVE_WRITE_COUNT,
             'native_storage_rule_qualified': False, 'universal_group_or_F32_domain_qualified': False,
             'actual_source_rows_or_saved_scene_qualified': False,
             'native_fidelity_export_repair_adoption_qualified': False,
             'immediate_vs_after_validate_exact': True, 'synthetic_group_indices_exact': True,
             'owned_object_mesh_cleanup_exact': True, 'cleanup_error_types': [],
             'runtime_binary_hash_verified_by_probe': False,
             'native_API_execution_observed_by_this_script': True,
             'factory_background_no_model_file': True, 'scene_or_native_model_files_opened': False,
             'files_exported_or_blend_saved': False, 'window_or_desktop_API_called_by_probe': False,
             'request_sha256': expected_request_sha256, 'copied_script_identities': expected_scripts,
             'Root_expected_runtime_identity': expected_runtime}
    additional = {'case_catalogue_sha256', 'immediate', 'after_validate', 'mesh_validate_reported_change',
                  'runtime_version', 'runtime_version_string', 'runtime_build_hash'}
    require(set(report) == set(fixed) | additional, 'Closed public observation fields required')
    for name, value in fixed.items():
        require(name in report and _typed_equal(report[name], value), 'Public observation refused: ' + name)
    require(type(report.get('run_id')) is str and len(report['run_id']) == 32 and
            all(value in '0123456789abcdef' for value in report['run_id']), 'Public run ID differs')
    require('error_type' not in report and type(report.get('mesh_validate_reported_change')) is bool,
            'Public observation reported an error or invalid validate result')
    require(type(report.get('runtime_version')) is list and len(report['runtime_version']) == 3 and
            all(type(value) is int and 0 <= value <= 1000 for value in report['runtime_version']),
            'Runtime version observation differs')
    require(all(type(report.get(name)) is str and 0 < len(report[name]) <= 128
                for name in ('runtime_version_string', 'runtime_build_hash')), 'Bounded runtime build strings required')
    catalogue = cases()
    require(report.get('case_catalogue_sha256') == case_digest(catalogue), 'Finite catalogue hash differs')
    ordered_hash = row_digest(tuple(expected_row(case) for case in catalogue))
    for phase in ('immediate', 'after_validate'):
        evidence = report.get(phase)
        wanted = {'observed_rows': CASE_COUNT, 'expected_rows': CASE_COUNT, 'mismatch_cases': 0,
                  'extra_observed_rows': 0, 'mismatch_counts': {'row_missing': 0, 'ordered_group_relation': 0, 'weight_word': 0},
                  'bounded_examples': [], 'expected_ordered_rows_sha256': ordered_hash,
                  'observed_ordered_rows_sha256': ordered_hash,
                  'expected_group_count_histogram': {str(key): value for key, value in EXPECTED_GROUP_HISTOGRAM.items()},
                  'all_cases_match': True}
        require(_typed_equal(evidence, wanted), 'Public finite readback evidence differs: ' + phase)
    return {'bounded_synthetic_report_matches': True, 'case_catalogue_sha256': case_digest(catalogue),
            'ordered_rows_sha256': ordered_hash, 'native_storage_rule_qualified': False,
            'universal_or_actual_source_row_policy_qualified': False}

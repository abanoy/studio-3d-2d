"""Exact recorded-handler metadata matching; no model load or callback call.

File reads occur only in read_bound_baseline, later under Root's owned driver.
No path obtained from a callback is opened. Runtime globals are not observed.
"""
import hashlib
import json
from pathlib import Path
import baseline_predicate as B
from handler_metadata import capture_handlers

CAPTURE_SHA256 = 'bf55509b28438aa532063168a502bd8a4a8c509108d7f0338c6eba37bbd08cef'
CAPTURE_BYTES = 2005
PUBLIC_RELATIVE = {
    'POSE_LIBRARY_GUI': 'addons_core/pose_library/gui.py',
    'COPY_GLOBAL_TRANSFORM': 'startup/bl_operators/copy_global_transform.py',
}
PHASES = ('BEFORE_OWNED_B_OPEN', 'AFTER_OWNED_B_OPEN', 'AFTER_RESOURCE_COLLECTION')


def need(value, message):
    if not value:
        raise ValueError(message)


def validate_descriptor(value):
    need(type(value) is dict and set(value) == {'capture', 'public_sources'}, 'Exact factory-baseline descriptor required')
    need(type(value['public_sources']) is dict and set(value['public_sources']) == set(B.SOURCES), 'Exact two public-source roles required')
    rows = [value['capture'], *value['public_sources'].values()]
    for row in rows:
        need(type(row) is dict and set(row) == {'path', 'bytes', 'mtime_ns', 'sha256'}, 'Exact stable file descriptor required')
        need(type(row['path']) is str and row['path'] and '\0' not in row['path'], 'Explicit file path required')
        need(type(row['bytes']) is int and row['bytes'] > 0 and type(row['mtime_ns']) is int and row['mtime_ns'] > 0,
             'Positive integer identity stamps required')
    need(value['capture']['bytes'] == CAPTURE_BYTES and value['capture']['sha256'] == CAPTURE_SHA256,
         'Only the exact historical private metadata capture may supply this baseline')
    for role, expected in B.SOURCES.items():
        row = value['public_sources'][role]
        need({key: row[key] for key in ('bytes', 'sha256')} == expected, 'Pinned whole public source differs')
        need(row['path'].replace('\\', '/').endswith('/' + PUBLIC_RELATIVE[role]), 'Explicit approved public-source pathname required')
    need(len({row['path'] for row in rows}) == 3, 'Distinct explicit baseline paths required')
    return value


def read_bound_baseline(descriptor, reader, safe, root):
    """Root-only later: validate identities before and after bounded known reads."""
    validate_descriptor(descriptor)
    capture_path = safe(descriptor['capture']['path'])
    need(capture_path.is_relative_to(root / 'output'), 'Historical baseline stays in private ROOT/output')
    bodies = {}
    for role, row in [('capture', descriptor['capture']), *descriptor['public_sources'].items()]:
        path = safe(row['path'])
        expected = {key: row[key] for key in ('bytes', 'mtime_ns', 'sha256')}
        need(reader.identity(path, single_link=True) == expected, 'Baseline/public-source identity changed')
        raw = path.read_bytes()
        need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Baseline/public-source read differs')
        need(reader.identity(path, single_link=True) == expected, 'Baseline/public-source changed during read')
        bodies[role] = raw
    capture = json.loads(bodies['capture'])
    trusted_paths = {role: row['path'] for role, row in descriptor['public_sources'].items()}
    identities = {role: {key: row[key] for key in ('bytes', 'sha256')} for role, row in descriptor['public_sources'].items()}
    B.validate_baseline(capture, trusted_paths, identities)
    return {'capture': capture, 'trusted_paths': trusted_paths, 'source_identities': identities}


def assert_same_handler_fields(observed, expected):
    """Both inputs must have been captured by the bounded metadata collector."""
    need(observed['handler_list_counts'] == expected['handler_list_counts']
         and observed['callbacks'] == expected['callbacks'], 'Extra, different or reordered live handler metadata refused')


def check_live(handlers, bound, phase):
    need(phase in PHASES, 'Explicit live-observation phase required')
    B.validate_baseline(bound['capture'], bound['trusted_paths'], bound['source_identities'])
    raw, _ = capture_handlers(handlers)
    observed = json.loads(raw)
    # The unmodified capture helper's legacy phase/flags describe its own
    # metadata collection. They are discarded for post-load observations.
    assert_same_handler_fields(observed, bound['capture'])
    # The bound historical capture has already passed the original predicate.
    # Exact field equality to it admits the live identity fields without
    # treating the legacy collector's phase/flags as post-load assertions.
    return {'format': 'has_private_known_factory_handler_identity_observation_1',
            'phase': phase, 'baseline_capture_sha256': CAPTURE_SHA256,
            'handler_list_counts': observed['handler_list_counts'], 'callbacks': observed['callbacks'],
            'recorded_metadata_exact_match': True, 'metadata_collection_calls_callbacks': False,
            'loader_callbacks_may_have_run': phase != PHASES[0],
            'runtime_globals_observed': False, 'callback_behavior_or_global_safety_proved': False}


def public_summary():
    return {'format': 'has_known_factory_handler_resource_profile_1',
            'baseline_capture_sha256': CAPTURE_SHA256, 'handler_lists': 11, 'callbacks': 3,
            'slots': [dict(row) for row in B.SLOTS],
            'public_source_identities': {role: dict(value) for role, value in B.SOURCES.items()},
            'before_load_and_after_load_metadata_match_required': True,
            'loader_callbacks_may_have_run': True, 'runtime_globals_observed': False,
            'callback_behavior_or_global_safety_proved': False, 'IO_confinement_proved': False,
            'old_strict31_native_pass': False}

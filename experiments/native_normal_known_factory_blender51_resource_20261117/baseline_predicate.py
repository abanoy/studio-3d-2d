"""Pure fixed metadata baseline/projection; no IO, callback call or native admission."""
import hashlib
import json

COUNTS = {'load_pre': 1, 'load_post': 2, 'load_post_fail': 0, 'depsgraph_update_pre': 0, 'depsgraph_update_post': 0, 'frame_change_pre': 0, 'frame_change_post': 0, 'render_pre': 0, 'render_post': 0, 'save_pre': 0, 'save_post': 0}
SOURCES = {'POSE_LIBRARY_GUI': {'bytes': 7510, 'sha256': 'abdd0336bd48e66bcd35d6282d5374d3bfa39974c4dbe30090ee0ea0e2670057'}, 'COPY_GLOBAL_TRANSFORM': {'bytes': 30603, 'sha256': 'ea911fd6ba24224a15800409c66843b8f37a4dc6deb8ae256d75e9d184c70552'}}
SLOTS = [{'handler_list': 'load_pre', 'index': 0, 'source_role': 'POSE_LIBRARY_GUI', 'public_role': 'POSE_MESSAGE_BUS_PRE', 'metadata_signature': '15396c13c4acba669a4eaa80b461c936f19203deba081de105b5c3ee19e3cbc8'}, {'handler_list': 'load_post', 'index': 0, 'source_role': 'COPY_GLOBAL_TRANSFORM', 'public_role': 'TRANSFORM_MESSAGE_BUS_POST', 'metadata_signature': '746537657ec8d2843ce1dfcce2d827e8c8142d13befaa92be24527df428598c9'}, {'handler_list': 'load_post', 'index': 1, 'source_role': 'POSE_LIBRARY_GUI', 'public_role': 'POSE_MESSAGE_BUS_POST', 'metadata_signature': '7de470d1f831e59711fad7a16ffadb8088c8e6508d20404ffd7a392d007acc59'}]
FIELDS = {'handler_list', 'index', 'kind', 'name', 'module', 'qualname', 'code_filename', 'first_line', 'bytecode_sha256'}
FLAGS = ('callbacks_called', 'code_paths_opened', 'known_B_opened', 'resource_collector_invoked', 'resource_or_native_PASS')

def need(ok, message):
    if not ok: raise ValueError(message)

def signature(row, source_role):
    fields = {key: row[key] for key in FIELDS - {'code_filename'}}
    fields['source_role'] = source_role
    return hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def _normalize(capture, trusted_paths, source_identities):
    need(type(capture) is dict and set(capture) == {'format', 'phase', 'handler_list_counts', 'callbacks', *FLAGS}, 'Exact capture fields required')
    need(capture['format'] == 'has_private_Blender_factory_handler_metadata_1' and capture['phase'] == 'FACTORY_BEFORE_KNOWN_B_OPEN', 'Exact before-model metadata phase required')
    need(all(capture[key] is False for key in FLAGS), 'Capture must not call/load/qualify anything')
    counts = capture['handler_list_counts']
    need(type(counts) is dict and counts.keys() == COUNTS.keys() and all(type(counts[k]) is int and counts[k] == COUNTS[k] for k in COUNTS), 'Exact all-eleven handler counts required')
    need(type(trusted_paths) is dict and set(trusted_paths) == set(SOURCES) and all(type(v) is str and v and '\0' not in v for v in trusted_paths.values()) and len(set(trusted_paths.values())) == 2, 'Explicit distinct trusted public source paths required')
    need(type(source_identities) is dict and set(source_identities) == set(SOURCES), 'Exact public-source roles required')
    for role, expected in SOURCES.items():
        actual = source_identities[role]
        need(type(actual) is dict and set(actual) == {'bytes', 'sha256'} and type(actual['bytes']) is int
             and type(actual['sha256']) is str and actual == expected, 'Pinned whole public source identity differs')
    rows = capture['callbacks']; need(type(rows) is list and len(rows) == 3, 'Exact three callback rows required')
    normalized = []
    for row in rows:
        need(type(row) is dict and set(row) == FIELDS and row['kind'] == 'PYTHON_FUNCTION', 'Exact Python-function metadata row required')
        need(type(row['index']) is int and row['index'] >= 0 and type(row['first_line']) is int and row['first_line'] > 0, 'Exact index/line types required')
        need(all(type(row[k]) is str and row[k] and len(row[k].encode('utf-8')) <= 4096 and '\0' not in row[k]
                 for k in FIELDS - {'index', 'first_line'}), 'Bounded scalar callback metadata required')
        roles = [role for role,path in trusted_paths.items() if row['code_filename'] == path]
        need(len(roles) == 1, 'Callback path must equal an explicit trusted source; no path is opened')
        role = roles[0]
        normalized.append({'handler_list': row['handler_list'], 'index': row['index'], 'source_role': role,
                           'metadata_signature': signature(row, role)})
    return normalized

def _check_normalized(rows):
    expected = [{k: row[k] for k in ('handler_list', 'index', 'source_role', 'metadata_signature')} for row in SLOTS]
    need(rows == expected, 'Exact ordered callback metadata/source-role identities differ')
    return True

def validate_baseline(capture, trusted_paths, source_identities):
    """Match the recorded fields only; supplied source identities are caller evidence."""
    return _check_normalized(_normalize(capture, trusted_paths, source_identities))

def _public_payload():
    return {'format': 'has_factory_handler_public_metadata_projection_1',
            'status': 'RECORDED_METADATA_MATCHES_PINNED_PUBLIC_STARTUP_SOURCES_ONLY',
            'handler_lists': 11, 'callbacks': 3, 'slots': [dict(row) for row in SLOTS],
            'public_source_identities': {role: dict(value) for role,value in SOURCES.items()},
            'runtime_co_names_or_globals_observed': False, 'callbacks_invoked': False,
            'known_B_opened': False, 'resource_inventory_observed': False,
            'handler_safety_or_future_admission_proved': False, 'current_full_context_established': False,
            'old_strict31_native_PASS': False, 'native_fidelity_repair_export_or_adoption': False}

def project_capture(capture, trusted_paths, source_identities):
    validate_baseline(capture, trusted_paths, source_identities)
    return _public_payload()

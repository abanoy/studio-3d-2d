"""Pure future Root-issued current-context checks; no current authority exists here."""
import datetime
import re

PROFILE = 'SESSION_B_READONLY_KNOWN_FACTORY_RESOURCE_DIAGNOSTIC'
ROOT_FUNCTIONAL_COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'
EXPECTED_METADATA_HEAD = 'dcbeb9dddb4326d80ad1f24ae135fd7bda7be152'
EXPECTED_REVIEW_COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'
QUALIFICATIONS = ('preload_IO_confinement', 'historical_generation', 'export_equivalence',
                  'normal_repair', 'native_fidelity', 'artifact_adoption', 'legacy_strict_survey_native_pass')
PROOFS = {'functional_snapshot', 'review_functional_snapshot', 'closed_lane_root_record'}


def need(value, message):
    if not value:
        raise ValueError(message)


def validate_admission(value, now):
    need(type(value) is dict and value.get('format') == 'has_session_B_known_factory_resource_admission_1', 'New known-factory admission schema required')
    need(value.get('profile') == PROFILE and value.get('root_native_lane_exclusive') is True,
         'Separate Root-owned known-factory diagnostic profile required')
    need(value.get('loader_readonly_dependency_resolution_authorized') is True, 'Read-only loader dependency resolution authorization required')
    need(type(value.get('claims')) is dict and set(value['claims']) == set(QUALIFICATIONS)
         and all(item is False for item in value['claims'].values()), 'All qualification claims must remain false')
    for key in ('expected_metadata_head', 'functional_commit', 'candidate_commit'):
        need(type(value.get(key)) is str and re.fullmatch('[a-f0-9]{40}', value[key]), 'Future exact commit binding required')
    need(value['functional_commit'] == ROOT_FUNCTIONAL_COMMIT and value['candidate_commit'] == EXPECTED_REVIEW_COMMIT,
         'Exact qualified tested1029 Main and candidate source roles required')
    need(type(value.get('functional_count')) is int and value['functional_count'] == 1029
         and type(value.get('candidate_functional_count')) is int and value['candidate_functional_count'] == 1029,
         'Exact tested1029 Main and Review counts required')
    need(value['expected_metadata_head'] == EXPECTED_METADATA_HEAD, 'Exact dcb Main metadata checkpoint required')
    need(value.get('cold187_disposition') == 'NOT_STARTED_CURRENT_CONTEXT', 'Fresh explicit Root cold187 disposition required')
    issued = datetime.datetime.fromisoformat(value['issued_utc']); expires = datetime.datetime.fromisoformat(value['expires_utc'])
    need(issued.tzinfo is not None and expires.tzinfo is not None and issued <= now < expires
         and 0 < (expires - issued).total_seconds() <= 600, 'Fresh bounded Root authority required')
    need(set(value.get('proofs', {})) == PROOFS, 'Current closed-lane record and both current source maps required')
    need(set(value.get('protected_originals', {})) == {'blend', 'glb', 'parameters'}, 'Exact known B companions required')
    need(type(value.get('factory_baseline')) is dict, 'Explicit historical metadata/public-source descriptor required')
    return value


def validate_current_closed_lane(value, data):
    """A Root-issued scalar record is authority; the driver also observes scopes."""
    record = data['closed_lane_root_record']
    need(type(record) is dict and record.get('format') == 'has_root_known_factory_resource_current_closed_lane_1',
         'Current Root closed-lane schema required; old00bf authority is not accepted')
    for key in ('root_native_lane_exclusive', 'ui_lane_closed', 'all_owned_jobs_desktops_closed', 'source_unchanged'):
        need(record.get(key) is True, 'Current closed UI/native lane and unchanged source required')
    for key in ('current_full_run_active', 'current_targeted_run_active', 'cold187_launched', 'termination_issued', 'full_suite_pass_claimed'):
        need(record.get(key) is False, 'No active run, interruption, cold187 or full-PASS substitution permitted')
    need(all(type(record.get(key)) is int and record[key] == 0 for key in ('owned_count', 'main_count', 'neon_count')),
         'Fresh actual empty Root and Review scopes required')
    for key, wanted in (
        ('root_metadata_head', value['expected_metadata_head']),
        ('root_functional_commit', value['functional_commit']), ('root_functional_count', 1029),
        ('review_commit', value['candidate_commit']), ('review_functional_count', 1029),
        ('root_snapshot_sha256', value['proofs']['functional_snapshot']['sha256']),
        ('review_snapshot_sha256', value['proofs']['review_functional_snapshot']['sha256']),
        ('cold187_disposition', value['cold187_disposition']),
    ):
        need(type(record.get(key)) is type(wanted) and record[key] == wanted, 'Current authority/source-map join differs')
    observed = datetime.datetime.fromisoformat(record['observed_utc'])
    issued = datetime.datetime.fromisoformat(value['issued_utc'])
    need(observed.tzinfo is not None and observed <= issued and (issued - observed).total_seconds() <= 120,
         'Fresh Root scope authority must precede admission by at most120seconds')

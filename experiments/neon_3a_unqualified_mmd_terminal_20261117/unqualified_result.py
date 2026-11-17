"""Closure-only signature; never accepts or rewrites a qualified full result."""
import math

QUALIFICATION = 'UNQUALIFIED_MMD_POSED_FIXTURE_MISSING'
MISSING = 'posed_model_video_1'
UNQUALIFIED_SUMMARY = {
    'qualification': QUALIFICATION,
    'software_completed': True,
    'native_mmd_owner_acceptance': False,
    'required_full_result_groups': 158,
    'observed_result_groups': 157,
    'required_movie_groups': 21,
    'observed_movie_groups': 20,
    'missing_result_keys': [MISSING],
    'actual_mmd_tested': False,
    'pose_checks': 37,
    'merge_copy_or_cold187_authorized': False,
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def validate_unqualified_result(value, context, registry):
    need(type(value) is dict and type(registry) is dict, 'Exact unqualified dictionaries required')
    expected = registry['expected_result_keys']
    movies = registry['expected_movie_keys']
    core = registry['expected_core_process_keys']
    need(len(expected) == len(set(expected)) == 158 and len(movies) == len(set(movies)) == 21
         and len(core) == len(set(core)) == 36 and MISSING in expected and MISSING in movies,
         'Original complete158/36/21 registry must remain intact')
    need(registry['source_commit'] == context['commit'], 'Unchanged candidate registry context required')
    need(len(value) == 157 and set(value) == set(expected) - {MISSING}, 'Only the exact missing posed1 signature is admitted')
    need(value['actual_mmd_tested'] is False and type(value['pose_checks']) is int
         and value['pose_checks'] == 37, 'Exact false-MMD/37-check refusal signature required')
    actual_core = {name: row for name, row in value.items()
                   if type(row) is dict and set(row) == {'exit', 'seconds'}}
    need(set(actual_core) == set(core), 'Original36 named core scopes required for closure')
    for row in actual_core.values():
        need(type(row['exit']) is int and row['exit'] == 0 and type(row['seconds']) in (int, float)
             and math.isfinite(row['seconds']) and row['seconds'] >= 0, 'Core software completion differs')
    actual_movies = {name: row for name, row in value.items()
                     if type(row) is dict and set(row) == {'frames', 'fps', 'duration'}}
    need(set(actual_movies) == set(movies) - {MISSING}, 'Only20 actual movies with posed0 are admitted')
    for row in actual_movies.values():
        try:
            duration = float(row['duration'])
        except (ValueError, TypeError, OverflowError):
            raise ValueError('Actual movie duration differs') from None
        need(type(row['frames']) is int and row['frames'] == 48 and row['fps'] == '24/1'
             and type(row['duration']) in (str, int, float) and math.isfinite(duration)
             and abs(duration - 2) < .01, 'Actual movie scalar completion differs')
    neon = value['neon_workspace']
    counts = {'inset': 12384, 'behavior': 32, 'compact': 14, 'rail': 45, 'lifecycle': 29}
    need(type(neon) is dict and neon['format'] == 'has_neon_workspace_verification_1'
         and neon['passed'] is True and type(neon['checks']) is int and neon['checks'] == 12504
         and type(neon['failures']) is int and neon['failures'] == 0
         and type(neon['expected_checks']) is dict and set(neon['expected_checks']) == set(counts)
         and all(type(neon['expected_checks'][key]) is int and neon['expected_checks'][key] == count
                 for key, count in counts.items())
         and set(neon['reports']) == set(counts)
         and neon['all_functional_sources_hash_size_mtime_unchanged'] is True
         and neon['all_private_jobs_and_desktops_closed'] is True, 'Neon scalar/source/closure signature differs')
    return dict(UNQUALIFIED_SUMMARY)

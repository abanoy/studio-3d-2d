"""Pure explicit scalar projection. NOT a full-suite validator or archive entry.

No file/process/API imports: actual report admission and publication are absent.
Unknown nested report content is neither copied nor stringified in errors.
"""
import math
import re

COUNTS = {'inset': 12384, 'behavior': 32, 'compact': 14, 'rail': 45, 'lifecycle': 29}
LIFECYCLE = ['theme-detach-reentry-reparent-free', 'queued-owner', 'immediate-free-resize']


class Refusal(ValueError): pass


def need(value, message):
    if not value: raise Refusal(message)


def integer(value, expected):
    return type(value) is int and value == expected


def finite(value, low=0, high=1e12):
    if type(value) not in (int, float): return False
    try: return math.isfinite(value) and low <= value <= high
    except (OverflowError, ValueError): return False


def names(values, count):
    need(type(values) is list and len(values) == count, 'Fixed registry membership required')
    need(all(type(v) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', v) for v in values),
         'Only source-authored result names admitted')
    need(len(set(values)) == count, 'Unique source-authored result names required')
    return set(values)


def neon_projection(neon, expected_behavior_names):
    need(type(neon) is dict and neon.get('format') == 'has_neon_workspace_verification_1'
         and neon.get('passed') is True and integer(neon.get('checks'), 12504)
         and integer(neon.get('failures'), 0), 'Neon scalar result differs')
    expected = neon.get('expected_checks')
    need(type(expected) is dict and set(expected) == set(COUNTS)
         and all(integer(expected[k], v) for k, v in COUNTS.items()), 'Neon split differs')
    need(neon.get('all_functional_sources_hash_size_mtime_unchanged') is True
         and neon.get('all_private_jobs_and_desktops_closed') is True,
         'Neon reported source/receipt closure flags differ')
    reports = neon.get('reports')
    need(type(reports) is dict and set(reports) == set(COUNTS), 'All five Neon cases required')
    out = {}
    for name, count in COUNTS.items():
        value = reports[name]
        need(type(value) is dict and type(value.get('result')) is dict, 'Neon result container differs')
        result = value['result']; process = value.get('process')
        need(integer(result.get('checks'), count) and integer(result.get('failures'), 0),
             'Neon constituent count/failure differs')
        need(type(process) is dict and integer(process.get('exit'), 0)
             and process.get('reaped') is True and process.get('timed_out') is False
             and finite(process.get('seconds')), 'Neon reported process outcome differs')
        row = {'checks': count, 'failures': 0, 'headless': name == 'inset',
               'process': {'exit': 0, 'reaped': True, 'timed_out': False, 'seconds': process['seconds']}}
        need(value.get('headless') is row['headless'], 'Neon execution kind differs')
        if name == 'inset':
            need(result.get('status') == 'PASS' and integer(result.get('configurations'), 576)
                 and result.get('native_assets_used') is False, 'Inset fixture/configuration differs')
            need(finite(result.get('maximum_projection_error_pixels'), 0, .01)
                 and result['maximum_projection_error_pixels'] < .01
                 and finite(result.get('maximum_ray_error'), 0, .000003)
                 and result['maximum_ray_error'] < .000003, 'Inset numerical bounds differ')
            row.update(configurations=576, native_assets_used=False,
                       maximum_projection_error_pixels=result['maximum_projection_error_pixels'],
                       maximum_ray_error=result['maximum_ray_error'])
        elif name == 'behavior':
            need(result.get('format') == 'has_neon_behavior_regression_result_1'
                 and integer(result.get('expected_checks'), 32)
                 and result.get('complete_assertion_set') is True,
                 'Behavior result format/assertion set differs')
            need(type(expected_behavior_names) in (list, tuple) and len(expected_behavior_names) == 32
                 and all(type(n) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', n)
                         for n in expected_behavior_names), 'Frozen behavior names required')
            need(len(set(expected_behavior_names)) == 32, 'Unique frozen behavior names required')
            named = result.get('named_checks')
            need(type(named) is dict and set(named) == set(expected_behavior_names)
                 and all(v is True for v in named.values()), 'Behavior named predicates differ')
            for key in ('synthetic_included_assets_only', 'save_and_fullscreen_actions_instrumented',
                        'refresh_preserved_faded_context'):
                need(result.get(key) is True, 'Behavior scope/context differs')
                row[key] = True
            row['named_checks'] = {n: True for n in sorted(expected_behavior_names)}
        elif name == 'compact':
            need(result.get('native_owner_assets_used') is False
                 and result.get('compact_timeline_preserved') is True, 'Compact scope differs')
            samples = result.get('samples')
            need(type(samples) is list and len(samples) == 3, 'Compact sample set differs')
            selected = []
            for value, expected_row in zip(samples, (0, 32, 63), strict=True):
                need(type(value) is dict and integer(value.get('row'), expected_row)
                     and value.get('visible_before_route') is True
                     and value.get('selected_after_route') is True
                     and finite(value.get('viewport_height'), 26, 115)
                     and value['viewport_height'] < 115
                     and finite(value.get('scroll_vertical')), 'Compact route/viewport differs')
                selected.append({'row': expected_row, 'visible_before_route': True,
                                 'selected_after_route': True, 'viewport_height': value['viewport_height'],
                                 'scroll_vertical': value['scroll_vertical']})
            row.update(samples=selected, native_owner_assets_used=False, compact_timeline_preserved=True)
        elif name == 'rail':
            need(result.get('format') == 'has_neon_rail_placement_regression_1'
                 and result.get('synthetic_fixture_only') is True
                 and result.get('screenshots_written') is False, 'Rail scope differs')
            row.update(synthetic_fixture_only=True, screenshots_written=False)
        elif name == 'lifecycle':
            need(result.get('format') == 'has_neon_world_rail_lifecycle_1'
                 and type(result.get('cases')) is list and result['cases'] == LIFECYCLE
                 and result.get('source_only_fixture_uses_native_models') is False, 'Lifecycle scope differs')
            row.update(cases=list(LIFECYCLE), source_only_fixture_uses_native_models=False)
        out[name] = row
    return {'checks': 12504, 'failures': 0, 'expected_checks': dict(COUNTS), 'reports': out,
            'reported_functional_sources_unchanged': True, 'reported_private_jobs_closed': True,
            'physical_receipts_must_be_independently_bound': True}


def project(report, registry, behavior_names):
    need(type(report) is dict and type(registry) is dict, 'Report/registry objects required')
    keys = names(registry.get('expected_result_keys'), 158)
    core_names = names(registry.get('expected_core_process_keys'), 36)
    movie_names = names(registry.get('expected_movie_keys'), 21)
    need(set(report) == keys and core_names <= keys and movie_names <= keys
         and not core_names & movie_names and 'neon_workspace' in keys, 'Exact result domains differ')
    core = {}
    for name in sorted(core_names):
        row = report[name]
        need(type(row) is dict and set(row) == {'exit', 'seconds'} and integer(row.get('exit'), 0)
             and finite(row.get('seconds')), 'Core scalar row differs')
        core[name] = {'exit': 0, 'seconds': row['seconds']}
    movies = {}
    for name in sorted(movie_names):
        row = report[name]
        need(type(row) is dict and set(row) == {'frames', 'fps', 'duration'}
             and integer(row.get('frames'), 48) and row.get('fps') == '24/1', 'Movie scalar row differs')
        duration = row['duration']
        need(type(duration) in (str, int, float) and type(duration) is not bool,
             'Movie duration scalar required')
        if type(duration) is str:
            need(len(duration) <= 32 and re.fullmatch(r'\d+(?:\.\d+)?', duration) is not None,
                 'Movie duration syntax differs')
        need(finite(float(duration)) and abs(float(duration) - 2) < .01, 'Movie duration bound differs')
        movies[name] = {'frames': 48, 'fps': '24/1', 'duration': duration}
    neon = neon_projection(report['neon_workspace'], behavior_names)
    return {'format': 'has_successful_full_explicit_scalar_projection_prototype_1',
            'qualification': 'PROJECTION_ONLY_NOT_A_FULL_VALIDATOR_OR_ACTUAL_RECEIPT',
            'result_keys': sorted(keys), 'core_process_groups': core, 'movie_groups': movies,
            'neon_workspace': neon, 'omitted_private_group_values_copied': False,
            'raw_full_report_or_canonical_log_copied': False,
            'independent_validation_of_all_158_groups_claimed': False,
            'codec_evidence_must_be_joined_separately': True}


def activate_archive(*unused, **also_unused):
    raise Refusal('No actual archive entry exists: root terminal/release and explicit closed input inventory are prerequisites')

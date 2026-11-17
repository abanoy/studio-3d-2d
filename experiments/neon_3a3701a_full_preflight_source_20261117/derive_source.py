"""Pure exact-base derivation of one3a preflight, with a complete byte inverse."""
import hashlib

BASE_SHA = '4f70c47833011da549259085816552ac3b373ebd26a4838187b5dd42851c5488'
COMMIT = '3a3701ab6edfa81dc883759403c170b8555aab07'
FOCUS_SHA = '84569db064d65d35e6fa8f4087bbcd21f18b9a5d8db14a8e0ad29152ea0920b2'
FOCUS_MAP_SHA = '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'


def derive(raw, tail_verification=None, tail_completion=None):
    assert hashlib.sha256(raw).hexdigest() == BASE_SHA
    old = raw.decode('utf-8'); new = old
    begin = old.index('# BEGIN 696 FOCUSED AND RELEASE GATES\n')
    end = old.index('# END 696 FOCUSED AND RELEASE GATES\n') + len('# END 696 FOCUSED AND RELEASE GATES\n')
    ancestor = old[old.index('def validate_focused('):old.index('def validate_prior_release(')]
    ancestor = ancestor.replace('def validate_focused(', 'def validate_ancestor_focused(', 1)
    gates = '''# BEGIN 3A FOCUSED AND RELEASE GATES
# Color is actual closed3a evidence. Camera/Neon/controls are unchanged-app ancestor evidence.
FOCUSED_VERIFICATION_SHA256 = FOCUS_LITERAL
TAIL_VERIFICATION_SHA256 = TAIL_VERIFICATION_LITERAL
TAIL_COMPLETION_SHA256 = TAIL_COMPLETION_LITERAL


def validate_functional_dirt(tracked, untracked):
    # Exact declared functional scope excludes session caches; retain their bytes.
    for names in (tracked, untracked):
        assert type(names) is list and all(type(name) is str for name in names)
        assert not [name for name in names if '__pycache__' not in Path(name).parts and Path(name).suffix != '.pyc']


def validate_source_delta(sources, old):
    assert type(sources) is dict and type(old) is dict and len(sources) == len(old) == 1029
    assert set(sources) == set(old)
    assert {name for name in sources if sources[name] != old[name]} == {'tests/color_sampler_smoke.gd'}
    assert old['tests/color_sampler_smoke.gd'] == '7c2150ad2a5221bf3e81cad758cea609f46d414e8e2761c9b50cfb82598bf141'
    assert sources['tests/color_sampler_smoke.gd'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'


def validate_focused(check):
    assert check['format'] == 'has_root_workspace_followup_1'
    assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
    assert type(check['functional_source_files']) is int and check['functional_source_files'] == 1029
    assert check['full_suite_pass_claimed'] is False
    row, = check['rows']
    assert row['label'] == 'color' and type(row['exit']) is int and row['exit'] == 0
    assert row['retained_Popen_reaped'] is True and row['timed_out'] is False
    report = row['report']
    assert type(report['checks']) is int and report['checks'] == 44
    assert type(report['failures']) is int and report['failures'] == 0
    assert type(report['native_projects']) is list and len(report['native_projects']) == 3


ANCESTOR_FUNCTION
def validate_prior_release(release):
    assert release['format'] == 'has_root_neon_ffcf_graphics_lease_release_1' and release['released'] is True
    assert release['source_commit'] == '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'
    assert release['canonical_run'] == 'windows-neon-696ca7f-20261117T170720480423'
    assert type(release['physical_jobs']) is int and release['physical_jobs'] == 93
    assert release['receipt_inventory_sha256'] == 'c11d074afa51f2144cce34eb4605280aea39f789904cf327e4fc30cbcfa96e97'
    assert release['release_kind'] == 'closed_failed_partial_run' and release['full_suite_passed'] is False and release['final_full_report_used'] is False
    assert type(release['suite_exit']) is int and release['suite_exit'] == 1
    assert all(type(release[name]) is int for name in ('coordinator_pid', 'python_pid', 'functional_sources'))
    assert release['coordinator_pid'] == 12740 and release['python_pid'] == 5384 and release['functional_sources'] == 1029
    assert release['released_utc'] == '2026-11-17T17:42:05.1961829Z'
    assert release['all_collected_jobs_desktops_closed_private'] is True and release['all_inline_exact_physical_matches'] is True and release['root_observer_issued_no_termination'] is True


def validate_tail(check, completion, cases, canonical_report):
    assert check['format'] == 'has_root_workspace_followup_1'
    assert check['passed'] is True and check['host_scopes_closed'] is True and check['all_functional_source_unchanged'] is True
    assert type(check['functional_source_files']) is int and check['functional_source_files'] == 1029
    assert check['full_suite_pass_claimed'] is False
    assert len(cases) == 44 and len(check['rows']) == 44
    assert [row['label'] for row in check['rows']] == [row[0] for row in cases]
    for row in check['rows']:
        assert type(row['exit']) is int and row['exit'] == 0
        assert row['retained_Popen_reaped'] is True and row['timed_out'] is False and type(row['report']) is dict
        canonical_report(row['label'], row['report'])
    assert completion['format'] == 'has_targeted_neon_late_stage_completion_1'
    assert completion['candidate_commit'] == '3a3701ab6edfa81dc883759403c170b8555aab07'
    assert type(completion['expected_wrappers']) is int and completion['expected_wrappers'] == 44
    assert completion['all44_completed_and_canonical_reports_passed'] is True
    assert type(completion['host_return']) is int and completion['host_return'] == 0
    assert completion['full_PASS_or_merge_claimed'] is False


for pin in (FOCUSED_VERIFICATION_SHA256, TAIL_VERIFICATION_SHA256, TAIL_COMPLETION_SHA256):
    assert type(pin) is str and len(pin) == 64 and all(c in '0123456789abcdef' for c in pin), 'Actual closed focused/tail seals required before reservation'
# END 3A FOCUSED AND RELEASE GATES
'''.replace('FOCUS_LITERAL', repr(FOCUS_SHA)).replace('TAIL_VERIFICATION_LITERAL', repr(tail_verification)).replace('TAIL_COMPLETION_LITERAL', repr(tail_completion)).replace('ANCESTOR_FUNCTION', ancestor.rstrip() + '\n\n')
    changes = [(old[begin:end], gates),
        ('"""Fresh696 full reservation only after actual root-sealed camera/Neon/control success."""',
         '"""Fresh3a reservation after closed color44/tail44; ancestor camera evidence stays historical."""'),
        ("REV = '696ca7f1491a43b1a2267a53f8ca0f62b7c211a9'", "REV = '" + COMMIT + "'"),
        ("focused = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'", "focused = REVIEW / 'output/neon-color-center-3a3701a-attempt1'"),
        ('validate_focused(check)\nprior_run =', '''validate_focused(check)
assert sha(focused / 'source-before.json') == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
assert sha(focused / 'source-after.json') == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
ancestor_focus = REVIEW / 'output/neon-camera-visible-696ca7f-20261117-attempt1'
assert sha(ancestor_focus / 'verification.json') == '9a0a959734ae56925af31a63207ba711ff6443fe44b38ef8f14425f64aa6bb4c'
validate_ancestor_focused(load(ancestor_focus / 'verification.json'))
late_packet = ROOT / 'experiments/neon_late_stage_cases_source_20261117'
assert sha(late_packet / 'INDEX.json') == '790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3'
for row in load(late_packet / 'INDEX.json')['files']:
    path = late_packet / row['path']
    assert path.resolve().is_relative_to(late_packet) and not path.is_symlink()
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
assert sha(late_packet / 'late_cases.py') == '6a2f0b07dd684dbfcb99ac89b35f4fbe93891a735ada368fa543d38db25b2f43'
late_spec = importlib.util.spec_from_file_location('root_sealed3a_late_cases', late_packet / 'late_cases.py')
late = importlib.util.module_from_spec(late_spec); late_spec.loader.exec_module(late)
late.check_source((REVIEW / 'tests/verify.py').read_bytes(), (ROOT / 'experiments/run_neon_scene_followup_20261117.py').read_bytes())
tail = REVIEW / 'output/neon-late-3a-attempt2'
assert sha(tail / 'verification.json') == TAIL_VERIFICATION_SHA256
assert sha(tail / 'TARGETED-COMPLETION.json') == TAIL_COMPLETION_SHA256
validate_tail(load(tail / 'verification.json'), load(tail / 'TARGETED-COMPLETION.json'), late.CASES, late.assert_canonical_report)
for name in ('source-before.json', 'source-after.json'):
    assert sha(tail / name) == '5561ab5a3bca4aeffb839cd1c88913a2857f6f2cd49544c70ff05253a171a2fc'
prior_run ='''),
        ("prior_run = REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051'", "prior_run = REVIEW / 'output/windows-neon-696ca7f-20261117T170720480423'"),
        ("assert sha(prior_run / 'source-before.json') == '5064dc9e7932cfb05360e3df974dbbeb56cae682bfade6cb286e3040302ab67f'", "assert sha(prior_run / 'source-before.json') == '594cf0dfc7c28c402e5ddd01a81f42c6764761a969e1758df0ae37757b061eab'"),
        ("assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=REVIEW).strip()", "functional_scope = ('src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw')\ntracked_dirt = subprocess.check_output(['git', 'diff', '--name-only', '--', *functional_scope], cwd=REVIEW, text=True).splitlines()\nuntracked_dirt = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *functional_scope], cwd=REVIEW, text=True).splitlines()\nvalidate_functional_dirt(tracked_dirt, untracked_dirt)"),
        ("assert {name for name in sources if sources[name] != old[name]} == {'src/app.gd', 'tests/helper_preview_port_files.json', 'tests/wind_review_port_files.json'}", "assert load(ancestor_focus / 'source-before.json') == load(ancestor_focus / 'source-after.json') == old\nvalidate_source_delta(sources, old)"),
        ('# BEGIN 696 SOURCE PINS', '# BEGIN 3A SOURCE PINS'),
        ('# END 696 SOURCE PINS', "assert sources['tests/color_sampler_smoke.gd'] == '102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781'\n# END 3A SOURCE PINS"),
        ("('windows-neon-696ca7f-' +", "('windows-neon-3a3701a-' +"),
        ("packet = ROOT / 'experiments/neon_windows_696ca7f_20261117'", "packet = ROOT / 'experiments/neon_windows_3a3701a_20261117'"),
        ("'format': 'has_neon_696_full_windows_preparation_1'", "'format': 'has_neon_3a3701a_full_windows_preparation_1'"),
        ("'actual_focused_checks': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48}", "'actual_focused_checks': {'color': 44, 'native_projects': 3, 'late_wrappers': 44},\n    'ancestor696_focused_checks_not_fresh3a': {'camera': 60, 'camera_native_models': 5, 'neon': 12504, 'controls': 48},\n    'tail_verification_sha256': TAIL_VERIFICATION_SHA256, 'tail_completion_sha256': TAIL_COMPLETION_SHA256,\n    'main_metadata_checkpoint': '855d67fe44868793a29d6c6c75c61c0ba86236d2',\n    'main_functional_source_commit': '52f63c944ded7a651da871524d23a345b606424d', 'main_functional_sources': 1019"),
        ("'sole_functional_delta': 'one existing camera-inspector refresh; exact two app-hash manifest rows; test predicates unchanged'", "'sole_functional_delta': 'one native fixture click targets the same expected pixel center; all assertions/thresholds/cases and app/helper/wind bytes unchanged',\n    'dirt_check_ignores_only_declared_pycache_and_pyc_scope_exclusions': True, 'cache_reset_or_deleted': False"),
    ]
    for before, after in changes:
        assert new.count(before) == 1, before[:100]
        new = new.replace(before, after, 1)
    inverse = new
    for before, after in reversed(changes):
        assert inverse.count(after) == 1, after[:100]
        inverse = inverse.replace(after, before, 1)
    assert inverse.encode('utf-8') == raw
    return new.encode('utf-8'), changes

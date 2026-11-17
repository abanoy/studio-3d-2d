"""Source-only bootstrap; actual input access belongs to explicit Root execution."""
from pathlib import Path
import ast, hashlib, os, subprocess, sys, time, types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARNESS = ROOT / 'experiments/pmx_physics_native_observation_harness_20261117'
DIAGNOSTIC = ROOT / 'experiments/pmx_physics_oracle_count_diagnostic_20261117'
HARNESS_SHA = '4258db09011aab285d00889cda1ada279f511f4553828cb69b6b07975bdaf8ec'
DIAGNOSTIC_SHA = 'c21bac607f5772817455dc50f7db95580601545009fb8ba4b944a1ccd4b2b7d8'
COMMON_SHA = 'f1972557534e1346ee24930a59026a8fb9d813199bb6f1016bb666ff894d870e'
HOST_SHA = '348913a5c8c1666d46b73f463295fa877491ec6c71e4190ffba94a0d857231d4'
raw = (HARNESS / 'common.py').read_bytes()
if hashlib.sha256(raw).hexdigest() != COMMON_SHA: raise ValueError('sealed common source differs')
S = types.ModuleType('_root_count_sealed_common'); S.__file__ = str(HARNESS / 'common.py')
sys.modules[S.__name__] = S
exec(compile(raw, S.__file__, 'exec'), S.__dict__)


def verify_sources(index_sha):
    S.need(type(index_sha) is str and S.re.fullmatch('[a-f0-9]{64}', index_sha), 'explicit driver INDEX pin required')
    S.packet(HERE, index_sha); S.packet(HARNESS, HARNESS_SHA); S.packet(DIAGNOSTIC, DIAGNOSTIC_SHA)
    oracle_folder, oracle_sha = S.PACKETS['oracle']
    S.packet(ROOT / 'experiments' / oracle_folder, oracle_sha)
    return {'driver_INDEX_sha256': index_sha, 'harness_INDEX_sha256': HARNESS_SHA,
            'diagnostic_INDEX_sha256': DIAGNOSTIC_SHA, 'oracle_INDEX_sha256': oracle_sha}


def closed_lane(path, digest, root_closed):
    S.need(root_closed is True, 'fresh actual closed-lane Root assertion required')
    path = S.safe(path)
    review_output = ROOT.parent / 'has-neon-review-20261116-c2d52ff/output'
    S.need(path.parent.parent == review_output and path.parent.name.startswith('neon-mmd-pose-3a-')
           and path.name == 'verification.json', 'exact fresh focused pose closure required')
    value = S.read_json(path, 1024 * 1024, digest)
    S.need(value.get('format') == 'has_root_workspace_followup_1' and value.get('passed') is True
           and value.get('host_scopes_closed') is True and value.get('all_functional_source_unchanged') is True
           and value.get('functional_source_files') == 1029 and value.get('full_suite_pass_claimed') is False,
           'actual focused host closure required')
    row, = value['rows']
    S.need(row['label'] == 'pose' and row['exit'] == 0 and row['retained_Popen_reaped'] is True
           and row['timed_out'] is False and row['report']['checks'] == 45
           and row['report']['failures'] == 0 and row['report']['actual_mmd_tested'] is True
           and len(row['report']['movies']) == 2, 'actual native focused pose closure required')
    return {'path': str(path), 'sha256': digest}


def retained_host():
    raw = S.read_stable(HARNESS / 'run_observation.py', 2 * 1024 * 1024, expected_sha=HOST_SHA)
    tree = ast.parse(raw); wanted = {'UnconfirmedClosure', 'reaped', 'run_child'}
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in wanted]
    S.need({n.name for n in nodes} == wanted and len(nodes) == 3, 'exact retained host definitions required')
    namespace = {'S': S, 'os': os, 'subprocess': subprocess, 'time': time, 'RETAINED_UNCONFIRMED': []}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact sealed retained60s host>', 'exec'), namespace)
    return namespace

"""Separate read-only diagnostic profile. Import performs no file/native IO."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SURVEY = ROOT / 'experiments/native_normal_resource_survey_20261117'
SURVEY_SHA = 'b6069eb8c87d7599d10165de987ab2d9924fb377890e12a4cb2f0bdaf9ab735c'
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
LOCK_SHA = '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6'
READER = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
READER_SHA = '5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'
REFERENCE = ROOT / 'experiments/source_normal_followup_plan_20261115/INPUT_METADATA.json'
REFERENCE_SHA = '080cfbcea375c18fa21f29b51d9afbd30bfc4862524974b8900cfd67541d4914'
PWSH = Path(r'C:\Users\noble\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
PWSH_SHA = '2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233'
WRAPPER = ROOT / 'tools/private_desktop.py'
WRAPPER_SHA = '9788e7fde42de7bce022589c86146eaa93deb142ef368aa37a05259ec3047628'
PROFILE = 'SESSION_B_READONLY_RESOURCE_DIAGNOSTIC_AFTER_FAILED_FULL'
CANDIDATE = '00bf0f916a549f5e858cb39dd91a149071fd5181'
FULL_RUN = 'windows-neon-00bf0f9-replay2-20261117T155709412051'
ROOT_FUNCTIONAL_COMMIT = '52f63c944ded7a651da871524d23a345b606424d'
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
QUALIFICATIONS = ('preload_IO_confinement', 'historical_generation', 'export_equivalence',
                  'normal_repair', 'native_fidelity', 'artifact_adoption', 'legacy_strict_survey_native_pass')
PROOFS = {'full_release', 'functional_snapshot', 'review_functional_snapshot', 'cold187_not_started_root_record'}


def need(value, message):
    if not value: raise ValueError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def validate_identity(value, with_path=True):
    keys = {'bytes', 'mtime_ns', 'sha256'} | ({'path'} if with_path else set())
    need(type(value) is dict and set(value) == keys, 'Exact identity record required')
    need(type(value['bytes']) is int and value['bytes'] > 0 and type(value['mtime_ns']) is int
         and value['mtime_ns'] > 0 and type(value['sha256']) is str
         and re.fullmatch('[a-f0-9]{64}', value['sha256']), 'Strict byte/time/hash identity types required')
    if with_path: need(type(value['path']) is str, 'Literal identity path required')
    return value


def safe(value):
    path = Path(value); need(path.is_absolute(), 'Absolute path required')
    for item in (path, *path.parents):
        if item.exists():
            need(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400,
                 'Reparse path refused')
    return path.resolve()


def read_json(path, maximum=2 * 1024 * 1024):
    path = safe(path); need(path.is_file() and path.stat().st_size <= maximum, 'Bounded regular JSON required')
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def packet(folder, expected):
    folder = safe(folder); raw = (folder / 'INDEX.json').read_bytes()
    need(digest(raw) == expected, 'Exact packet INDEX required')
    rows = json.loads(raw)['files']; need(type(rows) is list, 'Exact packet list required')
    for row in rows:
        path = safe(folder / row['path']); need(path.is_relative_to(folder), 'Packet boundary')
        body = path.read_bytes()
        need(len(body) == row['bytes'] and digest(body) == row['sha256'], 'Packet member changed')
    return {row['path']: row['sha256'] for row in rows}


def reader():
    need(digest(safe(READER).read_bytes()) == READER_SHA, 'Identity reader source changed')
    spec = importlib.util.spec_from_file_location('resource_diagnostic_identity_reader', READER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate_admission(value, now):
    """Pure schema/authority checks; these do not independently observe a lane."""
    need(type(value) is dict and value.get('format') == 'has_session_B_resource_diagnostic_admission_2', 'Diagnostic admission schema')
    need(value.get('profile') == PROFILE and value.get('root_native_lane_exclusive') is True,
         'Separate root-owned diagnostic profile required')
    need(value.get('loader_readonly_dependency_resolution_authorized') is True, 'Loader read-only dependency authorization required')
    need(type(value.get('claims')) is dict and set(value['claims']) == set(QUALIFICATIONS)
         and all(item is False for item in value['claims'].values()), 'Qualification claims must remain false')
    for key in ('expected_metadata_head', 'functional_commit', 'candidate_commit'):
        need(type(value.get(key)) is str and re.fullmatch('[a-f0-9]{40}', value[key]), 'Exact commit required')
    need(value['candidate_commit'] == CANDIDATE, 'This diagnostic context is the exact retained candidate')
    need(value['functional_commit'] == ROOT_FUNCTIONAL_COMMIT and type(value.get('functional_count')) is int
         and value['functional_count'] == 1019, 'This unmerged ROOT remains qualified52 functional1019')
    need(type(value.get('candidate_functional_count')) is int and value['candidate_functional_count'] == 1029
         and value.get('cold187_disposition') == 'NOT_STARTED_AFTER_FAILED_FULL', 'Review1029 and explicit cold187-not-started context required')
    issued = datetime.datetime.fromisoformat(value['issued_utc']); expires = datetime.datetime.fromisoformat(value['expires_utc'])
    need(issued.tzinfo is not None and expires.tzinfo is not None and issued <= now < expires
         and 0 < (expires - issued).total_seconds() <= 600, 'Fresh bounded root admission required')
    need(set(value.get('proofs', {})) == PROOFS, 'Full and cold187 closure plus source proofs required')
    need(set(value.get('protected_originals', {})) == {'blend', 'glb', 'parameters'}, 'Exact known B companions required')
    return value



def validate_failed_full_lane(value, data):
    """Pure exact failed-Review/root-unstarted joins; no successful cold/full claim."""
    full = data['full_release']; unstarted = data['cold187_not_started_root_record']
    need(full.get('format') == 'has_root_neon_ffcf_graphics_lease_release_1'
         and full.get('released') is True and full.get('all_collected_jobs_desktops_closed_private') is True
         and full.get('canonical_run') == FULL_RUN and full.get('source_commit') == CANDIDATE
         and type(full.get('functional_sources')) is int and full['functional_sources'] == 1029
         and full.get('full_suite_passed') is False and full.get('final_full_report_used') is False
         and type(full.get('suite_exit')) is int and full['suite_exit'] != 0
         and full.get('release_kind') == 'closed_failed_partial_run', 'Actual failed replay2 Review1029 release required')
    need(unstarted.get('format') == 'has_root_cold187_not_started_after_failed_full_1'
         and unstarted.get('disposition') == 'NOT_STARTED_AFTER_FAILED_FULL'
         and unstarted.get('cold187_launched') is False and unstarted.get('root_native_lane_exclusive') is True
         and unstarted.get('candidate_commit') == CANDIDATE and unstarted.get('canonical_run') == FULL_RUN
         and unstarted.get('root_metadata_head') == value['expected_metadata_head']
         and unstarted.get('root_functional_commit') == ROOT_FUNCTIONAL_COMMIT
         and type(unstarted.get('root_functional_count')) is int and unstarted['root_functional_count'] == 1019
         and type(unstarted.get('review_functional_count')) is int and unstarted['review_functional_count'] == 1029,
         'Explicit root cold187-not-started authority and separate actual source roles required')
    for field, role in (('full_release_sha256', 'full_release'), ('root_snapshot_sha256', 'functional_snapshot'),
                        ('review_snapshot_sha256', 'review_functional_snapshot')):
        need(unstarted.get(field) == value['proofs'][role]['sha256'], 'Root disposition proof binding differs')
    observed = datetime.datetime.fromisoformat(unstarted['observed_utc'])
    released = datetime.datetime.fromisoformat(full['released_utc'])
    issued = datetime.datetime.fromisoformat(value['issued_utc'])
    need(observed.tzinfo is not None and released.tzinfo is not None
         and released <= observed <= issued and (issued - observed).total_seconds() <= 120,
         'Fresh root not-started disposition after actual release required')


def check_snapshot(folder, snapshot, commit, count):
    sources = snapshot['source_sha256']
    need(snapshot['commit'] == commit and type(sources) is dict and len(sources) == count,
         'Explicit ROOT1019 or Review1029 functional snapshot required')
    names = {p.relative_to(folder).as_posix() for name in ('src', 'tests', 'tools', 'data', 'examples')
             for p in (folder / name).rglob('*') if p.is_file() and p.suffix != '.pyc' and '__pycache__' not in p.parts}
    names.update(('project.godot', 'main.tscn', 'run.py', 'launch.pyw'))
    need(names == set(sources) and all(digest(safe(folder / name).read_bytes()) == pin for name, pin in sources.items()),
         'Current functional source differs from its own explicit root/commit/count map')

def check_inputs(admission_path, admission_sha, packet_sha):
    """Root-only later: hashes known files/catalogues, never opens discovered paths."""
    packet(HERE, packet_sha); packet(SURVEY, SURVEY_SHA)
    need(digest(safe(admission_path).read_bytes()) == admission_sha, 'Root admission changed')
    value = validate_admission(read_json(admission_path), datetime.datetime.now(datetime.timezone.utc))
    r = reader(); need(digest(LOCK.read_bytes()) == LOCK_SHA and digest(REFERENCE.read_bytes()) == REFERENCE_SHA, 'Approved references changed')
    lock = read_json(LOCK); reference = read_json(REFERENCE)
    need(len(lock['runtime_executables']) == 6 and all(r.identity(safe(name)) == row for name, row in lock['runtime_executables'].items()), 'Approved six runtimes differ')
    need(len(lock['sourceio_files']) == 574 and r.metadata_map(r.SOURCEIO) == lock['sourceio_files'], 'Original SourceIO574 differs')
    copy = safe(value['sourceio_copy']); need(copy != r.SOURCEIO and copy.is_relative_to(ROOT.parent), 'Distinct reviewed SourceIO copy required')
    need(r.metadata_map(copy) == lock['sourceio_files'], 'Reviewed SourceIO574 copy differs')
    need(len(lock['exporter_noncache_sources']) == 120 and r.metadata_map(safe(lock['exporter_root']), 'exporter') == lock['exporter_noncache_sources'], 'Exporter120 differs')
    need(digest(safe(PWSH).read_bytes()) == PWSH_SHA and digest(safe(WRAPPER).read_bytes()) == WRAPPER_SHA, 'Host support changed')
    observed = {}
    for role, row in value['protected_originals'].items():
        validate_identity(row)
        expected = reference['files'][role]; path = safe(ROOT / expected['path'])
        need(safe(row['path']) == path and row['sha256'] == expected['sha256'] and row['bytes'] == expected['bytes'], 'Known B identity/path differs')
        actual = r.identity(path, single_link=True)
        need(actual == {key: row[key] for key in ('bytes', 'mtime_ns', 'sha256')}, 'Protected original changed')
        observed[role] = actual
    proof_data = {}
    for role, row in value['proofs'].items():
        validate_identity(row)
        path = safe(row['path']); need(path.is_relative_to(ROOT.parent) and 'output' in path.parts, 'Private root proof boundary')
        need(r.identity(path) == {key: row[key] for key in ('bytes', 'mtime_ns', 'sha256')}, 'Root proof changed')
        proof_data[role] = read_json(path, 8 * 1024 * 1024)
    validate_failed_full_lane(value, proof_data)
    need(safe(value['proofs']['review_functional_snapshot']['path']) == REVIEW / 'output' / FULL_RUN / 'source-after.json',
         'Exact failed Review source-after role required')
    check_snapshot(ROOT, proof_data['functional_snapshot'], ROOT_FUNCTIONAL_COMMIT, 1019)
    check_snapshot(REVIEW, proof_data['review_functional_snapshot'], CANDIDATE, 1029)
    return value, observed, lock, reference

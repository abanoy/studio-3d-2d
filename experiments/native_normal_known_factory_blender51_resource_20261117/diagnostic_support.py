"""Separate read-only diagnostic profile. Import performs no file/native IO."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import re
import known_handler_policy as H

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SURVEY = ROOT / 'experiments/native_normal_blender51_resource_api_fix_20261117'
SURVEY_SHA = '9f8e24d0053d920dcdb7a5f5560a37ee0b493aa63351dc95e478435e95685369'
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
PROFILE = 'SESSION_B_READONLY_KNOWN_FACTORY_RESOURCE_DIAGNOSTIC'
ROOT_FUNCTIONAL_COMMIT = '52f63c944ded7a651da871524d23a345b606424d'
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
QUALIFICATIONS = ('preload_IO_confinement', 'historical_generation', 'export_equivalence',
                  'normal_repair', 'native_fidelity', 'artifact_adoption', 'legacy_strict_survey_native_pass')
PROOFS = {'functional_snapshot', 'review_functional_snapshot', 'closed_lane_root_record'}


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


from current_context import validate_admission, validate_current_closed_lane


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
    validate_current_closed_lane(value, proof_data)
    check_snapshot(ROOT, proof_data['functional_snapshot'], value['functional_commit'], 1019)
    check_snapshot(REVIEW, proof_data['review_functional_snapshot'], value['candidate_commit'], 1029)
    H.read_bound_baseline(value['factory_baseline'], r, safe, ROOT)
    return value, observed, lock, reference

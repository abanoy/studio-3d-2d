"""Small readonly observation support; import opens no input or runtime file."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_ROOT = Path(r'C:\a\tools\models')
COPY_ROOT = ROOT / 'output/PRIVATE-pmx-oracle-inputs-20261117-attempt1'
PROVENANCE_SHA = '339752b3e5d17b55f1cc13779e993b760cafcee571cc1b8f832f23b9c50831ed'
PYTHON = Path(r'C:\Program Files\Python313\python.exe')
PYTHON_SHA = '03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9'
PACKETS = {
    'oracle': ('pmx_physics_independent_oracle_20261117', 'd27d9873bc08ec2bc37f8939ae09f9b071f9f4e6fda8b112a2626fef7fabbb45'),
    'candidate': ('pmx_physics_native_reader_prototype_20261117', '9946bf2bccbe5e289fea013ec702c97775b33b9a64dc3bce7979d21d08e92487'),
    'archive': ('pmx_physics_archive_prototype_20261117', '97e7c5a6085de7e0eb67b87584a49d7401a9f42553373f85ddf81108873346d1')}
STAMP_KEYS = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_nlink', 'st_file_attributes')
SOURCE_CAP = 128 * 1024 * 1024
CODE_FILES = ('common.py', 'worker.py', 'run_observation.py')


class Refusal(ValueError):
    pass


def need(ok, label):
    if not ok: raise Refusal(label)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _pairs(rows):
    value = {}
    for key, child in rows:
        need(key not in value, 'duplicate JSON key'); value[key] = child
    return value


def parse(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda _value: need(False, 'nonfinite JSON'))


def safe(path):
    path = Path(path)
    need(path.is_absolute(), 'absolute owned path required')
    for item in (path, *path.parents):
        try: value = item.lstat()
        except FileNotFoundError: continue
        need(not stat.S_ISLNK(value.st_mode) and not getattr(value, 'st_file_attributes', 0) & 0x400,
             'reparse path refused')
    return path.resolve()


def stamp(value):
    return {key: int(getattr(value, key, 0)) for key in STAMP_KEYS}


def validate_stamp(value):
    need(type(value) is dict and set(value) == set(STAMP_KEYS)
         and all(type(n) is int and n >= 0 for n in value.values())
         and value['st_nlink'] == 1 and 0 < value['st_size'] <= SOURCE_CAP,
         'strict single-link source stamp required')


def read_stable(path, cap, expected_stamp=None, expected_sha=None, keep=True):
    """Ordinary rb open and observed stability; no denied-write/delete claim."""
    path = safe(path); before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= cap, 'bounded regular single-link file required')
    wanted = stamp(before) if expected_stamp is None else expected_stamp
    need(stamp(before) == wanted, 'file stamp changed before read')
    h = hashlib.sha256(); parts = []
    with path.open('rb') as stream:
        need(stamp(os.fstat(stream.fileno())) == wanted, 'opened handle stamp differs')
        total = 0
        while True:
            block = stream.read(min(65536, cap + 1 - total))
            if not block: break
            total += len(block); need(total <= cap, 'file read capacity exceeded'); h.update(block)
            if keep: parts.append(block)
        need(total == wanted['st_size'] and stamp(os.fstat(stream.fileno())) == wanted, 'file/EOF changed during read')
    need(stamp(path.lstat()) == wanted, 'file stamp changed after read')
    need(expected_sha is None or h.hexdigest() == expected_sha, 'file SHA differs')
    return b''.join(parts) if keep else None


def read_json(path, cap, digest=None):
    return parse(read_stable(path, cap, expected_sha=digest))


def save(path, value):
    path = Path(path)
    need(path.name.startswith('PRIVATE_'), 'private payload filename required')
    with path.open('xb') as stream: stream.write(canonical(value))


def context(synthetic_root=None, synthetic_sha=None):
    if synthetic_root is None:
        return {'synthetic': False, 'source_root': SOURCE_ROOT, 'copy_root': COPY_ROOT,
                'output_root': ROOT / 'output', 'provenance_sha': PROVENANCE_SHA,
                'python': PYTHON, 'python_sha': PYTHON_SHA, 'total_bytes': 20781686}
    base = safe(synthetic_root)
    need(base.is_relative_to(HERE / 'synthetic_runs') and base != HERE / 'synthetic_runs', 'synthetic files must stay in owned test tree')
    need(type(synthetic_sha) is str and re.fullmatch('[a-f0-9]{64}', synthetic_sha), 'synthetic provenance SHA required')
    python = Path(sys.executable).resolve()
    return {'synthetic': True, 'source_root': base / 'originals', 'copy_root': base / 'copies',
            'output_root': base / 'outputs', 'provenance_sha': synthetic_sha,
            'python': python, 'python_sha': sha(python.read_bytes()), 'total_bytes': None}


def load_provenance(ctx):
    source_root = safe(ctx['source_root']); copy_root = safe(ctx['copy_root'])
    value = read_json(copy_root / 'PROVENANCE.json', 1024 * 1024, ctx['provenance_sha'])
    need(type(value) is dict and set(value) == {'format', 'discovery_sha256', 'producer_sha256', 'rows',
         'source_read_only_and_unchanged', 'native_body_or_joint_tables_parsed', 'native_qualification',
         'private_original_copies_do_not_upload'}, 'exact Root provenance fields required')
    need(value['format'] == 'has_private_owned_pmx_source_copies_1'
         and value['source_read_only_and_unchanged'] is True and value['native_body_or_joint_tables_parsed'] is False
         and value['native_qualification'] is False and value['private_original_copies_do_not_upload'] is True,
         'historical unqualified Root copy provenance required')
    for key in ('discovery_sha256', 'producer_sha256'):
        need(type(value[key]) is str and re.fullmatch('[a-f0-9]{64}', value[key]), 'Root provenance source pin required')
    rows = value['rows']; need(type(rows) is list and len(rows) == 4, 'exact four source/copy rows required')
    originals = set(); total = 0
    for i, row in enumerate(rows):
        need(type(row) is dict and set(row) == {'source', 'source_identity', 'sha256', 'copy', 'copy_identity', 'copy_bytes_equal_source'}, 'exact source/copy row required')
        need(type(row['sha256']) is str and re.fullmatch('[a-f0-9]{64}', row['sha256']) and row['copy_bytes_equal_source'] is True, 'explicit copied-source pin required')
        validate_stamp(row['source_identity']); validate_stamp(row['copy_identity'])
        source = safe(row['source']); copied = safe(row['copy'])
        need(source.is_relative_to(source_root) and source != source_root and source.suffix.lower() == '.pmx', 'exact original root required')
        need(copied == copy_root / ('input-' + str(i) + '.pmx') and copied.name == 'input-' + str(i) + '.pmx', 'exact copy root/leaf required')
        need(row['source_identity']['st_size'] == row['copy_identity']['st_size'], 'source/copy declared lengths differ')
        originals.add(source); total += row['source_identity']['st_size']
    need(len(originals) == 4 and (ctx['total_bytes'] is None or total == ctx['total_bytes']), 'distinct exact staged source set required')
    return value


def read_pair(row, keep=True):
    source = read_stable(row['source'], SOURCE_CAP, row['source_identity'], row['sha256'], keep)
    copied = read_stable(row['copy'], SOURCE_CAP, row['copy_identity'], row['sha256'], keep)
    need(not keep or source == copied, 'actual original/copy bytes differ')
    return source, copied


def packet(folder, expected_sha):
    folder = safe(folder); raw = read_stable(folder / 'INDEX.json', 1024 * 1024, expected_sha=expected_sha)
    index = parse(raw); roles = [k for k in ('files', 'payloads', 'artifacts') if k in index]
    need(len(roles) == 1 and type(index[roles[0]]) is list, 'exact sealed source packet required')
    for row in index[roles[0]]:
        path = safe(folder / row['path']); need(path.is_relative_to(folder), 'source packet path boundary')
        body = read_stable(path, 2 * 1024 * 1024, expected_sha=row['sha256'])
        need(len(body) == row['bytes'], 'source packet size differs')


def code_binding():
    return {name: sha((HERE / name).read_bytes()) for name in CODE_FILES}


def verify_code(request):
    need(request['code_binding'] == code_binding(), 'harness source files changed')
    if not request['synthetic_root']:
        packet(HERE, request['harness_index_sha256'])
    for folder, digest in PACKETS.values(): packet(ROOT / 'experiments' / folder, digest)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


def output_path(ctx, path):
    path = safe(path)
    need(path.parent == safe(ctx['output_root']) and re.fullmatch('PRIVATE-pmx-observation-[A-Za-z0-9._-]+', path.name),
         'exact private observation output root required')
    return path


def frozen_manifest(ctx, path, digest, harness_sha, binding):
    need(type(digest) is str and re.fullmatch('[a-f0-9]{64}', digest), 'explicit frozen manifest SHA required')
    path = safe(path); output_path(ctx, path.parent)
    need(path.name == 'PRIVATE_ORACLE_PHASE.json', 'owned oracle manifest path required')
    value = read_json(path, 1024 * 1024, digest)
    need(value.get('format') == 'has_private_pmx_oracle_observation_phase_1' and value.get('phase') == 'oracle'
         and value.get('all_cases_completed_and_preserved') is True and value.get('native_protocol_qualified') is False
         and value.get('provenance_sha256') == ctx['provenance_sha'] and value.get('harness_index_sha256') == harness_sha
         and value.get('code_binding') == binding and value.get('source_indexes') == {k: v[1] for k, v in PACKETS.items()},
         'complete exact independently frozen oracle phase required')
    need(type(value.get('cases')) is list and len(value['cases']) == 4, 'exact frozen oracle case set required')
    for i, row in enumerate(value['cases']):
        need(type(row) is dict and type(row.get('case_index')) is int and row['case_index'] == i
             and row.get('completed') is True and row.get('preserved') is True
             and type(row.get('witness_bytes')) is int and 0 < row['witness_bytes'] <= 8 * 1024 * 1024
             and type(row.get('witness_sha256')) is str and re.fullmatch('[a-f0-9]{64}', row['witness_sha256']), 'frozen oracle case binding required')
    return value

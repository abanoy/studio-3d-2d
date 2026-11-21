"""Metadata-only audit of the checksum-bound supplied SFM corpus.

Uses installed 7-Zip and an explicit approved Python/SourceIO runtime. Stages
only native MDL definitions inside a new ignored output folder; no textures,
sidecars, model scripts, scene imports, rendering, installs or network access.
This research audit does not establish application/native-feature fidelity.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import zlib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from source_archive import resource_path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive-root', type=Path, required=True)
parser.add_argument('--seven-zip', type=Path, required=True)
parser.add_argument('--python', type=Path, required=True, help='Existing approved Python with the pinned reader dependencies')
parser.add_argument('--sourceio', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True, help='Fresh folder inside this checkout/output')
options = parser.parse_args()
ARCHIVES = options.archive_root.resolve(strict=True)
SEVEN = options.seven_zip.resolve(strict=True)
PYTHON = options.python.resolve(strict=True)
SOURCEIO = options.sourceio.resolve(strict=True)
FOLDER = options.output.resolve()
boundary = (ROOT/'output').resolve()
if FOLDER == boundary or not FOLDER.is_relative_to(boundary) or FOLDER.exists() or options.output.is_symlink():
    parser.error('Choose a new owned folder inside this checkout/output')
if not ARCHIVES.is_dir() or FOLDER.is_relative_to(ARCHIVES):
    parser.error('Keep staging outside the original archive directory')
FOLDER.mkdir(parents=True, exist_ok=False)
STAGE = FOLDER/'stage'
STAGE.mkdir()
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
MAX_MODEL = 16*1024*1024
MAX_TOTAL = 128*1024*1024


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path):
    before = path.stat()
    value = {'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns, 'sha256': sha(path)}
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input changed during reading')
    return value


def index_archive(path, log):
    with log.open('xb') as stream:
        result = subprocess.run([str(SEVEN), 'l', '-slt', '-ba', '-sccUTF-8', '-pHAS_NO_PASSWORD', '--', str(path)],
                                stdout=stream, stderr=subprocess.STDOUT, timeout=30, creationflags=FLAGS)
    if result.returncode != 0 or log.stat().st_size > 4*1024*1024:
        raise ValueError('Archive index failed or exceeds4MiB: '+path.name)
    text = log.read_bytes().decode('utf-8').replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n')
    entries, seen = [], set()
    current = {}
    for line in text.splitlines()+['']:
        if not line.strip():
            if not current:
                continue
            if 'Path' not in current:
                raise ValueError('Unexpected archive index record')
            raw_name = current['Path']
            directory = current.get('Folder') == '+'
            name = resource_path(raw_name.rstrip('/\\') if directory else raw_name)
            if name.casefold() in seen:
                raise ValueError('Duplicate case-insensitive archive member')
            seen.add(name.casefold())
            if current.get('Encrypted', '-') != '-' or current.get('Anti', '-') != '-':
                raise ValueError('Encrypted or anti archive entry')
            if (any(current.get(k, '') not in ('', '-') for k in ['Symbolic Link', 'Hard Link', 'Copy Link', 'Reparse Point'])
                    or current.get('Alternate Stream', '-') != '-' or 'l' in current.get('Attributes', '')):
                raise ValueError('Link archive entry')
            size = int(current.get('Size', 0))
            if not 0 <= size <= 512*1024*1024:
                raise ValueError('Archive member exceeds size budget')
            current.update(normalized_name=name, native_name=raw_name, directory=directory, size=size)
            entries.append(current)
            current = {}
            if len(entries) > 10000:
                raise ValueError('Archive exceeds10000entries')
            continue
        if ' = ' not in line:
            raise ValueError('Unexpected archive index line')
        key, value = line.split(' = ', 1)
        if key in current:
            raise ValueError('Duplicate archive index field')
        current[key] = value
    if not entries:
        raise ValueError('Empty archive index')
    return entries


def extract_definition(path, entry, target, log):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve().is_relative_to(STAGE.resolve()) is False or target.exists():
        raise ValueError('Invalid owned staging target')
    crc = total = 0
    with log.open('xb') as errors:
        process = subprocess.Popen([str(SEVEN), 'x', '-so', '-spd', '-pHAS_NO_PASSWORD', '--', str(path), entry['native_name']],
                                   stdout=subprocess.PIPE, stderr=errors, creationflags=FLAGS)
        timer = threading.Timer(30, process.kill)
        timer.start()
        try:
            with target.open('xb') as output:
                while True:
                    block = process.stdout.read(min(1024*1024, entry['size']-total+1))
                    if not block:
                        break
                    total += len(block)
                    if total > entry['size'] or total > MAX_MODEL:
                        raise ValueError('Definition exceeds indexed size/budget')
                    output.write(block)
                    crc = zlib.crc32(block, crc)
            process.stdout.close()
            code = process.wait(timeout=2)
            if code != 0:
                raise ValueError('7-Zip definition read failed: '+str(code))
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
    if total != entry['size'] or f'{crc & 0xffffffff:08X}' != entry['CRC'].upper():
        raise ValueError('Definition size/CRC differs')
    with target.open('rb') as stream:
        header = stream.read(80)
    if len(header) != 80 or header[:4] != b'IDST' or struct.unpack_from('<I', header, 76)[0] != total:
        raise ValueError('Definition MDL header/file size differs')
    return {'bytes': total, 'sha256': sha(target), 'crc32': f'{crc & 0xffffffff:08X}',
            'version': struct.unpack_from('<I', header, 4)[0]}


baseline = json.loads((ROOT/'docs/benchmarks/sfm_uploaded_samples_2026-11-07.json').read_bytes())
archive_rows, models = [], []
total_staged = total_indexed = 0
initial = {}
print(json.dumps({'folder': str(FOLDER)}), flush=True)
for index, row in enumerate(baseline['archives_provenance']):
    source = (ARCHIVES/row['name']).resolve(strict=True)
    if source.parent != ARCHIVES or source.stat().st_size > 512*1024*1024:
        raise ValueError('Archive escaped explicit original root or exceeds budget')
    before = identity(source)
    if before['sha256'] != row['sha256'] or before['bytes'] != row['bytes']:
        raise ValueError('Original archive differs from committed provenance')
    initial[source] = before
    entries = index_archive(source, FOLDER/f'archive-{index:02d}-index.log')
    total_indexed += sum(entry['size'] for entry in entries)
    if total_indexed > 4*1024*1024*1024:
        raise ValueError('Combined indexed payload exceeds4GiB')
    wanted = [entry for entry in entries if not entry['directory'] and Path(entry['normalized_name']).suffix.lower() == '.mdl']
    if len(wanted) != row['models']:
        raise ValueError('Definition count differs from committed provenance')
    for item, entry in enumerate(wanted):
        if not re.fullmatch('[0-9A-Fa-f]{8}', entry.get('CRC', '')) or not 80 <= entry['size'] <= MAX_MODEL:
            raise ValueError('Missing indexed CRC or excessive definition')
        total_staged += entry['size']
        if total_staged > MAX_TOTAL or len(models) >= 128:
            raise ValueError('Combined model definition budget exceeded')
        relative = f'{index:02d}/'+entry['normalized_name']
        target = STAGE/relative
        result = extract_definition(source, entry, target, FOLDER/f'archive-{index:02d}-model-{item:02d}.log')
        models.append({'archive': row['name'], 'member': entry['normalized_name'], 'staged_member': relative, **result})
    archive_rows.append({'archive': row['name'], 'path': str(source), **before, 'index_entries': len(entries), 'staged_models': len(wanted)})
    print(json.dumps({'archive': row['name'], 'models': len(wanted)}), flush=True)
for path, before in initial.items():
    if identity(path) != before:
        raise ValueError('Original changed during metadata staging')
historical = json.loads((ROOT/'docs/benchmarks/supplied_source_corpus_2026-11-08.json').read_bytes())
if collections.Counter(row['sha256'] for row in models) != collections.Counter(row['source_sha256'] for row in historical['conversions']):
    raise ValueError('Native definition hashes differ from the recorded corpus')
manifest = {'format': 'has_sfm_mdl_only_stage_1', 'stage': str(STAGE), 'archives': archive_rows,
            'models': models, 'staged_bytes': total_staged, 'originals_unchanged': True,
            'limits': {'definition_bytes': MAX_MODEL, 'total_definition_bytes': MAX_TOTAL, 'definitions': 128,
                       'index_bytes_per_archive': 4*1024*1024, 'index_entries_per_archive': 10000},
            'runtime': {'seven_zip': str(SEVEN), 'seven_zip_sha256': sha(SEVEN),
                        'python': str(PYTHON), 'python_sha256': sha(PYTHON), 'sourceio': str(SOURCEIO)}}
with (FOLDER/'staging.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, indent=2)
probe = Path(__file__).with_name('sfm_native_metadata_probe.py')
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', NO_BPY='1')
with (FOLDER/'native-parser.log').open('x', encoding='utf-8') as log:
    result = subprocess.run([str(PYTHON), '-B', str(probe), '--sourceio', str(SOURCEIO), '--inventory', str(FOLDER/'staging.json'), '--output', str(FOLDER/'metadata.json')],
                            stdout=log, stderr=subprocess.STDOUT, cwd=FOLDER, env=env, timeout=180, creationflags=FLAGS)
if result.returncode != 0:
    raise ValueError('Metadata reader failed; see native-parser.log')
for path, before in initial.items():
    if identity(path) != before:
        raise ValueError('Original changed during metadata parsing')
metadata = json.loads((FOLDER/'metadata.json').read_bytes())
if metadata['summary']['errors'] or metadata['summary']['refused_versions'] or metadata['summary']['parsed'] != len(models):
    raise ValueError('Native metadata has errors/refusals; retained output is not a successful inventory')
proof = {'format': 'has_sfm_native_inventory_receipt_1', 'folder': str(FOLDER), 'archives': len(archive_rows),
         'staged_definitions': len(models), 'staged_bytes': total_staged, 'metadata': metadata['summary'],
         'original_archive_sha256_bytes_mtime_unchanged': True, 'only_mdl_payloads_staged': True,
         'native_metadata_only': True, 'model_script_execution': False, 'app_gpu_render': False, 'network': False,
         'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), probe, ROOT/'tools/source_archive.py', ROOT/'tools/asset_audit.py']},
         'sourceio_reader_sha256': {str(p.relative_to(SOURCEIO)): sha(p) for p in [SOURCEIO/'__init__.py', SOURCEIO/'library/models/mdl/structs/header.py', SOURCEIO/'library/models/mdl/structs/flex.py', SOURCEIO/'library/models/mdl/structs/bone.py', SOURCEIO/'library/models/mdl/structs/bodygroup.py']}}
with (FOLDER/'receipt.json').open('x', encoding='utf-8') as stream:
    json.dump(proof, stream, indent=2)
print(json.dumps(proof), flush=True)

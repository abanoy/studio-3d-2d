"""UNRUN preparation: fresh read-only preservation proof; no cleanup authority.

Only the requested fresh ROOT/output JSON is written. No app, process query,
network, Git, source/native content copy, media output, move, or deletion.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT.parent / 'HAS-Review-20261115-SFM-Joints-f0dd57a-replay2'
SOURCEIO = ROOT / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
PINS = {
    'original561': ('experiments/resume_archive_20261115/historical-cleanup-audit/retained-originals-fresh-proof.json.gz', 'f9dfbcde4184ee13d6aa7f9efcf77f48cefeae718c13fefff7741408c3db304c', '80de0389dc4c2220b2ac6a3751f525bf001259810d27a2e799d169cd759e7f1c'),
    'approved_inputs': ('experiments/replay_audio_fix_20261115/builder/input-lock.json', '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6', None),
    'review2_shipped': ('experiments/sfm_review_actual_20261115/replay/shipped-before.json.gz', '36835f9a75926c3a8e53493661700ebab9024cb05f6bb78291cd3bcb572814c9', 'f72f239d4461f81744ea03f32ae995957f1746311bd3f72a12ef921f6cda9acc'),
    'full_source': ('output/windows-canonical-bone-binding-20261115T225514304/source-before.json', '8d9e7d94c745081e0ca084bc64e7498bc7ccb218c44209e1354bcd53f3c50a2a', None),
}


def need(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def no_links(path):
    for item in (path, *path.parents):
        info = item.lstat()
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
             'Reparse or symlink refused: ' + str(item))


def stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink,
            getattr(info, 'st_file_attributes', 0))


def identity(path, single_link=False):
    no_links(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'Regular protected file required')
    need(not single_link or before.st_nlink == 1, 'Original must remain single-link')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    final = path.lstat()
    need(all(stamp(value) == stamp(before) for value in (opened, after, final)),
         'Protected file changed during read: ' + str(path))
    return {'bytes': final.st_size, 'mtime_ns': final.st_mtime_ns, 'sha256': digest}


def relative(name):
    item = PurePosixPath(name)
    need(item.as_posix() == name and not item.is_absolute() and bool(item.parts) and
         not set(item.parts) & {'', '.', '..'} and '\\' not in name and ':' not in name,
         'Unsafe map member')
    return name


def metadata_map(folder, mode='all'):
    no_links(folder)
    need(folder.resolve(strict=True) == folder, 'Protected root must be literal')
    result = {}
    for base, dirs, files in os.walk(folder, followlinks=False):
        base = Path(base)
        for name in dirs + files:
            no_links(base / name)
        if mode == 'review' and base == folder / 'Studio':
            dirs[:] = [n for n in dirs if n not in ('output', '.godot')]
        for name in files:
            path = base / name
            if mode == 'exporter' and ('__pycache__' in path.parts or path.suffix == '.pyc'):
                continue
            result[path.relative_to(folder).as_posix()] = identity(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    output = args.output.absolute()
    need(output.suffix == '.json' and output.parent.is_dir() and not output.exists(),
         'Fresh JSON in an existing owned output directory required')
    no_links(output.parent)
    need(output.parent.resolve(strict=True).is_relative_to((ROOT / 'output').resolve(strict=True)),
         'Only ROOT/output output permitted')
    need(not output.is_relative_to(ROOT / 'output/source-choices-native'),
         'Do not write inside old native roots')
    maps = {}
    evidence = {}
    for key, (name, expected, raw_expected) in PINS.items():
        path = ROOT / name
        raw = path.read_bytes()
        need(sha(raw) == expected, 'Frozen map differs: ' + key)
        decoded = gzip.decompress(raw) if raw_expected else raw
        need(raw_expected is None or sha(decoded) == raw_expected, 'Raw map differs: ' + key)
        maps[key] = json.loads(decoded)
        evidence[key] = {'path': str(path), 'bytes': len(raw), 'sha256': expected,
                         'raw_bytes': len(decoded), 'raw_sha256': sha(decoded)}
    old = ROOT / 'output/source-choices-native'
    originals = maps['original561']
    lock = maps['approved_inputs']
    need(len(originals) == 5 and sum(map(len, originals.values())) == 561, 'Original561 scope differs')
    need(len(lock['native_families']) == 4 and sum(map(len, lock['native_families'].values())) == 495,
         'Current495 original scope differs')
    need(all(originals.get(name) == rows for name, rows in lock['native_families'].items()),
         'Current original submaps differ')
    original_bytes = 0
    for name, rows in originals.items():
        folder = Path(name)
        need(folder.is_absolute() and folder.is_relative_to(ROOT / 'output') and
             not folder.is_relative_to(old), 'Original outside protected boundary')
        for name, expected in rows.items():
            observed = identity(folder / relative(name), single_link=True)
            need(observed == expected, 'Original content or stamp differs: ' + str(folder / name))
            original_bytes += observed['bytes']
    need(original_bytes == 469130387, 'Original bytes differ')
    need(len(lock['runtime_executables']) == 6, 'Runtime scope differs')
    for name, expected in lock['runtime_executables'].items():
        path = Path(name)
        need(path.is_absolute() and not path.is_relative_to(old), 'Runtime scope overlaps old roots')
        need(identity(path) == expected, 'Approved runtime differs: ' + name)
    need(len(lock['sourceio_files']) == 574 and metadata_map(SOURCEIO) == lock['sourceio_files'],
         'Approved original SourceIO map differs')
    exporter = Path(lock['exporter_root'])
    need(exporter.is_absolute() and not exporter.is_relative_to(old), 'Exporter scope differs')
    need(len(lock['exporter_noncache_sources']) == 120 and
         metadata_map(exporter, 'exporter') == lock['exporter_noncache_sources'],
         'Installed exporter120 sources differ')
    shipped = maps['review2_shipped']
    need(len(shipped) == 5844 and metadata_map(REVIEW, 'review') == shipped,
         'Actual replay2 shipped review map differs')
    catalogue = maps['full_source']['source_sha256']
    need(len(catalogue) == 1008, 'Full source scope differs')
    for name, digest in catalogue.items():
        need(identity(ROOT / relative(name))['sha256'] == digest, 'Qualified current source differs: ' + name)
    result = {
        'format': 'has_protected_inputs_fresh_readonly_proof_1', 'passed': True,
        'started_utc': started, 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_commit': 'f0dd57a2e568089d396fecba819ab987da658bf0', 'frozen_maps': evidence,
        'originals': {'families': 5, 'files': 561, 'bytes': original_bytes,
                      'current_review_files': 495, 'additional_Kanako_files': 66,
                      'all_historical_identity_fields_match': True, 'regular_single_link': True},
        'shared_runtime_executables': 6, 'original_SourceIO_files': 574,
        'installed_exporter_noncache_sources': 120,
        'current_review': {'root': str(REVIEW), 'shipped_files': 5844,
                           'historical_size_mtime_SHA256_and_exact_membership_match': True,
                           'excluded_runtime_generated_subtrees': ['Studio/output', 'Studio/.godot']},
        'functional_source_files': 1008, 'all_sources_current_exact_SHA256': True,
        'no_reparse_ancestors_and_stable_regular_reads': True,
        'actual_metadata_source_code_sha256': sha(Path(__file__).read_bytes()),
        'content_arrays_or_media_copied': False, 'originals_or_tools_modified': False,
        'apps_parsers_or_process_queries': False, 'Git_or_network_operations': False,
        'cleanup_authorized': False,
        'limits': 'Point-in-time file preservation only. Older review trees and runtime-generated review files are retained outside the two cleanup roots but not rehashed by this bounded proof. No current ownership, remote backup, deletion access, later preservation, or cleanup authority is inferred.'}
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'passed': True, 'original_files': 561, 'review_files': 5844,
                      'SourceIO_files': 574, 'exporter_sources': 120, 'runtime_files': 6,
                      'functional_source_files': 1008, 'report_sha256': sha(output.read_bytes()),
                      'cleanup_authorized': False}))


if __name__ == '__main__':
    main()

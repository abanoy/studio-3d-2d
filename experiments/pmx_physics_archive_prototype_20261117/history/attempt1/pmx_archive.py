"""Inert PMX declaration archive: immutable RAM inputs, no native/engine/file IO.

The pinned reader supplies a declared-layout capsule, not a native oracle. This
prototype never qualifies a model, simulation, production import or portability.
"""
from dataclasses import dataclass, fields
import hashlib
import json
import math
import re
import struct
import pmx_native_physics as reader

KEY = 'has_native_physics_archive'
LOCATION = 'asset.extras.' + KEY
ENVELOPE = 'has_inert_pmx_physics_archive_prototype_1'
DESCRIPTOR = 'has_pmx_physics_archive_descriptor_prototype_1'
PROVENANCE = 'has_pmx_physics_archive_provenance_prototype_1'
READER_SHA = 'e356894782e02389c215e2bdf335ebd102b98ad0b286e9728434201d21cf0426'
READER_INDEX_SHA = '9946bf2bccbe5e289fea013ec702c97775b33b9a64dc3bce7979d21d08e92487'
JSON_CHUNK = 0x4e4f534a
BIN_CHUNK = 0x004e4942


class Refusal(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    capsule_bytes: int = 2 * 1024 * 1024
    json_bytes: int = 16 * 1024 * 1024
    glb_bytes: int = 128 * 1024 * 1024
    report_bytes: int = 256 * 1024
    project_metadata_bytes: int = 1024 * 1024


HARD = Limits()


def need(ok, message):
    if not ok:
        raise Refusal(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def limits_ok(value):
    need(type(value) is Limits, 'Exact archive limits required')
    for field in fields(Limits):
        n = getattr(value, field.name)
        need(type(n) is int and 0 <= n <= getattr(HARD, field.name),
             'Invalid or widened archive capacity')


def _pairs(rows):
    result = {}
    for key, value in rows:
        need(key not in result, 'Duplicate JSON key')
        result[key] = value
    return result


def _constant(_value):
    raise Refusal('Nonfinite JSON number')


def canonical(value):
    try:
        def typed(item):
            if type(item) is dict:
                need(all(type(key) is str for key in item), 'JSON object keys must remain text')
                for child in item.values(): typed(child)
            elif type(item) is list:
                for child in item: typed(child)
            else:
                need(type(item) in (str, int, float, bool, type(None)), 'Exact JSON value types required')
                need(type(item) is not float or math.isfinite(item), 'Finite JSON numbers required')
        typed(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise Refusal('Unsupported JSON value') from error


def parse_json(raw):
    need(type(raw) is bytes, 'Immutable UTF8 JSON bytes required')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Refusal('Invalid strict UTF8 JSON') from error


def identity(value):
    need(type(value) is dict and set(value) == {'bytes', 'sha256'}, 'Exact identity fields required')
    need(type(value['bytes']) is int and 0 < value['bytes'] <= reader.Limits().source_bytes,
         'Exact bounded source length required')
    need(type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['sha256']),
         'Exact source SHA256 required')


def _raw_words(value):
    """Check recorded word spelling/classification without float conversion."""
    if type(value) is dict:
        if 'words_le_hex' in value:
            need(set(value) == {'offset', 'words_le_hex', 'nonfinite_word_indices'}, 'Exact F32 record required')
            need(type(value['offset']) is int and value['offset'] >= 0, 'Exact F32 offset required')
            words = value['words_le_hex']
            need(type(words) is list and all(type(w) is str and re.fullmatch('[a-f0-9]{8}', w) for w in words),
                 'Exact little-endian binary32 words required')
            observed = [i for i, w in enumerate(words)
                        if int.from_bytes(bytes.fromhex(w), 'little') & 0x7f800000 == 0x7f800000]
            indices = value['nonfinite_word_indices']
            need(type(indices) is list and all(type(i) is int for i in indices) and indices == observed,
                 'Raw nonfinite classification differs')
        for child in value.values():
            _raw_words(child)
    elif type(value) is list:
        for child in value:
            _raw_words(child)
    elif type(value) is float:
        raise Refusal('Capsule words must not be decoded JSON floats')


def capsule_ok(raw, provenance, limits):
    need(type(raw) is bytes and len(raw) <= limits.capsule_bytes, 'Complete capsule capacity exceeded')
    capsule = parse_json(raw)
    need(type(capsule) is dict and capsule.get('format') == 'has_pmx20_native_physics_capsule_prototype_1'
         and capsule.get('qualification') == 'UNQUALIFIED_SOURCE_CPU_ONLY', 'Unqualified reader capsule required')
    need(canonical(capsule) == raw, 'Exact canonical capsule text required')
    need(type(provenance) is dict and set(provenance) == {
        'format', 'reader_sha256', 'reader_INDEX_sha256', 'source_sha256', 'source_bytes',
        'owned_copy_sha256', 'owned_copy_bytes', 'capsule_sha256', 'capsule_bytes', 'native_qualified'},
        'Exact provenance fields required')
    need(provenance['format'] == PROVENANCE and provenance['reader_sha256'] == READER_SHA
         and provenance['reader_INDEX_sha256'] == READER_INDEX_SHA and provenance['native_qualified'] is False,
         'Source-only pinned reader provenance required')
    identity({'bytes': provenance['source_bytes'], 'sha256': provenance['source_sha256']})
    need(type(provenance['owned_copy_bytes']) is int and provenance['owned_copy_bytes'] == provenance['source_bytes']
         and provenance['owned_copy_sha256'] == provenance['source_sha256'], 'Exact original/copy provenance required')
    need(type(provenance['capsule_bytes']) is int and provenance['capsule_bytes'] == len(raw)
         and provenance['capsule_sha256'] == sha(raw), 'Capsule checksum/length differs')
    need(type(capsule.get('source_bytes')) is int and capsule['source_bytes'] == provenance['source_bytes']
         and capsule.get('source_sha256') == provenance['source_sha256'], 'Capsule source provenance differs')
    _raw_words(capsule)
    return capsule


def read_glb(raw, limits=Limits()):
    limits_ok(limits)
    need(type(raw) is bytes and 28 <= len(raw) <= limits.glb_bytes, 'Bounded immutable GLB required')
    magic, version, size = struct.unpack_from('<4sII', raw)
    need(magic == b'glTF' and version == 2 and size == len(raw), 'Exact GLB2 header/EOF required')
    chunks = []; offset = 12
    while offset < len(raw):
        need(offset + 8 <= len(raw), 'Truncated GLB chunk header')
        count, kind = struct.unpack_from('<II', raw, offset); end = offset + 8 + count
        need(count % 4 == 0 and end <= len(raw), 'Truncated or unaligned GLB chunk')
        chunks.append((kind, raw[offset + 8:end])); offset = end
    need([kind for kind, _ in chunks] == [JSON_CHUNK, BIN_CHUNK],
         'Prototype helper-compatible profile requires exactly JSON then BIN')
    need(len(chunks[0][1]) <= limits.json_bytes, 'Whole GLB JSON capacity exceeded')
    document = parse_json(chunks[0][1])
    need(type(document) is dict and type(document.get('asset')) is dict
         and document['asset'].get('version') == '2.0', 'GLTF2 asset object required')
    return document, chunks[1][1]


def _glb(document, binary, limits):
    raw = canonical(document); padded = raw + b' ' * (-len(raw) % 4)
    need(len(padded) <= limits.json_bytes, 'Whole escaped GLB JSON capacity exceeded')
    result = (struct.pack('<4sII', b'glTF', 2, 28 + len(padded) + len(binary))
              + struct.pack('<II', len(padded), JSON_CHUNK) + padded
              + struct.pack('<II', len(binary), BIN_CHUNK) + binary)
    need(len(result) <= limits.glb_bytes, 'Whole GLB capacity exceeded')
    return result


def _descriptor(raw, provenance):
    return {'format': DESCRIPTOR, 'version': 1, 'location': LOCATION,
            'capsule_sha256': sha(raw), 'capsule_bytes': len(raw),
            'provenance_sha256': sha(canonical(provenance)),
            'status': 'OPAQUE_DECLARATIONS_ARCHIVED_SOURCE_CPU_ONLY',
            'native_simulation_supported': False, 'native_qualified': False,
            'warning': 'Physics declarations archived; native simulation is unsupported.'}


def add_report(report, descriptor, limits=Limits()):
    limits_ok(limits)
    need(type(report) is dict and KEY not in report, 'Fresh report descriptor slot required')
    result = parse_json(canonical(report))
    result[KEY] = parse_json(canonical(descriptor))
    need(len(canonical(result)) <= limits.report_bytes, 'Whole preparation report capacity exceeded')
    return result


def check_project_metadata(metadata, limits=Limits()):
    limits_ok(limits)
    need(len(canonical(metadata)) <= limits.project_metadata_bytes, 'Whole project metadata capacity exceeded')


def assemble(glb, source, owned_copy, expected_source, report, limits=Limits()):
    """Capture supplied immutable bytes, then atomically return a new RAM artifact.

    The reader is not an independent oracle. Only authored sources are exercised
    by this experiment; native qualification remains a separate missing gate.
    """
    limits_ok(limits); identity(expected_source)
    need(type(source) is bytes and type(owned_copy) is bytes and source == owned_copy
         and len(source) == expected_source['bytes'] and sha(source) == expected_source['sha256'],
         'Immutable source/original-copy identity differs')
    document, binary = read_glb(glb, limits)
    extras = document['asset'].get('extras', {})
    need(type(extras) is dict and KEY not in extras, 'Occupied or unsupported asset extra slot')
    try:
        capsule = reader.read_pmx20_physics(source)
    except reader.Refusal as error:
        raise Refusal('Source profile unsupported/invalid/capacity refused; no archive returned') from error
    raw = canonical(capsule)
    provenance = {'format': PROVENANCE, 'reader_sha256': READER_SHA, 'reader_INDEX_sha256': READER_INDEX_SHA,
                  'source_sha256': sha(source), 'source_bytes': len(source), 'owned_copy_sha256': sha(owned_copy),
                  'owned_copy_bytes': len(owned_copy), 'capsule_sha256': sha(raw), 'capsule_bytes': len(raw),
                  'native_qualified': False}
    capsule_ok(raw, provenance, limits)
    extras[KEY] = {'format': ENVELOPE, 'version': 1, 'encoding': 'canonical_utf8_json_text',
                   'capsule_text': raw.decode('utf-8'), 'provenance': provenance,
                   'runtime_supported': False, 'native_qualified': False}
    document['asset']['extras'] = extras
    descriptor = _descriptor(raw, provenance)
    return {'glb': _glb(document, binary, limits), 'report': add_report(report, descriptor, limits),
            'provenance': provenance}


def extract(glb, descriptor, expected_provenance, limits=Limits()):
    """Extract exact capsule bytes using an independently retained capture binding."""
    document, _binary = read_glb(glb, limits)
    extras = document['asset'].get('extras')
    need(type(extras) is dict and type(extras.get(KEY)) is dict, 'Archive envelope missing')
    envelope = extras[KEY]
    need(set(envelope) == {'format', 'version', 'encoding', 'capsule_text', 'provenance',
                           'runtime_supported', 'native_qualified'}, 'Exact archive envelope fields required')
    need(envelope['format'] == ENVELOPE and type(envelope['version']) is int and envelope['version'] == 1
         and envelope['encoding'] == 'canonical_utf8_json_text' and envelope['runtime_supported'] is False
         and envelope['native_qualified'] is False and type(envelope['capsule_text']) is str,
         'Inert versioned archive profile required')
    try:
        raw = envelope['capsule_text'].encode('utf-8')
    except UnicodeError as error:
        raise Refusal('Invalid capsule UTF8 text') from error
    capsule_ok(raw, envelope['provenance'], limits)
    need(canonical(envelope['provenance']) == canonical(expected_provenance), 'Retained capture provenance differs')
    need(canonical(descriptor) == canonical(_descriptor(raw, expected_provenance)), 'Report/archive descriptor differs')
    return raw

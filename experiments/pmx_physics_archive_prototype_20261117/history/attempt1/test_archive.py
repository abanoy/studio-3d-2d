"""Authored RAM PMX/GLB round trips and refusals; no models, engine or native IO."""
from dataclasses import replace
import copy
import hashlib
import json
import math
import struct
import unittest
from unittest.mock import patch
import pmx_archive as A
from synthetic_pmx import build_fixture


BIN = b'SYNTHETIC_ENCODED_IMAGE_BYTES\x00\xff\x80\x01'
BIN += b'\x00' * (-len(BIN) % 4)
DOCUMENT = {'asset': {'version': '2.0', 'generator': 'Authored RAM fixture',
                      'extras': {'existing': {'integer': 1, 'float': 1.0, 'negative_zero': -0.0}}},
            'buffers': [{'byteLength': len(BIN)}], 'bufferViews': [{'buffer': 0, 'byteLength': len(BIN)}],
            'images': [{'bufferView': 0, 'mimeType': 'application/x-synthetic-placeholder'}],
            'nodes': [{'name': 'Untouched', 'extras': {'signed_zero': -0.0}}],
            'extensionsUsed': ['UNRELATED_authored'],
            'extensions': {'UNRELATED_authored': {'values': [True, None, 0, 0.0, -0.0, '日本語']}}}


def glb_json(raw, binary=BIN):
    raw += b' ' * (-len(raw) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(raw) + len(binary))
            + struct.pack('<II', len(raw), A.JSON_CHUNK) + raw
            + struct.pack('<II', len(binary), A.BIN_CHUNK) + binary)


def glb(document=DOCUMENT):
    return glb_json(json.dumps(document, ensure_ascii=False, allow_nan=False).encode('utf-8'))


def unpack(raw):
    count, kind = struct.unpack_from('<II', raw, 12)
    assert kind == A.JSON_CHUNK
    document = json.loads(raw[20:20 + count])
    n, kind = struct.unpack_from('<II', raw, 20 + count)
    assert kind == A.BIN_CHUNK
    binary = raw[28 + count:28 + count + n]
    return document, binary


def authored():
    raw, expected = build_fixture(index_size=2, encoding=0, bone_flags=0x3f3f, deform=3)
    return raw, expected, {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def assembled(limits=A.Limits(), document=DOCUMENT, report=None):
    source, _expected, identity = authored()
    return A.assemble(glb(document), source, source, identity,
                      {'adapter': 'unchanged_mmd', 'warnings': ['Existing warning']} if report is None else report,
                      limits)


def descriptor(result):
    return result['report'][A.KEY]


def modified(result, action):
    document, binary = unpack(result['glb'])
    action(document['asset']['extras'][A.KEY])
    return glb_json(json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode(), binary)


class ArchiveTests(unittest.TestCase):
    def assertTyped(self, actual, expected):
        self.assertIs(type(actual), type(expected))
        if type(expected) is dict:
            self.assertEqual(actual.keys(), expected.keys())
            for key in expected: self.assertTyped(actual[key], expected[key])
        elif type(expected) is list:
            self.assertEqual(len(actual), len(expected))
            for a, b in zip(actual, expected): self.assertTyped(a, b)
        elif type(expected) is float:
            self.assertEqual(actual.hex(), expected.hex())
        else:
            self.assertEqual(actual, expected)

    def test_roundtrip_exact_authored_words_names_refs_masks_and_unqualified_flags(self):
        source, expected, identity = authored()
        with patch('builtins.open', side_effect=AssertionError('RAM-only archive must not open files')):
            result = A.assemble(glb(), source, source, identity, {'adapter': 'unchanged_mmd'})
            raw = A.extract(result['glb'], descriptor(result), result['provenance'])
        capsule = json.loads(raw)
        self.assertEqual(raw, A.canonical(capsule))
        self.assertEqual(capsule['qualification'], 'UNQUALIFIED_SOURCE_CPU_ONLY')
        self.assertEqual(capsule['source_sha256'], expected['source_sha256'])
        self.assertEqual(capsule['rigid_bodies'][0]['values']['words_le_hex'], expected['rigid']['F32_words_le_hex'])
        self.assertEqual(capsule['joints'][0]['values']['words_le_hex'], expected['joint']['F32_words_le_hex'])
        self.assertEqual(capsule['rigid_bodies'][0]['values']['nonfinite_word_indices'], [13])
        self.assertEqual(capsule['joints'][0]['values']['nonfinite_word_indices'], [23])
        self.assertEqual(capsule['rigid_bodies'][0]['collision_mask']['value'], 65535)
        self.assertEqual(capsule['rigid_bodies'][0]['bone']['value'], -1)
        self.assertEqual([row['name']['text'] for row in capsule['bones']], [row['name']['decoded'] for row in expected['bones']])
        self.assertFalse(descriptor(result)['native_simulation_supported'])
        self.assertFalse(result['provenance']['native_qualified'])

    def test_every_unrelated_typed_json_member_and_encoded_BIN_bytes_preserved(self):
        original = glb(); result = assembled(); changed, binary = unpack(result['glb'])
        del changed['asset']['extras'][A.KEY]
        self.assertTyped(changed, DOCUMENT)
        self.assertEqual(binary, BIN)
        self.assertEqual(unpack(original)[1], binary)

    def test_report_is_small_preserves_existing_members_and_64_instances_do_not_duplicate_capsule(self):
        report = {'adapter': 'unchanged_mmd', 'warnings': ['Existing warning'], 'scale': 0.08}
        before = copy.deepcopy(report); result = assembled(report=report)
        self.assertTyped(report, before)
        retained = copy.deepcopy(result['report']); del retained[A.KEY]
        self.assertTyped(retained, before)
        text = json.dumps(result['report'])
        self.assertNotIn('capsule_text', text); self.assertNotIn('words_le_hex', text)
        self.assertNotIn('source_sha256', text); self.assertNotIn('骨', text)
        metadata = [{'asset': 'same-owner-local.glb', 'metadata': result['report']} for _ in range(64)]
        A.check_project_metadata(metadata)
        self.assertLess(len(A.canonical(metadata)), A.HARD.project_metadata_bytes)
        self.assertEqual(text.count('native_simulation_supported'), 1)

    def test_original_copy_source_hash_type_and_length_mismatches_refuse_atomically(self):
        source, _e, identity = authored(); original = glb(); report = {'keep': True}
        cases = [(bytearray(source), source, identity), (source, source[:-1], identity),
                 (source, source, dict(identity, sha256='f' * 64)),
                 (source, source, dict(identity, bytes=True)),
                 (source, source, dict(identity, bytes=len(source) - 1))]
        for raw, owned, proof in cases:
            with self.subTest(proof=proof), self.assertRaises(A.Refusal):
                A.assemble(original, raw, owned, proof, report)
        self.assertEqual(original, glb()); self.assertEqual(report, {'keep': True})

    def test_unsupported_PMD_PMX21_truncated_and_QDEF_never_become_empty_capsules(self):
        source, _e, _identity = authored()
        qdef, e = build_fixture(); at = e['fields']['vertex.0.deform']['offset']
        variants = [b'Pmd' + source[3:], source[:4] + struct.pack('<f', 2.1) + source[8:],
                    source[:-1], qdef[:at] + b'\x04' + qdef[at + 1:]]
        for raw in variants:
            identity = {'bytes': len(raw), 'sha256': A.sha(raw)}
            with self.subTest(prefix=raw[:8]), self.assertRaises(A.Refusal):
                A.assemble(glb(), raw, raw, identity, {})

    def test_every_GLB_truncation_header_chunk_order_and_extra_chunk_refuses(self):
        raw = glb()
        for end in range(len(raw)):
            with self.subTest(end=end), self.assertRaises(A.Refusal): A.read_glb(raw[:end])
        variants = [b'BAD!' + raw[4:], raw[:4] + struct.pack('<I', 1) + raw[8:],
                    raw + b'EXTRA', raw[:16] + struct.pack('<I', A.BIN_CHUNK) + raw[20:]]
        for value in variants:
            with self.assertRaises(A.Refusal): A.read_glb(value)

    def test_strict_JSON_duplicate_keys_nonfinite_invalid_UTF8_and_non_JSON_report_types(self):
        for raw in (b'{"asset":{"version":"2.0","version":"2.0"}}',
                    b'{"asset":{"version":"2.0"},"bad":NaN}', b'\xff'):
            with self.assertRaises(A.Refusal): A.read_glb(glb_json(raw))
        for report in ({'bad': (1, 2)}, {1: 'bad'}, {'bad': math.inf}):
            with self.assertRaises(A.Refusal): assembled(report=report)

    def test_occupied_or_non_object_extras_and_report_descriptor_collisions_refuse(self):
        for value in (None, [], {A.KEY: None}):
            document = copy.deepcopy(DOCUMENT); document['asset']['extras'] = value
            with self.assertRaises(A.Refusal): assembled(document=document)
        with self.assertRaises(A.Refusal): assembled(report={A.KEY: {'old': 'never overwrite'}})

    def test_missing_extra_version_and_boolean_archive_fields_refuse(self):
        result = assembled()
        actions = [lambda e: e.pop('capsule_text'), lambda e: e.update(extra='unknown'),
                   lambda e: e.update(version=True), lambda e: e.update(version=2),
                   lambda e: e.update(runtime_supported=0), lambda e: e.update(native_qualified=True)]
        for action in actions:
            with self.assertRaises(A.Refusal): A.extract(modified(result, action), descriptor(result), result['provenance'])

    def test_checksum_and_retained_provenance_descriptor_tampering_refuse(self):
        result = assembled()
        raw = modified(result, lambda e: e.update(capsule_text=e['capsule_text'][:-1]))
        with self.assertRaises(A.Refusal): A.extract(raw, descriptor(result), result['provenance'])
        for field, value in (('owned_copy_sha256', 'f' * 64), ('reader_sha256', 'f' * 64), ('native_qualified', True)):
            raw = modified(result, lambda e, f=field, v=value: e['provenance'].update({f: v}))
            with self.assertRaises(A.Refusal): A.extract(raw, descriptor(result), result['provenance'])
        with self.assertRaises(A.Refusal):
            A.extract(result['glb'], dict(descriptor(result), capsule_sha256='f' * 64), result['provenance'])

    def test_word_change_is_not_tolerated_even_if_envelope_checksum_is_repaired(self):
        result = assembled()
        def alter(envelope):
            value = json.loads(envelope['capsule_text'])
            value['rigid_bodies'][0]['values']['words_le_hex'][3] = '00000000'
            text = A.canonical(value); envelope['capsule_text'] = text.decode()
            envelope['provenance'].update(capsule_sha256=A.sha(text), capsule_bytes=len(text))
        changed = modified(result, alter)
        with self.assertRaisesRegex(A.Refusal, 'Retained capture provenance'):
            A.extract(changed, descriptor(result), result['provenance'])

    def test_malformed_raw_words_and_nonfinite_classification_refuse_before_provenance_join(self):
        result = assembled()
        for bad in ('GGGGGGGG', '0000000000'):
            def alter(e):
                value = json.loads(e['capsule_text']); value['rigid_bodies'][0]['values']['words_le_hex'][0] = bad
                text = A.canonical(value); e['capsule_text'] = text.decode(); e['provenance'].update(capsule_sha256=A.sha(text), capsule_bytes=len(text))
            with self.assertRaisesRegex(A.Refusal, 'binary32 words'):
                A.extract(modified(result, alter), descriptor(result), result['provenance'])
        def wrong(e):
            value = json.loads(e['capsule_text']); value['joints'][0]['values']['nonfinite_word_indices'] = []
            text = A.canonical(value); e['capsule_text'] = text.decode(); e['provenance'].update(capsule_sha256=A.sha(text), capsule_bytes=len(text))
        with self.assertRaisesRegex(A.Refusal, 'nonfinite classification'):
            A.extract(modified(result, wrong), descriptor(result), result['provenance'])

    def test_capsule_whole_JSON_GLB_report_and_project_exact_capacity_edges(self):
        result = assembled(); raw = A.extract(result['glb'], descriptor(result), result['provenance'])
        json_bytes = struct.unpack_from('<I', result['glb'], 12)[0]
        boundaries = {'capsule_bytes': len(raw), 'json_bytes': json_bytes,
                      'glb_bytes': len(result['glb']), 'report_bytes': len(A.canonical(result['report']))}
        for field, exact in boundaries.items():
            self.assertEqual(assembled(limits=replace(A.Limits(), **{field: exact}))['glb'], result['glb'])
            with self.subTest(field=field), self.assertRaises(A.Refusal):
                assembled(limits=replace(A.Limits(), **{field: exact - 1}))
        metadata = [{'metadata': result['report']}] * 64; length = len(A.canonical(metadata))
        A.check_project_metadata(metadata, replace(A.Limits(), project_metadata_bytes=length))
        with self.assertRaises(A.Refusal): A.check_project_metadata(metadata, replace(A.Limits(), project_metadata_bytes=length - 1))

    def test_escaped_envelope_and_large_existing_JSON_are_measured_whole(self):
        document = copy.deepcopy(DOCUMENT); document['extras'] = {'large_existing': 'quote"backslash\\' * 300}
        before = len(glb(document)); result = assembled(document=document)
        json_count = struct.unpack_from('<I', result['glb'], 12)[0]
        self.assertGreater(json_count, len(A.extract(result['glb'], descriptor(result), result['provenance'])))
        self.assertGreater(len(result['glb']), before)
        with self.assertRaises(A.Refusal): assembled(document=document, limits=replace(A.Limits(), json_bytes=json_count - 1))

    def test_hard_caps_cannot_be_widened_or_retyped(self):
        for field in A.Limits.__dataclass_fields__:
            for bad in (True, -1, getattr(A.HARD, field) + 1):
                with self.subTest(field=field, bad=bad), self.assertRaises(A.Refusal):
                    assembled(limits=replace(A.Limits(), **{field: bad}))


if __name__ == '__main__': unittest.main(verbosity=2)

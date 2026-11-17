"""Independent authored byte expectations plus synthetic candidate comparisons.

Only tests import the candidate, under an exact source SHA. The oracle module
has no access to it; witnesses are obtained before each candidate invocation.
"""
import ast
import copy
from dataclasses import replace
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import oracle as O
import compare_tables as C
from synthetic_pmx import build_fixture
import manual_wide_fixture as W

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'experiments/pmx_physics_native_reader_prototype_20261117'
candidate_path = OLD / 'pmx_native_physics.py'
assert hashlib.sha256(candidate_path.read_bytes()).hexdigest() == 'e356894782e02389c215e2bdf335ebd102b98ad0b286e9728434201d21cf0426'
spec = importlib.util.spec_from_file_location('_existing_candidate_SYNTHETIC_TEST_ONLY', candidate_path)
R = importlib.util.module_from_spec(spec); sys.modules[spec.name] = R; spec.loader.exec_module(R)
MANUAL = json.loads((HERE / 'MANUAL_FIXTURE_EXPECTATIONS.json').read_bytes())
SMALL = bytes.fromhex(MANUAL['complete_hex'])


def changed(raw, at, word): return raw[:at] + word + raw[at + len(word):]


class OracleTests(unittest.TestCase):
    def compare_source(self, source):
        witness = O.read_oracle(source)
        capsule = R.read_pmx20_physics(source)
        result = C.compare(capsule, witness)
        self.assertFalse(result['native_qualified'])
        return witness, capsule

    def test_independent339_byte_fixed_offsets_words_and_names(self):
        with patch('builtins.open', side_effect=AssertionError('Oracle must not open any path')):
            witness = O.read_oracle(SMALL)
        self.assertEqual(witness['source'], {'sha256': MANUAL['sha256'], 'bytes': 339})
        self.assertEqual([row['span'] for row in witness['records']['bone']], [[53, 95], [95, 137]])
        body = witness['records']['body'][0]; joint = witness['records']['joint'][0]
        self.assertEqual(body['span'], [149, 223]); self.assertEqual(joint['span'], [227, 339])
        self.assertEqual(body['parameters']['start'], 166); self.assertEqual(joint['parameters']['start'], 243)
        self.assertEqual(body['parameters']['word_hex'], MANUAL['rigid0']['F32_words_le_hex'])
        self.assertEqual(joint['parameters']['word_hex'], MANUAL['joint0']['F32_words_le_hex'])
        self.assertEqual(body['mask']['hex'], '0180'); self.assertEqual(body['mask']['number'], 32769)
        self.assertEqual(joint['body_b']['number'], -1); self.assertEqual(joint['body_b']['hex'], 'ff')
        self.assertEqual([row['names'][0]['decoded'] for row in witness['records']['bone']], ['dup', 'dup'])
        self.assertTrue(C.compare(R.read_pmx20_physics(SMALL), witness)['candidate_unqualified_flag_preserved'])

    def test_new_manually_dimensioned_mixed_width_UTF16_two_body_joint_fixture(self):
        witness = O.read_oracle(W.DATA)
        self.assertEqual(witness['source']['bytes'], 531)
        self.assertEqual([r['span'] for r in witness['records']['bone']], [[53, 95], [95, 139]])
        self.assertEqual([r['span'] for r in witness['records']['body']], [[151, 224], [224, 297]])
        self.assertEqual([r['span'] for r in witness['records']['joint']], [[301, 416], [416, 531]])
        self.assertEqual([r['parameters']['start'] for r in witness['records']['body']], [167, 240])
        self.assertEqual([r['parameters']['start'] for r in witness['records']['joint']], [320, 435])
        self.assertEqual(witness['records']['body'][0]['parameters']['word_hex'], W.BODY0)
        self.assertEqual(witness['records']['body'][1]['parameters']['word_hex'], W.BODY1)
        self.assertEqual(witness['records']['joint'][0]['parameters']['word_hex'], W.JOINT0)
        self.assertEqual(witness['records']['joint'][1]['parameters']['word_hex'], W.JOINT1)
        self.assertEqual(witness['records']['body'][0]['parameters']['nonfinite_offsets'], [175, 179, 183])
        self.assertEqual(witness['records']['body'][0]['mask']['number'], 65535)
        self.assertEqual(witness['records']['body'][1]['mask']['number'], 32768)
        self.assertEqual(witness['records']['body'][0]['bone']['hex'], 'ffff')
        self.assertEqual(witness['records']['joint'][1]['body_a']['hex'], 'ffffffff')
        self.assertEqual(witness['records']['bone'][0]['names'][0]['encoded'], 'a89a')
        self.assertEqual(witness['records']['bone'][0]['names'][0]['decoded'], '骨')
        self.assertEqual(witness['records']['body'][1]['names'][0]['decoded'], '')
        self.assertEqual(witness['records']['body'][1]['names'][1]['decoded'], 'B')
        self.assertEqual(witness['header']['reference_widths'], {'vertex': 4, 'texture': 2, 'material': 1, 'bone': 2, 'morph': 4, 'body': 4})
        self.assertFalse(C.compare(R.read_pmx20_physics(W.DATA), witness)['native_qualified'])

    def test_all720_authored_prefix_layout_combinations_with_independent_expectations(self):
        count = 0
        for width, encoding, uv, deform, tail, flags in itertools.product((1, 2, 4), (0, 1), range(5), range(4), (False, True), (0, 0x300, 0x3f3f)):
            source, expected = build_fixture(width, encoding, uv, deform, tail, flags)
            witness = O.read_oracle(source)
            for category, name in (('body', 'rigid'), ('joint', 'joint')):
                row = witness['records'][category][0]; authored = expected[name]
                self.assertEqual(row['span'], [authored['offset'], authored['end']])
                self.assertEqual(row['parameters']['start'], authored['F32_offset'])
                self.assertEqual(row['parameters']['word_hex'], authored['F32_words_le_hex'])
                self.assertEqual(row['names'][0]['encoded'], authored['name']['raw_hex'])
            self.assertEqual(witness['source']['sha256'], expected['source_sha256'])
            capsule = R.read_pmx20_physics(source)
            self.assertFalse(C.compare(capsule, witness)['native_qualified'])
            count += 1
        self.assertEqual(count, 720)

    def test_exhaustive_truncation_of_both_manual_sources_and_full_optional_prefix(self):
        full, _e = build_fixture(index_size=4, encoding=0, additional_uv=4, deform=3, bone_flags=0x3f3f)
        for raw in (SMALL, W.DATA, full):
            for end in range(len(raw)):
                with self.subTest(size=len(raw), end=end), self.assertRaises(O.Refused): O.read_oracle(raw[:end])

    def test_header_unsupported_versions_widths_QDEF_and_trailing_data_refuse(self):
        raw, e = build_fixture(); at = e['fields']['vertex.0.deform']['offset']
        variants = [changed(raw, 0, b'BAD!'), changed(raw, 4, struct.pack('<f', 2.1)), changed(raw, 8, b'\x09'),
                    changed(raw, 9, b'\x02'), changed(raw, 10, b'\x05'), changed(raw, at, b'\x04'), raw + b'\x00' * 4]
        variants += [changed(raw, at, b'\x03') for at in range(11, 17)]
        for source in variants:
            with self.assertRaises(O.Refused): O.read_oracle(source)

    def test_unknown_material_bone_morph_display_and_joint_selectors_refuse(self):
        raw, e = build_fixture(bone_flags=0x3f3f)
        names = [('material.0.flags', b'\x20'), ('material.0.shared_toon', b'\x02'),
                 ('bone.0.flags', b'\x40\x00'), ('bone.0.IK.link0.limited', b'\x02'),
                 ('morph.0.type', b'\x09'), ('display.special', b'\x02'), ('display.bone.tag', b'\x02'), ('joint.mode', b'\x01')]
        for name, word in names:
            with self.subTest(field=name), self.assertRaises(O.Refused): O.read_oracle(changed(raw, e['fields'][name]['offset'], word))

    def test_negative_counts_and_nested_budgets_refuse(self):
        raw, e = build_fixture(bone_flags=0x3f3f)
        names = ['vertices.count', 'indices.count', 'textures.count', 'materials.count', 'bones.count',
                 'morphs.count', 'displays.count', 'rigids.count', 'joints.count', 'morph.0.offset_count']
        for name in names:
            with self.subTest(field=name), self.assertRaises(O.Refused): O.read_oracle(changed(raw, e['fields'][name]['offset'], struct.pack('<i', -1)))
        for limits in (replace(O.Limits(), morph_items=0), replace(O.Limits(), ik_links=0), replace(O.Limits(), display_items=0)):
            with self.assertRaises(O.Refused): O.read_oracle(raw, limits)

    def test_prefix_reference_ranges_and_minus_one_field_policy(self):
        raw, e = build_fixture()
        for name, value in [('vertex.0.bone0', -2), ('material.0.texture', -2), ('display.bone.index', -1),
                            ('morph.0.group_morph', -1), ('rigid.bone', -2), ('joint.source', 1)]:
            field = e['fields'][name]
            word = value.to_bytes(field['bytes'], 'little', signed=True)
            with self.subTest(field=name), self.assertRaises(O.Refused): O.read_oracle(changed(raw, field['offset'], word))
        # Legal raw absence remains distinct from zero; no physical-validity claim.
        witness, _capsule = self.compare_source(raw)
        self.assertEqual(witness['records']['body'][0]['bone']['number'], -1)

    def test_signedzero_subnormal_and_NaN_payloads_are_words_not_normalized_floats(self):
        for word, exceptional in [('00000080', False), ('01000000', False), ('4523c17f', True), ('0000807f', True), ('000080ff', True)]:
            raw = changed(SMALL, 166, bytes.fromhex(word)); witness, capsule = self.compare_source(raw)
            words = witness['records']['body'][0]['parameters']
            self.assertEqual(words['word_hex'][0], word)
            self.assertEqual(166 in words['nonfinite_offsets'], exceptional)
            self.assertEqual(capsule['rigid_bodies'][0]['values']['words_le_hex'][0], word)

    def test_resource_limits_are_strict_typed_and_never_widened(self):
        for limits in (None, {}, replace(O.Limits(), source_bytes=True), replace(O.Limits(), output_bytes=-1),
                       replace(O.Limits(), bone_count=4097)):
            with self.assertRaises(O.Refused): O.read_oracle(SMALL, limits)
        for limits in (replace(O.Limits(), source_bytes=338), replace(O.Limits(), output_bytes=1),
                       replace(O.Limits(), string_bytes=2), replace(O.Limits(), name_utf8_bytes=2),
                       replace(O.Limits(), bone_count=1), replace(O.Limits(), work_units=1)):
            with self.assertRaises(O.Refused): O.read_oracle(SMALL, limits)
        for raw in (bytearray(SMALL), memoryview(SMALL), None):
            with self.assertRaises(O.Refused): O.read_oracle(raw)

    def test_invalid_UTF8_odd_UTF16_and_isolated_surrogate_are_not_replaced(self):
        variants = [changed(SMALL, 57, b'\xff'), changed(W.DATA, 17, struct.pack('<i', 1)),
                    changed(W.DATA, 155, b'\x00\xd8')]
        for raw in variants:
            with self.assertRaisesRegex(O.Refused, 'encoded PMX text'): O.read_oracle(raw)

    def test_oracle_import_graph_and_API_have_no_candidate_or_caller_offsets(self):
        tree = ast.parse((HERE / 'oracle.py').read_text(encoding='utf-8'))
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        modules |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(modules, {'dataclasses', 'hashlib', 'json', 'struct'})
        with patch.object(R, 'read_pmx20_physics', side_effect=AssertionError('Oracle must not call candidate')):
            self.assertEqual(O.read_oracle(SMALL)['source']['bytes'], 339)


class ComparatorTests(unittest.TestCase):
    def pair(self):
        witness = O.read_oracle(W.DATA)
        return R.read_pmx20_physics(W.DATA), witness

    def test_candidate_words_names_spans_refs_masks_and_order_tampering_disagree(self):
        base, witness = self.pair()
        changes = [lambda c: c['rigid_bodies'][0]['values']['words_le_hex'].__setitem__(0, '00000000'),
                   lambda c: c['rigid_bodies'][0]['name'].__setitem__('raw_hex', '0000'),
                   lambda c: c['rigid_bodies'][0].__setitem__('offset', 152),
                   lambda c: c['rigid_bodies'][0]['bone'].__setitem__('value', 0),
                   lambda c: c['rigid_bodies'][0]['collision_mask'].__setitem__('value', 32767),
                   lambda c: c['joints'].reverse(), lambda c: c['bones'].reverse(),
                   lambda c: c['joints'][0]['values'].__setitem__('nonfinite_word_indices', [])]
        for mutate in changes:
            current = copy.deepcopy(base); mutate(current)
            with self.assertRaises(C.Disagreement): C.compare(current, witness)

    def test_witness_independent_field_tampering_and_reordered_prefix_disagree(self):
        capsule, base = self.pair()
        changes = [lambda w: w['records']['body'][0]['parameters']['word_hex'].__setitem__(1, '00000000'),
                   lambda w: w['records']['joint'][0]['body_a'].__setitem__('number', 1),
                   lambda w: w['records']['body'][0]['names'][0].__setitem__('decoded', 'different'),
                   lambda w: w['ranges'].reverse(), lambda w: w['source'].__setitem__('sha256', 'f' * 64)]
        for mutate in changes:
            current = copy.deepcopy(base); mutate(current)
            with self.assertRaises(C.Disagreement): C.compare(capsule, current)

    def test_missing_extra_bool_int_float_and_qualification_aliases_refuse(self):
        base, witness = self.pair()
        changes = [lambda c: c.pop('joints'), lambda c: c.update(extra='unexpected'),
                   lambda c: c['rigid_bodies'][0].__setitem__('native_index', False),
                   lambda c: c['rigid_bodies'][0]['bone'].__setitem__('value', -1.0),
                   lambda c: c['header'].__setitem__('encoding_byte', False),
                   lambda c: c.__setitem__('qualification', 'QUALIFIED')]
        for mutate in changes:
            current = copy.deepcopy(base); mutate(current)
            with self.assertRaises(C.Disagreement): C.compare(current, witness)
        bad = copy.deepcopy(witness); bad['native_qualified'] = 0
        with self.assertRaises(C.Disagreement): C.compare(base, bad)

    def test_duplicate_key_truncated_UTF8_and_oversize_JSON_inputs_refuse(self):
        capsule, witness = self.pair()
        candidate = json.dumps(capsule, separators=(',', ':'), ensure_ascii=False).encode()
        other = O.canonical(witness)
        self.assertFalse(C.compare_json(candidate, other)['native_qualified'])
        for raw in (b'{"format":"x","format":"y"}', candidate[:-1], b'\xff', b' ' * (2 * 1024 * 1024 + 1)):
            with self.assertRaises(C.Disagreement): C.compare_json(raw, other)

    def test_results_and_errors_do_not_publish_private_name_source_words_or_paths(self):
        capsule, witness = self.pair(); result = C.compare(capsule, witness)
        text = json.dumps(result)
        for secret in ('source_sha256', 'a89a', '4523c17f', '骨', 'code_filename', 'C:\\'):
            self.assertNotIn(secret, text)
        bad = copy.deepcopy(capsule); bad['rigid_bodies'][0]['name']['text'] = 'SECRET_PRIVATE_NATIVE_NAME'
        with self.assertRaises(C.Disagreement) as caught: C.compare(bad, witness)
        self.assertNotIn('SECRET_PRIVATE_NATIVE_NAME', str(caught.exception))
        self.assertFalse(result['physical_validity_simulation_portability_or_adoption'])

    def test_agreement_does_not_mutate_inputs_or_promote_candidate_flags(self):
        capsule, witness = self.pair(); before = copy.deepcopy((capsule, witness))
        C.compare(capsule, witness)
        self.assertEqual((capsule, witness), before)
        self.assertEqual(capsule['qualification'], 'UNQUALIFIED_SOURCE_CPU_ONLY')
        self.assertFalse(witness['native_qualified'])


if __name__ == '__main__': unittest.main(verbosity=2)

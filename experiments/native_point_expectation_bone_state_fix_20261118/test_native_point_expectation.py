"""Synthetic native-family CPU fixtures; no original asset or Blender import."""
import copy
from fractions import Fraction
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

import native_point_expectation as N

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JOIN_PATH = ROOT / 'experiments/native_normal_carrier_probe_20261117/exact_point_join.py'
JOIN_SHA = 'c3a5ac1acc6b6a2988020d924313f27fedaa371281bfeae5f6871a545d54d85d'


def append(raw, size):
    offset = len(raw)
    raw.extend(bytes(size))
    return offset


def pin(raw):
    raw = bytes(raw)
    return {'raw': raw, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def typed_fixture_value(value):
    if type(value) is float:
        return ('float', struct.pack('<d', value))
    if type(value) is list:
        return ('list', tuple(typed_fixture_value(item) for item in value))
    return (type(value).__name__, value)


def fixture(blank_model=False, blank_name=b'', bone_states=None):
    checksum = 0x1234FEDC
    mdl = bytearray(408)
    struct.pack_into('<4sII', mdl, 0, b'IDST', 49, checksum)
    bone_table = append(mdl, 3 * 216)
    part_table = append(mdl, 16)
    model_table = append(mdl, (2 if blank_model else 1) * 148)
    mesh_table = append(mdl, 2 * 116)
    struct.pack_into('<2I', mdl, 156, 3, bone_table)
    struct.pack_into('<2I', mdl, 232, 1, part_table)
    struct.pack_into('<3I', mdl, part_table + 4, 2 if blank_model else 1, 0, model_table - part_table)
    mdl[model_table:model_table + 8] = b'unit.smd'
    struct.pack_into('<4I', mdl, model_table + 72, 2, mesh_table - model_table, 6, 3 * 48)
    if blank_model:
        mdl[model_table + 148:model_table + 148 + len(blank_name)] = blank_name
    for index in range(2):
        struct.pack_into('<Ii3I', mdl, mesh_table + 116 * index, index, 0, 3, 3 * index, 0)
    for index, name in enumerate((b'root', b'arm', b'head')):
        base = bone_table + 216 * index
        offset = append(mdl, len(name) + 1)
        mdl[offset:offset + len(name)] = name
        struct.pack_into('<ii', mdl, base, offset - base, index - 1)
        struct.pack_into('<4f', mdl, base + 44, 0., 0., 0., 1.)
    name_offset = append(mdl, 5)
    mdl[name_offset:name_offset + 4] = b'body'
    struct.pack_into('<I', mdl, part_table, name_offset - part_table)
    struct.pack_into('<I', mdl, 76, len(mdl))

    vvd = bytearray(64)
    fixups = append(vvd, 24)
    vertex_table = append(vvd, 9 * 48)
    tangent_table = append(vvd, 9 * 16)
    struct.pack_into('<4s15I', vvd, 0, b'IDSV', 4, checksum, 4,
                     9, 8, 8, 1, 0, 0, 0, 0, 2, fixups, vertex_table, tangent_table)
    struct.pack_into('<6I', vvd, fixups, 3, 8, 1, 0, 0, 8)
    for index in range(9):
        base = vertex_table + 48 * index
        struct.pack_into('<3f4B3f3f2f', vvd, base,
                         .25, .75, 0., index % 3, index % 3, 255, 0,
                         index + .125, -0.0 if index == 4 else -.25 * index, 512. + index,
                         -0.0, 0., 1., -.0 if index == 4 else index / 8., index / 8.)
        struct.pack_into('<4f', vvd, tangent_table + 16 * index, 1., 0., 0., 1.)

    vtx = bytearray(36)
    replacements = append(vtx, 8)
    vtx_parts = append(vtx, 8)
    vtx_models = append(vtx, 16 if blank_model else 8)
    vtx_lods = append(vtx, 24 if blank_model else 12)
    vtx_meshes = append(vtx, 2 * 9)
    struct.pack_into('<IIHH6I', vtx, 0, 7, 32, 3, 3, 3, checksum, 1, replacements, 1, vtx_parts)
    struct.pack_into('<2I', vtx, vtx_parts, 2 if blank_model else 1, vtx_models - vtx_parts)
    struct.pack_into('<2i', vtx, vtx_models, 1, vtx_lods - vtx_models)
    struct.pack_into('<2If', vtx, vtx_lods, 2, vtx_meshes - vtx_lods, 0.)
    if blank_model:
        struct.pack_into('<2i', vtx, vtx_models + 8, 1, vtx_lods + 12 - (vtx_models + 8))
    group_tables, vertex_tables, index_tables, strip_tables, state_tables = [], [], [], [], []
    for index in range(2):
        mesh = vtx_meshes + 9 * index
        group = append(vtx, 25)
        vertices = append(vtx, 3 * 9)
        indices = append(vtx, 6)
        strips = append(vtx, 27)
        states = [] if bone_states is None else bone_states[index]
        state_table = append(vtx, 8 * len(states)) if states else None
        struct.pack_into('<2IB', vtx, mesh, 1, group - mesh, 0)
        struct.pack_into('<6IB', vtx, group, 3, vertices - group, 3, indices - group, 1, strips - group, 2)
        for slot, original in enumerate((2, 0, 1)):
            struct.pack_into('<H', vtx, vertices + 9 * slot + 4, original)
        struct.pack_into('<3H', vtx, indices, 0, 1, 2)
        struct.pack_into('<4IH B2I', vtx, strips, 3, 0, 3, 0, 3, 1,
                         len(states), state_table - strips if states else 0)
        for state_index, pair in enumerate(states):
            struct.pack_into('<2i', vtx, state_table + 8 * state_index, *pair)
        group_tables.append(group); vertex_tables.append(vertices)
        index_tables.append(indices); strip_tables.append(strips)
        state_tables.append(state_table)
    refs = {'mdl': pin(mdl), 'vvd': pin(vvd), 'vtx': pin(vtx)}
    offsets = {'mdl_bones': bone_table, 'mdl_part': part_table, 'mdl_model': model_table,
               'mdl_meshes': mesh_table, 'vvd_vertices': vertex_table, 'vvd_fixups': fixups,
               'vtx_replacements': replacements, 'vtx_models': vtx_models,
               'vtx_lods': vtx_lods, 'vtx_meshes': vtx_meshes,
               'vtx_groups': group_tables, 'vtx_vertices': vertex_tables,
               'vtx_indices': index_tables, 'vtx_strips': strip_tables, 'vtx_states': state_tables}
    return refs, offsets


def change(refs, family, fmt, offset, *values):
    result = copy.deepcopy(refs)
    raw = bytearray(result[family]['raw'])
    struct.pack_into(fmt, raw, offset, *values)
    result[family] = pin(raw)  # Mutation fixtures have their own synthetic identities.
    return result


IDS = [5, 3, 4, 8, 6, 7]
RAW_IDS = [4, 2, 3, 7, 5, 6]


def build(refs, ids=None, policy=N.COORDINATE_POLICY, name='unit.smd'):
    return N.build_native_point_expectation(refs, IDS[:] if ids is None else ids,
                                            policy, logical_name=name)


def exact_f32_word(value, negative_zero=False):
    """Independent integer/rational nearest-even oracle, without struct F32 cast."""
    sign = 0x80000000 if value < 0 or (value == 0 and negative_zero) else 0
    value = abs(Fraction(value))
    if not value:
        return sign
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    power = Fraction(2 ** exponent) if exponent >= 0 else Fraction(1, 2 ** -exponent)
    if value < power:
        exponent -= 1
    shift = 149 if exponent < -126 else 23 - exponent
    scaled = value * (2 ** shift if shift >= 0 else Fraction(1, 2 ** -shift))
    quotient, remainder = divmod(scaled.numerator, scaled.denominator)
    twice = remainder * 2
    significand = quotient + int(twice > scaled.denominator or
                                 (twice == scaled.denominator and quotient % 2))
    if exponent < -126:
        return sign | significand
    if significand == 1 << 24:
        exponent += 1; significand >>= 1
    return sign | ((exponent + 127) << 23) | (significand - (1 << 23))


class NativePointExpectationTests(unittest.TestCase):
    def test_bounded_nonconsumed_hardware_state_keeps_VVD_point_expectation(self):
        baseline_refs, _ = fixture(blank_model=True)
        baseline = build(baseline_refs)
        for states in ((((0, 2), (2, 0)), ((1, 1),)),
                       (((0, 1), (0, 2), (0, 0)), ((2, 2),))):
            refs, _ = fixture(blank_model=True, bone_states=states)
            result = build(refs)
            for field in ('source_lod0_vertex_indices', 'source_raw_vertex_indices', 'vertices',
                          'corner_vertex_indices', 'vertex_groups', 'vertex_weights', 'corner_uv_active',
                          'object_matrix_world', 'armature_matrix_world', 'normal_transform',
                          'native_normal_words_as_F32'):
                self.assertEqual(typed_fixture_value(result[field]), typed_fixture_value(baseline[field]))
            self.assertNotEqual(result['source_identities']['vtx'], baseline['source_identities']['vtx'])
            self.assertIs(result['VTX_hardware_palette_or_render_equivalence_qualified'], False)
            self.assertIs(N.derive_native_point_rows(refs)['VTX_hardware_palette_or_render_equivalence_qualified'], False)

    def test_bone_state_signed_ranges_offsets_counts_and_table_overlap_refused(self):
        refs, o = fixture(bone_states=(((0, 0), (2, 2)), ((1, 1),)))
        state, strip = o['vtx_states'][0], o['vtx_strips'][0]
        cases = [('<i', state, -1), ('<i', state, 3), ('<i', state + 4, -1),
                 ('<i', state + 4, 3), ('<I', strip + 19, 513),
                 ('<I', strip + 19, 0xffffffff), ('<I', strip + 23, 0),
                 ('<I', strip + 23, len(refs['vtx']['raw']) - strip - 1),
                 ('<I', strip + 23, o['vtx_vertices'][1] - strip),
                 ('<I', strip + 23, o['vtx_strips'][1] - strip),
                 ('<I', strip + 23, o['vtx_states'][1] - strip),
                 ('<H', 8, 0), ('<H', 8, 513)]
        for fmt, offset, value in cases:
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                build(change(refs, 'vtx', fmt, offset, value))

    def test_bone_state_declared_slot_boundary_and_aggregate_budget(self):
        refs, o = fixture(bone_states=(((511, 0),), ((0, 0),)))
        refs = change(refs, 'vtx', '<H', 8, 512)
        self.assertEqual(build(refs)['source_lod0_vertex_indices'], IDS)
        largest_strip, _ = fixture(bone_states=(tuple((0, index % 3) for index in range(512)), ()))
        self.assertEqual(build(largest_strip)['source_lod0_vertex_indices'], IDS)
        # A small explicit budget exercises accumulation across independently
        # bounded strip tables without allocating a large synthetic payload.
        previous = N.MAX_BONE_STATE_ROWS
        try:
            N.MAX_BONE_STATE_ROWS = 1
            with self.assertRaisesRegex(ValueError, 'Aggregate VTX bone-state row budget'):
                build(refs)
        finally:
            N.MAX_BONE_STATE_ROWS = previous

    def test_empty_zero_vertex_model_uses_source_fallback_and_import_skip(self):
        refs, _ = fixture(blank_model=True)
        decoded = N._mdl(refs['mdl']['raw'])
        self.assertEqual(decoded['parts'][0][1]['name'], 'blank')
        self.assertEqual(decoded['parts'][0][1]['count'], 0)
        source = N.derive_native_point_rows(refs)
        self.assertEqual(set(source['models']), {'unit.smd'})
        result = build(refs)
        original, _ = fixture(); baseline = build(original)
        for field in ('source_lod0_vertex_indices', 'source_raw_vertex_indices', 'vertices',
                      'corner_vertex_indices', 'vertex_groups', 'vertex_weights', 'corner_uv_active',
                      'object_matrix_world', 'armature_matrix_world', 'normal_transform',
                      'native_normal_words_as_F32'):
            self.assertEqual(result[field], baseline[field])
        self.assertIs(result['native_expected_adapter_independently_qualified'], False)

    def test_empty_renderable_or_invalid_ascii_models_still_refused(self):
        refs, offsets = fixture(blank_model=True)
        empty_renderable = copy.deepcopy(refs)
        raw = bytearray(refs['mdl']['raw'])
        raw[offsets['mdl_model']:offsets['mdl_model'] + 64] = bytes(64)
        empty_renderable['mdl'] = pin(raw)
        with self.assertRaisesRegex(ValueError, 'Bounded ASCII model name required'):
            build(empty_renderable)
        bad, _ = fixture(blank_model=True, blank_name=b'\xff')
        with self.assertRaisesRegex(ValueError, 'Bounded ASCII model name required'):
            build(bad)
        # SourceIO strips leading NULs before decoding this fixed field. It is
        # not an empty source name if a later byte is nonzero; no fallback.
        for name in (b'\0later', b'\0\xff'):
            bad, _ = fixture(blank_model=True, blank_name=name)
            with self.assertRaisesRegex(ValueError, 'Bounded ASCII model name required'):
                build(bad)
        # Blank metadata still validates declared table seeks before skipping.
        bad = change(refs, 'mdl', '<I', offsets['mdl_model'] + 148 + 104, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'eyeball seek'):
            build(bad)

    def test_independent_native_rows_fixups_and_mesh_order(self):
        refs, _ = fixture()
        result = N.derive_native_point_rows(refs)
        model = result['models']['unit.smd']
        self.assertEqual(model['ids'], IDS)
        self.assertEqual(model['raw_ids'], RAW_IDS)
        self.assertEqual(model['corners'], [5, 4, 3, 2, 1, 0])
        self.assertEqual(model['materials'], [1, 0])
        self.assertEqual(result['vertex_groups'], ['root', 'arm', 'head'])
        self.assertEqual(result['native_bone_parents'], [-1, 0, 1])
        self.assertEqual(model['rows'][0]['positive_weight_writes'], [[1, .25], [1, .75]])
        self.assertFalse(result['native_adapter_independently_qualified'])

    def test_exact_scaled_words_signed_zero_uv_and_replace(self):
        refs, _ = fixture(); result = build(refs)
        # Fixed binary32 words are independently calculated fixture expectations.
        self.assertEqual(struct.pack('<3f', *result['vertices'][0]).hex(), '35efa03d00000080dc461d41')
        scale = Fraction(0x9c0ebf, 1 << 29)  # Binary32 .01905, independently decoded.
        for index, position in zip(RAW_IDS, result['vertices']):
            expected_words = [exact_f32_word(Fraction(8 * index + 1, 8) * scale),
                              exact_f32_word(Fraction(-index, 4) * scale) if index != 4 else 0x80000000,
                              exact_f32_word((512 + index) * scale)]
            self.assertEqual(list(struct.unpack('<3I', struct.pack('<3f', *position))), expected_words)
        self.assertEqual(struct.pack('<3f', *result['native_normal_words_as_F32'][0]).hex(), '00000080000000000000803f')
        self.assertEqual(struct.pack('<2f', *result['corner_uv_active'][-1]).hex(), '000000800000003f')
        self.assertEqual(result['vertex_weights'], [[[raw % 3, .75]] for raw in RAW_IDS])
        self.assertEqual(result['position_scale_F32'], struct.unpack('<f', bytes.fromhex('bf0e9c3c'))[0])
        self.assertEqual(result['source_identities'], {key: {field: row[field] for field in ('bytes', 'sha256')} for key, row in refs.items()})
        for field in ('native_expected_adapter_independently_qualified', 'actual_native_family_profile_observed',
                      'Blender_storage_or_validate_behavior_qualified', 'nearest_matching_used',
                      'source_unit_conversion_changed', 'six_foot_normalization_applied',
                      'native_runtime_or_normal_fidelity_qualified'):
            self.assertIs(result[field], False)

    def test_generalized_ledger_exhaustive_three_slot_sequences(self):
        import itertools
        for groups in itertools.product((0, 1, 2, 255), repeat=3):
            for weights in itertools.product((0., -.0, .25, .5, 1.), repeat=3):
                writes = [list(pair) for pair in zip(groups, weights)]
                # Independent history model: retain only latest positive write per group,
                # ordered by the earliest positive event for that group.
                positives = [(slot, group, weight) for slot, (group, weight) in enumerate(writes) if weight > 0]
                first = {group: min(slot for slot, other, _ in positives if other == group) for _, group, _ in positives}
                last = {group: weight for _, group, weight in positives}
                expected = [[group, last[group]] for group in sorted(first, key=first.get)]
                self.assertEqual(N.replay_replace_weight_writes(writes), expected)

    def test_multi_group_is_explicitly_refused_without_native_storage_policy(self):
        refs, offsets = fixture()
        refs = change(refs, 'vvd', '<B', offsets['vvd_vertices'] + 4 * 48 + 13, 2)
        source = N.derive_native_point_rows(refs)
        self.assertEqual(source['models']['unit.smd']['rows'][0]['positive_weight_writes'], [[1, .25], [2, .75]])
        with self.assertRaisesRegex(ValueError, 'stored-weight order is unproved'):
            build(refs)

    def test_identity_inputs_pinned_and_immutable(self):
        refs, _ = fixture()
        for family in refs:
            for field, value in [('sha256', '0' * 64), ('bytes', True), ('raw', bytearray(refs[family]['raw']))]:
                bad = copy.deepcopy(refs); bad[family][field] = value
                with self.subTest(family=family, field=field), self.assertRaises(ValueError): build(bad)
        bad = copy.deepcopy(refs); bad['vvd']['sha256'] = bad['vvd']['sha256'].upper()
        with self.assertRaises(ValueError): build(bad)
        bad = copy.deepcopy(refs); bad['unexpected'] = refs['mdl']
        with self.assertRaises(ValueError): build(bad)

    def test_no_permutation_nearest_or_policy_fallback(self):
        refs, _ = fixture()
        for ids in (IDS[::-1], [5, 3, 4, 8, 6, True], IDS[:-1], [5] * 6):
            with self.subTest(ids=ids), self.assertRaises(ValueError): build(refs, ids=ids)
        for policy in (None, '.01905', N.COORDINATE_POLICY + '_sixfoot'):
            with self.assertRaises(ValueError): build(refs, policy=policy)
        with self.assertRaises(ValueError): build(refs, name='UNIT.SMD')

    def test_family_headers_checksums_and_sizes(self):
        refs, _ = fixture()
        cases = [('mdl', '<I', 4, 48), ('mdl', '<I', 76, 408), ('mdl', '<I', 152, 16),
                 ('vvd', '<I', 4, 5), ('vvd', '<I', 8, 1), ('vtx', '<I', 0, 6),
                 ('vtx', '<I', 12, 4), ('vtx', '<I', 16, 1), ('vtx', '<I', 20, 2)]
        for family, fmt, offset, value in cases:
            with self.subTest(family=family, offset=offset), self.assertRaises(ValueError):
                build(change(refs, family, fmt, offset, value))
        for family in refs:
            bad = copy.deepcopy(refs); bad[family] = pin(refs[family]['raw'][:35])
            with self.assertRaises(ValueError): build(bad)

    def test_native_model_bone_range_and_feature_refusals(self):
        refs, o = fixture()
        cases = [('mdl', '<I', o['mdl_model'] + 84, 1),
                 ('mdl', '<I', o['mdl_model'] + 100, 1),
                 ('mdl', '<I', o['mdl_model'] + 104, 0xffffffff),
                 ('mdl', '<I', o['mdl_model'] + 80, 7),
                 ('mdl', '<I', o['mdl_meshes'] + 16, 1),
                 ('mdl', '<i', o['mdl_bones'] + 4, 0),
                 ('mdl', '<I', 156, 257),
                 ('mdl', '<I', 160, 408 - 1),
                 ('mdl', '<I', o['mdl_meshes'] + 12, 6),
                 ('vvd', '<B', o['vvd_vertices'] + 4 * 48 + 12, 255)]
        for family, fmt, offset, value in cases:
            with self.subTest(family=family, offset=offset), self.assertRaises(ValueError):
                build(change(refs, family, fmt, offset, value))

    def test_vvd_fixup_overlap_extra_uv_and_value_guards(self):
        refs, o = fixture()
        cases = [('<I', 12, 9), ('<I', 16, N.MAX_POINTS + 1),
                 ('<I', 48, N.MAX_POINTS + 1), ('<I', 52, o['vvd_vertices']),
                 ('<I', 60, 0), ('<I', o['vvd_fixups'], 8),
                 ('<I', o['vvd_fixups'] + 8, 10), ('<I', o['vvd_fixups'] + 20, 7),
                 ('<f', o['vvd_vertices'], -1.), ('<f', o['vvd_vertices'] + 16, float('inf')),
                 ('<f', o['vvd_vertices'] + 28, .5), ('<f', o['vvd_vertices'] + 40, float('nan'))]
        for fmt, offset, value in cases:
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                build(change(refs, 'vvd', fmt, offset, value))
        bad = copy.deepcopy(refs); bad['vvd'] = pin(refs['vvd']['raw'] + b'\0' * 8)
        with self.assertRaisesRegex(ValueError, 'Trailing VVD'): build(bad)

    def test_vtx_topology_partitions_and_aggregate_budgets(self):
        refs, o = fixture()
        cases = [('<I', 28, 2), ('<i', o['vtx_models'], 9),
                 ('<i', o['vtx_replacements'], 1),
                 ('<i', o['vtx_replacements'] + 4, 0x7fffffff),
                 ('<I', o['vtx_lods'], 1), ('<I', o['vtx_meshes'] + 4, 1),
                 ('<I', o['vtx_groups'][0], N.MAX_POINTS + 1),
                 ('<I', o['vtx_groups'][0] + 8, N.MAX_CORNERS + 1),
                 ('<H', o['vtx_vertices'][0] + 4, 3),
                 ('<H', o['vtx_indices'][0], 3),
                 ('<H', o['vtx_indices'][0], 1),
                 ('<I', o['vtx_strips'][0] + 8, 2),
                 ('<B', o['vtx_strips'][0] + 18, 2),
                 ('<I', o['vtx_strips'][0] + 19, 1),
                 ('<I', o['vtx_strips'][0] + 23, 0xffffffff)]
        for fmt, offset, value in cases:
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                build(change(refs, 'vtx', fmt, offset, value))

    def test_empty_vtx_traversal_offsets_remain_bounded(self):
        refs, o = fixture()
        # A zero-group first mesh is a valid point-source subset; second mesh
        # still provides a complete triangle and an independently derived order.
        no_first_group = change(refs, 'vtx', '<2I', o['vtx_meshes'], 0, 0)
        subset = build(no_first_group, ids=[8, 6, 7])
        self.assertEqual(subset['corner_vertex_indices'], [2, 1, 0])
        bad = change(no_first_group, 'vtx', '<I', o['vtx_meshes'] + 4, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'strip-group seek'):
            build(bad, ids=[8, 6, 7])
        blank_mdl = {'checksum': 0x1234fedc,
                     'parts': [[{'name': 'blank', 'count': 0, 'start': 0, 'meshes': []}]]}
        no_meshes = change(refs, 'vtx', '<2I', o['vtx_lods'], 0, 0)
        self.assertEqual(N._vtx(no_meshes['vtx']['raw'], blank_mdl), {})
        bad = change(no_meshes, 'vtx', '<I', o['vtx_lods'] + 4, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'Empty VTX mesh seek'):
            N._vtx(bad['vtx']['raw'], blank_mdl)

    def test_duplicate_point_and_selected_raw_identity_refusals(self):
        refs, o = fixture()
        with self.assertRaisesRegex(ValueError, 'Repeated source point identities'):
            build(change(refs, 'vtx', '<H', o['vtx_vertices'][0] + 4, 0))
        raw = bytearray(refs['vvd']['raw'])
        raw[o['vvd_vertices']:o['vvd_vertices']] = bytes(12)
        struct.pack_into('<4I', raw, 48, 3, o['vvd_fixups'], o['vvd_vertices'] + 12,
                         len(raw) - 9 * 16)
        struct.pack_into('<9I', raw, o['vvd_fixups'], 3, 8, 1, 0, 0, 4, 0, 3, 4)
        bad = copy.deepcopy(refs); bad['vvd'] = pin(raw)
        with self.assertRaisesRegex(ValueError, 'Repeated original raw IDs'):
            build(bad)

    def test_structural_table_limit_and_overlap_are_bounded(self):
        reader = N._Reader(bytes(16 + 4 * N.MAX_TABLES), 'synthetic', 16)
        for index in range(N.MAX_TABLES - 1):
            reader.table(16 + 4 * index, 1, 4, 'synthetic', 1)
        with self.assertRaisesRegex(ValueError, 'Table-count budget'):
            reader.table(16 + 4 * (N.MAX_TABLES - 1), 1, 4, 'over-budget', 1)
        reader = N._Reader(bytes(64), 'synthetic', 16)
        reader.table(32, 2, 4, 'later', 2)
        reader.table(16, 2, 4, 'earlier', 2)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            reader.table(22, 4, 4, 'overlap', 4)

    def test_existing_exact_join_accepts_independently_authored_snapshot(self):
        self.assertEqual(hashlib.sha256(JOIN_PATH.read_bytes()).hexdigest(), JOIN_SHA)
        spec = importlib.util.spec_from_file_location('existing_exact_point_join', JOIN_PATH)
        join = importlib.util.module_from_spec(spec); spec.loader.exec_module(join)
        refs, _ = fixture(); expected = build(refs)
        raw = RAW_IDS
        # Snapshot is authored directly from the fixture construction, not copied
        # from producer output. Native topology order is the fixed expected list.
        vertices = [[N.f32((index + .125) * N.F32_SCALE),
                     N.f32((-0.0 if index == 4 else -.25 * index) * N.F32_SCALE),
                     N.f32((512. + index) * N.F32_SCALE)] for index in raw]
        corners = [5, 4, 3, 2, 1, 0]
        snapshot = {'name': 'unit.smd', 'mesh_name': 'synthetic_MESH', 'vertices': vertices,
                    'corner_vertex_indices': corners, 'corner_edge_indices': [0, 1, 2, 3, 4, 5],
                    'edges': [[5, 4], [4, 3], [3, 5], [2, 1], [1, 0], [0, 2]],
                    'faces': [{'start': 0, 'count': 3, 'material': 1, 'smooth': True},
                              {'start': 3, 'count': 3, 'material': 0, 'smooth': True}],
                    'vertex_groups': ['root', 'arm', 'head'],
                    'vertex_weights': [[[index % 3, .75]] for index in raw],
                    'corner_uv_active': [[-.0 if raw[i] == 4 else raw[i] / 8., N.f32(1. - raw[i] / 8.)] for i in corners],
                    'object_matrix_world': [[float(r == c) for c in range(4)] for r in range(4)],
                    'armature_matrix_world': [[float(r == c) for c in range(4)] for r in range(4)],
                    'normal_transform': [[float(r == c) for c in range(3)] for r in range(3)]}
        setter = {'source_lod0_vertex_indices': IDS[:], 'source_raw_vertex_indices': RAW_IDS[:],
                  'initial_vertices': copy.deepcopy(vertices), 'initial_corner_indices': corners[:],
                  'setter_payload': [[-0., 0., 1.] for _ in IDS]}
        result, report = join.join_saved_point_ids('unit.smd', snapshot, setter, copy.deepcopy(snapshot), expected)
        self.assertEqual(result, tuple(IDS))
        self.assertIs(report['exact_components_joined'], True)
        self.assertIs(report['native_expected_adapter_independently_qualified'], False)
        bad = copy.deepcopy(snapshot); bad['vertices'][0][0] = N.f32(bad['vertices'][0][0] + .01)
        with self.assertRaises(ValueError):
            join.join_saved_point_ids('unit.smd', bad, setter, copy.deepcopy(bad), expected)


if __name__ == '__main__':
    unittest.main()

"""Unrun, entirely fabricated byte fixtures; no native assets or host imports."""
import copy
import hashlib
import struct
import unittest

import material_metadata as oracle

CHECKSUM = 0x1234ABCD


def family():
    """Hand-laid independent fixture: 2 materials, 2 skins, 2 models/3 meshes.

    Explicit offsets/strides intentionally do not use the parser's constants.
    VVD vertex payload and VTX strip groups are not geometry-valid fixtures:
    this suite qualifies only the metadata reader's intentionally narrow scope.
    """
    mdl = bytearray(1216)
    struct.pack_into('<4sII', mdl, 0, b'IDST', 49, CHECKSUM)
    # textures408..536, paths536..548, skins548..556, body556..572,
    # models572..868, meshes868..1216. Strings follow all structural tables.
    struct.pack_into('<7I', mdl, 204, 2, 408, 3, 536, 2, 2, 548)
    struct.pack_into('<2I', mdl, 232, 1, 556)
    def text(value):
        offset = len(mdl)
        mdl.extend(value + b'\0')
        return offset
    hair = text(b'test/hair')
    hat = text(b'test/hat')
    path = text(b'models/synthetic/')
    body = text(b'body')
    struct.pack_into('<iII', mdl, 408, hair - 408, 5, 3)
    struct.pack_into('<iII', mdl, 472, hat - 472, 9, 1)
    struct.pack_into('<3i', mdl, 536, 0, path, path)
    struct.pack_into('<4H', mdl, 548, 1, 0, 0, 1)
    struct.pack_into('<4I', mdl, 556, body - 556, 2, 17, 16)
    mdl[572:572 + 10] = b'front.smd\0'
    mdl[720:720 + 9] = b'back.smd\0'
    struct.pack_into('<4I', mdl, 644, 2, 296, 6, 0)
    struct.pack_into('<4I', mdl, 792, 1, 380, 3, 288)
    for offset, material, count, start in ((868, 1, 3, 0), (984, 0, 3, 3), (1100, 0, 3, 0)):
        struct.pack_into('<Ii3I', mdl, offset, material, -7, count, start, 0)
        struct.pack_into('<2I', mdl, offset + 24, 0, 0)
    struct.pack_into('<I', mdl, 76, len(mdl))
    vvd = bytearray(640)
    # 64-byte header, nine48-byte vertex records, nine16-byte tangents.
    struct.pack_into('<4s15I', vvd, 0, b'IDSV', 4, CHECKSUM, 1,
                     9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 496)
    vtx = bytearray(119)
    struct.pack_into('<IIHH6I', vtx, 0, 7, 32, 3, 3, 3, CHECKSUM, 1, 36, 1, 44)
    struct.pack_into('<2i', vtx, 36, 0, 0)
    struct.pack_into('<2I', vtx, 44, 2, 8)
    struct.pack_into('<2i', vtx, 52, 1, 16)
    struct.pack_into('<2i', vtx, 60, 1, 20)
    struct.pack_into('<2If', vtx, 68, 2, 24, 0.)
    struct.pack_into('<2If', vtx, 80, 1, 30, 0.)
    return {'mdl': bytes(mdl), 'vvd': bytes(vvd), 'vtx': bytes(vtx)}


def descriptors(values):
    return {role: dict(raw=raw, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            for role, raw in values.items()}


def changed(values, role, offset, fmt, *numbers):
    result = dict(values)
    raw = bytearray(result[role])
    struct.pack_into(fmt, raw, offset, *numbers)
    result[role] = bytes(raw)
    return result


class MaterialMetadataTests(unittest.TestCase):
    def decode(self, values=None):
        return oracle.derive_material_metadata(descriptors(family() if values is None else values))

    def refused(self, values, code):
        with self.assertRaisesRegex(oracle.Refusal, '^' + code + '$'):
            self.decode(values)

    def test_nontrivial_native_domains_order_and_metadata_are_preserved(self):
        result = self.decode()
        self.assertEqual(result['checksum'], CHECKSUM)
        meta = result['metadata']
        self.assertEqual([(m['index'], m['name'], m['flags'], m['used']) for m in meta['materials']],
                         [(0, 'test/hair', 5, 3), (1, 'test/hat', 9, 1)])
        self.assertEqual(meta['search_paths'], ['', 'models/synthetic/', 'models/synthetic/'])
        self.assertEqual(meta['skin_families'], [[1, 0], [0, 1]])
        self.assertEqual(meta['skin_reference_count'], 2)
        self.assertEqual(meta['body_parts'][0]['body_base'], 17)
        models = meta['body_parts'][0]['models']
        self.assertEqual([(m['native_name'], m['vertex_start'], m['vertex_count']) for m in models],
                         [('front.smd', 0, 6), ('back.smd', 6, 3)])
        self.assertEqual([[m['material_index'] for m in model['meshes']] for model in models], [[1, 0], [0]])
        self.assertEqual([[m['vertex_start'] for m in model['meshes']] for model in models], [[0, 3], [0]])
        self.assertEqual((meta['model_records'], meta['mesh_records']), (2, 3))

    def test_digest_binding_is_private_input_identity_not_current_output(self):
        values = family()
        result = self.decode(values)
        self.assertEqual(result['source_identities'], {role: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                                                     for role, raw in values.items()})
        self.assertEqual(result['metadata']['materials'][0]['descriptor_sha256'],
                         hashlib.sha256(values['mdl'][408:472]).hexdigest())

    def test_no_geometry_face_slot_resource_or_application_claim_is_made(self):
        result = self.decode()
        for key, value in result.items():
            if key.endswith('_qualified'):
                self.assertIs(value, False, key)
        self.assertFalse(result['VTX_face_material_order_qualified'])
        self.assertNotIn('faces', result['metadata'])
        self.assertNotIn('positions', result['metadata'])

    def test_exact_three_role_and_descriptor_schemas_are_required(self):
        refs = descriptors(family())
        for bad in ({key: value for key, value in refs.items() if key != 'vtx'}, dict(refs, other=refs['mdl'])):
            with self.assertRaisesRegex(oracle.Refusal, 'EXACT_THREE_NATIVE_INPUTS'):
                oracle.derive_material_metadata(bad)
        refs['mdl']['observed_slots'] = [0]
        with self.assertRaisesRegex(oracle.Refusal, 'EXACT_NATIVE_DESCRIPTOR_SCHEMA'):
            oracle.derive_material_metadata(refs)

    def test_mutable_bytes_boolean_count_uppercase_or_wrong_digest_refuse(self):
        for key, value in (('raw', bytearray(family()['mdl'])), ('bytes', True),
                           ('sha256', descriptors(family())['mdl']['sha256'].upper()), ('sha256', '0' * 64)):
            refs = descriptors(family())
            refs['mdl'][key] = value
            with self.assertRaises(oracle.Refusal): oracle.derive_material_metadata(refs)

    def test_each_native_signature_or_version_is_checked(self):
        for role, offset, fmt, value, code in (
            ('mdl', 0, '<4s', b'NOPE', 'MDL49_SIGNATURE_VERSION'),
            ('mdl', 4, '<I', 48, 'MDL49_SIGNATURE_VERSION'),
            ('vvd', 0, '<4s', b'NOPE', 'VVD4_SIGNATURE_VERSION'),
            ('vvd', 4, '<I', 3, 'VVD4_SIGNATURE_VERSION'),
            ('vtx', 0, '<I', 6, 'STANDARD_VTX7_THREE_SLOT_ONE_LOD_PROFILE')):
            self.refused(changed(family(), role, offset, fmt, value), code)

    def test_cross_family_checksums_refuse_even_with_matching_new_descriptor_hashes(self):
        for role, offset in (('mdl', 8), ('vtx', 16)):
            self.refused(changed(family(), role, offset, '<I', CHECKSUM + 1), 'NATIVE_FAMILY_CHECKSUM')

    def test_declared_mdl_size_and_truncation_are_checked(self):
        self.refused(changed(family(), 'mdl', 76, '<I', 408), 'MDL_DECLARED_SIZE')
        values = family(); values['mdl'] = values['mdl'][:407]
        self.refused(values, 'IMMUTABLE_BOUNDED_NATIVE_BYTES')

    def test_material_count_and_table_extents_are_bounded_before_iteration(self):
        self.refused(changed(family(), 'mdl', 204, '<I', 257), 'MATERIAL_COUNT_BUDGET')
        for offset in (0, 1, len(family()['mdl']) - 1):
            self.refused(changed(family(), 'mdl', 208, '<I', offset), 'TRUNCATED_OR_HEADER_ALIASED_TABLE')

    def test_structural_tables_must_not_overlap(self):
        self.refused(changed(family(), 'mdl', 216, '<I', 408), 'OVERLAPPING_METADATA_TABLES')
        self.refused(changed(family(), 'mdl', 656, '<I', 47), 'MODEL_VVD_RANGE_OR_BYTE_ALIGNMENT')

    def test_string_offsets_cannot_alias_tables_or_escape_file(self):
        self.refused(changed(family(), 'mdl', 408, '<i', 164), 'STRING_ALIASES_METADATA_TABLE')
        self.refused(changed(family(), 'mdl', 408, '<i', 2**31 - 1), 'STRING_OFFSET_DOMAIN')
        self.refused(changed(family(), 'mdl', 408, '<i', -1), 'NEGATIVE_STRING_OFFSET_OUTSIDE_PROFILE')
        self.refused(changed(family(), 'mdl', 408, '<i', 0), 'EMPTY_REQUIRED_METADATA_NAME')

    def test_unterminated_and_non_ascii_material_names_refuse(self):
        values = family(); raw = bytearray(values['mdl'])
        offset = 408 + struct.unpack_from('<i', raw, 408)[0]
        raw[offset] = 255; values['mdl'] = bytes(raw)
        self.refused(values, 'PRINTABLE_ASCII_METADATA_PROFILE')
        values = family(); raw = bytearray(values['mdl']); raw.extend(b'A' * 257)
        struct.pack_into('<i', raw, 408, len(raw) - 257 - 408)
        struct.pack_into('<I', raw, 76, len(raw)); values['mdl'] = bytes(raw)
        self.refused(values, 'UNTERMINATED_OR_OVERLONG_METADATA_STRING')

    def test_duplicate_material_names_remain_distinct_native_records_not_slot_alias_proof(self):
        values = family(); raw = bytearray(values['mdl'])
        first_name = 408 + struct.unpack_from('<i', raw, 408)[0]
        struct.pack_into('<i', raw, 472, first_name - 472); values['mdl'] = bytes(raw)
        meta = self.decode(values)['metadata']
        self.assertEqual([m['name'] for m in meta['materials']], ['test/hair', 'test/hair'])
        self.assertEqual([m['index'] for m in meta['materials']], [0, 1])
        self.assertEqual(meta['skin_families'], [[1, 0], [0, 1]])

    def test_skin_uint16_values_use_material_domain_and_preserve_family_order(self):
        self.refused(changed(family(), 'mdl', 548, '<H', 2), 'SKIN_MATERIAL_INDEX_DOMAIN')
        self.refused(changed(family(), 'mdl', 548, '<H', 65535), 'SKIN_MATERIAL_INDEX_DOMAIN')

    def test_empty_skins_are_allowed_only_with_both_dimensions_zero(self):
        values = changed(family(), 'mdl', 220, '<3I', 0, 0, 0)
        self.assertEqual(self.decode(values)['metadata']['skin_families'], [])
        for refs, families in ((0, 1), (2, 0)):
            self.refused(changed(family(), 'mdl', 220, '<2I', refs, families), 'PARTIAL_EMPTY_SKIN_DIMENSIONS')

    def test_skin_dimensions_and_search_path_table_are_bounded(self):
        self.refused(changed(family(), 'mdl', 224, '<I', 257), 'SKIN_FAMILY_COUNT_BUDGET')
        self.refused(changed(family(), 'mdl', 212, '<I', 257), 'METADATA_TABLE_COUNT_BUDGET')

    def test_mesh_material_index_is_checked_against_texture_count_not_skin_reference_count(self):
        self.refused(changed(family(), 'mdl', 868, '<I', 2), 'MESH_MATERIAL_INDEX_DOMAIN')
        fewer_skin_refs = changed(family(), 'mdl', 220, '<I', 1)
        self.assertEqual(self.decode(fewer_skin_refs)['metadata']['body_parts'][0]['models'][0]['meshes'][0]['material_index'], 1)
        # A different valid material ordinal is preserved, never sorted or repaired.
        values = changed(family(), 'mdl', 868, '<I', 0)
        self.assertEqual(self.decode(values)['metadata']['body_parts'][0]['models'][0]['meshes'][0]['material_index'], 0)

    def test_mesh_vertex_span_cannot_escape_its_mdl_model(self):
        self.refused(changed(family(), 'mdl', 880, '<I', 5), 'MDL_MESH_VERTEX_RANGE')
        self.refused(changed(family(), 'mdl', 876, '<I', 7), 'MDL_MESH_VERTEX_RANGE')

    def test_flexes_eyeballs_and_static_prop_are_outside_this_profile(self):
        self.refused(changed(family(), 'mdl', 884, '<I', 1), 'FLEXES_OUTSIDE_PROFILE')
        self.refused(changed(family(), 'mdl', 672, '<I', 1), 'EYEBALLS_OUTSIDE_PROFILE')
        self.refused(changed(family(), 'mdl', 152, '<I', 0x10), 'STATIC_PROP_OUTSIDE_PROFILE')

    def test_repeated_renderable_model_names_refuse(self):
        values = family(); raw = bytearray(values['mdl']); raw[720:784] = raw[572:636]; values['mdl'] = bytes(raw)
        self.refused(values, 'UNIQUE_RENDERABLE_LOGICAL_NAME')

    def test_vvd_table_overlap_trailing_data_and_model_bounds_refuse(self):
        self.refused(changed(family(), 'vvd', 60, '<I', 64), 'OVERLAPPING_METADATA_TABLES')
        values = family(); values['vvd'] += b'unknown'
        self.refused(values, 'VVD_TRAILING_OR_EXTRA_UV_PROFILE')
        self.refused(changed(family(), 'mdl', 804, '<I', 432), 'MODEL_VVD_RANGE_OR_BYTE_ALIGNMENT')

    def test_vtx_replacement_lod_and_body_model_mesh_counts_are_separate_domains(self):
        for offset, fmt, value, code in (
            (36, '<i', 1, 'VTX_MATERIAL_REPLACEMENTS_OUTSIDE_PROFILE'),
            (20, '<I', 2, 'STANDARD_VTX7_THREE_SLOT_ONE_LOD_PROFILE'),
            (28, '<I', 2, 'VTX_MDL_BODY_PART_COUNT'),
            (44, '<I', 1, 'VTX_MDL_MODEL_COUNT'),
            (52, '<i', 2, 'VTX_MODEL_LOD_COUNT'),
            (68, '<I', 1, 'VTX_MDL_MESH_COUNT_OR_SWITCH'),
            (76, '<f', float('nan'), 'VTX_MDL_MESH_COUNT_OR_SWITCH')):
            self.refused(changed(family(), 'vtx', offset, fmt, value), code)

    def test_vtx_metadata_table_may_not_alias_replacement_list(self):
        self.refused(changed(family(), 'vtx', 32, '<I', 36), 'OVERLAPPING_METADATA_TABLES')

    def test_decoding_does_not_mutate_or_retain_caller_descriptor_containers(self):
        refs = descriptors(family()); before = copy.deepcopy(refs)
        result = oracle.derive_material_metadata(refs)
        self.assertEqual(refs, before)
        refs['mdl']['sha256'] = '0' * 64
        self.assertEqual(result['source_identities']['mdl']['sha256'], before['mdl']['sha256'])


if __name__ == '__main__':
    unittest.main()

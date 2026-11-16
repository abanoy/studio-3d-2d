"""CPU-only necessary metadata gates for the first bounded Source native route.

This does not resolve a live skeleton, open a GLB, authorize native execution,
or replace SourceBindings.resolve/current. Generic route means the existing
generic-secondary behavior remains responsible for the model.
"""
import hashlib
import json
import math
import struct

MDL = '8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716'
GLB = '4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d'
SOURCEIO = 'fe24260b97ac03b899d9b5d4f0fd7b34772f3647'
PROFILE = 'junko_hair_mdl49_fe242_blender51_1'
WIRE = '34230c89c7cda4417a0f142b375f26fbb5cf15a7faf4d98b5424acd0bec621c2'
PREFIX8 = '945d7fd433ddba7f7e8f90cb1cb2c2e7d4c1e26005684ac4a330b23a3691a3fd'
ACTIVE8 = {'length': 20.0, 'tip_mass': 20.0, 'yaw_stiffness': 100.0,
           'yaw_damping': 5.0, 'pitch_stiffness': 100.0, 'pitch_damping': 5.0,
           'angle_limit': 0.7853981852531433, 'along_stiffness': 100.0,
           'along_damping': 0.0}
FIELDS = ['length', 'tip_mass', 'yaw_stiffness', 'yaw_damping', 'pitch_stiffness',
          'pitch_damping', 'along_stiffness', 'along_damping', 'angle_limit',
          'min_yaw', 'max_yaw', 'yaw_friction', 'yaw_bounce', 'min_pitch',
          'max_pitch', 'pitch_friction', 'pitch_bounce', 'base_mass',
          'base_stiffness', 'base_damping', 'base_min_left', 'base_max_left',
          'base_left_friction', 'base_min_up', 'base_max_up', 'base_up_friction',
          'base_min_forward', 'base_max_forward', 'base_forward_friction']


def number(value, target):
    return type(value) in (int, float) and math.isfinite(value) and value == target


def false(value):
    return type(value) is bool and value is False


def sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def whole(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and value == int(value) and low <= value <= high


def generic(reason):
    return {'route': 'generic', 'reason': reason, 'native_metadata_modified': False,
            'full_native_rule_layout_verified': False, 'runtime_admission_proven': False}


def route(report, binding_summary, selected_native=(8,), generic_override=False):
    # Explicit custom/manual secondary setup wins; importing metadata does not
    # override an artist's established helper behavior.
    if generic_override:
        return generic('explicit_generic_override')
    if type(report) is not dict:
        return generic('no_qualified_native_report')
    if selected_native != (8,) or any(type(value) is not int for value in selected_native):
        return generic('only_native8_leaf_proven')
    if report.get('source_sha256') != MDL or report.get('sourceio_revision') != SOURCEIO or not number(report.get('scale'), .01905):
        return generic('source_identity_or_conversion_scale')
    native = report.get('native_parameters')
    if type(native) is not dict:
        return generic('native_metadata')
    bones = native.get('bones')
    jiggle = native.get('source_jiggle')
    cross = native.get('source_export_crosswalk')
    if type(bones) is not list or len(bones) != 69 or type(jiggle) is not dict or type(cross) is not dict:
        return generic('native69_rule49_shape')
    if cross.get('format') != 'studio_source_bone_crosswalk_1' or cross.get('status') != 'retained_inert' or cross.get('profile') != PROFILE:
        return generic('crosswalk_profile')
    if (not false(cross.get('applied')) or cross.get('native_solver') != 'not_implemented' or
            cross.get('sourceio_revision') != SOURCEIO or cross.get('original_source_sha256') != MDL or
            cross.get('native_mdl_sha256') != MDL or cross.get('glb_sha256') != GLB or
            cross.get('jiggle_wire_sha256') != WIRE or not number(cross.get('source_scale'), .01905) or
            not number(cross.get('native_bone_count'), 69) or not sha(cross.get('proof_sha256'))):
        return generic('crosswalk_identity_or_inert_contract')
    if (jiggle.get('format') != 'studio_source_jiggle_metadata_1' or jiggle.get('status') != 'retained_inert' or
            not false(jiggle.get('applied')) or not false(jiggle.get('full_native_rule_layout_verified')) or
            jiggle.get('runtime_support') != 'not_implemented' or jiggle.get('binding_status') != 'unattempted' or
            jiggle.get('native_mdl_sha256') != MDL or jiggle.get('sourceio_revision') != SOURCEIO or
            not number(jiggle.get('native_version'), 49) or not number(jiggle.get('native_bone_count'), 69) or
            not number(jiggle.get('declared_jiggle_rule_count'), 49) or not number(jiggle.get('source_scale'), .01905)):
        return generic('native_inert_contract')
    rules = jiggle.get('rules')
    if type(rules) is not list or len(rules) != 49:
        return generic('rule_count')
    names = set()
    for index, row in enumerate(bones):
        if (type(row) is not dict or set(row) != {'name', 'parent'} or
                not isinstance(row['name'], str) or not row['name'] or row['name'] in names or
                type(row['parent']) not in (int, float) or not math.isfinite(row['parent']) or
                row['parent'] != int(row['parent']) or row['parent'] < -1 or row['parent'] >= 69 or row['parent'] == index):
            return generic('bone_catalogue')
        names.add(row['name'])
    for index in range(69):
        seen = set()
        while index >= 0:
            if index in seen:
                return generic('bone_parent_cycle')
            seen.add(index)
            index = int(bones[index]['parent'])
    if bones[8] != {'name': 'FrontHair1', 'parent': 7} or any(row['parent'] == 8 for row in bones):
        return generic('native8_leaf_topology')
    catalogue_hash = hashlib.sha256((json.dumps(bones, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')).hexdigest()
    if cross.get('native_bone_catalogue_sha256') != catalogue_hash or jiggle.get('native_bone_catalogue_sha256') != catalogue_hash:
        return generic('catalogue_digest')
    owners = set()
    leaf = None
    for row in rules:
        if type(row) is not dict or type(row.get('native_bone_index')) not in (int, float):
            return generic('rule_owner')
        owner = row['native_bone_index']
        if not math.isfinite(owner) or owner != int(owner) or not 0 <= owner < 69 or owner in owners:
            return generic('rule_owner')
        owner = int(owner)
        owners.add(owner)
        if (row.get('native_bone_name') != bones[owner]['name'] or not number(row.get('native_parent_index'), bones[owner]['parent']) or
                not number(row.get('native_procedure_type'), 5) or not number(row.get('raw_rule_flags'), 0x31) or
                not whole(row.get('native_bone_flags'), 0, 0xffffffff) or
                not number(row.get('unknown_rule_flag_bits'), 0) or
                row.get('known_rule_flags') != ['IS_FLEXIBLE', 'HAS_ANGLE_CONSTRAINT', 'HAS_LENGTH_CONSTRAINT'] or
                not false(row.get('applied')) or row.get('binding_status') != 'unattempted'):
            return generic('rule_contract')
        if owner == 8:
            leaf = row
    wire = 'studio_source_jiggle_binding_1\nnative_mdl_sha256=' + MDL + '\nnative_bone_count=69\nrule_count=49\n'
    for row in sorted(rules, key=lambda item: item['native_bone_index']):
        parameters = row.get('parameters')
        provenance = row.get('binary_provenance')
        if type(parameters) is not dict or set(parameters) != set(FIELDS) or type(provenance) is not dict:
            return generic('parameter_fields_or_provenance')
        words = provenance.get('float32_words_uint32')
        if type(words) is not list or len(words) != 29 or not number(provenance.get('prefix_bytes'), 120):
            return generic('binary_prefix_shape')
        for field in ['bone_record_offset', 'bone_relative_rule_offset', 'rule_absolute_offset']:
            if not whole(provenance.get(field), 0, 16 * 1024 * 1024):
                return generic('binary_offsets')
        if provenance['bone_record_offset'] + provenance['bone_relative_rule_offset'] != provenance['rule_absolute_offset']:
            return generic('binary_offsets')
        for field, word in zip(FIELDS, words):
            value = parameters[field]
            if not whole(word, 0, 0xffffffff) or type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e6:
                return generic('float32_word')
            reconstructed = struct.unpack('<I', struct.pack('<f', value))[0]
            if reconstructed != word and not (value == 0 and word in (0, 0x80000000)):
                return generic('float32_word')
        prefix = struct.pack('<I29I', 49, *map(int, words))
        if hashlib.sha256(prefix).hexdigest() != provenance.get('prefix_sha256'):
            return generic('prefix_digest')
        wire += 'rule=%d\t%d\t%s\t%d\t5\t49\t%s\n' % (row['native_bone_index'], row['native_parent_index'], row['native_bone_name'], row['native_bone_flags'], provenance['prefix_sha256'])
        wire += 'words=' + '\t'.join(str(int(word)) for word in words) + '\n'
    if hashlib.sha256(wire.encode('ascii')).hexdigest() != WIRE:
        return generic('authenticated_rule_wire')
    if leaf is None or type(leaf.get('parameters')) is not dict or type(leaf.get('binary_provenance')) is not dict:
        return generic('leaf_parameters')
    if leaf['binary_provenance'].get('prefix_sha256') != PREFIX8 or any(not number(leaf['parameters'].get(k), v) for k, v in ACTIVE8.items()):
        return generic('exact_measured_leaf_parameters')
    # This summary is an assertion from an upstream live resolver, not something
    # this CPU module can establish. The production consumer must create it from
    # actual SourceBindings and guarded import context, never serialized metadata.
    if type(binding_summary) is not dict or binding_summary.get('status') != 'bound_inactive':
        return generic('live_binding_required')
    if (binding_summary.get('source_sha256') != GLB or binding_summary.get('jiggle_wire_sha256') != WIRE or
            not number(binding_summary.get('bindings'), 69) or not number(binding_summary.get('rule_owner_ids'), 49) or
            binding_summary.get('selected_native8_is_leaf') is not True or
            binding_summary.get('import_context_current') is not True):
        return generic('live_binding_context')
    return {'route': 'eligible_for_native8_live_checks', 'native_ids': [8],
            'retained_unactivated_rules': 48, 'native_metadata_modified': False,
            'full_native_rule_layout_verified': False, 'runtime_admission_proven': False,
            'remaining_live_checks': ['actual current skeleton and immutable imported rest',
                                     'positive uniform non-reflected world frame',
                                     'no active conflicting bone owner',
                                     'per-actor sequential fixed-tick state and restore ownership']}

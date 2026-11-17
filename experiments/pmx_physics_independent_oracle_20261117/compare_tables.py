"""Exact typed candidate/witness comparison, no parser invocation or file IO.

Only this adapter knows the candidate's capsule field names. The independent
oracle has its own schema and does not import this adapter or the candidate.
"""
import json
import re


class Disagreement(ValueError):
    pass


def insist(ok, field):
    if not ok:
        # Fixed schema paths only; never include a private source value/name.
        raise Disagreement('declaration disagreement: ' + field)


def keys(value, expected, field):
    insist(type(value) is dict and set(value) == set(expected), field + '.fields')


def exact(actual, expected, field):
    insist(type(actual) is type(expected), field + '.type')
    if type(expected) is dict:
        insist(actual.keys() == expected.keys(), field + '.fields')
        for key in expected: exact(actual[key], expected[key], field + '.' + key)
    elif type(expected) is list:
        insist(len(actual) == len(expected), field + '.length')
        for i, (a, b) in enumerate(zip(actual, expected)): exact(a, b, field + '[' + str(i) + ']')
    else:
        insist(actual == expected, field + '.value')


def integer(value, field, minimum=0):
    insist(type(value) is int and value >= minimum, field + '.integer')


def token(value, field):
    keys(value, ('start', 'number', 'hex', 'width', 'signed'), field)
    integer(value['start'], field + '.start')
    insist(type(value['width']) is int and value['width'] in (1, 2, 4), field + '.width')
    insist(type(value['signed']) is bool and type(value['number']) is int, field + '.number')
    insist(type(value['hex']) is str and re.fullmatch('[a-f0-9]{' + str(value['width'] * 2) + '}', value['hex']), field + '.hex')
    insist(int.from_bytes(bytes.fromhex(value['hex']), 'little', signed=value['signed']) == value['number'], field + '.raw_integer')
    return value


def name(value, field):
    keys(value, ('length_field', 'payload_start', 'byte_count', 'encoding', 'encoded', 'decoded'), field)
    for key in ('length_field', 'payload_start', 'byte_count'): integer(value[key], field + '.' + key)
    insist(value['payload_start'] == value['length_field'] + 4, field + '.payload_start')
    insist(value['encoding'] in ('utf-8', 'utf-16-le') and type(value['encoded']) is str
           and re.fullmatch('[a-f0-9]*', value['encoded']) and len(value['encoded']) == 2 * value['byte_count'], field + '.encoded')
    try:
        decoded = bytes.fromhex(value['encoded']).decode(value['encoding'], errors='strict')
    except (ValueError, UnicodeError) as error:
        raise Disagreement('declaration disagreement: ' + field + '.encoding') from error
    insist(type(value['decoded']) is str and decoded == value['decoded'], field + '.decoded')
    return {'text': value['decoded'], 'raw_hex': value['encoded'], 'offset': value['length_field'],
            'payload_offset': value['payload_start'], 'bytes': value['byte_count'], 'encoding': value['encoding']}


def floats(value, count, field):
    keys(value, ('start', 'word_hex', 'nonfinite_offsets'), field)
    integer(value['start'], field + '.start')
    words = value['word_hex']
    insist(type(words) is list and len(words) == count and all(type(w) is str and re.fullmatch('[a-f0-9]{8}', w) for w in words), field + '.words')
    # A separate unsigned-word exponent test checks the witness classification.
    exceptional = [i for i, word in enumerate(words)
                   if ((int.from_bytes(bytes.fromhex(word), 'little') >> 23) & 255) == 255]
    exact(value['nonfinite_offsets'], [value['start'] + 4 * i for i in exceptional], field + '.nonfinite')
    return {'offset': value['start'], 'words_le_hex': words, 'nonfinite_word_indices': exceptional}


def reference(value, field):
    token(value, field)
    return {'value': value['number'], 'word_le_hex': value['hex'], 'offset': value['start'],
            'width': value['width'], 'signed': value['signed']}


def scalar(value, field, word=False):
    token(value, field)
    result = {'offset': value['start'], 'value': value['number']}
    if word: result['word_le_hex'] = value['hex']
    return result


def span(value, field):
    insist(type(value) is list and len(value) == 2, field + '.span')
    for item in value: integer(item, field + '.span')
    insist(value[0] <= value[1], field + '.span_order')


def bone(row):
    field = 'bone'
    integer(row['index'], field + '.index')
    flags = token(row['flags'], field + '.flags')['number']
    expected = {'index', 'names', 'position', 'parent', 'layer', 'flags', 'tail', 'span'}
    for bit, key in ((0x300, 'inherit'), (0x400, 'fixed_direction'), (0x800, 'local_directions'),
                     (0x2000, 'external_transform'), (0x20, 'ik')):
        if flags & bit: expected.add(key)
    keys(row, expected, field); span(row['span'], field)
    insist(type(row['names']) is list and len(row['names']) == 2, field + '.names')
    result = {'native_index': row['index'], 'offset': row['span'][0], 'end_offset': row['span'][1],
              'name': name(row['names'][0], field + '.name'), 'name_e': name(row['names'][1], field + '.name_e'),
              'location': floats(row['position'], 3, field + '.position'), 'parent': reference(row['parent'], field + '.parent'),
              'transform_layer': scalar(row['layer'], field + '.layer', True), 'flags': scalar(row['flags'], field + '.flags', True)}
    if flags & 1:
        keys(row['tail'], ('bone',), field + '.tail'); result['tail_bone'] = reference(row['tail']['bone'], field + '.tail')
    else:
        keys(row['tail'], ('offset_words',), field + '.tail'); result['tail_offset'] = floats(row['tail']['offset_words'], 3, field + '.tail')
    if flags & 0x300:
        keys(row['inherit'], ('parent', 'factor'), field + '.inherit')
        result['grant'] = {'source': reference(row['inherit']['parent'], field + '.grant'), 'influence': floats(row['inherit']['factor'], 1, field + '.influence')}
    if flags & 0x400: result['fixed_axis'] = floats(row['fixed_direction'], 3, field + '.fixed_axis')
    if flags & 0x800: result['local_axes'] = floats(row['local_directions'], 6, field + '.local_axes')
    if flags & 0x2000: result['external_parent_key'] = scalar(row['external_transform'], field + '.external', True)
    if flags & 0x20:
        ik = row['ik']; keys(ik, ('target', 'iterations', 'step_angle', 'links'), field + '.ik')
        insist(type(ik['links']) is list, field + '.ik.links')
        links = []
        for link in ik['links']:
            limited = token(link['limited'], field + '.ik.limited')['number']
            insist(limited in (0, 1), field + '.ik.limited')
            keys(link, ('bone', 'limited', 'limits') if limited else ('bone', 'limited'), field + '.ik.link')
            target = {'bone': reference(link['bone'], field + '.ik.link.bone'), 'limited': scalar(link['limited'], field + '.ik.limited')}
            if limited: target['angle_bounds'] = floats(link['limits'], 6, field + '.ik.limits')
            links.append(target)
        result['ik'] = {'target': reference(ik['target'], field + '.ik.target'), 'iterations': scalar(ik['iterations'], field + '.ik.iterations', True),
                        'limit': floats(ik['step_angle'], 1, field + '.ik.step'), 'links': links}
    return result


def physics(row, joint=False):
    field = 'joint' if joint else 'body'
    required = {'index', 'names', 'mode', 'parameters', 'span'} | ({'body_a', 'body_b'} if joint else {'bone', 'group', 'mask', 'shape'})
    keys(row, required, field); span(row['span'], field); integer(row['index'], field + '.index')
    insist(type(row['names']) is list and len(row['names']) == 2, field + '.names')
    result = {'native_index': row['index'], 'offset': row['span'][0], 'end_offset': row['span'][1],
              'name': name(row['names'][0], field + '.name'), 'name_e': name(row['names'][1], field + '.name_e'),
              'mode': scalar(row['mode'], field + '.mode'), 'values': floats(row['parameters'], 24 if joint else 14, field + '.parameters')}
    if joint:
        result.update(source=reference(row['body_a'], field + '.body_a'), destination=reference(row['body_b'], field + '.body_b'))
    else:
        result.update(bone=reference(row['bone'], field + '.bone'), collision_group=scalar(row['group'], field + '.group'),
                      collision_mask=scalar(row['mask'], field + '.mask', True), shape=scalar(row['shape'], field + '.shape'))
    return result


def _compare(capsule, witness):
    """Compare all captured declarations; return a data-free unqualified result."""
    keys(witness, ('format', 'native_qualified', 'physical_validity_or_simulation', 'source', 'header',
                   'model_names', 'ranges', 'records', 'scope', 'work_units', 'string_bytes'), 'witness')
    insist(witness['format'] == 'has_independent_pmx20_table_witness_prototype_1'
           and witness['native_qualified'] is False and witness['physical_validity_or_simulation'] is False,
           'witness.unqualified_profile')
    keys(witness['source'], ('sha256', 'bytes'), 'witness.source')
    integer(witness['source']['bytes'], 'witness.source.bytes', 1)
    insist(type(witness['source']['sha256']) is str and re.fullmatch('[a-f0-9]{64}', witness['source']['sha256']), 'witness.source.sha256')
    integer(witness['work_units'], 'witness.work_units'); integer(witness['string_bytes'], 'witness.string_bytes')
    insist(witness['scope'] == 'OPAQUE_BONE_AND_PHYSICS_WORDS_WITH_RESTRICTED_PREFIX_LAYOUT_ONLY', 'witness.scope')
    keys(capsule, ('format', 'qualification', 'source_sha256', 'source_bytes', 'header', 'model_names',
                   'rigid_f32_layout', 'joint_f32_layout', 'sections', 'bones', 'rigid_bodies', 'joints',
                   'prefix_reference_policy', 'f32_policy', 'geometry_policy', 'budgets'), 'candidate')
    insist(capsule['format'] == 'has_pmx20_native_physics_capsule_prototype_1'
           and capsule['qualification'] == 'UNQUALIFIED_SOURCE_CPU_ONLY', 'candidate.unqualified_profile')
    exact(capsule['source_sha256'], witness['source']['sha256'], 'source.sha256')
    exact(capsule['source_bytes'], witness['source']['bytes'], 'source.bytes')
    h = witness['header']; keys(h, ('version', 'globals', 'codec', 'encoding_selector', 'extra_uv_vectors', 'reference_widths'), 'witness.header')
    aliases = {'vertex': 'vertices', 'texture': 'textures', 'material': 'materials', 'bone': 'bones', 'morph': 'morphs', 'body': 'rigid_bodies'}
    keys(h['reference_widths'], aliases, 'witness.widths')
    insist(h['version'] == '00000040' and type(h['encoding_selector']) is int and h['encoding_selector'] in (0, 1)
           and type(h['extra_uv_vectors']) is int and 0 <= h['extra_uv_vectors'] <= 4
           and h['codec'] == ('utf-16-le', 'utf-8')[h['encoding_selector']], 'witness.header_profile')
    insist(all(type(v) is int and v in (1, 2, 4) for v in h['reference_widths'].values()), 'witness.width_types')
    expected_globals = bytes([h['encoding_selector'], h['extra_uv_vectors']]
                             + [h['reference_widths'][key] for key in aliases]).hex()
    insist(h['globals'] == expected_globals, 'witness.raw_globals')
    expected_header = {'version_word_le_hex': h['version'], 'encoding': h['codec'], 'encoding_byte': h['encoding_selector'],
                       'global_bytes_le_hex': h['globals'], 'additional_uv': h['extra_uv_vectors'],
                       'index_widths': {aliases[k]: v for k, v in h['reference_widths'].items()}}
    exact(capsule['header'], expected_header, 'header')
    insist(type(witness['model_names']) is list and len(witness['model_names']) == 2, 'witness.model_names')
    exact(capsule['model_names'], [name(n, 'model_name') for n in witness['model_names']], 'model_names')
    section_names = ('vertices', 'face_indices', 'textures', 'materials', 'bones', 'morphs', 'displays', 'rigid_bodies', 'joints')
    order = ('vertex', 'index', 'texture', 'material', 'bone', 'morph', 'display', 'body', 'joint')
    insist(type(witness['ranges']) is list and len(witness['ranges']) == len(order), 'witness.ranges')
    sections = {}
    previous_end = None
    for row, own, target in zip(witness['ranges'], order, section_names):
        keys(row, ('kind', 'quantity', 'count_token', 'payload_start', 'payload_end'), 'witness.range')
        insist(row['kind'] == own, 'witness.range_order'); t = token(row['count_token'], 'witness.count')
        integer(row['quantity'], 'witness.quantity'); integer(row['payload_start'], 'witness.payload_start'); integer(row['payload_end'], 'witness.payload_end')
        insist(t['width'] == 4 and t['signed'] is True and row['payload_start'] == t['start'] + 4
               and row['payload_start'] <= row['payload_end'] <= witness['source']['bytes'], 'witness.range_span')
        if previous_end is not None: insist(t['start'] == previous_end, 'witness.range_contiguity')
        previous_end = row['payload_end']
        exact(row['quantity'], t['number'], 'witness.count_quantity')
        sections[target] = {'count': row['quantity'], 'count_offset': t['start'], 'count_word_le_hex': t['hex'],
                            'data_offset': row['payload_start'], 'end_offset': row['payload_end']}
    exact(capsule['sections'], sections, 'sections')
    insist(previous_end == witness['source']['bytes'], 'witness.EOF')
    keys(witness['records'], ('bone', 'body', 'joint'), 'witness.records')
    for category, section in (('bone', 'bones'), ('body', 'rigid_bodies'), ('joint', 'joints')):
        rows = witness['records'][category]
        insist(type(rows) is list and len(rows) == sections[section]['count'], 'witness.record_count')
        insist(all(type(row.get('index')) is int and row['index'] == i for i, row in enumerate(rows)), 'witness.native_index_order')
    exact(capsule['bones'], [bone(row) for row in witness['records']['bone']], 'bones')
    exact(capsule['rigid_bodies'], [physics(row) for row in witness['records']['body']], 'rigid_bodies')
    exact(capsule['joints'], [physics(row, True) for row in witness['records']['joint']], 'joints')
    for key, layout in (('rigid_f32_layout', [('size', 3), ('location', 3), ('rotation', 3), ('mass', 1),
                                           ('velocity_attenuation', 1), ('rotation_attenuation', 1), ('bounce', 1), ('friction', 1)]),
                        ('joint_f32_layout', [(n, 3) for n in ('location', 'rotation', 'minimum_location', 'maximum_location',
                                                             'minimum_rotation', 'maximum_rotation', 'linear_spring', 'angular_spring')])):
        expected = []; position = 0
        for field, length in layout:
            expected.append({'name': field, 'word_offset': position, 'words': length}); position += length
        exact(capsule[key], expected, key)
    for key in ('prefix_reference_policy', 'f32_policy', 'geometry_policy'):
        insist(type(capsule[key]) is str and len(capsule[key].encode('utf-8')) <= 1024, 'candidate.policy_metadata')
    keys(capsule['budgets'], ('operations_used', 'conservative_metadata_bytes_reserved', 'string_bytes_used', 'limits'), 'candidate.budgets')
    for key in ('operations_used', 'conservative_metadata_bytes_reserved', 'string_bytes_used'):
        integer(capsule['budgets'][key], 'candidate.budget')
    keys(capsule['budgets']['limits'], ('source_bytes', 'string_bytes', 'total_string_bytes', 'retained_name_utf8_bytes',
         'vertices', 'face_indices', 'textures', 'materials', 'bones', 'morphs', 'morph_offsets', 'displays',
         'display_elements', 'ik_links', 'rigid_bodies', 'joints', 'operations', 'metadata_bytes'), 'candidate.limits')
    insist(all(type(k) is str and type(v) is int and v >= 0
           for k, v in capsule['budgets']['limits'].items()), 'candidate.limit_metadata')
    return {'format': 'has_exact_independent_pmx_declaration_comparison_prototype_1',
            'status': 'EXACT_CAPTURED_DECLARATIONS_AGREE_SYNTHETIC_SOURCE_ONLY',
            'candidate_unqualified_flag_preserved': True, 'native_qualified': False,
            'physical_validity_simulation_portability_or_adoption': False}


def compare(capsule, witness):
    try:
        for value, cap in ((capsule, 2 * 1024 * 1024), (witness, 8 * 1024 * 1024)):
            insist(len(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')) <= cap, 'complete_comparison_input_budget')
        return _compare(capsule, witness)
    except Disagreement:
        raise
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, UnicodeError, RecursionError) as error:
        raise Disagreement('declaration disagreement: typed_schema') from error


def _pairs(rows):
    result = {}
    for key, value in rows:
        insist(key not in result, 'duplicate_JSON_key'); result[key] = value
    return result


def compare_json(candidate_raw, witness_raw):
    inputs = []
    for raw, cap in ((candidate_raw, 2 * 1024 * 1024), (witness_raw, 8 * 1024 * 1024)):
        insist(type(raw) is bytes and len(raw) <= cap, 'bounded_immutable_JSON')
        try:
            inputs.append(json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                                     parse_constant=lambda _v: insist(False, 'nonfinite_JSON')))
        except (ValueError, UnicodeError, RecursionError) as error:
            raise Disagreement('declaration disagreement: strict_JSON') from error
    return compare(*inputs)

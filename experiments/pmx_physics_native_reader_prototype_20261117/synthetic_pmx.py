"""Independent authored PMX2.0 prefix/physics fixtures; no parser or native input.

The expected offsets come from construction and separate record-size equations.
No installed MMD module is imported. Physics words deliberately include NaN/Inf:
this is a byte-provenance oracle, never a physical/model-validity assertion.
"""
import hashlib
import struct


_ZERO = '00000000'
_NEG_ZERO = '00000080'
_ONE = '0000803f'
_HALF = '0000003f'
_QUARTER = '0000803e'
_BODY_WORDS = (
    '0000803f', '00000040', '00004040',  # size
    '00000080', '01000000', '000080bf',  # location: -0, subnormal, -1
    '00000000', '0000803e', '0000003f',  # rotation
    '0000803f', '0000803e', '0000003f', '0000003e', '4523c17f',
)
_JOINT_WORDS = (
    '0000803f', '00000040', '00004040',
    '00000080', '0000803e', '000000bf',
    '000080bf', '000000c0', '000040c0',
    '0000803f', '00000040', '00004040',
    '000080be', '000000bf', '000040bf',
    '0000803e', '0000003f', '0000403f',
    '00000040', '00008040', '00000041',
    '00008041', '01000000', '0000807f',  # subnormal, +Inf
)


def _int(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Invalid fixture integer: ' + name)
    return value


def _words(values):
    """Author finite prefix constants, not decode any source float."""
    return tuple(struct.pack('<f', float(value)).hex() for value in values)


class _Writer:
    def __init__(self, size, encoding):
        self.data = bytearray()
        self.size = size
        self.encoding = 'utf-8' if encoding else 'utf-16-le'
        self.fields = {}

    def put(self, name, payload, value=None):
        if name in self.fields:
            raise AssertionError('Duplicate fixture field: ' + name)
        begin = len(self.data)
        self.data.extend(payload)
        row = {'offset': begin, 'end': len(self.data), 'bytes': len(payload), 'hex': payload.hex()}
        if value is not None:
            row['value'] = value
        self.fields[name] = row
        return row

    def count(self, name, value):
        return self.put(name, struct.pack('<i', value), value)

    def byte(self, name, value, signed=False):
        return self.put(name, struct.pack('<b' if signed else '<B', value), value)

    def index(self, name, value, vertex=False):
        code = {1: 'B', 2: 'H', 4: 'I'}[self.size] if vertex else {1: 'b', 2: 'h', 4: 'i'}[self.size]
        return self.put(name, struct.pack('<' + code, value), value)

    def text(self, name, value):
        encoded = value.encode(self.encoding, errors='strict')
        start = len(self.data)
        self.count(name + '.length', len(encoded))
        self.put(name + '.data', encoded, value)
        return {'offset': start, 'end': len(self.data), 'decoded': value, 'encoding': self.encoding,
                'raw_hex': encoded.hex()}

    def floats(self, name, words):
        words = tuple(words)
        if any(type(word) is not str or len(word) != 8 for word in words):
            raise ValueError('Fixture words must be four-byte LE hex')
        row = self.put(name, bytes.fromhex(''.join(words)))
        row['words_le_hex'] = list(words)
        return row


def build_fixture(index_size=1, encoding=1, additional_uv=0, deform=0,
                  tail_bone=True, bone_flags=0, morph_types=(0, 1, 2, 3, 4, 5, 6, 7, 8),
                  bone_ref=-1, rigid_ref=-1, joint_mode=0, vertex_count=3):
    """Return authored bytes and JSON-safe expectations independent of the reader.

    All six index widths use index_size. bone_flags/tail_bone control bone0;
    bone1 is a simple offset-tail child. Both names deliberately collide.
    The two materials always exercise both shared and unshared toon branches.
    Out-of-domain physics refs/joint modes can be authored within their binary
    word range for negative tests; expected does not call those valid.
    """
    if type(index_size) is not int or index_size not in (1, 2, 4):
        raise ValueError('Fixture index width must be 1, 2 or 4')
    _int(encoding, 0, 1, 'encoding')
    _int(additional_uv, 0, 4, 'additional_uv')
    _int(deform, 0, 3, 'deform')
    _int(bone_flags, 0, 65535, 'bone_flags')
    _int(joint_mode, -128, 127, 'joint_mode')
    _int(vertex_count, 3, min(1024, 1 << (8 * index_size)), 'vertex_count')
    if type(tail_bone) is not bool:
        raise ValueError('Fixture tail selector must be bool')
    if type(morph_types) not in (tuple, list) or len(morph_types) > 64:
        raise ValueError('Bounded authored morph list required')
    for kind in morph_types:
        _int(kind, 0, 8, 'morph_type')
    low, high = -(1 << (8 * index_size - 1)), (1 << (8 * index_size - 1)) - 1
    _int(bone_ref, low, high, 'bone_ref')
    _int(rigid_ref, low, high, 'rigid_ref')
    flags = (bone_flags | 1) if tail_bone else (bone_flags & ~1)
    w = _Writer(index_size, encoding)
    sections = {}
    w.put('header', b'PMX ' + bytes.fromhex('00000040') + bytes([8, encoding, additional_uv] + [index_size] * 6))
    assert len(w.data) == 17
    for key, value in [('model.name', 'HAS authored prefix'), ('model.name_e', 'Synthetic'),
                       ('model.comment', 'No native asset or solver claim'), ('model.comment_e', '')]:
        w.text(key, value)

    sections['vertices'] = len(w.data)
    w.count('vertices.count', vertex_count)
    vertices = []
    positions = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
    uvs = ((0, 0), (1, 0), (0, 1))
    for i in range(vertex_count):
        position, uv = positions[i % 3], uvs[i % 3]
        prefix = 'vertex.' + str(i)
        start = len(w.data)
        w.floats(prefix + '.position', _words(position))
        w.floats(prefix + '.normal', (_ZERO, _ZERO, _ONE))
        w.floats(prefix + '.uv', _words(uv))
        for layer in range(additional_uv):
            w.floats(prefix + '.additional_uv.' + str(layer), _words(((layer + 1) / 8, 0, 0, 1)))
        tag = w.byte(prefix + '.deform', deform)
        if deform == 0:
            w.index(prefix + '.bone0', 0)
        elif deform in (1, 3):
            w.index(prefix + '.bone0', 0); w.index(prefix + '.bone1', 1)
            w.floats(prefix + '.weight', (_HALF,))
            if deform == 3:
                for part, values in [('C', (0, .125, 0)), ('R0', (.25, 0, 0)), ('R1', (0, 0, .5))]:
                    w.floats(prefix + '.' + part, _words(values))
        else:
            for j, value in enumerate((0, 1, 0, 1)):
                w.index(prefix + '.bone' + str(j), value)
            w.floats(prefix + '.weights', (_QUARTER,) * 4)
        w.floats(prefix + '.edge_scale', (_ONE,))
        payload_size = {0: index_size, 1: 2 * index_size + 4,
                        2: 4 * index_size + 16, 3: 2 * index_size + 40}[deform]
        assert len(w.data) - start == 32 + 16 * additional_uv + 1 + payload_size + 4
        vertices.append({'offset': start, 'end': len(w.data), 'deform_offset': tag['offset']})

    sections['indices'] = len(w.data)
    w.count('indices.count', 3)
    face_indices = (0, 1, vertex_count - 1)
    for i, vertex_index in enumerate(face_indices):
        w.index('index.' + str(i), vertex_index, vertex=True)
    sections['textures'] = len(w.data)
    w.count('textures.count', 1); w.text('texture.0', 'fixture.png')

    sections['materials'] = len(w.data)
    w.count('materials.count', 2)
    materials = []
    for i, shared in enumerate((1, 0)):
        prefix = 'material.' + str(i); start = len(w.data)
        a = w.text(prefix + '.name', '材質' + str(i)); b = w.text(prefix + '.name_e', 'Material' + str(i))
        fixed = len(w.data)
        w.floats(prefix + '.diffuse', _words((.5, .75, 1, 1)))
        w.floats(prefix + '.specular', _words((0, .125, .25)))
        w.floats(prefix + '.shininess', _words((2,)))
        w.floats(prefix + '.ambient', _words((.125, .25, .5)))
        w.byte(prefix + '.flags', 31)
        w.floats(prefix + '.edge_color', _words((0, 0, 0, 1)))
        w.floats(prefix + '.edge_size', (_ONE,))
        w.index(prefix + '.texture', 0); w.index(prefix + '.sphere_texture', -1)
        w.byte(prefix + '.sphere_mode', 0, signed=True)
        toon_flag = w.byte(prefix + '.shared_toon', shared, signed=True)
        if shared:
            w.byte(prefix + '.toon', 9, signed=True)
        else:
            w.index(prefix + '.toon', 0)
        assert len(w.data) - fixed == 67 + 2 * index_size + (1 if shared else index_size)
        comment = w.text(prefix + '.comment', '')
        w.count(prefix + '.surface_indices', 3 if i == 0 else 0)
        assert len(w.data) - start == (a['end'] - a['offset']) + (b['end'] - b['offset']) + 67 + 2 * index_size + (1 if shared else index_size) + (comment['end'] - comment['offset']) + 4
        materials.append({'offset': start, 'end': len(w.data), 'shared_toon': shared,
                          'shared_toon_flag_offset': toon_flag['offset']})

    sections['bones'] = len(w.data)
    w.count('bones.count', 2)
    bones = []
    for i, actual_flags in enumerate((flags, 0)):
        prefix = 'bone.' + str(i); start = len(w.data)
        name = w.text(prefix + '.name', '髪'); english = w.text(prefix + '.name_e', 'Hair')
        fixed = len(w.data)
        w.floats(prefix + '.location', (_ZERO, _NEG_ZERO, _ONE) if i == 0 else (_ZERO, _ONE, _ZERO))
        w.index(prefix + '.parent', -1 if i == 0 else 0); w.count(prefix + '.layer', i)
        flag_row = w.put(prefix + '.flags', struct.pack('<H', actual_flags), actual_flags)
        if actual_flags & 1:
            w.index(prefix + '.tail', 1)
        else:
            w.floats(prefix + '.tail_offset', (_ZERO, _ONE, _ZERO))
        if actual_flags & 0x0300:
            w.index(prefix + '.grant_parent', 1); w.floats(prefix + '.grant_weight', (_ZERO,))
        if actual_flags & 0x0400:
            w.floats(prefix + '.fixed_axis', (_ONE, _ZERO, _ZERO))
        if actual_flags & 0x0800:
            w.floats(prefix + '.local_x', (_ONE, _ZERO, _ZERO))
            w.floats(prefix + '.local_z', (_ZERO, _ZERO, _ONE))
        if actual_flags & 0x2000:
            w.count(prefix + '.external_parent_key', 17)
        if actual_flags & 0x0020:
            w.index(prefix + '.IK.target', 1); w.count(prefix + '.IK.iterations', 1)
            w.floats(prefix + '.IK.angle', (_QUARTER,)); w.count(prefix + '.IK.links', 2)
            w.index(prefix + '.IK.link0.target', 0); w.byte(prefix + '.IK.link0.limited', 1)
            w.floats(prefix + '.IK.link0.minimum', _words((-.5, -.25, -.125)))
            w.floats(prefix + '.IK.link0.maximum', _words((.5, .25, .125)))
            w.index(prefix + '.IK.link1.target', 1); w.byte(prefix + '.IK.link1.limited', 0)
        expected_size = 18 + index_size + (index_size if actual_flags & 1 else 12)
        expected_size += index_size + 4 if actual_flags & 0x0300 else 0
        expected_size += 12 if actual_flags & 0x0400 else 0
        expected_size += 24 if actual_flags & 0x0800 else 0
        expected_size += 4 if actual_flags & 0x2000 else 0
        expected_size += index_size + 12 + (index_size + 1 + 24) + (index_size + 1) if actual_flags & 0x0020 else 0
        assert len(w.data) - fixed == expected_size
        bones.append({'index': i, 'offset': start, 'end': len(w.data), 'name': name,
                      'name_e': english, 'flags': actual_flags, 'flags_offset': flag_row['offset'],
                      'unknown_flag_bits': actual_flags & ~0x3f3f})

    sections['morphs'] = len(w.data)
    w.count('morphs.count', len(morph_types))
    morphs = []
    for i, kind in enumerate(morph_types):
        prefix = 'morph.' + str(i); start = len(w.data)
        w.text(prefix + '.name', 'Morph' + str(i)); w.text(prefix + '.name_e', '')
        w.byte(prefix + '.category', 4, signed=True); kind_row = w.byte(prefix + '.type', kind, signed=True)
        w.count(prefix + '.offset_count', 1); payload = len(w.data)
        if kind == 0:
            w.index(prefix + '.group_morph', 1 if len(morph_types) > 1 else 0)
            w.floats(prefix + '.group_weight', (_HALF,))
        elif kind == 1:
            w.index(prefix + '.vertex', 0, vertex=True); w.floats(prefix + '.delta', _words((.125, .25, .5)))
        elif kind == 2:
            w.index(prefix + '.bone', 1); w.floats(prefix + '.translation', _words((.125, .25, .5)))
            w.floats(prefix + '.quaternion', (_ZERO, _ZERO, _ZERO, _ZERO))
        elif 3 <= kind <= 7:
            w.index(prefix + '.vertex', 1, vertex=True); w.floats(prefix + '.uv', _words((.125, .25, .5, 1)))
        else:
            w.index(prefix + '.material', 0); w.byte(prefix + '.operation', 1, signed=True)
            w.floats(prefix + '.material_words', _words(range(1, 29)))
        width = (index_size + {0: 4, 1: 12, 2: 28, 3: 16, 4: 16, 5: 16, 6: 16, 7: 16, 8: 113}[kind])
        assert len(w.data) - payload == width
        morphs.append({'index': i, 'type': kind, 'offset': start, 'end': len(w.data),
                       'type_offset': kind_row['offset'], 'payload_offset': payload, 'payload_bytes': width})

    sections['displays'] = len(w.data)
    w.count('displays.count', 1); w.text('display.name', 'Display'); w.text('display.name_e', '')
    w.byte('display.special', 1); w.count('display.elements', 2 if morph_types else 1)
    w.byte('display.bone.tag', 0); w.index('display.bone.index', 0)
    if morph_types:
        w.byte('display.morph.tag', 1); w.index('display.morph.index', 0)

    sections['rigids'] = len(w.data)
    w.count('rigids.count', 1); rigid_start = len(w.data)
    body_name = w.text('rigid.name', '試験Body'); body_english = w.text('rigid.name_e', 'Body')
    rigid_payload = len(w.data)
    w.index('rigid.bone', bone_ref); w.byte('rigid.group', 15, signed=True)
    w.put('rigid.mask', bytes.fromhex('0180'), 32769); w.byte('rigid.shape', 1, signed=True)
    body_float = w.floats('rigid.F32_words', _BODY_WORDS); w.byte('rigid.mode', 2, signed=True)
    assert len(w.data) - rigid_payload == index_size + 61
    rigid_end = len(w.data)

    sections['joints'] = len(w.data)
    w.count('joints.count', 1); joint_start = len(w.data)
    joint_name = w.text('joint.name', '接続Joint'); joint_english = w.text('joint.name_e', 'Joint')
    joint_payload = len(w.data)
    w.byte('joint.mode', joint_mode, signed=True); w.index('joint.source', 0); w.index('joint.destination', rigid_ref)
    joint_float = w.floats('joint.F32_words', _JOINT_WORDS)
    assert len(w.data) - joint_payload == 97 + 2 * index_size
    data = bytes(w.data)
    expected = {
        'scope': 'Authored layout/byte oracle only; not geometry, skeleton, physics or native-behavior validity',
        'source_sha256': hashlib.sha256(data).hexdigest(), 'source_bytes': len(data), 'EOF': len(data),
        'index_size': index_size, 'encoding': encoding, 'additional_uv': additional_uv, 'deform': deform,
        'counts': {'vertices': vertex_count, 'indices': 3, 'textures': 1, 'materials': 2, 'bones': 2,
                   'morphs': len(morph_types), 'displays': 1, 'rigids': 1, 'joints': 1},
        'face_indices': list(face_indices),
        'sections': sections, 'fields': w.fields, 'vertices': vertices, 'materials': materials,
        'bones': bones, 'morphs': morphs,
        'rigid': {'index': 0, 'offset': rigid_start, 'end': rigid_end, 'payload_offset': rigid_payload,
                  'payload_bytes': index_size + 61, 'name': body_name, 'name_e': body_english,
                  'bone_ref': bone_ref, 'group': 15, 'mask': 32769, 'shape': 1, 'mode': 2,
                  'F32_offset': body_float['offset'], 'F32_words_le_hex': list(_BODY_WORDS),
                  'negative_zero_word_indices': [3], 'subnormal_word_indices': [4], 'NaN_word_indices': [13]},
        'joint': {'index': 0, 'offset': joint_start, 'end': len(data), 'payload_offset': joint_payload,
                  'payload_bytes': 97 + 2 * index_size, 'name': joint_name, 'name_e': joint_english,
                  'mode': joint_mode, 'source_ref': 0, 'destination_ref': rigid_ref,
                  'F32_offset': joint_float['offset'], 'F32_words_le_hex': list(_JOINT_WORDS),
                  'negative_zero_word_indices': [3], 'subnormal_word_indices': [22], 'infinity_word_indices': [23]},
        'native_model_or_float_validity_qualified': False, 'parser_used': False,
    }
    return data, expected

"""Independent PMX2.0 declared-layout witness, immutable RAM bytes only.

Authored from the public layout document, not the candidate implementation.
This module imports no candidate, fixture, installed addon or file API. It walks
all preceding tables itself; a witness is not native or physical qualification.
"""
from dataclasses import dataclass, fields
import hashlib
import json
import struct

FORMAT = 'has_independent_pmx20_table_witness_prototype_1'


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Limits:
    source_bytes: int = 128 * 1024 * 1024
    output_bytes: int = 8 * 1024 * 1024
    string_bytes: int = 1024 * 1024
    total_string_bytes: int = 8 * 1024 * 1024
    name_utf8_bytes: int = 1024
    vertex_count: int = 2_000_000
    index_count: int = 12_000_000
    texture_count: int = 10_000
    material_count: int = 10_000
    bone_count: int = 4096
    morph_count: int = 4096
    display_count: int = 4096
    body_count: int = 512
    joint_count: int = 1024
    morph_items: int = 1_000_000
    ik_links: int = 65_536
    display_items: int = 65_536
    work_units: int = 20_000_000


HARD = Limits()
ORDER = ('vertex', 'index', 'texture', 'material', 'bone', 'morph', 'display', 'body', 'joint')


def require(ok, label):
    if not ok:
        raise Refused(label)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


class _Walk:
    def __init__(self, data, limits):
        self.data = data
        self.pos = 17
        self.limits = limits
        self.work = 0
        self.text_total = 0
        self.output_charge = 4096
        self.extents = {}
        self.quantities = {}
        self.ranges = []
        self.totals = {'morph_items': 0, 'ik_links': 0, 'display_items': 0}
        require(type(data) is bytes and 17 <= len(data) <= limits.source_bytes, 'immutable bounded PMX bytes required')
        require(data[:4] == b'PMX ' and data[4:8] == b'\x00\x00\x00\x40', 'only exact PMX2.0 supported')
        require(data[8] == 8, 'unsupported global-header length')
        require(data[9] in (0, 1) and data[10] <= 4, 'unsupported encoding or additional UV profile')
        self.codec = ('utf-16-le', 'utf-8')[data[9]]
        self.uv = data[10]
        keys = ('vertex', 'texture', 'material', 'bone', 'morph', 'body')
        self.width = dict(zip(keys, data[11:17]))
        require(all(n in (1, 2, 4) for n in self.width.values()), 'unsupported reference width')
        self.names = []

    def consume(self, size):
        self.work += 1
        require(self.work <= self.limits.work_units, 'oracle work budget')
        require(type(size) is int and 0 <= size <= len(self.data) - self.pos, 'truncated PMX field')
        start = self.pos
        self.pos += size
        return start

    def charge(self, size):
        self.output_charge += size
        require(self.output_charge <= self.limits.output_bytes, 'oracle retained-output budget')

    def number(self, code):
        size = struct.calcsize('<' + code)
        at = self.consume(size)
        value = struct.unpack_from('<' + code, self.data, at)[0]
        return {'start': at, 'number': value, 'hex': self.data[at:at + size].hex(),
                'width': size, 'signed': code.islower()}

    def selector(self, choices):
        token = self.number('B')
        require(token['number'] in choices, 'unsupported PMX selector')
        return token

    def reference(self, category, absent=False):
        codes = {1: ('b', 'B'), 2: ('h', 'H'), 4: ('i', 'I')}
        token = self.number(codes[self.width[category]][category == 'vertex'])
        n = token['number']
        require(n >= (-1 if absent else 0), 'invalid negative PMX reference')
        if n >= 0:
            self.extents[category] = max(n, self.extents.get(category, -1))
        return token

    def text(self, retain=False):
        length = self.number('i')
        n = length['number']
        require(0 <= n <= self.limits.string_bytes, 'oracle string budget')
        self.text_total += n
        require(self.text_total <= self.limits.total_string_bytes, 'oracle aggregate string budget')
        at = self.consume(n)
        encoded = self.data[at:at + n]
        try:
            decoded = encoded.decode(self.codec, errors='strict')
        except UnicodeError as error:
            raise Refused('invalid encoded PMX text') from error
        if not retain:
            return None
        require(len(decoded.encode('utf-8')) <= self.limits.name_utf8_bytes, 'oracle retained name budget')
        self.charge(4 * n + 6 * len(decoded.encode('utf-8')) + 256)
        return {'length_field': length['start'], 'payload_start': at, 'byte_count': n,
                'encoding': self.codec, 'encoded': encoded.hex(), 'decoded': decoded}

    def words(self, quantity):
        self.charge(512 + quantity * 48)
        at = self.consume(quantity * 4)
        raw = self.data[at:at + quantity * 4]
        # Independently classify exponent bits directly from the high two bytes.
        exceptional = [at + 4 * i for i in range(quantity)
                       if raw[4 * i + 3] & 127 == 127 and raw[4 * i + 2] >= 128]
        return {'start': at, 'word_hex': [raw[i:i + 4].hex() for i in range(0, len(raw), 4)],
                'nonfinite_offsets': exceptional}

    def nested_count(self, budget):
        n = self.number('i')['number']
        require(n >= 0, 'negative nested PMX count')
        self.totals[budget] += n
        require(self.totals[budget] <= getattr(self.limits, budget), 'oracle aggregate nested-count budget')
        return n

    def table(self, name, entry, minimum):
        token = self.number('i')
        count = token['number']
        require(0 <= count <= getattr(self.limits, name + '_count'), 'oracle table-count budget')
        require(count <= (len(self.data) - self.pos) // minimum, 'truncated PMX table extent')
        if name == 'index':
            require(count % 3 == 0, 'face index count must be divisible by three')
        self.quantities[name] = count
        block = {'kind': name, 'quantity': count, 'count_token': token, 'payload_start': self.pos}
        retained = []
        for i in range(count):
            record = entry(i)
            if record is not None:
                retained.append(record)
        block['payload_end'] = self.pos
        self.ranges.append(block)
        return retained

    def vertex(self, _index):
        self.consume(8 * 4 + self.uv * 4 * 4)
        deform = self.selector((0, 1, 2, 3))['number']
        if deform == 0:
            self.reference('bone', True)
        elif deform == 1:
            self.reference('bone', True); self.reference('bone', True)
            self.consume(4)
        elif deform == 2:
            for _ in range(4): self.reference('bone', True)
            self.consume(4 * 4)
        else:
            self.reference('bone', True); self.reference('bone', True)
            self.consume((1 + 3 + 3 + 3) * 4)
        self.consume(4)

    def face_index(self, _index):
        self.reference('vertex')

    def texture(self, _index):
        self.text()

    def material(self, _index):
        self.text(); self.text()
        self.consume((4 + 3 + 1 + 3) * 4)
        self.selector(range(32)); self.consume((4 + 1) * 4)
        self.reference('texture', True); self.reference('texture', True)
        self.selector((0, 1, 2, 3))
        shared = self.selector((0, 1))['number']
        if shared:
            self.selector(range(10))
        else:
            self.reference('texture', True)
        self.text()
        count = self.number('i')['number']
        require(0 <= count <= self.quantities['index'] and count % 3 == 0, 'invalid material index extent')

    def bone(self, index):
        self.charge(1024)
        begin = self.pos
        row = {'index': index, 'names': [self.text(True), self.text(True)], 'position': self.words(3),
               'parent': self.reference('bone', True), 'layer': self.number('i'), 'flags': self.number('H')}
        flags = row['flags']['number']
        require(flags & ~0x3f3f == 0, 'unsupported bone flag bits')
        row['tail'] = {'bone': self.reference('bone', True)} if flags & 1 else {'offset_words': self.words(3)}
        if flags & (0x100 | 0x200):
            row['inherit'] = {'parent': self.reference('bone', True), 'factor': self.words(1)}
        if flags & 0x400: row['fixed_direction'] = self.words(3)
        if flags & 0x800: row['local_directions'] = self.words(6)
        if flags & 0x2000: row['external_transform'] = self.number('i')
        if flags & 0x20:
            ik = {'target': self.reference('bone', True), 'iterations': self.number('i')}
            require(ik['iterations']['number'] >= 0, 'negative IK iteration count')
            ik['step_angle'] = self.words(1)
            count = self.nested_count('ik_links')
            require(count <= (len(self.data) - self.pos) // (self.width['bone'] + 1), 'truncated IK link list')
            links = []
            for _ in range(count):
                self.charge(512)
                link = {'bone': self.reference('bone', True), 'limited': self.selector((0, 1))}
                if link['limited']['number']: link['limits'] = self.words(6)
                links.append(link)
            ik['links'] = links
            row['ik'] = ik
        row['span'] = [begin, self.pos]
        return row

    def morph(self, _index):
        self.text(); self.text(); self.selector(range(5))
        kind = self.selector(range(9))['number']
        count = self.nested_count('morph_items')
        sizes = {0: self.width['morph'] + 4, 1: self.width['vertex'] + 3 * 4,
                 2: self.width['bone'] + 7 * 4, 8: self.width['material'] + 1 + 28 * 4}
        minimum = sizes.get(kind, self.width['vertex'] + 4 * 4)
        require(count <= (len(self.data) - self.pos) // minimum, 'truncated morph offsets')
        for _ in range(count):
            if kind == 0:
                self.reference('morph'); self.consume(4)
            elif kind == 1:
                self.reference('vertex'); self.consume(3 * 4)
            elif kind == 2:
                self.reference('bone'); self.consume(7 * 4)
            elif 3 <= kind <= 7:
                self.reference('vertex'); self.consume(4 * 4)
            else:
                self.reference('material', True); self.selector((0, 1)); self.consume(28 * 4)

    def display(self, _index):
        self.text(); self.text(); self.selector((0, 1))
        count = self.nested_count('display_items')
        require(count <= (len(self.data) - self.pos) // 2, 'truncated display entries')
        for _ in range(count):
            tag = self.selector((0, 1))['number']
            self.reference('bone' if tag == 0 else 'morph')

    def body(self, index):
        self.charge(1024)
        begin = self.pos
        row = {'index': index, 'names': [self.text(True), self.text(True)], 'bone': self.reference('bone', True),
               'group': self.selector(range(16)), 'mask': self.number('H'), 'shape': self.selector((0, 1, 2)),
               'parameters': self.words(3 + 3 + 3 + 1 + 1 + 1 + 1 + 1), 'mode': self.selector((0, 1, 2))}
        row['span'] = [begin, self.pos]
        return row

    def joint(self, index):
        self.charge(1024)
        begin = self.pos
        row = {'index': index, 'names': [self.text(True), self.text(True)], 'mode': self.selector((0,)),
               'body_a': self.reference('body', True), 'body_b': self.reference('body', True),
               'parameters': self.words(8 * 3)}
        row['span'] = [begin, self.pos]
        return row


def read_oracle(data, limits=Limits()):
    require(type(limits) is Limits, 'exact oracle Limits required')
    for field in fields(Limits):
        value = getattr(limits, field.name)
        require(type(value) is int and 0 <= value <= getattr(HARD, field.name), 'invalid or widened oracle budget')
    scan = _Walk(data, limits)
    model_names = [scan.text(True), scan.text(True)]
    scan.text(); scan.text()
    plans = [('vertex', scan.vertex, 8 * 4 + scan.uv * 16 + 1 + scan.width['bone'] + 4),
             ('index', scan.face_index, scan.width['vertex']), ('texture', scan.texture, 4),
             ('material', scan.material, 8 + 44 + 1 + 20 + 2 * scan.width['texture'] + 1 + 1 + 1 + 4 + 4),
             ('bone', scan.bone, 8 + 12 + scan.width['bone'] + 4 + 2 + scan.width['bone']),
             ('morph', scan.morph, 8 + 1 + 1 + 4), ('display', scan.display, 8 + 1 + 4),
             ('body', scan.body, 8 + scan.width['bone'] + 1 + 2 + 1 + 14 * 4 + 1),
             ('joint', scan.joint, 8 + 1 + 2 * scan.width['body'] + 24 * 4)]
    records = {}
    for name, entry, minimum in plans:
        rows = scan.table(name, entry, minimum)
        if name in ('bone', 'body', 'joint'): records[name] = rows
    require(scan.pos == len(data), 'trailing bytes or unsupported soft-body/extension data')
    # All prefix references are checked against final table extents, independently
    # of the candidate's immediate/deferred validation strategy.
    require(all(high < scan.quantities[kind] for kind, high in scan.extents.items()), 'reference exceeds declared table')
    result = {'format': FORMAT, 'native_qualified': False, 'physical_validity_or_simulation': False,
              'source': {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)},
              'header': {'version': data[4:8].hex(), 'globals': data[9:17].hex(), 'codec': scan.codec,
                         'encoding_selector': data[9], 'extra_uv_vectors': scan.uv, 'reference_widths': scan.width},
              'model_names': model_names, 'ranges': scan.ranges, 'records': records,
              'scope': 'OPAQUE_BONE_AND_PHYSICS_WORDS_WITH_RESTRICTED_PREFIX_LAYOUT_ONLY',
              'work_units': scan.work, 'string_bytes': scan.text_total}
    require(len(canonical(result)) <= limits.output_bytes, 'complete oracle JSON output budget')
    return result

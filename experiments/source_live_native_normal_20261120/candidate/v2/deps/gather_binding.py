"""Bounded CPU observation ledger; no Blender import, hooks, file IO or launch.

Observation provenance is a future host obligation. Object references are retained
and compared with `is`; names, traversal order and carrier values select no IDs.
"""
import copy
import hashlib
import json
import operator
import struct

from experiments.carrier_input_domain_20261118.semantic_compare import Snapshot, freeze, parse_json_document

MAX_OBJECTS = 2
MAX_PRIMITIVES = 4
MAX_POINTS = 200_000
MAX_CORNERS = 1_000_000
MAX_GLB = 128 * 1024 * 1024
MAX_TABLE = 65_536


def need(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value, maximum):
    need(type(value) is int and 0 <= value < maximum, 'Exact bounded integer required')
    return value


def integers(values, maximum, limit):
    need(type(values) in (list, tuple) and 0 < len(values) <= limit, 'Bounded nonempty integer sequence required')
    return tuple(integer(value, maximum) for value in values)


def same_refs(left, right):
    return len(left) == len(right) and all(a is b for a, b in zip(left, right))


def cached_material_slot(value, maximum):
    """Read authentic cached np.uint32 scalars without rewriting their row.

    Exact runtime type provenance remains the future pinned hook's obligation.
    __index__ is an integer protocol; no floating conversion/truncation occurs.
    """
    if type(value) is int:
        return integer(value, maximum)
    scalar_type = type(value)
    dtype = getattr(value, 'dtype', None)
    need(scalar_type.__module__ == 'numpy' and scalar_type.__name__ == 'uint32'
         and getattr(dtype, 'kind', None) == 'u' and getattr(dtype, 'itemsize', None) == 4
         and getattr(value, 'ndim', None) == 0, 'Exact cached NumPy uint32 material scalar required')
    return integer(operator.index(value), maximum)


def read_glb(raw):
    """Same strict lexical/two-chunk boundary as the sealed input-domain reader."""
    need(type(raw) is bytes and 28 <= len(raw) <= MAX_GLB, 'Bounded immutable GLB required')
    need(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Exact GLB2 header required')
    size, kind = struct.unpack_from('<I4s', raw, 12)
    need(kind == b'JSON' and size % 4 == 0 and 20 + size + 8 <= len(raw), 'JSON-first two-chunk profile')
    doc = parse_json_document(raw[20:20 + size])
    at = 20 + size
    count, kind = struct.unpack_from('<I4s', raw, at)
    need(kind == b'BIN\0' and count % 4 == 0 and at + 8 + count == len(raw), 'One exact BIN chunk')
    binary = raw[at + 8:]
    need(type(doc) is dict, 'GLB document object required')
    for name in ('scenes', 'nodes', 'meshes', 'materials', 'textures', 'images', 'samplers',
                 'skins', 'animations', 'cameras', 'accessors', 'bufferViews', 'buffers'):
        need(type(doc.get(name, [])) is list and len(doc.get(name, [])) <= MAX_TABLE, 'Bounded resource table required')
    buffers = doc.get('buffers')
    need(type(buffers) is list and len(buffers) == 1 and type(buffers[0]) is dict, 'One embedded buffer')
    declared = buffers[0].get('byteLength')
    need(type(declared) is int and 0 < declared <= len(binary) <= declared + 3, 'BIN bounds')
    need(not any(binary[declared:]), 'Zero BIN padding required')
    return doc, binary


class GatherBinding:
    """One cold, nonshared, triangle-only gather per exact admitted object/mesh.

    Each admission has object, mesh, joined_source_ids, material_slots and
    primitive_count. IDs must already come from the independent exact point join.
    The outer host must normalize admitted NumPy integer arrays/scalars only after
    checking their exact unsigned dtype, dimensionality and bounds. No coercion is
    performed here. Every event must come from independently pinned actual hooks;
    this module alone cannot establish that provenance.
    """
    def __init__(self, admissions):
        need(type(admissions) is list and 1 <= len(admissions) <= MAX_OBJECTS, 'Bounded admissions required')
        self.entries = []
        for row in admissions:
            need(type(row) is dict and set(row) == {'object', 'mesh', 'joined_source_ids', 'material_slots', 'primitive_count'}, 'Exact admission schema required')
            obj, mesh = row['object'], row['mesh']
            need(obj is not None and mesh is not None and obj is not mesh, 'Distinct actual object and mesh required')
            need(all(obj is not prior['object'] and mesh is not prior['mesh'] for prior in self.entries), 'Object/mesh alias refused')
            ids = integers(row['joined_source_ids'], MAX_POINTS, MAX_POINTS)
            need(len(set(ids)) == len(ids), 'Unique joined source IDs required')
            slots = row['material_slots']
            need(type(slots) in (list, tuple) and 1 <= len(slots) <= 64 and all(x is not None for x in slots), 'Exact material-bearing profile required')
            count = row['primitive_count']
            need(type(count) is int and 1 <= count <= MAX_PRIMITIVES, 'Bounded primitive count')
            self.entries.append(dict(object=obj, mesh=mesh, ids=ids, slots=tuple(slots), count=count,
                                     creator=None, rows=[], gathered=None, final=None))
        ids = [x for row in self.entries for x in row['ids']]
        need(len(ids) <= MAX_POINTS and len(ids) == len(set(ids)), 'Global source ID overlap/budget refused')
        need(sum(row['count'] for row in self.entries) <= MAX_PRIMITIVES, 'Primitive budget exceeded')
        self.material_references = []

    def _creator_entry(self, creator):
        matches = [row for row in self.entries if getattr(creator, 'blender_object', None) is row['object']
                   and getattr(creator, 'blender_mesh', None) is row['mesh']]
        need(len(matches) == 1, 'Exact admitted creator object/mesh identity required')
        return matches[0]

    def observe_creator(self, creator, branch, blender_indices, material_slot, topology_indices, ordinal):
        row = self._creator_entry(creator)
        need(row['gathered'] is None and row['final'] is None and branch == 'not_shared', 'Cold nonshared observation required')
        need(row['creator'] is None or row['creator'] is creator, 'Repeated creator/cache extraction refused')
        need(type(ordinal) is int and ordinal == len(row['rows']) < row['count'], 'Exact creation ordinal required')
        points = integers(blender_indices, len(row['ids']), MAX_POINTS)
        need(len(points) == len(set(points)), 'No-new-split profile required')
        slot = integer(material_slot, len(row['slots']))
        topology = integers(topology_indices, len(points), MAX_CORNERS)
        need(len(topology) % 3 == 0, 'Triangle topology required')
        need(sum(len(x['topology']) for e in self.entries for x in e['rows']) + len(topology) <= MAX_CORNERS, 'Cumulative corner bound')
        row['creator'] = creator
        row['rows'].append(dict(slot=slot, ids=tuple(row['ids'][i] + 1 for i in points), topology=topology))

    def bind_gather(self, creator, materials, cached_internal_primitives, gathered_primitives, gltf_mesh):
        """Observe exact cache-return rows, gather return list and owning Mesh.

        The host captures these inside one actual cold call chain. Supplying
        arbitrary dictionaries can exercise this CPU contract, not qualify hooks.
        """
        row = self._creator_entry(creator)
        need(row['creator'] is creator and len(row['rows']) == row['count'] and row['gathered'] is None, 'Missing observer or reused gather refused')
        need(type(materials) in (list, tuple) and same_refs(materials, row['slots']), 'Exact source material tuple required')
        need(type(cached_internal_primitives) is list and type(gathered_primitives) is list
             and len(cached_internal_primitives) == len(gathered_primitives) == row['count'], 'Exact cache/gather cardinality required')
        need(getattr(gltf_mesh, 'primitives', None) is gathered_primitives, 'Owning gathered Mesh list identity required')
        need(all(e['gathered'] is None or e['gathered']['mesh'] is not gltf_mesh for e in self.entries), 'Gathered Mesh cache alias refused')
        prior = [p for e in self.entries if e['gathered'] for p in e['gathered']['primitives']]
        need(len({id(x) for x in gathered_primitives}) == len(gathered_primitives)
             and all(all(p is not q for q in prior) for p in gathered_primitives), 'Primitive object reuse refused')
        need(len({id(x) for x in cached_internal_primitives}) == len(cached_internal_primitives), 'Internal primitive alias refused')
        prior_internal = [p for e in self.entries if e['gathered'] for p in e['gathered']['internal']]
        need(all(all(p is not q for q in prior_internal) for p in cached_internal_primitives), 'Cross-object extraction cache reuse refused')
        prior_attributes = [p.attributes for p in prior]
        need(len({id(p.attributes) for p in gathered_primitives}) == len(gathered_primitives)
             and all(all(p.attributes is not attrs for attrs in prior_attributes) for p in gathered_primitives), 'Gathered attribute-table alias refused')
        captured = []
        for observation, internal, primitive in zip(row['rows'], cached_internal_primitives, gathered_primitives):
            need(type(internal) is dict and 'material' in internal, 'Cached internal material slot required')
            need(cached_material_slot(internal['material'], len(row['slots'])) == observation['slot'], 'Observed source material slot/order differs')
            need(getattr(primitive, 'attributes', None) is internal.get('attributes')
                 and getattr(primitive, 'indices', None) is internal.get('indices'), 'Actual cache/gather attribute/index references differ')
            need(type(primitive.attributes) is dict and primitive.attributes and primitive.indices is not None, 'Gathered storage references required')
            need(primitive.mode is None or type(primitive.mode) is int and primitive.mode == 4, 'Triangle-only mode required')
            need(getattr(primitive, 'targets', None) is None and getattr(primitive, 'extensions', None) is None
                 and getattr(primitive, 'extras', None) is None, 'Morph/extension/extra primitive profile refused')
            need(primitive.material is not None and type(primitive.material) not in (int, float, bool, str), 'Actual glTF material object required')
            captured.append(dict(attributes=primitive.attributes, material=primitive.material))
        row['gathered'] = dict(mesh=gltf_mesh, primitives=tuple(gathered_primitives), captured=captured,
                               internal=tuple(cached_internal_primitives))

    def record_material_reference(self, material, index):
        integer(index, MAX_TABLE)
        need(any(e['gathered'] and any(x['material'] is material for x in e['gathered']['captured']) for e in self.entries), 'Unobserved material reference refused')
        for ref, found in self.material_references:
            if ref is material:
                need(found == index, 'Material reference reassigned')
                return
            need(found != index, 'Distinct material objects alias one index')
        self.material_references.append((material, index))

    def record_mesh_reference(self, mesh, index):
        integer(index, MAX_OBJECTS)
        matches = [e for e in self.entries if e['gathered'] and e['gathered']['mesh'] is mesh]
        need(len(matches) == 1, 'Actual gathered Mesh reference required')
        row = matches[0]; gathered = row['gathered']
        need(row['final'] is None and all(e['final'] is None or e['final']['index'] != index for e in self.entries), 'Repeated/aliased final Mesh reference refused')
        need(type(mesh.primitives) is list and same_refs(mesh.primitives, gathered['primitives']), 'Final primitive object order changed')
        finals = []
        for primitive, captured in zip(mesh.primitives, gathered['captured']):
            need(primitive.attributes is captured['attributes'] and type(primitive.attributes) is dict
                 and all(type(k) is str and type(v) is int and 0 <= v < MAX_TABLE for k, v in primitive.attributes.items()), 'Final attribute references differ')
            integer(primitive.indices, MAX_TABLE)
            materials = [value for ref, value in self.material_references if ref is captured['material']]
            need(len(materials) == 1 and type(primitive.material) is int and primitive.material == materials[0], 'Final actual material reference differs')
            need(primitive.mode is None or type(primitive.mode) is int and primitive.mode == 4, 'Final triangle mode differs')
            need(getattr(primitive, 'targets', None) is None and getattr(primitive, 'extensions', None) is None
                 and getattr(primitive, 'extras', None) is None, 'Final primitive profile differs')
            value = dict(attributes=copy.deepcopy(primitive.attributes), indices=primitive.indices, material=primitive.material)
            if primitive.mode is not None: value['mode'] = primitive.mode
            finals.append(value)
        row['final'] = dict(index=index, primitives=finals)

    def finalize(self, raw_glb, expected_sha256):
        need(type(expected_sha256) is str and len(expected_sha256) == 64 and all(c in '0123456789abcdef' for c in expected_sha256), 'Exact host GLB SHA pin required')
        need(type(raw_glb) is bytes and 28 <= len(raw_glb) <= MAX_GLB, 'Bounded immutable GLB required')
        need(hashlib.sha256(raw_glb).hexdigest() == expected_sha256, 'Pinned GLB bytes differ')
        need(all(e['final'] is not None for e in self.entries), 'Missing final exporter reference event')
        doc, binary = read_glb(raw_glb)
        need(len(doc.get('meshes', [])) == len(self.entries), 'Unobserved or missing final GLB Mesh')
        snapshot = Snapshot(doc, binary, carrier=True)
        relation = {}; public_rows = []
        for row in self.entries:
            final = row['final']; mi = final['index']; mesh = doc['meshes'][mi]
            need(type(mesh) is dict and type(mesh.get('primitives')) is list
                 and len(mesh['primitives']) == row['count'], 'Final GLB primitive count differs')
            for pi, (primitive, bound, observation) in enumerate(zip(mesh['primitives'], final['primitives'], row['rows'])):
                need(freeze(primitive) == freeze(bound), 'Final serialized primitive references/order/material differ')
                attrs = primitive['attributes']
                need('POSITION' in attrs, 'POSITION required for independent exported row count')
                need([name for name in attrs if name.casefold() == '_has_native_normal_id'] == ['_HAS_NATIVE_NORMAL_ID'], 'Exact owned carrier semantic required')
                position = doc['accessors'][integer(attrs['POSITION'], len(doc['accessors']))]
                need(position.get('componentType') == 5126 and type(position.get('componentType')) is int
                     and position.get('type') == 'VEC3' and type(position.get('count')) is int
                     and position['count'] == len(observation['ids']), 'POSITION row count differs')
                index = integer(primitive['indices'], len(doc['accessors']))
                accessor = doc['accessors'][index]
                need(type(accessor.get('count')) is int and accessor['count'] == len(observation['topology'])
                     and accessor.get('type') == 'SCALAR' and type(accessor.get('componentType')) is int
                     and accessor['componentType'] in (5121, 5123, 5125) and accessor.get('normalized', False) is False, 'Bounded unsigned topology accessor required')
                _, token = snapshot.accessor(index)
                code = {5121: 'B', 5123: 'H', 5125: 'I'}[accessor['componentType']]
                topology = tuple(x[0] for x in struct.iter_unpack('<' + code, token['component_bytes']))
                need(topology == observation['topology'], 'Decoded GLB topology differs from observer')
                relation[(mi, pi)] = observation['ids']
                public_rows.append(dict(mesh=mi, primitive=pi, source_ids=len(observation['ids']), corners=len(topology)))
        ids = [x for values in relation.values() for x in values]
        expected = {x + 1 for row in self.entries for x in row['ids']}
        need(len(ids) == len(set(ids)) and set(ids) == expected, 'Incomplete/repeated source coverage refused')
        private = [{'mesh': mi, 'primitive': pi, 'one_based_source_ids': list(relation[(mi, pi)])} for mi, pi in sorted(relation)]
        digest = hashlib.sha256(json.dumps(private, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return relation, dict(format='has_CPU_observation_to_final_primitive_binding_1', passed=True,
                              carrier_glb_sha256=expected_sha256, private_relation_sha256=digest,
                              meshes=len(self.entries), primitives=len(relation), source_ids=len(ids), rows=public_rows,
                              carrier_values_used_for_identity=False, names_used_for_identity=False,
                              actual_hooks_observed=False, actual_native_GLTF_binding_qualified=False,
                              independent_input_domain_qualified=False, native_normal_fidelity_qualified=False,
                              adoption_qualified=False, source_unit_conversion_changed=False,
                              six_foot_normalization_applied=False)

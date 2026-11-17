"""Pure CPU ledger of exporter point IDs. No carrier values enter this API."""
import hashlib
import json


def require(ok, message):
    if not ok: raise ValueError(message)


def integers(values, maximum):
    require(type(values) in (list, tuple) and len(values) <= 1_000_000, 'Bounded integer sequence required')
    require(all(type(value) is int and 0 <= value < maximum for value in values), 'Exact in-domain integer sequence required')
    return list(values)


class ManifestLedger:
    """Host must separately bind logical name to exact observed Blender object identity."""
    def __init__(self, point_maps):
        require(type(point_maps) is dict and 1 <= len(point_maps) <= 2, 'Bounded exact logical object maps required')
        self.maps = {}
        for name, ids in point_maps.items():
            require(type(name) is str and name, 'Exact logical name required')
            values = integers(ids, 200_000)
            require(values and len(values) <= 200_000 and len(set(values)) == len(values), 'Unique nonempty source IDs required')
            self.maps[name] = tuple(values)
        all_ids = [value for values in self.maps.values() for value in values]
        require(len(all_ids) == len(set(all_ids)), 'Cross-object source ID overlap refused')
        self.rows = []

    def record(self, name, branch, blender_indices, material_index, topology_indices, ordinal):
        require(name in self.maps and branch == 'not_shared', 'Only exact nonshared object profile admitted')
        require(type(material_index) is int and material_index >= 0 and type(ordinal) is int and ordinal >= 0, 'Exact material/ordinal required')
        prior = [row for row in self.rows if row['logical_name'] == name]
        require(ordinal == len(prior), 'Primitive ordinal differs from creation sequence')
        points = integers(blender_indices, len(self.maps[name]))
        require(points and len(set(points)) == len(points), 'Deduplicated exporter point order required')
        topology = integers(topology_indices, len(points))
        require(topology and len(topology) % 3 == 0, 'Triangle topology required')
        ids = [self.maps[name][point] + 1 for point in points]
        self.rows.append({'logical_name': name, 'creation_ordinal': ordinal, 'material_slot': material_index,
                          'one_based_source_ids': ids, 'topology_indices': topology})

    def finalize(self, expected_primitives, expected_rows):
        require(type(expected_primitives) is int and type(expected_rows) is int and expected_primitives > 0 and expected_rows > 0, 'Exact expected cardinalities required')
        require(len(self.rows) == expected_primitives and {row['logical_name'] for row in self.rows} == set(self.maps), 'Incomplete object/primitive observation')
        ids = [value for row in self.rows for value in row['one_based_source_ids']]
        expected = {value + 1 for values in self.maps.values() for value in values}
        require(len(ids) == expected_rows and len(ids) == len(set(ids)) and set(ids) == expected, 'Expected exact point coverage/order cardinality differs')
        raw = json.dumps(self.rows, sort_keys=True, separators=(',', ':')).encode()
        private = {'format': 'has_private_carrier_creation_identity_manifest_1', 'rows': json.loads(raw),
                   'GLTF_mesh_primitive_binding_qualified': False}
        public = {'format': 'has_carrier_creation_identity_manifest_summary_1', 'primitives': len(self.rows),
                  'source_ids': len(expected), 'private_rows_sha256': hashlib.sha256(raw).hexdigest(),
                  'reads_carrier_values': False, 'shared_accessor_branch_admitted': False,
                  'GLTF_mesh_primitive_binding_qualified': False, 'native_normal_fidelity_qualified': False}
        return private, public

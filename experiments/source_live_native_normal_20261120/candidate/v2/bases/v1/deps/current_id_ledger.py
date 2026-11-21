"""UNRUN pure ledger for a NEW SourceIO import's native-ID/weight observations.

No Blender/NumPy/native imports or IO. All byte arrays are private RAM facts.
The host must admit exact source/runtime/native pins and genuine typed API reads.
Historical saved B never supplies point labels or geometry expectations here.
"""
import hashlib
import math
import struct

PHASES = ('before_setter', 'after_setter', 'before_validate', 'after_validate')
MAX_POINTS, MAX_CORNERS, MAX_GROUPS = 200_000, 1_000_000, 256


class Refusal(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Refusal(code)


def integer(value, bound):
    need(type(value) is int and 0 <= value < bound, 'EXACT_BOUNDED_INTEGER_REQUIRED')
    return value


def words(values, code, bound=None):
    need(type(values) in (list, tuple), 'EXACT_WORD_SEQUENCE_REQUIRED')
    if code == 'I':
        for value in values:
            integer(value, MAX_CORNERS if bound is None else bound)
    elif code == 'B':
        for value in values:
            integer(value, 256)
    elif code == 'f':
        need(all(type(value) is float and math.isfinite(value) and
                 struct.unpack('<f', struct.pack('<f', value))[0] == value for value in values),
             'EXACT_FINITE_F32_WORD_REQUIRED')
    else:
        raise Refusal('UNSUPPORTED_WORD_CODE')
    return struct.pack('<' + code * len(values), *values)


def facts_from_independent(native, mdl_metadata, raw_index_map, native_helper, weight_policy):
    """Package already independently decoded native facts; never take observations.

    native_helper is pinned cbb4 and weight_policy is pinned f838's word admission.
    This calls the explicit source-order REPLACE candidate; actual RNA comparison
    later qualifies only this exact new import/family, never a generic alphabet.
    """
    need(type(native) is dict and native.get('format') == 'has_private_native_point_source_rows_1', 'NATIVE_FACT_FORMAT')
    groups = tuple(native['vertex_groups'])
    need(0 < len(groups) <= MAX_GROUPS and len(set(groups)) == len(groups) and all(type(x) is str for x in groups),
         'UNIQUE_NATIVE_GROUP_NAMES_REQUIRED')
    starts = {}
    for part in mdl_metadata['parts']:
        for model in part:
            if model['count']:
                need(model['name'] not in starts, 'REPEATED_NATIVE_LOGICAL_RECORD')
                starts[model['name']] = (model['start'], model['count'])
    need(set(starts) == set(native['models']), 'NATIVE_MODEL_METADATA_DOMAIN')
    need(type(raw_index_map) is list and len(raw_index_map) == native['native_lod0_row_count'], 'RAW_FIXUP_MAP_DOMAIN')
    need(all(type(value) is int and 0 <= value < native['native_raw_row_count'] for value in raw_index_map) and
         len(set(raw_index_map)) == len(raw_index_map), 'EXACT_UNIQUE_NATIVE_RAW_FIXUP_MAP_REQUIRED')
    result = {}
    for name, record in native['models'].items():
        start, count = starts[name]
        ids, raw_ids, rows = record['ids'], record['raw_ids'], record['rows']
        need(type(ids) is list and type(raw_ids) is list and len(ids) == len(raw_ids) == len(rows) and
             0 < len(ids) <= MAX_POINTS and len(set(ids)) == len(set(raw_ids)) == len(ids), 'NATIVE_ID_CARDINALITY_OR_ALIAS')
        for index, raw in zip(ids, raw_ids):
            integer(index, len(raw_index_map)); integer(raw, native['native_raw_row_count'])
            need(start <= index < start + count and raw_index_map[index] == raw, 'NATIVE_FIXUP_OR_MODEL_RANGE_DIFFERS')
        corner_words = words(record['corners'], 'I', len(ids))
        need(0 < len(corner_words) // 4 <= MAX_CORNERS and len(corner_words) % 12 == 0, 'NATIVE_TRIANGLE_DOMAIN')
        flatten = lambda field: [value for row in rows for value in row[field]]
        stored = tuple(weight_policy.stored_weight_words(
            native_helper.replay_replace_weight_writes(row['positive_weight_writes']), len(groups)) for row in rows)
        result[name] = dict(start=start, model_count=count, ids=tuple(ids), raw_ids=tuple(raw_ids),
                            raw_map=tuple(raw_index_map), groups=groups,
                            source_positions=words(flatten('position'), 'f'),
                            source_normals=words(flatten('normal'), 'f'),
                            source_bones=words(flatten('bones'), 'B'),
                            source_weights=words(flatten('weights'), 'f'),
                            positions=words([native_helper.f32(value * native_helper.F32_SCALE)
                                             for row in rows for value in row['position']], 'f'),
                            loops=corner_words, weights=stored,
                            positive_calls=sum(len(row['positive_weight_writes']) for row in rows))
    return result


class CurrentIDLedger:
    """Four genuine creation stages + final returned object ownership.

    Expected fact schema is produced above. Adapter snapshot schema:
      positions/loops: typed exact readback bytes; groups: ordered tuple of names;
      weights: tuple of per-vertex typed ordered word rows; parent: actual ref.
    Payload schema is four source word streams, after exact ndarray admission.
    Names select only unique already hash-bound native logical records. They never
    select points, a nearest match, current normals or output-derived IDs.
    """
    def __init__(self, facts):
        need(type(facts) is dict and 0 < len(facts) <= 2, 'BOUNDED_NATIVE_FACTS_REQUIRED')
        for name, fact in facts.items():
            need(type(name) is str and type(fact) is dict and set(fact) == {
                'start', 'model_count', 'ids', 'raw_ids', 'raw_map', 'groups', 'source_positions', 'source_normals',
                'source_bones', 'source_weights', 'positions', 'loops', 'weights', 'positive_calls'}, 'EXACT_NATIVE_FACT_SCHEMA')
            integer(fact['start'], MAX_POINTS)
            need(type(fact['model_count']) is int and 0 < fact['model_count'] <= MAX_POINTS and
                 type(fact['ids']) is tuple and 0 < len(fact['ids']) <= MAX_POINTS and
                 type(fact['raw_ids']) is tuple and len(fact['raw_ids']) == len(fact['ids']) and
                 type(fact['raw_map']) is tuple and fact['start'] + fact['model_count'] <= len(fact['raw_map']) <= MAX_POINTS,
                 'NATIVE_FACT_ID_OR_MODEL_DOMAIN')
            for value in fact['raw_map']: integer(value, len(fact['raw_map']))
            need(len(set(fact['raw_map'])) == len(fact['raw_map']), 'NATIVE_FACT_RAW_MAP_ALIAS')
            for index, raw in zip(fact['ids'], fact['raw_ids']):
                integer(index, len(fact['raw_map'])); integer(raw, len(fact['raw_map']))
                need(fact['start'] <= index < fact['start'] + fact['model_count'] and fact['raw_map'][index] == raw,
                     'NATIVE_FACT_ID_FIXUP_RELATION_DIFFERS')
            points = len(fact['ids'])
            need(type(fact['groups']) is tuple and 0 < len(fact['groups']) <= MAX_GROUPS and
                 all(type(group) is str for group in fact['groups']) and len(set(fact['groups'])) == len(fact['groups']),
                 'NATIVE_FACT_GROUP_NAME_DOMAIN')
            need(all(type(fact[key]) is bytes and len(fact[key]) == points * width for key, width in (
                ('source_positions', 12), ('source_normals', 12), ('source_bones', 3), ('source_weights', 12), ('positions', 12))) and
                 type(fact['loops']) is bytes and 0 < len(fact['loops']) <= MAX_CORNERS * 4 and len(fact['loops']) % 12 == 0 and
                 type(fact['weights']) is tuple and len(fact['weights']) == points and all(
                     type(row) is bytes and len(row) <= 24 and len(row) % 8 == 0 for row in fact['weights']) and
                 type(fact['positive_calls']) is int and 0 <= fact['positive_calls'] <= points * 3, 'NATIVE_FACT_WORD_STREAM_DOMAIN')
        self.facts, self.records, self.armature = facts, {}, None
        all_ids = [value for row in facts.values() for value in row['ids']]
        all_raw = [value for row in facts.values() for value in row['raw_ids']]
        need(len(all_ids) <= MAX_POINTS and len(set(all_ids)) == len(all_ids) and len(set(all_raw)) == len(all_raw),
             'GLOBAL_NATIVE_ID_ALIAS_OR_BUDGET')
        self.closed = False

    def _snapshot(self, fact, snapshot, early):
        need(type(snapshot) is dict and set(snapshot) == {'positions', 'loops', 'groups', 'weights', 'parent'},
             'EXACT_MESH_SNAPSHOT_SCHEMA')
        need(type(snapshot['positions']) is bytes and snapshot['positions'] == fact['positions'], 'CURRENT_POSITION_WORDS_DIFFER')
        need(type(snapshot['loops']) is bytes and snapshot['loops'] == fact['loops'], 'CURRENT_LOOP_INDEX_WORDS_DIFFER')
        need(type(snapshot['groups']) is tuple and type(snapshot['weights']) is tuple and
             len(snapshot['weights']) == len(fact['ids']) and all(type(row) is bytes for row in snapshot['weights']),
             'CURRENT_GROUP_OR_WEIGHT_ROW_SCHEMA')
        if early:
            need(snapshot['groups'] == () and all(row == b'' for row in snapshot['weights']) and snapshot['parent'] is None,
                 'EARLY_SETTER_STAGE_ALREADY_HAS_GROUPS_WEIGHTS_OR_PARENT')
        else:
            need(snapshot['groups'] == fact['groups'], 'CURRENT_GROUP_NAME_ORDER_DIFFERS')
            need(snapshot['weights'] == fact['weights'], 'CURRENT_ORDERED_RNA_WEIGHT_WORDS_DIFFER')
            parent = snapshot['parent']
            need(parent is not None and getattr(parent, 'type', None) == 'ARMATURE', 'CURRENT_ACTUAL_ARMATURE_PARENT_REQUIRED')
            need(self.armature is None or self.armature is parent, 'CURRENT_ARMATURE_PARENT_IDENTITY_DIFFERS')
            self.armature = parent

    def observe(self, phase, model, name, model_start, model_count, obj, mesh, mapping, payload, snapshot):
        need(not self.closed and phase in PHASES and type(name) is str and name in self.facts,
             'UNEXPECTED_STAGE_OR_NATIVE_LOGICAL_RECORD')
        fact = self.facts[name]
        need(type(model_start) is int and model_start == fact['start'] and
             type(model_count) is int and model_count == fact['model_count'], 'MODEL_START_OR_COUNT_DIFFERS')
        need(obj is not None and mesh is not None and obj is not mesh and getattr(obj, 'data', None) is mesh,
             'ACTUAL_NEW_OBJECT_MESH_OWNERSHIP_REQUIRED')
        if phase == PHASES[0]:
            need(name not in self.records and all(row['obj'] is not obj and row['mesh'] is not mesh and row['model'] is not model
                                                for row in self.records.values()), 'REPEATED_OR_ALIASED_CREATION_REFERENCE')
            self.records[name] = dict(obj=obj, mesh=mesh, model=model, phases=[], returned=False)
        need(name in self.records, 'CREATION_BOUNDARY_MISSING')
        record = self.records[name]
        need(record['obj'] is obj and record['mesh'] is mesh and record['model'] is model,
             'STAGE_OBJECT_MESH_OR_MODEL_IDENTITY_CHANGED')
        need(len(record['phases']) < 4 and phase == PHASES[len(record['phases'])], 'STAGE_ORDER_OR_REPLAY_REFUSED')
        need(type(mapping) is list and len(mapping) == len(fact['ids']) and len(set(mapping)) == len(mapping),
             'OBSERVED_MAPPING_CARDINALITY_OR_ALIAS')
        for value in mapping:
            integer(value, model_count)
        observed_ids = tuple(model_start + value for value in mapping)
        need(observed_ids == fact['ids'], 'OBSERVED_NATIVE_LOD0_ID_ORDER_DIFFERS')
        observed_raw = tuple(fact['raw_map'][value] for value in observed_ids)
        need(observed_raw == fact['raw_ids'], 'OBSERVED_NATIVE_RAW_ID_ORDER_DIFFERS')
        need(type(payload) is dict and set(payload) == {'positions', 'normals', 'bones', 'weights'} and
             all(type(value) is bytes for value in payload.values()), 'EXACT_TYPED_SOURCE_PAYLOAD_SCHEMA')
        need(all(payload[key] == fact['source_' + key] for key in payload), 'SELECTED_SOURCE_VVD_WORDS_DIFFER')
        self._snapshot(fact, snapshot, len(record['phases']) < 2)
        record['phases'].append(phase)

    def returned(self, container, snapshots):
        need(not self.closed and set(self.records) == set(self.facts) and
             all(tuple(row['phases']) == PHASES for row in self.records.values()), 'INCOMPLETE_CREATION_STAGES')
        objects = getattr(container, 'objects', None)
        need(type(objects) is list and len(objects) == len(self.records) and len({id(obj) for obj in objects}) == len(objects),
             'RETURNED_OBJECT_CARDINALITY_OR_ALIAS')
        need(container.armature is self.armature and self.armature is not None, 'RETURNED_ARMATURE_IDENTITY_DIFFERS')
        need(type(snapshots) is list and len(snapshots) == len(objects), 'RETURNED_SNAPSHOT_CARDINALITY')
        for obj, snapshot in snapshots:
            matches = [name for name, row in self.records.items() if row['obj'] is obj]
            need(len(matches) == 1 and sum(actual is obj for actual in objects) == 1, 'RETURNED_OBJECT_NOT_OBSERVED_CREATION')
            name = matches[0]
            record = self.records[name]
            need(not record['returned'] and obj.data is record['mesh'], 'RETURNED_MESH_CHANGED_OR_REPEATED')
            self._snapshot(self.facts[name], snapshot, False)
            record['returned'] = True
        need(all(row['returned'] for row in self.records.values()), 'MISSING_RETURNED_OBJECT')
        self.closed = True
        rows = []
        for name in sorted(self.facts):
            fact = self.facts[name]
            rows.append(dict(points=len(fact['ids']), corners=len(fact['loops']) // 4,
                             groups=len(fact['groups']), observed_stages=4,
                             ordered_positive_source_calls=fact['positive_calls'],
                             lod0_id_order_sha256=hashlib.sha256(words(fact['ids'], 'I', MAX_POINTS)).hexdigest(),
                             raw_id_order_sha256=hashlib.sha256(words(fact['raw_ids'], 'I', MAX_POINTS)).hexdigest()))
        return dict(format='has_fresh_sourceio_current_id_and_RNA_weight_observation_1', models=rows,
                    observed_new_models=len(rows), observed_new_points=sum(row['points'] for row in rows),
                    observed_new_corners=sum(row['corners'] for row in rows),
                    fresh_creation_chain_matches_independent_native_candidate=True,
                    current_exact_family_ordered_weight_storage_observed=True,
                    historical_saved_B_native_causality_qualified=False,
                    current_B_opened_or_relabelled=False, generic_weight_storage_qualified=False,
                    native_normal_fidelity_qualified=False, carrier_or_exporter_binding_qualified=False,
                    non_normal_semantic_equivalence_qualified=False, application_adoption_qualified=False)

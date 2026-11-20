"""UNRUN stdlib synthetic tests; no native/Blender/NumPy imports or IO."""
import copy
import math
import struct
import unittest
from types import SimpleNamespace as NS

from current_id_ledger import CurrentIDLedger, PHASES, Refusal, words


def fwords(*values):
    return struct.pack('<' + 'f' * len(values), *values)


def weight(*pairs):
    return b''.join(struct.pack('<If', group, value) for group, value in pairs)


def fixture():
    # Native source slots deliberately exercise repeated positive REPLACE,
    # ignored -0/zero slots and an ignored zero-weight bone255.
    raw_map = (11, 10, 12, 3, 4, 5, 6, 7, 8, 9, 1, 0, 2)
    fact = dict(start=10, model_count=3, ids=(10, 11, 12), raw_ids=(1, 0, 2), raw_map=raw_map,
                groups=('root', 'loose'), source_positions=fwords(1., 0., 0., 0., 1., 0., 0., 0., 1.),
                source_normals=fwords(0., 0., 1., 0., 0., 1., 0., 0., 1.),
                source_bones=bytes([1, 0, 1, 255, 0, 0, 1, 0, 1]),
                source_weights=fwords(.5, .25, .75, -0., 1., 0., .25, .5, 0.),
                positions=fwords(.01905, 0., 0., 0., .01905, 0., 0., 0., .01905),
                loops=struct.pack('<3I', 2, 1, 0),
                weights=(weight((1, .75), (0, .25)), weight((0, 1.)), weight((1, .25), (0, .5))),
                positive_calls=6)
    mesh, model, parent = object(), object(), NS(type='ARMATURE')
    obj = NS(data=mesh)
    payload = {key: fact['source_' + key] for key in ('positions', 'normals', 'bones', 'weights')}
    early = dict(positions=fact['positions'], loops=fact['loops'], groups=(), weights=(b'', b'', b''), parent=None)
    late = dict(positions=fact['positions'], loops=fact['loops'], groups=fact['groups'], weights=fact['weights'], parent=parent)
    return NS(fact=fact, ledger=CurrentIDLedger({'logical.smd': fact}), obj=obj, mesh=mesh, model=model,
              parent=parent, payload=payload, early=early, late=late)


def observe(case, phase, **overrides):
    values = dict(phase=phase, model=case.model, name='logical.smd', model_start=10, model_count=3,
                  obj=case.obj, mesh=case.mesh, mapping=[0, 1, 2], payload=case.payload,
                  snapshot=case.early if phase in PHASES[:2] else case.late)
    values.update(overrides)
    case.ledger.observe(**values)


def complete(case):
    for phase in PHASES: observe(case, phase)


class CurrentIDTests(unittest.TestCase):
    def test_exact_new_creation_and_current_weight_rows_close_only_at_returned_refs(self):
        case = fixture()
        complete(case)
        report = case.ledger.returned(NS(objects=[case.obj], armature=case.parent), [(case.obj, case.late)])
        self.assertEqual((report['observed_new_points'], report['observed_new_corners']), (3, 3))
        self.assertTrue(report['current_exact_family_ordered_weight_storage_observed'])
        for key in ('historical_saved_B_native_causality_qualified', 'generic_weight_storage_qualified',
                    'native_normal_fidelity_qualified', 'carrier_or_exporter_binding_qualified',
                    'non_normal_semantic_equivalence_qualified', 'application_adoption_qualified'):
            self.assertFalse(report[key])
        self.assertNotIn('ids', report['models'][0])

    def test_boolean_and_float_mapping_values_refuse_despite_numeric_equality(self):
        for value in (True, 1.):
            case = fixture()
            with self.assertRaises(Refusal): observe(case, PHASES[0], mapping=[0, value, 2])

    def test_mapping_duplicate_or_reorder_is_not_repaired_by_matching_positions(self):
        for mapping in ([0, 0, 2], [1, 0, 2]):
            case = fixture()
            with self.assertRaises(Refusal): observe(case, PHASES[0], mapping=mapping)

    def test_native_raw_fixup_relation_cannot_alias_or_use_boolean(self):
        case = fixture()
        for raw in ((1, 1, 2), (True, 0, 2)):
            altered = dict(case.fact, raw_ids=raw)
            with self.assertRaises(Refusal): CurrentIDLedger({'logical.smd': altered})

    def test_source_selected_words_are_independent_of_current_geometry(self):
        case = fixture()
        altered = dict(case.payload, normals=fwords(0., 1., 0.) * 3)
        with self.assertRaises(Refusal): observe(case, PHASES[0], payload=altered)

    def test_source_negative_zero_is_not_collapsed_to_positive_zero(self):
        case = fixture()
        source = bytearray(case.payload['weights'])
        source[12:16] = fwords(0.)
        with self.assertRaises(Refusal): observe(case, PHASES[0], payload=dict(case.payload, weights=bytes(source)))

    def test_changed_current_position_words_refuse_without_tolerance(self):
        case = fixture()
        shifted = bytearray(case.early['positions'])
        shifted[0] ^= 1
        with self.assertRaises(Refusal): observe(case, PHASES[0], snapshot=dict(case.early, positions=bytes(shifted)))

    def test_changed_loop_order_refuses_without_index_zip_repair(self):
        case = fixture()
        with self.assertRaises(Refusal): observe(case, PHASES[0], snapshot=dict(case.early, loops=struct.pack('<3I', 0, 1, 2)))

    def test_actual_object_mesh_owner_change_refuses_even_with_equal_geometry(self):
        case = fixture()
        observe(case, PHASES[0])
        different_mesh = object()
        case.obj.data = different_mesh
        with self.assertRaises(Refusal): observe(case, PHASES[1], mesh=different_mesh)

    def test_distinct_model_reference_is_not_accepted_by_same_logical_name(self):
        case = fixture()
        observe(case, PHASES[0])
        with self.assertRaises(Refusal): observe(case, PHASES[1], model=object())

    def test_missing_reordered_and_replayed_phases_refuse(self):
        for phases in ((PHASES[1],), (PHASES[0], PHASES[2]), (PHASES[0], PHASES[0])):
            case = fixture()
            with self.assertRaises(Refusal):
                for phase in phases: observe(case, phase)

    def test_early_stage_weights_groups_or_parent_are_not_falsely_read_as_finished(self):
        for changed in (dict(groups=('root',)), dict(weights=(weight((0, 1.)), b'', b'')), dict(parent=NS(type='ARMATURE'))):
            case = fixture()
            with self.assertRaises(Refusal): observe(case, PHASES[0], snapshot=dict(case.early, **changed))

    def test_current_stored_weight_group_order_is_not_sorted_into_agreement(self):
        case = fixture()
        observe(case, PHASES[0]); observe(case, PHASES[1])
        changed = (weight((0, .25), (1, .75)), *case.late['weights'][1:])
        with self.assertRaises(Refusal): observe(case, PHASES[2], snapshot=dict(case.late, weights=changed))

    def test_current_last_replace_value_is_exact_not_summed_or_normalized(self):
        case = fixture()
        observe(case, PHASES[0]); observe(case, PHASES[1])
        changed = (weight((1, 1.25), (0, .25)), *case.late['weights'][1:])
        with self.assertRaises(Refusal): observe(case, PHASES[2], snapshot=dict(case.late, weights=changed))

    def test_group_name_order_and_late_parent_identity_must_remain_exact(self):
        case = fixture()
        observe(case, PHASES[0]); observe(case, PHASES[1])
        with self.assertRaises(Refusal): observe(case, PHASES[2], snapshot=dict(case.late, groups=('loose', 'root')))
        case = fixture()
        for phase in PHASES[:3]: observe(case, phase)
        with self.assertRaises(Refusal): observe(case, PHASES[3], snapshot=dict(case.late, parent=NS(type='ARMATURE')))

    def test_returned_container_cannot_substitute_equal_looking_new_object(self):
        case = fixture(); complete(case)
        replacement = NS(data=case.mesh)
        with self.assertRaises(Refusal):
            case.ledger.returned(NS(objects=[replacement], armature=case.parent), [(replacement, case.late)])

    def test_returned_container_requires_complete_stages_and_still_exact_weights(self):
        case = fixture(); observe(case, PHASES[0])
        with self.assertRaises(Refusal): case.ledger.returned(NS(objects=[case.obj], armature=case.parent), [(case.obj, case.late)])
        case = fixture(); complete(case)
        with self.assertRaises(Refusal):
            case.ledger.returned(NS(objects=[case.obj], armature=case.parent), [(case.obj, dict(case.late, weights=(b'', b'', b'')))])

    def test_closed_ledger_cannot_be_reused_or_relabelled(self):
        case = fixture(); complete(case)
        case.ledger.returned(NS(objects=[case.obj], armature=case.parent), [(case.obj, case.late)])
        with self.assertRaises(Refusal): observe(case, PHASES[0])

    def test_exact_word_admission_rejects_nonfinite_nonf32_and_boolean_values(self):
        for value in (float('nan'), float('inf'), .1, True):
            with self.assertRaises(Refusal): words([value], 'f')
        with self.assertRaises(Refusal): words([True], 'I')
        self.assertNotEqual(words([-0.], 'f'), words([0.], 'f'))


if __name__ == '__main__':
    unittest.main()

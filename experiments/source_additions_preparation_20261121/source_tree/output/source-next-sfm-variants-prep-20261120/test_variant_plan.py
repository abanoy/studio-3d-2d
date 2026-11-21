"""Authored pure schema/planning controls. No Blender/Godot/native assets.

Fixtures resemble glove and independent accessory choices only in cardinality;
they do not contain or qualify any supplied model, VMT, exported mapping or pixels.
"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import variant_plan as V


def glove():
    inventory = {'format': V.INVENTORY, 'asset_sha256': 'a' * 64, 'material_count': 3,
                 'mesh_nodes': [{'node': 10, 'parent_mesh': None, 'surface_materials': [0]}]}
    manifest = {'format': V.FORMAT, 'asset_sha256': 'a' * 64, 'default_skin': 0,
                'skins': [{'id': i, 'name': name} for i, name in enumerate(['Glove', 'Green', 'White'])],
                'groups': [{'id': 0, 'name': 'Glove', 'default': 0,
                            'choices': [{'id': 0, 'name': 'glove.smd', 'blank': False, 'nodes': [10]},
                                        {'id': 1, 'name': 'blank', 'blank': True, 'nodes': []}]}],
                'surfaces': [{'node': 10, 'surface': 0, 'materials': [0, 1, 2]}]}
    return manifest, inventory


def accessories():
    manifest, inventory = glove()
    inventory['mesh_nodes'] = [{'node': node, 'parent_mesh': None, 'surface_materials': [0]}
                               for node in [10, 20, 30]]
    manifest['groups'] = [{'id': i, 'name': name, 'default': 0,
                           'choices': [{'id': 0, 'name': name, 'blank': False, 'nodes': [node]},
                                       {'id': 1, 'name': '', 'blank': True, 'nodes': []}]}
                          for i, (node, name) in enumerate([(10, 'Tools'), (20, 'Box'), (30, 'Flame')])]
    manifest['surfaces'] = [{'node': node, 'surface': 0, 'materials': [0, 1, 2]} for node in [10, 20, 30]]
    return manifest, inventory


class VariantPlanTests(unittest.TestCase):
    def test_default_plan_is_explicit(self):
        m, i = glove(); s = V.default_selection(m, i); p = V.plan_selection(m, i, s)
        self.assertEqual(s, {'format': V.SELECTION, 'skin': 0, 'groups': {'0': 0}})
        self.assertEqual(p['visibility'], [{'node': 10, 'visible': True}])
        self.assertEqual(p['materials'], [{'node': 10, 'surface': 0, 'material': 0}])

    def test_three_skins_use_declared_material_ids(self):
        m, i = glove(); s = V.default_selection(m, i)
        for skin in [1, 2]:
            transition = V.plan_change(m, i, s, skin=skin)
            self.assertEqual(transition['after']['materials'][0]['material'], skin)
            self.assertEqual(transition['after']['visibility'], [{'node': 10, 'visible': True}])
            self.assertTrue(transition['changed'])

    def test_blank_hides_geometry_without_removing_it(self):
        m, i = glove(); before = copy.deepcopy((m, i))
        result = V.plan_change(m, i, V.default_selection(m, i), groups={'0': 1})
        self.assertEqual(result['after']['visibility'], [{'node': 10, 'visible': False}])
        self.assertEqual((m, i), before)
        self.assertEqual(len(i['mesh_nodes']), 1)

    def test_combined_skin_and_blank_are_one_plan(self):
        m, i = glove()
        p = V.plan_change(m, i, V.default_selection(m, i), skin=2, groups={'0': 1})
        self.assertEqual(p['before']['selection']['skin'], 0)
        self.assertEqual(p['after']['selection'], {'format': V.SELECTION, 'skin': 2, 'groups': {'0': 1}})
        self.assertEqual(p['after']['materials'][0]['material'], 2)
        self.assertFalse(p['after']['visibility'][0]['visible'])

    def test_independent_bodygroups_do_not_need_cartesian_exports(self):
        m, i = accessories()
        p = V.plan_change(m, i, V.default_selection(m, i), groups={'0': 1, '2': 1})
        self.assertEqual(p['after']['visibility'], [{'node': 10, 'visible': False},
                                                  {'node': 20, 'visible': True}, {'node': 30, 'visible': False}])
        self.assertEqual(len(i['mesh_nodes']), 3)

    def test_runtime_all_blank_is_valid_on_retained_asset(self):
        m, i = accessories()
        p = V.plan_change(m, i, V.default_selection(m, i), groups={'0': 1, '1': 1, '2': 1})
        self.assertTrue(all(row['visible'] is False for row in p['after']['visibility']))
        self.assertEqual(len(p['after']['materials']), 3)

    def test_skins_only_manifest_does_not_touch_visibility(self):
        m, i = glove(); m['groups'] = []
        p = V.plan_change(m, i, V.default_selection(m, i), skin=1)
        self.assertEqual(p['after']['visibility'], [])
        self.assertEqual(p['after']['materials'][0]['material'], 1)

    def test_ungrouped_mesh_stays_out_of_visibility_writes(self):
        m, i = glove()
        i['mesh_nodes'].append({'node': 99, 'parent_mesh': None, 'surface_materials': [1]})
        m['surfaces'].append({'node': 99, 'surface': 0, 'materials': [1, 2, 0]})
        p = V.plan_change(m, i, V.default_selection(m, i), skin=2)
        self.assertEqual([row['node'] for row in p['after']['visibility']], [10])
        self.assertEqual(p['after']['materials'][1], {'node': 99, 'surface': 0, 'material': 0})

    def test_labels_preserve_spaces_unicode_and_case(self):
        m, i = glove(); m['groups'][0]['name'] = ' Gloves 手袋 '
        self.assertEqual(V.validate_manifest(m, i)['groups'][0]['name'], ' Gloves 手袋 ')
        self.assertEqual(V.default_selection(m, i)['groups'], {'0': 0})

    def test_manifest_and_plan_are_detached(self):
        m, i = glove(); old = copy.deepcopy((m, i))
        clean = V.validate_manifest(m, i); clean['groups'][0]['choices'][0]['nodes'].clear()
        p = V.plan_selection(m, i, V.default_selection(m, i)); p['selection']['groups']['0'] = 1
        p['materials'][0]['material'] = 2
        self.assertEqual((m, i), old)

    def test_asset_mismatch_refuses(self):
        m, i = glove(); m['asset_sha256'] = 'b' * 64
        with self.assertRaisesRegex(V.Refusal, '^manifest_asset_mismatch$'): V.validate_manifest(m, i)

    def test_default_surface_must_match_actual_inventory(self):
        m, i = glove(); m['surfaces'][0]['materials'][0] = 2
        with self.assertRaisesRegex(V.Refusal, '^default_material_mismatch$'): V.validate_manifest(m, i)

    def test_every_surface_is_required(self):
        m, i = glove(); i['mesh_nodes'][0]['surface_materials'].append(1)
        with self.assertRaisesRegex(V.Refusal, '^surface_coverage$'): V.validate_manifest(m, i)

    def test_duplicate_surface_refuses(self):
        m, i = glove(); m['surfaces'].append(copy.deepcopy(m['surfaces'][0]))
        with self.assertRaisesRegex(V.Refusal, '^surface_duplicate$'): V.validate_manifest(m, i)

    def test_one_material_per_skin_required(self):
        m, i = glove(); m['surfaces'][0]['materials'].pop()
        with self.assertRaisesRegex(V.Refusal, '^surface_skin_count$'): V.validate_manifest(m, i)

    def test_foreign_material_index_refuses(self):
        m, i = glove(); m['surfaces'][0]['materials'][2] = 3
        with self.assertRaisesRegex(V.Refusal, '^surface_material$'): V.validate_manifest(m, i)

    def test_boolean_or_float_indices_are_not_integers(self):
        for value in [True, False, 1.0, -1]:
            m, i = glove(); m['surfaces'][0]['materials'][1] = value
            with self.subTest(value=value), self.assertRaises(V.Refusal): V.validate_manifest(m, i)

    def test_duplicate_choice_node_ownership_refuses(self):
        m, i = glove(); m['groups'][0]['choices'][1] = {'id': 1, 'name': 'Other', 'blank': False, 'nodes': [10]}
        with self.assertRaisesRegex(V.Refusal, '^choice_node_ownership$'): V.validate_manifest(m, i)

    def test_blank_name_does_not_mean_zero_geometry(self):
        m, i = glove(); m['groups'][0]['choices'][0]['name'] = 'blank'
        self.assertTrue(V.plan_selection(m, i, V.default_selection(m, i))['visibility'][0]['visible'])

    def test_true_blank_cannot_own_mesh_nodes(self):
        m, i = glove(); m['groups'][0]['choices'][0]['blank'] = True
        with self.assertRaisesRegex(V.Refusal, '^choice_blank_nodes$'): V.validate_manifest(m, i)

    def test_controlled_mesh_cannot_hide_a_different_mesh_descendant(self):
        m, i = glove(); i['mesh_nodes'].append({'node': 20, 'parent_mesh': 10, 'surface_materials': [0]})
        m['surfaces'].append({'node': 20, 'surface': 0, 'materials': [0, 1, 2]})
        with self.assertRaisesRegex(V.Refusal, '^controlled_mesh_has_mesh_descendant$'): V.validate_manifest(m, i)

    def test_parent_cycles_and_missing_mesh_parent_refuse(self):
        for parent in [10, 20]:
            m, i = glove(); i['mesh_nodes'][0]['parent_mesh'] = parent
            with self.subTest(parent=parent), self.assertRaisesRegex(V.Refusal, '^inventory_parent_graph$'):
                V.validate_manifest(m, i)

    def test_noncanonical_or_missing_selection_keys_refuse(self):
        m, i = glove()
        for groups in [{}, {'00': 0}, {'0': 0, '1': 0}, {0: 0}]:
            s = {'format': V.SELECTION, 'skin': 0, 'groups': groups}
            with self.subTest(groups=groups), self.assertRaises(V.Refusal): V.plan_selection(m, i, s)

    def test_invalid_combined_change_is_atomic(self):
        m, i = glove(); s = V.default_selection(m, i); old = copy.deepcopy((m, i, s))
        with self.assertRaisesRegex(V.Refusal, '^selection_choice$'): V.plan_change(m, i, s, skin=2, groups={'0': 99})
        self.assertEqual((m, i, s), old)

    def test_noop_and_returned_state_do_not_alias(self):
        m, i = glove(); s = V.default_selection(m, i)
        p = V.plan_change(m, i, s)
        self.assertFalse(p['changed']); self.assertEqual(p['before'], p['after'])
        p['after']['selection']['groups']['0'] = 1
        self.assertEqual(p['before']['selection']['groups']['0'], 0)
        self.assertEqual(s['groups']['0'], 0)

    def test_unknown_fields_and_formats_refuse(self):
        for key, value in [('unknown', 1), ('format', 'foreign')]:
            m, i = glove(); m[key] = value
            with self.subTest(key=key), self.assertRaises(V.Refusal): V.validate_manifest(m, i)

    def test_global_metadata_budget_refuses_complete_oversize_declaration(self):
        m, i = glove(); i['mesh_nodes'] = []; m['groups'] = []; m['surfaces'] = []
        for group in range(8):
            choices = []
            for choice in range(64):
                node = group * 64 + choice
                i['mesh_nodes'].append({'node': node, 'parent_mesh': None, 'surface_materials': [0]})
                choices.append({'id': choice, 'name': 'x' * 1024, 'blank': False, 'nodes': [node]})
                m['surfaces'].append({'node': node, 'surface': 0, 'materials': [0, 1, 2]})
            m['groups'].append({'id': group, 'name': 'group', 'default': 0, 'choices': choices})
        with self.assertRaisesRegex(V.Refusal, '^manifest_metadata_budget$'): V.validate_manifest(m, i)

    def test_inventory_material_count_is_bounded(self):
        m, i = glove(); i['material_count'] = 257
        with self.assertRaisesRegex(V.Refusal, '^inventory_material_count$'): V.validate_manifest(m, i)

    def test_duplicate_skin_rows_remain_distinct_numeric_choices(self):
        m, i = glove(); m['surfaces'][0]['materials'] = [0, 0, 0]
        p = V.plan_change(m, i, V.default_selection(m, i), skin=2)
        self.assertEqual(p['after']['selection']['skin'], 2)
        self.assertEqual(p['after']['materials'][0]['material'], 0)

    def test_surface_plan_order_is_deterministic(self):
        m, i = accessories(); expected = V.plan_selection(m, i, V.default_selection(m, i))
        i['mesh_nodes'].reverse(); m['surfaces'].reverse()
        self.assertEqual(V.plan_selection(m, i, V.default_selection(m, i)), expected)

    def test_planning_never_opens_files(self):
        m, i = glove()
        with patch('builtins.open', side_effect=AssertionError('unexpected IO')):
            self.assertTrue(V.plan_change(m, i, V.default_selection(m, i), skin=1)['changed'])


if __name__ == '__main__':
    unittest.main()

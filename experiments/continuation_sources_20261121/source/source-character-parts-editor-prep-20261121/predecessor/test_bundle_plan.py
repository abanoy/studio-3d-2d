"""Source-only pure planning controls; no SourceIO/assets/application execution."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('_exact_junko_bundle_plan', HERE/'bundle_plan.py')
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
AUDIT = json.loads((HERE/'BUNDLE_AUDIT.json').read_text(encoding='utf-8'))

def ids():
    return {role:'actor-'+role for role in P.ORDER}

def build(audit=None, actor_ids=None, **kwargs):
    options = dict(group_id='character-root', common_source_unit_scale=0.01905)
    options.update(kwargs)
    return P.build(copy.deepcopy(AUDIT) if audit is None else audit, ids() if actor_ids is None else actor_ids, **options)

def parts(plan):
    return {row['role']:row for row in plan['parts']}

class BundlePlanningTests(unittest.TestCase):
    def test_only_mdl_entrypoints_become_parts(self):
        paths=[row['mdl_relative'] for row in AUDIT['records']]
        result=P.primary_models(paths+['models/touhou/tamo/junko.vvd','models/touhou/tamo/junko.dx90.vtx','materials/char/body.vmt','materials/char/body.vtf'])
        self.assertEqual(tuple(result),P.ORDER)
        self.assertEqual(len(result),6)

    def test_case_preserved_after_unique_casefold_matching(self):
        paths=[row['mdl_relative'].replace('junko','Junko') for row in AUDIT['records']]
        self.assertEqual(set(P.primary_models(paths).values()),set(paths))

    def test_missing_model_is_not_replaced_by_sidecar(self):
        paths=[row['mdl_relative'] for row in AUDIT['records'] if row['role']!='hair']
        with self.assertRaisesRegex(P.Refusal,'all_six_primary_families_required'):
            P.primary_models(paths+['models/touhou/tamo/junko hair.vvd'])

    def test_unknown_seventh_model_requires_separate_review(self):
        paths=[row['mdl_relative'] for row in AUDIT['records']]
        with self.assertRaisesRegex(P.Refusal,'unknown_or_duplicate_primary_model'):
            P.primary_models(paths+['models/new-character.mdl'])

    def test_case_alias_refuses_before_part_selection(self):
        paths=[row['mdl_relative'] for row in AUDIT['records']]
        with self.assertRaisesRegex(P.Refusal,'case_ambiguous_input_path'):
            P.primary_models(paths+[paths[0].upper()])

    def test_one_inert_group_root_and_one_reference_scale(self):
        plan=build(root_reference_scale=1.5)
        self.assertEqual(plan['root']['kind'],'group')
        self.assertTrue(plan['root']['inert_group_asset_required'])
        self.assertEqual(plan['root']['reference_scale'],1.5)
        self.assertEqual(plan['root']['height_reference_role'],'body')
        self.assertEqual(plan['root']['height_reference_applied_to'],'bundle_root_only')
        self.assertTrue(all(row['parent_id']=='character-root' and row['relative_scale']==1 and row['individual_height_normalization']=='none' for row in plan['parts']))

    def test_default_does_not_overlay_three_outfits_or_mask(self):
        plan=build(); rows=parts(plan)
        self.assertEqual({role for role,row in rows.items() if row['visible']},{'body','hair'})
        self.assertTrue(plan['outfit_review_required'])
        self.assertEqual(len(rows),6)

    def test_explicit_dress_set_keeps_other_clothes_available_hidden(self):
        plan=build(outfit=['dress']); rows=parts(plan)
        self.assertEqual({role for role,row in rows.items() if row['visible']},{'body','hair','dress'})
        self.assertFalse(plan['outfit_review_required'])
        self.assertEqual(set(rows),set(P.EXPECTED))

    def test_explicit_reviewed_combination_is_not_reclassified(self):
        plan=build(outfit=['skirt','dress'])
        self.assertEqual(plan['reviewed_outfit'],['dress','skirt'])
        self.assertTrue(parts(plan)['dress']['visible'] and parts(plan)['skirt']['visible'])
        self.assertFalse(parts(plan)['miniskirt']['visible'])

    def test_explicit_no_outfit_is_a_complete_review(self):
        plan=build(outfit=[])
        self.assertFalse(plan['outfit_review_required'])
        self.assertTrue(all(not parts(plan)[role]['visible'] for role in P.OUTFITS))

    def test_mask_is_separate_optional_attachment(self):
        self.assertTrue(parts(build(show_mask=True))['mask']['visible'])
        with self.assertRaisesRegex(P.Refusal,'explicit_mask_visibility_required'):
            build(show_mask=1)

    def test_every_part_keeps_pose_morph_simulation_ownership(self):
        for row in build()['parts']:
            self.assertEqual((row['pose_owner'],row['morph_owner'],row['simulation_owner']),('self','self','self'))
            self.assertEqual(row['bone_following'],'none')

    def test_audit_ids_and_outfit_inputs_are_not_mutated(self):
        audit=copy.deepcopy(AUDIT); actor_ids=ids(); outfit=['skirt']
        old=copy.deepcopy((audit,actor_ids,outfit))
        build(audit,actor_ids,outfit=outfit)
        self.assertEqual((audit,actor_ids,outfit),old)

    def test_plan_output_has_no_live_reference_to_audit_or_ids(self):
        audit=copy.deepcopy(AUDIT); actor_ids=ids(); plan=build(audit,actor_ids)
        before=copy.deepcopy((audit,actor_ids))
        plan['parts'][0]['label']='edited'
        self.assertEqual((audit,actor_ids),before)
        with self.assertRaisesRegex(P.Refusal,'plan_changed'):
            P.validate(plan)

    def test_original_family_sha_cannot_be_substituted(self):
        audit=copy.deepcopy(AUDIT); audit['records'][0]['mdl_sha256']='0'*64
        with self.assertRaisesRegex(P.Refusal,'exact_source_family_required'):
            build(audit)

    def test_family_header_or_checksum_failure_cannot_plan(self):
        for field,value in [('family_checksums_match',False),('mdl_version',48),('vvd_version',3),('dx90_version',6)]:
            with self.subTest(field=field):
                audit=copy.deepcopy(AUDIT); audit['records'][0][field]=value
                with self.assertRaisesRegex(P.Refusal,'exact_source_family_required'):
                    build(audit)

    def test_unique_role_set_required(self):
        for role in ['unreviewed',[],None]:
            with self.subTest(role=repr(role)):
                audit=copy.deepcopy(AUDIT); audit['records'][0]['role']=role
                with self.assertRaisesRegex(P.Refusal,'unique_role_required'):
                    build(audit)
        audit=copy.deepcopy(AUDIT); audit['records'][0]['role']=audit['records'][1]['role']
        with self.assertRaises(P.Refusal): build(audit)

    def test_part_ids_and_group_id_must_be_complete_and_distinct(self):
        for changed in ['missing','duplicate','root_collision','path_id']:
            with self.subTest(changed=changed):
                actor_ids=ids(); group='character-root'
                if changed=='missing': actor_ids.pop('hair')
                elif changed=='duplicate': actor_ids['hair']=actor_ids['body']
                elif changed=='root_collision': group=actor_ids['body']
                else: actor_ids['hair']='other/scene'
                with self.assertRaises(P.Refusal): build(actor_ids=actor_ids,group_id=group)

    def test_explicit_unit_and_reference_scale_bounds(self):
        for name,values in [('common_source_unit_scale',[0,-1,True,float('nan'),float('inf'),1.01]),('root_reference_scale',[0,-1,True,float('nan'),1001])]:
            for value in values:
                with self.subTest(name=name,value=value):
                    with self.assertRaisesRegex(P.Refusal,'explicit_positive_common_units_required'):
                        build(**{name:value})

    def test_unreviewed_or_duplicate_outfit_values_refuse(self):
        for outfit in ['dress',['hair'],['dress','dress'],[True]]:
            with self.subTest(outfit=repr(outfit)):
                with self.assertRaises(P.Refusal): build(outfit=outfit)

    def test_outfit_switch_uses_only_three_existing_visibility_targets(self):
        plan=build(outfit=['dress']); before=copy.deepcopy(plan)
        operation=P.outfit_visibility_operations(plan,['miniskirt'],17)
        expected=[{'id':'actor-'+role,'visible':role=='miniskirt','frame':17} for role in P.OUTFITS]
        self.assertEqual(operation['operations'],expected)
        self.assertTrue(operation['one_existing_world_object_history_transaction_required'])
        self.assertFalse(operation['root_transform_changed'] or operation['pose_or_physics_changed'] or operation['asset_removed'] or operation['applied'])
        self.assertEqual(plan,before)

    def test_outfit_switch_requires_whole_bounded_frame_and_review(self):
        plan=build()
        for frame in [True,0.0,-1,1000001]:
            with self.subTest(frame=frame):
                with self.assertRaisesRegex(P.Refusal,'whole_visibility_frame_required'):
                    P.outfit_visibility_operations(plan,[],frame)
        with self.assertRaisesRegex(P.Refusal,'reviewed_outfit_required'):
            P.outfit_visibility_operations(plan,None,0)

    def test_exact_dress_rest_does_not_promote_bone_merge(self):
        pair=next(row for row in AUDIT['compatibility'] if row['a']=='junko dress' and row['b']=='junko')
        self.assertEqual(pair['shared_bones'],56)
        self.assertTrue(pair['strict_merge_candidates'])
        self.assertEqual(pair['shared_procedural_owner_count'],2)
        plan=build()
        self.assertFalse(plan['skeleton_merge_performed'] or plan['posed_bone_following_qualified'])
        self.assertTrue(all(row['bone_following']=='none' for row in plan['parts']))

    def test_same_skirt_names_do_not_override_rest_conflict(self):
        pair=next(row for row in AUDIT['compatibility'] if row['a']=='junko miniskirt' and row['b']=='junko skirt')
        self.assertEqual(pair['shared_bones'],136)
        self.assertEqual(pair['mismatch_counts']['local_rest_words'],135)
        self.assertFalse(pair['strict_merge_candidates'])

    def test_static_plan_does_not_claim_conversion_alignment_or_storage(self):
        plan=build()
        self.assertFalse(plan['same_source_origin_conversion_qualified'])
        self.assertFalse(plan['final_conversion_or_storage_qualified'])
        self.assertFalse(plan['application_adopted'])
        self.assertTrue(P.validate(plan))

if __name__=='__main__': unittest.main()

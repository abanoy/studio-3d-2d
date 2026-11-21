import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_lights import plan,plan_batches,MAX_LIGHTS
class LightTests(unittest.TestCase):
 def test_point_scale_color(self):
  a=plan([{'classname':'light','origin':'10 -20 30','_light':'255 128 0 200'}],.1)['lights'][0]
  self.assertEqual(a['position'],[1,-2,3]);self.assertEqual(a['type'],'POINT');self.assertAlmostEqual(a['energy'],200);self.assertEqual(a['color'][0],1);self.assertAlmostEqual(a['color'][1],.21586050011389926);self.assertEqual(a['color'][2],0)
 def test_pitch_and_sun(self):
  a=plan([{'classname':'light_environment','pitch':'-90'}],1)['lights'][0];self.assertEqual(a['type'],'SUN');self.assertAlmostEqual(a['direction'][2],-1);self.assertEqual(a['energy'],1)
 def test_spot(self):
  a=plan([{'classname':'light_spot','angles':'90 0 0','_cone':'40','_inner_cone':'20'}],1)['lights'][0];self.assertAlmostEqual(a['direction'][2],-1);self.assertAlmostEqual(a['spot_size'],math.radians(80));self.assertEqual(a['spot_blend'],.5)
 def test_off_and_style(self):
  a=plan([{'classname':'light','spawnflags':'1'},{'classname':'light','style':'4'}],1);self.assertFalse(a['lights']);self.assertEqual(len(a['warnings']),2)
 def test_unsupported_light_report(self):
  self.assertIn('unsupported',plan([{'classname':'light_dynamic'}],1)['warnings'][0])
 def test_other_entities_do_not_run(self):
  self.assertEqual(plan([{'classname':'logic_auto','OnMapSpawn':'dangerous'},{'classname':'worldspawn'}],1),{'lights':[],'warnings':[]})
 def test_count(self):
  self.assertEqual(len(plan([{'classname':'light'}]*MAX_LIGHTS,1)['lights']),MAX_LIGHTS)
  with self.assertRaisesRegex(ValueError,'64'):plan([{'classname':'light'}]*(MAX_LIGHTS+1),1)
 def test_malformed(self):
  for values in [{'_light':'nan 0 0 200'},{'_light':'256 0 0 200'},{'_light':'0 0 0 -1'},{'origin':'0 0'},{'angles':'inf 0 0'},{'_cone':'90.0001'},{'_inner_cone':'50','_cone':'40'},{'pitch':'bad'},{'style':'0.5'},{'spawnflags':'-1'}]:
   with self.subTest(values=values),self.assertRaises(ValueError):plan([{'classname':'light_spot',**values}],1)
 def test_inventory_scale(self):
  for scale in [0,-1,math.inf,True,'1']:
   with self.subTest(scale=scale),self.assertRaises(ValueError):plan([],scale)
  for entities in [{},[None]]:
   with self.assertRaises(ValueError):plan(entities,1)
 def test_ninety_degree_outer_boundary(self):
  a=plan([{'classname':'light_spot','_cone':'90','_inner_cone':'50'}],.01905)['lights'][0]
  self.assertEqual(a['spot_size'],math.pi);self.assertAlmostEqual(a['spot_blend'],1-50/90)
 def test_equal_inner_outer_is_unrepresentable(self):
  for outer in ['40','90']:
   with self.subTest(outer=outer),self.assertRaisesRegex(ValueError,'cone'):plan([{'classname':'light_spot','_cone':outer,'_inner_cone':outer}],1)
 def test_invalid_environment_remains_fatal_by_default(self):
  with self.assertRaisesRegex(ValueError,'color or brightness'):plan([{'classname':'light_environment','_light':'-1 -1 -1 -1','_lightHDR':'-1 -1 -1 1'}],.01905)
 def test_optional_environment_is_retained_and_visible_as_omission(self):
  import copy
  entities=[{'classname':'light_environment','_light':'-1 -1 -1 -1','_lightHDR':'-1 -1 -1 1'},{'classname':'light','origin':'0 0 0'}];before=copy.deepcopy(entities)
  a=plan(entities,.01905,optional_omissions=True)
  self.assertEqual(entities,before);self.assertEqual(len(a['lights']),1);self.assertEqual(a['omissions']['invalid'],1)
  self.assertTrue(any('raw entity' in warning and 'omitted' in warning for warning in a['warnings']))
 def test_105_light_inventory_keeps64_and_reports_every_omission(self):
  entities=[{'classname':'light_environment','_light':'-1 -1 -1 -1'}]+[{'classname':'light','targetname':str(i)} for i in range(104)]
  a=plan(entities,.01905,optional_omissions=True)
  self.assertEqual(len(a['lights']),64);self.assertEqual(a['omissions']['light_entities'],105);self.assertEqual(a['omissions']['invalid'],1);self.assertEqual(a['omissions']['budget'],40)
  self.assertTrue(any('global64' in warning for warning in a['warnings']));self.assertEqual(a['lights'][0]['name'],'0');self.assertEqual(a['lights'][-1]['name'],'63')
 def test_global_budget_across_multiple_entity_texts(self):
  batches=[[{'classname':'light','targetname':str(i)} for i in range(40)],[{'classname':'light','targetname':str(i)} for i in range(40,80)]]
  a=plan_batches(batches,.01905,optional_omissions=True)
  self.assertEqual(len(a['entities']),80);self.assertEqual(len(a['lights']),64);self.assertEqual(a['omissions']['budget'],16)
  self.assertEqual(a['entities'],batches[0]+batches[1]);self.assertEqual(len(batches[0]),40)
 def test_strict_multitext_budget_still_refuses(self):
  with self.assertRaisesRegex(ValueError,'64'):plan_batches([[{'classname':'light'}]*40,[{'classname':'light'}]*40],1)
 def test_remaining_budget_is_not_per_call_reset(self):
  a=plan([{'classname':'light'}]*4,1,optional_omissions=True,remaining_budget=2)
  self.assertEqual(len(a['lights']),2);self.assertEqual(a['omissions']['budget'],2)
  b=plan([{'classname':'light'}],1,optional_omissions=True,remaining_budget=0)
  self.assertFalse(b['lights']);self.assertEqual(b['omissions']['budget'],1)
 def test_structural_and_scale_malformed_stay_fatal_in_optional_mode(self):
  for entities in [{},[None],[{'classname':1}]]:
   with self.subTest(entities=entities),self.assertRaises(ValueError):plan(entities,1,optional_omissions=True)
  for scale in [0,-1,math.inf,True,'1']:
   with self.subTest(scale=scale),self.assertRaises(ValueError):plan([],scale,optional_omissions=True)
 def test_policy_and_budget_are_exact(self):
  for policy in [1,None,'yes']:
   with self.assertRaises(ValueError):plan([],1,optional_omissions=policy)
  for budget in [True,-1,65,1.5,'64']:
   with self.assertRaises(ValueError):plan([],1,remaining_budget=budget)
 def test_disabled_animated_and_unsupported_counts_visible(self):
  a=plan([{'classname':'light','spawnflags':'1'},{'classname':'light','style':'1'},{'classname':'env_projectedtexture'}],1,optional_omissions=True)
  self.assertFalse(a['lights']);self.assertEqual(a['omissions']['starts_off'],1);self.assertEqual(a['omissions']['animated_style'],1);self.assertEqual(a['omissions']['unsupported_type'],1);self.assertEqual(len(a['warnings']),3)
 def test_optional_cone_omission_does_not_clamp_or_modify(self):
  entities=[{'classname':'light_spot','_cone':'90.0001','_inner_cone':'30'}]
  a=plan(entities,1,optional_omissions=True)
  self.assertFalse(a['lights']);self.assertEqual(a['omissions']['invalid'],1);self.assertEqual(entities[0]['_cone'],'90.0001')
 def test_optional_notes_are_bounded_with_complete_counts(self):
  entities=[{'classname':'light_environment','_light':'-1 -1 -1 -1'} for _ in range(100)]+[{'classname':'light_'+('x'*5000)}]
  a=plan(entities,1,optional_omissions=True)
  self.assertEqual(a['omissions']['invalid'],100);self.assertEqual(a['omissions']['unsupported_type'],1)
  self.assertEqual(a['omissions']['warning_details_omitted'],69)
  self.assertEqual(len(a['warnings']),33);self.assertTrue(all(len(warning)<=800 for warning in a['warnings']))
  self.assertIn('additional per-light',a['warnings'][-1]);self.assertIn('entities.json',a['warnings'][-1])
 def test_optional_lightmap_wording_is_separate_from_static_light_conversion(self):
  optional=plan([{'classname':'light'}],1,optional_omissions=True)
  self.assertTrue(any('LDR brush lightmaps are reported separately' in warning for warning in optional['warnings']))
  self.assertFalse(any('Baked lightmaps, HDR/ambient' in warning for warning in optional['warnings']))
  self.assertTrue(any('Baked lightmaps, HDR/ambient' in warning for warning in plan([{'classname':'light'}],1)['warnings']))
 def test_unicode_note_json_bytes_are_bounded(self):
  import json
  entities=[{'classname':'light_environment','targetname':'\U0001f310'*160,'_light':'-1 -1 -1 -1'} for _ in range(40)]
  a=plan(entities,1,optional_omissions=True)
  details=[warning for warning in a['warnings'] if 'optional map light omitted' in warning]
  self.assertEqual(a['omissions']['invalid'],40)
  self.assertEqual(a['omissions']['warning_details_omitted'],40-len(details))
  self.assertLessEqual(sum(len(json.dumps(warning,ensure_ascii=True).encode('ascii')) for warning in details),32*1024)
  self.assertGreater(a['omissions']['warning_details_omitted'],0)
if __name__=='__main__':unittest.main()




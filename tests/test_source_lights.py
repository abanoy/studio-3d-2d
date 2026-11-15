import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_lights import plan,MAX_LIGHTS
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
  for values in [{'_light':'nan 0 0 200'},{'_light':'256 0 0 200'},{'_light':'0 0 0 -1'},{'origin':'0 0'},{'angles':'inf 0 0'},{'_cone':'90'},{'_inner_cone':'50','_cone':'40'},{'pitch':'bad'},{'style':'0.5'},{'spawnflags':'-1'}]:
   with self.subTest(values=values),self.assertRaises(ValueError):plan([{'classname':'light_spot',**values}],1)
 def test_inventory_scale(self):
  for scale in [0,-1,math.inf,True,'1']:
   with self.subTest(scale=scale),self.assertRaises(ValueError):plan([],scale)
  for entities in [{},[None]]:
   with self.assertRaises(ValueError):plan(entities,1)
if __name__=='__main__':unittest.main()

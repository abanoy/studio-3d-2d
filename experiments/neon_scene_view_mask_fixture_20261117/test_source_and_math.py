import ast,hashlib,json,math,unittest
from pathlib import Path
from palette_math import MASK,ALPHA,TOLERANCE,forward,recover,qualify
HERE=Path(__file__).resolve().parent

def unorm8(value):return math.floor(value*255)/255

class SourceAndMath(unittest.TestCase):
 def test_original_fixture_exact_inverse(self):
  old=(HERE/'original-scene_view_smoke.gd').read_bytes()
  new=(HERE/'scene_view_smoke.proposed.gd').read_bytes().decode().replace('\r\n','\n')
  start=new.index('# The unchanged model-color predicate below')
  end=new.index('func native_pixels() -> Image:',start)
  new=new[:start]+new[end:]
  added='\t\t\tvar sample: Dictionary=setup_sample(image,screen,scene,frame)\n\t\t\tpixel=sample.pixel\n\t\t\tcheck(sample.supported and sample.composite_ok,"independent raw scene texel matches the source-pinned display composition: "+sample.reason)\n'
  self.assertEqual(new.count(added),1);new=new.replace(added,'')
  new=new.replace(',"display_composition":sample','')
  self.assertEqual(new.replace('\n','\r\n').encode(),old)
 def test_wrapper_exact_additive_inverse(self):
  old=(HERE/'original-verify_scene_view.py').read_text(encoding="utf-8")
  new=(HERE/'verify_scene_view.proposed.py').read_text(encoding="utf-8")
  start=new.index('        if not headless:\n')
  end=new.index("        if not headless and os.name=='nt':",start)
  self.assertEqual(new[:start]+new[end:],old)
  ast.parse(new)
 def test_original_threshold_literal_retained_once(self):
  text=(HERE/'scene_view_smoke.proposed.gd').read_text(encoding="utf-8")
  self.assertEqual(text.count('check(pixel.g>.45 and pixel.b>.3,"actual shared-world scene pixels show the off-frame model at its native-projected location")'),1)
  self.assertIn('result.composite_ok=base.g>.45 and base.b>.3 and error<=COMPOSITE_TOLERANCE',text)
 def test_source_pin_contract(self):
  text=(HERE/'scene_view_smoke.proposed.gd').read_text(encoding="utf-8");pins=json.loads((HERE/'SOURCE_PINS.json').read_bytes())
  literal=text.split('const DISPLAY_SOURCE_PINS=',1)[1].split('\n',1)[0]
  self.assertEqual(json.loads(literal),pins)
  self.assertEqual(len(pins),5)
 def test_explicit_profile_refusals(self):
  text=(HERE/'scene_view_smoke.proposed.gd').read_text(encoding="utf-8")
  for literal in ['unsupported palette','unsupported renderer or HDR2D','unsupported screen scaling or fractional translation','unsupported root viewport scaling','unsupported canvas modulation','unsupported scene texture modulation','unsupported scene texture mapping','sample touches a scene or mask boundary','unsupported readback extent or pixel format','unsupported translucent scene or screen sample','unsupported scene overlays at source sampling boundary']:
   self.assertIn(literal,text)
  self.assertIn('result.reason=reason;return result',text)
  self.assertIn('result:={"supported":false',text)
 def test_source_mask_and_tolerance_exact(self):
  text=(HERE/'scene_view_smoke.proposed.gd').read_text(encoding="utf-8")
  self.assertIn('const SETUP_MASK=Color(4/255.,5/255.,8/255.,.62)',text)
  self.assertIn('const COMPOSITE_TOLERANCE=2./255.',text)
  self.assertNotIn('clampf(',text);self.assertNotIn('.srgb_to_linear(',text)
 def test_exact_analytical_inverse(self):
  for base in [(0,.7,.6),(.47,.77,.73),(1,1,1)]:
   for actual,expected in zip(recover(forward(base,True),True),base):self.assertAlmostEqual(actual,expected,places=14)
 def test_classic_is_exact_identity(self):
  base=(.47,.77,.73);self.assertEqual(forward(base,False),base);self.assertEqual(recover(base,False),base);self.assertTrue(qualify(base,base,False))
 def test_teal_masked_display_uses_strict_base_threshold(self):
  base=(121/255,198/255,189/255);pixel=tuple(unorm8(v) for v in forward(base,True))
  self.assertFalse(pixel[1]>.45 and pixel[2]>.3)
  self.assertTrue(qualify(base,pixel,True))
 def test_two_unorm8_writes_bound(self):
  for channel in range(3):
   for index in range(4097):
    original=index/4096;first=unorm8(original);last=unorm8((1-ALPHA)*first+ALPHA*MASK[channel])
    ideal=(1-ALPHA)*original+ALPHA*MASK[channel]
    self.assertLessEqual(abs(last-ideal),((1-ALPHA)+1)/255+1e-15)
    self.assertLess(abs(last-ideal),TOLERANCE)
 def test_missing_model_rejected(self):
  base=(.035,.045,.065);self.assertFalse(qualify(base,forward(base,True),True))
 def test_wrong_display_pixel_rejected(self):
  base=(.47,.77,.73)
  self.assertFalse(qualify(base,(.035,.045,.065),True))
 def test_missing_mask_rejected(self):
  base=(.47,.77,.73);self.assertFalse(qualify(base,base,True))
 def test_wrong_color_space_rejected(self):
  base=(.47,.77,.73);linear=tuple(pow(x,2.2) for x in base)
  pixel=tuple(pow(x,1/2.2) for x in forward(linear,True))
  self.assertFalse(qualify(base,pixel,True))
 def test_no_threshold_relaxation(self):
  for base in [(.8,.45,.8),(.8,.8,.3),(.8,.449,.8),(.8,.8,.299)]:
   self.assertFalse(qualify(base,forward(base,True),True))
 def test_source_threshold_blocks_quantization_promotion(self):
  base=(.7,.45,.31);pixel=list(forward(base,True));pixel[1]+=1/255
  self.assertGreater(recover(pixel,True)[1],.45)
  self.assertFalse(qualify(base,pixel,True))
 def test_recovered_threshold_still_required(self):
  base=(.7,.451,.6);pixel=list(forward(base,True));pixel[1]-=1/255
  self.assertLess(recover(pixel,True)[1],.45)
  self.assertFalse(qualify(base,pixel,True))
 def test_tolerance_boundary_not_widened(self):
  base=(.47,.77,.73);pixel=list(forward(base,True));pixel[0]+=TOLERANCE+1e-9
  self.assertFalse(qualify(base,pixel,True))
 def test_nonfinite_refused(self):
  for value in [float('inf'),float('-inf'),float('nan')]:self.assertFalse(qualify((value,.7,.6),(.2,.3,.4),True))
 def test_pixel_center_maps_same_positive_texel(self):
  for point in [(43.2,190.8),(361.7,58.9)]:
   texel=tuple(int(x)+.5 for x in point)
   self.assertEqual(tuple(int(x) for x in texel),tuple(int(x) for x in point))
if __name__=='__main__':unittest.main()

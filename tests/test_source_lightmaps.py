"""Static BSP lightmap bounds, face identity, exact UV projection and atlas isolation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,struct
from types import SimpleNamespace
from unittest import TestCase
from tools.source_lightmaps import affine,face_info,key,shelves,tag_glb

class LightmapTests(TestCase):
 def face(self,**changes):
  values=dict(lightmap_width=1,lightmap_height=1,light_offset=0,styles=(0,-1,-1,-1),lightmap_texture_mins_in_luxels=(2,3));values.update(changes);return SimpleNamespace(**values)
 def test_signed_style_terminator_and_bounds(self):
  row,why=face_info(self.face(),16);self.assertEqual(why,'');self.assertEqual((row['width'],row['height'],row['offset']),(2,2,0))
 def test_styled_missing_and_truncated_samples_are_explicit(self):
  for change,reason in [({'styles':(1,255,255,255)},'styled'),({'styles':(0,2,255,255)},'styled'),({'light_offset':-1},'no static'),({'light_offset':1},'bounds'),({'light_offset':4},'bounds'),({'lightmap_width':2048},'bounds')]:
   row,why=face_info(self.face(**change),16);self.assertIsNone(row);self.assertIn(reason,why)
 def test_face_identity_matches_winding_and_float32_mesh_storage(self):
  points=[(0,0,0),(.1,0,0),(0,.1,0)];self.assertEqual(key(points),key(list(reversed(points))));self.assertNotEqual(key(points),key([(0,0,0),(.2,0,0),(0,.1,0)]))
 def test_affine_retains_repeated_rotated_material_uvs(self):
  pts=[(0,0),(2,0),(2,3),(0,3)];uv=[(2,3),(2,7),(-1,7),(-1,3)];rows=affine(pts,uv)
  for point,expected in zip(pts,uv):self.assertEqual(tuple(a*point[0]+b*point[1]+c for a,b,c in rows),expected)
 def test_ambiguous_and_nonplanar_uvs_refuse(self):
  for pts,uv in [([(0,0),(0,0),(0,0)],[(0,0),(1,0),(0,1)]), ([(0,0),(1,0),(1,1),(0,1)],[(0,0),(1,0),(1,1),(.2,1)])]:
   with self.assertRaises(ValueError):affine(pts,uv)
 def test_padded_atlas_cells_do_not_overlap_and_overflow_is_explicit(self):
  sizes=[(5,4),(8,4),(40,40),(10,10)];places,height=shelves(sizes,32);self.assertIsNone(places[2]);self.assertLessEqual(height,32);rect=[]
  for pos,(w,h) in zip(places,sizes):
   if pos is None:continue
   x,y=pos;box=(x-2,y-2,x+w+2,y+h+2)
   self.assertTrue(all(box[2]<=b[0] or b[2]<=box[0] or box[3]<=b[1] or b[3]<=box[1] for b in rect));rect.append(box)

 def test_emitted_tag_preserves_binary_chunk_and_existing_metadata(self):
  with TemporaryDirectory() as folder:
   path=Path(folder)/'scene.glb';doc={'materials':[{'name':'base'},{'name':'baked','extras':{'original':'kept'}}]};text=json.dumps(doc).encode();text+=b' '*((-len(text))%4);tail=struct.pack('<II',4,0x004e4942)+b'abcd';path.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(text)+len(tail),len(text),0x4e4f534a)+text+tail)
   tag_glb(path,['baked']);blob=path.read_bytes();n=struct.unpack_from('<I',blob,12)[0];actual=json.loads(blob[20:20+n]);self.assertEqual(blob[20+n:],tail);self.assertEqual(actual['materials'][0],doc['materials'][0]);self.assertEqual(actual['materials'][1]['extras']['original'],'kept');self.assertEqual(actual['materials'][1]['extras']['has_static_source_lightmap'],'studio_source_lightmaps_1')
 def test_missing_emitted_material_refuses_without_mutation(self):
  with TemporaryDirectory() as folder:
   path=Path(folder)/'scene.glb';text=b'{"materials":[]} ';blob=struct.pack('<4sIIII',b'glTF',2,20+len(text),len(text),0x4e4f534a)+text;path.write_bytes(blob)
   with self.assertRaisesRegex(ValueError,'identify'):tag_glb(path,['missing'])
   self.assertEqual(path.read_bytes(),blob)

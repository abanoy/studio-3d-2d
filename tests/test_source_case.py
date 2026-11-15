from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
import hashlib
from unittest.mock import patch
from tools.source_case import CaseResolver,sidecars

class SourceCaseTests(TestCase):
 def setUp(self):self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_mixed_directory_and_file_case_preserves_original(self):
  path=self.root/'Materials'/'TouHou'/'Reimu.VMT';path.parent.mkdir(parents=True);path.write_bytes(b'original');before=hashlib.sha256(path.read_bytes()).hexdigest();r=CaseResolver(self.root);self.assertEqual(r.find('materials/touhou/reimu.vmt'),path);self.assertEqual(r.find('MATERIALS\\TOUHOU\\REIMU.vmt'),path);self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
 def test_actual_sidecar_case_is_found_without_renaming_source(self):
  mdl=self.root/'byakuren hijiri_default.mdl';mdl.write_bytes(b'MDL');side=self.root/'byakuren Hijiri_default.dx90.vtx';side.write_bytes(b'VTX');self.assertEqual(sidecars(mdl),{'.dx90.vtx':side});self.assertTrue(side.exists());self.assertEqual({p.name for p in self.root.iterdir()},{mdl.name,side.name})
 def test_ambiguous_names_refuse_even_exact_spelling(self):
  (self.root/'eye.vtf').write_bytes(b'a');(self.root/'Eye.vtf').write_bytes(b'b')
  if len(list(self.root.iterdir()))!=2:self.skipTest('Filesystem is case-insensitive')
  for value in ['eye.vtf','Eye.vtf','EYE.VTF']:
   with self.assertRaisesRegex(ValueError,'Ambiguous'):CaseResolver(self.root).find(value)
 def test_escapes_and_absolute_paths_refuse(self):
  r=CaseResolver(self.root)
  for value in ['../x','a/../x','/etc/passwd','C:/x','a//b','a/','./x','']:
   with self.assertRaisesRegex(ValueError,'Unsafe'):r.find(value)
 def test_external_symlink_is_not_a_dependency(self):
  outside=self.root.parent/(self.root.name+'-external');outside.write_bytes(b'protected');self.addCleanup(outside.unlink)
  try:(self.root/'link.vtf').symlink_to(outside)
  except OSError as error:self.skipTest('Symbolic links unavailable: '+str(error))
  with self.assertRaisesRegex(ValueError,'escaped'):CaseResolver(self.root).find('LINK.VTF')
  self.assertEqual(outside.read_bytes(),b'protected')
 def test_missing_resource_is_none_and_cache_observes_new_names(self):
  r=CaseResolver(self.root);self.assertIsNone(r.find('absent.vmt'));p=self.root/'Absent.VMT';p.write_bytes(b'new');self.assertEqual(r.find('absent.vmt'),p);p.unlink();self.assertIsNone(r.find('absent.vmt'))
 def test_directory_is_not_returned_as_file(self):
  (self.root/'Materials').mkdir();self.assertIsNone(CaseResolver(self.root).find('materials'))

 def test_total_cached_name_budget_refuses_without_scanning_unbounded_trees(self):
  for name in ['A','B']:
   (self.root/name).mkdir();(self.root/name/'file.vtf').write_bytes(b'original')
  with patch('tools.source_case.MAX_NAMES',3):
   resolver=CaseResolver(self.root);self.assertIsNotNone(resolver.find('a/FILE.VTF'))
   with self.assertRaisesRegex(ValueError,'cached names'):resolver.find('b/file.vtf')

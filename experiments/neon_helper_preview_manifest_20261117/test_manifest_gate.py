"""CPU-only calls to unchanged source-extracted production validate_port.

No import of the whole driver, launch function, process or engine capability.
"""
import ast,copy,hashlib,json,stat,tempfile,unittest
from pathlib import Path,PureWindowsPath
HERE=Path(__file__).resolve().parent
SOURCE=json.loads((HERE/'SOURCE_INPUTS.json').read_bytes())
ORIGINAL=(HERE/'original-candidate-helper_preview_port_files.json').read_bytes()
PROPOSED=(HERE/'helper_preview_port_files.proposed.json').read_bytes()
NAMESPACE={'Path':Path,'PureWindowsPath':PureWindowsPath,'hashlib':hashlib,'json':json,'stat':stat}
source=(HERE/'verify_helper_preview.original.py').read_bytes()
assert hashlib.sha256(source).hexdigest()==json.loads((HERE/'SOURCE_PROOF.json').read_bytes())['driver_sha256']
parsed=ast.parse(source)
functions={'require','relative','owned','validate_port'};assignments={'RUNTIME_FILES','TEST_FILES'}
nodes=[]
for node in parsed.body:
 if isinstance(node,ast.FunctionDef) and node.name in functions:nodes.append(node)
 elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in node.targets):nodes.append(node)
assert {n.name for n in nodes if isinstance(n,ast.FunctionDef)}==functions
assert len(nodes)==6
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<unchanged pinned helper manifest gate>','exec'),NAMESPACE)
validate=NAMESPACE['validate_port']
SCRATCH=HERE/'cpu-scratch'

class ManifestGate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inputs={}
  root=Path(SOURCE['checkout'])
  for name,row in SOURCE['sources'].items():
   raw=(root/name).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['raw_sha256'];cls.inputs[name]=raw
  SCRATCH.mkdir(exist_ok=True)
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='case-',dir=str(SCRATCH))
  self.root=Path(self.temp.name).resolve();assert self.root.is_relative_to(SCRATCH.resolve())
  def cleanup():
   assert self.root.is_relative_to(SCRATCH.resolve()) and self.root!=SCRATCH.resolve()
   assert not self.root.is_symlink() and not getattr(self.root.lstat(),'st_file_attributes',0)&0x400
   self.temp.cleanup()
  self.addCleanup(cleanup)
  for name,raw in self.inputs.items():
   path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  (self.root/'tests/helper_preview_port_files.json').write_bytes(PROPOSED)
 def manifest(self,value):
  (self.root/'tests/helper_preview_port_files.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
 def mutate(self,name,suffix=b'\n# CPU tamper\n'):
  p=self.root/name;p.write_bytes(p.read_bytes()+suffix)
 def test_original_manifest_reproduces_closed_stale_pin_refusal(self):
  (self.root/'tests/helper_preview_port_files.json').write_bytes(ORIGINAL)
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,True)
 def test_proposed_25_sources_admit_only_reviewed_bytes_with_explicit_EOL(self):
  proof=validate(self.root,True);self.assertEqual(len(proof),25)
  self.assertEqual(set(proof),set(self.inputs))
  self.assertEqual(proof['src/app.gd']['reconstruction'],'exact bytes')
  self.assertEqual(proof['src/pose_editor.gd']['reconstruction'],'exact bytes')
 def test_no_EOLOptIn_remains_required_for_other23rows(self):
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/physics_editor.gd'):validate(self.root,False)
 def test_LF_variants_admit_only_with_existing_explicit_policy(self):
  for name in self.inputs:
   p=self.root/name;p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
  proof=validate(self.root,True);self.assertEqual(len(proof),25)
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,False)
 def test_changed_app_content_refuses_even_with_EOL(self):
  self.mutate('src/app.gd')
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,True)
 def test_changed_pose_content_refuses_even_with_EOL(self):
  self.mutate('src/pose_editor.gd')
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/pose_editor.gd'):validate(self.root,True)
 def test_untouched_runtime_row_content_refuses(self):
  self.mutate('src/secondary_helper_editor.gd')
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/secondary_helper_editor.gd'):validate(self.root,True)
 def test_untouched_test_driver_row_content_refuses(self):
  self.mutate('tests/verify_helper_preview.py')
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: tests/verify_helper_preview.py'):validate(self.root,True)
 def test_false_LF_pin_refuses_when_LF_branch_is_exercised(self):
  p=self.root/'src/app.gd';p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
  doc=json.loads(PROPOSED);doc['files'][0]['lf_sha256']='0'*64;self.manifest(doc)
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,True)
 def test_wrong_raw_and_LF_pins_refuse(self):
  doc=json.loads(PROPOSED);doc['files'][0]['sha256']='0'*64;doc['files'][0]['lf_sha256']='0'*64;self.manifest(doc)
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,True)
 def test_lone_CR_is_not_normalized_away(self):
  self.mutate('src/app.gd',b'\r')
  with self.assertRaisesRegex(RuntimeError,'Unreviewed helper main bytes: src/app.gd'):validate(self.root,True)
 def test_missing_required_manifest_member_refuses(self):
  doc=json.loads(PROPOSED);doc['files']=[row for row in doc['files'] if row['path']!='src/pending_helper_preview.gd'];self.manifest(doc)
  with self.assertRaisesRegex(RuntimeError,'omits required'):validate(self.root,True)
 def test_duplicate_manifest_member_refuses(self):
  doc=json.loads(PROPOSED);doc['files'].append(copy.deepcopy(doc['files'][0]));self.manifest(doc)
  with self.assertRaisesRegex(RuntimeError,'Repeated reviewed port source'):validate(self.root,True)
 def test_missing_source_file_refuses(self):
  p=self.root/'src/app.gd';assert p.resolve().is_relative_to(self.root);p.unlink()
  with self.assertRaisesRegex(RuntimeError,'Missing reviewed helper main source'):validate(self.root,True)
 def test_unsafe_manifest_path_refuses(self):
  for value in ['../escape.gd','C:/escape.gd','src\\app.gd','src/x:stream.gd']:
   doc=json.loads(PROPOSED);doc['files'][0]['path']=value;self.manifest(doc)
   with self.assertRaises(RuntimeError):validate(self.root,True)
 def test_unknown_manifest_format_refuses(self):
  doc=json.loads(PROPOSED);doc['format']='unreviewed';self.manifest(doc)
  with self.assertRaisesRegex(RuntimeError,'Invalid reviewed helper port manifest'):validate(self.root,True)
 def test_exact_four_hash_string_changes_have_byte_exact_inverse(self):
  proof=json.loads((HERE/'SOURCE_PROOF.json').read_bytes());result=PROPOSED
  for row in proof['changed_rows']:
   begin=result.index(('"path": "'+row['path']+'"').encode());end=result.index(b'\n    }',begin);block=result[begin:end]
   for field,old,new in [('sha256','old_sha256','new_sha256'),('lf_sha256','old_lf_sha256','new_lf_sha256')]:
    needle=('"'+field+'": "'+row[new]+'"').encode();replacement=('"'+field+'": "'+row[old]+'"').encode();self.assertEqual(block.count(needle),1);block=block.replace(needle,replacement)
   result=result[:begin]+block+result[end:]
  self.assertEqual(result,ORIGINAL)
 def test_manifest_metadata_membership_and23rows_are_exact(self):
  before=json.loads(ORIGINAL);after=json.loads(PROPOSED)
  self.assertEqual([r['path'] for r in before['files']],[r['path'] for r in after['files']]);self.assertEqual(len(after['files']),25)
  for old,new in zip(before['files'],after['files']):
   if old['path'] in ('src/app.gd','src/pose_editor.gd'):
    self.assertEqual({k:v for k,v in old.items() if k not in ('sha256','lf_sha256')},{k:v for k,v in new.items() if k not in ('sha256','lf_sha256')})
   else:self.assertEqual(old,new)
  before.pop('files');after.pop('files');self.assertEqual(before,after)

if __name__=='__main__':unittest.main()

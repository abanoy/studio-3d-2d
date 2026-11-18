"""Source/synthetic IO only; actual activation, Git and native reads forbidden."""
from pathlib import Path
import copy,json,tempfile,unittest
from unittest.mock import patch
import qualified_inputs as Q
import admission_core as A
HERE=Path(__file__).resolve().parent

class FutureAdapter(unittest.TestCase):
 def test_None_activation_refuses_before_qualification_functional_Git_or_copy(self):
  with patch.object(Path,'read_bytes',side_effect=AssertionError('external read')),patch.object(Q.subprocess,'check_output',side_effect=AssertionError('Git called')):
   with self.assertRaisesRegex(ValueError,'UNREADY'):Q.require_qualified_inputs()
 def test_token_cannot_be_forged_or_created_while_unready(self):
  fake=Q.Admitted({},object(),'0'*64)
  with patch.object(Q.subprocess,'check_output',side_effect=AssertionError('Git called')):
   with self.assertRaises(ValueError):Q.assert_admitted(fake)
   with self.assertRaisesRegex(ValueError,'UNREADY'):Q._admitted({})
 def test_committed_name_policy_rejects_windows_escapes_and_aliases(self):
  for name in ['../x','C:/x','/x','a\\x','a/x:stream','a/NUL.txt','a/COM¹.log','a/trailing.','a/trailing ','a//x','a/./x','a/<x>']:
   with self.subTest(name=name),self.assertRaises(ValueError):Q.validate_git_name(name)
  self.assertEqual(Q.validate_git_name('docs/licenses.md'),['docs','licenses.md'])
 def test_owner_archive_exclusion_retains_old_default(self):
  for name in ['output/a','.git/a','.godot/a','a/__pycache__/x','a/x.pyc']:self.assertFalse(Q.archive_included(name))
  for name in ['dependencies.json','docs/licenses.md','experiments/public_source.py']:self.assertTrue(Q.archive_included(name))
 def test_historical_raw_reconstruction_is_exact_and_explicit(self):
  blobs={'src/f%04d.gd'%i:b'authored\n' for i in range(1019)}
  manifest={'source_sha256':{n:A.digest(b'authored\r\n') for n in blobs}}
  recipe={n:{'mode':'explicit_canonical_LF_to_CRLF','git_blob_sha256':A.digest(v),'tested_working_sha256':manifest['source_sha256'][n],'canonical_content_sha256':A.digest(v)} for n,v in blobs.items()}
  out=Q.reconstruct_historical52(blobs,manifest,recipe);self.assertTrue(all(v==b'authored\r\n' for v in out.values()))
  wrong=copy.deepcopy(recipe);wrong['src/f0000.gd']['mode']='automatic'
  with self.assertRaises(ValueError):Q.reconstruct_historical52(blobs,manifest,wrong)
  wrong=copy.deepcopy(recipe);wrong['src/f0000.gd']['tested_working_sha256']='0'*64
  with self.assertRaises(ValueError):Q.reconstruct_historical52(blobs,manifest,wrong)
 def test_mixed_historical_EOL_mask_preserves_each_newline_and_exact_target(self):
  blob=b'one\ntwo\nthree\n';raw=b'one\r\ntwo\nthree\r\n'
  mode=Q.infer_historical_eol_mode(blob,raw,'src/f0000.gd');self.assertEqual(mode,'explicit_per_newline_CRLF_mask:3:05')
  blobs={'src/f%04d.gd'%i:blob for i in range(1019)};manifest={'source_sha256':{n:A.digest(raw) for n in blobs}}
  recipe={n:{'mode':mode,'git_blob_sha256':A.digest(blob),'tested_working_sha256':A.digest(raw),'canonical_content_sha256':A.digest(blob)} for n in blobs}
  self.assertTrue(all(v==raw for v in Q.reconstruct_historical52(blobs,manifest,recipe).values()))
  for wrong in ['explicit_per_newline_CRLF_mask:4:05','explicit_per_newline_CRLF_mask:3:85','explicit_per_newline_CRLF_mask:3:xx']:
   changed=copy.deepcopy(recipe);changed['src/f0000.gd']['mode']=wrong
   with self.assertRaises(ValueError):Q.reconstruct_historical52(blobs,manifest,changed)
  with self.assertRaises(ValueError):Q.infer_historical_eol_mode(blob,b'content changed\n','src/f.gd')
 def test_historical_nontext_or_missing_member_transform_refuses(self):
  blobs={'src/f%04d.gd'%i:b'authored\n' for i in range(1019)};blobs['data/a.png']=blobs.pop('src/f0000.gd')
  manifest={'source_sha256':{n:A.digest(b'authored\r\n') for n in blobs}}
  recipe={n:{'mode':'explicit_canonical_LF_to_CRLF','git_blob_sha256':A.digest(v),'tested_working_sha256':manifest['source_sha256'][n],'canonical_content_sha256':A.digest(v)} for n,v in blobs.items()}
  with self.assertRaises(ValueError):Q.reconstruct_historical52(blobs,manifest,recipe)
  recipe.pop('data/a.png')
  with self.assertRaises(ValueError):Q.reconstruct_historical52(blobs,manifest,recipe)
 def test_Git_proxy_admits_only_read_commands_and_pins_tool_before_after(self):
  identity={'bytes':1,'mtime_ns':1,'sha256':'1'*64};H={'identity':lambda _:identity};G=Q.ApprovedGit(H,Path(r'C:\synthetic\git.exe'),identity)
  with patch.object(Q.subprocess,'check_output',return_value='fake') as run:
   self.assertEqual(G.check_output(['git','rev-parse','HEAD'],cwd=Q.ROOT,text=True),'fake')
   args,opts=run.call_args;self.assertIn('--no-optional-locks',args[0]);self.assertEqual(opts['env']['GIT_OPTIONAL_LOCKS'],'0');self.assertEqual(opts['timeout'],120)
  for args in [['git','reset','--hard'],['other','diff'],['git','status']]:
   with patch.object(Q.subprocess,'check_output',side_effect=AssertionError('Git called')):
    with self.assertRaises(ValueError):G.check_output(args,cwd=Q.ROOT)
  with patch.object(Q.subprocess,'check_output',side_effect=AssertionError('Git called')):
   with self.assertRaises(ValueError):G.check_output(['git','diff','HEAD'],cwd=Q.ROOT.parent)
 def test_historical_full_roles_missing_refuse_before_file_reads(self):
  with self.assertRaises(ValueError):Q._historical52_proof({}, {}, {})

class OriginalNativeBridge(unittest.TestCase):
 def source(self):
  original={'src/f%04d.gd'%i:('old%d\n'%i).encode() for i in range(1005)}
  original.update({'src/model.gd':b'model\n','src/source_bone_bindings.gd':b'bindings\n','src/scene3d.gd':b'scene\n'})
  new=dict(original)
  for i in range(9):new['src/f%04d.gd'%i]=('changed%d\n'%i).encode()
  for i in range(11):new['src/added%02d.gd'%i]=('new%d\n'%i).encode()
  native={'passed':True,'preservation':{'source':True},'source_before':{'files':{n:{'sha256':A.digest(v)} for n,v in original.items()}}}
  rows=[]
  for name,b in new.items():
   a=original.get(name)
   if a==b:continue
   rows.append({'path':name,'old_native_sha256':A.digest(a) if a is not None else None,'old_content_sha256':A.digest(a) if a is not None else None,'new_working_sha256':A.digest(b),'new_content_sha256':A.digest(b)})
  return native,original,new,{'changed_or_added':rows,'unchanged_core':['src/model.gd','src/source_bone_bindings.gd','src/scene3d.gd']}
 def test_original1008_to52_1019_exact20_bridge_remains_checked(self):
  result=Q.validate_native52_byte_bridge(*self.source());self.assertEqual(result['explicit_changed_added'],20);self.assertEqual(result['old_native_files'],1008)
 def test_original_bytes_or_delta_or_unchanged_core_tamper_refuses(self):
  for change in [lambda v:v[1].update({'src/model.gd':b'wrong'}),lambda v:v[2].update({'src/model.gd':b'changed core'}),lambda v:v[3]['changed_or_added'].pop(),lambda v:v[3]['changed_or_added'][0].update(new_content_sha256='0'*64)]:
   args=list(self.source());change(args)
   with self.assertRaises(ValueError):Q.validate_native52_byte_bridge(*args)

class BoundedCatalogue(unittest.TestCase):
 def source(self):
  body=b'authored support\n';oid=b'1'*40;row={'mode':'100644','git_oid':oid.decode(),'bytes':len(body),'sha256':A.digest(body)}
  declared={'format':'has_neon_owner_committed_archive_catalogue_1','revision':'a'*40,'files':{'docs/licenses.md':row}}
  responses=[b'100644 blob '+oid+b'\tdocs/licenses.md\0',oid+b' blob '+str(len(body)).encode()+b'\n',oid+b' blob '+str(len(body)).encode()+b'\n'+body+b'\n']
  class Git:
   def check_output(self,*args,**opts):return responses.pop(0)
  return Git(),declared,responses
 def test_exact_committed_support_blob_catalogue(self):
  G,d,_=self.source();blobs,proof=Q.read_committed_archive(G,'a'*40,d);self.assertEqual(blobs,{'docs/licenses.md':b'authored support\n'});self.assertEqual(proof['files'],1)
 def test_catalogue_membership_hash_mode_or_size_refuses(self):
  for field,value in [('sha256','0'*64),('mode','100755'),('bytes',999),('git_oid','2'*40)]:
   G,d,_=self.source();d['files']['docs/licenses.md'][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
  G,d,_=self.source();d['files']['extra']={}
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
 def test_case_collision_symlink_and_overbound_blob_refuse(self):
  G,d,r=self.source();r[0]+=b'100644 blob '+b'1'*40+b'\tDOCS/licenses.md\0';d['files']['DOCS/licenses.md']=copy.deepcopy(d['files']['docs/licenses.md'])
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
  G,d,r=self.source();r[0]=r[0].replace(b'100644 blob',b'120000 blob')
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
  G,d,r=self.source();size=128*1024*1024+1;d['files']['docs/licenses.md']['bytes']=size;r[1]=b'1'*40+b' blob '+str(size).encode()+b'\n'
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
 def test_blob_framing_or_trailing_bytes_refuse(self):
  G,d,r=self.source();r[2]+=b'unbound'
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)
  G,d,r=self.source();r[2]=r[2][:-1]+b'X'
  with self.assertRaises(ValueError):Q.read_committed_archive(G,'a'*40,d)

if __name__=='__main__':unittest.main()

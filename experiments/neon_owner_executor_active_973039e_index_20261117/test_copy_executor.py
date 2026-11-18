"""Synthetic owned-temp primitive tests only; never invoke Q/main/build or Git."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,hashlib,json,os,shutil,stat,tempfile,unittest,warnings,zipfile
import copy_executor as C
HERE=Path(__file__).resolve().parent
SCRATCH=HERE/'cpu-copy-scratch'

class CopyPrimitives(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  boundary=HERE.parents[1].resolve()
  assert HERE.resolve().is_relative_to(boundary) and HERE.resolve()!=boundary
  for p in (HERE,*HERE.parents):
   if p.exists():assert not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400
  SCRATCH.mkdir(exist_ok=True)
  assert SCRATCH.resolve().parent==HERE.resolve() and not SCRATCH.is_symlink() and not getattr(SCRATCH.lstat(),'st_file_attributes',0)&0x400
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='owned-',dir=SCRATCH)
  self.root=Path(self.temp.name).resolve()
  assert self.root.is_relative_to(SCRATCH.resolve()) and self.root!=SCRATCH.resolve()
  def cleanup():
   resolved=self.root.resolve()
   assert resolved.is_relative_to(SCRATCH.resolve()) and resolved!=SCRATCH.resolve()
   assert not self.root.is_symlink() and not getattr(self.root.lstat(),'st_file_attributes',0)&0x400
   self.temp.cleanup()
  self.addCleanup(cleanup)
  self.H=C.helpers(self.root)
  self.source=self.root/'source.txt';self.source.write_bytes(b'authored raw\r\nbytes\n')
  self.expected=self.H.identity(self.source);self.dest=self.root/'copy/final.txt'
 def archive(self,name='fixture.has',extra=None,sha=None,method=zipfile.ZIP_STORED):
  project=b'{"schema_version":4}'
  payload=b'SYNTHETIC-PAYLOAD-CONTROL'
  rows=[{'path':'project.json','bytes':len(project),'sha256':hashlib.sha256(project).hexdigest()},
        {'path':'payload.bin','bytes':len(payload),'sha256':sha or hashlib.sha256(payload).hexdigest()}]
  target=self.root/name
  with zipfile.ZipFile(target,'x',compression=method) as z:
   z.writestr('has.json',json.dumps({'storage':'packed','payload':rows}))
   z.writestr('project.json',project);z.writestr('payload.bin',payload)
   if extra:z.writestr(extra,b'not admitted')
  return target
 def test_exact_reference_and_only_requested_helper_ASTs_load(self):
  raw=(HERE/'reference_builder.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),C.REFERENCE_SHA)
  self.assertEqual({k for k in vars(self.H) if callable(getattr(self.H,k))},C.FUNCTIONS)
  self.assertNotIn('main',vars(self.H));self.assertNotIn('Admission',self.H.copy_new.__globals__)
  self.assertEqual(self.H.ROOT,self.root)
 def test_Q_mapping_API_installs_proxy_in_exact_Git_function_globals(self):
  self.assertIs(self.H['identity'],self.H.identity)
  body=b'authored';oid=b'1'*40
  responses=[b'100644 blob '+oid+b'\tsrc/a.gd\0',oid+b' blob '+str(len(body)).encode()+b'\n'+body+b'\n']
  calls=[]
  class FakeGit:
   def check_output(self,args,**options):
    calls.append((args,options));return responses.pop(0)
  proxy=FakeGit();self.H['subprocess']=proxy
  self.assertIs(self.H.git_blobs.__globals__['subprocess'],proxy)
  self.assertEqual(self.H['git_blobs']('a'*40,['src/a.gd']),{'src/a.gd':body})
  self.assertEqual(len(calls),2);self.assertEqual(calls[0][1]['cwd'],self.root)
  with self.assertRaises(RuntimeError):self.H['ROOT']=Path('not-admitted')
 def test_exact_copy_preserves_raw_bytes_stamps_and_original(self):
  self.H.copy_new(self.source,self.dest,self.root,self.expected)
  self.assertEqual(self.dest.read_bytes(),b'authored raw\r\nbytes\n')
  self.assertEqual(self.H.identity(self.dest),self.expected);self.assertEqual(self.H.identity(self.source),self.expected)
 def test_existing_copy_is_never_overwritten(self):
  self.dest.parent.mkdir();self.dest.write_bytes(b'owner work')
  with self.assertRaises(RuntimeError):self.H.copy_new(self.source,self.dest,self.root,self.expected)
  self.assertEqual(self.dest.read_bytes(),b'owner work')
 def test_changed_source_refuses_before_destination_creation(self):
  self.source.write_bytes(b'changed after pin')
  with self.assertRaises(RuntimeError):self.H.copy_new(self.source,self.dest,self.root,self.expected)
  self.assertFalse(self.dest.exists())
 def test_copy_path_escape_and_equal_boundary_refuse(self):
  for target in (self.root.parent/(self.root.name+'-outside.txt'),self.root):
   with self.assertRaises(RuntimeError):self.H.copy_new(self.source,target,self.root,self.expected)
 def test_relative_source_names_reject_traversal_aliases_and_ADS(self):
  for name in ('','../x','src/../x','./x','src//x','src\\x','C:/x','src/x:stream',True):
   with self.assertRaises(RuntimeError):C._relative(name)
 def test_copy_exclusive_creation_defeats_destination_race(self):
  original=Path.open;target=self.dest;triggered=[]
  def race(path,mode='r',*a,**kw):
   if path==target and mode=='xb' and not triggered:
    triggered.append(True)
    with original(path,'xb') as f:f.write(b'racing owner')
   return original(path,mode,*a,**kw)
  with patch.object(Path,'open',race):
   with self.assertRaises(FileExistsError):self.H.copy_new(self.source,target,self.root,self.expected)
  self.assertEqual(target.read_bytes(),b'racing owner')
 def test_postcopy_source_mutation_refuses_and_retains_partial_copy(self):
  original=shutil.copyfileobj
  def changed(src,dst,length):
   original(src,dst,length);self.source.write_bytes(b'changed during copy')
  with patch.object(shutil,'copyfileobj',changed):
   with self.assertRaises(RuntimeError):self.H.copy_new(self.source,self.dest,self.root,self.expected)
  self.assertTrue(self.dest.is_file());self.assertEqual(self.dest.read_bytes(),b'authored raw\r\nbytes\n')
 def test_support_Git_blob_keeps_exact_CRLF_without_normalization(self):
  raw=b'committed support\r\nbytes\n';target=self.root/'support/doc.txt'
  C._write_blob(self.H,target,self.root,raw,hashlib.sha256(raw).hexdigest())
  self.assertEqual(target.read_bytes(),raw)
 def test_support_bad_hash_and_existing_target_refuse(self):
  raw=b'support';target=self.root/'support.txt'
  with self.assertRaises(RuntimeError):C._write_blob(self.H,target,self.root,raw,'0'*64)
  self.assertFalse(target.exists());target.write_bytes(b'existing')
  with self.assertRaises(RuntimeError):C._write_blob(self.H,target,self.root,raw,hashlib.sha256(raw).hexdigest())
  self.assertEqual(target.read_bytes(),b'existing')
 def test_write_new_JSON_is_exclusive(self):
  target=self.root/'new.json';self.H.write_new(target,{'one':1})
  before=target.read_bytes()
  with self.assertRaises(FileExistsError):self.H.write_new(target,{'two':2})
  self.assertEqual(target.read_bytes(),before)
 def test_reparse_attribute_refuses_without_creating_a_link(self):
  fake=SimpleNamespace(st_mode=stat.S_IFREG,st_file_attributes=0x400)
  with patch.object(Path,'lstat',return_value=fake):
   with self.assertRaises(RuntimeError):self.H.no_links(self.source)
 def test_source_map_has_exact_functional_scope_excluding_caches(self):
  for name in C.ENTRY:(self.root/name).write_bytes(b'authored')
  for name in ('src/a.gd','tests/t.py','tools/u.py','data/v.json','examples/e.bin','src/__pycache__/bad.py','tests/bad.pyc'):
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'authored')
  self.assertEqual(set(self.H.source_map()),set(C.ENTRY)|{'src/a.gd','tests/t.py','tools/u.py','data/v.json','examples/e.bin'})
 def test_exporter_noncache_catalogue_scope(self):
  folder=self.root/'exporter';folder.mkdir()
  for name in ('a.py','b.txt','skip.pyc','__pycache__/skip.py'):
   p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'authored')
  self.assertEqual(set(self.H.exporter_sources(folder)),{'a.py','b.txt'})
 def test_packed_schema4_inventory_SHA_CRC_readback(self):
  proof=self.H.package_readback(self.archive())
  self.assertEqual(proof,{'packed':True,'all_payload_SHA_and_CRC_verified':True,'payload_files':2})
 def test_bad_payload_SHA_and_extra_archive_member_refuse(self):
  with self.assertRaises(RuntimeError):self.H.package_readback(self.archive('bad-sha.has',sha='0'*64))
  with self.assertRaises(RuntimeError):self.H.package_readback(self.archive('extra.has',extra='unlisted.bin'))
 def test_unsafe_archive_member_and_duplicate_members_refuse(self):
  for i,unsafe in enumerate(('../outside','/absolute','dir\\backslash','x:stream')):
   p=self.root/('unsafe'+str(i)+'.has');data=b'authored';project=b'{"schema_version":4}'
   with zipfile.ZipFile(p,'x') as z:
    z.writestr('has.json',json.dumps({'storage':'packed','payload':[{'path':'project.json','bytes':len(project),'sha256':hashlib.sha256(project).hexdigest()},{'path':unsafe,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}))
    z.writestr('project.json',project);z.writestr(unsafe,data)
   with self.assertRaises(RuntimeError):self.H.package_readback(p)
  p=self.archive('duplicate.has')
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',UserWarning)
   with zipfile.ZipFile(p,'a') as z:z.writestr('payload.bin',b'duplicate')
  with self.assertRaises(RuntimeError):self.H.package_readback(p)
 def test_corrupt_payload_CRC_refuses(self):
  p=self.archive();raw=bytearray(p.read_bytes());at=raw.index(b'SYNTHETIC-PAYLOAD-CONTROL');raw[at]^=1;p.write_bytes(raw)
  with self.assertRaises(zipfile.BadZipFile):self.H.package_readback(p)
 def test_unsupported_archive_compression_refuses(self):
  with self.assertRaises(RuntimeError):self.H.package_readback(self.archive(method=zipfile.ZIP_BZIP2))
 def test_archive_inventory_budget_refuses_before_any_payload_read(self):
  class Fake:
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def infolist(self):return [SimpleNamespace(filename='huge',file_size=513*1024*1024)]
  with patch.object(zipfile,'ZipFile',return_value=Fake()):
   with self.assertRaises(RuntimeError):self.H.package_readback(self.root/'not-read.has')

if __name__=='__main__':unittest.main()

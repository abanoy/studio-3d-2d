from pathlib import Path
import copy,json,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has
class PackageTests(unittest.TestCase):
 def fixture(self,root):
  folder=root/'snapshot';(folder/'assets').mkdir(parents=True);blob=b'original controlled asset';digest=has.hashlib.sha256(blob).hexdigest();name='assets/'+digest+'.glb';(folder/name).write_bytes(blob)
  row={'format':'studio_model_1','id':'asset','name':'Original model','kind':'model','parent_id':'','start_frame':0,'path':name,'sha256':digest,'position':[0,0,0],'rotation_xyzw':[0,0,0,1],'scale':1,'visible':True,'reference_only':False,'pose':{},'draft_frame':0,'pose_keys':[],'metadata':{'provenance':'original fixture'}}
  manifest={'schema_version':4,'video':{'width':1920,'height':1080,'fps_num':24,'fps_den':1,'duration_frames':48},'world':{'format':'studio_world_1','objects':[row]},'audio':{},'layers':[]}
  header={'format':'studio_asset_package_1','kind':'model','name':row['name']};(folder/'project.json').write_bytes(has.json_bytes(manifest));request={'folder':str(folder),'path':str(root/'Model.has'),'storage':'packed','cache_root':str(root/'cache'),'references':{},'asset_package':header};return request,manifest,header
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);request,manifest,header=self.fixture(root);has.pack(request);result=has.unpack({'path':request['path'],'folder':str(root/'opened')});self.assertEqual(result['asset_package'],header);self.assertEqual(json.loads((root/'opened/project.json').read_bytes()),manifest)
 def test_refuse_scene_and_mismatched_marker_before_replacing_good_package(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);request,manifest,header=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
   for bad in [dict(header,kind='environment'),dict(header,extra=True),dict(header,name=''),dict(header,format='unknown')]:
    with self.subTest(header=bad),self.assertRaises(has.HasError):has.pack({**request,'asset_package':bad})
    self.assertEqual(Path(request['path']).read_bytes(),before)
   for change in ['layers','audio','two','grouped']:
    bad=copy.deepcopy(manifest)
    if change=='layers':bad['layers']=[{'cels':[]}]
    elif change=='audio':bad['audio']={'format':'unexpected'}
    elif change=='two':bad['world']['objects'].append({**bad['world']['objects'][0],'id':'second'})
    else:bad['world']['objects'][0]['parent_id']='missing'
    (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
    with self.subTest(change=change),self.assertRaises(has.HasError):has.pack(request)
    self.assertEqual(Path(request['path']).read_bytes(),before)
 def test_corrupt_purpose_does_not_replace_good_backup(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);request,_,_=self.fixture(root);has.pack(request);has.pack(request);backup=Path(request['path']+'.backup');good=backup.read_bytes()
   with zipfile.ZipFile(request['path']) as source:members={name:source.read(name) for name in source.namelist()}
   header=json.loads(members['has.json']);header['asset_package']['kind']='environment';members['has.json']=has.json_bytes(header)
   with zipfile.ZipFile(request['path'],'w') as out:
    for name,blob in members.items():out.writestr(name,blob)
   has.pack(request);self.assertEqual(backup.read_bytes(),good)
 def test_tampered_package_marker_refuses_before_extraction(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);request,_,_=self.fixture(root);has.pack(request)
   with zipfile.ZipFile(request['path']) as source:members={name:source.read(name) for name in source.namelist()}
   header=json.loads(members['has.json']);header['asset_package']['kind']='environment';members['has.json']=has.json_bytes(header)
   with zipfile.ZipFile(root/'tampered.has','w') as out:
    for name,blob in members.items():out.writestr(name,blob)
   with self.assertRaises(has.HasError):has.unpack({'path':str(root/'tampered.has'),'folder':str(root/'opened')})
   self.assertFalse((root/'opened').exists())
if __name__=='__main__':unittest.main()

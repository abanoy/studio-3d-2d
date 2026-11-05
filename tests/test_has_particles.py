"""Schema5 asset inventory tests; opaque blobs here do not prove rendering."""
from pathlib import Path
import copy,json,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has
import test_has_world as world_tests

class ParticleContainerTests(unittest.TestCase):
    def fixture(self,root):
        base=world_tests.WorldContainerTests();request,manifest,_=base.fixture(root)
        manifest['schema_version']=5;manifest['world']['format']='studio_world_2'
        sources={}
        for extension in ['json','png']:
            p=root/('effect.'+extension);p.write_bytes(('opaque particle '+extension).encode());digest=has.sha(p);name='assets/'+digest+'.'+extension
            (Path(request['folder'])/name).write_bytes(p.read_bytes());sources[extension]=(p,name,digest);request['references'][name]=str(p)
        _,name,digest=sources['json'];_,texture,texture_hash=sources['png']
        effect={'format':'studio_particle_instance_1','id':'flash','name':'Flash','path':name,'sha256':digest,'texture_path':texture,'texture_sha256':texture_hash,'position':[0,1,0],'rotation_xyzw':[0,0,0,1],'scale':1,'start_frame':12,'end_frame':20,'source_in_seconds':0,'visible':True}
        manifest['world']['effects']=[effect,{**effect,'id':'second','start_frame':24,'end_frame':32}]
        self.write(request,manifest);return request,manifest,sources
    def write(self,request,manifest):
        (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))
    def test_packed_shared_particle_dependencies_survive_originals_moving(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);request,manifest,sources=self.fixture(root);has.pack(request)
            with zipfile.ZipFile(request['path'])as z:
                self.assertEqual(len(json.loads(z.read('has.json'))['assets']),4)
                for _,name,_ in sources.values():self.assertEqual(z.namelist().count(name),1)
            for p,_,_ in sources.values():p.rename(p.with_name(p.name+'.moved'))
            result=has.unpack({'path':request['path'],'folder':str(root/'opened')});self.assertTrue(result['ok']);self.assertEqual(json.loads((root/'opened/project.json').read_bytes()),manifest)
    def test_linked_particle_dependencies_relink_once_for_shared_instances(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);request,_,sources=self.fixture(root);request['storage']='linked';has.pack(request);relinks={}
            for p,name,_ in sources.values():new=p.with_name(p.name+'.moved');p.rename(new);relinks[name]=str(new)
            r={'path':request['path'],'folder':str(root/'opened')};missing=has.unpack(r);self.assertEqual(len(missing['missing']),2);self.assertFalse((root/'opened').exists());self.assertTrue(has.unpack({**r,'relinks':relinks})['ok'])
    def test_invalid_effects_preserve_previous_container(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);request,manifest,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            for field,value in [('format','future'),('id','object-0'),('texture_path','../texture.png'),('texture_sha256','z'*64),('start_frame',True),('end_frame',12),('scale',0),('source_in_seconds',float('nan')),('rotation_xyzw',[0,0,0,0]),('position',[1,2,float('inf')]),('visible',1),('future_behavior',True)]:
                bad=copy.deepcopy(manifest);bad['world']['effects'][0][field]=value;self.write(request,bad)
                with self.subTest(field=field),self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)
    def test_schema_and_format_gate_and_no_silent_legacy_effects(self):
        with tempfile.TemporaryDirectory()as d:
            _,manifest,_=self.fixture(Path(d))
            for version,format in [(4,'studio_world_1'),(4,'studio_world_2'),(5,'studio_world_1'),(6,'studio_world_2')]:
                bad=copy.deepcopy(manifest);bad['schema_version']=version;bad['world']['format']=format
                with self.subTest(version=version,format=format),self.assertRaises(has.HasError):has.members(bad)
    def test_missing_or_excess_effect_collection(self):
        with tempfile.TemporaryDirectory()as d:
            _,manifest,_=self.fixture(Path(d))
            for value in [None,{},manifest['world']['effects']*9]:
                bad=copy.deepcopy(manifest);bad['world']['effects']=value
                with self.assertRaises(has.HasError):has.members(bad)
    def test_changed_particle_asset_refuses_replacement(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);request,_,sources=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            (Path(request['folder'])/sources['png'][1]).write_bytes(b'changed')
            with self.assertRaises(has.HasError):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

if __name__=='__main__':unittest.main()

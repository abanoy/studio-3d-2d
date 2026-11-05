from pathlib import Path
import copy,hashlib,json,struct,sys,tempfile,unittest,zipfile,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has
import reference_sheet as reference

def png():
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\0\0\x80'))+chunk(b'IEND',b'')

class ReferenceTests(unittest.TestCase):
    def fixture(self,root):
        folder=root/'snapshot';(folder/'assets').mkdir(parents=True);(folder/'cels').mkdir()
        geometry=root/'original.glb';geometry.write_bytes(b'controlled geometry fixture')
        digest=has.sha(geometry);asset='assets/'+digest+'.glb';(folder/asset).write_bytes(geometry.read_bytes());(folder/'cels/test.png').write_bytes(png())
        cache=root/'cache';cache.mkdir();original=cache/'sheet.png';original.write_bytes(png());digest=has.sha(original);name='references/'+digest+'.png';(folder/'references').mkdir();(folder/name).write_bytes(original.read_bytes())
        manifest=dict(schema_version=7,content_schema_version=3,scene=dict(path=asset,sha256=has.sha(geometry)),model={},audio={},layers=[dict(cels=[dict(path='cels/test.png')])],reference_sheet=dict(format=reference.FORMAT,name='Sheet α.png',path=name,sha256=digest))
        (folder/'project.json').write_bytes(has.json_bytes(manifest))
        return dict(action='pack',folder=str(folder),path=str(root/'film.has'),storage='packed',references={asset:str(geometry),name:str(original)},cache_root=str(cache)),manifest,name,original
    def test_packed_and_linked_reference_survives_source_cache_loss(self):
        for mode in ['packed','linked']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,manifest,name,original=self.fixture(root);request['storage']=mode;has.pack(request)
                original.unlink();(Path(request['folder'])/name).unlink()
                result=has.unpack(dict(path=request['path'],folder=str(root/'opened')))
                self.assertTrue(result['ok']);self.assertEqual((Path(result['folder'])/name).read_bytes(),png())
                restored=json.loads((Path(result['folder'])/'project.json').read_bytes());self.assertEqual(restored,manifest)
                if mode=='linked':
                    with zipfile.ZipFile(request['path']) as archive:
                        row=next(r for r in json.loads(archive.read('has.json'))['assets'] if r['path']==name)
                        self.assertTrue(row['reference'].startswith('film.assets/'));self.assertTrue((root/row['reference']).is_file())
    def test_malformed_reference_and_schema_downgrade_preserve_prior_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            variants=[]
            for field,value in [('path','../outside.png'),('name','bad\nname'),('name','a/b.png'),('sha256','bad'),('format','unknown')]:
                bad=copy.deepcopy(manifest);bad['reference_sheet'][field]=value;variants.append(bad)
            for version in [True,3.5,7,'3']:
                bad=copy.deepcopy(manifest);bad['content_schema_version']=version;variants.append(bad)
            for version in [3,4,5,6]:
                bad=copy.deepcopy(manifest);bad['schema_version']=version;variants.append(bad)
            bad=copy.deepcopy(manifest);bad['reference_sheet']['script']='../../external.gd';variants.append(bad)
            for bad in variants:
                with self.subTest(bad=bad):
                    (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(bad))
                    with self.assertRaises(has.HasError):has.pack(request)
                    self.assertEqual(Path(request['path']).read_bytes(),before)
    def test_reference_size_limit_does_not_raise_particle_texture_limit(self):
        self.assertEqual(has.asset_limit('references/'+'a'*64+'.png'),16*1024*1024)
        self.assertEqual(has.asset_limit('assets/'+'a'*64+'.png'),8*1024*1024)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,manifest,_,_=self.fixture(root);has.pack(request);before=Path(request['path']).read_bytes()
            oversized=b'x'*(reference.MAX_FILE+1);digest=hashlib.sha256(oversized).hexdigest();name='references/'+digest+'.png'
            (Path(request['folder'])/name).write_bytes(oversized);manifest['reference_sheet'].update(path=name,sha256=digest)
            (Path(request['folder'])/'project.json').write_bytes(has.json_bytes(manifest))
            with self.assertRaises(has.HasError):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

if __name__=='__main__':unittest.main()

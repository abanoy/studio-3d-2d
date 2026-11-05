from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import has_project as has
import test_has_project as fixtures

class PaletteTests(unittest.TestCase):
    def fixture(self,root):return fixtures.HasTests('test_packed_portable_without_original_assets').fixture(root)
    def test_packed_linked_palette_roundtrip(self):
        for mode in ('packed','linked'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d);request,_,_=self.fixture(root);request['storage']=mode;p=Path(request['folder'])/'project.json';manifest=json.loads(p.read_bytes())
                manifest['palette']=[{'name':'Skin / 肌','rgba':'f4dfbdff'},{'name':'Transparent','rgba':'12345600'}];p.write_bytes(has.json_bytes(manifest));has.pack(request)
                result=has.unpack({'path':request['path'],'folder':str(root/'open')});self.assertTrue(result['ok']);self.assertEqual(json.loads((root/'open/project.json').read_bytes())['palette'],manifest['palette'])
    def test_invalid_palette_preserves_previous_container(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request,_,_=self.fixture(root);p=Path(request['folder'])/'project.json';manifest=json.loads(p.read_bytes());has.pack(request);before=Path(request['path']).read_bytes()
            for value in [None,True,'bad',{},[{}],[{'name':'','rgba':'000000ff'}],[{'name':'x'*49,'rgba':'000000ff'}],[{'name':'A\nB','rgba':'000000ff'}],[{'name':'x','rgba':'red'}],[{'name':'x','rgba':'FFFFFFff'}],[{'name':'x','rgba':'000000ff','extra':0}],[{'name':'x','rgba':'000000ff'}]*33]:
                with self.subTest(value=value):
                    bad=copy.deepcopy(manifest);bad['palette']=value;p.write_bytes(has.json_bytes(bad))
                    with self.assertRaises(has.HasError):has.pack(request)
                    self.assertEqual(Path(request['path']).read_bytes(),before)
    def test_invalid_palette_in_corrupt_container_not_published(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);request,_,_=self.fixture(root);has.pack(request)
            with zipfile.ZipFile(request['path']) as z:files={n:z.read(n) for n in z.namelist()}
            manifest=json.loads(files['project.json']);manifest['palette']=[{'name':'bad','rgba':'red'}];blob=has.json_bytes(manifest);header=json.loads(files['has.json'])
            for row in header['payload']:
                if row['path']=='project.json':row.update(sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob))
            files['project.json']=blob;files['has.json']=has.json_bytes(header);bad=root/'corrupt.has'
            with zipfile.ZipFile(bad,'w',zipfile.ZIP_DEFLATED) as z:
                for n,value in files.items():z.writestr(n,value)
            with self.assertRaises(has.HasError):has.unpack({'path':str(bad),'folder':str(root/'open')})
            self.assertFalse((root/'open').exists())

if __name__=='__main__':unittest.main()

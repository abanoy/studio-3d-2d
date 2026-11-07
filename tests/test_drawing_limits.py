"""Drawing count and bounded larger HAS member protocol, preserving prior saves."""
import json,tempfile,unittest,zipfile
from pathlib import Path
from tools import drawing_limits as limits
from tests import test_has_project as fixtures
has=fixtures.has
class DrawingLimitTests(unittest.TestCase):
    def test_count_boundary(self):
        self.assertFalse(limits.error([dict(cels=[{}]*400)]))
        self.assertTrue(limits.error([dict(cels=[{}]*401)]))
        for invalid in [None,False,{},[{}],[dict(cels=False)]]:
            with self.subTest(invalid=invalid):self.assertTrue(limits.error(invalid))
    def test_zip_member_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            for count in [has.MAX_FILES,has.MAX_FILES+1]:
                path=Path(temporary)/('count'+str(count)+'.has')
                with zipfile.ZipFile(path,'w') as archive:
                    for index in range(count):archive.writestr('item%04d'%index,b'x')
                if count==has.MAX_FILES:has.preflight_archive(path)
                else:
                    with self.assertRaises(has.HasError):has.preflight_archive(path)
    def test400declared_payloads_roundtrip_and401preserves_save(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);request,_,_=fixtures.HasTests().fixture(root);folder=Path(request['folder']);manifest=json.loads((folder/'project.json').read_text());rows=[]
            for index in range(400):
                path='cels/drawing%04d.png'%index;(folder/path).write_bytes(('controlled encoded payload'+str(index)).encode());rows.append(dict(path=path))
            manifest['layers'][0]['cels']=rows;(folder/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request);before=Path(request['path']).read_bytes()
            with zipfile.ZipFile(request['path']) as archive:self.assertEqual(len([n for n in archive.namelist() if n.startswith('cels/')]),400)
            reopened=fixtures.HasTests().unpack(root,request);self.assertEqual(len(json.loads((Path(reopened['folder'])/'project.json').read_text())['layers'][0]['cels']),400)
            manifest['layers'][0]['cels'].append(dict(path=rows[0]['path']));(folder/'project.json').write_bytes(has.json_bytes(manifest))
            with self.assertRaises(has.HasError):has.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)
if __name__=='__main__':unittest.main()

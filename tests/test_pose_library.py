from pathlib import Path
import base64,copy,json,struct,sys,tempfile,unittest,zlib
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).parent)]
import pose_library as P
import test_has_project as containers
import has_project as has
def picture():
    def chunk(kind,raw):return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
    return base64.b64encode(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,54,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes(96*4))*54))+chunk(b'IEND',b'')).decode()
def good():return {'format':P.FORMAT,'sha256':'a'*64,'bone_ids':['rig:0','rig:1'],'entries':[{'id':'wave','name':'Wave','pose':{'rig:1':{'position':[0,0,0],'rotation_xyzw':[0,0,.5,.8660254037844386]}},'thumbnail_png':picture()}]}
def cases():
    values=[good(),{**good(),'entries':[]}]
    for key,items in {'format':['other'],'sha256':['bad'],'bone_ids':[[],['rig:0','rig:0'],['@root'],[True]],'entries':[[None],[]]}.items():
        for value in items:
            if key=='entries' and value==[]:continue
            values.append({**good(),key:value})
    for key,items in {'id':['',False],'name':['','two\nlines','A'*65],'pose':[None,{'missing':{'position':[0,0,0],'rotation_xyzw':[0,0,0,1]}},{'rig:1':{'position':[False,0,0],'rotation_xyzw':[0,0,0,1]}},{'rig:1':{'position':[0,0,0],'rotation_xyzw':[0,0,0,0]}}],'thumbnail_png':['?','A===','abc','AAAA',base64.b64encode(b'not PNG'*7).decode()]}.items():
        for value in items:
            v=good();v['entries'][0][key]=value;values.append(v)
    v=good();v['entries'].append(copy.deepcopy(v['entries'][0]));values.append(v)
    v=good();v['entries'][0]['pose']['rig:1']['scale']=2;values.append(v)
    v=good();v['entries']=[{**v['entries'][0],'id':str(i),'name':str(i)} for i in range(17)];values.append(v)
    values.extend([None,[],{**good(),'path':'must never resolve'}]);return values
class PoseLibraryTests(unittest.TestCase):
    def test_schema_bindings_payload_bounds(self):
        for i,v in enumerate(cases()):
            with self.subTest(i=i):self.assertEqual(not P.error(v),i<2)
    def test_packed_linked_and_bad_save_preserves_good(self):
        for storage in ['packed','linked']:
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as d:
                root=Path(d);helper=containers.HasTests();request,_,_=helper.fixture(root);request['storage']=storage;folder=Path(request['folder']);m=json.loads((folder/'project.json').read_bytes());library=good();library['sha256']=m['scene']['sha256'];m['model']={**m['scene'],'metadata':{P.FIELD:library}}
                (folder/'project.json').write_bytes(has.json_bytes(m));has.pack(request);before=Path(request['path']).read_bytes();opened=helper.unpack(root,request);self.assertEqual(json.loads((Path(opened['folder'])/'project.json').read_bytes())['model']['metadata'][P.FIELD],library)
                m['model']['metadata'][P.FIELD]['sha256']='b'*64;(folder/'project.json').write_bytes(has.json_bytes(m))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)
    def test_thumbnail_crc_and_inflate_budget(self):
        value=good();raw=bytearray(base64.b64decode(value['entries'][0]['thumbnail_png']));raw[-1]^=1;value['entries'][0]['thumbnail_png']=base64.b64encode(raw).decode();self.assertTrue(P.error(value))
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--corpus':Path(sys.argv[2]).write_text(json.dumps([{'value':v,'valid':not P.error(v)} for v in cases()]),encoding='utf-8')
    else:unittest.main()

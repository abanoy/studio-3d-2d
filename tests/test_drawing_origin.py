from pathlib import Path
import copy,json,sys,tempfile,unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools'),str(Path(__file__).parent)]
import drawing_origin as origin
from test_has_project import HasTests
import has_project as has
def good():return dict(format='studio_drawing_origin_1',kind='krita',name='絵.kra',sha256='a'*64,width=2160,height=3840,fps=24,range=[0,47],visibility={'native-id':False},fit=[608,1080,656,0],rate=[24,1],at=0,duration=48)
def cases():
    result=[good(),{**good(),'fps':0,'range':[]},{**good(),'rate':[24000,1001]}]
    for key,values in {'format':['other'],'name':['../file.kra','C:\\art.kra','','a\n.kra','\ud800.kra'],'sha256':['A'*64,None],'width':[True,0,32769],'height':[32768],'fps':[True,-1,1001],'range':[[4,3],[False,2],[0,'1'],[0]],'visibility':[{'id':'0'},{'\n':True},[]],'fit':[[1920,1080,1,0],[1],[0,1,0,0]],'rate':[[1,0],[121,1],[24000,False]],'at':[240,0.5],'duration':[0,241]}.items():
        for value in values:result.append({**good(),key:value})
    result.extend([{**good(),'path':'do not resolve'},None,[]])
    return result
def video_good():
    v=good()
    for key in ['fps','range','visibility']:del v[key]
    return {**v,'format':'studio_drawing_origin_2','kind':'video','name':'clip.mov','source_rate':[24000,1001],'source_duration':[1001,500],'chroma':{'enabled':True,'color':'00ff00','similarity':.1,'blend':.05}}
def video_cases():
    valid=video_good();result=[(valid,True)]
    for key,values in {'format':['studio_drawing_origin_1'],'kind':['krita'],'source_rate':[[0,1],[241,1],[1,False],[]],'source_duration':[[61,1],[1,0],[1]],'chroma':[{},None,{'enabled':1,'color':'00ff00','similarity':.1,'blend':0},{'enabled':True,'color':'ff0000','similarity':.1,'blend':0}]}.items():
        result.extend([({**valid,key:value},False) for value in values])
    extended={**valid,'format':'studio_drawing_origin_4','at':0,'duration':400}
    result.extend([(extended,True),({**extended,'duration':401},False),({**extended,'at':6800},True),({**extended,'at':6801},False),({**extended,'format':'studio_drawing_origin_2'},False),({**good(),'format':'studio_drawing_origin_3','duration':400},False)])
    return result
class OriginTests(unittest.TestCase):
    def test_bounds_and_portable_identity(self):
        for i,v in enumerate(cases()):
            with self.subTest(i=i):self.assertEqual(not origin.error(v),i<3)
    def test_video_origin_bounds(self):
        for v,valid in video_cases():
            with self.subTest(v=v):self.assertEqual(not origin.error(v),valid)
    def test_video_packed_and_linked_preserve_ancestry(self):
        for storage in ['packed','linked']:
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as d:
                root=Path(d);helper=HasTests();request,_,_=helper.fixture(root);request['storage']=storage
                folder=Path(request['folder']);manifest=json.loads((folder/'project.json').read_bytes());manifest['layers'][0]['origin']=video_good();(folder/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request)
                result=helper.unpack(root,request)
                self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['layers'][0]['origin'],video_good())
    def test_packed_and_linked_preserve_ancestry_and_bad_save(self):
        for storage in ['packed','linked']:
            with self.subTest(storage=storage),tempfile.TemporaryDirectory() as d:
                root=Path(d);helper=HasTests();request,_,_=helper.fixture(root);request['storage']=storage;folder=Path(request['folder']);manifest=json.loads((folder/'project.json').read_bytes());manifest['layers'][0]['origin']=good();(folder/'project.json').write_bytes(has.json_bytes(manifest));has.pack(request);before=Path(request['path']).read_bytes()
                result=helper.unpack(root,request);self.assertEqual(json.loads((Path(result['folder'])/'project.json').read_bytes())['layers'][0]['origin'],good())
                manifest['layers'][0]['origin']['path']='C:/missing.kra';(folder/'project.json').write_bytes(has.json_bytes(manifest))
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(Path(request['path']).read_bytes(),before)
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--corpus':
        # Keep surrogate failure in Python only; JSON parser may normalize it.
        data=[v for v in cases() if not isinstance(v,dict) or v.get('name')!='\ud800.kra'];Path(sys.argv[2]).write_text(json.dumps([{'value':v,'valid':not origin.error(v)} for v in data]+[{'value':v,'valid':valid} for v,valid in video_cases()],ensure_ascii=True),encoding='utf-8')
    else:unittest.main()

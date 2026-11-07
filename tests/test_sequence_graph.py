from pathlib import Path
import copy,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import sequence_graph as graph


def scene():
    return dict(schema_version=4,video=dict(width=1920,height=1080,fps_num=24,fps_den=1,duration_frames=48),
                world=dict(format='studio_world_1',objects=[]),layers=[],audio={},camera_keys=[])


def key(frame=0):
    return dict(frame=frame,offset=[0,0],scale=1,rotation=0,opacity=1,interpolation='linear')


def clip(identity='clip1',asset='child'):
    return dict(id=identity,asset_id=asset,start=0,duration=48,source_in=0,time_in=0,key_in=0,loop=False,
                visible=True,muted=False,gain_db=0,keys=[key()])


def good():
    return dict(format=graph.FORMAT,assets=[dict(id='child',name='絵 and rig',scene=scene(),clips=[])],clips=[clip()])


def cases():
    result=[(good(),scene(),True)]
    for field,values in {'format':['unknown'],'assets':[None,[],[None]],'clips':[None,[None]]}.items():
        for value in values:result.append(({**good(),field:value},scene(),False))
    for field,values in {'id':['../bad',None,True],'asset_id':['missing',None,[]],'start':[-1,48,True],'duration':[0,49,.5],'source_in':[-1,48,True],'loop':[1],'visible':['true'],'muted':[None],'gain_db':[-61,13,True],'keys':[[],None,[key(1)],[key(),key()]]}.items():
        for value in values:
            v=good();v['clips'][0][field]=value;result.append((v,scene(),False))
    for field,values in {'frame':[-1,1000241,True],'offset':[[0],None,[False,0],[19201,0]],'scale':[0,8.1,True],'rotation':[36001,'0'],'opacity':[-.1,1.1,False],'interpolation':['other']}.items():
        for value in values:
            v=good();v['clips'][0]['keys'][0][field]=value;result.append((v,scene(),False))
    v=good();v['assets'][0]['clips']=[clip('cycle')];result.append((v,scene(),False))
    v=good();v['assets']*=2;result.append((v,scene(),False))
    v=good();v['clips']=[clip('n'+str(i)) for i in range(9)];result.append((v,scene(),False))
    for field,values in {'fps_num':[25,True],'fps_den':[0],'width':[1280],'duration_frames':[0,241]}.items():
        for value in values:
            v=good();v['assets'][0]['scene']['video'][field]=value;result.append((v,scene(),False))
    v=good();v['assets'][0]['scene']['sequence_graph']={};result.append((v,scene(),False))
    v=good();v['assets'][0]['scene']['layers']=[{'cels':[{}]*201}];root=scene();root['layers']=[{'cels':[{}]*200}];result.append((v,root,False))
    v=good();v['assets'][0]['scene']['layers']=[{'cels':[{}]*200}];root=scene();root['layers']=[{'cels':[{}]*200}];result.append((v,root,True))
    v=good();v['assets'][0]['scene']['audio']={'clips':[{}]*9};root=scene();root['audio']={'clips':[{}]*8};result.append((v,root,False))
    v=good();v['assets'][0]['scene']['world']['objects']=[{}]*33;root=scene();root['world']['objects']=[{}]*32;result.append((v,root,False))
    v=good();v['assets'][0]['scene']['video']['duration_frames']=12;v['clips'][0]['loop']=True;result.append((v,scene(),True))
    v=good();v['clips'][0]['keys'].append({**key(48),'offset':[1920,-1080],'opacity':.5,'rotation':360,'scale':2,'interpolation':'ease'});result.append((v,scene(),True))
    v=good();v['assets']=[dict(id='a'+str(i),name='Depth'+str(i),scene=scene(),clips=[clip('d'+str(i),'a'+str(i+1))] if i<3 else []) for i in range(4)];v['clips']=[clip('root','a0')];result.append((v,scene(),True))
    for value,valid in [(dict(format='studio_sequence_editor_1',asset_id='child',frame=24),True),(dict(format='studio_sequence_editor_1',asset_id='missing',frame=0),False),(dict(format='other',asset_id='child',frame=0),False),(dict(format='studio_sequence_editor_1',asset_id='child',frame=49),False),(dict(format='studio_sequence_editor_1',asset_id='child',frame=True),False),(None,False)]:
        root=scene();root['editor']={'sequence_editor':value};result.append((good(),root,valid))
    styled=good();styled['format']=graph.SHADOW_FORMAT;styled['clips'][0]['shadow']={}
    result.append((copy.deepcopy(styled),scene(),True))
    styled['clips'][0]['shadow']=dict(offset=[120,-5],color=[0,0,0,.5],softness=8)
    result.append((copy.deepcopy(styled),scene(),True))
    for value in [None,False,dict(offset=[0],color=[0,0,0,.5],softness=4),dict(offset=[2049,0],color=[0,0,0,.5],softness=4),dict(offset=[0,0],color=[0,0,0,True],softness=4),dict(offset=[0,0],color=[0,0,0,1.1],softness=4),dict(offset=[0,0],color=[0,0,0,.5],softness=33),dict(offset=[0,0],color=[0,0,0,.5],softness=False),dict(offset=[0,0],color=[0,0,0,.5],softness=4,unknown=0)]:
        v=copy.deepcopy(styled);v['clips'][0]['shadow']=value;result.append((v,scene(),False))
    v=copy.deepcopy(styled);v['format']=graph.FORMAT;result.append((v,scene(),False))
    v=copy.deepcopy(styled);del v['clips'][0]['shadow'];result.append((v,scene(),False))
    masked=copy.deepcopy(styled);masked['format']=graph.MASK_FORMAT;masked['clips'][0]['mask']={}
    result.append((copy.deepcopy(masked),scene(),True))
    masked['clips'][0]['mask']=dict(rect=[800,400,50,100],invert=False);result.append((copy.deepcopy(masked),scene(),True))
    for rect in [[0,0,1920,1080],[1919,1079,1,1]]:
        v=copy.deepcopy(masked);v['clips'][0]['mask']=dict(rect=rect,invert=True);result.append((v,scene(),True))
    for value in [None,False,[],dict(rect=[0,0,1],invert=False),dict(rect=[0,0,1,1],invert=1),dict(rect=[-1,0,1,1],invert=False),dict(rect=[0,0,0,1],invert=False),dict(rect=[1919,0,2,1],invert=False),dict(rect=[0,1079,1,2],invert=False),dict(rect=[True,0,1,1],invert=False),dict(rect=[0,0,1.5,1],invert=False),dict(rect=[0,0,1,1],invert=False,extra=0)]:
        v=copy.deepcopy(masked);v['clips'][0]['mask']=value;result.append((v,scene(),False))
    v=copy.deepcopy(masked);v['format']=graph.SHADOW_FORMAT;result.append((v,scene(),False))
    for field in ['mask','shadow']:
        v=copy.deepcopy(masked);del v['clips'][0][field];result.append((v,scene(),False))
    return result


class SequenceGraphTests(unittest.TestCase):
    def test_cross_runtime_corpus(self):
        for i,(value,root,valid) in enumerate(cases()):
            with self.subTest(i=i):self.assertEqual(not graph.error(value,root),valid)

    def test_exact_offset_loop_and_exclusive_end(self):
        v=clip();v.update(start=2,duration=6,source_in=1,loop=True)
        self.assertEqual([graph.local_frame(v,i,4) for i in range(10)],[-1,-1,1,2,3,0,1,2,-1,-1])
        v.update(duration=3,loop=False)
        self.assertEqual([graph.local_frame(v,i,4) for i in range(7)],[-1,-1,1,2,3,-1,-1])

    def test_mutual_cycle_refuses_even_if_unused(self):
        v=good();v['assets']=[dict(id='a',name='A',scene=scene(),clips=[clip('ab','b')]),dict(id='b',name='B',scene=scene(),clips=[clip('ba','a')])];v['clips']=[]
        self.assertIn('Cyclic',graph.error(v,scene()))


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--corpus':
        Path(sys.argv[2]).write_text(json.dumps([dict(value=v,root=r,valid=valid) for v,r,valid in cases()],ensure_ascii=True),encoding='utf-8')
    else:unittest.main()

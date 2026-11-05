"""Extended parent timing stays explicit while child/resource bounds stay fixed."""
from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import extended_timing as timing
import has_project as has
import sequence_graph as graph
import drawing_origin

class ExtendedTimingTests(unittest.TestCase):
    def video(self,n=24,d=1,count=1440):return dict(width=1920,height=1080,fps_num=n,fps_den=d,duration_frames=count)
    def scene(self,count=48):return dict(schema_version=4,video=self.video(count=count),world=dict(format='studio_world_1',objects=[]),layers=[],camera_keys=[],audio={})
    def test_exact_rational_envelope(self):
        for n,d,last in [(24,1,1440),(120,1,7200),(24000,1001,1438),(30000,1001,1798)]:
            with self.subTest(n=n,d=d):
                self.assertFalse(timing.video_error(self.video(n,d,last)))
                self.assertTrue(timing.video_error(self.video(n,d,last+1)))
        self.assertFalse(timing.video_error(self.video(1,1001,240)))
        for v in [0,1441,7201,True,12.5,float('nan'),float('inf')]:self.assertTrue(timing.video_error(self.video(count=v)))
    def test_wrapper_and_downgrade(self):
        scene=self.scene(1440)
        with self.assertRaises(has.HasError):has.members(scene)
        scene.update(schema_version=8,timing_content_schema_version=4)
        self.assertEqual(has.members(scene),({},set()))
        for bad in [True,0,8,4.5,'4',None]:
            with self.subTest(bad=bad),self.assertRaises(has.HasError):has.members({**scene,'timing_content_schema_version':bad})
    def test_long_parent_short_child(self):
        root=self.scene(1440);child=self.scene()
        clip=dict(id='loop',asset_id='child',start=1200,duration=240,source_in=0,time_in=0,key_in=0,loop=True,visible=True,muted=False,gain_db=0,keys=[dict(frame=0,offset=[0,0],scale=1,rotation=0,opacity=1,interpolation='linear')])
        sequence=dict(format=graph.FORMAT,assets=[dict(id='child',name='Child',scene=child,clips=[])],clips=[clip])
        self.assertFalse(graph.error(sequence,root))
        child['video']['duration_frames']=241
        self.assertTrue(graph.error(sequence,root))
        child['video']['duration_frames']=48
        child.update(schema_version=8,timing_content_schema_version=4)
        self.assertFalse(graph.error(sequence,root))
        child['timing_content_schema_version']=4.5
        self.assertTrue(graph.error(sequence,root))
        child['timing_content_schema_version']=4
        clip['keys'].append({**clip['keys'][0],'frame':1007200})
        self.assertFalse(graph.error(sequence,root));self.assertTrue(timing.required({'sequence_graph':sequence}))
        clip['keys'][-1]['frame']+=1
        self.assertTrue(graph.error(sequence,root))
    def test_ancestry_survives_shortening_without_downgrade(self):
        origin=dict(format='studio_drawing_origin_3',kind='krita',name='source.kra',sha256='a'*64,width=32,height=32,fps=24,range=[],visibility={},fit=[32,32,0,0],rate=[24,1],at=1300,duration=24)
        self.assertFalse(drawing_origin.error(origin))
        self.assertTrue(drawing_origin.error({**origin,'duration':241}))
        video={**origin,'format':'studio_drawing_origin_4','kind':'video','source_rate':[24,1],'source_duration':[1,1],'chroma':dict(enabled=False,color='00ff00',similarity=.1,blend=.05)}
        for key in ['fps','range','visibility']:video.pop(key)
        self.assertFalse(drawing_origin.error(video))
        self.assertTrue(drawing_origin.error({**video,'format':'studio_drawing_origin_2'}))
        self.assertTrue(drawing_origin.error({**video,'at':7199,'duration':2}))
        self.assertTrue(drawing_origin.error({**origin,'format':'studio_drawing_origin_1'}))
        scene=self.scene();scene['layers']=[dict(id='ink',name='Ink',visible=True,cels=[],origin=origin)]
        self.assertTrue(timing.required(scene))
        with self.assertRaises(has.HasError):has.members(scene)
        scene.update(schema_version=8,timing_content_schema_version=4)
        self.assertEqual(has.members(scene),({},set()))

if __name__=='__main__':unittest.main()

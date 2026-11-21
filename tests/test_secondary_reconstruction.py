"""Owned guide preservation and admission controls, using authored geometry only."""
from pathlib import Path
import copy,hashlib,json,math,struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import secondary_reconstruction as R
import secondary_helpers_batch as B
from test_secondary_helpers import mixed_fixture,write_glb

class Reconstruction(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name);self.source=self.folder/'source.glb';self.g=mixed_fixture(self.source)
        self.request={'source_sha256':self.g.sha,'reviewed':True,'node':3,'primitive':1,'component':0,'segments':3,'reconstruct_weights':True}
    def tearDown(self):self.temp.cleanup()
    def build(self,**changes):
        request=dict(self.request,**changes);value=R.build(self.source,self.folder/'candidate',request);return R.H.GLB(value['glb']),value
    def test_exact_float_partitions(self):
        for w in (.1,.8,1.,2**-126,2**-149):
            w=struct.unpack('<f',struct.pack('<f',w))[0]
            for f in (0.,.13,.5,.99,1.):
                a,b=R.split_weight(w,f);self.assertEqual(a+b,w);self.assertEqual(a,struct.unpack('<f',struct.pack('<f',a))[0]);self.assertEqual(b,struct.unpack('<f',struct.pack('<f',b))[0])
    def test_source_and_binary_prefix(self):
        raw=self.source.read_bytes();stamp=self.source.stat().st_mtime_ns;g,value=self.build()
        self.assertEqual(self.source.read_bytes(),raw);self.assertEqual(self.source.stat().st_mtime_ns,stamp);self.assertEqual(g.binary[:len(self.g.binary)],self.g.binary)
        for key in ('materials','textures','images','scenes','animations','extensions'):
            self.assertEqual(g.doc.get(key),self.g.doc.get(key))
        self.assertEqual(g.doc['accessors'][:len(self.g.doc['accessors'])],self.g.doc['accessors'])

    def test_rest_surface_retains_original_attributes_and_all_other_geometry(self):
        g,value=self.build();rows=R.rest_surfaces(g)
        self.assertEqual(len(rows),1);row=rows[0]
        self.assertEqual((row['node'],row['mesh'],row['primitive']),(3,0,1))
        attrs=self.g.skin(3,1)[2]['attributes']
        self.assertEqual(row['attributes'],{key:attrs[key] for key in R.SKIN_ATTRIBUTES if key in attrs})
        self.assertEqual(row['helper_nodes'],value['report']['helper_nodes'])
        self.assertNotEqual(g.skin(3,1)[2]['attributes']['WEIGHTS_0'],row['attributes']['WEIGHTS_0'])
        primitive=g.doc['meshes'][0]['primitives'][1]
        current=copy.deepcopy(primitive['attributes'])
        restored={k:v for k,v in current.items() if k not in R.SKIN_ATTRIBUTES};restored.update(row['attributes'])
        primitive['attributes']=restored
        self.assertEqual(g.skin(3,1)[4:7],self.g.skin(3,1)[4:7])

    def test_subsequent_reconstruction_keeps_first_rest_view(self):
        first,value=self.build();baseline=copy.deepcopy(R.rest_surfaces(first)[0])
        request=dict(self.request,source_sha256=first.sha,component=1,
                     points_in_anchor=[[-.55,.4,.1],[-.55,.7,.1],[-.55,1.,.1],[-.55,1.3,.1]])
        next_value=R.build(first.source,self.folder/'next',request);second=R.H.GLB(next_value['glb'])
        rows=R.rest_surfaces(second)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['attributes'],baseline['attributes'])
        self.assertEqual(set(rows[0]['helper_nodes']),set(baseline['helper_nodes'])|set(next_value['report']['helper_nodes']))

    def test_distinct_skin_joint_sets_keep_only_their_own_guides(self):
        g=self.g;g.doc['nodes'].append({'name':'Arm'})
        g.doc['nodes'][1]['children'].append(5)
        g.doc['nodes'].append({'name':'Second','mesh':1,'skin':1})
        g.doc['nodes'][0]['children'].append(6)
        g.doc['meshes'].append(copy.deepcopy(g.doc['meshes'][0]))
        skin={'joints':[1,5],'skeleton':1,'inverseBindMatrices':g.append([R.H.IDENTITY,R.H.translation((.15,0,0))],'MAT4')}
        g.doc['skins'].append(skin)
        for primitive in g.doc['meshes'][1]['primitives']:
            count=g.doc['accessors'][primitive['attributes']['POSITION']]['count']
            primitive['attributes']['JOINTS_0']=g.append([(0,1,0,0)]*count,'VEC4',5121)
            primitive['attributes']['WEIGHTS_0']=g.append([(.25,.75,0.,0.)]*count,'VEC4')
        write_glb(self.source,g.doc,bytes(g.binary))
        request=R.recipe(self.request);request.update(source_sha256=R.H.GLB(self.source).sha,
            regions=[{'node':3,'primitive':1,'component':0},{'node':6,'primitive':1,'component':0}])
        value=R.build(self.source,self.folder/'separate-skins',request);candidate=R.H.GLB(value['glb'])
        rows=R.rest_surfaces(candidate);self.assertEqual(len(rows),2)
        for row in rows:
            joints=candidate.doc['skins'][candidate.doc['nodes'][row['node']]['skin']]['joints']
            self.assertTrue(set(row['helper_nodes']).issubset(set(joints)))
        self.assertNotEqual(set(rows[0]['helper_nodes']),set(rows[1]['helper_nodes']))

    def test_malformed_rest_views_refuse_without_output(self):
        g,value=self.build();good=copy.deepcopy(g.doc['extras'][R.REST_KEY])
        mutations=[lambda v:v.update(format='unknown'),
                   lambda v:v['surfaces'].append(copy.deepcopy(v['surfaces'][0])),
                   lambda v:v['surfaces'][0].update(mesh=99),
                   lambda v:v['surfaces'][0]['attributes'].update(WEIGHTS_0=999999),
                   lambda v:v['surfaces'][0].update(helper_nodes=[2]),
                   lambda v:v['surfaces'][0]['attributes'].update(WEIGHTS_1=0)]
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                bad=copy.deepcopy(good);mutate(bad);g.doc['extras'][R.REST_KEY]=bad
                path=self.folder/f'bad-{index}.glb';write_glb(path,g.doc,bytes(g.binary))
                request=dict(self.request,source_sha256=R.H.GLB(path).sha)
                with self.assertRaises(ValueError):R.build(path,self.folder/f'refused-{index}',request)
                self.assertFalse((self.folder/f'refused-{index}').exists())
    def test_original_fk_morph_and_unselected_surfaces(self):
        g,value=self.build();old=self.g.skin(3,1);new=g.skin(3,1);count=len(self.g.doc['nodes']);globals={}
        for i in range(count):
            angle=.19*i;c=math.cos(angle);s=math.sin(angle)
            globals[i]=[c,s,0,0,-s,c,0,0,0,0,1,0,i*.17,-i*.03,i*.11,1]
        parents={c:i for i,n in enumerate(g.doc['nodes']) for c in n.get('children',[])}
        for i in range(count,len(g.doc['nodes'])):globals[i]=R.H.multiply(globals[parents[i]],R.H.translation(g.doc['nodes'][i]['translation']))
        for morph in (0.,.65):
            a=self.g.shaped_skin(3,1,{'morph_weights':{'3':[morph]}});b=g.shaped_skin(3,1,{'morph_weights':{'3':[morph]}})
            for v in range(len(a[4])):
                points=[]
                for data in (a,b):
                    p=[0.,0.,0.]
                    for joint,w in data[6][v]:
                        q=R.H.point(R.H.multiply(globals[data[3]['joints'][joint]],data[7][joint]),data[4][v])
                        for k in range(3):p[k]+=w*q[k]
                    points.append(p)
                self.assertLess(R.H.distance(*points),2e-6)
        self.assertEqual(g.doc['meshes'][0]['primitives'][0],self.g.doc['meshes'][0]['primitives'][0])
        self.assertEqual(new[6][20:],old[6][20:]);self.assertEqual(new[2]['targets'],old[2]['targets'])
    def test_nonzero_shape_drives_reviewed_parameter(self):
        neutral=R.prepare(self.source,R.recipe(self.request));recipe=R.recipe(self.request);recipe['morph_weights']={'3':[1.]}
        # Move longitudinally, not the fixture's original transverse morph.
        a=self.g.doc['meshes'][0]['primitives'][1]['targets'][0]['POSITION'];self.g.doc['accessors'][a]=copy.deepcopy(self.g.doc['accessors'][a])
        replacement=self.g.append([(0,-.4,0)]*24,'VEC3');self.g.doc['meshes'][0]['primitives'][1]['targets'][0]['POSITION']=replacement
        write_glb(self.source,self.g.doc,bytes(self.g.binary));self.g=R.H.GLB(self.source);self.request['source_sha256']=self.g.sha
        base=R.recipe(self.request);base['points_in_anchor']=neutral['controls'];shape=dict(base,morph_weights={'3':[1.]})
        before=R.prepare(self.source,base);after=R.prepare(self.source,shape)
        self.assertTrue(any(abs(before['parameters'][k]-after['parameters'][k])>.1 for k in before['parameters']))
        g,_=self.build(morph_weights={'3':[1.]},points_in_anchor=neutral['controls']);self.assertNotEqual(g.skin(3,1)[6],R.H.GLB(R.build(self.source,self.folder/'neutral',base)['glb']).skin(3,1)[6])
    def test_unreviewed_refused(self):
        with self.assertRaises(ValueError):self.build(reviewed=False)
    def test_stale_source_refused(self):
        with self.assertRaises(ValueError):self.build(source_sha256='0'*64)
    def test_existing_candidate_refused(self):
        self.build()
        with self.assertRaises(ValueError):self.build()
    def test_quantized_weight_profile_refused(self):
        accessor=self.g.doc['meshes'][0]['primitives'][1]['attributes']['WEIGHTS_0'];self.g.doc['accessors'][accessor]['componentType']=5123;self.g.doc['accessors'][accessor]['normalized']=True
        write_glb(self.source,self.g.doc,bytes(self.g.binary));self.request['source_sha256']=R.H.GLB(self.source).sha
        with self.assertRaises(ValueError):self.build()
    def test_preview_original_indices_and_edges(self):
        view=R.H.preview(self.source,self.request);self.assertEqual(view['source_vertices'],list(range(20)));self.assertTrue(view['edges']);self.assertEqual(view['mode'],'reconstructed_weights')
    def test_batch_does_not_silently_enable_reconstruction(self):
        request={'format':B.FORMAT,'source_sha256':self.g.sha,'reviewed':True,'items':[self.request]};plan=B.plan(self.source,request)
        self.assertEqual(plan['operations'][0]['mode'],'reconstructed_weights');self.assertEqual(plan['added_nodes'],12)
        value=B.build(self.source,self.folder/'batch',request);self.assertEqual(value['report']['mode'],'reconstructed_weights')
    def test_compatible_multiskin_frames_and_incompatible_refusal(self):
        doc=self.g.doc;doc['nodes'].append({'name':'Second','mesh':1,'skin':1});doc['nodes'][0]['children'].append(len(doc['nodes'])-1);doc['meshes'].append(copy.deepcopy(doc['meshes'][0]));doc['skins'].append(copy.deepcopy(doc['skins'][0]))
        write_glb(self.source,doc,bytes(self.g.binary));recipe=R.recipe(self.request);recipe.update(source_sha256=R.H.GLB(self.source).sha,regions=[{'node':3,'primitive':1,'component':0},{'node':5,'primitive':1,'component':0}])
        R.prepare(self.source,recipe)
        binds=list(self.g.accessor(doc['skins'][1]['inverseBindMatrices'],'MAT4'));binds[1]=R.H.multiply(R.H.translation((.2,0,0)),binds[1]);doc['skins'][1]['inverseBindMatrices']=self.g.append(binds,'MAT4')
        write_glb(self.source,doc,bytes(self.g.binary));recipe['source_sha256']=R.H.GLB(self.source).sha
        with self.assertRaisesRegex(ValueError,'incompatible'):R.prepare(self.source,recipe)

if __name__=='__main__':unittest.main()

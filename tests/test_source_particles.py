from pathlib import Path
import copy,hashlib,struct,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from particle_effect import compile_effect
from source_particles import Resources,png_rgba
from asset_audit import AssetError

def fixture():
    def op(name,**parameters):return {'function':name,'parameters':parameters}
    return {'name':'Authored sprite','parameters':{'max_particles':10},'groups':{'renderers':[op('render_animated_sprites')],'emitters':[op('emit_continuously',emission_rate=2)],'initializers':[op('Lifetime Random',lifetime_min=1,lifetime_max=1)],'operators':[],'forces':[],'constraints':[],'children':[]}}

class Particles(unittest.TestCase):
    def test_vtf_resources_and_animation_refused_before_native_codec(self):
        class NoCodec:
            def VTFFile(self):raise AssertionError('Unsupported image reached native codec')
        def header(minor=2,size=80,frames=1):
            blob=bytearray(80);blob[:4]=b'VTF\0';struct.pack_into('<IIIHH',blob,4,7,minor,size,4,4);struct.pack_into('<H',blob,24,frames);return bytes(blob)
        for blob in [header(3),header(2,64),header(2,80,2),header()[:64]]:
            with self.assertRaises(AssetError):png_rgba(blob,NoCodec())
    def test_seed_repeat_and_change(self):
        a=fixture();before=copy.deepcopy(a);first=compile_effect(a,2,17)
        self.assertEqual(first,compile_effect(a,2,17));self.assertNotEqual(first['particles'],compile_effect(a,2,18)['particles']);self.assertEqual(a,before)
    def test_birth_window_and_units(self):
        a=fixture();a['groups']['operators']=[{'function':'Movement Basic','parameters':{'gravity':[0,0,-10]}}]
        v=compile_effect(a,2);self.assertEqual([p['birth']for p in v['particles']],[0,.5,1,1.5]);self.assertEqual(v['particles'][0]['acceleration'],[0,-.1905,0])
    def test_unknown_and_children_refuse_whole(self):
        for key,row in [('children',{'function':'child','parameters':{}}),('forces',{'function':'random force','parameters':{}}),('operators',{'function':'Future native operator','parameters':{}})]:
            a=fixture();a['groups'][key]=[row]
            with self.assertRaises(AssetError):compile_effect(a)
        for key,value in [('future_native_behavior',True),('control point to disable rendering if it is the camera',0)]:
            a=fixture();a['parameters'][key]=value
            with self.assertRaises(AssetError):compile_effect(a)
        a=fixture();a['groups']['future_group']=[]
        with self.assertRaises(AssetError):compile_effect(a)
    def test_nonzero_drag_fades_and_parameters_refuse(self):
        for parameters in [{'drag':1},{'drag':0,'operator end fadein':1},{'drag':0,'unknown':1}]:
            a=fixture();a['groups']['operators']=[{'function':'Movement Basic','parameters':parameters}]
            with self.assertRaises(AssetError):compile_effect(a)
    def test_capacity_is_not_silent_drop(self):
        a=fixture();a['parameters']['max_particles']=1
        with self.assertRaises(AssetError):compile_effect(a,2)
    def test_budgets_and_nonfinite(self):
        for duration,seed in [(float('nan'),17),(61,17),(2,0),(2,True)]:
            with self.assertRaises(AssetError):compile_effect(fixture(),duration,seed)
        a=fixture();a['groups']['emitters'][0]['parameters']['emission_rate']=1000
        with self.assertRaises(AssetError):compile_effect(a,2)
    def test_native_offset_axis_mapping(self):
        a=fixture();a['groups']['initializers'].append({'function':'Position Modify Offset Random','parameters':{'offset min':[1,2,3],'offset max':[1,2,3]}})
        self.assertEqual(compile_effect(a,1)['particles'][0]['position'],[.01905,3*.01905,-2*.01905])
    def test_material_data_only_and_containment(self):
        with tempfile.TemporaryDirectory()as directory:
            base=Path(directory);(base/'materials').mkdir();p=base/'materials/test.vmt';p.write_bytes(b'authored');before=p.read_bytes();r=Resources([base]);self.assertEqual(r.read('materials/test.vmt'),before);self.assertEqual(r.reads[0]['sha256'],hashlib.sha256(before).hexdigest())
            for name in ['materials/../test.vmt','lua/foo.lua','C:/secret.vmt','materials/con.vmt']:
                with self.assertRaises(AssetError):r.read(name)
            self.assertEqual(p.read_bytes(),before)
    def test_maximum_emission_per_frame_not_ignored(self):
        a=fixture();a['groups']['emitters']=[{'function':'emit_instantaneously','parameters':{'num_to_emit':3,'maximum emission per frame':2}}]
        with self.assertRaises(AssetError):compile_effect(a)
    def test_unknown_local_basis_and_sequence(self):
        for entry in [{'bias in local system':True},{'control_point_number':2},{'speed_in_local_coordinate_system_max':[1,0,0]}]:
            a=fixture();a['groups']['initializers'].append({'function':'Position Within Sphere Random','parameters':entry})
            with self.assertRaises(AssetError):compile_effect(a)
        a=fixture();a['parameters']['sequence_number']=1
        with self.assertRaises(AssetError):compile_effect(a)

if __name__=='__main__':unittest.main()

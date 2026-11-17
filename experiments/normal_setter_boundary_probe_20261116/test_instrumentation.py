"""Synthetic observer and scalar boundary tests, no native/Blender data or engines."""
import ast,math,unittest
from instrumentation import observed_import_function,scalar_stats
SOURCE="""def import_model(cm, model, mesh_obj, mesh_data, normals):
    vertices={'normal':normals}
    vtx_vertices=[0,1]
    mesh_data.normals_split_custom_set_from_vertices(vertices['normal'])
    mesh_data.validate()
    return 'unchanged'
"""
class Tests(unittest.TestCase):
    def test_callback_order_and_one_real_setter(self):
        events=[]
        class Mesh:
            def normals_split_custom_set_from_vertices(self,v):events.append(('setter',v))
            def validate(self):events.append(('validate',))
        factory,proof=observed_import_function(SOURCE)
        ns={'_HAS_NORMAL_OBSERVER':lambda phase,*a:events.append((phase,))};exec(compile(factory,'<synthetic>','exec'),ns)
        normals=object();self.assertEqual(ns['import_model'](None,None,None,Mesh(),normals),'unchanged')
        self.assertEqual([x[0] for x in events],['before_setter','setter','after_setter','before_validate','validate','after_validate']);self.assertIs(events[1][1],normals)
        self.assertTrue(proof['original_function_AST_restored']);self.assertEqual(proof['observer_calls'],4)
    def test_other_function_is_not_instrumented(self):
        factory,_=observed_import_function(SOURCE+'\ndef other(mesh_data):\n    mesh_data.validate()\n')
        self.assertEqual([n.name for n in factory.body],['import_model'])
    def test_missing_setter_refuses(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE.replace('mesh_data.normals_split_custom_set_from_vertices','other.normals_split_custom_set_from_vertices'))
    def test_duplicate_setter_refuses(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE.replace("    mesh_data.validate()","    mesh_data.normals_split_custom_set_from_vertices(vertices['normal'])\n    mesh_data.validate()"))
    def test_wrong_payload_refuses(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE.replace("vertices['normal'])","vertices['vertex'])"))
    def test_changed_setter_keywords_refuse(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE.replace("vertices['normal'])","normals=vertices['normal'])"))
    def test_validate_options_refuse(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE.replace('mesh_data.validate()','mesh_data.validate(clean_customdata=False)'))
    def test_duplicate_entry_refuses(self):
        with self.assertRaises(ValueError):observed_import_function(SOURCE+'\n'+SOURCE)
    def test_decorated_entry_refuses(self):
        with self.assertRaises(ValueError):observed_import_function('@decorator\n'+SOURCE)
    def test_finite_scalar_threshold_preserved(self):
        result=scalar_stats([0,2e-5,3e-5]);self.assertEqual(result['count'],3);self.assertEqual(result['above_2e_5'],1)
    def test_bad_scalars_refuse(self):
        for bad in (-1,math.nan,math.inf,True,'1'):
            with self.assertRaises(ValueError):scalar_stats([bad])
    def test_empty_stats_are_explicit(self):
        result=scalar_stats([]);self.assertEqual(result['count'],0);self.assertIsNone(result['max'])
if __name__=='__main__':unittest.main()

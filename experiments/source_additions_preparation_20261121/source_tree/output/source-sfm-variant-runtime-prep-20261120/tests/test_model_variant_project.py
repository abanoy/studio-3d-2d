"""Pure schema10 controls. No engine, files, assets or process calls."""
import copy
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import model_variant_project as P
import import_basis as Old

def actor():
    return {'id':'m','sha256':'a'*64,'kind':'model','metadata':{'model_variants':{
        'format':'studio_model_variants_1','asset_sha256':'a'*64,'default_skin':0,
        'skins':[{'id':0,'name':'Default'},{'id':1,'name':'Other'}],
        'groups':[{'id':0,'name':'Part','default':0,'choices':[
            {'id':0,'name':'Visible','blank':False,'nodes':[10]},
            {'id':1,'name':'Hidden','blank':True,'nodes':[]}]}],
        'surfaces':[{'node':10,'surface':0,'materials':[0,1]}]}},
        'variant_selection':{'format':'studio_variant_selection_1','skin':1,'groups':{'0':1}}}
def project(wrapped=True):
    result={'schema_version':4,'world':{'format':'studio_world_1','objects':[actor()]}}
    if wrapped:result.update(schema_version=10,variant_content_schema_version=4,variant_capability='studio_model_variants_1')
    return result

class ProjectVariantTests(unittest.TestCase):
    def test_legacy_is_byte_value_unchanged(self):
        original={'schema_version':4,'world':{'format':'studio_world_1','objects':[]}}
        self.assertEqual(P.validation_view(original),original)
        self.assertIsNot(P.validation_view(original),original)
    def test_new_view_strips_only_new_fields(self):
        original=project(); before=copy.deepcopy(original)
        view=P.validation_view(original)
        self.assertEqual(view['schema_version'],4)
        self.assertNotIn(P.MARKER,view);self.assertNotIn(P.CONTENT,view)
        self.assertNotIn(P.META,view['world']['objects'][0]['metadata'])
        self.assertNotIn(P.FIELD,view['world']['objects'][0])
        self.assertEqual(original,before)
    def test_actual_old_boundary_rejects_ten(self):
        with self.assertRaises(Old.BasisError):Old.members_with_capability(project(),lambda value:({},[]),runtime_basis_ready=True)
    def test_actual_old_boundary_accepts_stripped_view(self):
        token=object();view=P.validation_view(project())
        self.assertIs(Old.members_with_capability(view,lambda value:token,runtime_basis_ready=True),token)
    def test_unwrapped_variant_is_refused(self):
        with self.assertRaisesRegex(P.VariantError,'schema10'):P.validation_view(project(False))
    def test_wrong_capability_or_content_is_refused(self):
        for field,value in [(P.MARKER,'unknown'),(P.CONTENT,10),(P.CONTENT,True),(P.CONTENT,4.5)]:
            source=project();source[field]=value
            with self.assertRaises(P.VariantError):P.validation_view(source)
    def test_redundant_capability_is_refused(self):
        source=project();source['world']['objects']=[]
        with self.assertRaisesRegex(P.VariantError,'schema10'):P.validation_view(source)
    def test_wrong_asset_refuses_before_stripping(self):
        source=project();source['world']['objects'][0]['sha256']='b'*64
        with self.assertRaises(P.VariantError):P.validation_view(source)
    def test_bool_and_fraction_selection_are_refused(self):
        for value in (True,1.5):
            source=project();source['world']['objects'][0][P.FIELD]['skin']=value
            with self.assertRaises(P.VariantError):P.validation_view(source)
    def test_json_integral_float_ids_are_accepted_without_mutating(self):
        source=project();before=copy.deepcopy(source)
        row=source['world']['objects'][0]
        row[P.FIELD]['skin']=1.0;row[P.FIELD]['groups']['0']=1.0
        row['metadata'][P.META]['groups'][0]['choices'][0]['nodes']=[10.0]
        frozen=copy.deepcopy(source)
        self.assertEqual(P.validation_view(source)['schema_version'],4)
        self.assertEqual(source,frozen);self.assertEqual(before['schema_version'],10)
    def test_nested_scene_capability_is_checked_and_stripped(self):
        source={'schema_version':10,P.CONTENT:6,P.MARKER:'studio_model_variants_1',
            'world':{'format':'studio_world_1','objects':[]},
            'sequence_graph':{'assets':[{'id':'child','scene':project()}]}}
        self.assertEqual(P.validation_view(source)['sequence_graph']['assets'][0]['scene']['schema_version'],4)
        source['sequence_graph']['assets'][0]['scene']=project(False)
        with self.assertRaises(P.VariantError):P.validation_view(source)
    def test_huge_integer_refuses_as_controlled_error(self):
        source=project();source['world']['objects'][0][P.FIELD]['skin']=10**1000
        with self.assertRaises(P.VariantError):P.validation_view(source)
    def test_missing_blank_correspondence_and_material_coverage_refuse(self):
        for edit in ('blank','surface'):
            source=project();manifest=source['world']['objects'][0]['metadata'][P.META]
            if edit=='blank':manifest['groups'][0]['choices'][1]['nodes']=[10]
            else:manifest['surfaces'][0]['surface']=1
            with self.assertRaises(P.VariantError):P.validation_view(source)

if __name__=='__main__':unittest.main(verbosity=2)

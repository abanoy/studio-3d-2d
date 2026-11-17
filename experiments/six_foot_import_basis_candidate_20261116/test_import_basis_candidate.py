"""Meaningful synthetic contract/matrix tests; no engine or native model IO."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import importlib
import json
from pathlib import Path
import sys
import unittest

import import_basis_candidate as B

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIGEST = hashlib.sha256(b'SYNTHETIC_CONTRACT_ONLY_NOT_A_GLB').hexdigest()


def model(kind='model'):
    return {'format':'studio_model_1','id':'synthetic_human','name':'Synthetic contract fixture',
        'kind':kind,'parent_id':'','start_frame':0,'sha256':DIGEST,'path':'assets/'+DIGEST+'.glb',
        'scale':1,'position':[0,0,0],'rotation_xyzw':[0,0,0,1],'visible':True,
        'reference_only':False,'pose':{},'pose_keys':[],'draft_frame':0,'metadata':{}}


def assessment(height='2', classification='verified_complete_human'):
    return {'source_sha256':DIGEST,'height_metres':height,'classification':classification,
        'neutral_reference':True,'height_reviewed':True,'positive_uniform_root':True}


def normalized(height='2'):
    return B.prepare_fresh_import(model(),assessment(height),fresh_raw=True)[0]


def project(row=None, version=4):
    out={'schema_version':version,'video':{'width':1920,'height':1080,'fps_num':24,'fps_den':1,'duration_frames':48},
        'camera_keys':[],'layers':[],'audio':{},'editor':{'frame':0}}
    if version==3:
        out.update(model=row or {},scene={})
    else:
        out['world']={'format':'studio_world_2' if version==5 else 'studio_world_1','objects':[row] if row else []}
        if version==5:out['world']['effects']=[]
    return out


def add_reference(document):
    out=deepcopy(document);out['content_schema_version']=out['schema_version'];out['schema_version']=7
    out['reference_sheet']={'format':'synthetic_reference_contract_only'}
    return out


def add_timing(document):
    out=deepcopy(document);out['timing_content_schema_version']=out['schema_version'];out['schema_version']=8
    out['video']['duration_frames']=480
    return out


def sequences(root,children):
    out=deepcopy(root);out['schema_version']=6
    out['sequence_graph']={'format':'studio_sequences_1','clips':[],
        'assets':[{'id':'s'+str(i),'name':'Synthetic '+str(i),'clips':[],'scene':child}for i,child in enumerate(children)]}
    return out


def point(matrix,p):
    return tuple(sum(matrix[i][j]*p[j] for j in range(4)) for i in range(4))


def scale_translation(scale,xyz):
    return tuple(tuple(Q(scale) if i==j and i<3 else Q(xyz[i]) if j==3 and i<3 else Q(int(i==j))
                       for j in range(4)) for i in range(4))


class BasisContract(unittest.TestCase):
    def test_target_and_source_units_exact(self):
        self.assertEqual(Q(B.TARGET),6*Q(3048,10000))
        self.assertEqual(B.SOURCE_UNIT,Q(1905,100000))

    def test_height_ratio_properties_against_rational_oracle(self):
        # Deliberately includes nonterminating decimal quotients. The persisted
        # factor is50-digit rounded text; it does not claim an exact rational fit.
        for centimetres in range(30,301):
            height=Decimal(centimetres)/100
            fixture=normalized(str(height).rstrip('0').rstrip('.') if '.'in str(height)else str(height))
            actual=Q(fixture['asset_basis']['factor'])*Q(height)
            self.assertLess(abs(actual-Q(1143,625)),Q(1,10**46))
            self.assertEqual(fixture['scale'],1)

    def test_factor_guard_boundaries(self):
        self.assertEqual(B.factor_for('0.00018288'),'10000')
        self.assertEqual(B.factor_for('1828.8'),'0.001')
        for value in ['0.000182879','1828.8001']:
            with self.assertRaises(B.BasisError):B.factor_for(value)

    def test_canonical_decimal_negative_controls(self):
        for value in [None,True,1.2,'NaN','Infinity','-1','+1','1e0','01','1.0','0','0.0','.1','1.','1,2',' 1','1\n','9'*97]:
            with self.subTest(value=value),self.assertRaises(B.BasisError):B.decimal_text(value)

    def test_full_complete_human_conversion_preserves_every_other_field(self):
        original=model();original['metadata']={'native_parameters':{'scale':0.01905,'retained_rules':49}}
        before=deepcopy(original)
        converted,status=B.prepare_fresh_import(original,assessment(),fresh_raw=True)
        self.assertEqual(status,'standardized_complete_human');self.assertEqual(original,before)
        basis=converted.pop('asset_basis');self.assertEqual(converted,before)
        self.assertEqual(basis['source_sha256'],DIGEST)

    def test_per_model_preserve_override(self):
        original=model();result,status=B.prepare_fresh_import(original,assessment(),fresh_raw=True,intent='preserve_original')
        self.assertEqual((result,status),(original,'owner_preserved_original'))

    def test_complete_human_override_requires_reviewed_complete_input(self):
        original=model();reviewed=assessment(classification='reviewed_complete_human')
        self.assertEqual(B.prepare_fresh_import(original,reviewed,fresh_raw=True)[1],'uncertain_identity')
        result,status=B.prepare_fresh_import(original,reviewed,fresh_raw=True,intent='complete_human_override')
        self.assertEqual(status,'standardized_complete_human')
        self.assertEqual(result['asset_basis']['decision'],'explicit_complete_human_override')

    def test_partial_map_tool_prop_multiple_figure_exclusions_survive_override(self):
        for category in ['partial','prop','tool','map','multiple_figures']:
            for intent in ['standard_complete_human','complete_human_override']:
                original=model();result,status=B.prepare_fresh_import(original,assessment(classification=category),fresh_raw=True,intent=intent)
                self.assertEqual(result,original);self.assertEqual(status,'ineligible_identity')
        for kind in ['environment','group']:
            original=model(kind);self.assertEqual(B.prepare_fresh_import(original,assessment(),fresh_raw=True)[0],original)

    def test_uncertain_input_keeps_original_size(self):
        original=model();result,status=B.prepare_fresh_import(original,assessment(classification='uncertain'),fresh_raw=True)
        self.assertEqual((result,status),(original,'uncertain_identity'))

    def test_saved_has_and_legacy_height_diagnostics_are_identity(self):
        original=model();original['scale']=2.5;original['metadata']['import_height']={'factor':'0.5','target':'1.8288'}
        original['pose_keys']=[{'frame':24,'transform':{'scale':3}}]
        result,status=B.prepare_fresh_import(original,assessment(),fresh_raw=False)
        self.assertEqual((result,status),(original,'saved_or_legacy_identity'))
        self.assertEqual(B.factor(original),1)

    def test_existing_basis_does_not_remeasure_or_compound(self):
        original=normalized();result,status=B.prepare_fresh_import(original,{},fresh_raw=False)
        self.assertEqual((result,status),(original,'already_standardized'))
        result['metadata']['new']='copy';self.assertNotIn('new',original['metadata'])

    def test_stale_or_unreviewed_measurement_refuses_atomically(self):
        for field,value in [('source_sha256','0'*64),('neutral_reference',False),('height_reviewed',False),('positive_uniform_root',False)]:
            original=model();before=deepcopy(original);a=assessment();a[field]=value
            with self.assertRaises(B.BasisError):B.prepare_fresh_import(original,a,fresh_raw=True)
            self.assertEqual(original,before)

    def test_fresh_import_never_flattens_authored_scale_or_keys(self):
        for field,value in [('scale',2),('pose_keys',[{'frame':0}]),('scale',True)]:
            original=model();original[field]=value
            with self.assertRaises(B.BasisError):B.prepare_fresh_import(original,assessment(),fresh_raw=True)

    def test_basis_tamper_and_derivative_change_refuse(self):
        for field,value in [('factor','0.5'),('target_metres','2'),('source_sha256','a'*64),('measured_from_sha256','b'*64),('decision','guess'),('classification','partial')]:
            data=normalized();data['asset_basis'][field]=value
            with self.assertRaises(B.BasisError):B.factor(data,capability=True)
        data=normalized();data['sha256']='c'*64
        with self.assertRaises(B.BasisError):B.factor(data,capability=True)
        data=normalized();data['asset_basis']['unknown']=True
        with self.assertRaises(B.BasisError):B.factor(data,capability=True)

    def test_model_capability_and_kind_refusals(self):
        for kind in ['environment','group']:
            row=normalized();row['kind']=kind
            with self.assertRaises(B.BasisError):B.factor(row,capability=True)
        with self.assertRaises(B.BasisError):B.factor(normalized())

    def test_schema3_to8_wrappers_preserve_payload_and_are_idempotent(self):
        roots=[project(normalized(),3),project(normalized(),4),project(normalized(),5),
               sequences(project(normalized()),[project(model())]),add_reference(project(normalized())),
               add_timing(project(normalized())),add_timing(add_reference(project(normalized())))]
        for original in roots:
            before=deepcopy(original);encoded=B.encode_capability(original)
            self.assertEqual(original,before);self.assertEqual(encoded['schema_version'],9)
            self.assertEqual(encoded['basis_content_schema_version'],original['schema_version'])
            restored=deepcopy(encoded);restored['schema_version']=restored.pop('basis_content_schema_version');restored.pop('import_basis_capability')
            self.assertEqual(restored,original);self.assertEqual(B.encode_capability(encoded),encoded)
            self.assertTrue(B.inspect_capability(encoded)['basis_required'])

    def test_legacy_projects_are_not_upgraded_without_basis(self):
        for original in [project(model(),3),project(model()),project(model(),5),add_reference(project(model())),add_timing(project(model()))]:
            self.assertEqual(B.encode_capability(original),original)

    def test_child_capability_is_local_and_parent_also_requires_wrapper(self):
        child=project(normalized());root=sequences(project(model()),[child,project(model())])
        wrapped=B.encode_capability(root);self.assertEqual(wrapped['schema_version'],9)
        self.assertEqual(wrapped['sequence_graph']['assets'][0]['scene']['schema_version'],9)
        self.assertEqual(wrapped['sequence_graph']['assets'][1]['scene']['schema_version'],4)
        bad=deepcopy(wrapped);c=bad['sequence_graph']['assets'][0]['scene'];c['schema_version']=c.pop('basis_content_schema_version');c.pop('import_basis_capability')
        with self.assertRaises(B.BasisError):B.inspect_capability(bad)
        bad=deepcopy(wrapped);bad['schema_version']=bad.pop('basis_content_schema_version');bad.pop('import_basis_capability')
        with self.assertRaises(B.BasisError):B.inspect_capability(bad)

    def test_malformed_and_redundant_capabilities_refuse(self):
        wrapped=B.encode_capability(project(normalized()))
        for field,value in [('basis_content_schema_version',9),('basis_content_schema_version',True),('import_basis_capability','unknown')]:
            bad=deepcopy(wrapped);bad[field]=value
            with self.assertRaises(B.BasisError):B.inspect_capability(bad)
        bad=project();bad.update(schema_version=9,basis_content_schema_version=4,import_basis_capability=B.FORMAT)
        with self.assertRaises(B.BasisError):B.inspect_capability(bad)
        bad=project();bad['basis_content_schema_version']=4
        with self.assertRaises(B.BasisError):B.inspect_capability(bad)
        bad=wrapped;bad['timing_content_schema_version']=4
        with self.assertRaises(B.BasisError):B.inspect_capability(bad)

    def test_existing_shared_object_and_child_graph_limits_remain(self):
        child=project();child['world']['objects']=[model() for _ in range(64)]
        self.assertEqual(B.inspect_capability(child)['object_count'],64)
        root=sequences(project(model()),[child])
        with self.assertRaises(B.BasisError):B.encode_capability(root)
        with self.assertRaises(B.BasisError):B.encode_capability(sequences(project(),[project()]*5))
        nested=sequences(project(),[sequences(project(),[project()])])
        with self.assertRaises(B.BasisError):B.encode_capability(nested)
        for child in [add_reference(project(normalized())),add_timing(add_reference(project(normalized())))]:
            with self.assertRaises(B.BasisError):B.encode_capability(sequences(project(),[child]))

    def test_old_python_reader_refuses_9_but_ignores_ungated_model_field(self):
        # This exercises the real unchanged old reader on synthetic metadata.
        # Its acceptance of the old-version extra field proves why gating is vital.
        sys.path.insert(0,str(ROOT))
        old=importlib.import_module('tools.has_project')
        legacy_with_ignored_field=project(normalized())
        assets,_=old.members(legacy_with_ignored_field)
        self.assertIn('assets/'+DIGEST+'.glb',assets)
        with self.assertRaises(old.HasError):old.members(B.encode_capability(legacy_with_ignored_field))
        with self.assertRaises(B.BasisError):B.inspect_capability(legacy_with_ignored_field)

    def test_container_facade_retains_old_resource_checks_and_original_manifest(self):
        sys.path.insert(0,str(ROOT));old=importlib.import_module('tools.has_project')
        wrapped=B.encode_capability(project(normalized()));before=deepcopy(wrapped)
        actual=B.members_with_capability(wrapped,old.members)
        expected=old.members(project(model()))
        self.assertEqual(actual,expected);self.assertEqual(wrapped,before)
        bad=deepcopy(wrapped);bad['world']['format']='unknown'
        with self.assertRaises(old.HasError):B.members_with_capability(bad,old.members)
        calls=[]
        with self.assertRaises(B.BasisError):B.members_with_capability(project(normalized()),lambda x:calls.append(x))
        self.assertEqual(calls,[])

    def test_transient_validation_view_preserves_underlying_timing_requirement(self):
        sys.path.insert(0,str(ROOT));extended=importlib.import_module('tools.extended_timing')
        original=sequences(project(),[add_timing(project(normalized()))])
        wrapped=B.encode_capability(original)
        view=B._legacy_validation_view(wrapped)
        self.assertEqual(view,original)
        self.assertTrue(extended.required(view))
        old=importlib.import_module('tools.has_project')
        with self.assertRaises(old.HasError):B.members_with_capability(wrapped,old.members)

    def test_composition_scales_imported_offset_not_artist_position(self):
        raw=((Q(0),Q(0),Q(2),Q(3)),(Q(0),Q(2),Q(0),Q(4)),(Q(-2),Q(0),Q(0),Q(5)),(Q(0),Q(0),Q(0),Q(1)))
        row=normalized('2');configured=B.ImportRoot.configured(raw,row,capability=True)
        artist=scale_translation(3,(10,20,30));result=configured.evaluate(artist)
        c=Q(1143,1250)
        self.assertEqual(point(result,(Q(1),Q(2),Q(3),Q(1))),
                         (10+3*c*(3+2*3),20+3*c*(4+2*2),30+3*c*(5-2*1),1))
        self.assertEqual(configured.raw_root,raw)

    def test_scale_keys_parent_scale_and_repeat_do_not_compound_basis(self):
        row=normalized('2');raw=B.identity_matrix();root=B.ImportRoot.configured(raw,row,capability=True)
        for user_scale in [Q(1,2),Q(1),Q(2),Q(7,3),Q(1)]:
            artist=scale_translation(user_scale,(5,0,0));world=B.multiply(scale_translation(3,(0,0,0)),root.evaluate(artist))
            height=point(world,(0,2,0,1))[1]-point(world,(0,0,0,1))[1]
            self.assertEqual(height,Q(1143,625)*user_scale*3)
            self.assertEqual(root.effective_base(),root.effective_base())
        with self.assertRaises(B.BasisError):B.ImportRoot.configured(root,row,capability=True)

    def test_source_rule_conversion_uses_actual_basis_exactly_once(self):
        factor=Q(B.factor(normalized('2'),capability=True));native_length=Q(20);user=Q(3,2);parent=Q(2)
        world_length=native_length*B.SOURCE_UNIT*factor*user*parent
        self.assertEqual(world_length,Q(381,1000)*Q(1143,1250)*3)
        self.assertNotEqual(world_length,native_length*(B.SOURCE_UNIT*factor)*factor*user*parent)


def main():
    result=unittest.TestResult()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(BasisContract)
    names=[case.id().split('.')[-1] for case in suite]
    suite.run(result)
    output={'format':'has_six_foot_basis_candidate_cpu_1','status':'SYNTHETIC_CONTRACT_ONLY',
        'passed':result.wasSuccessful(),'test_methods':result.testsRun,'named_tests':names,
        'height_ratio_rational_cases':271,'failures':[{'test':str(t),'error':e}for t,e in result.failures],
        'errors':[{'test':str(t),'error':e}for t,e in result.errors],
        'engine_or_converter_or_native_model_runs':0,'installed_in_application':False}
    target=HERE/'CPU_RESULT_v2.json'
    with target.open('x',encoding='utf-8') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('named_tests','failures','errors')}))
    for t,e in result.failures+result.errors:print(str(t)+'\n'+e)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())

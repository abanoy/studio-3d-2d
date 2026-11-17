"""Preregister expected scalar/text outcomes for later isolated GDScript execution."""
from copy import deepcopy
from decimal import Decimal,Context,ROUND_HALF_EVEN,localcontext
from pathlib import Path
import hashlib
import json
import random

import import_basis_v2 as B
from decimal_string_reference import rounded_ratio
from test_python_v2 import project,model as model_fixture,normalized,sequences,add_reference,add_timing

HERE=Path(__file__).resolve().parent
SHA=hashlib.sha256(b'SYNTHETIC_CONTRACT_ONLY_NOT_A_GLB').hexdigest()


def main():
    rows=[]
    def add(name,operation,request,expected):
        assert not any(row['name']==name for row in rows)
        rows.append(dict(name=name,operation=operation,request=request,expected=expected))
    for centimetres in range(30,301):
        height=B.canonical(Decimal(centimetres)/100)
        expected=B.factor_for(height)
        parsed=B.decimal_text(height);places=max(0,-parsed.as_tuple().exponent)
        numerator='18288'+'0'*places;denominator=str(int(parsed*10**places))+'0000'
        assert rounded_ratio(numerator,denominator)==expected
        add('height_cm_'+str(centimetres),'factor',{'height':height},{'factor_text':expected})
    for text in ['0.00018288','1828.8','7','1.8288','0.000182879','1828.8001','0','0.0','1.0','01','1e0','NaN','+1','-1','.5','1.','1\n','9'*97,'9'*96,'1'+'0'*95,'0.'+'0'*93+'1','0.'+'0'*92+'11']:
        try:expected={'factor_text':B.factor_for(text)}
        except B.BasisError:expected={'error':True}
        add('factor_edge_'+str(len(rows)),'factor',{'height':text},expected)
    for value in [None,True,False,1,1.2,[],{}]:
        add('factor_type_'+str(len(rows)),'factor',{'height':value},{'error':True})
    # Deliberate tie, carry and tiny/large cases exercise50-digit rounding directly.
    ratios=[('1','7'),('1','2'),('1','8'),('1'+'0'*49+'5','10'),('1'+'0'*48+'15','10'),
            ('9'*50+'5','10'),('1','1'+'0'*95),('9'*96,'3')]
    rng=random.Random(6282026)
    ratios.extend((str(rng.randrange(1,10**60)),str(rng.randrange(1,10**60)))for _ in range(64))
    context=Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999)
    for n,d in ratios:
        with localcontext(context):expected=B.canonical(Decimal(n)/Decimal(d))
        assert rounded_ratio(n,d)==expected
        add('rounded_ratio_'+str(len(rows)),'ratio',{'numerator':n,'denominator':d},{'text':expected})
    record=B.make_basis(SHA,'7')
    base={'sha256':SHA,'kind':'model','asset_basis':record}
    def admission(name,model,capability=False,ready=False):
        try:
            value=B.factor(model,capability=capability)
            if'asset_basis'in model and not ready:raise B.BasisError('Runtime unavailable')
            if type(ready)is not bool:raise B.BasisError('Bad readiness')
            expected={'factor_text':str(value)if'asset_basis'in model else'1','legacy_identity':'asset_basis'not in model}
        except B.BasisError:expected={'error':True}
        add(name,'model',{'model':model,'scene_capability':capability,'runtime_basis_ready':ready},expected)
    admission('active_ready_contract_only',deepcopy(base),True,True)
    admission('active_default_runtime_refusal',deepcopy(base),True,False)
    admission('active_without_scene_permission',deepcopy(base),False,True)
    admission('legacy_absent_basis',{'metadata':{'import_height':{'factor':'2'}}})
    for flag in ['false',0,1,None,[],{}]:
        admission('bad_capability_'+str(len(rows)),deepcopy(base),flag,True)
        admission('bad_runtime_readiness_'+str(len(rows)),deepcopy(base),True,flag)
    for key,value in [('factor','0.5'),('measured_from_sha256','0'*64),('source_sha256','a'*64),('decision','guess'),('target_metres','2')]:
        model=deepcopy(base);model['asset_basis'][key]=value;admission('record_tamper_'+key,model,True,True)
    for kind in ['environment','group']:
        model=deepcopy(base);model['kind']=kind;admission('kind_'+kind,model,True,True)
    model=deepcopy(base);model['asset_basis']['unknown']=True;admission('unknown_basis_field',model,True,True)
    def schema_case(name,operation,document):
        try:
            expected=B.inspect_capability(document)if operation=='inspect'else{'document':B.encode_capability(document)}
        except B.BasisError:expected={'error':True}
        add(name,operation,{'document':document},expected)
    variants=[project(normalized(),3),project(normalized()),project(normalized(),5),
        sequences(project(normalized()),[project(model_fixture())]),add_reference(project(normalized())),
        add_timing(project(normalized())),add_timing(add_reference(project(normalized())))]
    for index,document in enumerate(variants):
        schema_case('schema_encode_'+str(index),'encode',document)
        schema_case('schema_inspect_'+str(index),'inspect',B.encode_capability(document))
        schema_case('schema_missing_capability_'+str(index),'inspect',document)
    for index,document in enumerate([project(model_fixture(),3),project(model_fixture()),project(model_fixture(),5),add_reference(project(model_fixture())),add_timing(project(model_fixture()))]):
        schema_case('legacy_identity_encode_'+str(index),'encode',document)
    nested=B.encode_capability(sequences(project(model_fixture()),[project(normalized()),project(model_fixture())]))
    schema_case('nested_valid_local_permissions','inspect',nested)
    bad=deepcopy(nested);child=bad['sequence_graph']['assets'][0]['scene'];child['schema_version']=child.pop('basis_content_schema_version');child.pop('import_basis_capability')
    schema_case('nested_parent_cannot_authorize_child','inspect',bad)
    bad=deepcopy(nested);bad['schema_version']=bad.pop('basis_content_schema_version');bad.pop('import_basis_capability')
    schema_case('nested_child_requires_parent_envelope','inspect',bad)
    for field,value in [('basis_content_schema_version',True),('basis_content_schema_version',9),('import_basis_capability','unknown')]:
        bad=B.encode_capability(project(normalized()));bad[field]=value;schema_case('schema_bad_'+field+str(len(rows)),'inspect',bad)
    bad=project();bad.update(schema_version=9,basis_content_schema_version=4,import_basis_capability=B.FORMAT)
    schema_case('schema_redundant_wrapper','inspect',bad)
    schema_case('reference_sequence_child_still_refused','encode',sequences(project(),[add_reference(project(normalized()))]))
    schema_case('five_sequence_assets_still_refused','encode',sequences(project(),[project()]*5))
    schema_case('nested_graph_still_refused','encode',sequences(project(),[sequences(project(),[project()])]))
    child=project();child['world']['objects']=[model_fixture()for _ in range(64)]
    schema_case('shared64_objects_allowed_by_basis_gate','inspect',child)
    schema_case('shared65_objects_refused_by_basis_gate','encode',sequences(project(model_fixture()),[child]))
    corpus={'format':'has_six_foot_gd_parity_corpus_1','status':'EXPECTED_ONLY_GDSCRIPT_UNPARSED_UNRUN',
        'rows':rows,'count':len(rows),'synthetic_only':True}
    with(HERE/'PARITY_CORPUS_v3.json').open('x',encoding='utf-8')as f:json.dump(corpus,f,indent=2);f.write('\n')
    result={'format':'has_six_foot_cpu_parity_preflight_1','passed':True,'expected_gd_cases':len(rows),
        'height_ratio_cases':271,'independent_rounded_ratio_cases':len(ratios),
        'decimal_vs_integer_string_reference_equal':True,'godot_parser_or_runtime_executed':False}
    with(HERE/'PARITY_CPU_RESULT_v3.json').open('x',encoding='utf-8')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()

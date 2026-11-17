"""CPU reproduction of transport/type semantics, not a GDScript execution."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import re

HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'six_foot_import_basis_gd_candidate_20261116'
spec = importlib.util.spec_from_file_location('sealed_basis_python', OLD/'import_basis_v2.py')
B = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = B
spec.loader.exec_module(B)
MAX_SAFE = 2**53
checks = {}


def mark(name, ok):
    assert name not in checks
    checks[name] = bool(ok)
    assert ok, name


def number_equal(a, e):
    if type(a) not in (int,float) or type(e) not in (int,float):
        return False
    if (type(a) is float and not math.isfinite(a)) or (type(e) is float and not math.isfinite(e)):
        return False
    if type(a) is type(e):
        return a == e
    integer = a if type(a) is int else e
    return -MAX_SAFE <= integer <= MAX_SAFE and float(a) == float(e)


def differences(a, e, path='$', depth=0, transport=True):
    if depth > 64:
        return [{'path':path,'reason':'depth_limit'}]
    if type(a) in (int,float) and type(e) in (int,float):
        eq = number_equal(a,e)
        if eq and (transport or type(a) is type(e)):
            return []
        return [{'path':path,'actual_type':type(a).__name__,'expected_type':type(e).__name__,
                 'reason':'number_representation' if eq else 'number_value_or_nonfinite',
                 'exact_numeric_equal':eq,'actual_number':a,'expected_number':e}]
    if type(a) is not type(e):
        return [{'path':path,'reason':'type'}]
    if type(a) is dict:
        out=[]
        if len(a)!=len(e): out.append({'path':path,'reason':'object_key_count'})
        for key in a:
            if type(key) is not str or key not in e:
                out.append({'path':path,'reason':'unexpected_or_nonstring_key'})
        for key in e:
            if type(key) is not str or key not in a:
                out.append({'path':path,'reason':'missing_or_nonstring_key'})
            else: out.extend(differences(a[key],e[key],path+'.'+key,depth+1,transport))
        return out
    if type(a) is list:
        if len(a)!=len(e): return [{'path':path,'reason':'array_length'}]
        return [d for i,(v,w) in enumerate(zip(a,e)) for d in differences(v,w,f'{path}[{i}]',depth+1,transport)]
    if a is not None and type(a) not in (bool,str):
        return [{'path':path,'reason':'non_json_type'}]
    return [] if a==e else [{'path':path,'reason':'value'}]


def main():
    corpus=json.loads((HERE/'PARITY_CORPUS_v3.json').read_text(encoding='utf-8'),parse_int=float,parse_float=float)
    mark('corpus434',len(corpus['rows'])==434)
    predictions={}
    for row in corpus['rows']:
        if row['operation']!='encode' or row['expected'].get('error',False): continue
        actual={'document':B.encode_capability(row['request']['document'])}
        raw=differences(actual,row['expected'],transport=False)
        semantic=differences(actual,row['expected'])
        mark(row['name']+'.exact_json_value_equal',not semantic)
        if row['name'].startswith('schema_encode_'):
            mark(row['name']+'.only_new_int9',len(raw)==1 and raw[0]['path']=='$.document.schema_version'
                 and raw[0]['actual_type']=='int' and raw[0]['expected_type']=='float'
                 and raw[0]['exact_numeric_equal'] and raw[0]['actual_number']==9 and raw[0]['expected_number']==9)
        else:
            mark(row['name']+'.legacy_no_type_delta',not raw)
        predictions[row['name']]={'old_strict_comparison_would_pass':not raw,'exact_json_value_comparison_would_pass':not semantic,'strict_differences':raw}
    failed=json.loads((HERE/'failed_predecessor/result.json').read_text(encoding='utf-8'))
    observed={k for k,v in failed['named_checks'].items() if not v}
    predicted={'corpus.'+k for k,v in predictions.items() if not v['old_strict_comparison_would_pass']}
    mark('predicted_strict_failures_match_recorded_seven',predicted==observed and len(predicted)==7)
    cases=[('int_float',9,9.,True),('float_int',9.,9,True),('nested',{'a':[{'b':9}]},{'a':[{'b':9.}]},True),
        ('safe_positive',2**53,float(2**53),True),('safe_negative',-2**53,-float(2**53),True),
        ('unsafe_alias',2**53+1,float(2**53),False),('unsafe_negative',-(2**53+1),-float(2**53),False),
        ('large_int_exact',2**53+1,2**53+1,True),('true_one',True,1,False),('false_zero',False,0.,False),
        ('string_number','9',9,False),('changed_number',9,10.,False),('changed_fraction',9,9.000000000000002,False),
        ('nan',float('nan'),float('nan'),False),('inf',float('inf'),float('inf'),False),
        ('negative_inf',-float('inf'),-float('inf'),False),('null',None,None,True),('null_false',None,False,False),
        ('case','Model','model',False),('array_order',[1,2],[2.,1.],False),('array_length',[1],[1.,2.],False),
        ('missing_null',{}, {'a':None},False),('extra_key',{'a':None},{},False),
        ('object_order',{'a':1,'b':2},{'b':2.,'a':1.},True),('nonstring_key',{1:9},{'1':9.},False),
        ('native_type',(0,0,0),(0,0,0),False)]
    nested=None
    for _ in range(66): nested=[nested]
    cases.append(('depth_limit',nested,nested,False))
    for name,a,e,equal in cases:
        mark('mirror_comparator.'+name,(not differences(a,e))==equal)
    old=(OLD/'basis_domain_unit.gd').read_text(encoding='utf-8')
    new=(HERE/'basis_domain_unit.gd').read_text(encoding='utf-8')
    transforms=lambda s:s[s.index('\tvar sha :='):s.index('\tvar result :=')]
    mark('all_ten_transform_checks_byte_text_unchanged',transforms(old)==transforms(new))
    mark('encoder_entire_file_byte_unchanged',(HERE/'import_basis_domain.gd').read_bytes()==(OLD/'import_basis_domain.gd').read_bytes())
    mark('corpus_entire_file_byte_unchanged',(HERE/'PARITY_CORPUS_v3.json').read_bytes()==(OLD/'PARITY_CORPUS_v3.json').read_bytes())
    contract_body=new.split('func run_comparator_contracts() -> void:',1)[1].split('func checked_job()',1)[0]
    mark('gd28_contracts_present',len(re.findall(r'^\tcompare_contract\(',contract_body,re.M))+len(re.findall(r'^\tmark\("transport.comparator\.',contract_body,re.M))==28)
    mark('gd444_plus28_plus8_is480',444+28+8==480 and new.count('named.size()==480')==2)
    mark('domain_no_tolerance_edit','EPS' not in (HERE/'comparison_functions.gd.txt').read_text(encoding='utf-8'))
    result={'format':'has_six_foot_json_transport_cpu_diagnosis_1','passed':all(checks.values()),'checks':len(checks),
        'named_checks':checks,'predicted_encode_outcomes':predictions,
        'actual_old_godot_run':{'checks':444,'failures':7,'result_sha256':hashlib.sha256((HERE/'failed_predecessor/result.json').read_bytes()).hexdigest()},
        'gd_successor_executed':False,'gd_successor_parsed':False,'python_oracle_cpu_only':True,
        'prediction_is_actual_gd_payload_evidence':False}
    (HERE/'CPU_DIAGNOSIS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'predicted_failures':sorted(predicted),'gd_successor_executed':False}))


if __name__=='__main__': main()

"""Source joins and aggregate timing context only; no runtime/parser launches."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INPUT=ROOT/'experiments/source_native_five_port_candidate_v2_20261115'


def sha(body):return hashlib.sha256(body).hexdigest()


def functions(text):
    matches=list(re.finditer(r'^(?:static )?func ([a-zA-Z0-9_]+)\(',text,re.M))
    return {m.group(1):text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)].strip() for i,m in enumerate(matches)}


def main():
    provenance=json.loads((HERE/'PROVENANCE.json').read_bytes())
    unchanged={name:sha((INPUT/name).read_bytes())==digest for name,digest in provenance['inputs'].items()}
    assert all(unchanged.values())
    sealed=json.loads((INPUT/'INDEX.json').read_bytes())
    for row in sealed['files']:assert sha((INPUT/row['path']).read_bytes())==row['sha256'],row['path']
    actual_stage=ROOT/'output/native-five-stage-attempt1/Studio/src'
    actual_stage_matches={name:sha((actual_stage/name).read_bytes())==provenance['inputs'][name] for name in ('source_secondary.gd','source_chain_math.gd','secondary_live.gd')}
    assert all(actual_stage_matches.values())
    original=(INPUT/'source_secondary.gd').read_text(encoding='utf-8')
    blocks=functions(original)
    deliberate={'create','capture_baseline','dispose'}
    rows={}
    for variant in ('strict','closure'):
        text=(HERE/('source_secondary_'+variant+'.gd')).read_text(encoding='utf-8')
        candidate=functions(text)
        joins={name:candidate.get(name)==block for name,block in blocks.items() if name not in deliberate}
        assert all(joins.values()),joins
        assert not re.search(r'^\s*(class_name\b|@tool\b)',text,re.M)
        assert 'const EPS := 0.00002' in text
        assert 'frame64(local) if _solver_bone_specs.has(id) else raw_frame_guard(local)' in text if variant=='closure' else 'frame64(local)' in text
        rows[variant]={'sha256':sha((HERE/('source_secondary_'+variant+'.gd')).read_bytes()),'unchanged_functions':joins,'full_source_guards_and_step_byte_text_unchanged':joins['step'] and joins['context_error'] and joins['binding_stamp'] and joins['offered'],'unparsed_unrun':True}
    old_prefix=blocks['frame64'].split('\n',1)[1].split('\tvar x: Array = units[0]')[0].strip()
    new_raw=functions((HERE/'source_secondary_closure.gd').read_text())['raw_frame_guard']
    new_prefix=new_raw[new_raw.index('\tif not value.origin'):new_raw.index('\treturn {"scale":size}')].strip()
    assert old_prefix==new_prefix
    assert (HERE/'source_chain_math.gd').read_bytes()==(INPUT/'source_chain_math.gd').read_bytes()
    for path in HERE.glob('*.py'):ast.parse(path.read_bytes(),filename=str(path))
    writer=ROOT/'output/native-five-stage-attempt1/Studio/output/native-five-gui-attempt1/writer/result.json'
    actual=json.loads(writer.read_bytes())
    timings={}
    for name,row in actual.get('metrics',{}).items():
        if isinstance(row,dict) and isinstance(row.get('native_step_processing'),dict):
            sample=row['native_step_processing']
            timings[name]={key:sample[key] for key in ('mean_usec','max_usec','samples')}
    context={'format':'native_five_performance_actual_context_1','writer_result_sha256':sha(writer.read_bytes()),'checks':actual['checks'],'failures':actual['failures'],'actual_writer_label':'FAILED_REMAINS_FAILED','native_step_processing_by_profile':timings,'120Hz_tick_budget_usec':1000000/120,'scope':'Prior unchanged sealedv2 actual timings only. These draft variants have not been parsed/executed/profiled. No FPS criterion is retroactively added or waived.'}
    (HERE/'PERFORMANCE_CONTEXT.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
    result={'format':'native_five_performance_static_1','sealed_v2_inputs_unchanged':unchanged,'sealed_v2_all32_payloads_hash_verified':len(sealed['files']),'actual_failed_writer_stage_code_matches_sealed_v2':actual_stage_matches,'variants':rows,'unchanged_scalar_core_sha256':sha((HERE/'source_chain_math.gd').read_bytes()),'raw_guard_is_exact_frame64_prefix':True,'GDScript_parsed':False,'engine_executed':False,'Git_or_CIM_executed':False}
    (HERE/'STATIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_source_joins_passed':True,'unchanged_functions_per_variant':len(next(iter(rows.values()))['unchanged_functions']),'actual_prior_writer_checks':actual['checks'],'actual_prior_writer_failures':actual['failures'],'timing_profiles':len(timings),'core_sha256':result['unchanged_scalar_core_sha256']},indent=2))


if __name__=='__main__':main()

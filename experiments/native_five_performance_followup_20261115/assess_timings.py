"""Retain aggregate root-run timings and source-only strict2 proof joins."""
from pathlib import Path
import ast
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PATHS={
    'original_gui':'output/native-five-stage-attempt1/Studio/output/native-five-gui-attempt1/writer/result.json',
    'strict_gui_diagnostic':'output/native-five-stage-attempt2/Studio/output/opposite-diagnostic-attempt1/result.json',
    'original_state':'output/native-five-stage-attempt1/Studio/output/source-native-five-state-20261116T032753090430/result.json',
    'strict_state':'output/native-five-stage-attempt2/Studio/output/source-native-five-state-20261116T034910930092/result.json',
}


def sha(body):return hashlib.sha256(body).hexdigest()


def functions(text):
    matches=list(re.finditer(r'^(?:static )?func ([a-zA-Z0-9_]+)\(',text,re.M))
    return {m.group(1):text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)].strip() for i,m in enumerate(matches)}


def main():
    context={};raw_results={}
    for name,relative in PATHS.items():
        path=ROOT/relative;body=path.read_bytes();data=json.loads(body);raw_results[name]=data
        rows={}
        for profile,row in data.get('metrics',{}).items():
            if not isinstance(row,dict) or not isinstance(row.get('native_step_processing'),dict):continue
            timing=row['native_step_processing'];rows[profile]={key:timing[key] for key in ('mean_usec','max_usec','samples')}
            for key in ('advance_mean_usec','advance_max_usec','advance_samples'):
                if key in row:rows[profile][key]=row[key]
        context[name]={'relative_path':relative,'sha256':sha(body),'checks':data['checks'],'failures':data['failures'],'metrics':rows}
    comparisons={}
    for workload,old_name,new_name in [('gui','original_gui','strict_gui_diagnostic'),('rotating_headless','original_state','strict_state')]:
        rows={}
        for profile,old in context[old_name]['metrics'].items():
            new=context[new_name]['metrics'][profile]
            row={'old_mean_usec':old['mean_usec'],'strict_mean_usec':new['mean_usec'],'observed_reduction_percent':100*(1-new['mean_usec']/old['mean_usec']),'old_max_usec':old['max_usec'],'strict_max_usec':new['max_usec'],'samples_each':new['samples']}
            if 'advance_mean_usec' in old:row.update(old_advance_mean_usec=old['advance_mean_usec'],strict_advance_mean_usec=new['advance_mean_usec'])
            if workload=='gui':row['captured_points_sha_equal']=raw_results[old_name]['metrics'][profile]['points_sha256']==raw_results[new_name]['metrics'][profile]['points_sha256']
            rows[profile]=row
        old_mean=sum(row['old_mean_usec'] for row in rows.values())/len(rows)
        new_mean=sum(row['strict_mean_usec'] for row in rows.values())/len(rows)
        comparisons[workload]={'profiles':rows,'equal_sample_weighted_old_mean_usec':old_mean,'equal_sample_weighted_strict_mean_usec':new_mean,'observed_reduction_percent':100*(1-new_mean/old_mean)}
    strict_path=ROOT/'experiments/native_five_performance_candidate_20261115/source_secondary_strict.gd'
    successor=HERE/'source_secondary_strict2.gd'
    before=functions(strict_path.read_text());after=functions(successor.read_text())
    allowed={'create','capture_baseline','dispose'}
    joins={name:after.get(name)==block for name,block in before.items() if name not in allowed}
    assert all(joins.values()),joins
    create=after['create']
    ordering={
        'full69_guard_before_capture':create.index('candidate._baseline_guard = guard.actor')<create.index('candidate.capture_baseline()'),
        'capture_before_any_reset':create.index('candidate.capture_baseline()')<create.index('candidate._chain.reset('),
        'capture_before_alive':create.index('candidate.capture_baseline()')<create.index('candidate._alive = true'),
        'capture_before_runner_return':create.index('candidate.capture_baseline()')<create.index('return {"runner":candidate}'),
    }
    assert all(ordering.values())
    stage=ROOT/'output/native-five-stage-attempt2/Studio/src/source_secondary.gd'
    assert sha(stage.read_bytes())==sha(strict_path.read_bytes())
    for path in HERE.glob('*.py'):ast.parse(path.read_bytes(),filename=str(path))
    result={'format':'native_five_strict_timing_followup_1','source':'Aggregate scalars/hashes from root-owned completed runs; no new engine execution.','context':context,'comparisons':comparisons,'nominal120Hz_interval_usec':1000000/120,'FPS_pass_claimed':False,'strict2_status':'UNPARSED_UNRUN_UNAPPLIED','strict_actual_stage_sha256':sha(stage.read_bytes()),'strict2_sha256':sha(successor.read_bytes()),'unchanged_functions':joins,'create_order_proof':ordering,'recommendation':'Try narrowly deduplicated strict2 next with existing266state/GUI/preservation/closure gates. Do not switch to hybrid or invent FPS admission requirement based on these nonrandomized measurements.','unresolved':['Strict2 speed/runtime behavior unmeasured.','Original GUI82/1 and diagnostic57/2 remain their recorded outcomes; no full writer qualification inferred.','Rotating whole-wrapper advance averages still13.1–13.7ms; Native.step alone is not total frame cost.']}
    (HERE/'TIMING_ASSESSMENT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'gui':comparisons['gui']['observed_reduction_percent'],'rotating_headless':comparisons['rotating_headless']['observed_reduction_percent'],'all7_captured_point_hashes_equal':all(row['captured_points_sha_equal'] for row in comparisons['gui']['profiles'].values()),'source_joins':len(joins),'create_order_proof':ordering},indent=2))


if __name__=='__main__':main()

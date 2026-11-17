"""Synthetic metadata only; no observer, process query, engine, Git or live terminal reads."""
import ast
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import close_terminal as C


def receipt():
    return {'format':'studio_private_desktop_1','desktop':'HAS_Test_synthetic','child_pid':123,
        'private_window_seen':True,'child_desktop_confirmed':True,'job_closed':True,'desktop_closed':True,
        'desktop_switch_requested':False,'foreground_child_observed':False,'exit':0,'seconds':1.0}


def metadata(status='passed'):
    context=copy.deepcopy(C.CONTEXT)
    state={'format':'has_owned_canonical_run_1','status':status,'suite_exit':0 if status=='passed' else 1,
        'source_unchanged':True,'started_utc':'2026-11-17T01:27:36.0900000Z','finished_utc':'2026-11-17T02:27:36.0900000Z',
        'source_commit':context['commit'],'pid':context['coordinator_pid'],'process_started':context['coordinator_birth'],
        'checkout':context['checkout'],'run_folder':str(Path(context['checkout'])/'output'/context['run_name']),
        'script_sha256':context['runner_sha256'],'command':[context['python_executable'],'-u','tests/verify.py']}
    birth={'format':'has_root_neon_corrected_birth_observation_1','coordinator':{'pid':context['coordinator_pid'],'creation_utc':context['coordinator_birth']},
        'python':{'pid':context['python_pid'],'parent_pid':context['coordinator_pid'],'creation_utc':context['python_birth'],'command_line':context['python_command']}}
    launch={'format':'has_root_neon_full_launch_1','source_commit':context['commit'],'coordinator_pid':context['coordinator_pid'],'coordinator_creation_utc':context['coordinator_birth'],
        'run_folder':state['run_folder'],'functional_source_files':context['functional_sources'],'runner':context['runner'],'runner_sha256':context['runner_sha256'],'graphics_lease':'root-exclusive'}
    before={'commit':context['commit'],'source_sha256':{'synthetic/'+str(i):'0'*64 for i in range(context['functional_sources'])}}
    return state,birth,launch,before,copy.deepcopy(before),context


def result():
    registry=json.loads((C.HERE/'RESULT_REGISTRY.json').read_bytes())
    value={key:{} for key in registry['expected_result_keys']}
    for key in registry['expected_core_process_keys']:value[key]={'exit':0,'seconds':1.0}
    for key in registry['expected_movie_keys']:value[key]={'frames':48,'fps':'24/1','duration':'2.000000'}
    basic=lambda count:{'checks':count,'passed':True,'source_unchanged':True,'native_conversion':False,'graphics':False}
    jiggle=basic(66);cross=basic(77);cross['reports']={key:{'checks':count} for key,count in [('collector',47),('metadata',11),('adapter',19)]}
    headless=basic(96);headless.update(headless=True,runtime_unchanged=True,reports={key:{'checks':count,'failures':0,'result':{'failures':0},'parse':{'exit':0,'timed_out':False},'run':{'exit':0,'timed_out':False}} for key,count in [('bindings',79),('helper',17)]})
    value['source_choice_foundation']={'checks':167,'passed':True,'source_unchanged':True,'native_conversion':False,'reports':{'jiggle_cpu':jiggle,'crosswalk_cpu':cross,'bone_bindings_headless':headless},'separate_checks':{'crosswalk_cpu':77,'bone_bindings_headless':96}}
    value['source_import_owner']={'passed':True,'headless':True,'native_conversion':False,'source_unchanged':True,'result':{'checks':53,'failures':0,'cases':[{}]*6}}
    value['actual_mmd_tested']=True
    value['contact_selection']={'checks':67,'failures':0,'native_reports':[{}]*5,'audio_driver':'Dummy'}
    for mode,split in [('cpu',[('transport',11),('adapter',128),('host',69)]),('graphical',[('focused',221),('peers',45)])]:
        rows=[]
        for label,count in split:
            child={'label':label,'checks':count,'passed':True,'exit':0,'timed_out':False,'retained_Popen_reaped':True,'error_markers':[],'result_source_context_bound':True}
            if mode=='graphical':child.update(clean_private_receipt=True,private_receipt=receipt())
            rows.append(child)
        value['helper_preview_'+mode]={'passed':True,'mode':mode,'source_context':'main_source_snapshot','source_state':{'revision':C.CONTEXT['commit'],'working_status':[]},'overlay_files':0,'native_requested':False,'native_inputs_checked':False,'native_fidelity':False,'gpu_used':mode=='graphical','results':rows,'checks':sum(count for _,count in split),'preservation':{'source':True}}
    value['neon_workspace']={'format':'has_neon_workspace_verification_1','passed':True,'expected_checks':{'inset':12384,'behavior':32,'compact':14,'rail':45,'lifecycle':29},'checks':12504,'failures':0,'reports':{'inset':{},'behavior':{},'compact':{},'rail':{},'lifecycle':{}},'all_functional_sources_hash_size_mtime_unchanged':True,'all_private_jobs_and_desktops_closed':True}
    return value,registry


class TerminalTests(unittest.TestCase):
    def test_exact_pass_and_failure_metadata(self):
        self.assertTrue(C.validate_terminal(*metadata()))
        self.assertFalse(C.validate_terminal(*metadata('failed')))
        self.assertFalse(C.validate_terminal(*metadata('runner_error')))

    def test_nonterminal_exit_source_and_birth_mutations_refused(self):
        for index,key,value in [(0,'status','running'),(0,'suite_exit',1),(0,'source_unchanged',False),(0,'pid',25389),(0,'script_sha256','0'*64),
            (0,'pid',25388.0),(0,'checkout','C:\\wrong'),(0,'finished_utc','2026-11-17T00:00:00Z'),(1,'format','old_flat_schema'),(2,'graphics_lease','shared'),(2,'coordinator_pid',25388.0),(2,'functional_source_files',1028.0)]:
            values=list(metadata());values[index][key]=value
            with self.subTest(index=index,key=key):
                with self.assertRaises(ValueError):C.validate_terminal(*values)

    def test_child_birth_parent_command_and_after_source_refused(self):
        for key,value in [('pid',23905),('parent_pid',1),('creation_utc','2026-11-17T01:27:37.1616851Z'),('command_line','python fake.py')]:
            values=list(metadata());values[1]['python'][key]=value
            with self.assertRaises(ValueError):C.validate_terminal(*values)
        values=list(metadata());values[4]['source_sha256']['synthetic/0']='1'*64
        with self.assertRaises(ValueError):C.validate_terminal(*values)

    def test_failure_branch_never_loads_final_full_report(self):
        state,birth,launch,before,after,context=metadata('failed');context['immutable_run_inputs']={}
        reads=[]
        mapping={'state.json':state,'source-before.json':before,'source-after.json':after,'root-birth-observation.json':birth,'launch.json':launch}
        def fake_load(path):
            reads.append(Path(path).name)
            self.assertIn(Path(path).name,mapping,'Failure must not load a full report')
            return copy.deepcopy(mapping[Path(path).name])
        def fake_sha(path):
            return {'legacy_result_gates.py':context['legacy_result_gates_sha256'],'RESULT_REGISTRY.json':context['registry_sha256']}.get(Path(path).name,context['runner_sha256'])
        with patch.object(C,'CONTEXT',context),patch.object(C,'load',side_effect=fake_load),patch.object(C,'sha',side_effect=fake_sha),patch.object(C,'validate_current_sources') as current,patch.object(C,'observe') as observed:
            actual=C.terminal();self.assertIsNone(actual[2]);current.assert_called_once();observed.assert_not_called()
        self.assertNotIn('verification.json',reads)

    def test_original_158_36_21_and_Neon_scope_accept(self):
        value,registry=result();C.validate_result(value,C.CONTEXT,registry)
        self.assertEqual((len(value),len(registry['expected_core_process_keys']),len(registry['expected_movie_keys'])),(158,36,21))

    def test_missing_extra_native_skip_core_and_movie_mutations_refused(self):
        for mutation in (lambda v:v.pop('neon_workspace'),lambda v:v.update(unexpected={}),lambda v:v.update(actual_mmd_tested=False),
            lambda v:v['source_import_owner'].update(skipped=True),lambda v:v['unit'].update(exit=1),lambda v:v['posed_model_video_0'].update(frames=47)):
            value,registry=result();mutation(value)
            with self.assertRaises((ValueError,KeyError)):C.validate_result(value,C.CONTEXT,registry)

    def test_Neon_count_type_bool_case_source_and_closure_mutations_refused(self):
        for key,value in [('passed',False),('checks',12503),('checks',12504.0),('failures',True),('all_functional_sources_hash_size_mtime_unchanged',False),('all_private_jobs_and_desktops_closed',False),('reports',{'inset':{}})]:
            record,registry=result();record['neon_workspace'][key]=value
            with self.assertRaises(ValueError):C.validate_result(record,C.CONTEXT,registry)
        record,registry=result();record['neon_workspace']['expected_checks']['behavior']=32.0
        with self.assertRaises(ValueError):C.validate_result(record,C.CONTEXT,registry)

    def test_strict_private_receipt_and_registered_cancel(self):
        self.assertEqual(C.classify_receipt(receipt(),False,True),'normal_exit0')
        item=receipt();item.update(exit=2,cancelled=True,error='Owned converter cancelled')
        self.assertEqual(C.classify_receipt(item,True,True),'registered_Krita_cancel_exit2')
        with self.assertRaises(ValueError):C.classify_receipt(item,False,True)

    def test_failed_partial_exit_is_not_a_PASS(self):
        item=receipt();item['exit']=1
        self.assertEqual(C.classify_receipt(item,False,False),'failed_partial_run_nonzero_exit')
        with self.assertRaises(ValueError):C.classify_receipt(item,False,True)

    def test_placement_foreground_monitor_enumeration_and_error_refused(self):
        for key,value in [('private_window_seen',False),('child_desktop_confirmed',1),('job_closed',False),('desktop_closed',False),('desktop_switch_requested',True),('foreground_child_observed',True),('monitor_error','synthetic'),('desktop_enumeration_error',5),('error','synthetic'),('cancelled',True),('exit',False)]:
            item=receipt();item[key]=value
            with self.assertRaises(ValueError):C.classify_receipt(item,False,True)

    def test_typed_inline_equality_preserves_JSON_types(self):
        item=receipt();duplicate=copy.deepcopy(item);self.assertTrue(C.typed_same(item,duplicate))
        duplicate['job_closed']=1;self.assertFalse(C.typed_same(item,duplicate))
        self.assertFalse(C.typed_same(({'closed':True},),({'closed':1},)))

    def test_identical_physical_copies_count_as_one_job(self):
        rows=[{'receipt':receipt(),'classification':'normal_exit0'},{'receipt':receipt(),'classification':'normal_exit0'}]
        inline=[{'receipt':receipt()}]
        self.assertEqual(C.validate_ownership(rows,inline,None),{'HAS_Test_synthetic':'normal_exit0'})

    def test_conflicting_copy_or_inline_only_or_typed_mismatch_refused(self):
        rows=[{'receipt':receipt(),'classification':'normal_exit0'}]
        changed=receipt();changed['child_pid']=124
        with self.assertRaises(ValueError):C.validate_ownership([*rows,{'receipt':changed,'classification':'normal_exit0'}],[],None)
        with self.assertRaises(ValueError):C.validate_ownership(rows,[{'receipt':changed}],None)
        with self.assertRaises(ValueError):C.validate_ownership([], [{'receipt':receipt()}],None)
        changed=receipt();changed['job_closed']=1
        with self.assertRaises(ValueError):C.validate_ownership(rows,[{'receipt':changed}],None)

    def test_registered_cancel_identity_is_required_and_deduplicated(self):
        cancelled=receipt();cancelled.update(exit=2,cancelled=True,error='Owned converter cancelled')
        rows=[{'receipt':cancelled,'classification':'registered_Krita_cancel_exit2'}]*2
        self.assertEqual(len(C.validate_ownership(rows,[],cancelled)),1)
        with self.assertRaises(ValueError):C.validate_ownership([],[],cancelled)

    def test_exact_nanosecond_birth_order(self):
        self.assertEqual(C.ns('2026-11-17T01:27:37.1616851Z')-C.ns('2026-11-17T01:27:37.1616850Z'),100)
        with self.assertRaises(ValueError):C.ns('2026-11-17 01:27:37')

    def test_host_observer_has_no_termination_and_preserves_PID_reuse_rule(self):
        source=(C.HERE/'close_terminal.py').read_text()
        tree=ast.parse(source);node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='observe')
        body=ast.get_source_segment(source,node)
        for forbidden in ('Stop-Process','taskkill','TerminateProcess','process.kill(','process.terminate('):self.assertNotIn(forbidden,body)
        self.assertIn('[DateTimeOffset]::Parse($now) -ne [DateTimeOffset]::Parse($pin.birth)',body)
        self.assertIn('process.communicate(timeout=60)',body)
        self.assertIn('process.poll() is not None',body)

    def test_phase_recheck_precedes_first_audit_write(self):
        source=(C.HERE/'close_terminal.py').read_text()
        self.assertLess(source.index("'Phase document changed before audit admission'"),source.index('out.mkdir(exist_ok=False)'))


if __name__=='__main__':unittest.main()

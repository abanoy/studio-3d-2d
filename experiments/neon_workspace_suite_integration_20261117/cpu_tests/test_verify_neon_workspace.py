"""Synthetic orchestration/report failures only. No engines, runtime clients, CIM or Git."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

FILE = Path(__file__).resolve().parents[1]/'tests/verify_neon_workspace.py'
SPEC = importlib.util.spec_from_file_location('neon_workspace_suite_cpu_subject',FILE)
W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W)
NAMES = ['synthetic_%02d' % i for i in range(32)]


def report(name):
    counts = {'behavior':32,'inset':12384,'compact':14,'rail':45}
    value = {'checks':counts[name],'failures':0}
    if name=='behavior':
        value.update(format='has_neon_behavior_regression_result_1',expected_checks=32,
                     complete_assertion_set=True,script_sha256='a'*64,app_sha256='b'*64,
                     named_checks={key:True for key in NAMES},synthetic_included_assets_only=True,
                     save_and_fullscreen_actions_instrumented=True,refresh_preserved_faded_context=True)
    elif name=='inset':
        value.update(status='PASS',configurations=576,native_assets_used=False,
                     maximum_projection_error_pixels=.0008,maximum_ray_error=.0000003)
    elif name=='compact':
        value.update(native_owner_assets_used=False,compact_timeline_preserved=True,
                     samples=[{'row':i,'visible_before_route':True,'selected_after_route':True,
                               'viewport_height':62.0} for i in (0,32,63)])
    else:
        value.update(format='has_neon_rail_placement_regression_1',synthetic_fixture_only=True,screenshots_written=False)
    return value


def log(name,value):
    if name=='behavior': return '\n'.join('PASS neon_behavior.'+key for key in NAMES)
    return W.MARKERS[name]+json.dumps(value)


class ReportGates(unittest.TestCase):
    def validate(self,name,value,text=None):
        return W.validate_report(name,value,log(name,value) if text is None else text,'a'*64,'b'*64,NAMES)

    def test_all_complete_result_shapes(self):
        for name in ('behavior','inset','compact','rail'):
            with self.subTest(name=name): self.validate(name,report(name))

    def test_count_failures_and_boolean_aliases_refused(self):
        for name in ('behavior','inset','compact','rail'):
            for key,value in (('checks',1),('failures',1),('failures',False),('checks',float(report(name)['checks']))):
                with self.subTest(name=name,key=key,value=value):
                    changed=report(name);changed[key]=value
                    with self.assertRaises(ValueError): self.validate(name,changed)

    def test_behavior_missing_duplicate_or_wrong_name_pass_lines_refused(self):
        good=log('behavior',report('behavior')).splitlines()
        for lines in (good[:-1],good+[good[0]],good[:-1]+['PASS neon_behavior.other']):
            with self.subTest(lines=len(lines)):
                with self.assertRaises(ValueError): self.validate('behavior',report('behavior'),'\n'.join(lines))

    def test_behavior_named_boolean_and_exact_script_app_binding(self):
        for key,value in (('complete_assertion_set',False),('script_sha256','c'*64),('app_sha256','c'*64),('synthetic_included_assets_only',False),('refresh_preserved_faded_context',False)):
            changed=report('behavior');changed[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError): self.validate('behavior',changed)
        changed=report('behavior');changed['named_checks'][NAMES[0]]=1
        with self.assertRaises(ValueError): self.validate('behavior',changed)

    def test_marker_is_single_and_exact_result(self):
        for name in ('inset','compact','rail'):
            good=report(name)
            for text in ('',log(name,good)+'\n'+log(name,good),W.MARKERS[name]+'{}'):
                with self.subTest(name=name,text=text[:20]):
                    with self.assertRaises(ValueError): self.validate(name,good,text)

    def test_inset_configuration_and_numeric_error_bounds(self):
        for key,value in (('configurations',575),('configurations',576.0),('maximum_projection_error_pixels',.01),
                           ('maximum_ray_error',.000003),('maximum_ray_error',float('nan')),('maximum_ray_error',True)):
            changed=report('inset');changed[key]=value
            with self.subTest(key=key,value=value):
                with self.assertRaises(ValueError): self.validate('inset',changed)

    def test_compact_first_middle_last_and_small_visible_routes(self):
        mutations=[lambda v:v['samples'].reverse(),lambda v:v['samples'].pop(),
                   lambda v:v['samples'][1].update(visible_before_route=False),
                   lambda v:v['samples'][1].update(selected_after_route=False),
                   lambda v:v['samples'][1].update(viewport_height=115)]
        for mutate in mutations:
            changed=report('compact');mutate(changed)
            with self.assertRaises(ValueError): self.validate('compact',changed)

    def test_diagnostics_cannot_pass_with_zero_failure_report(self):
        for bad in W.BAD_LOG:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): self.validate('rail',report('rail'),log('rail',report('rail'))+'\n'+bad)


class OwnedInputs(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'output').mkdir()
        self.script=self.root/'script.gd';self.script.write_text('synthetic',encoding='utf-8')

    def test_behavior_job_exact_fresh_folder_hash_and_expiry(self):
        job=W.behavior_job(self.root,self.root/'output/fresh',self.script,'b'*64,True,1000.0)
        self.assertEqual(job['expires_unix'],1180.0)
        self.assertEqual(job['script_sha256'],W.sha(b'synthetic'))
        self.assertEqual(job['folder'],(self.root/'output/fresh').as_posix())
        self.assertIs(job['root_closure_is_explicit_caller_attestation'],True)

    def test_missing_lease_existing_and_outside_destinations_refused(self):
        with self.assertRaises(ValueError): W.behavior_job(self.root,self.root/'output/fresh',self.script,'b'*64,False)
        (self.root/'output/existing').mkdir()
        for path in (self.root/'outside',self.root/'output',self.root/'output/existing'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError): W.owned_fresh(self.root,path)

    def test_invalid_behavior_job_clock_and_app_pin_refused(self):
        for clock in (True,float('inf'),float('nan')):
            with self.assertRaises(ValueError): W.behavior_job(self.root,self.root/'output/fresh',self.script,'b'*64,True,clock)
        with self.assertRaises(ValueError): W.behavior_job(self.root,self.root/'output/fresh',self.script,'missing',True,1000)

    def test_standard_private_command_gets_bounded_limits(self):
        receipt=self.root/'output/private-desktop/synthetic.json'
        factory=lambda *a,**k:['pythonw','private_desktop.py','--receipt',str(receipt),'--','godot','--script','synthetic.gd']
        args,path=W.bounded_command(factory,'synthetic.gd',False,[],self.root,150)
        self.assertEqual(path,receipt)
        self.assertEqual(args[args.index('--timeout')+1],'150')
        self.assertEqual(args[args.index('--memory-limit-mib')+1],'4096')

    def test_nonprivate_or_existing_receipt_commands_refused(self):
        with self.assertRaises(ValueError): W.bounded_command(lambda *a,**k:['godot'],'x',False,[],self.root,150)
        with self.assertRaises(ValueError): W.bounded_command(lambda *a,**k:['godot'],'x',True,[],self.root,150)
        receipt=self.root/'output/private-desktop/existing.json';receipt.parent.mkdir();receipt.write_text('{}')
        with self.assertRaises(ValueError): W.bounded_command(lambda *a,**k:['pythonw','--receipt',str(receipt),'--','godot'],'x',False,[],self.root,150)

    def test_unconfirmed_main_never_reaches_any_process(self):
        with patch.object(W.subprocess,'Popen',side_effect=AssertionError('must not start')):
            with self.assertRaisesRegex(ValueError,'lease-confirmed'): W.main([])


class PhysicalReceipts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'receipt.json'
        self.base={'format':'studio_private_desktop_1','exit':0,'child_pid':123,'child_desktop_confirmed':True,
                   'job_closed':True,'desktop_closed':True,'foreground_child_observed':False,'desktop_switch_requested':False}

    def write(self,value): self.path.write_text(json.dumps(value),encoding='utf-8')

    def test_actual_receipt_shape_and_hash(self):
        self.write(self.base);start=self.path.stat().st_mtime_ns
        value,digest=W.physical_receipt(self.path,start)
        self.assertEqual(value,self.base);self.assertEqual(digest,W.sha(self.path.read_bytes()))

    def test_each_physical_closure_or_placement_flag_is_literal(self):
        for key,value in (('exit',False),('exit',2),('child_desktop_confirmed',1),('job_closed',False),
                          ('desktop_closed',False),('foreground_child_observed',True),('desktop_switch_requested',True),('child_pid',True)):
            changed=copy.deepcopy(self.base);changed[key]=value;self.write(changed)
            with self.subTest(key=key,value=value):
                with self.assertRaises(ValueError): W.physical_receipt(self.path,0)

    def test_monitor_error_and_stale_receipt_refused(self):
        for key in ('error','monitor_error','desktop_enumeration_error','cancelled'):
            changed=copy.deepcopy(self.base);changed[key]='synthetic';self.write(changed)
            with self.assertRaises(ValueError): W.physical_receipt(self.path,0)
        self.write(self.base);os.utime(self.path,ns=(1,1))
        with self.assertRaises(ValueError): W.physical_receipt(self.path,time.time_ns())


class SourceAndProcessEvidence(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()

    def fixture(self):
        for part in W.FUNCTIONAL_DIRS: (self.root/part).mkdir()
        for name in W.FUNCTIONAL_FILES: (self.root/name).write_text('synthetic',encoding='utf-8')
        (self.root/'src/test.gd').write_text('synthetic',encoding='utf-8')

    def test_actual_membership_hash_size_and_mtime_snapshot(self):
        self.fixture();before=W.snapshot(self.root)
        (self.root/'tests/__pycache__').mkdir();(self.root/'tests/__pycache__/ignored.pyc').write_bytes(b'x')
        self.assertEqual(before,W.snapshot(self.root))
        (self.root/'tests/new.gd').write_text('new',encoding='utf-8')
        self.assertNotEqual(before,W.snapshot(self.root))
        (self.root/'tests/new.gd').unlink()
        path=self.root/'src/test.gd';stamp=path.stat().st_mtime_ns;os.utime(path,ns=(stamp,stamp+1000000000))
        self.assertNotEqual(before,W.snapshot(self.root))

    def test_execute_records_reaped_process_without_native_execution(self):
        process=Mock(pid=123,returncode=0);process.communicate.return_value=('synthetic','');process.poll.return_value=0
        with patch.object(W.subprocess,'Popen',return_value=process):
            text,record=W.execute(['synthetic'],self.root,self.root,'success',1)
        self.assertTrue(record['reaped']);self.assertFalse(record['timed_out']);self.assertEqual(text,'synthetic')
        self.assertTrue((self.root/'success-command.json').is_file())

    def test_timeout_preserves_failure_record_and_reaps_mock(self):
        process=Mock(pid=123,returncode=2);process.communicate.side_effect=[subprocess.TimeoutExpired(['synthetic'],1),('','timeout')];process.poll.return_value=2
        with patch.object(W.subprocess,'Popen',return_value=process):
            with self.assertRaises(ValueError): W.execute(['synthetic'],self.root,self.root,'timeout',1)
        process.kill.assert_called_once();self.assertEqual(process.communicate.call_count,2)
        saved=json.loads((self.root/'timeout-process.json').read_bytes())
        self.assertTrue(saved['timed_out'] and saved['reaped'])


if __name__=='__main__': unittest.main()

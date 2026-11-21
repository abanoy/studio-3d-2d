"""Source-only authored receipt classifier controls; Root executes separately.
Does not launch Godot, create desktops or invoke a component/Full verifier.
"""
from pathlib import Path
import ast,copy,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'payload/tests/verify_import_capability.py').read_text(encoding='utf-8')
module=ast.parse(source)
functions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='private_receipt_closed']
assert len(functions)==1
space={'re':re}
exec(compile(ast.Module(body=functions,type_ignores=[]),'<actual_wrapper_receipt_classifier>','exec'),space)
f=space['private_receipt_closed']
p=json.loads((ROOT/'evidence/ACTUAL_HEADLESS_PRIVATE_RECEIPT.json').read_text(encoding='utf-8'))
before=copy.deepcopy(p)
h=['pinned-godot.exe','--headless','--script','res://unit.gd','--','case']
g=['pinned-godot.exe','--script','res://gui.gd','--','case']
checks=0
def check(ok,name):
    global checks
    checks+=1
    assert ok,name
    print('PASS '+name)
def altered(**updates):
    value=copy.deepcopy(p);value.update(updates);return value
check(f(p,0,True,h),'actual_no_window_headless_receipt_retains_full_lifecycle_proof')
check(p==before,'actual_receipt_not_mutated')
check(f(altered(child_desktop_confirmed=True),0,True,h),'headless_thread_desktop_observation_optional_without_window_claim')
q=altered(child_desktop_confirmed=True,private_window_seen=True,maximum_owned_windows=1)
check(f(q,0,False,g),'graphical_positive_requires_private_window_and_desktop')
for key,value,label in [('child_desktop_confirmed',False,'GUI_missing_desktop'),('private_window_seen',False,'GUI_missing_window'),('maximum_owned_windows',0,'GUI_zero_windows')]:
    x=copy.deepcopy(q);x[key]=value;check(not f(x,0,False,g),label)
check(not f(altered(maximum_owned_windows=1),0,True,h),'headless_nonzero_window_count_refused')
check(not f(altered(private_window_seen=True),0,True,h),'headless_window_observation_refused')
check(not f(p,0,True,g),'headless_scope_requires_actual_engine_flag')
check(not f(q,0,False,h),'GUI_scope_refuses_headless_engine_flag')
check(not f(p,0,True,g+['--headless']),'user_argument_cannot_fake_engine_headless_flag')
check(not f(altered(exit=False),0,True,h),'boolean_exit_refused')
check(not f(p,1,True,h),'exit_mismatch_refused')
for key,value,label in [('job_closed',False,'unclosed_job'),('desktop_closed',False,'unclosed_desktop'),('foreground_child_observed',True,'foreground_child'),('desktop_switch_requested',True,'desktop_switch')]:
    check(not f(altered(**{key:value}),0,True,h),label)
for key in ['monitor_error','error','desktop_enumeration_error','cancelled']:
    check(not f(altered(**{key:'injected'}),0,True,h),'helper_'+key+'_refused')
check(not f(altered(format='other'),0,True,h),'wrong_format_refused')
check(not f(altered(desktop='Default'),0,True,h),'unowned_desktop_refused')
check(not f(altered(child_pid=True),0,True,h),'boolean_child_PID_refused')
check(not f(altered(job_memory_limit_bytes=1),0,True,h),'wrong_job_limit_refused')
x=copy.deepcopy(p);del x['private_window_seen'];check(not f(x,0,True,h),'missing_window_flag_refused')
x=copy.deepcopy(p);del x['child_desktop_confirmed'];check(not f(x,0,True,h),'missing_desktop_flag_refused')
check(not f(altered(maximum_owned_windows=False),0,True,h),'boolean_window_count_refused')
check(p==before,'negative_controls_leave_actual_receipt_unchanged')
assert checks==30
print('IMPORT_INFO_RECEIPT_CONTROLS '+json.dumps({'checks':checks,'failures':0,'processes_launched':0,'graphics_executed':False}))

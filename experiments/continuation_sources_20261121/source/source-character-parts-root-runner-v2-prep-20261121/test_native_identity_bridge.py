"""Pure synthetic profile/identity controls; authored UNRUN. No native inputs."""
import importlib.util,json
from pathlib import Path

path=Path(__file__).with_name('native_identity_bridge.py')
spec=importlib.util.spec_from_file_location('_synthetic_bridge',path)
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
base=(14290083805553457215,5910974513560200,1,33206,12268,1795256292370901300)
seal=('1351841855','5910974513560200','1','33206','12268','1795256292370901300')
godot='C:/a/tools/Godot/Godot_v4.6-stable_win64.exe'
python='C:/Program Files/Python313/python.exe'
checks=0

def changed(values,index,value):
    rows=list(values);rows[index]=value;return tuple(rows)

def check(label,function,refuse=False):
    global checks
    try:value=function()
    except RuntimeError:
        if not refuse:raise
    else:
        if refuse:raise AssertionError(label+' unexpectedly admitted')
        if value is False:raise AssertionError(label)
    checks+=1;print('PASS '+label,flush=True)

check('measured64dev_projects_exact32_and_all_six_fields',lambda:B.project(base,'data/file.gd')==seal)
check('decimal_seal_roundtrip_remains_exact',lambda:B.parse_seal(json.loads(json.dumps(seal)))==seal)
check('ordinary_runtime_asserts_seal',lambda:B.assert_seal(base,'src/app.gd',seal))
check('Godot_exact_measured_execute_profile',lambda:B.project(changed(base,3,33279),godot)==seal)
check('Python_exact_measured_execute_profile',lambda:B.project(changed(base,3,33279),python)==seal)
check('Windows_separator_and_case_profile',lambda:B.project(changed(base,3,33279),'C:\\PROGRAM FILES\\PYTHON313\\PYTHON.EXE')==seal)
check('unmeasured_executable_mask_refused',lambda:B.project(changed(base,3,33279),'C:/other/tool.exe'),True)
check('unmeasured_batch_mask_refused',lambda:B.project(changed(base,3,33279),'C:/other/file.bat'),True)
check('runtime_execute_bits_refused',lambda:B.project(changed(base,3,33279),'src/app.gd'),True)
check('known_tool_missing_inferred_execute_bits_refused',lambda:B.project(base,godot),True)
check('readonly_regular_producer_preserved',lambda:B.project(changed(base,3,33060),'src/app.gd')[3]=='33060')
check('readonly_permission_drift_fails_original_seal',lambda:B.assert_seal(changed(base,3,33060),'src/app.gd',seal),True)
check('device_low32_drift_refused',lambda:B.assert_seal(changed(base,0,base[0]+1),'src/app.gd',seal),True)
check('inode_drift_refused',lambda:B.assert_seal(changed(base,1,base[1]+1),'src/app.gd',seal),True)
check('hardlink_count_refused',lambda:B.project(changed(base,2,2),'src/app.gd'),True)
check('size_drift_refused',lambda:B.assert_seal(changed(base,4,base[4]+1),'src/app.gd',seal),True)
check('nanosecond_mtime_drift_refused',lambda:B.assert_seal(changed(base,5,base[5]+1),'src/app.gd',seal),True)
check('directory_type_refused',lambda:B.project(changed(base,3,16822),'src/app.gd'),True)
check('unexpected_readwrite_mode_refused',lambda:B.project(changed(base,3,33152),'src/app.gd'),True)
check('boolean_native_dev_refused',lambda:B.project(changed(base,0,True),'src/app.gd'),True)
check('fractional_native_field_refused',lambda:B.project(changed(base,4,12268.5),'src/app.gd'),True)
check('negative_native_field_refused',lambda:B.project(changed(base,5,-1),'src/app.gd'),True)
check('native_dev_overflow_refused',lambda:B.project(changed(base,0,2**64),'src/app.gd'),True)
check('seal_numeric_field_refused',lambda:B.parse_seal(changed(seal,0,1351841855)),True)
check('seal_leading_zero_refused',lambda:B.parse_seal(changed(seal,0,'01351841855')),True)
check('seal_device64_profile_refused',lambda:B.parse_seal(changed(seal,0,str(base[0]))),True)
check('seal_inferred_execute_bits_refused',lambda:B.parse_seal(changed(seal,3,'33279')),True)
check('native_exact_identity_passes',lambda:B.same_native(base,base))
check('native_high32_drift_refused_even_when_projection_matches',lambda:B.same_native(base,changed(base,0,base[0]-(1<<32))),True)
check('native_raw_mode_drift_refused_independently',lambda:B.same_native(changed(base,3,33279),base),True)
check('native_inode_drift_refused_independently',lambda:B.same_native(base,changed(base,1,base[1]+1)),True)
check('native_nsmtime_drift_refused_independently',lambda:B.same_native(base,changed(base,5,base[5]+1)),True)
if checks!=32:raise AssertionError('EXACT32_CONTROLS')
print('NATIVE_IDENTITY_BRIDGE_RESULT '+json.dumps({'checks':checks,'failures':0,'synthetic_only':True,'native_inputs_read':False}),flush=True)

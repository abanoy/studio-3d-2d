"""Source-only scientifically controlled fixture successor; no engine/core edits."""
from pathlib import Path
import ast
import hashlib
import json
import difflib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SEALED=ROOT/'experiments/source_native_five_port_candidate_v2_20261115'
OBSERVER_SHA='ee14e069a6e9606edb1338aac1c91397d47fad9797148da09868babbc27c3a0a'
DRIVER_SHA='07c3c2e7403af0096753c1c8c2b6e8516cb3bd3b74b46cfdc29bb00fca90d3e0'


def change(source,old,new,count=1):
    assert source.count(old)==count,(old,source.count(old),count)
    return source.replace(old,new)


def write(name,text):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)


def names_function(source):
    fn=next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='names')
    scope={'__builtins__':{}};exec(compile(ast.Module(body=[fn],type_ignores=[]),'names-only','exec'),scope)
    return scope['names']


def main():
    raw=(SEALED/'test_drafts/source_native_five_live_ui.gd').read_bytes();assert hashlib.sha256(raw).hexdigest()==OBSERVER_SHA
    driver_raw=(SEALED/'test_drafts/verify_source_native_five_live.py').read_bytes();assert hashlib.sha256(driver_raw).hexdigest()==DRIVER_SHA
    source=raw.decode();driver=driver_raw.decode()
    # Fix the confounded experimental placement: both directions use the same
    # actual Aim centroid, not native8 for one and the five-anchor center for the other.
    source=change(source,'\t\tvar center: Vector3=actor().bone_transform(binding.has_id).origin\n\t\tvar base: Dictionary=editor.aimed_world(actor(),1.0)',
                  '\t\tvar base: Dictionary=editor.aimed_world(actor(),1.0)\n\t\tvar center: Vector3=base.transform*Vector3(0,.85,1.5)')
    helper='''func transverse_camera_fixture() -> void:
\t# Establish a bending experiment instead of a nearly axial wind experiment.
\t# This changes only the observer's camera fixture, never product airflow.
\tvar center:=Vector3.ZERO;var chosen: Array=selected_bindings()
\tfor entry in chosen:center+=actor().bone_transform(entry.has_id).origin
\tcenter/=float(chosen.size())
\tvar forward: Vector3=actor().bone_transform(binding.has_id).basis.z.normalized()
\tvar direction: Vector3=forward.cross(Vector3.UP)
\tif direction.length_squared()<.000000000001:direction=Vector3.RIGHT
\tdirection=direction.normalized()
\tvar camera: Camera3D=app.renderer.camera
\tvar distance: float=maxf(2.0,camera.global_position.distance_to(center))
\tvar height: float=camera.global_position.y-center.y
\tcamera.global_position=center-direction*distance+Vector3.UP*height;camera.look_at(center,Vector3.UP)

func controlled_fixture_admission() -> void:
\t# Root keys and actual root geometry stay fixed during fan comparisons.
\tapp.set_frame(0);await settled();var root0: Transform3D=actor().root.global_transform
\tapp.set_frame(24);await settled();var root24: Transform3D=actor().root.global_transform
\tvar root_keys_equal: bool=actor().sample_transform(0)==actor().sample_transform(24)
\tapp.set_frame(12);await settled();await configure_fan(12.0,"aimed")
\tvar fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
\tvar positive: Transform3D=fan.root.global_transform;var settings: Dictionary=fan.data.metadata.airflow.duplicate(true)
\tvar means: Dictionary={};var all_hits:=true;var maximum_alignment:=0.0;var greatest_opposite_dot:=-INF
\tvar forward: Vector3=actor().bone_transform(binding.has_id).basis.z.normalized()
\tmaximum_alignment=absf(forward.dot(positive.basis.z.normalized()))
\tfor entry in selected_bindings():
\t\tvar force: Vector3=Airflow.field(positive,settings,actor().bone_transform(entry.has_id).origin)
\t\tmeans[entry.has_id]=force;all_hits=all_hits and force.length_squared()>0.0
\tawait configure_fan(12.0,"opposite");fan=app.renderer.world_runtime.instance(fan_id)
\tmaximum_alignment=maxf(maximum_alignment,absf(forward.dot(fan.root.global_basis.z.normalized())))
\tfor entry in selected_bindings():
\t\tvar force: Vector3=Airflow.field(fan.root.global_transform,fan.data.metadata.airflow,actor().bone_transform(entry.has_id).origin)
\t\tvar previous: Vector3=means[entry.has_id]
\t\tall_hits=all_hits and force.length_squared()>0.0
\t\tvar denominator: float=previous.length()*force.length()
\t\tgreatest_opposite_dot=maxf(greatest_opposite_dot,previous.dot(force)/denominator if denominator>0.0 else 1.0)
\tmetrics["controlled_fixture"]={"root_keys_equal":root_keys_equal,"root_geometry_frames0_24_exact":root0==root24,"native8_goal_mean_axis_abs_dot_max":maximum_alignment,"all5_both_mean_fields_hit":all_hits,"greatest_mean_field_normalized_dot":greatest_opposite_dot,"admission_only_no_physics_tolerance_change":true}
\tcheck(root_keys_equal and root0==root24 and all_hits and maximum_alignment<=.0001 and greatest_opposite_dot<=-.9999,"fan.controlled_transverse_fixture")

func enable_record_root_rotation_fixture() -> void:
\t# The same0.47 root-key stress remains in the actual Record pipeline, after
\t# the fixed-root fan experiment. Observe actual geometry, not just key data.
\tvar transform: Dictionary=actor().data.pose_keys[0].transform
\tvar later: Dictionary=actor().data.pose_keys[1].transform
\tvar root_q:=Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)
\tlater.rotation_xyzw=[root_q.x,root_q.y,root_q.z,root_q.w]
\tapp.set_frame(0);await settled();var root0: Transform3D=actor().root.global_transform
\tapp.set_frame(24);await settled();var root24: Transform3D=actor().root.global_transform
\tcheck(transform.scale==later.scale and transform.rotation_xyzw!=later.rotation_xyzw and root0!=root24,"import.keyed_root_rotation_constant_scale")
\tmetrics["record_root_rotation_fixture"]={"actual_root_geometry_changed":root0!=root24,"root_key_radians":0.47,"constant_scale":transform.scale==later.scale}
\tapp.set_frame(12);await settled()

'''
    source=change(source,'func sample_profile(name: String,speed: float,kind: String) -> Dictionary:',helper+'func sample_profile(name: String,speed: float,kind: String) -> Dictionary:')
    old='''\tvar later: Dictionary=transform.duplicate(true);var root_q:=Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)
\tlater.rotation_xyzw=[root_q.x,root_q.y,root_q.z,root_q.w]
\tactor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":later,"interpolation":"linear"}]
\tcheck(transform.scale==later.scale and transform.rotation_xyzw!=later.rotation_xyzw,"import.keyed_root_rotation_constant_scale")'''
    new='''\tvar later: Dictionary=transform.duplicate(true)
\tactor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":later,"interpolation":"linear"}]'''
    source=change(source,old,new)
    source=change(source,'app.pose_editor.frame_model();app.keys=[Timeline.key(',
                  'app.pose_editor.frame_model();transverse_camera_fixture();app.keys=[Timeline.key(')
    source=change(source,'\tvar profile: Dictionary={}\n\tfor row in',
                  '\tawait controlled_fixture_admission()\n\tvar profile: Dictionary={}\n\tfor row in')
    old_aim='\tcheck(fan_editor.target_model()==actor() and not fan_editor.aim.disabled and Native.offered(actor()) and var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))==aim_rig_before,"fan.native_target_and_aim")'
    new_aim='''\tvar aim_center:=Vector3.ZERO;var aim_bindings: Array=selected_bindings()
\tfor entry in aim_bindings:aim_center+=actor().bone_transform(entry.has_id).origin
\taim_center/=float(aim_bindings.size())
\tvar aim_fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
\tvar aim_centroid_error: float=(aim_fan.root.global_transform*Vector3(0,.85,1.5)).distance_to(aim_center)
\tmetrics["initial_UI_Aim"]={"anchor_count":aim_bindings.size(),"centroid_world_error":aim_centroid_error}
\tcheck(fan_editor.target_model()==actor() and not fan_editor.aim.disabled and Native.offered(actor()) and var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))==aim_rig_before and aim_bindings.size()==5 and aim_centroid_error<=.00002,"fan.native_target_and_aim")'''
    source=change(source,old_aim,new_aim)
    source=change(source,'\tawait configure_fan(12.0,"aimed");select(target_id)\n\tvar world_before:',
                  '\tawait enable_record_root_rotation_fixture()\n\tawait configure_fan(12.0,"aimed");select(target_id)\n\tvar world_before:')
    driver=change(driver,"'fan.native_target_and_aim', 'fan.actual_field_reaches_joint']",
                  "'fan.native_target_and_aim', 'fan.actual_field_reaches_joint', 'fan.controlled_transverse_fixture']")
    # New formats prevent accidentally treating original82/1 as this result.
    source=source.replace('has_source_native_five_live_job_2','has_source_native_five_transverse_live_job_3').replace('has_source_native_five_live_result_2','has_source_native_five_transverse_live_result_3')
    driver=driver.replace('has_source_native_five_live_job_2','has_source_native_five_transverse_live_job_3').replace('has_source_native_five_live_result_2','has_source_native_five_transverse_live_result_3')
    original_gate='''\tvar plus: Vector3=profile.speed12.tip-profile.disabled.tip
\tvar minus: Vector3=profile.opposite.tip-profile.disabled.tip
\tvar every_opposite: bool=plus.dot(minus)<0.0
\tfor id in profile.speed12.tips:
\t\tvar positive: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id]
\t\tvar negative: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]
\t\tevery_opposite=every_opposite and positive.dot(negative)<0.0
\tcheck(every_opposite,"fan.opposite_tip_directions")'''
    assert original_gate in source and original_gate in raw.decode()
    oldnames=names_function(driver_raw.decode());newnames=names_function(driver)
    assert len(oldnames('writer'))==82 and len(newnames('writer'))==83
    assert set(oldnames('writer'))<set(newnames('writer'))
    assert newnames('reader',True)==oldnames('reader',True) and newnames('reader')==oldnames('reader')
    assert len(newnames('reader',True))==11 and len(newnames('reader'))==8
    assert source.count('"import.keyed_root_rotation_constant_scale"')==1
    write('source_native_five_live_ui.gd',source);write('verify_source_native_five_live.py',driver)
    write('observer_from_failed82.patch',''.join(difflib.unified_diff(raw.decode().splitlines(True),source.splitlines(True),fromfile='retained-failed82/observer',tofile='proposed-transverse83/observer')))
    contract={'format':'has_native_five_transverse_fixture_source_contract_1','status':'SOURCE_ONLY_UNPARSED_UNRUN',
              'observer_sha256':hashlib.sha256(source.encode()).hexdigest(),'driver_sha256':hashlib.sha256(driver.encode()).hexdigest(),
              'failed_observer_sha256':OBSERVER_SHA,'sealed_driver_sha256':DRIVER_SHA,
              'writer_expected_names':newnames('writer'),'writer_proposed_checks':83,'packed_proposed_checks':11,'linked_proposed_checks':8,
              'all82_existing_predicates_retained':True,'original_native8_and_all5_dot_block_byte_exact':True,
              'new_gate':'Explicit fixed-root/transverse/symmetric-hit geometry admission; not a relaxed motion gate.',
              'root_rotation_0_47_and_actual_geometry_preserved_before_Record':True,
              'product_math_airflow_coefficients_tolerances_or_five_backend_modified':False,
              'qualification_or_fixture_pass_claimed':False}
    write('CONTRACT.json',json.dumps(contract,indent=2)+'\n')
    assert hashlib.sha256((SEALED/'test_drafts/source_native_five_live_ui.gd').read_bytes()).hexdigest()==OBSERVER_SHA
    print(json.dumps({'source_only_ready':True,'observer_sha256':contract['observer_sha256'],'driver_sha256':contract['driver_sha256'],'proposed_checks':[83,11,8],'actual_pass_claimed':False}))


if __name__=='__main__':main()

"""Source-only scalar diagnostic successor; preserves actual failed observer.

No engine/GDScript parser, native input, expected/HAS/PNG artifact or model array
is read here. The future observer keeps transient vectors in RAM only.
"""
from pathlib import Path
import hashlib
import json
import ast
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'output/native-five-stage-attempt1/Studio/tests/source_native_five_live_ui.gd'
BASE_SHA='ee14e069a6e9606edb1338aac1c91397d47fad9797148da09868babbc27c3a0a'


def change(text,old,new,count=1):
    assert text.count(old)==count,(old,text.count(old),count)
    return text.replace(old,new)


def main():
    raw=BASE.read_bytes();assert hashlib.sha256(raw).hexdigest()==BASE_SHA
    source=raw.decode('utf-8-sig')
    source=change(source,'\tvar samples: Array[Vector3] = []','\tvar samples: Array[Vector3] = []\n\tvar sampled_ages: Array[float] = []\n\tvar simulation')
    source=change(source,'\t\tvar states: Dictionary = runner._chain.snapshot().states',
                  '\t\tsampled_ages.append(maxf(0.0,float(simulation.age)-1.0/120.0))\n\t\tvar states: Dictionary = runner._chain.snapshot().states')
    helpers='''func diagnostic_context() -> Dictionary:
\t# Actual scene field/goal data; this dictionary NEVER enters write_json.
\tvar fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
\tvar fields: Array=Airflow.collect(app.renderer,float(app.frame),app.physics_editor.simulations)
\tvar result: Dictionary={"fields":fields,"axis":fan.root.global_basis.z.normalized(),"nozzle":fan.root.global_transform*Vector3(0,.85,0),"goals":{},"origins":{},"mean_fields":{},"locals":{},"lengths":{},"native_ids":{},"settings":fan.data.metadata.airflow.duplicate(true),"fan_transform":fan.root.global_transform}
\tvar resolved: RefCounted=Bindings.resolve(actor())
\tfor index in [8,17,18,26,27]:
\t\tvar entry: RefCounted=resolved.bindings[index];var id: String=entry.has_id
\t\tvar frame: Transform3D=actor().bone_transform(id)
\t\tresult.goals[id]={"left":frame.basis.x.normalized(),"up":frame.basis.y.normalized(),"forward":frame.basis.z.normalized()}
\t\tresult.origins[id]=frame.origin;result.locals[id]=entry.skeleton.get_bone_pose(entry.skeleton_bone_index);result.native_ids[id]=index
\t\tresult.mean_fields[id]=Airflow.field(fan.root.global_transform,result.settings,frame.origin)
\t\tfor rule in raw_report().native_parameters.source_jiggle.rules:
\t\t\tif int(rule.native_bone_index)==index:result.lengths[id]=float(rule.parameters.length)*Native.SOURCE_SCALE*frame.basis.get_scale().x
\treturn result

func diagnostic_finished(context: Dictionary, ages: Array[float]) -> void:
\tcontext["final_origins"]={};context["final_goals"]={};context["unsteady_mean"]={};context["input_stats"]={}
\tfor id in context.origins:
\t\tcontext.final_origins[id]=actor().bone_transform(id).origin
\t\tvar parent: String=actor().parent_id(id)
\t\tvar composed: Transform3D=actor().bone_transform(parent)*context.locals[id]
\t\tcontext.final_goals[id]={"left":composed.basis.x.normalized(),"up":composed.basis.y.normalized(),"forward":composed.basis.z.normalized()}
\t\tvar total:=Vector3.ZERO;var hits:=0;var peak:=0.0;var sum_lengths:=0.0;var minimum_axis:=INF;var maximum_axis:=-INF
\t\tfor age in ages:
\t\t\tvar force: Vector3=Airflow.unsteady_force(context.fields,context.origins[id],age)/0.03
\t\t\tvar size: float=force.length();total+=force;sum_lengths+=size;peak=maxf(peak,size)
\t\t\tif size>0.0:hits+=1
\t\t\tminimum_axis=minf(minimum_axis,force.dot(context.axis));maximum_axis=maxf(maximum_axis,force.dot(context.axis))
\t\tcontext.unsteady_mean[id]=total/float(maxi(1,ages.size()))
\t\tcontext.input_stats[id]={"samples":ages.size(),"hit_samples":hits,"mean_length":sum_lengths/float(maxi(1,ages.size())),"maximum_length":peak,"minimum_own_fan_axis":minimum_axis if not ages.is_empty() else 0.0,"maximum_own_fan_axis":maximum_axis if not ages.is_empty() else 0.0}

func safe_cosine(first: Vector3, second: Vector3) -> float:
\tvar length: float=first.length()*second.length()
\treturn first.dot(second)/length if length>0.0 else 0.0

func scalar_diagnostic(profile: Dictionary) -> Dictionary:
\tvar positive: Dictionary=profile.speed12.diagnostic_private;var negative: Dictionary=profile.opposite.diagnostic_private;var control: Dictionary=profile.disabled.diagnostic_private
\tvar result: Dictionary={"format":"has_native_five_opposite_scalar_diagnostic_1","diagnostic_only":true,"fixture_and_all_existing_gates_changed":false,
\t\t"input_sampler":"Recomputed from actual captured scene fields at authored anchors and sampled simulation ages; not a serialized backend force trace.",
\t\t"positive_field_count":positive.fields.size(),"negative_field_count":negative.fields.size(),"fan_axis_dot":positive.axis.dot(negative.axis),
\t\t"positive_negative_nozzle_midpoint_to_front8_distance":((positive.nozzle+negative.nozzle)*.5-positive.origins[binding.has_id]).length(),"native":{}}
\tfor id in positive.native_ids:
\t\tvar index: int=positive.native_ids[id]
\t\tvar dp: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id];var dm: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]
\t\tvar fp: Vector3=positive.mean_fields[id];var fm: Vector3=negative.mean_fields[id]
\t\tvar axis_p: Vector3=fp.normalized() if fp.length_squared()>0.0 else positive.axis
\t\tvar axis_m: Vector3=fm.normalized() if fm.length_squared()>0.0 else negative.axis
\t\tvar goal: Dictionary=control.goals[id];var forward: Vector3=goal.forward
\t\tvar perpendicular: Vector3=axis_p-forward*axis_p.dot(forward);var perpendicular_size: float=perpendicular.length()
\t\tvar cross_goal: Vector3=axis_p.cross(forward);var cross_size: float=cross_goal.length()
\t\tvar tangent: Vector3=perpendicular/perpendicular_size if perpendicular_size>0.000000001 else Vector3.ZERO
\t\tvar cross_axis: Vector3=cross_goal/cross_size if cross_size>0.000000001 else Vector3.ZERO
\t\tvar bp: Vector3=positive.final_origins[id]-control.final_origins[id];var bm: Vector3=negative.final_origins[id]-control.final_origins[id]
\t\tvar rp: Vector3=dp-bp;var rm: Vector3=dm-bm
\t\tvar world_dot: float=dp.dot(dm)
\t\tvar plus_residual: Vector3=profile.speed12.tips[id]-(positive.final_origins[id]+positive.final_goals[id].forward*positive.lengths[id])
\t\tvar minus_residual: Vector3=profile.opposite.tips[id]-(negative.final_origins[id]+negative.final_goals[id].forward*negative.lengths[id])
\t\tvar control_residual: Vector3=profile.disabled.tips[id]-(control.final_origins[id]+control.final_goals[id].forward*control.lengths[id])
\t\tvar ep: Vector3=plus_residual-control_residual;var em: Vector3=minus_residual-control_residual
\t\tvar nozzle_offset_p: Vector3=positive.origins[id]-positive.nozzle;var nozzle_offset_m: Vector3=negative.origins[id]-negative.nozzle
\t\tvar along_p: float=nozzle_offset_p.dot(positive.axis);var along_m: float=nozzle_offset_m.dot(negative.axis)
\t\tvar radius_p: float=float(positive.settings.radius)*positive.fan_transform.basis.get_scale().x+along_p*.15
\t\tvar radius_m: float=float(negative.settings.radius)*negative.fan_transform.basis.get_scale().x+along_m*.15
\t\tresult.native[str(index)]={"native_index":index,"parent_is_simulated":index in [18,27],"original_native8_gate":world_dot<0.0 if index==8 else null,
\t\t\t"world_delta_dot":world_dot,"world_delta_normalized_dot":safe_cosine(dp,dm),"positive_delta_length":dp.length(),"negative_delta_length":dm.length(),
\t\t\t"mean_positive_length":fp.length(),"mean_negative_length":fm.length(),"mean_field_normalized_dot":safe_cosine(fp,fm),"positive_mean_hit":fp.length_squared()>0.0,"negative_mean_hit":fm.length_squared()>0.0,
\t\t\t"goal_forward_abs_dot_positive_mean_axis":absf(forward.dot(axis_p)),"goal_forward_abs_dot_negative_mean_axis":absf(forward.dot(axis_m)),
\t\t\t"positive_delta_on_positive_mean_axis":dp.dot(axis_p),"positive_delta_on_negative_mean_axis":dp.dot(axis_m),"negative_delta_on_positive_mean_axis":dm.dot(axis_p),"negative_delta_on_negative_mean_axis":dm.dot(axis_m),
\t\t\t"perpendicular_to_goal_axis_defined":perpendicular_size>0.000000001,"perpendicular_axis_raw_length":perpendicular_size,"positive_delta_on_perpendicular_to_goal":dp.dot(tangent),"negative_delta_on_perpendicular_to_goal":dm.dot(tangent),
\t\t\t"cross_goal_axis_defined":cross_size>0.000000001,"positive_delta_on_cross_goal":dp.dot(cross_axis),"negative_delta_on_cross_goal":dm.dot(cross_axis),
\t\t\t"positive_delta_on_goal_left":dp.dot(goal.left),"negative_delta_on_goal_left":dm.dot(goal.left),"positive_delta_on_goal_up":dp.dot(goal.up),"negative_delta_on_goal_up":dm.dot(goal.up),"positive_delta_on_goal_forward":dp.dot(forward),"negative_delta_on_goal_forward":dm.dot(forward),
\t\t\t"positive_base_shift_length":bp.length(),"negative_base_shift_length":bm.length(),"base_base_dot":bp.dot(bm),"base_ray_dot":bp.dot(rm),"ray_base_dot":rp.dot(bm),"ray_ray_dot":rp.dot(rm),"dot_decomposition_residual":world_dot-bp.dot(bm)-bp.dot(rm)-rp.dot(bm)-rp.dot(rm),
\t\t\t"same_tick_goal_residual_delta_dot":ep.dot(em),"positive_same_tick_goal_residual_on_perpendicular":ep.dot(tangent),"negative_same_tick_goal_residual_on_perpendicular":em.dot(tangent),
\t\t\t"unsteady_mean_positive_length":positive.unsteady_mean[id].length(),"unsteady_mean_negative_length":negative.unsteady_mean[id].length(),"unsteady_means_normalized_dot":safe_cosine(positive.unsteady_mean[id],negative.unsteady_mean[id]),"unsteady_positive_on_positive_mean_axis":positive.unsteady_mean[id].dot(axis_p),"unsteady_negative_on_positive_mean_axis":negative.unsteady_mean[id].dot(axis_p),
\t\t\t"positive_input_samples":positive.input_stats[id].samples,"negative_input_samples":negative.input_stats[id].samples,"positive_input_hit_samples":positive.input_stats[id].hit_samples,"negative_input_hit_samples":negative.input_stats[id].hit_samples,"positive_input_peak_length":positive.input_stats[id].maximum_length,"negative_input_peak_length":negative.input_stats[id].maximum_length,
\t\t\t"positive_field_along":along_p,"negative_field_along":along_m,"positive_field_radial_fraction":(nozzle_offset_p-positive.axis*along_p).length()/radius_p,"negative_field_radial_fraction":(nozzle_offset_m-negative.axis*along_m).length()/radius_m}
\treturn result

'''
    source=change(source,'func sample_profile(name: String,speed: float,kind: String) -> Dictionary:',helpers+'func sample_profile(name: String,speed: float,kind: String) -> Dictionary:')
    source=change(source,'\tvar rest_capture:=Capture.capture(actor(),selected_bindings())','\tvar rest_capture:=Capture.capture(actor(),selected_bindings())\n\tvar diagnostic_private: Dictionary=diagnostic_context()')
    source=change(source,'gate.actor=actor();gate.bone_id=binding.has_id','gate.actor=actor();gate.bone_id=binding.has_id;gate.simulation=simulation')
    source=change(source,'var per_rule_samples: Dictionary=gate.samples_by_id.duplicate(true);gate.free()',
                  'var per_rule_samples: Dictionary=gate.samples_by_id.duplicate(true)\n\tdiagnostic_finished(diagnostic_private,gate.sampled_ages);gate.free()')
    source=change(source,'"tips":tips,"spans":spans,"subtrees":subtrees}',
                  '"tips":tips,"spans":spans,"subtrees":subtrees,"diagnostic_private":diagnostic_private}')
    start=source.index('\tvar plus: Vector3=profile.speed12.tip-profile.disabled.tip')
    stop=source.index('\nfunc reader()',start)
    # Keep the original aggregate gate exactly, add the original native8 gate
    # as a separately named diagnostic, then stop before HAS/PNG/oracle writes.
    gate=source[start:source.index('\n\tcheck(actor().data==target_before',start)]
    gate=gate.replace('\tvar every_opposite: bool=plus.dot(minus)<0.0',
                      '\tcheck(plus.dot(minus)<0.0,"fan.original_native8_opposite_tip_directions")\n\tvar every_opposite: bool=plus.dot(minus)<0.0')
    extra='''\tvar scalar_report: Dictionary=scalar_diagnostic(profile)
\tmetrics["opposite_diagnostic"]=scalar_report
\twrite_json(job.folder.path_join("opposite-diagnostic.json"),scalar_report)
\t# Diagnostic ends here. Full writer82/1 remains failed and retained.
\treturn
'''
    source=source[:start]+gate+'\n'+extra+source[stop:]
    # No cold-reader or picture implementation is needed in a scalar probe.
    start=source.index('\nfunc reader()');stop=source.index('\nfunc write_json(',start)
    source=source[:start]+source[stop:]
    start=source.index('\nfunc picture(');stop=source.index('\nfunc writer()',start)
    source=source[:start]+source[stop:]
    source=source.replace('has_source_native_five_live_job_2','has_source_native_five_opposite_diagnostic_job_1').replace('has_source_native_five_live_result_2','has_source_native_five_opposite_diagnostic_result_1')
    source=change(source,'if not parsed is Dictionary or parsed.get("format")!="has_source_native_five_opposite_diagnostic_job_1":',
                  'if not parsed is Dictionary or parsed.get("format")!="has_source_native_five_opposite_diagnostic_job_1" or parsed.get("mode")!="writer":')
    source=change(source,'if job.mode=="writer":await writer()\n\telse:await reader()','await writer()')
    source=change(source,'"expected":job.folder.path_join("expected.json") if job.mode=="writer" else job.expected,','"diagnostic_only":true,"full_writer_qualification_claimed":false,')
    assert 'func picture(' not in source and 'func reader(' not in source
    assert 'save_png' not in source and 'save_file(' not in source and 'expected.json' not in source
    assert 'check(every_opposite,"fan.opposite_tip_directions")' in source
    target=HERE/'source_native_five_live_opposite_diagnostic.gd'
    with target.open('x',encoding='utf-8',newline='\n') as stream:stream.write(source)
    # Proposed names are an explicit diagnostic subset, never a full82 pass.
    driver=ROOT/'output/native-five-stage-attempt1/Studio/tests/verify_source_native_five_live.py'
    tree=ast.parse(driver.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='names')
    namespace={'__builtins__':{}};exec(compile(ast.Module(body=[function],type_ignores=[]),'names-only','exec'),namespace)
    all_names=namespace['names']('writer')
    prefixes=('import.','fan.','disabled.','zero.','miss.','speed3.','speed12.','speed50.','opposite.')
    names=[name for name in all_names if name.startswith(prefixes)]
    names.append('fan.original_native8_opposite_tip_directions')
    assert len(names)==len(set(names))==57
    contract={'format':'has_native_five_opposite_diagnostic_source_contract_1','status':'SOURCE_ONLY_GDSCRIPT_UNPARSED_UNRUN',
              'observer_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'failed_original_observer_sha256':BASE_SHA,
              'job_format':'has_source_native_five_opposite_diagnostic_job_1','result_format':'has_source_native_five_opposite_diagnostic_result_1',
              'mode':'writer','expected_names':sorted(names),'proposed_checks':57,
              'native8_original_dot_assertion_retained_separately':True,'new_all_five_dot_assertion_unchanged':True,
              'fixture_fan_placement_coefficients_tolerances_or_physics_changed':False,
              'native_vectors_or_arrays_serialized':False,'HAS_PNG_expected_oracles_written':False,
              'scope':'Diagnostic only. Full82 failed writer and sealedv2 remain unchanged. Root must create a fresh private stage/job and bind this exact source.'}
    with (HERE/'DIAGNOSTIC_CONTRACT.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(contract,stream,indent=2);stream.write('\n')
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_SHA
    print(json.dumps({'prepared_source_only':True,'proposed_checks':57,'observer_sha256':contract['observer_sha256'],'failed_original_unchanged':True}))


if __name__=='__main__':main()

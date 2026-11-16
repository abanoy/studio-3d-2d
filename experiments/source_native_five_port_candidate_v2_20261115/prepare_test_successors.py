"""Draft state/UI successors only; does not run or apply them."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TARGET=HERE/'test_drafts'
NEW_NEGATIVES=['chain_reorder','chain_source_binding','chain_binding_kind','chain_duplicate']+['force_slot_'+str(i) for i in range(5)]


def change(value,old,new,count=1):
    assert value.count(old)==count,(old,value.count(old),count)
    return value.replace(old,new)


def save(name,value):
    with (TARGET/name).open('x',encoding='utf-8',newline='\n') as stream:stream.write(value)


def state_successor(old):
    value=change(old,'const PLANNED_ASSERTIONS := 180','const PLANNED_ASSERTIONS := 266\nconst SELECTED := [8,17,18,26,27]\nconst WRAPPER_INVENTORY_CASES := ["source_missing","joints_empty","binding_shape","count","order"]')
    value=change(value,'"data_sha","source_path"]','"data_sha","source_path",'+','.join('"'+name+'"' for name in NEW_NEGATIVES)+']')
    value=value.replace('has_source_native_state_job_1','has_source_native_five_state_job_2').replace('ROOT_APPROVED_HEADLESS_STATE_TEST','ROOT_APPROVED_HEADLESS_FIVE_STATE_TEST').replace('has_source_native_state_result_1','has_source_native_five_state_result_2')
    value=change(value,'func state_bytes(runner: RefCounted) -> PackedByteArray: return bytes_of([runner._tick,runner._state])',
                 'func state_bytes(runner: RefCounted) -> PackedByteArray: return bytes_of([runner._tick,runner._chain.snapshot(),runner.configuration_stamp(runner._chain),runner.configuration_stamp(runner._trial),runner._size_tokens,runner._chain_inventory_stamp])')
    value=change(value,'func unselected_bytes(actor: RefCounted, id: String) -> PackedByteArray:',
                 'func selected_ids(resolution: RefCounted) -> Array:\n\tvar ids: Array = []\n\tfor index in SELECTED: ids.append(resolution.by_native[index])\n\treturn ids\n\nfunc unselected_bytes(actor: RefCounted, ids: Array) -> PackedByteArray:')
    value=change(value,'if key != id: values.append([key,actor.bone_transform(key)])','if not ids.has(key): values.append([key,actor.bone_transform(key)])')
    value=change(value,'unselected_bytes(actors[0],bindings[0].by_native[8])','unselected_bytes(actors[0],selected_ids(bindings[0]))',2)
    value=change(value,'if id != bindings[0].by_native[8]: complete = complete and sims[0].latest.get(id) == authored[id]',
                 'if not selected_ids(bindings[0]).has(id): complete = complete and sims[0].latest.get(id) == authored[id]\n\t\telse: complete = complete and sims[0].latest.get(id,Model.identity()).position == authored.get(id,Model.identity()).position')
    value=value.replace('wrapper.68_unselected_world_bones_exact','wrapper.64_unselected_world_bones_exact')
    value=change(value,'"native_rule_index_selected":8,','"native_rule_index_selected":8,"native_rule_indices_selected":SELECTED,"native_rules_solved":5,')
    fresh='''func fresh_baseline_checks(actor: RefCounted, resolution: RefCounted, name: String) -> void:
\tactor.live_pose = null; actor.apply(0,false)
\tvar saved := model_bytes(actor); var report := bytes_of(report_of(actor))
\tvar sparse: bool = actor.data.pose_keys.is_empty() and actor.data.pose.size() < 69
\tvar made: Dictionary = Native.create(actor)
\tvar rest_ok := not made.has("error")
\tif rest_ok:
\t\tvar step := native_step(made.runner)
\t\trest_ok = not step.has("error") and step.pose.size() == 5 and made.runner._chain.snapshot().states.size() == 5
\t\tfor id in selected_ids(resolution): rest_ok = rest_ok and step.get("pose",{}).get(id,Model.identity()).position == Model.identity().position
\t\tmade.runner.dispose()
\tcheck(sparse and rest_ok and model_bytes(actor) == saved and bytes_of(report_of(actor)) == report,"load."+name+".fresh_rest_null")
\tvar id: String = resolution.by_native[8]
\tactor.live_pose = {id:{"position":[0.001,-0.0015,0.0007],"rotation_xyzw":[0.0,0.0,0.0,1.0]}}; actor.apply(0,false)
\tvar partial: Dictionary = actor.live_pose.duplicate(true)
\tmade = Native.create(actor)
\tvar partial_ok := not made.has("error")
\tif partial_ok:
\t\tvar step := native_step(made.runner)
\t\tpartial_ok = not step.has("error") and step.pose.size() == 5
\t\tfor selected in selected_ids(resolution): partial_ok = partial_ok and step.get("pose",{}).get(selected,Model.identity()).position == partial.get(selected,Model.identity()).position
\t\tmade.runner.dispose()
\tactor.live_pose = null; actor.apply(0,false)
\tcheck(partial_ok and model_bytes(actor) == saved and bytes_of(report_of(actor)) == report,"load."+name+".fresh_partial_dictionary")

'''
    value=change(value,'func load_actor(index: int) -> bool:',fresh+'func load_actor(index: int) -> bool:')
    value=change(value,'actor.data.pose = authored_pose(actor,resolution,false)','fresh_baseline_checks(actor,resolution,name)\n\tactor.data.pose = authored_pose(actor,resolution,false)')
    value=change(value,'"chain_id": runner.chains[0].ids[0] = other',
                 '"chain_id": runner.chains[0].ids[0] = other\n\t\t"chain_reorder": runner.chains.reverse()\n\t\t"chain_source_binding": runner.chains[0].source.joints[0].binding.id = other\n\t\t"chain_binding_kind": runner.chains[0].source.joints[0].binding.kind = "root"\n\t\t"chain_duplicate": runner.chains.append(runner.chains[0].duplicate(true))')
    value=change(value,'\tif CREATE_REFUSALS.has(kind):\n\t\tvar rejected:',
                 '\tif kind.begins_with("force_slot_"):\n\t\tforces = [Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,Vector3.ZERO]\n\t\tforces[int(kind.get_slice("_",2))] = Vector3(NAN,0.0,0.0)\n\tif CREATE_REFUSALS.has(kind):\n\t\tvar rejected:')
    extras='''func wrapper_inventory_case(kind: String) -> void:
\tvar actor: RefCounted=actors[0]; baseline(actor)
\tvar made: Dictionary=await Secondary.create(actor,null,FRAME,false)
\tif made.has("error"):
\t\tfor suffix in ["refused","atomic","visual_exact","restored"]:check(false,"wrapper_inventory."+kind+"."+suffix)
\t\treturn
\tvar sim: RefCounted=made.physics;sim.start()
\tvar warm: String=sim.advance(Math.DT,FRAME,float(FRAME),false,[],null)
\tif warm.is_empty():ticks_executed+=1
\tvar before:=state_bytes(sim.runner);var latest:=bytes_of(sim.latest);var visual:=model_bytes(actor)
\tvar age: float=sim.age;var last_time: float=sim.last_input_time;var processed: int=sim.runner.processing_samples
\tmatch kind:
\t\t"source_missing":sim.runner.chains[0].erase("source")
\t\t"joints_empty":sim.runner.chains[0].source.joints=[]
\t\t"binding_shape":sim.runner.chains[0].source.joints[0].binding=[]
\t\t"count":sim.runner.chains.pop_back()
\t\t"order":sim.runner.chains.reverse()
\tvar error: String=sim.advance(Math.DT,FRAME,float(FRAME),false,[],null)
\tcheck(warm.is_empty() and not error.is_empty(),"wrapper_inventory."+kind+".refused")
\tcheck(state_bytes(sim.runner)==before and bytes_of(sim.latest)==latest and sim.age==age and sim.last_input_time==last_time and sim.runner.processing_samples==processed,"wrapper_inventory."+kind+".atomic")
\tcheck(model_bytes(actor)==visual,"wrapper_inventory."+kind+".visual_exact")
\tsim.stop();sim.dispose();baseline(actor)
\tcheck(model_bytes(actor)==snapshots[0] and document_bytes(actor)==docs[0] and bytes_of(report_of(actor))==raw_reports[0],"wrapper_inventory."+kind+".restored")

func direct_null_checks() -> void:
\tvar actor: RefCounted = actors[0]; baseline(actor)
\tvar model_before := model_bytes(actor); var document := document_bytes(actor)
\tvar made: Dictionary = Native.create(actor)
\tif made.has("error"):
\t\tcheck(false,"baseline.direct_nonzero_null_refused"); check(false,"baseline.direct_nonzero_null_atomic"); check(model_bytes(actor) == model_before,"baseline.direct_nonzero_null_pose_exact"); return
\tvar runner: RefCounted = made.runner; var saved := state_bytes(runner)
\tvar rejected := native_step(runner)
\tcheck(rejected.has("error") and str(rejected.error).contains("fresh authored pose baseline"),"baseline.direct_nonzero_null_refused")
\tcheck(state_bytes(runner) == saved and runner._tick == 0,"baseline.direct_nonzero_null_atomic")
\tcheck(model_bytes(actor) == model_before and document_bytes(actor) == document,"baseline.direct_nonzero_null_pose_exact")
\trunner.dispose(); baseline(actor)

func root_rotation_checks() -> void:
\tvar actor: RefCounted = actors[0]; var original: Dictionary = actor.data.duplicate(true)
\tfor spec in [{"name":"half","scale":0.5},{"name":"one","scale":1.0},{"name":"two","scale":2.0}]:
\t\tactor.data = original.duplicate(true); actor.data.scale = spec.scale
\t\tfor key in actor.data.pose_keys:
\t\t\tkey.transform.scale = spec.scale
\t\t\tvar q := Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47 if key.frame == 24 else -0.21)
\t\t\tkey.transform.rotation_xyzw = [q.x,q.y,q.z,q.w]
\t\tactor.live_pose = null; actor.live_world_transform = null; actor.apply(0,false)
\t\tvar saved := model_bytes(actor); var document := bytes_of(actor.data)
\t\tvar made: Dictionary = await Secondary.create(actor,null,0,false)
\t\tvar ok := not made.has("error"); var sizes_exact := ok; var drift := 0.0
\t\tvar measured_samples:=0;var measured_total_usec:=0;var measured_max_usec:=0;var native_perf: Dictionary={}
\t\tif ok:
\t\t\tvar sim: RefCounted = made.physics; sim.start()
\t\t\tvar sizes := bytes_of(sim.runner._chain.snapshot().sizes)
\t\t\tfor tick in range(1,TICKS+1):
\t\t\t\tvar time: float = float(tick)*Math.DT*24.0
\t\t\t\tvar started: int=Time.get_ticks_usec()
\t\t\t\tvar error: String = sim.advance(Math.DT,int(floor(time)),time,true,[],null)
\t\t\t\tvar elapsed: int=maxi(0,Time.get_ticks_usec()-started)
\t\t\t\tmeasured_samples+=1;measured_total_usec+=elapsed;measured_max_usec=maxi(measured_max_usec,elapsed)
\t\t\t\tif not error.is_empty(): ok = false; break
\t\t\t\tticks_executed += 1
\t\t\t\tsizes_exact = sizes_exact and bytes_of(sim.runner._chain.snapshot().sizes) == sizes
\t\t\t\tvar measured: Dictionary = Native.frame64(sim.runner._skeleton.global_transform)
\t\t\t\tif measured.has("error"): ok = false; break
\t\t\t\tdrift = maxf(drift,absf(float(measured.scale)-sim.runner._prefix_scale))
\t\t\tok = ok and sim.runner._tick == TICKS and sim.runner._chain.snapshot().states.size() == 5
\t\t\tnative_perf={"samples":sim.runner.processing_samples,"mean_usec":float(sim.runner.processing_total_usec)/float(maxi(1,sim.runner.processing_samples)),"max_usec":sim.runner.processing_max_usec,"scope":"Successful full Native.step, measured only; no FPS criterion"}
\t\t\tsim.stop(); sim.dispose(); actor.live_pose = null; actor.live_world_transform = null; actor.apply(0,false)
\t\tcheck(ok,"rotation."+spec.name+".fixed_ticks")
\t\tcheck(sizes_exact,"rotation."+spec.name+".sizes_exact")
\t\tcheck(bytes_of(actor.data) == document and bytes_of(report_of(actor)) == raw_reports[0],"rotation."+spec.name+".authored_preserved")
\t\tcheck(model_bytes(actor) == saved,"rotation."+spec.name+".Off_exact")
\t\tmetrics["rotation_"+spec.name] = {"prefix_scale_residual_max":drift,"logical_scale":spec.scale,"completed":ok,"advance_samples":measured_samples,"advance_mean_usec":float(measured_total_usec)/float(maxi(1,measured_samples)),"advance_max_usec":measured_max_usec,"native_step_processing":native_perf,"FPS_pass_claimed":false}
\tactor.data = original; baseline(actor)

'''
    value=change(value,'func planned_names() -> Array:',extras+'func planned_names() -> Array:')
    value=change(value,'["copied","actual_Model_SceneIO","qualified69_49","complete_nonrest_baseline","raw_report_file_exact"]',
                 '["copied","actual_Model_SceneIO","qualified69_49","complete_nonrest_baseline","raw_report_file_exact","fresh_rest_null","fresh_partial_dictionary"]')
    value=change(value,'\tnames.sort()\n\treturn names',
                 '\tfor suffix in ["refused","atomic","pose_exact"]: names.append("baseline.direct_nonzero_null_"+suffix)\n\tfor root_name in ["half","one","two"]:\n\t\tfor suffix in ["fixed_ticks","sizes_exact","authored_preserved","Off_exact"]: names.append("rotation."+root_name+"."+suffix)\n\tfor kind in WRAPPER_INVENTORY_CASES:\n\t\tfor suffix in ["refused","atomic","visual_exact","restored"]:names.append("wrapper_inventory."+kind+"."+suffix)\n\tnames.sort()\n\treturn names')
    value=change(value,'\tinstance_checks()','\tdirect_null_checks()\n\tinstance_checks()')
    value=change(value,'\tawait wrapper_checks()','\tawait wrapper_checks()\n\tfor kind in WRAPPER_INVENTORY_CASES:await wrapper_inventory_case(kind)\n\tawait root_rotation_checks()')
    value=change(value,'runners[0]._tick == TICKS and state_bytes(runners[1])',
                 'runners[0]._tick == TICKS and runners[0].processing_samples == TICKS and runners[1].processing_samples == 0 and runners[2].processing_samples == 0 and state_bytes(runners[1])')
    value=change(value,'state_bytes(runners[0]) == state_bytes(runners[1]) and state_bytes(runners[2])',
                 'state_bytes(runners[0]) == state_bytes(runners[1]) and runners[0].processing_samples == TICKS and runners[1].processing_samples == TICKS and runners[2].processing_samples == 0 and state_bytes(runners[2])')
    return value


def ui_successors(old,driver):
    value=old.replace('res://tests/source_native_live_capture.gd','res://tests/source_native_five_capture.gd')
    value=value.replace('has_source_native_live_job_1','has_source_native_five_live_job_2').replace('has_source_native_live_result_1','has_source_native_five_live_result_2')
    value=change(value,'"native_rules_solved":1','"native_rules_solved":5')
    start=value.index('class TickGate extends Node:');end=value.index('func _initialize()',start)
    gate='''class TickGate extends Node:
\tvar editor
\tvar runner
\tvar target: int
\tvar done := false
\tvar samples: Array[Vector3] = []
\tvar samples_by_id: Dictionary = {}
\tvar actor
\tvar bone_id := ""
\tvar lengths: Dictionary = {}
\tvar world_scale := 1.0
\tvar maximum_tip_error := 0.0
\tvar state_valid := true
\tfunc _physics_process(_delta: float) -> void:
\t\tif runner == null or not runner.active():
\t\t\teditor.set_physics_process(false);done=true;set_physics_process(false);return
\t\tvar states: Dictionary = runner._chain.snapshot().states
\t\tstate_valid = state_valid and states.size() == 5 and runner.chains.size() == 5
\t\tfor id in lengths:
\t\t\tvar value: Vector3 = actor.bone_transform(id)*Vector3(0,0,lengths[id])
\t\t\tvar tip: Array = states.get(id,{}).get("tip",[])
\t\t\tif tip.size()!=3: state_valid=false
\t\t\telse:
\t\t\t\tvar desired:=Vector3(float(tip[0]),float(tip[1]),float(tip[2]))
\t\t\t\tif not value.is_finite() or not desired.is_finite():state_valid=false
\t\t\t\telse:
\t\t\t\t\tvar error: float = value.distance_to(desired)
\t\t\t\t\tmaximum_tip_error=maxf(maximum_tip_error,error)
\t\t\t\t\tstate_valid = state_valid and error <= .00002*float(runner._size_tokens[id])
\t\t\tif not samples_by_id.has(id):samples_by_id[id]=[]
\t\t\tsamples_by_id[id].append(value)
\t\t\tif id==bone_id:samples.append(value)
\t\tif runner._tick >= target:
\t\t\teditor.set_physics_process(false);done=true;set_physics_process(false)

'''
    value=value[:start]+gate+value[end:]
    helper='''func selected_bindings() -> Array:
\tvar resolved: RefCounted = Bindings.resolve(actor())
\tvar result: Array=[]
\tif resolved.status!="bound_inactive":return result
\tfor index in [8,17,18,26,27]:result.append(resolved.bindings[index])
\treturn result

func selected_ids() -> Array:
\tvar result: Array=[]
\tfor entry in selected_bindings():result.append(entry.has_id)
\treturn result

func subtree_captures() -> Dictionary:
\tvar resolved: RefCounted=Bindings.resolve(actor());var result: Dictionary={}
\tif resolved.status!="bound_inactive":return result
\tfor index in [8,17,18,26,27]:
\t\tvar native_ids: Array = [17,18] if index==17 else [26,27] if index==26 else [index]
\t\tvar chosen: Array=[]
\t\tfor native_id in native_ids:chosen.append(resolved.bindings[native_id])
\t\tresult[str(index)]=Capture.capture(actor(),chosen)
\treturn result

'''
    value=change(value,'func world_bones(exclude: String="") -> PackedByteArray:',helper+'func world_bones(exclude: Array=[]) -> PackedByteArray:')
    value=change(value,'if id!=exclude:rows.append([id,actor().bone_transform(id)])','if not exclude.has(id):rows.append([id,actor().bone_transform(id)])')
    value=value.replace('world_bones(binding.has_id)','world_bones(selected_ids())')
    value=value.replace('Capture.capture(actor(),binding)','Capture.capture(actor(),selected_bindings())')
    value=change(value,'gate.world_scale=float(simulation.runner._scale)',
                 'gate.world_scale=float(simulation.runner._size_tokens[binding.has_id])\n\tfor id in simulation.runner._size_tokens:gate.world_scale=minf(gate.world_scale,float(simulation.runner._size_tokens[id]))')
    value=change(value,'if int(row.native_bone_index)==8:gate.length=float(row.parameters.length)*Native.SOURCE_SCALE',
                 'if int(row.native_bone_index) in [8,17,18,26,27]:\n\t\t\tvar id: String=simulation.runner.resolution.by_native[int(row.native_bone_index)]\n\t\t\tgate.lengths[id]=float(row.parameters.length)*Native.SOURCE_SCALE')
    value=change(value,'captured.affected==152 and captured.shared==144 and captured.unaffected==9509',
                 'captured.affected==694 and captured.shared==484 and captured.unaffected==8967')
    value=value.replace('authored_and_68_bones','authored_and_64_bones')
    value=change(value,'var captured:=Capture.capture(actor(),selected_bindings())',
                 'var captured:=Capture.capture(actor(),selected_bindings())\n\tvar subtrees: Dictionary=subtree_captures()')
    value=change(value,'check(not captured.has("error") and captured.vertices==9661 and captured.affected==694 and captured.shared==484 and captured.unaffected==8967,name+".weighted_profile")',
                 'var profile_ok: bool=not captured.has("error") and captured.vertices==9661 and captured.affected==694 and captured.shared==484 and captured.unaffected==8967 and subtrees.size()==5\n\tfor native_index in [8,17,18,26,27]:\n\t\tvar domain: Dictionary=subtrees.get(str(native_index),{})\n\t\tvar expected: Array=SUBTREE_COUNTS[str(native_index)]\n\t\tprofile_ok=profile_ok and not domain.has("error") and domain.get("affected")==expected[0] and domain.get("shared")==expected[1] and domain.get("unaffected")==expected[2]\n\tcheck(profile_ok,name+".weighted_profile")')
    profile=json.loads((HERE/'PUBLIC_PROFILE.json').read_bytes())
    domains={str(i):[profile['influence_counts']['subtree'+str(i)][key] for key in ('weighted_to_selected','shared_with_other_bones','unaffected')] for i in [8,17,18,26,27]}
    value=change(value,'const Storage = preload("res://src/storage.gd")',
                 'const Storage = preload("res://src/storage.gd")\nconst SUBTREE_COUNTS := '+json.dumps(domains,separators=(',',':')))
    value=change(value,'var samples: Array[Vector3]=gate.samples.duplicate();gate.free()',
                 'var samples: Array[Vector3]=gate.samples.duplicate()\n\tvar per_rule_samples: Dictionary=gate.samples_by_id.duplicate(true);gate.free()')
    value=change(value,'metrics[name]={"tick_count":180,',
                 'var tips: Dictionary={};var spans: Dictionary={}\n\tfor id in per_rule_samples:\n\t\tvar values: Array=per_rule_samples[id];var extent:=0.0\n\t\tif values.size()>60:\n\t\t\tfor point in values.slice(values.size()-60):extent=maxf(extent,point.distance_to(values[-1]))\n\t\ttips[id]=values[-1] if not values.is_empty() else Vector3.ZERO;spans[id]=extent\n\tmetrics[name]={"per_rule_last60_tick_spans":spans,"tick_count":180,')
    value=change(value,'"per_rule_last60_tick_spans":spans,"tick_count":180,',
                 '"native_step_processing":{"samples":simulation.runner.processing_samples,"mean_usec":float(simulation.runner.processing_total_usec)/float(maxi(1,simulation.runner.processing_samples)),"max_usec":simulation.runner.processing_max_usec,"scope":"Successful full Native.step; measured only, no FPS criterion"},"per_rule_last60_tick_spans":spans,"tick_count":180,')
    value=change(value,'"last_second_tip_span":span','"last60_tick_span":span,"span_duration_seconds":0.5')
    value=change(value,'return {"capture":captured,"restored":restored,"tip":samples[-1] if not samples.is_empty() else Vector3.ZERO,"span":span}',
                 'return {"capture":captured,"restored":restored,"tip":samples[-1] if not samples.is_empty() else Vector3.ZERO,"span":span,"tips":tips,"spans":spans,"subtrees":subtrees}')
    value=change(value,'var delta:=Capture.difference(control,profile[name].capture,.00001)\n\t\tcheck(not delta.has("error") and delta.unaffected_exact and delta.affected_vertices_moved>0 and delta.affected_max>.00001,"fan."+name+"_weighted_response")\n\t\tmetrics[name]["affected_max_vs_disabled"]=delta.get("affected_max",0.0)',
                 'var delta:=Capture.difference(control,profile[name].capture,.00001)\n\t\tvar every_rule: bool=not delta.has("error") and delta.unaffected_exact and delta.affected_vertices_moved>0 and delta.affected_max>.00001\n\t\tvar original_front: Dictionary={}\n\t\tfor index in [8,17,18,26,27]:\n\t\t\tvar difference:=Capture.difference(profile.disabled.subtrees[str(index)],profile[name].subtrees[str(index)],.00001)\n\t\t\tevery_rule=every_rule and not difference.has("error") and difference.affected_vertices_moved>0 and difference.affected_max>.00001\n\t\t\tif index==8:original_front=difference\n\t\tcheck(every_rule,"fan."+name+"_weighted_response")\n\t\tmetrics[name]["affected_max_vs_disabled"]=original_front.get("affected_max",0.0)\n\t\tmetrics[name]["union_affected_max_vs_disabled"]=delta.get("affected_max",0.0)')
    value=change(value,'check(metrics.speed50.affected_max_vs_disabled>.001 and profile.speed50.span>.00005,"fan.strong_response_and_wiggle")',
                 'var every_wiggle: bool=metrics.speed50.affected_max_vs_disabled>.001 and profile.speed50.span>.00005\n\tfor id in profile.speed50.spans:every_wiggle=every_wiggle and profile.speed50.spans[id]>.00005\n\tcheck(every_wiggle,"fan.strong_response_and_wiggle")')
    value=change(value,'check(plus.dot(minus)<0.0,"fan.opposite_tip_directions")',
                 'var every_opposite: bool=plus.dot(minus)<0.0\n\tfor id in profile.speed12.tips:\n\t\tvar positive: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id]\n\t\tvar negative: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]\n\t\tevery_opposite=every_opposite and positive.dot(negative)<0.0\n\tcheck(every_opposite,"fan.opposite_tip_directions")')
    fresh='''\t# Actual native On/Off before synthetic full-pose keys.
\tvar fresh_data: Dictionary=actor().data.duplicate(true);var fresh_worlds:=world_bones()
\tvar fresh: RefCounted=await on();await settled()
\tcheck(fresh is Secondary and fresh.native_backend and fresh.runner.chains.size()==5 and fresh.runner._chain.snapshot().states.size()==5,"import.fresh_native5_on")
\tvar fallback_ok: bool=fresh!=null and fresh.latest.size()>=5 and fresh_data.pose_keys.is_empty() and fresh_data.pose.size()<69
\tif fresh:
\t\tfor id in selected_ids():fallback_ok=fallback_ok and fresh.latest.get(id,Model.identity()).position==fresh_data.pose.get(id,Model.identity()).position
\tcheck(fallback_ok,"import.fresh_native5_identity_fallback")
\tawait off()
\tcheck(unchanged_pose(fresh_data) and world_bones()==fresh_worlds,"import.fresh_native5_off_exact")
\tactor().data.pose={binding.has_id:{"position":[0.001,-0.0015,0.0007],"rotation_xyzw":[0.0,0.0,0.0,1.0]}};actor().data.pose_keys=[];app.set_frame(0)
\tvar partial: Dictionary=actor().data.duplicate(true);fresh=await on();await settled()
\tvar partial_ok: bool=fresh is Secondary and fresh.native_backend
\tif fresh:
\t\tfor id in selected_ids():partial_ok=partial_ok and fresh.latest.get(id,Model.identity()).position==partial.pose.get(id,Model.identity()).position
\tawait off();check(partial_ok and unchanged_pose(partial),"import.partial_native5_on_off")
\tactor().data=fresh_data;app.set_frame(0)
'''
    value=change(value,'\tvar original_report_sha:=digest(raw_report())',fresh+'\tvar original_report_sha:=digest(raw_report())')
    value=change(value,'for index in [7,8,18]:','for index in [7,8,17,18,25,26,27]:')
    value=change(value,'actor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":transform.duplicate(true),"interpolation":"linear"}]',
                 'var later: Dictionary=transform.duplicate(true);var root_q:=Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)\n\tlater.rotation_xyzw=[root_q.x,root_q.y,root_q.z,root_q.w]\n\tactor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":later,"interpolation":"linear"}]\n\tcheck(transform.scale==later.scale and transform.rotation_xyzw!=later.rotation_xyzw,"import.keyed_root_rotation_constant_scale")')
    driver=driver.replace('has_source_native_live_job_1','has_source_native_five_live_job_2').replace('has_source_native_live_result_1','has_source_native_five_live_result_2')
    driver=driver.replace('tests/source_native_live_ui.gd','tests/source_native_five_live_ui.gd').replace('tests/source_native_live_capture.gd','tests/source_native_five_capture.gd')
    driver=driver.replace('authored_and_68_bones','authored_and_64_bones')
    driver=change(driver,"result.get('native_rules_solved') == 1","result.get('native_rules_solved') == 5")
    driver=change(driver,"CAPTURE_SHA = '1ffecc00666a7e9e6957b7354fd0b862eac07b0f16b79200345370348e91aacb'","CAPTURE_SHA = 'b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'")
    driver=change(driver,"'import.nonrest_keys_valid', 'fan.add_control'", "'import.nonrest_keys_valid', 'import.fresh_native5_on', 'import.fresh_native5_identity_fallback',\n              'import.fresh_native5_off_exact', 'import.partial_native5_on_off',\n              'import.keyed_root_rotation_constant_scale', 'fan.add_control'")
    driver=driver.replace('Explicit actual native8','SOURCE-ONLY UNRUN proposed native5').replace('HAS native8 live ','HAS native5 live ')
    return value,driver


def main():
    if TARGET.exists(): assert not any(TARGET.iterdir()), 'Only the empty first source-generation directory may be reused.'
    else: TARGET.mkdir(exist_ok=False)
    sources={}
    for name,expected in [('source_native_state_unit.gd','008e694dfc3947e9ca3054e6dff14b64e22ee0d1dea3aaf8147df6c9ec0e74fc'),
                          ('source_native_live_ui.gd','d5b10f2c06937296e597dae8fdac7e74cdff90c1d2b6b16d38865a80236663b7'),
                          ('verify_source_native_live.py','c4568f0d505a58125ceddd88aa1056cfea98fb0c70513d3a220d38ea1d0aaf6a')]:
        raw=(ROOT/'tests'/name).read_bytes(); assert hashlib.sha256(raw).hexdigest()==expected
        sources[name]=raw.decode('utf-8-sig')
    save('source_native_five_state_unit.gd',state_successor(sources['source_native_state_unit.gd']))
    # UI successor generation is installed below before invoking this script.
    ui,driver=ui_successors(sources['source_native_live_ui.gd'],sources['verify_source_native_live.py'])
    save('source_native_five_live_ui.gd',ui);save('verify_source_native_five_live.py',driver)
    capture=(ROOT/'output/source-0x31-native-chains-20261115-attempt1/Studio/chain_capture.gd').read_bytes()
    assert hashlib.sha256(capture).hexdigest()=='b1dc120815f9e56b79ca4406dd3a04ddd5b0978510c6e5ca8234b11ae88ff58b'
    (TARGET/'source_native_five_capture.gd').write_bytes(capture)
    print(json.dumps({'status':'SOURCE_ONLY_TEST_DRAFTS_UNPARSED_UNRUN','state_proposed_assertions':266,'old_predicates_retained':True}))


if __name__=='__main__':main()

extends SceneTree
const Model=preload("res://src/model.gd")
const Follow=preload("res://src/part_pose_follow_controller.gd")
var checks:=0
var failures:=0
var fixtures: Array=[]
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Synthetic part follow watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func record(id: String) -> Dictionary:
	return {"format":"studio_model_1","id":id,"name":id,"source":"synthetic-only.glb","sha256":"0".repeat(64),"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.,"visible":true,"reference_only":false,"pose":{},"draft_frame":0,"pose_keys":[],"metadata":{"part_follow_synthetic_fixture":true}}
func actor(name: String,parents: Array,bases: Array,names: Array,parent: Node3D) -> RefCounted:
	var result: RefCounted=Model.new();result.root=Node3D.new();result.root.name=name;parent.add_child(result.root)
	var sk:=Skeleton3D.new();sk.name="Rig"
	if sk.has_method("set_animate_physical_bones"):sk.call("set_animate_physical_bones",false)
	result.root.add_child(sk)
	for bone in names:sk.add_bone(bone)
	for i in range(names.size()):
		sk.set_bone_parent(i,parents[i]);sk.set_bone_rest(i,Transform3D.IDENTITY)
		sk.set_bone_pose(i,bases[i])
	sk.force_update_all_bone_transforms();result.inventory(result.root);result.data=record(name)
	return result
func fixture() -> Dictionary:
	var bundle:=Node3D.new();root.add_child(bundle);fixtures.append(bundle)
	var a: RefCounted=actor("Master",[-1,0,1],[Transform3D.IDENTITY,Transform3D(Basis(Vector3.UP,.2),Vector3.UP),Transform3D(Basis.IDENTITY,Vector3.UP)],["Root","Anchor","Tip"],bundle)
	# Child indices precede parents deliberately; the target root is index3.
	var b: RefCounted=actor("Target",[2,0,3,-1],[Transform3D(Basis(Vector3.UP,.1),Vector3.UP),Transform3D(Basis.IDENTITY,Vector3.DOWN),Transform3D(Basis(Vector3.BACK,.3),Vector3.UP),Transform3D(Basis.IDENTITY,Vector3(3,0,0))],["Tip","Loose","Anchor","Root"],bundle)
	return {"bundle":bundle,"a":a,"b":b,"as":a.bones["Rig::Root"].skeleton,"bs":b.bones["Rig::Root"].skeleton,"pairs":[{"master_id":"Rig::Anchor","target_id":"Rig::Anchor"},{"master_id":"Rig::Tip","target_id":"Rig::Tip"}]}
func capacity_fixture(count: int) -> Dictionary:
	var bundle:=Node3D.new();root.add_child(bundle);fixtures.append(bundle)
	var parents:=[];var names:=[];var am:=[];var bm:=[];var pairs:=[]
	for i in range(count):
		parents.append(i-1);names.append("Joint"+str(i))
		am.append(Transform3D(Basis.IDENTITY,Vector3.ZERO if i==0 else Vector3(0,.02,0)))
		bm.append(Transform3D(Basis.IDENTITY,Vector3(.3,0,0) if i==0 else Vector3(0,.02,0)))
		pairs.append({"master_id":"Rig::Joint"+str(i),"target_id":"Rig::Joint"+str(i)})
	var a: RefCounted=actor("Master54",parents,am,names,bundle)
	var b: RefCounted=actor("Target54",parents,bm,names,bundle)
	return {"bundle":bundle,"a":a,"b":b,"bs":b.bones["Rig::Joint0"].skeleton,"pairs":pairs}
func raw(sk: Skeleton3D) -> Array:
	var result:=[]
	for i in range(sk.get_bone_count()):result.append([sk.get_bone_pose_position(i),sk.get_bone_pose_rotation(i),sk.get_bone_pose_scale(i)])
	return result
func apply_data(who: RefCounted,value: Dictionary) -> void:
	who.data=value.duplicate(true);who.apply(0,true)
func capture(control: RefCounted,epoch: int) -> Dictionary:
	return control.capture_authored(epoch,Follow.PHASE,0,true,true)
func apply(control: RefCounted,epoch: int) -> Dictionary:
	return control.apply_captured(epoch,Follow.PHASE)
func override_global(sk: Skeleton3D,index: int,amount: float) -> void:
	var value: Transform3D=sk.get_bone_global_pose(index)
	if amount>0:value.origin+=Vector3(.4,0,0)
	sk.call("set_bone_global_pose_override",index,value,amount,true)
	sk.force_update_all_bone_transforms()
func finish() -> void:
	for node in fixtures:
		if is_instance_valid(node):node.free()
	await process_frame;await process_frame
	print("PART_POSE_FOLLOW_CONTROLLER "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"actual_Model_API_used":true,"actual_Skeleton3D_used":true,"actual_native_bindings_qualified":false,"actual_native_alignment_qualified":false,"application_adopted":false,"SecondaryLive_integration_qualified":false}))
	quit(1 if failures else 0)
func run() -> void:
	check(DisplayServer.get_name()=="headless","real Skeleton API fixture remains headless")
	var f:=fixture();var a: RefCounted=f.a;var b: RefCounted=f.b;var ask: Skeleton3D=f["as"];var bsk: Skeleton3D=f.bs
	check(ask!=bsk and ask.get_bone_name(1)==bsk.get_bone_name(2),"identical names remain owned by two distinct Skeletons")
	check(b.bones["Rig::Anchor"].base!=bsk.get_bone_rest(2),"Model inventory captures actual imported base pose instead of Skeleton rest")
	check(Model.validate(a.data,48).is_empty() and Model.validate(b.data,48).is_empty(),"synthetic actors use actual valid Model records")
	a.apply(0,true);b.apply(0,true)
	var made: Dictionary=Follow.create_fixture(a,b,f.bundle,f.pairs)
	check(made.has("controller") and made.get("native_qualified")==false,"explicit runtime pairs create only a synthetic controller")
	if not made.has("controller"):await finish();return
	var c: RefCounted=made.controller
	var user_modifier:=PhysicalBoneSimulator3D.new();user_modifier.active=false;bsk.add_child(user_modifier)
	check(Follow.create_fixture(a,b,f.bundle,f.pairs).has("error"),"even an inactive user-added simulator is outside the fixture-owned phase")
	bsk.remove_child(user_modifier);user_modifier.free()
	check(Follow.create_native(a,b,f.bundle,{}).has("error"),"native source-index admission remains explicitly unsupported")
	var nested:=fixture();nested.b.root.reparent(nested.a.root)
	check(Follow.create_fixture(nested.a,nested.b,nested.bundle,nested.pairs).has("error"),"nested actor roots cannot double inherit the master object transform")
	check(Follow.create_fixture(a,a,f.bundle,f.pairs).has("error"),"one actor cannot alias both owners")
	check(Follow.create_fixture(RefCounted.new(),b,f.bundle,f.pairs).has("error"),"duck-typed substitute is not admitted as the actual Model script")
	check(Follow.create_fixture(a,b,f.bundle,[{"master_id":"Rig::missing","target_id":"Rig::Tip"}]).has("error"),"missing runtime ID is never guessed from a nearby name")
	check(Follow.create_fixture(a,b,f.bundle,[f.pairs[0],f.pairs[0]]).has("error"),"duplicate target ownership refuses")
	check(Follow.create_fixture(a,b,f.bundle,f.pairs,{"target":["Rig::Tip"]}).has("error"),"target procedural ownership excludes a followed channel")
	check(Follow.create_fixture(a,b,f.bundle,f.pairs,{"master":["Rig::Anchor"]}).has("error"),"master procedural ownership is also explicit")
	check(Follow.create_fixture(a,b,f.bundle,f.pairs,{"target":["foreign"]}).has("error"),"unknown procedural ID cannot silently waive ownership")
	var initial:=raw(bsk);var master_initial:=raw(ask);var ad: Dictionary=a.data.duplicate(true);var bd: Dictionary=b.data.duplicate(true)
	check(not capture(c,1).has("error"),"both actual applied Models admit their authored frame")
	var at_rest: Dictionary=apply(c,1)
	check(not at_rest.has("error") and raw(bsk)==initial and raw(ask)==master_initial,"following at master rest leaves both actual rigs unchanged")
	var writes: int=c.stats.pose_writes;var repeat: Dictionary=apply(c,1)
	check(repeat.get("writes")==0 and c.stats.pose_writes==writes,"same captured epoch performs no second pose write or accumulation")
	check(not c.release_owned().has("error") and raw(bsk)==initial,"Off restores exact captured position quaternion and scale channels")
	check(c.capture_authored(2,"secondary_running",0,true,true).has("error"),"unsupported secondary phase refuses capture")
	check(capture(c,1).has("error"),"stale epochs cannot reuse a released snapshot")
	var q:=Quaternion(Vector3.BACK,PI/2.)
	a.data.pose["Rig::Root"]={"position":[1,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	check(capture(c,2).has("error") and raw(bsk)==initial,"changed master data without Model.apply detects stale dependency order")
	# Evaluate target first, then the actual master: capture verifies both are ready.
	b.data.pose["Rig::Tip"]={"position":[0,0,0],"rotation_xyzw":[sin(.125),0,0,cos(.125)]}
	b.apply(0,true);a.apply(0,true)
	var authored:=raw(bsk);var master_authored:=raw(ask);var target_data: Dictionary=b.data.duplicate(true);var master_data: Dictionary=a.data.duplicate(true)
	var history:=UndoRedo.new();var version:=history.get_version()
	check(not capture(c,2).has("error"),"capture verifies current Models independent of sibling evaluation order")
	var applied: Dictionary=apply(c,2)
	check(not applied.has("error") and applied.get("writes")==2,"actual controller writes exactly the two linked target bones")
	check(bsk.get_bone_global_pose(2).origin.distance_to(Vector3(0,3,0))<.00002,"actual target anchor follows the independently expected translated quarter-turn")
	check(bsk.get_bone_global_pose(0).origin.distance_to(Vector3(-cos(.3),3-sin(.3),0))<.00002,"actual child world goal keeps its different rest offset")
	check(Follow.same_frame(bsk.get_bone_pose(0),c.captured.b[0].local),"linked child does not apply its linked parent's master delta twice")
	check(raw(bsk)[1]==authored[1] and bsk.get_bone_global_pose(1).origin.distance_to(Vector3(3,0,0))>.1,"unlinked loose child keeps its own exact local channels while its anchor moves")
	check(raw(ask)==master_authored and a.data==master_data and b.data==target_data,"derived following never writes master channels or either authored Model record")
	check(history.get_version()==version and history.get_history_count()==0 and b.data.pose_keys.is_empty(),"derived evaluation creates no Undo action or recorded key")
	var derived:=raw(bsk);var derived_channels: Dictionary=c.channels.duplicate(true)
	check(derived_channels.size()==2 and derived_channels.has("Rig::Tip") and derived_channels.has("Rig::Anchor"),"inspection channels remain owned by explicit target IDs only")
	check(not c.release_owned().has("error") and raw(bsk)==authored,"Off restores the target's refined pre-follow pose exactly")
	var roundtrip: Dictionary=target_data.duplicate(true)
	for id in derived_channels:roundtrip.pose[id]=derived_channels[id].duplicate(true)
	apply_data(b,roundtrip)
	var expected_tip:=Transform3D(Basis(derived[0][1])*Basis.from_scale(derived[0][2]),derived[0][0])
	var expected_anchor:=Transform3D(Basis(derived[2][1])*Basis.from_scale(derived[2][2]),derived[2][0])
	check(Follow.same_frame(bsk.get_bone_pose(0),expected_tip) and Follow.same_frame(bsk.get_bone_pose(2),expected_anchor),"derived base-relative channels roundtrip through actual Model.apply")
	check(bsk.get_bone_pose_scale(0)==authored[0][2] and bsk.get_bone_pose_scale(2)==authored[2][2],"actual Model roundtrip retains imported per-bone base scale")
	apply_data(b,target_data)
	check(raw(bsk)==authored,"ordinary authored Model.apply restores its own channels after the roundtrip probe")
	f.bundle.transform=Transform3D(Basis(Vector3.UP,.6).scaled(Vector3.ONE*2.),Vector3(-3,1,7))
	a.apply(0,true);b.apply(0,true)
	check(not capture(c,3).has("error") and not apply(c,3).has("error"),"same explicit bundle root can move rotate and scale once")
	check((bsk.global_transform*bsk.get_bone_global_pose(2)).origin.distance_to(f.bundle.global_transform*Vector3(0,3,0))<.00005,"actual Skeleton result receives the common bundle transform exactly once")
	check(apply(c,3).get("writes")==0,"repeated moved-bundle frame still performs no additional writes")
	check(not c.release_owned().has("error") and raw(bsk)==authored,"moved-bundle Off still restores local authored channels")
	check(not capture(c,4).has("error"),"new epoch snapshots both ready actors")
	var before_global_first:=raw(bsk)
	override_global(ask,1,1.)
	check(apply(c,4).has("error") and raw(bsk)==before_global_first and c.owned.is_empty(),"master global-only override after capture refuses before first writes")
	override_global(ask,1,0.);override_global(bsk,2,1.)
	check(apply(c,4).has("error") and raw(bsk)==before_global_first and c.owned.is_empty(),"target global-only override after capture also refuses before first writes")
	override_global(bsk,2,0.)
	a.data.pose["Rig::Root"].position=[2,0,0];a.apply(0,true)
	check(apply(c,4).has("error") and raw(bsk)==authored,"master changes after capture refuse before any target write")
	c.release_owned();apply_data(a,master_data)
	check(not capture(c,5).has("error"),"released failed epoch can recapture under a new epoch")
	b.live_pose={}
	check(apply(c,5).has("error") and raw(bsk)==authored,"actual SecondaryLive-style live_pose entry refuses the unsupported phase")
	b.live_pose=null;c.release_owned();a.preview_frame=0
	check(capture(c,6).has("error"),"interactive preview overrides need an explicit integration adapter")
	a.preview_frame=-1
	b.data.metadata.part_follow_synthetic_fixture=false
	check(capture(c,6).has("error"),"fixture marker admission remains mandatory across epochs")
	b.data.metadata.part_follow_synthetic_fixture=true;b.data.metadata["native_parameters"]={}
	check(capture(c,6).has("error"),"native parameters cannot enter through an existing fixture controller")
	b.data.metadata.erase("native_parameters")
	var refined: Dictionary=target_data.duplicate(true);refined.pose["Rig::Tip"].rotation_xyzw=[sin(.2),0,0,cos(.2)]
	history.create_action("Own target refinement");history.add_do_method(apply_data.bind(b,refined));history.add_undo_method(apply_data.bind(b,target_data));history.commit_action()
	var history_size:=history.get_history_count();var refined_data: Dictionary=b.data.duplicate(true)
	check(not capture(c,6).has("error") and not apply(c,6).has("error") and history.get_history_count()==history_size and b.data==refined_data,"real UndoRedo owns refinement while follow remains a derived layer")
	c.release_owned();var undone:=history.undo()
	check(undone and b.data==target_data and not capture(c,7).has("error") and not apply(c,7).has("error"),"Undo reapplies authored target data before a fresh following epoch")
	c.release_owned();var redone:=history.redo()
	check(redone and b.data==refined and not capture(c,8).has("error") and not apply(c,8).has("error"),"Redo restores its own refinement without recording followed channels")
	check(history.get_history_count()==1 and b.data.pose_keys.is_empty(),"follow adds no hidden history entry or pose key during UndoRedo")
	var before_repeat_global:=raw(bsk);var repeat_writes: int=c.stats.pose_writes
	override_global(ask,1,1.)
	check(apply(c,8).has("error") and raw(bsk)==before_repeat_global and c.stats.pose_writes==repeat_writes,"master global-only writer cannot bypass repeated-epoch no-op")
	override_global(ask,1,0.);override_global(bsk,2,1.)
	check(apply(c,8).has("error") and raw(bsk)==before_repeat_global and c.stats.pose_writes==repeat_writes,"target global-only writer cannot bypass repeated-epoch no-op")
	override_global(bsk,2,0.)
	var foreign:=bsk.get_bone_pose_position(2)+Vector3(.1,0,0);bsk.set_bone_pose_position(2,foreign);bsk.force_update_all_bone_transforms()
	var conflict:=raw(bsk)
	check(c.release_owned().has("error") and raw(bsk)==conflict,"Off cannot overwrite a new writer and restores no partial subset")
	f.bundle.free()
	check(not c.dispose().has("error") and not c.dispose().has("error"),"freed target teardown and repeated dispose avoid stale Node access")
	var deleted:=fixture();deleted.a.apply(0,true);deleted.b.apply(0,true)
	var dc: RefCounted=Follow.create_fixture(deleted.a,deleted.b,deleted.bundle,deleted.pairs).controller
	var delete_authored:=raw(deleted.bs)
	deleted.a.data.pose["Rig::Root"]={"position":[1,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]};deleted.a.apply(0,true)
	var delete_capture: Dictionary=capture(dc,1);var delete_applied: Dictionary=apply(dc,1) if not delete_capture.has("error") else delete_capture
	deleted.a.root.free()
	check(delete_applied.get("writes")==2 and not dc.release_owned().has("error") and raw(deleted.bs)==delete_authored,"master deletion still permits exact target-owned restoration")
	check(not dc.dispose().has("error"),"master-deleted controller disposes after releasing its target")
	var late:=fixture();late.a.apply(0,true);late.b.apply(0,true)
	var lc: RefCounted=Follow.create_fixture(late.a,late.b,late.bundle,late.pairs).controller
	var before_late:=raw(late.bs);capture(lc,1);late.b.bones["Rig::Tip"].index=3
	check(apply(lc,1).has("error") and raw(late.bs)==before_late,"late runtime binding drift refuses atomically before either target write")
	late.b.bones["Rig::Tip"].index=0;lc.release_owned();lc.dispose()
	check(Follow.model_delta(Transform3D.IDENTITY,Transform3D(Basis.from_scale(Vector3(2,1,1)),Vector3.ZERO)).has("error"),"unrepresentable per-bone scale change is not silently serialized")
	var context:=fixture();context.a.apply(0,true);context.b.apply(0,true)
	var context_control: RefCounted=Follow.create_fixture(context.a,context.b,context.bundle,context.pairs).controller
	var context_rest:=raw(context.bs)
	context.a.data.pose["Rig::Root"]={"position":[1,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	context.a.data.pose_keys=[{"frame":0,"interpolation":"linear","pose":{},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.}}]
	context.a.apply(0,false);context.b.apply(0,true)
	check(Model.validate(context.a.data,48).is_empty() and context_control.capture_authored(1,Follow.PHASE,0,true,true).has("error"),"actual timeline pose cannot masquerade as a different saved draft context")
	context.a.apply(0,true)
	var draft_capture: Dictionary=context_control.capture_authored(1,Follow.PHASE,0,true,true)
	var draft_apply: Dictionary=context_control.apply_captured(1,Follow.PHASE) if not draft_capture.has("error") else draft_capture
	check(not draft_apply.has("error") and context.bs.get_bone_global_pose(2).origin.distance_to(Vector3(0,3,0))<.00002,"explicit edited context follows the actual applied draft rather than timeline rest")
	context_control.release_owned();context.a.apply(0,false);context.b.apply(0,false)
	var timeline_capture: Dictionary=context_control.capture_authored(2,Follow.PHASE,0,false,false)
	var timeline_apply: Dictionary=context_control.apply_captured(2,Follow.PHASE) if not timeline_capture.has("error") else timeline_capture
	check(not timeline_apply.has("error") and raw(context.bs)==context_rest and not context_control.dispose().has("error"),"explicit timeline context returns to rest without retaining draft following")
	var large:=capacity_fixture(54);large.a.apply(0,true);large.b.apply(0,true)
	var large_before:=raw(large.bs);var large_data: Dictionary=large.b.data.duplicate(true)
	var large_made: Dictionary=Follow.create_fixture(large.a,large.b,large.bundle,large.pairs)
	check(large_made.has("controller"),"54 generated explicit bindings exercise the body-dress-sized capacity without native data")
	if large_made.has("controller"):
		var cc: RefCounted=large_made.controller
		large.a.data.pose["Rig::Joint0"]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]};large.a.apply(0,true);large.b.apply(0,true)
		var cap: Dictionary=capture(cc,1);var solved54: Dictionary=apply(cc,1) if not cap.has("error") else cap
		check(not solved54.has("error") and solved54.get("writes")==54 and large.bs.get_bone_global_pose(53).origin.distance_to(Vector3(-1.06,.3,0))<.00005 and large.b.data==large_data,"all54 generated channels follow one same-frame delta without accumulating ancestor motion")
		check(not cc.release_owned().has("error") and raw(large.bs)==large_before and not cc.dispose().has("error"),"54-channel Off and disposal preserve exact imported/authored locals")
	else:
		check(false,"all54 generated channels require a constructed controller");check(false,"54-channel Off requires a constructed controller")
	if checks!=66:push_error("Expected66 isolated Skeleton controller assertions");failures+=1
	history.clear_history();history.free()
	await finish()

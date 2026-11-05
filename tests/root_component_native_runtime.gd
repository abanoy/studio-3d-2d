extends "res://tests/motion_assist_native.gd"
const ComponentRuntime=preload("res://src/root_component_runtime.gd")
const D=ComponentRuntime.Document
func attach(actor: RefCounted,data: Dictionary) -> String:
	actor.data=data;actor.motion_video={"fps_num":24,"fps_den":1,"duration_frames":48}
	actor.sample(0)
	return actor.evaluation_error
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(OS.get_cmdline_user_args()[1])
	while app.has_project.pid>0:await process_frame
	await settled();var plans: Array=app.current_world().objects.duplicate(true)
	for plan in plans:
		if not Model.is_contact(plan):continue
		var actor:=setup(plan);var poses:=[];var roots:=[]
		for half in range(97):poses.append(actor.sample(float(half)/2.));roots.append(actor.sample_transform(float(half)/2.))
		var promoted:=D.promote(actor.data,48);check(not promoted.has("error") and attach(actor,promoted.get("data",{})).is_empty(),"native component evaluator configures: "+plan.name)
		var exact:=true
		for half in range(97):exact=exact and actor.sample(float(half)/2.)==poses[half] and actor.sample_transform(float(half)/2.)==roots[half]
		check(exact,"component promotion preserves actual native contact poses: "+plan.name)
		var position: Vector3=T.vector(actor.sample_authored_transform(12).position)+Vector3(.001,0,0)
		var edited:=D.put_component(promoted.data,12,"position",[position.x,position.y,position.z],"ease",48);check(not edited.has("error") and attach(actor,edited.get("data",{})).is_empty(),"independent position edit joins native evaluator: "+plan.name)
		var reachable:=true;var peer_exact: bool=T.vector(actor.sample_transform(12).position).distance_to(position)<0.0000001 and T.vector(actor.sample_transform(12).position).distance_to(T.vector(roots[24].position))>0.0005;var values:=[]
		for half in range(97):
			var at:=float(half)/2.;values.append(actor.sample(at));reachable=reachable and actor.evaluation_error.is_empty();var root_value: Dictionary=actor.sample_transform(at);peer_exact=peer_exact and root_value.rotation_xyzw==roots[half].rotation_xyzw and root_value.scale==roots[half].scale
		var reverse:=true
		for half in range(96,-1,-1):reverse=reverse and actor.sample(float(half)/2.)==values[half]
		check(reachable and peer_exact and reverse,"native contacts remain reachable with exact turns/scale and reverse seeking: "+plan.name)
		var enabled: Dictionary=Model.motion_animation().configure(D.legacy_view(edited.data),true,.65,48).data
		var assisted: Dictionary=edited.data.duplicate(true);assisted.component_base_format=Model.MOTION_FORMAT;assisted["motion_assist"]=enabled.motion_assist
		actor.data=enabled;var composite=preload("res://src/root_component_assistance.gd").new();var error: String=composite.build(assisted,app.video)
		check(error.is_empty() and attach(actor,assisted).is_empty(),"native composite assistance compiles: "+plan.name)
		var assisted_values:=[];reachable=true;var changed:=false
		for half in range(97):
			assisted_values.append(actor.sample(float(half)/2.));reachable=reachable and actor.evaluation_error.is_empty();changed=changed or assisted_values[-1]!=values[half]
		reverse=true
		for half in range(96,-1,-1):reverse=reverse and actor.sample(float(half)/2.)==assisted_values[half]
		check(reachable and reverse and changed,"combined native root/bone helpers visibly change poses with reachable reversible contacts: "+plan.name)
		check(T.vector(actor.sample_transform(12).position).distance_to(position)<.000001 and actor.sample_transform(12).scale==roots[24].scale and not composite.helper_keys()["@root"].is_empty(),"native assistance preserves position main key/scale and exposes component helpers: "+plan.name)
	app.dirty=false;app.free();await settled();print("COMPONENT_NATIVE_RUNTIME "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

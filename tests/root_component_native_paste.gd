extends "res://tests/root_component_native_runtime.gd"
const Clipboard=preload("res://src/contact_clipboard.gd")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(OS.get_cmdline_user_args()[1])
	while app.has_project.pid>0:await process_frame
	await settled();var plans: Array=app.current_world().objects.duplicate(true)
	for plan in plans:
		if not Model.is_contact(plan):continue
		var actor:=setup(plan);var original:=D.promote(actor.data,48)
		var cut:=D.edit_clip(original.data,"split","",13,48)
		var removed:=D.edit_clip(cut.data,"remove",cut.right_id,0,48)
		# Remove any remaining tail/contact-only pieces to leave room for a copy.
		while removed.data.animation_clips.size()>1:
			removed=D.edit_clip(removed.data,"remove",removed.data.animation_clips[-1].id,0,48)
		var piece: Dictionary=removed.data.animation_clips[0].duplicate(true)
		var tracks: Dictionary=removed.data.root_components[piece.id].duplicate(true)
		actor.data=D.legacy_view(removed.data);check(attach(actor,removed.data).is_empty(),"native sliced component source prepares: "+plan.name)
		var poses:=[];var roots:=[]
		for half in range(25):poses.append(actor.sample(float(half)/2.));roots.append(actor.sample_transform(float(half)/2.))
		var shift:=Vector3(.001,0,0)
		var mapped:=Clipboard.reanchor(piece,Transform3D.IDENTITY,Transform3D(Basis.IDENTITY,shift))
		for key in tracks.position:
			var p:=T.vector(key.value.position)+shift;key.value.position=[p.x,p.y,p.z]
		var pasted:=D.paste_clip(removed.data,mapped.piece,tracks,32,48)
		check(not pasted.has("error"),"native copied contact IDs and component records validate: "+plan.name)
		if pasted.has("error"):continue
		actor.data=D.legacy_view(pasted.data);check(attach(actor,pasted.data).is_empty(),"native pasted components install in experimental evaluator: "+plan.name)
		var reachable:=true;var matching:=true;var sampled:=[]
		for half in range(25):
			var frame:=32.+float(half)/2.;var pose: Dictionary=actor.sample(frame);sampled.append(pose);reachable=reachable and actor.evaluation_error.is_empty()
			var transform: Dictionary=actor.sample_transform(frame)
			matching=matching and T.vector(transform.position).distance_to(T.vector(roots[half].position)+shift)<.000001
			for id in poses[half]:
				matching=matching and Preview.matching(pose.get(id,Model.identity()),poses[half][id])
		check(reachable and matching,"translated native pasted pins retain original solved motion: "+plan.name)
		var reverse:=true
		for half in range(24,-1,-1):reverse=reverse and actor.sample(32.+float(half)/2.)==sampled[half]
		check(reverse,"native pasted contact sampling is reversible: "+plan.name)
	app.dirty=false;app.free();await settled();print("COMPONENT_NATIVE_PASTE "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

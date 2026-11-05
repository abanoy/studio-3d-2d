extends SceneTree
const Model=preload("res://src/model.gd")
const Body=preload("res://src/body_animation.gd")
const Fixture=preload("res://tests/body_curve_fixture.gd")
const Timeline=Model.Timeline
const Channels=preload("res://src/animated_channels.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(170).timeout.connect(func():push_error("Body editor watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func bone(actor,suffix: String) -> String:
	for id in actor.order:
		if str(actor.bones[id].name).ends_with(suffix):return id
	return ""
func rotate(angle: float) -> Dictionary:
	var q:=Quaternion(Vector3.FORWARD,angle)
	return {"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
func same(a,b) -> bool:return JSON.stringify(a)==JSON.stringify(b)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("branches.glb");Fixture.create(asset)
	var plans: Array=[{"label":"Authored","source":asset,"metadata":{},"left":"left","right":"right"}];plans.append_array(JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json"))))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");var metrics:={};var movie:=""
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
		for field in plan.metadata:
			if field!="source_shape":actor.data.metadata[field]=plan.metadata[field]
		var metadata: Dictionary=actor.data.metadata.duplicate(true);var native_ids: Array=actor.order.duplicate();var source_hash:=FileAccess.get_sha256(actor.data.source)
		var left:=bone(actor,plan.left);var right:=bone(actor,plan.right)
		check(not left.is_empty() and not right.is_empty(),"standard native arm IDs bind in the normal editor: "+plan.label)
		if left.is_empty() or right.is_empty():continue
		var original: Dictionary=actor.data.duplicate(true)
		for frame in [0,24]:
			var transform:=Model.Clips.transform(original);transform.position[0]+=0. if frame==0 else .4
			original.pose_keys.append({"frame":frame,"pose":{left:rotate(0. if frame==0 else .6)},"transform":transform,"interpolation":"ease"})
		app.pose_editor.restore_state(original);app.set_frame(6);app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
		var before:=Model.new();before.data=original.duplicate(true);var editor=app.pose_editor
		app.set_frame(12);editor.tree_items[right].select(0);editor.operation.select(0);editor.refresh_values();var history: int=app.history.size()
		editor.fields[2].value=-50;editor.apply_numeric();await settled()
		check(actor.data.format==Model.BODY_FORMAT and app.history.size()==history+1,"normal numeric pose edit auto-keys model6 in one Undo: "+plan.label)
		var exact:=true
		for half in range(97):
			var frame:=float(half)/2;exact=exact and same(actor.sample(frame).get(left,Model.identity()),before.sample(frame).get(left,Model.identity())) and same(actor.sample_transform(frame),before.sample_transform(frame))
		check(exact,"normal bone edit preserves all peer/root half-frame samples: "+plan.label)
		var rows:=Channels.describe(actor.data)
		check(rows.any(func(row):return row.id==right and row.frames==[12]) and rows.any(func(row):return row.id==left and row.frames==[0,24]),"expanded normal timeline shows independent native part frames: "+plan.label)
		var keyed: Dictionary=actor.data.duplicate(true);app.undo();check(same(actor.data,original),"Undo restores the original legacy model and easing: "+plan.label)
		app.redo();check(same(actor.data,keyed),"Redo restores editable independent controls: "+plan.label)
		editor.tree_items[right].select(0);editor.delete_key();await settled()
		check(Body.B.frames(Body.view(actor.data),right).is_empty() and same(actor.sample(6).get(left,Model.identity()),before.sample(6).get(left,Model.identity())),"normal Delete selected part removes only its key: "+plan.label)
		app.undo();await settled();check(Body.B.frames(Body.view(actor.data),right)==[12],"Undo restores just-deleted native part controls: "+plan.label)
		var began:=Time.get_ticks_usec()
		for frame in range(100):actor.sample(float(frame%49)/2);actor.sample_transform(float(frame%49)/2)
		var average:=float(Time.get_ticks_usec()-began)/100.
		check(actor.data.metadata==metadata and actor.order==native_ids and FileAccess.get_sha256(actor.data.source)==source_hash,"normal independent editing preserves metadata, rig and source geometry: "+plan.label)
		if plan.label=="Authored":
			var split:=Model.Clips.split(actor.data,12);editor.restore_state(split.data)
			var moved:=Model.Clips.move(actor.data,split.right_id,30,48);editor.restore_state(moved.data);app.set_frame(36)
			check(same(actor.sample(36),Body.sample(keyed,18).pose),"normal split/move preserves independent source-time poses")
			app.undo();app.undo();editor.restore_state(keyed)
			var original_world: Dictionary=app.renderer.world_state().duplicate(true)
			editor.restore_state(split.data);app.clip_editor.request("copy",id,split.data.animation_clips[0].id,0)
			app.pose_editor.add_model(asset);var peer: RefCounted=app.renderer.active_model();var peer_id: String=peer.data.id
			var peer_base: Dictionary=peer.data.duplicate(true);peer_base.position[0]=4.;peer_base.pose={left:rotate(.2),right:rotate(.1)};editor.restore_state(peer_base)
			app.clip_editor.request("paste",peer_id,"",30);peer=app.renderer.world_runtime.instance(peer_id)
			check(peer.data.format==Model.BODY_FORMAT and same(peer.sample(36),Body.sample(keyed,6).pose) and same(peer.sample_transform(36),Body.sample(keyed,6).transform),"model6 clipboard promotes a legacy destination and preserves source motion over a different base")
			check(same(peer.sample(0).get(left,Model.identity()),peer_base.pose[left]) and same(peer.sample_transform(0),Model.Clips.transform(peer_base)),"pasting independent motion retains the receiving base outside its piece")
			var legacy_keys:=[]
			for frame in [0,4]:legacy_keys.append({"frame":frame,"pose":{left:rotate(float(frame)/10)},"transform":Model.Clips.transform(peer_base),"interpolation":"ease"})
			var old_piece:=Model.Clips.clip(peer_base,0,5,0,legacy_keys)
			var legacy_actor:=Model.new();legacy_actor.data=peer_base.duplicate(true);legacy_actor.data.pose_keys=legacy_keys
			app.clip_editor.clipboard={"sha256":peer.data.sha256,"fps_num":24,"fps_den":1,"piece":old_piece}
			app.clip_editor.request("paste",peer_id,"",15);peer=app.renderer.world_runtime.instance(peer_id)
			print("LEGACY_BODY_CLIPBOARD "+JSON.stringify({"error":Model.validate(peer.data,48),"frames":Body.B.frames(Body.view(peer.data),left),"actual":peer.sample(19).get(left,Model.identity()),"expected":legacy_actor.sample(4)[left]}))
			check(Model.validate(peer.data,48).is_empty() and Body.B.frames(Body.view(peer.data),left).has(19) and same(peer.sample(19).get(left,Model.identity()),legacy_actor.sample(4)[left]),"legacy snapshot clipboard remains editable when pasted onto model6")
			app.restore_world(original_world);app.world_selection.select_entity(id,false);actor=app.renderer.world_runtime.instance(id)
			Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
		for mode in ["packed","linked"]:
			var path:=folder.path_join(plan.label+"-"+mode+".has");app.has_project.save_file(path,mode);await wait_job(app.has_project)
			app.new_project();app.has_project.open_file(path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id);app.set_frame(6);await settled()
			check(actor!=null and actor.data.format==Model.BODY_FORMAT and same(actor.sample(6),Body.sample(keyed,6).pose) and actor.order==native_ids,"normal "+mode+" HAS retains editable native body controls: "+plan.label)
		if plan.label=="Authored":
			app.changed();app.autosave_tick(true);var checkpoint: String=app.recovery_root.path_join(app.recovery_session);app.new_project()
			check(app.restore_checkpoint({"folder":checkpoint}),"normal recovery accepts the complete model6 project")
			actor=app.renderer.world_runtime.instance(id);app.set_frame(6);await settled();var expected: Image=await app.renderer.capture(app.keys,app.layers,6,true);expected.save_png(folder.path_join("independent-body.png"))
			var error: String=await app.export_movie(folder);movie=app.last_export_folder.path_join("movie.mp4")
			check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000007.png")).get_data()==expected.get_data(),"normal final export directly samples independent controls with exact preview and drawing")
		metrics[plan.label]={"warm_pose_root_usec":average,"parts":native_ids.size(),"source_sha256":source_hash}
	var result:={"checks":checks,"failures":failures,"metrics":metrics,"movie":movie,"normal_editor_integration":true}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("BODY_ANIMATION "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)

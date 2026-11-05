extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
var app
var folder: String
var empty: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Contact transform watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func actor(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func peak() -> float:
	var rig:=actor("child");var segment:=Contacts.active(rig.data.animation_clips,app.frame);var error:=0.
	for foot in segment.get("feet",[]):error=maxf(error,rig.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position)))
	return error
func setup(plan: Dictionary) -> Dictionary:
	app.new_project();var group:=World.object(empty,"group","Outer group");group.id="group";group.position=[2,0,-1];group.scale=1.2;var q:=Quaternion(Vector3.UP,.2);group.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var middle:=World.object(empty,"group","Inner group");middle.id="middle";middle.parent_id=group.id;middle.position=[1,0,0]
	var child:=World.object(plan.source,"model",plan.name);child.id="child";child.parent_id=middle.id;child.metadata=plan.metadata.duplicate(true)
	# Retain the supplied standard-model baseline, including Scout's saved root
	# orientation. Recreating geometry with an identity root can lay a native rig
	# sideways and make a world-down crouch consume rather than add reach.
	var baseline: Dictionary=plan.get("body_base_transform",plan);child.rotation_xyzw=baseline.rotation_xyzw.duplicate();child.scale=baseline.scale
	var peer:=World.object(plan.source,"model","Unrelated peer");peer.id="peer";peer.position=[-3,0,0];peer.metadata=plan.metadata.duplicate(true)
	peer.rotation_xyzw=child.rotation_xyzw.duplicate();peer.scale=child.scale
	var world:=World.empty();world.objects=[child,peer,middle,group];app.restore_world(world);app.set_frame(0);var rig:=actor(child.id);var legs: Array=rig.contact_legs();var length: float=rig.bone_transform(legs[0].ids[0]).origin.distance_to(rig.bone_transform(legs[0].ids[2]).origin)/1.2
	for at in [0,24]:
		var transform:=Model.Clips.transform(rig.data);transform.position[1]=0. if at==0 else -length*.12
		rig.put_pose_key({"frame":at,"pose":{},"transform":transform,"authored_channels":["@root"],"interpolation":"ease"},48,false,rig.data.duplicate(true))
	app.set_frame(0);var track:=Contacts.capture(rig,0,49,"transform-pin");var knee: Vector3=rig.bone_transform(track.segments[0].feet[0].ids[0]).origin+Vector3(0,0,-.4);track.segments[0].feet[0]["pole"]=[knee.x,knee.y,knee.z];track=Contacts.track(track.segments)
	var planted:=Ranges.edit(rig.data,0,49,track.segments[0],48);app.renderer.world_runtime.restore_instance(child.id,planted.data);app.set_frame(12);app.world_selection.select_entity(group.id);app.set_advanced(true)
	return rig.data.duplicate(true)
func rotate_by(degrees: float) -> void:
	var editor=app.pose_editor;editor.selected="@root";editor.operation.select(0);editor.refresh_values();editor.fields[1].value+=degrees;editor.apply_numeric()
func scale_to(value: float) -> void:app.pose_editor.scale_field.value=value;app.pose_editor.scale_apply.pressed.emit()
func ring_point(editor,index: int) -> Vector2:
	var points: Array=editor.handles[index].points;var best:=Vector2(-10000,-10000);var margin:=-1.
	for i in range(points.size()-1):
		var point: Vector2=points[i].lerp(points[i+1],.4);var distance:=INF
		for other in range(editor.handles.size()):
			if other==index:continue
			var curve: Array=editor.handles[other].points
			for j in range(curve.size()-1):distance=minf(distance,point.distance_to(Geometry2D.get_closest_point_to_segment(point,curve[j],curve[j+1])))
		if distance>margin:margin=distance;best=point
	return best
func case_for(plan: Dictionary) -> Dictionary:
	var first_check:=checks;var first_failure:=failures;var child:=setup(plan);var peer: Dictionary=actor("peer").data.duplicate(true);var original: Dictionary=actor("group").data.duplicate(true);var shots: Array=app.keys.duplicate(true);var history: int=app.history.size();var editor=app.pose_editor
	rotate_by(2);await settled();var rotated: Dictionary=actor("group").data.duplicate(true);var diagnostics:={"rotation":{"status":app.status.text,"changed":rotated!=original,"history_delta":app.history.size()-history,"peak":peak()}}
	check(rotated!=original and app.history.size()==history+1 and peak()<.0002,"ancestor numeric rotation keys once while native feet stay planted: "+plan.name)
	check(actor("child").data==child and actor("peer").data==peer and app.keys==shots,"ancestor rotation preserves child controls/poles, peers and explicit shot keys: "+plan.name)
	app.undo();check(actor("group").data==original,"rotation Undo restores exact ancestor: "+plan.name);app.redo();check(actor("group").data==rotated,"rotation Redo restores exact ancestor: "+plan.name)
	history=app.history.size();scale_to(1.21);await settled();var scaled: Dictionary=actor("group").data.duplicate(true);diagnostics["scale"]={"status":app.status.text,"changed":scaled!=rotated,"history_delta":app.history.size()-history,"peak":peak()}
	check(scaled!=rotated and app.history.size()==history+1 and peak()<.0002 and actor("child").data==child,"ancestor uniform scale keys once without baking native child controls: "+plan.name)
	app.undo();check(actor("group").data==rotated,"scale Undo restores exact ancestor: "+plan.name);app.redo();check(actor("group").data==scaled,"scale Redo restores exact ancestor: "+plan.name)
	history=app.history.size();scale_to(.001)
	check(actor("group").data==scaled and app.history.size()==history and app.status.text.contains(plan.name),"unreachable scale refuses before changing native child or history: "+plan.name)
	rotate_by(90)
	check(actor("group").data==scaled and actor("child").data==child and app.history.size()==history and app.status.text.contains(plan.name),"unreachable ancestor rotation refuses atomically with native name: "+plan.name)
	app.set_frame(12);app.world_selection.frame_selected();await settled();editor.operation.select(0);editor.space.select(1);editor.update_gizmo();var point:=ring_point(editor,1);var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;editor.input(press,point)
	check(editor.dragging and absf(editor.drag_axis.normalized().dot(Vector3.UP))>.99,"actual world-axis ancestor rotation ring begins its intended drag: "+plan.name)
	var authored: Dictionary=actor("child").sample(12);var motion:=InputEventMouseMotion.new();editor.input(motion,point+Vector2(1,-1)*deg_to_rad(1)/.02);var preview: Dictionary=actor("group").data.duplicate(true)
	diagnostics["preview"]={"status":app.status.text,"changed":preview!=scaled,"peak":peak(),"authored_exact":actor("child").sample(12)==authored}
	check(preview!=scaled and peak()<.0002 and actor("child").sample(12)==authored and app.status.text.contains("held"),"rotation preview holds feet with current feedback while read-only sampling retains authored ancestors: "+plan.name)
	editor.input(motion,point+Vector2(1,-1)*deg_to_rad(90)/.02)
	check(actor("group").data==preview and peak()<.0002,"unreachable rotation drag keeps last valid native preview: "+plan.name)
	editor.input(motion,point+Vector2(1,-1)*deg_to_rad(1)/.02)
	check(actor("group").data==preview and peak()<.0002 and app.status.text.contains("held") and not app.status.text.contains("out of reach"),"returning to valid rotation clears stale reach feedback: "+plan.name)
	editor.finish_drag(true);check(actor("group").data==scaled and app.history.size()==history,"Escape restores exact pre-drag ancestor without history: "+plan.name)
	editor.update_gizmo();point=ring_point(editor,1);press.pressed=true;editor.input(press,point);editor.input(motion,point+Vector2(1,-1)*deg_to_rad(1)/.02);press.pressed=false;editor.input(press,point+Vector2(1,-1)*deg_to_rad(1)/.02)
	var released: Dictionary=actor("group").data.duplicate(true)
	check(released!=scaled and app.history.size()==history+1 and peak()<.0002 and actor("child").data==child,"releasing a valid ancestor rotation commits one key/Undo without baking the native child: "+plan.name)
	app.undo();check(actor("group").data==scaled,"rotation gesture Undo restores its exact original key: "+plan.name)
	app.redo();check(actor("group").data==released,"rotation gesture Redo restores the committed key exactly: "+plan.name);app.undo()
	var stable:=true
	for at in range(49):actor("child").sample(at);stable=stable and actor("child").evaluation_error.is_empty()
	check(stable and actor("child").data==child and actor("peer").data==peer,"all49 frames remain reachable after ancestor rotation/scale: "+plan.name)
	# Model scale remains a root operation even with a planted leg selected.
	app.set_frame(12);app.world_selection.select_entity("child");editor.selected=Contacts.active(child.animation_clips,12).feet[0].ids[2];editor.refresh_values();history=app.history.size();scale_to(1.002)
	check(actor("child").data!=child and app.history.size()==history+1 and peak()<.0002,"Apply model scale works with a planted foot selected and preserves its target: "+plan.name)
	app.undo();check(actor("child").data==child,"root scale Undo restores exact native contact/body data: "+plan.name)
	var saved_world: Dictionary=app.current_world()
	# Pending startup must survive a deferral rather than being silently consumed.
	setup(plan);var before: Dictionary=app.current_world();history=app.history.size();app.physics_editor.queue_import_start("child",true,false);var ticket: Dictionary=app.physics_editor.import_starts.duplicate(true);var generation: int=app.physics_editor.generation;scale_to(1.21)
	check(app.current_world()==before and app.history.size()==history and app.physics_editor.import_starts==ticket and app.physics_editor.generation==generation and app.status.text.contains("off"),"ancestor scale defers pending native physics without consuming its ticket: "+plan.name);app.physics_editor.clear()
	setup(plan);app.world_selection.select_entity("child");app.physics_editor.change(true);await settled();var physics=app.physics_editor;var simulation: RefCounted=physics.simulations.get("child");check(simulation!=null,"actual native body simulation starts for scale lifecycle: "+plan.name)
	app.world_selection.select_entity("group");before=app.current_world();history=app.history.size();generation=physics.generation;scale_to(1.21)
	check(physics.body_active("child") and physics.simulations.get("child")==simulation and app.current_world()==before and app.history.size()==history and physics.generation==generation,"ancestor scale defers live native physics without freezing or changing contacts: "+plan.name);physics.clear()
	setup(plan);app.world_selection.select_entity("child");physics.change(true);await settled();check(physics.recording.start(),"actual Local recording begins before ancestor scale: "+plan.name)
	app.world_selection.select_entity("group");before=app.current_world();history=app.history.size();scale_to(1.21)
	check(physics.recording.active and physics.body_active("child") and app.current_world()==before and app.history.size()==history,"ancestor scale cannot silently finish a live native recording: "+plan.name)
	if physics.recording.active:physics.recording.cancel("Test recording discarded.",false)
	physics.clear();app.restore_world(saved_world);app.set_frame(12)
	return {"name":plan.name,"bones":actor("child").order.size(),"checks":checks-first_check,"failures":failures-first_failure,"peak_error":peak(),"diagnostics":diagnostics}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];DirAccess.make_dir_recursive_absolute(folder);empty=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty);app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1]);await job();var plans:=[];var hashes:={}
	for row in app.current_world().objects:
		if row.get("format")==Model.CONTACT_FORMAT:plans.append(row);hashes[row.source]=FileAccess.get_sha256(row.source)
	check(plans.size()==5,"five prepared native rigs available for nested rotation/scale acceptance")
	if plans.size()!=5:app.free();quit(1);return
	var reports:=[]
	for plan in plans:reports.append(await case_for(plan))
	app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(130,40),8,Color.CYAN,false);app.changed();app.set_frame(12);app.world_selection.select_entity("child");app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var expected: Dictionary=actor("child").sample(12);var path:=folder.path_join("rotated-scaled-contacts.has");app.has_project.save_file(path,"packed");await job();app.new_project();app.has_project.open_file(path);await job();app.set_frame(12)
	check(actor("child").sample(12)==expected and peak()<.0002,"packed HAS reopens exact native pose under rotated/scaled nested ancestors")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);reference.save_png(folder.path_join("transform-frame.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"nested transforms and editable cyan paint match own preview/MP4 pixels")
	var unchanged:=true
	for source in hashes:unchanged=unchanged and FileAccess.get_sha256(source)==hashes[source]
	check(unchanged,"all original prepared native source bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"native_reports":reports,"movie":app.last_export_folder.path_join("movie.mp4"),"project":path};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_TRANSFORM "+JSON.stringify(result));quit(0 if failures==0 else 1)

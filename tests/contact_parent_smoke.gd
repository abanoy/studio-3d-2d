extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
const T=Model.Timeline
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Contact parent watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func actor(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func plant(id: String) -> Dictionary:
	app.set_frame(0);var rig:=actor(id);var capture:=Contacts.capture(rig,0,1,"parent-pin")
	var result:=Ranges.edit(rig.data,0,49,capture.segments[0],48)
	check(not result.has("error"),"parented feet capture into the shared format")
	app.renderer.world_runtime.restore_instance(id,result.data);app.set_frame(0);return result.data
func error_at(id: String) -> float:
	var rig:=actor(id);var segment:=Contacts.active(rig.data.animation_clips,app.frame);var error:=0.
	for foot in segment.feet:error=maxf(error,rig.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	return error
func numeric(y: float) -> void:
	app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[1].value=y;app.pose_editor.apply_numeric()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	var empty:=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var group:=World.object(empty,"group","Moving group");group.id="group"
	var middle:=World.object(empty,"group","Nested group");middle.id="middle";middle.parent_id=group.id
	var child:=World.object(asset);child.id="planted-child";child.name="Planted child";child.parent_id=middle.id
	var peer:=World.object(asset);peer.id="peer";peer.position=[4,0,0]
	var world:=World.empty();world.objects=[child,peer,middle,group]
	check(app.restore_world(world).is_empty(),"child-before-parent nested groups install")
	var child_before:=plant(child.id);var peer_before: Dictionary=actor(peer.id).data.duplicate(true);var original: Dictionary=actor(group.id).data.duplicate(true)
	app.set_frame(12);app.world_selection.select_entity(group.id);var editor=app.pose_editor;var shots: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var history: int=app.history.size()
	numeric(-.03);await settled();var valid: Dictionary=actor(group.id).data.duplicate(true)
	check(valid!=original and app.history.size()==history+1 and error_at(child.id)<.0002,"valid ancestor numeric Move keys once while both descendant feet remain planted")
	check(actor(child.id).data==child_before and actor(peer.id).data==peer_before and app.keys==shots and app.renderer.view_state()==view,"parent correction does not bake child keys or alter peer, shot or view")
	app.undo();check(actor(group.id).data==original,"parent correction Undo restores exact ancestor data")
	app.redo();check(actor(group.id).data==valid,"parent correction Redo retains fixed world contacts")
	history=app.history.size();numeric(10.)
	check(actor(group.id).data==valid and app.history.size()==history and app.status.text.contains("Planted child"),"unreachable ancestor numeric Move refuses atomically with the affected child's name")
	app.renderer.world_runtime.restore_instance(group.id,valid);app.set_frame(12);editor.frame_model();await settled();editor.operation.select(1);editor.update_gizmo()
	var handle: Dictionary=editor.handles[1];var point: Vector2=handle.points[0].lerp(handle.points[-1],.7);var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;editor.input(press,point)
	check(editor.dragging,"real ancestor Move handle begins a drag")
	var baseline: Dictionary=actor(child.id).sample(12);var motion:=InputEventMouseMotion.new()
	editor.input(motion,point+editor.drag_screen_axis.normalized()*(-.02)/editor.drag_units*editor.drag_pixels)
	var preview: Dictionary=actor(group.id).data.duplicate(true)
	check(error_at(child.id)<.0002,"descendant contacts evaluate the actual ancestor draft during a valid drag preview")
	check(actor(child.id).sample(12)==baseline,"read-only authored samples remain independent of the displayed ancestor draft")
	editor.input(motion,point+editor.drag_screen_axis.normalized()*10./editor.drag_units*editor.drag_pixels)
	check(actor(group.id).data==preview and error_at(child.id)<.0002,"invalid ancestor drag keeps its last valid preview and both pinned feet")
	editor.finish_drag(true);check(actor(group.id).data==valid,"Escape restores the exact ancestor baseline")
	app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(preload("res://src/drawing.gd").edit_image(app.layers[1].cels[0]).image,Vector2(30,50),Vector2(140,50),8,Color.CYAN,false);app.changed()
	app.set_frame(12);app.world_selection.select_entity(child.id);editor.frame_model();app.keys=[T.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var expected: Dictionary=actor(child.id).sample(12);var has_path:=folder.path_join("parented-contacts.has");app.has_project.save_file(has_path,"packed")
	while app.has_project.pid>0:await process_frame
	app.new_project();app.has_project.open_file(has_path)
	while app.has_project.pid>0:await process_frame
	app.set_frame(12);check(actor(child.id).sample(12)==expected and error_at(child.id)<.0002,"actual packed HAS reopens parent corrections with exact resolved child pose")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);reference.save_png(folder.path_join("parented-frame.png"));var export_error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(export_error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"parented contacts and independent paint match reopened preview and actual MP4 frames")
	# A harmless current root key can change future easing against inverse child motion.
	app.new_project();group=World.object(empty,"group","Animated group");group.id="animated-group";child=World.object(asset);child.id="animated-child";child.name="Animated child";child.parent_id=group.id
	var parent_model:=Model.new();parent_model.data=group;var child_model:=Model.new();child_model.data=child
	for at in [0,24]:
		var a: Dictionary=Model.identity();a["scale"]=1.;a.position[0]=0. if at==0 else 10.;var b:=a.duplicate(true);b.position[0]=-a.position[0]
		parent_model.put_pose_key({"frame":at,"pose":{},"transform":a,"authored_channels":["@root"],"interpolation":"ease"},48,false,parent_model.data.duplicate(true))
		child_model.put_pose_key({"frame":at,"pose":{},"transform":b,"authored_channels":["@root"],"interpolation":"ease"},48,false,child_model.data.duplicate(true))
	world=World.empty();world.objects=[child_model.data,parent_model.data];app.restore_world(world);child_before=plant(child.id);app.set_frame(12);app.world_selection.select_entity(group.id);history=app.history.size();original=actor(group.id).data.duplicate(true)
	numeric(-.01)
	check(actor(group.id).data==original and app.history.size()==history and app.status.text.contains("Frame"),"ancestor auto-key refuses when changed easing would break a future descendant contact")
	app.retime_object(group.id,4,original)
	check(actor(group.id).data==original and actor(child.id).data==child_before and app.history.size()==history and app.status.text.contains("Animated child"),"whole-group timing refuses unreachable descendant contacts without changing either record")
	app.clip_editor.move_piece(group.id,original.animation_clips[0].id,4,original)
	check(actor(group.id).data==original and app.history.size()==history and app.status.text.contains("Frame"),"ancestor animation-block movement validates descendant contacts before history")
	check(actor(child.id).evaluation_error.is_empty(),"refused timing validation restores the child's previous preview error state")
	check(FileAccess.get_sha256(asset)==sha,"original model bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_PARENT "+JSON.stringify(result));quit(0 if failures==0 else 1)

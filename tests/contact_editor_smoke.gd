extends SceneTree
const Model=preload("res://src/model.gd")
const Ranges=preload("res://src/contact_ranges.gd")
var app
var editor
var dialog
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Contact editor watchdog");quit(2));call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func active(data: Dictionary,frame: int) -> bool:return not Ranges.Contact.Contacts.active(data.get("animation_clips",[]),frame).is_empty()
func root_value(y: float) -> Dictionary:return {"position":[0,y,0],"rotation_xyzw":[0,0,0,1],"scale":1.}
func choose_range(first: int,last: int) -> void:
	app.set_frame(first);dialog.control.pressed.emit();await settled();dialog.end_frame.value=last
func current() -> RefCounted:return app.renderer.active_model()
func numeric(amount: float) -> void:
	editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[1].value+=amount;editor.apply_numeric()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	editor=app.pose_editor;dialog=editor.contacts;editor.add_model(asset)
	for frame in [0,24]:
		var rig:=current();var before: Dictionary=rig.data.duplicate(true)
		rig.put_pose_key({"frame":frame,"pose":{},"transform":root_value(0. if frame==0 else -.15),"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
	var original: Dictionary=current().data.duplicate(true);var poses:=[]
	for half in range(97):poses.append([current().sample_body(float(half)/2),current().sample_transform(float(half)/2)])
	var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	await choose_range(6,18)
	check(not app.advanced_mode and dialog.window.visible and dialog.control.is_visible_in_tree(),"Simple control opens the real range window")
	check(current().data==original and app.history.size()==history,"opening the range window authors nothing")
	dialog.plant_button.pressed.emit();await settled()
	var planted: Dictionary=current().data.duplicate(true)
	check(not dialog.window.visible and planted.format==Model.CONTACT_FORMAT and app.history.size()==history+1,"Plant creates one versioned undoable range through actual button")
	check(not active(planted,5) and active(planted,6) and active(planted,18) and not active(planted,19) and not active(planted,48),"inclusive range has exact introduction and release boundaries")
	var exact:=true
	for half in range(97):exact=exact and current().sample_body(float(half)/2)==poses[half][0] and current().sample_transform(float(half)/2)==poses[half][1]
	check(exact and app.keys==shots,"contact range splits preserve every half-frame body curve and shot key")
	app.undo();check(current().data==original,"Undo restores complete pre-contact model6 data")
	app.redo();check(current().data==planted,"Redo restores exact contact data")
	await choose_range(10,12);dialog.release_button.pressed.emit();await settled()
	var released: Dictionary=current().data.duplicate(true)
	check(active(released,9) and not active(released,10) and not active(released,12) and active(released,13) and active(released,18),"Release edits only the requested interval, preserving pins on both sides")
	history=app.history.size();await choose_range(10,12);dialog.release_button.pressed.emit()
	check(app.history.size()==history and current().data==released and dialog.window.visible,"already released range is an honest no-op")
	app.set_frame(20);dialog.plant_button.pressed.emit()
	check(app.history.size()==history and current().data==released and dialog.note.text.contains("changed"),"stale playhead cannot install an old range")
	dialog.window.hide();app.undo();check(current().data==planted,"range release has one complete Undo")
	# Gaps and held tails receive contact-only pieces without body/expression keys.
	var split: Dictionary=Model.Clips.split(original,12).data
	var moved: Dictionary=Model.Clips.move(split,split.animation_clips[1].id,28,48).data
	var target: Dictionary=planted.animation_clips[1].foot_contacts.segments[0].duplicate(true);target.id="gap-contact"
	var changed:=Ranges.edit(moved,6,36,target,48)
	check(not changed.has("error") and active(changed.data,20) and active(changed.data,35) and not active(changed.data,36),"one declared pin bridges distinct source slices and releases at a gap boundary")
	var a:=Model.new();a.data=moved;var b:=Model.new();b.data=changed.data;exact=true
	for half in range(97):exact=exact and a.sample_body(float(half)/2)==b.sample_body(float(half)/2) and a.sample_transform(float(half)/2)==b.sample_transform(float(half)/2)
	check(exact,"contact-only gap pieces preserve original connecting body interpolation exactly")
	changed=Ranges.edit(original,30,41,target,48)
	check(not changed.has("error") and active(changed.data,40) and not active(changed.data,41) and not active(changed.data,48),"a contact in the held tail releases without extending motion or presence")
	# Valid manual root edits remain independent keys; invalid ones cannot author a broken pin.
	await choose_range(0,48);dialog.plant_button.pressed.emit();await settled();app.set_frame(12)
	var before: Dictionary=current().data.duplicate(true);history=app.history.size();numeric(-.03);await settled()
	check(app.history.size()==history+1 and current().evaluation_error.is_empty() and active(current().data,12),"ordinary numeric body Move keeps the contact and auto-keys once")
	var body=Model.body_animation();var parts: Array=body.B.known_channels(body.view(current().data))
	check(parts==["@root"],"manual root edit does not bake solved leg controls into body keys")
	app.undo();check(current().data==before,"manual root correction Undo retains original contacts")
	history=app.history.size();numeric(10.)
	check(current().data==before and app.history.size()==history and app.status.text.contains("release"),"unreachable numeric Move preserves full data and history with useful guidance")
	var segment: Dictionary=Ranges.Contact.Contacts.active(before.animation_clips,12);editor.selected=segment.feet[0].ids[2];history=app.history.size();editor.operation.select(1);editor.refresh_values();editor.fields[0].value+=.1;editor.apply_numeric()
	check(current().data==before and app.history.size()==history and app.status.text.contains("Release"),"planted leg edits explain release instead of silently recording ineffective keys")
	editor.selected="@root";editor.frame_model();await settled();editor.operation.select(1);editor.update_gizmo()
	var handle: Dictionary=editor.handles[1];var point: Vector2=handle.points[0].lerp(handle.points[-1],.7);var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;editor.input(press,point)
	check(editor.dragging,"actual root gizmo begins under a persistent contact")
	var motion:=InputEventMouseMotion.new();editor.input(motion,point+editor.drag_screen_axis.normalized()*(-.02)/editor.drag_units*editor.drag_pixels)
	var valid: Dictionary=current().data.duplicate(true)
	editor.input(motion,point+editor.drag_screen_axis.normalized()*10./editor.drag_units*editor.drag_pixels)
	check(current().data==valid and current().evaluation_error.is_empty(),"unreachable drag preview preserves the last valid pose, not a half solve")
	editor.finish_drag(true);check(current().data==before,"Escape restores exact pre-drag authored state")
	# Real UI rejects an existing unreachable future pose atomically.
	var bad: Dictionary=before.duplicate(true)
	for piece in bad.animation_clips:piece.erase("foot_contacts")
	for piece in bad.animation_clips:
		for key in piece.body_controls.get("@root",[]):
			if key.frame==24:key.value.position[1]=10.
	editor.restore_state(bad,false);app.set_frame(0);history=app.history.size();before=current().data.duplicate(true);await choose_range(0,48);dialog.plant_button.pressed.emit()
	check(current().data==before and app.history.size()==history and dialog.window.visible and dialog.note.text.contains("Frame"),"range validation refuses an unreachable future pose without partial data or Undo")
	dialog.window.hide();editor.restore_state(planted,false);app.set_frame(12);await settled();var scene: Image=app.renderer.viewport.get_texture().get_image();scene.save_png(folder.path_join("planted-ui.png"))
	await choose_range(12,18);await settled();dialog.window.get_texture().get_image().save_png(folder.path_join("range-window.png"))
	check(dialog.window.size.x<=root.size.x and dialog.window.size.y<=root.size.y,"range window fits the actual application")
	dialog.window.hide();var bad_pin: Dictionary=current().data.duplicate(true)
	for piece in bad_pin.animation_clips:
		for pin in piece.get("foot_contacts",{}).get("segments",[]):pin.feet[1].position=[99999,99999,99999]
	editor.restore_state(bad_pin,false);app.set_frame(12)
	check(editor.info.text.contains("reach"),"an unreachable loaded contact has clear inspector feedback")
	await choose_range(12,18);history=app.history.size();dialog.release_button.pressed.emit();await settled()
	check(current().evaluation_error.is_empty() and app.history.size()==history+1 and not active(current().data,12) and active(current().data,11),"Release repairs an invalid current range while preserving earlier contact ownership")
	editor.restore_state(planted,false);app.set_frame(12)
	app.physics_editor.queue_import_start(current().data.id,true,false)
	before=current().data.duplicate(true);history=app.history.size();dialog.control.pressed.emit()
	check(not dialog.window.visible and app.physics_editor.import_starts.has(current().data.id) and current().data==before and app.history.size()==history,"pending real import physics defers contacts without cancelling its start ticket")
	app.physics_editor.clear();editor.apply_frame()
	before=current().data.duplicate(true);editor.auto_key.button_pressed=false;numeric(-.01);history=app.history.size();var draft: Dictionary=current().data.duplicate(true)
	await choose_range(12,18);dialog.plant_button.pressed.emit()
	check(current().data==draft and app.history.size()==history and dialog.note.text.contains("draft"),"an unrecorded animated draft receives guidance without becoming hidden body motion")
	dialog.window.hide();editor.restore_state(before,false);editor.auto_key.button_pressed=true
	app.physics_editor.toggle.button_pressed=true
	while app.physics_editor.pending.size()>0:await process_frame
	check(app.physics_editor.is_running(),"actual body Physics starts for the live-state guard")
	dialog.control.pressed.emit()
	check(not dialog.window.visible and app.physics_editor.is_running() and app.status.text.contains("off"),"opening contacts refuses live Physics without stopping or recording it")
	app.physics_editor.clear();editor.apply_frame()
	# The UI-authored record survives actual HAS worker save/open, with editable paint.
	app.mode.select(0);app.change_mode(0);app.create_cel(false)
	var drawing=preload("res://src/drawing.gd");var cel: Dictionary=drawing.cel_at(app.layers[1],app.frame)
	var editable: Dictionary=drawing.edit_image(cel)
	check(not editable.has("error"),"ordinary cel exposes editable pixels through its raster owner")
	if editable.has("error"):app.free();quit(1);return
	var paint: Image=editable.image
	drawing.stroke(paint,Vector2(80,70),Vector2(170,70),4,Color.CYAN,false);app.changed();var pixels: PackedByteArray=paint.get_data()
	var saved:=folder.path_join("ui-contacts.has");app.has_project.save_file(saved,"packed")
	while app.has_project.pid>0:await process_frame
	var id: String=current().data.id;app.new_project();app.has_project.open_file(saved)
	while app.has_project.pid>0:await process_frame
	app.world_selection.select_entity(id);app.set_frame(12)
	var reopened_paint: Image=drawing.image(drawing.cel_at(app.layers[1],12))
	check(current().data.format==Model.CONTACT_FORMAT and active(current().data,12) and reopened_paint!=null and reopened_paint.get_data()==pixels,"real UI contact range reopens with independent editable drawing")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,12,true);var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==preview.get_data(),"UI-authored contact range and paint match actual movie frames exactly")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.new_project();check(not dialog.window.visible and FileAccess.get_sha256(asset)==sha,"New clears stale range context and original asset stays unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_EDITOR "+JSON.stringify(result));quit(0 if failures==0 else 1)

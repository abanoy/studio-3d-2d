extends Node
# Static parts own independent poses/morphs/solvers. This dialog edits visibility only.
const Parts=preload("res://src/character_parts.gd")
const SceneIO=preload("res://src/scene3d.gd")
var app
var dialog: AcceptDialog
var switches: Dictionary={}
var opened_world: Dictionary={}
var opened_frame:=-1
var opened_session:=""
var opened_owner:=""
var opened_video: Dictionary={}
var root_id:=""
var info: Label
var preset_buttons: Dictionary={}

func foreign_dialog(node: Node) -> bool:
	for child in node.get_children():
		if child==dialog:continue
		if child is Window and child.get_flag(Window.FLAG_NO_FOCUS) and child.get_flag(Window.FLAG_MOUSE_PASSTHROUGH):continue
		if child is Window and child.visible and (child.exclusive or child is Popup):return true
		if foreign_dialog(child):return true
	return false

func ready_to_edit() -> bool:
	if not is_instance_valid(app) or app.exporting or app.playing or app.navigating or app.drawing:return false
	if foreign_dialog(app):return false
	if app.pose_editor.dragging or app.physics_editor.grabbing() or app.physics_editor.is_running():return false
	if not app.physics_editor.pending.is_empty() or not app.physics_editor.import_starts.is_empty() or app.physics_editor.recording.active:return false
	if app.camera_key_editor.active() or app.camera_transform_editor.has_draft():return false
	if app.timeline.cel_gesture_active() or app.timeline.audio_gesture_active():return false
	if app.source_import.pid>0 or app.has_project.pid>0 or app.height_review and app.height_review.pending:return false
	return true

func can_manage(selected: String) -> bool:
	return is_instance_valid(app) and app.renderer.world_runtime!=null and not Parts.describe(app.current_world(),selected,int(app.video.duration_frames)).has("error")

func open(selected: String) -> void:
	if not ready_to_edit():app.message("Finish the current edit and stop live physics before managing parts.");return
	var bundle: Dictionary=Parts.describe(app.current_world(),selected,int(app.video.duration_frames))
	if bundle.has("error"):app.message(bundle.error);return
	if is_instance_valid(dialog):dialog.hide();dialog.queue_free()
	opened_world=app.current_world().duplicate(true);opened_frame=app.frame;opened_session=app.recovery_session;opened_owner=app.sequence_editor.active_owner;opened_video=app.video.duplicate(true);root_id=bundle.root_id;switches.clear();preset_buttons.clear()
	dialog=AcceptDialog.new();dialog.title="Parts — "+str(bundle.name);dialog.exclusive=true;dialog.min_size=Vector2i(380,320)
	app.add_child(dialog);dialog.get_ok_button().hide()
	var box:=VBoxContainer.new();dialog.add_child(box)
	info=Label.new();info.text="Show or hide parts at frame %d. Clothes buttons choose one part; checkboxes can layer them." % opened_frame;info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;box.add_child(info)
	for part in bundle.parts:
		var control:=CheckBox.new();control.text=str(part.row.name)+" ("+str(part.role)+")"
		control.button_pressed=Parts.Visibility.target(part.row,opened_frame);box.add_child(control);switches[part.row.id]=control
	var outfit:=HBoxContainer.new();box.add_child(outfit)
	for role in ["dress","skirt","miniskirt"]:
		var button:=Button.new();button.text=role.capitalize()+" only";outfit.add_child(button);preset_buttons[role]=button
		button.pressed.connect(func():choose_outfit(role))
	var none:=Button.new();none.text="No clothes parts";outfit.add_child(none);none.pressed.connect(func():choose_outfit(""))
	var apply:=Button.new();apply.text="Apply visibility at this frame";box.add_child(apply);apply.pressed.connect(apply_visibility)
	var close:=Button.new();close.text="Close";box.add_child(close);close.pressed.connect(dialog.hide)
	dialog.popup_centered(Vector2i(520,420))

func choose_outfit(role: String) -> void:
	if app.recovery_session!=opened_session or app.sequence_editor.active_owner!=opened_owner:return
	var bundle: Dictionary=Parts.describe(opened_world,root_id,int(app.video.duration_frames))
	if bundle.has("error"):return
	for part in bundle.parts:
		if part.role in Parts.OUTFITS:switches[part.row.id].button_pressed=part.role==role

func apply_visibility() -> void:
	if not ready_to_edit() or app.frame!=opened_frame or app.recovery_session!=opened_session or app.sequence_editor.active_owner!=opened_owner or app.video!=opened_video or app.current_world()!=opened_world:
		info.text="The scene or frame changed. Reopen Parts before applying.";return
	var values:={}
	for id in switches:values[id]=switches[id].button_pressed
	var edit: Dictionary=Parts.visibility_edit(opened_world,root_id,values,opened_frame,int(app.video.duration_frames))
	if edit.has("error"):info.text=edit.error;return
	if edit.after.is_empty():info.text="Those visibility states are already set.";return
	var why: String=app.renderer.world_runtime.restore_instances(edit.after)
	if not why.is_empty():info.text=why;return
	app.push_history(edit);app.set_frame(app.frame);app.changed();app.refresh_timeline()
	opened_world=app.current_world().duplicate(true)
	info.text="Visibility saved at frame %d. Undo restores this whole change." % opened_frame

func inert_group_error(path: String, checksum: String="") -> String:
	var input:=FileAccess.open(path,FileAccess.READ)
	if input==null or input.get_length()>128*1024*1024:return "Cannot read the bounded empty group asset."
	input.close()
	var wanted: String=FileAccess.get_sha256(path) if checksum.is_empty() else checksum
	if wanted.length()!=64 or FileAccess.get_sha256(path)!=wanted:return "The empty group asset checksum changed."
	var decoded: Dictionary=SceneIO.load_glb(path)
	if decoded.has("error"):return decoded.error
	var pending: Array=[decoded.scene];var why:=""
	while not pending.is_empty():
		var node: Node=pending.pop_back()
		if node.get_class()!="Node3D" or node.get_script()!=null:why="The character root must contain only plain empty 3D nodes.";break
		if (node as Node3D).transform!=Transform3D.IDENTITY:why="The empty group asset must have identity transforms; source units and placement belong outside it.";break
		pending.append_array(node.get_children())
	decoded.scene.free()
	if FileAccess.get_sha256(path)!=wanted:return "The empty group asset changed while it was inspected."
	return why

func install_bundle(group: Dictionary, supplied: Dictionary, policy: Dictionary, root_scale=1.) -> String:
	# Host entrypoint for an explicit reviewed prepare-all import transaction.
	# It is not folder discovery, an MDL converter or proof of actual alignment.
	if not ready_to_edit():return "Finish the current edit and stop live physics first."
	if is_instance_valid(dialog) and dialog.visible:return "Close Parts before installing another bundle."
	var why: String=inert_group_error(str(group.get("source","")),str(group.get("sha256","")))
	if not why.is_empty():return why
	var before: Dictionary=app.current_world().duplicate(true)
	var proposed: Dictionary=Parts.assemble(before,group,supplied,policy,int(app.video.duration_frames),root_scale)
	if proposed.has("error"):return proposed.error
	why=app.restore_world(proposed.world)
	if not why.is_empty():return why
	app.push_history({"type":"world","before":before,"after":proposed.world.duplicate(true)})
	app.changed();app.world_selection.select_entity(proposed.root_id,false)
	return ""

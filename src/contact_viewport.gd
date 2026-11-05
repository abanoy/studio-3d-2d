extends Node
# Editor-only target gestures. Previews use Model.preview_pose, never authored
# dictionaries; the existing contact correction installs one validated Undo edit.
var app
var editor
var active:=false
var dragging:=false
var target_id:=""
var target_root: WeakRef
var expected: Dictionary={}
var revision:=-1
var first:=0
var last:=0
var foot_index:=0
var field:="position"
var origin:=Vector3.ZERO
var accepted:=Vector3.ZERO
var before: Dictionary={}
var candidate: Dictionary={}
var preview_pose: Dictionary={}
var drag_start:=Vector2.ZERO
var drag_origin:=Vector3.ZERO
var drag_axis:=Vector3.ZERO
var screen_axis:=Vector2.ZERO
var units:=0.
var depth:=0.
var plane:=false
var camera_state: Dictionary={}
var handles: Array=[]
var center:=Vector2.ZERO
var target_visible:=false
var hint: Label
var done: Button
var panel: PanelContainer
var last_preview_ms:=0.
var last_commit_ms:=0.

func setup(_parent: Node) -> void:
	# Keep the range and exit action in view even when the inspector is scrolled.
	panel=PanelContainer.new();app.canvas.add_child(panel);panel.position=Vector2(12,12);panel.hide()
	var column:=VBoxContainer.new();panel.add_child(column)
	hint=app.label(column,"")
	done=app.button(column,"Done adjusting",func():stop())
	app.renderer.assets_changed.connect(func():stop())

func rig() -> RefCounted:
	if not app.renderer.world_runtime:return null
	return app.renderer.world_runtime.instance(target_id)

func context_error() -> String:
	var actor:=rig()
	if not actor or not target_root or target_root.get_ref()!=actor.root or app.renderer.active_model()!=actor or app.mode.selected!=2 or app.frame!=first or app.exporting or app.playing or app.recovery_revision!=revision or actor.data!=expected:return "The scene changed. Foot adjustment closed without applying a new target."
	if editor.live_busy():return "Physics is active or starting. Foot adjustment closed."
	if app.has_dialog(app) or app.home and app.home.visible or app.canvas.review_pointer.is_valid():return "Foot adjustment closed while another view opened."
	var feet: Array=editor.Ranges.Contact.Contacts.active(expected.animation_clips,first).get("feet",[])
	if feet.size()!=2 or app.pose_editor.selected!=feet[foot_index].ids[2]:return "Foot selection changed. Adjustment closed."
	return ""

func start(kind: String) -> void:
	var actor: RefCounted=app.renderer.active_model()
	if not editor.window.visible or not actor or actor.data!=editor.before or actor.root!=editor.target_root or app.frame!=editor.first or app.exporting or editor.live_busy():editor.note.text="The scene changed. Close this window and choose the range again.";return
	if editor.has_draft(actor):editor.note.text="Record your draft pose before adjusting a foot.";return
	if int(editor.end_frame.value)<editor.first:editor.note.text="The last frame must follow the first frame.";return
	if app.canvas.review_pointer.is_valid():editor.note.text="Finish the current geometry review first.";return
	var foot: Dictionary=editor.selected_foot()
	if foot.is_empty():editor.note.text="Plant feet before dragging a target.";return
	if actor.preview_frame==app.frame:editor.note.text="Finish the current pose preview before adjusting a foot.";return
	stop();active=true;target_id=actor.data.id;target_root=weakref(actor.root);expected=actor.data.duplicate(true);revision=app.recovery_revision;first=editor.first;last=int(editor.end_frame.value)+1;foot_index=editor.foot_choice.selected;field=kind
	origin=editor.Model.Timeline.vector(foot.position) if kind=="position" else editor.Model.Timeline.vector(foot.pole) if foot.has("pole") else actor.bone_transform(foot.ids[1]).origin;accepted=origin
	app.pose_editor.selected=foot.ids[2]
	if app.pose_editor.tree_items.has(app.pose_editor.selected):app.pose_editor.tree_items[app.pose_editor.selected].select(0)
	editor.window.hide();panel.show();update_hint();app.canvas.grab_focus();app.pose_editor.update_gizmo();app.message(hint.text)

func update_hint() -> void:
	hint.text="%s %s · Frames %d–%d\nDrag axes or center. Esc cancels; Done exits." % ["Left" if foot_index==0 else "Right","foot" if field=="position" else "knee target",first,last-1]

func draw() -> bool:
	if not active:return false
	var error:=context_error()
	if not error.is_empty():stop(error);return false
	handles.clear();var camera: Camera3D=app.renderer.camera
	target_visible=not camera.is_position_behind(accepted)
	if not target_visible:return true
	center=camera.unproject_position(accepted);var z:=maxf(camera.near,-camera.to_local(accepted).z);var pixels:=64.*1920./maxf(1,app.canvas.image_rect().size.x);var radius:=camera.project_position(center+Vector2(pixels,0),z).distance_to(accepted)
	app.canvas.pose_joints.append({"point":center,"selected":true});app.pose_editor.joints.append({"id":app.pose_editor.selected,"point":center})
	for axis in range(3):
		var direction: Vector3=Basis.IDENTITY[axis];var end:=camera.unproject_position(accepted+direction*radius);var points: Array[Vector2]=[center,end]
		app.canvas.pose_lines.append({"a":center,"b":end,"color":[Color("ef5b50"),Color("6bd978"),Color("6c9eff")][axis]});handles.append({"axis":direction,"points":points,"units":radius})
	if field=="pole":
		var foot: Dictionary=editor.Ranges.Contact.Contacts.active(expected.animation_clips,first).feet[foot_index];var point: Vector3=editor.Model.Timeline.vector(foot.position)
		if not camera.is_position_behind(point):app.canvas.pose_lines.append({"a":camera.unproject_position(point),"b":center,"color":Color("fff1a0")})
	app.canvas.queue_redraw();return true

func input(event: InputEvent,point: Vector2) -> void:
	if not active:return
	var error:=context_error()
	if not error.is_empty():stop(error);return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if not event.pressed:finish(false);return
		if app.navigating or event.ctrl_pressed or not target_visible:return
		var threshold:=10.*1920./maxf(1,app.canvas.image_rect().size.x);var hit: Dictionary={};plane=point.distance_to(center)<threshold
		if not plane:
			var nearest:=threshold
			for handle in handles:
				var distance: float=point.distance_to(Geometry2D.get_closest_point_to_segment(point,handle.points[0],handle.points[1]))
				if distance<nearest:nearest=distance;hit=handle
			if hit.is_empty():return
		dragging=true;app.pose_editor.dragging=true;before=expected.duplicate(true);candidate=before.duplicate(true);preview_pose={};drag_start=point;drag_origin=accepted;camera_state=app.renderer.view_state();depth=-app.renderer.camera.to_local(accepted).z
		if not plane:drag_axis=hit.axis;screen_axis=hit.points[1]-hit.points[0];units=hit.units
		return
	if event is InputEventMouseMotion and dragging:
		if app.renderer.view_state()!=camera_state:stop("The view changed; target drag cancelled.");return
		# Screen/canvas round trips have subpixel error. Returning within a quarter
		# displayed pixel restores the exact anchor instead of authoring tiny noise.
		if point.distance_to(drag_start)<=.25*1920./maxf(1,app.canvas.image_rect().size.x):preview(drag_origin);return
		var position: Vector3=drag_origin+app.renderer.camera.project_position(point,depth)-app.renderer.camera.project_position(drag_start,depth) if plane else drag_origin+drag_axis*(point-drag_start).dot(screen_axis.normalized())/maxf(1,screen_axis.length())*units
		preview(position)

func preview(position: Vector3) -> void:
	var actor:=rig();var began:=Time.get_ticks_usec()
	if position==drag_origin:
		clear_preview();candidate=before.duplicate(true);accepted=drag_origin;app.pose_editor.apply_frame();app.message("Original target restored. Release makes no edit.");return
	var changed: Dictionary=editor.Correction.edit(before,first,last,foot_index,{field:[position.x,position.y,position.z]},int(app.video.duration_frames))
	var error: String=changed.get("error","")
	if error.is_empty():error=editor.correction_error(actor,changed.data,first,first+1)
	if not error.is_empty():last_preview_ms=float(Time.get_ticks_usec()-began)/1000.;app.message(error+" Last valid preview kept.");return
	var probe=editor.Model.new();probe.root=actor.root;probe.base_root=actor.base_root;probe.order=actor.order;probe.bones=actor.bones;probe.world_context=actor.world_context;probe.data=changed.data
	var pose: Dictionary=probe.sample(first)
	if not probe.evaluation_error.is_empty():app.message(probe.evaluation_error);return
	candidate=changed.data;preview_pose=pose.duplicate(true);actor.preview_frame=first;actor.preview_pose=pose;actor.preview_transform={};accepted=position;app.pose_editor.apply_frame();app.message("Target preview · Frames %d–%d. Release checks the full range; Esc cancels." % [first,last-1]);last_preview_ms=float(Time.get_ticks_usec()-began)/1000.

func clear_preview() -> void:
	var actor:=rig()
	if not preview_pose.is_empty() and actor and target_root and target_root.get_ref()==actor.root and actor.preview_frame==first and actor.preview_pose==preview_pose:actor.preview_frame=-1;actor.preview_pose={};actor.preview_transform={}
	preview_pose={}

func finish(cancel:=false) -> void:
	if not dragging:return
	var error:=context_error();var actor:=rig();dragging=false;app.pose_editor.dragging=false;clear_preview()
	if not error.is_empty():
		active=false;panel.hide();candidate={};before={}
		# An unrelated layer/setting edit can invalidate the gesture without
		# evaluating 3D. Restore the current authored scene after removing our
		# preview, while preserving any replacement live/preview owner.
		if actor and target_root and target_root.get_ref()==actor.root:app.pose_editor.apply_frame()
		app.message(error);return
	var began:=Time.get_ticks_usec()
	if cancel or candidate==before:
		accepted=drag_origin;app.pose_editor.apply_frame();candidate={};before={};app.message("Target drag cancelled." if cancel else "Target unchanged.");return
	error=editor.correction_error(actor,candidate,first,last)
	if not error.is_empty():accepted=drag_origin;app.pose_editor.apply_frame();candidate={};before={};app.message(error+" Target was not changed.");last_commit_ms=float(Time.get_ticks_usec()-began)/1000.;return
	error=app.pose_editor.restore_state(candidate)
	if not error.is_empty():accepted=drag_origin;app.pose_editor.apply_frame();app.message(error)
	expected=actor.data.duplicate(true);revision=app.recovery_revision;candidate={};before={};last_commit_ms=float(Time.get_ticks_usec()-began)/1000.;app.message("Corrected %s for frames %d–%d. Undo restores the target." % ["foot" if field=="position" else "knee target",first,last-1] if error.is_empty() else error)

func stop(message: String="") -> void:
	if dragging:finish(true)
	active=false;expected={};before={};candidate={};target_root=null;handles.clear();panel.hide()
	if not message.is_empty():app.message(message)

func global_event(event: InputEvent) -> bool:
	if not active:return false
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:
		if dragging:finish(true)
		else:stop()
		return true
	if not dragging:return false
	if event is InputEventMouseMotion:
		var rect: Rect2=app.canvas.image_rect();var local: Vector2=app.canvas.get_global_transform().affine_inverse()*event.position;input(event,(local-rect.position)/rect.size*Vector2(1920,1080));return true
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:finish(false);return true
	return false

func _exit_tree() -> void:
	if dragging and is_instance_valid(app) and is_instance_valid(app.pose_editor):app.pose_editor.dragging=false
	active=false;dragging=false

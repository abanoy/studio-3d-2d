extends Node
const Store=preload("res://src/lesson_store.gd")
const Assets=preload("res://src/tutorial_assets.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
const IK=preload("res://src/limb_ik.gd")
const First=preload("res://src/first_movie_lesson.gd")
const COURSES={First.ID:First.DEFINITION,"basic-pose":{"title":"Basic · Pose and draw","steps":["Click Practice figure in World.","At frame 24, raise and key its left hand above the shoulder.","At frame 24, draw a visible mark on Ink."],"hints":["Use the left World tree, or click the figure in the viewport.","Keep Physics off. Hold Alt, choose Left upper arm, and rotate upward at frame 24. Pose edits key automatically.","Choose Draw and the Ink layer. Add a cel if needed, then paint a mark." ]},"advanced-camera":{"title":"Advanced · Camera shots","steps":["Turn on Advanced in the blue top bar.","At frame 24, change your camera view and save a camera key.","Change FOV by at least 8 degrees, then replace the frame 24 camera key."],"hints":["Advanced reveals controls without changing the scene.","Choose Scene / camera. Ctrl + left-drag with WASD moves the view. Save camera key records it.","Use Editor camera FOV, then Save camera key and confirm replacement. An unrecorded view does not count."]}}
var app
var store=Store.new()
var assets_root:="res://examples/tutorials"
var active:=false
var loading:=false
var restoring:=false
var course:=""
var session:=""
var step:=0
var done:=false
var pending_course:=""
var panel: PanelContainer
var title: Label
var instruction: Label
var hint_button: Button
var previous_button: Button
var next_tick:=0
var last_action:=0
var last_signature:=""
var hint_due:=false
var fov_baseline:=55.
var observed:={}
var baseline:={}
var asset_hashes:={}
var action_row: HBoxContainer
var action_button: Button
var export_button: Button
var marker: Panel
var hint_visible:=false
var collapsed:=false
var collapse_button: Button

func _ready() -> void:
	store.root=app.home.store.file_path.get_base_dir().path_join("tutorial-progress")
	panel=PanelContainer.new();panel.name="LessonCard";panel.custom_minimum_size.x=430;panel.z_index=30;app.canvas.add_child(panel)
	panel.add_theme_stylebox_override("panel",preload("res://src/studio_theme.gd").surface("fffef1","e7f1fb","88a8c4",8));panel.mouse_filter=Control.MOUSE_FILTER_STOP
	var box:=VBoxContainer.new();panel.add_child(box);var heading:=HBoxContainer.new();box.add_child(heading);title=app.label(heading,"");title.size_flags_horizontal=Control.SIZE_EXPAND_FILL;collapse_button=app.button(heading,"−",func():set_collapsed(not collapsed));collapse_button.tooltip_text="Collapse / expand lesson instructions";instruction=app.label(box,"");instruction.custom_minimum_size.x=400;instruction.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;instruction.max_lines_visible=3
	action_row=HBoxContainer.new();box.add_child(action_row);action_button=app.button(action_row,"",func():First.action(self));export_button=app.button(action_row,"Export movie",func():app.export_dialog());action_row.hide()
	var row:=HBoxContainer.new();box.add_child(row)
	previous_button=app.button(row,"Previous",previous);hint_button=app.button(row,"Hint",show_hint);app.button(row,"Leave lesson",func():leave(true))
	panel.hide();app.has_project.operation_finished.connect(opened)
	app.movie_export_finished.connect(func(_folder,success):
		if active and course==First.ID and step==10:observed["export_done"]=success)
	marker=Panel.new();marker.name="LessonHintHighlight";marker.mouse_filter=Control.MOUSE_FILTER_IGNORE;marker.z_index=40;app.add_child(marker)
	var border:=StyleBoxFlat.new();border.bg_color=Color(1,.85,.2,.07);border.border_color=Color("ffd454");border.set_border_width_all(3);border.set_corner_radius_all(7);marker.add_theme_stylebox_override("panel",border);marker.hide()

func open_catalog() -> void:
	if app.exporting or app.has_dialog(app):return
	var dialog:=AcceptDialog.new();dialog.title="Tutorials";dialog.exclusive=false;dialog.ok_button_text="Back";app.add_child(dialog)
	var box:=VBoxContainer.new();dialog.add_child(box);app.label(box,"Learn by making a movie · focused practice chapters")
	for id in Store.COURSES:
		app.label(box,COURSES[id].title)
		var row:=HBoxContainer.new();box.add_child(row);var recent:=store.progress(id)
		if not recent.is_empty():app.button(row,"Open finished practice" if recent.done else "Continue",func():dialog.hide();dialog.queue_free();request(id,false))
		app.button(row,"Start fresh",func():dialog.hide();dialog.queue_free();request(id,true))
		var sessions:=store.sessions(id)
		if sessions.size()>1:
			var history:=MenuButton.new();history.text="Saved practices";row.add_child(history)
			for value in sessions:history.get_popup().add_item(Time.get_datetime_string_from_unix_time(int(value.updated_at)).replace("T"," ")+" UTC • step %d" % (int(value.step)+1))
			history.get_popup().index_pressed.connect(func(index):dialog.hide();dialog.queue_free();request(id,false,sessions[index].session))
	dialog.confirmed.connect(func():dialog.hide();dialog.queue_free());dialog.canceled.connect(dialog.queue_free);dialog.popup_centered()

func request(id: String,fresh: bool,saved_session := "") -> void:
	if not id in Store.COURSES or app.exporting:return
	var action:=func():start(id,fresh,saved_session)
	if app.dirty:app.confirm_action("Replace the current unsaved scene with this practice? Save first to keep it.",action)
	else:action.call()

func start(id: String,fresh: bool,saved_session := "") -> bool:
	if not id in Store.COURSES or app.exporting or loading:return false
	if app.physics_editor.recording.active:app.message("Finish recording before starting another lesson.");return false
	if active and not save_resume():return false
	if not fresh:
		var value:=store.progress(id,saved_session)
		if value.is_empty():app.message("No valid saved practice. Start fresh to begin.");return false
		restoring=true;var ok:=store.load_snapshot(app,id,value.session,value.current);restoring=false
		if not ok:app.message(store.error);return false
		course=id;session=value.session;step=int(value.step);done=value.done;observed=store.restored_observations.duplicate();active=true;asset_hashes.clear();arm();return true
	var manifest:=preload("res://src/recovery.gd").read_json(ProjectSettings.globalize_path(assets_root.path_join("manifest.json")))
	if manifest.get("format")!="studio_tutorial_assets_1" or not manifest.get("files") is Dictionary:app.message("Included practice assets are unavailable.");return false
	var scene_file:="first-movie.has" if id==First.ID else "practice.has"
	for name in ["Practice room.glb","Practice figure.glb",scene_file]:
		if not manifest.files.get(name) is Dictionary or FileAccess.get_sha256(assets_root.path_join(name))!=manifest.files[name].get("sha256"):app.message("Included practice asset is missing or changed: "+name);return false
	loading=true;pending_course=id;app.has_project.open_file(ProjectSettings.globalize_path(assets_root.path_join(scene_file)),{},true);return true

func opened(action: String,success: bool) -> void:
	if not loading or action!="unpack":return
	loading=false
	if not success:pending_course="";return
	course=pending_course;pending_course="";session="%d_%s" % [Time.get_unix_time_from_system(),str(ResourceUID.create_id())];step=0;done=false;observed={};asset_hashes.clear();active=true
	if not checkpoint("step_00"):active=false;return
	arm()

func checkpoint(name: String) -> bool:
	if course==First.ID:First.observe(self)
	if not app.physics_editor.freeze_all():return false
	app.finish_stroke();app.pose_editor.finish_drag();app.stop()
	if not store.save(app,course,session,step,done,name,observed):app.message(store.error);return false
	return true

func save_resume() -> bool:
	return checkpoint("resume") if active else true

func leave(save := true) -> void:
	if app.physics_editor.recording.active:app.message("Finish recording before leaving the lesson.");return
	if save and not save_resume():return
	active=false;panel.hide();marker.hide();app.message("Lesson progress kept. Your scene is still editable; Save if you want a normal HAS file.")

func document_changing() -> void:
	if active and not loading and not restoring:save_resume();active=false;panel.hide();marker.hide()

func arm() -> void:
	next_tick=Time.get_ticks_msec()+200;last_action=Time.get_ticks_msec();last_signature="";hint_due=false
	baseline=preload("res://src/recovery.gd").read_json(store.folder(course,session).path_join("step_%02d/project.json" % step)).get("editor",{}).get("lesson_ui",{})
	var key:=key_at(24);fov_baseline=float(key.get("fov",app.renderer.camera.fov))
	if course=="advanced-camera" and step==2:
		var before:=preload("res://src/recovery.gd").read_json(store.folder(course,session).path_join("step_02/project.json"))
		for item in before.get("camera_keys",[]):
			if item is Dictionary and item.get("frame")==24 and (item.get("fov") is int or item.get("fov") is float):fov_baseline=float(item.fov)
	refresh();panel.show()

func refresh() -> void:
	title.text=COURSES[course].title+(" · complete" if done else " · %d / %d" % [step+1,Store.COURSES[course]])
	instruction.text="Your practice scene stays editable. Save it if you want to keep it." if done else COURSES[course].steps[step]
	instruction.tooltip_text=instruction.text
	previous_button.disabled=step==0;hint_button.disabled=done;hint_button.text="Hint"
	action_button.text=First.action_label(step) if course==First.ID and not done else "";action_row.visible=not action_button.text.is_empty();export_button.visible=course==First.ID and step==10 and not done
	set_collapsed(collapsed)
	hint_visible=false;marker.hide()

func show_hint() -> void:
	if not active or done:return
	instruction.text=COURSES[course].hints[step];instruction.tooltip_text=instruction.text;hint_button.text="Hint shown";hint_due=false;hint_visible=true;set_collapsed(false);update_highlight()

func set_collapsed(value: bool) -> void:
	collapsed=value;collapse_button.text="+" if collapsed else "−";instruction.visible=not collapsed;action_row.visible=not collapsed and not action_button.text.is_empty();title.tooltip_text=instruction.text
	panel.size.y=0

func layout_card() -> void:
	panel.size.x=minf(460,app.canvas.size.x-20)
	var extent: Vector2=app.canvas.size-panel.size-Vector2(10,10)
	var candidates: Array[Vector2]=[Vector2(10,maxf(0,extent.y)),Vector2(maxf(10,extent.x),maxf(0,extent.y)),Vector2(10,0),Vector2(maxf(10,extent.x),0)]
	var rig=First.object(self,"model") if course==First.ID else app.renderer.world_runtime.instance(Assets.FIGURE_ID) if app.renderer.world_runtime else null
	var focus:=Rect2(app.canvas.size*.5-Vector2(60,80),Vector2(120,160))
	if rig:
		var id:=bone(rig,"upper_arm.L")
		if not id.is_empty():
			var point: Vector3=rig.bone_transform(id).origin
			if not app.renderer.camera.is_position_behind(point):
				var image: Rect2=app.canvas.image_rect();var center: Vector2=image.position+app.renderer.camera.unproject_position(point)/Vector2(1920,1080)*image.size
				focus=Rect2(center-Vector2(60,80),Vector2(120,160))
	var best: Vector2=candidates[0];var area:=INF
	for candidate in candidates:
		var overlap:=Rect2(candidate,panel.size).intersection(focus).get_area()
		if overlap<area:area=overlap;best=candidate
	panel.position=best

func asset_digest(name: String) -> String:
	if not asset_hashes.has(name):asset_hashes[name]=FileAccess.get_sha256(assets_root.path_join(name))
	return asset_hashes[name]

func find_button(prefix: String) -> Control:
	for button in app.find_children("","Button",true,false):
		if button.text.begins_with(prefix) and button.is_visible_in_tree():return button
	return null

func update_highlight() -> void:
	marker.hide()
	if not hint_visible or done or app.home.visible or app.has_dialog(app):return
	var target: Control
	var arm_hint: bool=(course==First.ID and step==5) or (course=="basic-pose" and step==1)
	if arm_hint:
		var rig=First.object(self,"model") if course==First.ID else app.renderer.world_runtime.instance(Assets.FIGURE_ID) if app.renderer.world_runtime else null
		if rig:
			var id:=bone(rig,"upper_arm.L")
			if not id.is_empty():
				var point: Vector3=rig.bone_transform(id).origin
				if not app.renderer.camera.is_position_behind(point):
					var pixel: Vector2=app.renderer.camera.unproject_position(point);var image: Rect2=app.canvas.image_rect();var position: Vector2=app.canvas.global_position+image.position+pixel/Vector2(1920,1080)*image.size
					if app.canvas.get_global_rect().has_point(position):marker.global_position=position-Vector2(14,14);marker.size=Vector2(28,28);marker.show()
		return
	if course==First.ID:
		match step:
			0:target=action_button
			1:target=action_button if First.object(self,"model")==null else app.physics_editor.toggle
			2:target=app.world_selection.tree
			3:target=app.canvas
			4,6:target=find_button("Save camera key")
			7:target=app.layer_choice
			8:target=app.play_button
			9:target=app.timeline
			10:target=export_button
	elif course=="advanced-camera":target=find_button("Advanced") if step==0 else find_button("Save camera key")
	elif course=="basic-pose":target=app.world_selection.tree if step==0 else app.layer_choice
	if target and target.is_visible_in_tree():marker.global_position=target.global_position-Vector2(2,2);marker.size=target.size+Vector2(4,4);marker.show()

func key_at(at: int) -> Dictionary:
	for key in app.keys:
		if key.frame==at:return key
	return {}

func bone(rig,name: String) -> String:
	for id in rig.order:
		if IK.normalized(rig.bones[id].name)==IK.normalized(name):return id
	return ""

func satisfied() -> bool:
	if course==First.ID:return First.satisfied(self)
	if course=="advanced-camera":
		if step==0:return app.advanced_mode
		var key:=key_at(24)
		if app.frame!=24 or key.is_empty():return false
		if step==2:return absf(float(key.fov)-fov_baseline)>=8
		return changed_camera()
	if step==0:return app.world_selection.selected==Assets.FIGURE_ID
	if step==2:return visible_ink()
	var rig=app.renderer.world_runtime.instance(Assets.FIGURE_ID) if app.renderer.world_runtime else null
	return raised_arm(rig)

func changed_camera() -> bool:
	var key:=key_at(24);var first:=key_at(0)
	return app.frame==24 and not key.is_empty() and not first.is_empty() and (Timeline.vector(key.position).distance_to(Timeline.vector(first.position))>=.3 or Timeline.quaternion(key.rotation_xyzw).angle_to(Timeline.quaternion(first.rotation_xyzw))>=.15 or absf(float(key.fov)-float(first.fov))>=5)

func visible_ink() -> bool:
	if app.frame!=24:return false
	for layer in app.layers:
		if layer.name!="Ink" or not layer.visible or float(layer.get("opacity",1.0))<=0:continue
		var cel:=Drawing.cel_at(layer,24)
		return not cel.is_empty() and Drawing.layer_image(cel.image,float(layer.get("opacity",1.0))).get_used_rect().get_area()>=16
	return false

func raised_arm(rig) -> bool:
	if not rig or app.frame!=24:return false
	var upper:=bone(rig,"upper_arm.L");var hand:=bone(rig,"hand.L")
	if upper.is_empty() or hand.is_empty():return false
	var keyed:=false
	for key in rig.authored_keys():
		if key.frame==24:keyed=true
	var pose: Dictionary=rig.sample(24);var bent:=false
	for part in [upper,bone(rig,"forearm.L")]:
		if pose.has(part) and Timeline.quaternion(pose[part].rotation_xyzw).get_angle()>=.15:bent=true
	var skeleton: Skeleton3D=rig.bones[hand].skeleton
	return keyed and bent and skeleton.get_bone_global_pose(rig.bones[hand].index).origin.y-skeleton.get_bone_global_pose(rig.bones[upper].index).origin.y>=.2

func previous() -> void:
	if not active or step<=0 or app.exporting:return
	if app.physics_editor.recording.active:app.message("Finish recording before restoring a lesson step.");return
	var target:=step-1;restoring=true;var ok:=store.load_snapshot(app,course,session,"step_%02d" % target);restoring=false
	if not ok:app.message(store.error);return
	step=target;done=false
	observed=store.restored_observations.duplicate()
	if not checkpoint("step_%02d" % step):return
	arm()

func _process(_delta: float) -> void:
	if not active or loading or restoring:return
	if app.home.visible:last_action=Time.get_ticks_msec();marker.hide();return
	layout_card()
	update_highlight()
	if course==First.ID:First.observe(self)
	if done or Time.get_ticks_msec()<next_tick:return
	next_tick=Time.get_ticks_msec()+200
	if app.exporting or app.playing or app.drawing or app.navigating or app.pose_editor.dragging or app.physics_editor.is_running() or app.has_dialog(app) or not app.timeline.moving_id.is_empty():return
	var signature:="%d:%d:%s:%s" % [app.recovery_revision,app.frame,app.world_selection.selected,str(app.advanced_mode)]
	if signature!=last_signature:last_signature=signature;last_action=Time.get_ticks_msec();hint_button.text="Hint";hint_due=false
	if satisfied():
		step+=1;done=step==int(Store.COURSES[course])
		if not checkpoint("step_%02d" % step):step-=1;done=false;return
		arm();app.message("Step completed." if not done else "Chapter completed. Your practice scene is yours to keep editing.")
	elif Time.get_ticks_msec()-last_action>=15000 and not hint_due:hint_due=true;hint_button.text="Need a hint?"

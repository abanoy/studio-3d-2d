extends Node
const Measure=preload("res://src/map_measure.gd")
const Renderer=preload("res://src/renderer.gd")
var app
var window: Window
var preview: TextureRect
var note: Label
var target: SpinBox
var apply_button: Button
var fit_preview: CheckButton
var scratch: Node
var guide: MeshInstance3D
var points: Array=[]
var triangles: Array=[]
var before:={}
var root_id:=0
var revision:=-1
var at_frame:=-1
var pending:=false
var dragging:=0
var generation:=0

func eligibility(rig) -> String:
	if not rig or rig.data.get("kind")!="environment":return "Select a map in the World tree first."
	if not rig.data.parent_id.is_empty():return "Measure an unattached map root. This map is attached to another object."
	if not rig.authored_keys().is_empty() or not rig.data.get("animation_clips",[]).is_empty() or not rig.data.get("pose",{}).is_empty():return "This map has animation or a draft pose. Keep its size or use its animation controls."
	for row in app.current_world().objects:
		if row.parent_id==rig.data.id:return "This map has attached objects. Size a separate map before attaching them."
	if not rig.root.is_visible_in_tree():return "Show the map at this frame before measuring it."
	if app.physics_editor.is_running():return "Turn Physics and Hair & clothes off before sizing a map."
	return ""

func valid() -> bool:
	var rig: RefCounted=app.renderer.active_model()
	return pending and is_instance_valid(window) and rig!=null and rig.root.get_instance_id()==root_id and rig.data==before and app.recovery_revision==revision and app.frame==at_frame and not app.exporting and not app.playing and not app.physics_editor.is_running() and not app.home.visible

func open() -> void:
	if pending:window.grab_focus();return
	if app.exporting or app.source_import.pid>0 or app.height_review.pending:return
	var rig: RefCounted=app.renderer.active_model();var error:=eligibility(rig)
	if not error.is_empty():app.message(error);return
	app.stop();app.release_mouse();app.pose_editor.finish_drag()
	before=rig.data.duplicate(true);root_id=rig.root.get_instance_id();revision=app.recovery_revision;at_frame=app.frame;points=[];triangles=[];pending=true
	window=Window.new();window.title="Size map from a known distance";window.theme=app.theme;window.transient=true;window.close_requested.connect(close);window.focus_exited.connect(func():dragging=0);app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new();panel.add_child(column)
	app.label(column,"Click the bottom, then top of a doorway — or any two surfaces a known distance apart.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	preview=TextureRect.new();preview.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;preview.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;preview.size_flags_vertical=Control.SIZE_EXPAND_FILL;preview.custom_minimum_size=Vector2(600,300);column.add_child(preview);preview.gui_input.connect(input)
	note=app.label(column,"Preparing a separate map view…");note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var row:=HBoxContainer.new();column.add_child(row)
	var presets:=OptionButton.new()
	for label in ["Door example: 80 inches","Six-foot reference","Ceiling example: 8 feet"]:presets.add_item(label)
	row.add_child(presets);presets.item_selected.connect(func(i):target.value=[2.032,1.8288,2.4384][i])
	target=app.spin(row,"Known distance (metres)",.1,100,2.032);target.step=.0001;target.value=2.032;target.value_changed.connect(func(_value):refresh())
	app.label(column,"Examples are editable. Yellow = measured span; cyan person = 6 feet. First point stays fixed.\nLeft: mark • Right drag: look • Middle drag: pan • Wheel: move closer / farther").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var buttons:=HBoxContainer.new();column.add_child(buttons)
	fit_preview=CheckButton.new();fit_preview.text="Preview size";fit_preview.disabled=true;fit_preview.toggled.connect(func(_value):refresh());buttons.add_child(fit_preview)
	apply_button=app.button(buttons,"Apply map size",apply);apply_button.disabled=true
	app.button(buttons,"Pick again",func():fit_preview.set_pressed_no_signal(false);points=[];refresh())
	app.button(buttons,"Frame map",func():if scratch and scratch.model:scratch.frame_scene(scratch.model.root))
	app.button(buttons,"Cancel",close)
	generation+=1;window.popup_centered(Vector2i(850,mini(650,maxi(550,int(app.get_viewport_rect().size.y)-80))));call_deferred("prepare",generation)

func prepare(token: int) -> void:
	if generation!=token:return
	if not valid():close();return
	if FileAccess.get_sha256(before.source)!=before.sha256:note.text="The source changed. Close and import it again.";return
	scratch=Renderer.new();add_child(scratch);scratch.setup(960,540);scratch.video_settings=app.video.duplicate(true);scratch.empty_environment=false;scratch.editor_grid.visible=false;scratch.set_background(app.video.get("world_background","legacy_blue"))
	var result: Dictionary=scratch.prepare_model(before)
	if result.has("error"):note.text=result.error;return
	scratch.install_model(result);scratch.model.apply(at_frame,false,false,app.video);scratch.camera.global_transform=app.renderer.camera.global_transform;scratch.camera.fov=app.renderer.camera.fov;scratch.camera.near=app.renderer.camera.near;scratch.camera.far=app.renderer.camera.far
	preview.texture=scratch.viewport.get_texture();var geometry:=Measure.collect(scratch.model.root)
	if not geometry.error.is_empty():note.text=geometry.error;return
	triangles=geometry.triangles;guide=MeshInstance3D.new();scratch.world.add_child(guide);guide.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	refresh()

func image_rect() -> Rect2:
	var size:=Vector2(960,540)*minf(preview.size.x/960.,preview.size.y/540.)
	return Rect2((preview.size-size)*.5,size)

func input(event: InputEvent) -> void:
	if not valid() or triangles.is_empty():return
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_RIGHT,MOUSE_BUTTON_MIDDLE]:dragging=event.button_index if event.pressed else 0
		if not event.pressed:return
		var rect:=image_rect()
		if not rect.has_point(event.position):return
		if event.button_index==MOUSE_BUTTON_LEFT:
			if fit_preview.button_pressed:note.text="Turn Preview size off, or choose Pick again, to mark another distance.";return
			var hit: Variant=Measure.pick(triangles,scratch.camera,(event.position-rect.position)/rect.size*Vector2(960,540))
			if hit==null:note.text="No map surface there. Pick a solid edge or change the view.";return
			if points.size()==2:points=[]
			points.append(hit);refresh()
		elif event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:scratch.camera.position+=scratch.camera.basis.z*(-1. if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1.)*maxf(.05,scratch.camera.position.distance_to(scratch.model.root.position)*.08)
	elif event is InputEventMouseMotion and dragging!=0:
		if dragging==MOUSE_BUTTON_RIGHT:
			scratch.camera.rotate_y(-event.relative.x*.004);scratch.camera.rotate_object_local(Vector3.RIGHT,-event.relative.y*.004)
		else:scratch.camera.position+=(scratch.camera.basis.x*-event.relative.x+scratch.camera.basis.y*event.relative.y)*maxf(.001,scratch.camera.position.distance_to(scratch.model.root.position)*.002)
		refresh_guide()

func refresh() -> void:
	if not is_instance_valid(apply_button):return
	apply_button.disabled=true;fit_preview.disabled=points.size()!=2
	if points.size()<2:note.text="Pick the first surface." if points.is_empty() else "Pick the second surface. Cyan guide is 6 feet tall."
	else:
		var plan:=Measure.fit(before,points,target.value)
		note.text=plan.error if not plan.error.is_empty() else "Measured %.5f units → %.4f metres. Map scale × %.5f. Nothing changes until Apply." % [plan.distance,target.value,plan.factor]
		apply_button.disabled=not plan.error.is_empty()
		fit_preview.disabled=not plan.error.is_empty()
	if scratch and scratch.model:
		var plan:=Measure.fit(before,points,target.value) if points.size()==2 else {"error":""}
		scratch.model.data=plan.data if fit_preview.button_pressed and plan.has("data") else before.duplicate(true)
		scratch.model.apply(at_frame,false,false,app.video)
	refresh_guide()

func refresh_guide() -> void:
	if not is_instance_valid(guide):return
	var mesh:=ImmediateMesh.new();guide.mesh=mesh
	if points.is_empty():return
	var material:=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.vertex_color_use_as_albedo=true;material.no_depth_test=true
	mesh.surface_begin(Mesh.PRIMITIVE_LINES,material)
	if points.size()==2:
		var plan:=Measure.fit(before,points,target.value)
		var end: Vector3=points[0]+(points[1]-points[0])*plan.factor if fit_preview.button_pressed and plan.has("factor") else points[1]
		mesh.surface_set_color(Color.YELLOW);mesh.surface_add_vertex(points[0]);mesh.surface_add_vertex(end)
	var origin: Vector3=points[0];var right:=Vector3(scratch.camera.basis.x.x,0,scratch.camera.basis.x.z).normalized()
	if right.length()<.1:right=Vector3.RIGHT
	mesh.surface_set_color(Color.CYAN)
	var pairs:=[Vector2(-.16,0),Vector2(0,.87),Vector2(0,.87),Vector2(.16,0),Vector2(0,.87),Vector2(0,1.52),Vector2(-.3,1.05),Vector2(0,1.42),Vector2(0,1.42),Vector2(.3,1.05)]
	for p in pairs:mesh.surface_add_vertex(origin+right*p.x+Vector3.UP*p.y)
	for i in range(16):
		for angle in [i*TAU/16.,(i+1)*TAU/16.]:mesh.surface_add_vertex(origin+right*sin(angle)*.1544+Vector3.UP*(1.6744+cos(angle)*.1544))
	mesh.surface_end()

func apply() -> void:
	if not valid():close();app.message("The scene changed. Measure the map again.");return
	var rig: RefCounted=app.renderer.active_model();var error:=eligibility(rig)
	if not error.is_empty():note.text=error;return
	if FileAccess.get_sha256(before.source)!=before.sha256:note.text="The source changed. Close and import it again.";return
	var plan:=Measure.fit(before,points,target.value)
	if not plan.error.is_empty():note.text=plan.error;return
	var world: Dictionary=app.current_world();var after:=world.duplicate(true)
	for i in range(after.objects.size()):
		if after.objects[i].id==before.id:after.objects[i]=plan.data
	error=preload("res://src/world_document.gd").validate(after,int(app.video.duration_frames))
	if not error.is_empty():note.text=error;return
	if app.pose_editor.contacts.metadata_bytes(after)>1024*1024:note.text="This adjustment exceeds the project metadata limit.";return
	close();error=app.restore_world(after)
	if not error.is_empty():app.message(error);return
	app.push_history({"type":"world","before":world,"after":after});app.changed();app.message("Map size adjusted. The first point stayed fixed. Undo restores the previous size.")

func close() -> void:
	pending=false;generation+=1;triangles=[];points=[];dragging=0
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null
	if is_instance_valid(scratch):scratch.camera.current=false;scratch.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;scratch.viewport.world_3d=null;scratch.queue_free()
	scratch=null;guide=null

func _process(_delta: float) -> void:
	if pending and not valid():close()

func _exit_tree() -> void:close()

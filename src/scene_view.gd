extends Node
# Personal editor presentation. The native camera, raster pixels and export
# viewport stay authoritative, including virtual pixels beyond the film frame.
var app
var viewport: SubViewport
var camera: Camera3D
var choice: OptionButton
var frame_button: CheckButton
var grid_button: CheckButton
var setup_enabled:=true
var frame_enabled:=false
var grid_enabled:=false
var last_layout: Array=[]

func setup(owner_app,parent: Control) -> void:
	app=owner_app;process_priority=10;app.world_selection.process_priority=20
	var prefs:=ConfigFile.new();prefs.load(app.display_prefs_path)
	var saved=prefs.get_value("scene_view","setup",true)
	if saved is bool:setup_enabled=saved
	saved=prefs.get_value("scene_view","frame",false)
	if saved is bool:frame_enabled=saved
	saved=prefs.get_value("scene_view","thirds",false)
	if saved is bool:grid_enabled=saved
	viewport=SubViewport.new();viewport.name="SceneSetupView";viewport.world_3d=app.renderer.viewport.find_world_3d()
	viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;viewport.gui_disable_input=true;add_child(viewport)
	camera=Camera3D.new();viewport.add_child(camera);camera.current=true
	choice=OptionButton.new();choice.add_item("Scene setup");choice.add_item("Camera focus");parent.add_child(choice)
	choice.tooltip_text="Scene setup fills the view. Camera focus shows the output-shaped view. Neither changes the shot or render size."
	choice.item_selected.connect(func(index):set_setup(index==0))
	frame_button=CheckButton.new();frame_button.text="Frame";parent.add_child(frame_button)
	frame_button.tooltip_text="Show the camera output boundary while arranging the scene. This guide stays out of renders."
	frame_button.toggled.connect(func(value):set_guides(value,grid_enabled))
	grid_button=CheckButton.new();grid_button.text="3×3";parent.add_child(grid_button)
	grid_button.tooltip_text="Show a rule-of-thirds composition grid inside the camera frame. This guide stays out of renders."
	grid_button.toggled.connect(func(value):set_guides(frame_enabled,value))
	sync()

func set_setup(value: bool,persist:=true) -> void:
	if setup_enabled!=value:
		app.pose_editor.finish_drag();app.release_mouse();app.canvas.cancel_middle();app.world_selection.cancel_gesture(true)
	setup_enabled=value
	if persist:app.save_display_preference("scene_view","setup",value)
	sync();app.pose_editor.update_gizmo()

func set_guides(frame: bool,grid: bool,persist:=true) -> void:
	frame_enabled=frame;grid_enabled=grid
	if persist:
		app.save_display_preference("scene_view","frame",frame)
		app.save_display_preference("scene_view","thirds",grid)
	sync()

static func copy_camera(source: Camera3D,target: Camera3D,native_size: Vector2i,display_size: Vector2i,extended: bool) -> void:
	target.global_transform=source.global_transform;target.projection=source.projection
	target.near=source.near;target.far=source.far;target.keep_aspect=source.keep_aspect
	target.fov=source.fov;target.size=source.size
	target.h_offset=source.h_offset;target.v_offset=source.v_offset;target.frustum_offset=source.frustum_offset
	target.environment=source.environment;target.attributes=source.attributes;target.cull_mask=source.cull_mask
	if extended:
		var native_aspect:=float(native_size.x)/native_size.y
		var display_aspect:=float(display_size.x)/display_size.y
		var vertical:=deg_to_rad(source.fov)
		if source.keep_aspect==Camera3D.KEEP_WIDTH:vertical=2.*atan(tan(vertical/2.)/native_aspect)
		target.keep_aspect=Camera3D.KEEP_HEIGHT
		target.fov=rad_to_deg(2.*atan(tan(vertical/2.)*maxf(1.,native_aspect/display_aspect)))

func _process(_delta: float) -> void:sync()

func sync() -> void:
	if not is_instance_valid(app.canvas) or not viewport:return
	var editing: bool=app.mode.selected in [1,2]
	# HAS authors a centered perspective camera. Retain Focus for an unsupported
	# projection rather than stretching it or changing its authored camera values.
	var native: Camera3D=app.renderer.camera
	var centered: bool=native.projection==Camera3D.PROJECTION_PERSPECTIVE and native.h_offset==0. and native.v_offset==0. and native.frustum_offset==Vector2.ZERO
	app.canvas.scene_editing=editing;app.canvas.scene_setup=editing and setup_enabled and centered
	app.canvas.show_camera_frame=frame_enabled;app.canvas.show_thirds=grid_enabled
	app.canvas.scene_navigation=app.mode.selected==1 or app.mode.selected==2 and app.canvas.scene_setup
	var extent: Vector2i=app.canvas.setup_size()
	if viewport.size!=extent:viewport.size=extent
	copy_camera(native,camera,app.renderer.viewport.size,extent,true)
	app.canvas.setup_background=viewport.get_texture()
	var capture: bool=app.renderer.native_readbacks>0
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS if app.canvas.scene_setup and not capture and not app.exporting else SubViewport.UPDATE_DISABLED
	app.renderer.viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS if not app.canvas.scene_setup or capture else SubViewport.UPDATE_DISABLED
	choice.visible=editing;frame_button.visible=editing;grid_button.visible=editing
	choice.select(0 if setup_enabled else 1);frame_button.set_pressed_no_signal(frame_enabled);grid_button.set_pressed_no_signal(grid_enabled)
	var layout: Array=[editing,app.canvas.scene_setup,app.canvas.size,app.canvas.resolution,frame_enabled,grid_enabled]
	if layout!=last_layout:last_layout=layout;app.canvas.queue_redraw()

func display_camera() -> Camera3D:
	return camera if app.canvas.scene_setup else app.renderer.camera

func pick_state() -> Array:
	var source: Camera3D=app.renderer.camera
	# Native rays and normalized mask UVs survive a pure UI translation (for
	# example an inspector relayout). Size/projection changes invalidate them.
	return [app.mode.selected,app.canvas.scene_setup,app.canvas.scene_rect().size,app.canvas.image_rect().size,source.global_transform,source.projection,source.keep_aspect,source.fov,source.size,source.near,source.far,source.h_offset,source.v_offset,source.frustum_offset]

func _exit_tree() -> void:
	if is_instance_valid(camera):camera.current=false
	if is_instance_valid(viewport):viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;viewport.world_3d=null

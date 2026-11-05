extends Node
const Drawing=preload("res://src/drawing.gd")
const Renderer=preload("res://src/renderer.gd")
const SOURCES=["View + drawings","Visible drawings","Active drawing (original)"]
var app
var panel: VBoxContainer
var source: OptionButton
var hint: Label
var viewport: SubViewport
var camera: Camera3D
var context: Dictionary={}
var captures:=0
var last_result: Dictionary={}

func _exit_tree() -> void:
	# Stop pending rendering and release the shared world before the scene is freed.
	context={}
	if RenderingServer.frame_post_draw.is_connected(finish_capture):RenderingServer.frame_post_draw.disconnect(finish_capture)
	if is_instance_valid(camera):camera.current=false
	if is_instance_valid(viewport):
		viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
		viewport.world_3d=null

func setup(parent: Control) -> void:
	panel=VBoxContainer.new();parent.add_child(panel);parent.move_child(panel,app.tool.get_index()+1)
	hint=app.label(panel,"Click a color. Guides are excluded.")
	hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;hint.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	var detail:=VBoxContainer.new();panel.add_child(detail);app.advanced(detail)
	app.label(detail,"Pick from")
	source=OptionButton.new();detail.add_child(source)
	for name in SOURCES:source.add_item(name)
	source.tooltip_text="View includes the visible 3D scene and drawing stack. Original reads raw active-cel RGBA before layer opacity."
	source.item_selected.connect(func(_index):cancel(false);refresh())
	refresh()

func arm() -> void:
	if app.mode.selected!=0 or app.playing or app.exporting or (app.home and app.home.visible) or app.has_dialog(app):return
	app.finish_stroke();app.fill_editor.cancel();cancel(false);app.tool.select(3);refresh()
	app.message("Click a color in the picture. Escape returns to Pen.")

func refresh() -> void:
	panel.visible=app.tool.selected==3
	hint.text="Picking color…" if not context.is_empty() else "Click a color: "+SOURCES[source.selected]+".\nThen return to Pen. Escape cancels."

func _process(_delta: float) -> void:
	if not context.is_empty() and not valid_context():cancel()
	refresh()

func cancel(return_to_pen: bool=true) -> void:
	context={}
	if RenderingServer.frame_post_draw.is_connected(finish_capture):RenderingServer.frame_post_draw.disconnect(finish_capture)
	if viewport:viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	if return_to_pen and app.tool.selected==3:app.tool.select(0)
	refresh()

func valid_context() -> bool:
	return not context.is_empty() and app.recovery_session==context.session and app.recovery_revision==context.revision and app.frame==context.frame and app.layers[app.active_layer].id==context.layer_id and app.mode.selected==0 and app.tool.selected==3 and source.selected==context.source and app.color.color==context.color and app.renderer.view_state()==context.view and not app.playing and not app.exporting and not app.navigating and not app.has_dialog(app) and not (app.home and app.home.visible) and (context.source!=0 or not app.physics_editor.is_running())

static func drawing_pixel(layers: Array,at: int,point: Vector2i,background: Image=null,raw_index: int=-1) -> Dictionary:
	var result:=Drawing.blank(1,1) if background==null else background.get_region(Rect2i(point,Vector2i.ONE))
	for i in range(layers.size()):
		var layer: Dictionary=layers[i]
		if raw_index>=0 and i!=raw_index:continue
		if raw_index<0 and not layer.visible:continue
		var cel:=Drawing.cel_at(layer,at)
		if cel.is_empty():continue
		var image: Image=cel.image
		if not Rect2i(Vector2i.ZERO,image.get_size()).has_point(point):continue
		var pixel:=image.get_region(Rect2i(point,Vector2i.ONE))
		if raw_index>=0:return {"color":pixel.get_pixel(0,0)}
		pixel=Drawing.faded(pixel,float(layer.get("opacity",1.0)));result.blend_rect(pixel,Rect2i(0,0,1,1),Vector2i.ZERO)
	var color:=result.get_pixel(0,0)
	return {} if color.a==0 else {"color":color}

func initialize_viewport() -> void:
	if viewport:return
	viewport=SubViewport.new();viewport.name="ColorSampleView";viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;add_child(viewport)
	camera=Camera3D.new();viewport.add_child(camera);camera.current=true

func start(point: Vector2) -> void:
	if app.mode.selected!=0 or app.tool.selected!=3 or app.playing or app.exporting or app.has_dialog(app) or (app.home and app.home.visible):return
	if not Rect2(Vector2.ZERO,Vector2(app.video.width,app.video.height)).has_point(point):return
	app.finish_stroke();app.fill_editor.cancel();cancel(false)
	if source.selected==0 and app.physics_editor.is_running():app.message("Freeze physics before picking a 3D color.");return
	var pixel:=Vector2i(point.floor())
	context={"session":app.recovery_session,"revision":app.recovery_revision,"frame":app.frame,"layer_id":app.layers[app.active_layer].id,"source":source.selected,"color":app.color.color,"view":app.renderer.view_state(),"point":pixel}
	refresh()
	if source.selected==0:
		initialize_viewport();viewport.size=Vector2i(app.video.width,app.video.height);viewport.world_3d=app.renderer.viewport.find_world_3d()
		var original: Camera3D=app.renderer.camera
		camera.global_transform=original.global_transform;camera.projection=original.projection;camera.keep_aspect=original.keep_aspect;camera.fov=original.fov;camera.size=original.size;camera.near=original.near;camera.far=original.far
		camera.h_offset=original.h_offset;camera.v_offset=original.v_offset;camera.frustum_offset=original.frustum_offset;camera.environment=original.environment;camera.attributes=original.attributes
		camera.cull_mask=original.cull_mask & ~Renderer.GUIDE_LAYER & ~(1<<19)
		viewport.render_target_update_mode=SubViewport.UPDATE_ONCE
		# An object-bound one-shot signal disconnects automatically on deletion.
		# Do not suspend a Node coroutine across app teardown.
		RenderingServer.frame_post_draw.connect(finish_capture,CONNECT_ONE_SHOT)
		return
	if not valid_context():cancel();return
	apply_result(drawing_pixel(app.layers,app.frame,pixel,null,app.active_layer if source.selected==2 else -1))

func finish_capture() -> void:
	if context.is_empty() or context.source!=0:return
	viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	if not valid_context():cancel();return
	var background:=viewport.get_texture().get_image();background.convert(Image.FORMAT_RGBA8);captures+=1
	apply_result(drawing_pixel(app.layers,app.frame,context.point,background))

func apply_result(result: Dictionary) -> void:
	var request:=context.duplicate();context={};refresh()
	if result.is_empty():app.message("No visible drawing color here. Choose another point or pick from View + drawings.");return
	var color: Color=result.color
	if color.a==0:app.message("This original pixel is transparent; drawing color kept.");return
	app.color.color=color;last_result={"color":color,"source":request.source,"point":request.point,"frame":request.frame};app.tool.select(0);refresh()
	app.message("Picked color from "+SOURCES[request.source]+". Pen is ready.")

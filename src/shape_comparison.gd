extends Node
# One disposable standard model, two snapshots, no suspended Node coroutine.
const Renderer=preload("res://src/renderer.gd")
const Model=preload("res://src/model.gd")
const Focus=preload("res://src/shape_comparison_bounds.gd")
var editor
var button: Button
var window: Window
var renderer: Node
var before_rect: TextureRect
var after_rect: TextureRect
var info: Label
var amount: SpinBox
var turn_left: Button
var turn_right: Button
var revision:=-1
var root_id:=0
var node_index:=-1
var target_index:=-1
var source_sha:=""
var row:={}
var phase:=0
var settling:=0
var direction:=Vector3.BACK
var up:=Vector3.UP
var before_image: Image
var after_image: Image
var focus:={}
var capture_camera: Transform3D

func setup(owner_editor,parent: Node) -> void:
	editor=owner_editor;button=editor.app.button(parent,"Compare without recording…",open)
	button.tooltip_text="Inspect neutral and changed geometry in an isolated preview. Your scene, keys and pending amount remain untouched."

func available() -> bool:
	return editor.actor()!=null and editor.shape_index>=0 and not editor.app.playing and not editor.app.exporting and not editor.app.pose_editor.contacts.live_busy() and editor.app.source_import.pid<=0 and editor.app.has_project.pid<=0

func valid() -> bool:
	var actor: RefCounted=editor.actor()
	return is_instance_valid(window) and window.visible and editor.panel.get_window().visible and actor!=null and is_instance_valid(actor.root) and actor.root.get_instance_id()==root_id and actor.data.sha256==source_sha and editor.app.recovery_revision==revision and editor.node_index==node_index and editor.shape_index==target_index and not editor.app.home.visible and available()

func open() -> void:
	if is_instance_valid(window):return
	if not available():editor.app.message("Select a control and stop live motion before comparing its geometry.");return
	var actor: RefCounted=editor.actor();root_id=actor.root.get_instance_id();revision=editor.app.recovery_revision;source_sha=actor.data.sha256;node_index=editor.node_index;target_index=editor.shape_index
	direction=editor.app.renderer.camera.global_basis.z.normalized();up=editor.app.renderer.camera.global_basis.y.normalized()
	window=Window.new();window.title="Compare deformation";window.theme=editor.app.theme;window.transient=true;window.exclusive=false;window.close_requested.connect(close);editor.app.add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var column:=VBoxContainer.new();panel.add_child(column)
	editor.app.label(column,str(editor.row().names[target_index]).left(100))
	var images:=HBoxContainer.new();images.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(images)
	for title in ["Neutral • all deforms off","Test • selected control only"]:
		var box:=VBoxContainer.new();box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;images.add_child(box);editor.app.label(box,title)
		var texture:=TextureRect.new();texture.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;texture.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;texture.custom_minimum_size=Vector2(280,240);texture.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(texture)
		if before_rect==null:before_rect=texture
		else:after_rect=texture
	info=editor.app.label(column,"Preparing an isolated neutral model…");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var controls:=HBoxContainer.new();column.add_child(controls);editor.app.label(controls,"Test amount")
	amount=SpinBox.new();amount.min_value=-1;amount.max_value=1;amount.step=.25;amount.value=1;amount.editable=false;controls.add_child(amount);amount.value_changed.connect(func(_value):render_pair())
	amount.tooltip_text="A mathematical POSITION test, not a declaration of the native control's valid range. No key is recorded."
	turn_left=editor.app.button(controls,"Turn left",func():turn(-45));turn_right=editor.app.button(controls,"Turn right",func():turn(45));editor.app.button(controls,"Close",close)
	turn_left.disabled=true;turn_right.disabled=true;phase=-1
	window.popup_centered(Vector2i(mini(940,maxi(640,int(editor.app.get_viewport_rect().size.x)-100)),mini(560,maxi(400,int(editor.app.get_viewport_rect().size.y)-100))))
	call_deferred("prepare")

func prepare() -> void:
	if not valid():close();return
	var actor: RefCounted=editor.actor()
	if FileAccess.get_sha256(actor.data.source)!=source_sha:fail("The source changed. Import it again before comparing.");return
	renderer=Renderer.new();add_child(renderer);renderer.setup(420,320);renderer.empty_environment=false;renderer.editor_grid.visible=false;renderer.video_settings={"lighting_mode":"unshaded"}
	var definition:=Model.definition(actor.data.source)
	definition.metadata={"source_shape":{"format":"studio_source_shape_2","enabled":false,"overrides":{str(node_index):{str(target_index):0.}}}}
	var prepared: Dictionary=renderer.prepare_model(definition)
	if prepared.has("error"):fail(prepared.error);return
	var basis: Basis=actor.root.global_basis.orthonormalized()*prepared.model.base_root.basis.orthonormalized().inverse()
	var q:=basis.get_rotation_quaternion();prepared.model.data.rotation_xyzw=[q.x,q.y,q.z,q.w]
	renderer.install_model(prepared);renderer.model.apply(0,false,true,renderer.video_settings)
	for candidate in renderer.model.root.get_meta(Model.Shape.META).rows:
		if int(candidate.node)==node_index:row=candidate;break
	if row.is_empty() or target_index>=row.names.size():fail("The comparison does not match the selected source control.");return
	if str(row.names[target_index])!=str(editor.row().names[target_index]):fail("The native control identity changed.");return
	phase=0
	render_pair()

func render_pair() -> void:
	if phase!=0 or not valid() or not is_instance_valid(renderer) or row.is_empty():return
	focus=Focus.query(row,target_index,amount.value)
	if not focus.error.is_empty():fail(focus.error);return
	var bounds: AABB=focus.bounds;var radius:=maxf(bounds.size.length()*.5,.005)
	renderer.camera.fov=35;renderer.camera.near=maxf(radius*.01,.00001);renderer.camera.far=maxf(radius*20,10.)
	var distance:=radius/sin(deg_to_rad(renderer.camera.fov*.5))*1.12
	renderer.camera.position=bounds.get_center()+direction*distance;renderer.camera.look_at(bounds.get_center(),up);capture_camera=renderer.camera.transform
	renderer.model.data.metadata.source_shape.overrides[str(node_index)][str(target_index)]=0.
	renderer.model.apply(0,false,true,renderer.video_settings)
	phase=1;settling=2;amount.editable=false;turn_left.disabled=true;turn_right.disabled=true;info.text="Rendering the same view before and after…"
	schedule()

func schedule() -> void:
	if RenderingServer.frame_post_draw.is_connected(rendered):RenderingServer.frame_post_draw.disconnect(rendered)
	renderer.viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	RenderingServer.frame_post_draw.connect(rendered,CONNECT_ONE_SHOT)

func rendered() -> void:
	if RenderingServer.frame_post_draw.is_connected(rendered):RenderingServer.frame_post_draw.disconnect(rendered)
	if not valid() or not is_instance_valid(renderer):close();return
	settling-=1
	if settling>0:schedule();return
	var image: Image=renderer.viewport.get_texture().get_image();image.convert(Image.FORMAT_RGBA8)
	if phase==1:
		before_image=image;before_rect.texture=ImageTexture.create_from_image(image)
		renderer.model.data.metadata.source_shape.overrides[str(node_index)][str(target_index)]=amount.value
		renderer.model.apply(0,false,true,renderer.video_settings);phase=2;settling=2;schedule()
	elif phase==2:
		after_image=image;after_rect.texture=ImageTexture.create_from_image(image);renderer.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
		phase=0;amount.editable=true;turn_left.disabled=false;turn_right.disabled=false
		info.text=str(int(focus.moved))+" moved vertices • neutral pose • amount "+String.num(amount.value,2)+".\nSame camera, all other deforms off. Original scene and pending edits are untouched. Native shading and non-position effects may differ."

func turn(degrees: float) -> void:
	if phase!=0:return
	direction=direction.rotated(up,deg_to_rad(degrees)).normalized();render_pair()

func fail(message: String) -> void:
	phase=0;info.text=message;amount.editable=false;turn_left.disabled=true;turn_right.disabled=true
	if is_instance_valid(renderer):renderer.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED

func _process(_delta: float) -> void:
	if not is_instance_valid(editor):return
	button.disabled=not available() or is_instance_valid(window)
	if is_instance_valid(window) and not valid():close()

func cleanup() -> void:
	if RenderingServer.frame_post_draw.is_connected(rendered):RenderingServer.frame_post_draw.disconnect(rendered)
	phase=0;row={};before_image=null;after_image=null;before_rect=null;after_rect=null
	if is_instance_valid(renderer):
		renderer.camera.current=false;renderer.viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED;renderer.viewport.world_3d=null

func close() -> void:
	cleanup()
	if is_instance_valid(renderer):renderer.queue_free()
	renderer=null
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null

func _exit_tree() -> void:
	cleanup()
	if is_instance_valid(window):window.hide();window.queue_free()

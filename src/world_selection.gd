extends Node
# Editor-only ID rendering shares meshes/skins, never source materials or save data.
const MASK_LAYER := 1 << 19
var app
var tree: Tree
var items := {}
var selected := ""
var signature := ""
var entries: Array = []
var copies_root: Node3D
var viewport: SubViewport
var camera: Camera3D
var outline: TextureRect
var outline_material: ShaderMaterial
var menu: PopupMenu
var pending_button := 0
var pending_motion := Vector2.ZERO
var serial := 0
var updating_tree := false
var picking := 0
var colors := {}
var boundaries := {}

func setup(parent: Node) -> void:
	app.label(parent,"World")
	tree = Tree.new()
	tree.custom_minimum_size = Vector2(156,150)
	tree.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tree.hide_root = false
	var font := SystemFont.new();font.font_names=PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"])
	tree.add_theme_font_override("font",font)
	tree.item_selected.connect(func():
		var item := tree.get_selected()
		if not updating_tree and item and item.get_metadata(0) is String: select_entity(item.get_metadata(0)))
	parent.add_child(tree)
	app.button(parent,"Frame selected",frame_selected).tooltip_text = "Find the selected map or model without changing shot keys."
	app.button(parent,"Save asset .has...",func():preload("res://src/asset_package.gd").export_dialog(app)).tooltip_text="Package the selected independent model or map with its editable controls and embedded dependencies."
	app.button(parent,"Size map…",func():app.map_calibration.open()).tooltip_text="Use two map surfaces a known distance apart; review against a six-foot guide."
	app.label(parent,"Click an object to select.\nRight-click empty space\nto deselect.").add_theme_font_size_override("font_size",12)

func initialize_mask() -> void:
	copies_root = Node3D.new(); copies_root.name = "EditorOnlySelection"
	app.renderer.world.add_child(copies_root)
	app.renderer.camera.set_cull_mask_value(20,false)
	viewport = SubViewport.new(); viewport.size = Vector2i(960,540)
	viewport.world_3d = app.renderer.viewport.find_world_3d()
	viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(viewport)
	camera = Camera3D.new(); camera.cull_mask = MASK_LAYER
	camera.environment = Environment.new()
	camera.environment.background_mode = Environment.BG_COLOR
	camera.environment.background_color = Color.BLACK
	viewport.add_child(camera); camera.current = true
	outline = TextureRect.new(); outline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Interpolating distinct ID colors can create another object's ID at an edge.
	outline.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	outline.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	outline.texture = viewport.get_texture()
	outline_material = ShaderMaterial.new()
	outline_material.shader = preload("res://src/selection_outline.gdshader")
	outline.material = outline_material; outline.visible = false
	app.canvas.add_child(outline)
	menu = PopupMenu.new(); app.add_child(menu)
	menu.id_pressed.connect(context_action)
	app.renderer.assets_changed.connect(func(): call_deferred("refresh"))
	refresh()

func entity_root(kind: String) -> Node3D:
	if app.renderer.world_runtime:
		var instance: RefCounted=app.renderer.world_runtime.instance(kind)
		return instance.root if instance else null
	if kind == "model": return app.renderer.model.root if app.renderer.model else null
	if kind == "scene": return app.renderer.environment_scene
	return null

func selected_rig() -> RefCounted:
	return app.renderer.active_model()

func color_for(id: String) -> Vector3:
	return colors.get(id,Vector3.ZERO)

func entity_rows() -> Array:
	var rows:=[]
	if app.renderer.world_runtime:
		for id in app.renderer.world_runtime.order:
			var instance: RefCounted=app.renderer.world_runtime.instance(id)
			rows.append({"id":id,"parent_id":instance.data.parent_id,"name":instance.data.name,"node":instance.root})
	else:
		for id in ["scene","model"]:
			var node:=entity_root(id)
			if node==null or id=="scene" and app.renderer.empty_environment:continue
			rows.append({"id":id,"parent_id":"","name":"Environment" if id=="scene" else app.renderer.model.data.name,"node":node})
	return rows

func belongs_to(id: String, ancestor: String) -> bool:
	if ancestor.is_empty():return false
	while not id.is_empty():
		if id==ancestor:return true
		if not app.renderer.world_runtime:return false
		id=app.renderer.world_runtime.instance(id).data.parent_id
	return false

func refresh() -> void:
	var scene: Node3D = entity_root("scene")
	var model: Node3D = entity_root("model")
	var next := str(app.renderer.world_runtime.root.get_instance_id()) if app.renderer.world_runtime else "%d/%d" % [scene.get_instance_id() if scene else 0,model.get_instance_id() if model else 0]
	if signature == next: return
	signature = next; serial += 1
	selected = ""; cancel_gesture()
	for entry in entries:
		if is_instance_valid(entry.copy): entry.copy.free()
	entries.clear(); items.clear(); colors.clear();boundaries.clear();tree.clear()
	var root_item := tree.create_item(); root_item.set_text(0,"World"); root_item.set_selectable(0,false)
	var rows:=entity_rows()
	for row in rows:boundaries[row.node.get_instance_id()]=row.id
	for i in range(rows.size()):
		var row: Dictionary=rows[i];var kind: String=row.id
		var levels:=[0.15,0.4,0.65,0.9]
		colors[kind]=Vector3(levels[i%4],levels[(i/4)%4],levels[(i/16)%4]) if app.renderer.world_runtime else Vector3(1,0,0) if kind=="model" else Vector3(0,1,0)
		var item := tree.create_item(items.get(row.parent_id,root_item)); item.set_metadata(0,kind)
		item.set_text(0,row.name)
		item.set_tooltip_text(0,row.name); items[kind] = item
		collect(row.node,kind)
	if app.renderer.world_runtime and not app.renderer.world_runtime.data.get("effects",[]).is_empty():
		var effects_item:=tree.create_item(root_item);effects_item.set_text(0,"Effects");effects_item.set_selectable(0,false)
		for effect in app.renderer.world_runtime.data.effects:
			var item:=tree.create_item(effects_item);item.set_text(0,effect.name);item.set_metadata(0,"effect:"+effect.id);item.set_tooltip_text(0,"Edit placement and timing")
	if app.renderer.world_runtime:
		app.renderer.select_instance("");app.pose_editor.rebuild_tree();app.pose_editor.update_gizmo();app.refresh_timeline()
	elif app.mode.selected == 2 and model: select_entity("model",false)
	elif app.mode.selected == 2: select_entity("")

func authored_material(mesh: MeshInstance3D,surface: int,kind: String) -> Material:
	var opacity: RefCounted
	if app.renderer.world_runtime:
		var rig: RefCounted=app.renderer.world_runtime.instance(kind)
		opacity=rig.opacity_materials if rig else null
	elif kind=="model" and app.renderer.model:opacity=app.renderer.model.opacity_materials
	else:opacity=app.renderer.legacy_materials
	return opacity.authored_material(mesh,surface) if opacity else mesh.get_active_material(surface)

func collect(node: Node, kind: String) -> void:
	if node!=entity_root(kind) and boundaries.has(node.get_instance_id()):return
	if node is MeshInstance3D and node.mesh:
		var copy := MeshInstance3D.new()
		copy.mesh = node.mesh; copy.skin = node.skin; copy.layers = MASK_LAYER
		copy.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		copies_root.add_child(copy)
		var skeleton := node.get_node_or_null(node.skeleton)
		if skeleton is Skeleton3D: copy.skeleton = copy.get_path_to(skeleton)
		for surface in range(node.mesh.get_surface_count()):
			var material := ShaderMaterial.new(); material.shader = preload("res://src/selection_id.gdshader")
			material.set_shader_parameter("object_color",color_for(kind))
			var original: Material = authored_material(node,surface,kind)
			if original is BaseMaterial3D and original.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
				material.set_shader_parameter("use_alpha",true)
				material.set_shader_parameter("opacity",original.albedo_color.a)
				var texture: Texture2D = original.get_texture(BaseMaterial3D.TEXTURE_ALBEDO)
				if texture: material.set_shader_parameter("alpha_texture",texture)
			copy.set_surface_override_material(surface,material)
		var materials: Array = []
		for surface in range(node.mesh.get_surface_count()): materials.append(copy.get_surface_override_material(surface))
		entries.append({"original":node,"copy":copy,"kind":kind,"materials":materials,"ghost_materials":[],"ghost":false,"color":color_for(kind)})
	for child in node.get_children(): collect(child,kind)

func _process(_delta: float) -> void:
	if viewport == null: return
	if pending_button!=0:
		for key in [KEY_W,KEY_A,KEY_S,KEY_D,KEY_Q,KEY_E]:
			if Input.is_physical_key_pressed(key):
				app.camera_button(pending_button,true);cancel_gesture();break
	var current: Camera3D = app.renderer.camera
	camera.transform = current.transform; camera.fov = current.fov
	camera.near = current.near; camera.far = current.far; camera.keep_aspect = current.keep_aspect
	camera.projection = current.projection; camera.size = current.size
	for entry in entries:
		if not is_instance_valid(entry.original): continue
		entry.copy.global_transform = entry.original.global_transform
		entry.copy.custom_aabb=entry.original.custom_aabb
		var root: Node3D = entity_root(entry.kind)
		var family:=belongs_to(entry.kind,selected)
		var ghost: bool = family and root!=null and not root.is_visible_in_tree()
		var color:=color_for(selected) if family and picking==0 else color_for(entry.kind)
		entry.copy.visible = entry.original.is_visible_in_tree() or ghost
		if ghost!=entry.ghost:
			if ghost and entry.ghost_materials.is_empty():
				for source in entry.materials:
					var material := ShaderMaterial.new(); material.shader=preload("res://src/selection_ghost.gdshader"); material.render_priority=127
					for key in ["object_color","use_alpha","opacity","alpha_texture"]: material.set_shader_parameter(key,source.get_shader_parameter(key))
					entry.ghost_materials.append(material)
			var materials: Array = entry.ghost_materials if ghost else entry.materials
			for surface in range(materials.size()):entry.copy.set_surface_override_material(surface,materials[surface])
			entry.ghost=ghost
		if entry.color!=color:
			for material in entry.materials+entry.ghost_materials:material.set_shader_parameter("object_color",color)
			entry.color=color
		for i in range(entry.original.get_blend_shape_count()): entry.copy.set_blend_shape_value(i,entry.original.get_blend_shape_value(i))
	outline.position = app.canvas.image_rect().position; outline.size = app.canvas.image_rect().size
	outline.visible = not selected.is_empty() and not app.exporting
	if outline.visible:
		outline_material.set_shader_parameter("object_color",color_for(selected))
		var node := entity_root(selected)
		outline_material.set_shader_parameter("ghost",node!=null and not node.is_visible_in_tree())
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS if outline.visible or pending_button!=0 or picking>0 else SubViewport.UPDATE_DISABLED
	if app.renderer.world_runtime:
		for id in items:
			var instance: RefCounted=app.renderer.world_runtime.instance(id)
			var name: String=instance.data.name+(" (hidden)" if not instance.root.is_visible_in_tree() else "")
			if items[id].get_text(0)!=name:items[id].set_text(0,name)
	elif items.has("model") and app.renderer.model:
		var name: String = str(app.renderer.model.data.name) + (" (hidden)" if not app.renderer.model.data.visible else "")
		if items.model.get_text(0)!=name: items.model.set_text(0,name)

func select_entity(kind: String, change_workspace := true) -> void:
	if kind.begins_with("effect:"):
		app.particle_editor.open();app.particle_editor.select_id(kind.substr(7));return
	if not kind.is_empty() and not items.has(kind): return
	app.pose_editor.finish_drag()
	var previous:=selected
	serial += 1; selected = kind; cancel_gesture()
	if app.renderer.world_runtime:
		app.renderer.select_instance(kind)
		if previous!=kind:app.pose_editor.selected="@root"
		app.pose_editor.rebuild_tree();app.pose_editor.apply_frame();app.refresh_timeline()
	updating_tree = true
	if kind.is_empty(): tree.deselect_all()
	elif tree.get_selected()!=items[kind]: items[kind].select(0)
	updating_tree = false
	if change_workspace:
		var view: Dictionary=app.renderer.view_state()
		var next := 2 if kind=="model" or app.renderer.world_runtime and not kind.is_empty() else 1
		app.mode.select(next); app.change_mode(next)
		app.renderer.restore_view(view)

func clear() -> void:
	select_entity("",false)
	if is_instance_valid(menu): menu.hide()

func frame_selected() -> void:
	var node := entity_root(selected)
	if node:
		if not app.renderer.frame_scene(node):app.message(app.renderer.last_framing.get("error","No mesh geometry to frame."))
		elif app.renderer.last_framing.conservative>0:app.message("Framed with extra space for a large model.")
	else: app.message("Select an object in the world or hierarchy first.")

func cancel_gesture(invalidate := false) -> void:
	if invalidate: serial += 1
	pending_button = 0; pending_motion = Vector2.ZERO

func input(event: InputEvent, point: Vector2) -> void:
	if event is InputEventMouseButton:
		var index: int = event.button_index
		if index not in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT,MOUSE_BUTTON_MIDDLE]: return
		if event.pressed:
			serial += 1
			if index==MOUSE_BUTTON_MIDDLE or event.ctrl_pressed or app.navigating:
				cancel_gesture(); app.camera_button(index,true,event.ctrl_pressed)
			elif pending_button!=0 and pending_button!=index:
				app.camera_button(pending_button,true); app.camera_button(index,true); cancel_gesture()
			else: pending_button=index; pending_motion=Vector2.ZERO
		else:
			if pending_button==index:
				cancel_gesture(); choose_at(point,index==MOUSE_BUTTON_RIGHT)
			elif app.camera_buttons!=0: app.camera_button(index,false)
	elif event is InputEventMouseMotion:
		if pending_button!=0:
			pending_motion+=event.relative
			if pending_motion.length()>=4:
				var delta := pending_motion; app.camera_button(pending_button,true); cancel_gesture(); app.camera_motion(delta)
		elif app.navigating: app.camera_motion(event.relative)

func choose_at(point: Vector2, context := false) -> void:
	serial += 1; var request := serial
	if not Rect2(0,0,app.video.width,app.video.height).has_point(point): return
	picking += 1
	_process(0); viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	picking -= 1
	if request!=serial or app.exporting or app.playing or app.navigating or pending_button!=0 or app.mode.selected==0: return
	var image := viewport.get_texture().get_image()
	var pixel := image.get_pixel(clampi(int(point.x/2),0,959),clampi(int(point.y/2),0,539))
	var kind := ""
	var nearest:=0.015
	var rgb:=Vector3(pixel.r,pixel.g,pixel.b)
	for id in colors:
		var distance:=rgb.distance_squared_to(color_for(id))
		if distance<nearest:nearest=distance;kind=id
	select_entity(kind)
	if context and not kind.is_empty():
		menu.clear(); menu.add_item("Frame selected",0)
		if selected_rig() and (kind=="model" or app.renderer.world_runtime):
			menu.add_item("Reset pose",1)
			menu.add_item("Hide object" if selected_rig().visible_at(app.frame) else "Show object",2)
		menu.add_separator(); menu.add_item("Deselect",3)
		var rect: Rect2 = app.canvas.image_rect()
		var position: Vector2 = app.canvas.global_position+rect.position+point/Vector2(app.video.width,app.video.height)*rect.size
		menu.position = app.get_window().position+Vector2i(position)
		menu.popup()

func context_action(id: int) -> void:
	menu.hide()
	match id:
		0: frame_selected()
		1:
			if not selected_rig(): return
			var before: Dictionary = selected_rig().data.duplicate(true)
			app.pose_editor.begin_draft(); selected_rig().data.pose={}; app.pose_editor.commit(before,true)
		2:
			if selected_rig(): app.pose_editor.set_visibility_key(not selected_rig().visible_at(app.frame))
		3: select_entity("")

extends Node
# Editor-only ID rendering shares meshes/skins, never source materials or save data.
const MASK_LAYER := 1 << 19
class PickRequest extends RefCounted:
	var receiver: WeakRef
	var data: Dictionary
	func complete() -> void:
		var keep_alive: RefCounted=self
		var target=receiver.get_ref()
		if target:target.complete_pick(keep_alive)
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
var pending_cursor := Vector2.ZERO
var serial := 0
var updating_tree := false
var picking := 0
var pick_requests: Dictionary = {}
var colors := {}
var boundaries := {}
# Neon Pro step 3: World icon rail (narrow dock) / list (wide dock). The rail mirrors the Tree rows;
# the Tree stays the source of truth for selection and only hides while the rail shows.
const StudioTheme = preload("res://src/studio_theme.gd")
const HELP := "Click an object to select.\nRight-click empty space\nto deselect."
var rail: VBoxContainer
var rail_tiles := {}
var rail_mode := false
var actions: Array = []
var help_label: Label
var rail_divider: Control
var rail_end: Control
var rail_ui_active := false

func _enter_tree() -> void:
	rail_ui_active = true

func setup(parent: Node) -> void:
	app.label(parent,"World")
	rail = VBoxContainer.new(); rail.name = "WorldRail"
	rail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rail.add_theme_constant_override("separation",6)
	rail.mouse_filter = Control.MOUSE_FILTER_PASS; rail.tooltip_text = HELP.replace("\n"," ")
	rail.visible = false
	parent.add_child(rail)
	tree = Tree.new()
	tree.custom_minimum_size = Vector2(156,150)
	tree.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tree.hide_root = false
	tree.add_theme_font_override("font",tree_font())
	tree.item_selected.connect(func():
		var item := tree.get_selected()
		if not updating_tree and item and item.get_metadata(0) is String: select_entity(item.get_metadata(0)))
	parent.add_child(tree)
	rail_divider = CenterContainer.new(); rail_divider.mouse_filter = Control.MOUSE_FILTER_IGNORE; rail_divider.visible = false
	var line := ColorRect.new(); line.color = StudioTheme.LINE2; line.custom_minimum_size = Vector2(28,1); line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rail_divider.add_child(line); parent.add_child(rail_divider)
	var frame: Button = app.button(parent,"Frame selected",frame_selected); frame.tooltip_text = "Find the selected map or model without changing shot keys."
	frame.set_meta("rail",["Frame","frame-target"])
	var asset: Button = app.button(parent,"Save asset .has...",func():preload("res://src/asset_package.gd").export_dialog(app)); asset.tooltip_text="Package the selected independent model or map with its editable controls and embedded dependencies."
	asset.set_meta("rail",["Save asset .has...","save","Save asset"])
	var size_map: Button = app.button(parent,"Size map…",func():app.map_calibration.open()); size_map.tooltip_text="Use two map surfaces a known distance apart; review against a six-foot guide."
	size_map.set_meta("rail",["Size map…","ruler","Size map"])
	actions = [frame,asset,size_map]
	help_label = app.label(parent,HELP); help_label.add_theme_font_size_override("font_size",12)
	rail_end = Control.new(); rail_end.custom_minimum_size.y = 4; rail_end.mouse_filter = Control.MOUSE_FILTER_IGNORE; rail_end.visible = false
	parent.add_child(rail_end)
	set_rail(StudioTheme.is_neon(), true)

func tree_font() -> Font:
	# Neon: the interface font, with Yu Gothic UI kept as the fallback for Japanese object names.
	# Retain both original profiles so docking reuses the same Font resources.
	var neon := StudioTheme.is_neon()
	var key := "world_tree_neon" if neon else "world_tree_classic"
	if StudioTheme.fonts.has(key): return StudioTheme.fonts[key]
	var japanese := SystemFont.new(); japanese.font_names = PackedStringArray(["Yu Gothic UI","Segoe UI","Arial"])
	if not neon:
		StudioTheme.fonts[key] = japanese
		return japanese
	var font := SystemFont.new(); font.font_names = PackedStringArray(StudioTheme.UI_FONTS); font.font_weight = 500
	font.fallbacks = [japanese]
	StudioTheme.fonts[key] = font
	return font

func style_tile(control: Button, kind: String, tile: bool) -> void:
	# Rail tile: 52x56, r8, 18 px icon (#8C93A3) over an 11/500 #B4BAC7 label, hover #1D2029, selected
	# #171A21 + 1 px #2C303B with a white icon and label. List mode: full-width outline button.
	var neon := StudioTheme.is_neon()
	control.theme_type_variation = "RailTile" if tile else ""
	control.custom_minimum_size = Vector2(52,56) if tile else Vector2.ZERO
	control.size_flags_horizontal = Control.SIZE_SHRINK_CENTER if tile else Control.SIZE_FILL
	control.icon = StudioTheme.icon(kind,Color.WHITE,18 if tile else 16) if neon else null
	control.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER if tile else HORIZONTAL_ALIGNMENT_LEFT
	control.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP if tile else VERTICAL_ALIGNMENT_CENTER
	control.alignment = HORIZONTAL_ALIGNMENT_CENTER if tile or not neon else HORIZONTAL_ALIGNMENT_LEFT
	for name in ["font_hover_color","font_pressed_color","font_hover_pressed_color","font_focus_color","font_disabled_color"]: control.remove_theme_color_override(name)
	if not neon:
		for name in ["icon_max_width","h_separation"]: control.remove_theme_constant_override(name)
		for name in ["font_color","icon_normal_color","icon_hover_color","icon_pressed_color","icon_hover_pressed_color","icon_focus_color"]: control.remove_theme_color_override(name)
		control.remove_theme_font_override("font"); control.autowrap_mode = TextServer.AUTOWRAP_OFF
		return
	control.add_theme_constant_override("icon_max_width",18 if tile else 16)
	control.add_theme_constant_override("h_separation",5 if tile else 8)
	control.add_theme_font_override("font",StudioTheme.font(500))
	# Words wrap so a long action label never widens the dock (list mode only exists from 140 px).
	control.autowrap_mode = TextServer.AUTOWRAP_WORD
	control.add_theme_color_override("font_color",StudioTheme.TEXT2 if tile else StudioTheme.TEXT)
	control.add_theme_color_override("icon_normal_color",StudioTheme.TEXT3 if tile else StudioTheme.TEXT2)
	control.add_theme_color_override("icon_focus_color",StudioTheme.TEXT3 if tile else StudioTheme.TEXT2)
	control.add_theme_color_override("icon_hover_color",StudioTheme.TEXT)
	control.add_theme_color_override("icon_pressed_color",Color.WHITE)
	control.add_theme_color_override("icon_hover_pressed_color",Color.WHITE)

func style_action(control: Button, kind: String, tile: bool) -> void:
	# Frame / Save asset / Size map. As rail tiles their (exact) text wraps under the icon in a face
	# drawn by child controls: Button autowrap does not wrap correctly under a top icon, so the
	# button's own text is clipped and transparent there while staying the real control text.
	style_tile(control,kind,tile)
	var face: VBoxContainer = control.get_node_or_null("TileFace")
	var neon := StudioTheme.is_neon()
	control.clip_text = tile and neon
	if face: face.visible = tile and neon
	if not (tile and neon): return
	control.icon = null
	# Neon Simple: Save asset / Size map (rail meta with a short name) are 40 px icon-only tiles under
	# Frame, which keeps its caption as in the mock; names stay in the tooltip, texts are unchanged.
	var rail_meta: Array = control.get_meta("rail", [])
	var icon_only: bool = rail_meta.size() > 2 and app != null and not app.advanced_mode
	for name in ["font_color","font_hover_color","font_pressed_color","font_hover_pressed_color","font_focus_color","font_disabled_color"]:
		control.add_theme_color_override(name,Color.TRANSPARENT)
	if face == null:
		face = VBoxContainer.new(); face.name = "TileFace"; face.mouse_filter = Control.MOUSE_FILTER_IGNORE
		face.alignment = BoxContainer.ALIGNMENT_CENTER; face.add_theme_constant_override("separation",5)
		var picture := TextureRect.new(); picture.name = "Icon"; picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
		picture.size_flags_horizontal = Control.SIZE_SHRINK_CENTER; picture.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		face.add_child(picture)
		var caption := Label.new(); caption.name = "Caption"; caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
		caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; caption.autowrap_mode = TextServer.AUTOWRAP_WORD
		caption.add_theme_font_size_override("font_size",11); caption.add_theme_constant_override("line_spacing",0)
		face.add_child(caption)
		control.add_child(face); face.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); face.offset_top = 6; face.offset_bottom = -6; face.offset_left = 2; face.offset_right = -2
		control.mouse_entered.connect(func(): tile_face_color(control,true))
		control.mouse_exited.connect(func(): tile_face_color(control,false))
	var caption: Label = face.get_node("Caption")
	# The visible tile caption is a short name (rail meta entry 3, e.g. "Save asset"), so it wraps to
	# two lines like the other tiles; the button text stays Codex's exact "Save asset .has..." (tests
	# find it by that text) and the full name is in the tooltip.
	var rail: Array = control.get_meta("rail", [])
	caption.text = str(rail[2]) if rail.size() > 2 else control.text
	if rail.size() > 2 and not control.tooltip_text.begins_with(control.text): control.tooltip_text = control.text + "\n" + control.tooltip_text
	caption.add_theme_font_override("font",StudioTheme.font(500))
	caption.visible = not icon_only
	var lines := StudioTheme.font(500).get_multiline_string_size(caption.text,HORIZONTAL_ALIGNMENT_CENTER,48,11,-1,TextServer.BREAK_MANDATORY|TextServer.BREAK_WORD_BOUND).y
	control.custom_minimum_size.y = 40.0 if icon_only else maxf(56,ceilf(12+18+5+lines))
	tile_face_color(control,false)

func refresh_actions() -> void:
	# Simple / Advanced switch: restyle the Frame / Save asset / Size map tiles (captions follow the mode).
	for control in actions:
		var meta: Array = control.get_meta("rail", [])
		if meta.size() > 1: style_action(control,meta[1],rail_mode)

func tile_face_color(control: Button, hover: bool) -> void:
	var face := control.get_node_or_null("TileFace")
	if face == null: return
	face.get_node("Caption").add_theme_color_override("font_color",StudioTheme.TEXT if hover else StudioTheme.TEXT2)
	face.get_node("Icon").texture = StudioTheme.icon(str(control.get_meta("rail")[1]),StudioTheme.TEXT if hover else StudioTheme.TEXT3,18)

func entity_tile(id: String, text: String, kind: String) -> Button:
	var tile := Button.new(); tile.focus_mode = Control.FOCUS_NONE
	tile.text = text; tile.tooltip_text = text; tile.set_meta("kind",kind)
	style_tile(tile,kind,true)
	tile.autowrap_mode = TextServer.AUTOWRAP_OFF; tile.clip_text = true
	tile.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	if not id.begins_with("effect:"):
		tile.toggle_mode = true
		# 2 px vertical neon bar on the rail edge (6 px left of the tile), inset 10, pink glow.
		var bar := Control.new(); bar.name = "SelectedBar"; bar.mouse_filter = Control.MOUSE_FILTER_IGNORE; bar.visible = false
		tile.add_child(bar)
		bar.anchor_top = 0; bar.anchor_bottom = 1; bar.offset_left = -6; bar.offset_right = -4; bar.offset_top = 10; bar.offset_bottom = -10
		var glow := Panel.new(); glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		glow.add_theme_stylebox_override("panel",StudioTheme.flat(Color(1,0.239,0.604,0),Color.TRANSPARENT,1,0,Vector4(0,0,0,0),Color(1,0.239,0.604,0.6),4))
		bar.add_child(glow); glow.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		var line := TextureRect.new(); line.texture = StudioTheme.neon_bar(); line.mouse_filter = Control.MOUSE_FILTER_IGNORE
		line.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; line.stretch_mode = TextureRect.STRETCH_SCALE
		bar.add_child(line); line.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tile.pressed.connect(func():
		if id != selected: select_entity(id)
		sync_rail())
	rail.add_child(tile); rail_tiles[id] = tile
	return tile

func tile_kind(id: String) -> String:
	if id.begins_with("effect:"): return "sparkle"
	var kind := "environment" if id == "scene" else "model"
	if app.renderer.world_runtime:
		var instance: RefCounted = app.renderer.world_runtime.instance(id)
		kind = str(instance.data.get("kind","")) if instance else ""
	return {"environment":"building","model":"runner"}.get(kind,"box")

func rebuild_rail(rows: Array) -> void:
	# Built from the same rows as the Tree; never selects anything while building.
	for tile in rail_tiles.values():
		if is_instance_valid(tile): rail.remove_child(tile); tile.queue_free()
	rail_tiles.clear()
	for row in rows: entity_tile(row.id,str(row.name),tile_kind(row.id))
	if app.renderer.world_runtime:
		for effect in app.renderer.world_runtime.data.get("effects",[]):
			entity_tile("effect:"+str(effect.id),str(effect.name),"sparkle").tooltip_text = str(effect.name)+": edit placement and timing"
	sync_rail()

func sync_rail() -> void:
	for id in rail_tiles:
		var tile: Button = rail_tiles[id]
		if not tile.toggle_mode: continue
		var on: bool = id == selected
		if tile.button_pressed != on: tile.set_pressed_no_signal(on)
		var bar := tile.get_node_or_null("SelectedBar")
		if bar: bar.visible = on
		tile.add_theme_font_override("font",StudioTheme.font(600 if on else 500))
		tile.add_theme_color_override("font_color",Color.WHITE if on else StudioTheme.TEXT2)

func set_rail(on: bool, force := false) -> bool:
	# A dock resize may be delivered while its owner or Tree is leaving the scene.
	if not rail_ui_active or not is_inside_tree() or is_queued_for_deletion() or not is_instance_valid(app) or not app.is_inside_tree() or app.is_queued_for_deletion(): return false
	if not is_instance_valid(tree) or not tree.is_inside_tree() or tree.is_queued_for_deletion(): return false
	var holder: Control = tree.get_parent()
	for control in [holder,rail,rail_divider,rail_end,help_label] + actions:
		if not is_instance_valid(control) or not control.is_inside_tree() or control.is_queued_for_deletion(): return false
	# Rail: tiles + spacer + divider + Frame / Save asset / Size map tiles, help text as the rail tooltip.
	# List: full-width Tree, full-width buttons and the help label. Visibility and texts only.
	if on == rail_mode and not force: return true
	rail_mode = on
	var neon := StudioTheme.is_neon()
	holder.custom_minimum_size.x = 64 if neon else 156
	holder.add_theme_constant_override("separation",6 if on else 7)
	tree.custom_minimum_size.x = 0 if neon else 156
	tree.visible = not on
	rail.visible = on; rail_divider.visible = on; rail_end.visible = on
	help_label.visible = not on
	help_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if neon else TextServer.AUTOWRAP_OFF
	if neon: help_label.add_theme_color_override("font_color",StudioTheme.TEXT2)
	else: help_label.remove_theme_color_override("font_color")
	if neon:
		tree.add_theme_stylebox_override("panel",StudioTheme.flat(StudioTheme.BAR,Color.TRANSPARENT,0,0,Vector4(4,4,4,4)))
		tree.add_theme_constant_override("v_separation",6)
	else:
		tree.remove_theme_stylebox_override("panel"); tree.remove_theme_constant_override("v_separation")
	tree.add_theme_font_override("font",tree_font())
	for control in actions:
		var meta: Array = control.get_meta("rail")
		control.text = meta[0] if on else str({"Frame":"Frame selected"}.get(meta[0],meta[0]))
		style_action(control,meta[1],on)
	if force:
		for tile in rail_tiles.values():
			style_tile(tile,str(tile.get_meta("kind")),true); tile.autowrap_mode = TextServer.AUTOWRAP_OFF
		sync_rail()
	return true

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
	rebuild_rail(rows)
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
				app.camera_button(pending_button,true,false,pending_cursor);cancel_gesture();break
	var current: Camera3D = app.scene_view.display_camera()
	var extent: Vector2i=app.scene_view.viewport.size if app.canvas.scene_setup else app.renderer.viewport.size/2
	if viewport.size!=extent:viewport.size=extent
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
	outline.position = app.canvas.scene_rect().position; outline.size = app.canvas.scene_rect().size
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
			if rail_tiles.has(id) and rail_tiles[id].tooltip_text!=name:rail_tiles[id].tooltip_text=name;rail_tiles[id].text=instance.data.name
	elif items.has("model") and app.renderer.model:
		var name: String = str(app.renderer.model.data.name) + (" (hidden)" if not app.renderer.model.data.visible else "")
		if items.model.get_text(0)!=name: items.model.set_text(0,name)
		if rail_tiles.has("model") and rail_tiles.model.tooltip_text!=name: rail_tiles.model.tooltip_text=name;rail_tiles.model.text=str(app.renderer.model.data.name)

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
	sync_rail()
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
				app.camera_button(pending_button,true,false,pending_cursor); app.camera_button(index,true); cancel_gesture()
			else: pending_button=index; pending_motion=Vector2.ZERO;pending_cursor=app.get_viewport().get_mouse_position()
		else:
			if pending_button==index:
				cancel_gesture(); choose_at(point,index==MOUSE_BUTTON_RIGHT)
			elif app.camera_buttons!=0: app.camera_button(index,false)
	elif event is InputEventMouseMotion:
		if pending_button!=0:
			pending_motion+=event.relative
			if pending_motion.length()>=4:
				var delta := pending_motion; app.camera_button(pending_button,true,false,pending_cursor); cancel_gesture(); app.camera_motion(delta)
		elif app.navigating: app.camera_motion(event.relative)

func choose_at(point: Vector2, context := false) -> void:
	serial += 1; var request := serial
	if not app.canvas.scene_contains(point): return
	picking += 1
	_process(0); viewport.render_target_update_mode = SubViewport.UPDATE_ONCE
	# Keep each frame wait owned by this Node. A suspended coroutine otherwise
	# retains its camera Transform3D after its selection owner is freed. Separate
	# receivers keep picks requested during an emission on the next frame; bound
	# arguments alone do not give signal connections distinct identities in 4.6.
	var pending:=PickRequest.new();pending.receiver=weakref(self)
	pending.data={"serial":request,"view":app.scene_view.pick_state(),"uv":app.canvas.scene_uv(point),"point":point,"context":context}
	pick_requests[request]=pending
	RenderingServer.frame_post_draw.connect(pending.complete,CONNECT_ONE_SHOT)

func complete_pick(pending: RefCounted) -> void:
	var request: Dictionary=pending.data
	pick_requests.erase(request.serial);picking=pick_requests.size()
	if request.serial!=serial or request.view!=app.scene_view.pick_state() or app.exporting or app.playing or app.navigating or pending_button!=0 or app.mode.selected==0: return
	var uv: Vector2=request.uv
	var image := viewport.get_texture().get_image()
	var pixel := image.get_pixel(clampi(int(uv.x*image.get_width()),0,image.get_width()-1),clampi(int(uv.y*image.get_height()),0,image.get_height()-1))
	var kind := ""
	var nearest:=0.015
	var rgb:=Vector3(pixel.r,pixel.g,pixel.b)
	for id in colors:
		var distance:=rgb.distance_squared_to(color_for(id))
		if distance<nearest:nearest=distance;kind=id
	select_entity(kind)
	if request.context and not kind.is_empty():
		menu.clear(); menu.add_item("Frame selected",0)
		if selected_rig() and (kind=="model" or app.renderer.world_runtime):
			menu.add_item("Reset pose",1)
			menu.add_item("Hide object" if selected_rig().visible_at(app.frame) else "Show object",2)
		menu.add_separator(); menu.add_item("Deselect",3)
		var rect: Rect2 = app.canvas.image_rect()
		var position: Vector2 = app.canvas.global_position+rect.position+request.point/Vector2(app.video.width,app.video.height)*rect.size
		menu.position = app.get_window().position+Vector2i(position)
		menu.popup()

func _exit_tree() -> void:
	rail_ui_active = false
	serial+=1
	for pending in pick_requests.values():
		if RenderingServer.frame_post_draw.is_connected(pending.complete):RenderingServer.frame_post_draw.disconnect(pending.complete)
	pick_requests.clear();picking=0

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

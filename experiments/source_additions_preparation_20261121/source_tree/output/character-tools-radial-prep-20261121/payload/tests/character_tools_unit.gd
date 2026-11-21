extends SceneTree
# SOURCE ONLY UNPARSED/UNRUN. Owned widgets + synthetic Model metadata, no native asset.
const Bindings = preload("res://src/shortcut_bindings.gd")
const Tools = preload("res://src/character_tools.gd")
const Policy = preload("res://src/character_tool_policy.gd")
const Model = preload("res://src/model.gd")
var checks := 0
var failures := 0

class FixtureJob extends RefCounted:
	var pid := -1
class FixtureRecord extends RefCounted:
	var active := false
class FixtureHelper extends Node:
	var window: Window
	var calls: Array = []
	func open(prefer: bool=false) -> void: calls.append(prefer)
class FixturePhysics extends Node:
	var running := false
	var helper_editor: Node
	var recording := FixtureRecord.new()
	func grabbing() -> bool: return false
	func active(_id: String) -> bool: return running
class FixtureOptional extends Node:
	var allowed := false
	var calls := 0
	func eligible(_actor: RefCounted) -> bool: return allowed
	func open() -> void: calls += 1
class FixturePose extends Node:
	var dragging := false
	var variant_editor: Node
	var import_capabilities: Node
	var operation := OptionButton.new()
	var visible_toggle := CheckButton.new()
	var shape_calls := 0
	var visibility_calls: Array = []
	func open_shapes() -> void: shape_calls += 1
	func set_visibility_key(value: bool) -> void: visibility_calls.append(value)
class FixtureRenderer extends Node:
	var actor: RefCounted
	var view := {"position":[1.0,2.0,3.0],"camera_marker":"unchanged"}
	var restored := 0
	func active_model() -> RefCounted: return actor
	func view_state() -> Dictionary: return view.duplicate(true)
	func restore_view(value: Dictionary) -> void: view = value.duplicate(true); restored += 1
class FixtureKeys extends Node:
	var decorated: Array = []
	func decorate(control: Control,id: String,description: String) -> Control:
		decorated.append([id,description]); return control
	func label_for(_id: String) -> String: return "C"
class FixtureApp extends Control:
	var renderer: Node
	var physics_editor: Node
	var pose_editor: Node
	var keyboard_shortcuts: Node
	var source_import := FixtureJob.new()
	var has_project := FixtureJob.new()
	var mode := OptionButton.new()
	var changed_modes: Array = []
	var playing := false
	var exporting := false
	var navigating := false
	var drawing := false
	var recovery_revision := 7
	var frame := 0
	var messages: Array = []
	var history: Array = []
	var keys: Array = [{"frame":0,"marker":"authored"}]
	func icon_button(parent: Node,text: String,_icon: String,action: Callable) -> Button:
		return button(parent,text,action)
	func button(parent: Node,text: String,action: Callable) -> Button:
		var item := Button.new(); item.text = text; item.pressed.connect(action); parent.add_child(item); return item
	func message(text: String) -> void: messages.append(text)
	func change_mode(index: int) -> void: changed_modes.append(index)
class FixtureChooser extends Tools:
	var invoked: Array = []
	func _perform(action: String,actor: RefCounted) -> void:
		invoked.append([action,actor.get_instance_id()])

func _initialize() -> void: call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks += 1
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"character_tools."+label)
func legacy(count: int=15) -> Dictionary:
	var result: Dictionary = Bindings.DEFAULTS.duplicate()
	result.erase("character_tools")
	if count == 14: result.erase("redo_alternate")
	return result
func entry(rows: Array,id: String) -> Dictionary:
	for row in rows:
		if row.id == id: return row
	return {}
func key(code: int) -> InputEventKey:
	var result := InputEventKey.new(); result.keycode = code; result.pressed = true; return result
func actor(id: String) -> RefCounted:
	var value: RefCounted = Model.new(); value.root = Node3D.new()
	value.data = {"id":id,"kind":"model","visible":true,"metadata":{},"pose_keys":[],"pose":{}}
	value.order = ["root"]
	return value
func fixture() -> Dictionary:
	var app := FixtureApp.new(); app.theme = Theme.new(); root.add_child(app)
	app.renderer = FixtureRenderer.new(); app.add_child(app.renderer)
	app.physics_editor = FixturePhysics.new(); app.add_child(app.physics_editor)
	app.physics_editor.helper_editor = FixtureHelper.new(); app.add_child(app.physics_editor.helper_editor)
	app.pose_editor = FixturePose.new(); app.add_child(app.pose_editor)
	app.pose_editor.operation.add_item("Rotate"); app.pose_editor.operation.add_item("Move")
	app.pose_editor.add_child(app.pose_editor.operation); app.pose_editor.add_child(app.pose_editor.visible_toggle)
	app.keyboard_shortcuts = FixtureKeys.new(); app.add_child(app.keyboard_shortcuts)
	for title in ["Draw","Scene","Pose"]: app.mode.add_item(title)
	app.add_child(app.mode)
	var first: RefCounted = actor("one"); var second: RefCounted = actor("two")
	app.add_child(first.root); app.add_child(second.root); app.renderer.actor = first
	var tools := FixtureChooser.new(); app.add_child(tools); tools.setup(app)
	var panel := VBoxContainer.new(); app.add_child(panel); tools.add_button(panel)
	return {"app":app,"tools":tools,"first":first,"second":second}
func immutable_bytes(app: FixtureApp,value: RefCounted) -> PackedByteArray:
	return var_to_bytes([value.data,value.root.transform,app.keys,app.history,app.physics_editor.running,app.recovery_revision])

func run() -> void:
	var defaults: Dictionary = Bindings.DEFAULTS.duplicate()
	check(defaults.size() == 16 and Bindings.error(defaults).is_empty() and defaults.character_tools == KEY_C,"sixteen_unique_actions_with_unmodified_C")
	var old: Dictionary = legacy(); old.play = KEY_P; old.next = KEY_F6; old.camera = KEY_MASK_CTRL|KEY_J
	var original: PackedByteArray = var_to_bytes(old)
	var migrated: Dictionary = Bindings.migrate(old,1)
	var retained := not migrated.has("error")
	for id in old: retained = retained and migrated.bindings[id] == old[id]
	check(retained and migrated.bindings.character_tools == KEY_C and var_to_bytes(old) == original,"all_actual_fifteen_v1_remaps_preserved_without_input_write")
	old.pen = KEY_C; original = var_to_bytes(old); migrated = Bindings.migrate(old,1)
	check(migrated.bindings.pen == KEY_C and migrated.bindings.character_tools == 0 and var_to_bytes(old) == original,"new_action_unassigned_on_collision_without_stealing_old_key")
	var oldest: Dictionary = legacy(14); oldest.undo = KEY_MASK_CTRL|KEY_MASK_SHIFT|KEY_Z
	var oldest_bytes: PackedByteArray = var_to_bytes(oldest); migrated = Bindings.migrate(oldest,1)
	check(migrated.has("error") and var_to_bytes(oldest) == oldest_bytes,"unverified_fourteen_form_is_refused_without_rewriting_its_remaps")
	var bad: Dictionary = legacy(14); bad.erase("next"); bad.redo_alternate = KEY_MASK_CTRL|KEY_MASK_SHIFT|KEY_Z
	check(Bindings.migrate(bad,1).has("error"),"arbitrary_fourteen_key_missing_field_is_not_silently_repaired")
	bad = legacy(); bad.erase("last"); bad.foreign = KEY_F9
	check(Bindings.migrate(bad,1).has("error"),"legacy_unknown_field_is_not_dropped")
	bad = legacy(); bad.next = bad.play
	check(Bindings.migrate(bad,1).has("error"),"legacy_duplicate_key_still_refused")
	for invalid_value in [true,65.0,-1,KEY_MASK_ALT|KEY_C]:
		bad = legacy(); bad.play = invalid_value
		check(Bindings.migrate(bad,1).has("error"),"legacy_invalid_key_"+str(invalid_value))
	for invalid_version in [0,3,1.0,true,"1"]:
		check(Bindings.migrate(legacy(),invalid_version).has("error"),"unknown_or_untyped_version_"+str(invalid_version))
	check(Bindings.migrate(legacy(),Bindings.VERSION).has("error"),"new_version_cannot_hide_missing_character_action")
	migrated = Bindings.migrate(defaults,Bindings.VERSION)
	migrated.bindings.play = KEY_F9
	check(defaults.play == KEY_SPACE,"new_profile_load_returns_private_copy")
	var event: InputEventKey = key(KEY_C)
	check(Bindings.action(defaults,event) == "character_tools","new_logical_C_dispatches_character_tools")
	event.ctrl_pressed = true
	check(Bindings.action(defaults,event).is_empty(),"Ctrl_C_clipboard_is_not_stolen")
	event.ctrl_pressed = false; event.alt_pressed = true
	check(Bindings.action(defaults,event).is_empty(),"Alt_bone_reveal_is_not_stolen")
	event.alt_pressed = false; event.echo = true
	check(Bindings.action(defaults,event).is_empty(),"held_shortcut_does_not_reopen_dial")
	var c: Dictionary = fixture(); var app: FixtureApp = c.app; var tools: FixtureChooser = c.tools
	var before: PackedByteArray = immutable_bytes(app,c.first)
	var rows: Array = tools.current_entries(c.first)
	check(rows.size() == 7 and not entry(rows,"face").enabled and entry(rows,"face").reason.contains("head"),"face_entry_remains_findable_with_actionable_missing_head_reason")
	check(not entry(rows,"materials").enabled and entry(rows,"materials").reason.contains("separate saved capability"),"material_surface_hiding_not_faked_by_item_visibility_or_variants")
	check(entry(rows,"visibility").enabled and entry(rows,"visibility").title == "Hide item","existing_item_visibility_is_a_separate_action")
	app.physics_editor.running = true; rows = tools.current_entries(c.first)
	check(not entry(rows,"hair").enabled and entry(rows,"body").enabled,"live_hair_setup_guard_does_not_turn_motion_off")
	app.physics_editor.running = false
	tools._process(0.0)
	check(not tools.buttons[0].disabled and app.keyboard_shortcuts.decorated[0][0] == "character_tools","visible_button_uses_configurable_action")
	tools.open()
	check(is_instance_valid(tools.popup) and tools.choices.size() == 7 and immutable_bytes(app,c.first) == before and tools.invoked.is_empty(),"opening_real_owned_dial_does_not_modify_pose_keys_history_or_physics")
	tools.activate(0)
	check(is_instance_valid(tools.popup) and tools.invoked.is_empty() and tools.help.text.contains("head"),"disabled_face_cannot_open_an_empty_editor")
	tools.window_input(key(KEY_LEFT))
	check(tools.selected == 6 and tools.help.text.contains("separate saved capability"),"keyboard_can_inspect_disabled_material_reason")
	tools.window_input(key(KEY_ENTER))
	check(is_instance_valid(tools.popup) and tools.invoked.is_empty(),"Enter_on_disabled_action_is_read_only")
	tools.window_input(key(KEY_ESCAPE))
	check(tools.popup == null and immutable_bytes(app,c.first) == before and tools.invoked.is_empty(),"Escape_cancels_without_authored_change")
	tools.open(); tools.window_input(key(KEY_RIGHT)); tools.window_input(key(KEY_ENTER))
	check(tools.popup == null and tools.invoked == [["body",c.first.get_instance_id()]],"enabled_keyboard_action_uses_exact_retained_actor_once")
	tools.activate(1)
	check(tools.invoked.size() == 1,"replayed_closed_action_cannot_repeat")
	tools.open(); app.renderer.actor = c.second; tools._process(0.0)
	check(tools.popup == null and tools.invoked.size() == 1,"changing_selection_cancels_old_actor_dial")
	app.renderer.actor = c.first; tools.open(); app.recovery_revision += 1; tools.activate(1)
	check(tools.popup == null and tools.invoked.size() == 1,"scene_revision_change_refuses_old_action")
	for mode in ["playing","exporting","navigating","drawing"]:
		app.set(mode,true); tools.open()
		check(tools.popup == null and tools.invoked.size() == 1,"busy_"+mode+"_blocks_open_without_changing_intent")
		app.set(mode,false)
	app.physics_editor.recording.active = true; tools.open()
	check(tools.popup == null,"recording_blocks_open_without_stopping_or_freezing")
	app.physics_editor.recording.active = false
	var optional := FixtureOptional.new(); app.pose_editor.add_child(optional); app.pose_editor.variant_editor = optional
	check(not entry(tools.current_entries(c.first),"appearance").enabled,"optional_editor_presence_alone_does_not_invent_asset_capability")
	optional.allowed = true
	check(entry(tools.current_entries(c.first),"appearance").enabled,"qualified_optional_editor_can_offer_its_existing_action")
	c.first.root.set_meta(Model.Shape.META,{"rows":[{"node":"synthetic","names":["blink"]}]})
	check(entry(tools.current_entries(c.first),"face").enabled,"retained_shape_hint_can_enable_existing_face_entry")
	var actual := Tools.new(); app.add_child(actual); actual.setup(app)
	actual._perform("face",c.first); actual._perform("hair",c.first); actual._perform("visibility",c.first); actual._perform("appearance",c.first)
	check(app.pose_editor.shape_calls == 1 and app.physics_editor.helper_editor.calls == [true] and app.pose_editor.visibility_calls == [false] and optional.calls == 1,"actions_call_existing_face_hair_visibility_and_appearance_methods")
	var view: Dictionary = app.renderer.view_state(); actual._perform("body",c.first)
	check(app.changed_modes == [2] and app.renderer.view == view and app.renderer.restored == 1,"pose_route_preserves_inspection_camera")
	var floating := Window.new(); floating.size=Vector2i(340,600); floating.content_scale_factor=1.25; app.add_child(floating); floating.popup_centered(Vector2i(340,600))
	tools.open(floating)
	check(is_instance_valid(tools.popup) and tools.popup.get_parent()==floating and tools.popup.content_scale_factor==floating.content_scale_factor,"floating_dock_button_owns_its_menu_and_scale")
	tools.close(); floating.free()
	var startup: String = FileAccess.get_file_as_string("res://src/app.gd")
	check(startup.find("character_tools.setup(self)") >= 0 and startup.find("character_tools.setup(self)") < startup.find("\tbuild_ui()".c_unescape()),"actual_startup_constructs_controller_before_World_setup")
	check(startup.contains("\"character_tools\": if character_tools:character_tools.open_from_event(event)".c_unescape()),"actual_shortcut_router_has_explicit_action")
	tools.close(); tools.close(); app.free()
	print("CHARACTER_TOOLS_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_asset_tested":false,"application_adopted":false}))
	quit(0 if failures == 0 else 1)

extends Node
## Tiny shell hook. All imports remain in the ordinary ImportActions pipeline.
const DiscoveryWindow = preload("res://src/discovery/window.gd")
const Preferences = preload("res://src/discovery/preferences.gd")
var owner_ref: WeakRef
var window: Window
var button: Button
var preferences_path := Preferences.DEFAULT_PATH

static func install(app: Node, toolbar: Node, settings_path: String = "") -> Node:
	var bridge = load("res://src/discovery/studio_bridge.gd").new()
	bridge.name = "AssetDiscoveryBridge"; bridge.owner_ref = weakref(app)
	bridge.preferences_path = settings_path if not settings_path.is_empty() else str(app.display_prefs_path).get_base_dir().path_join("discovery-preferences.json")
	app.add_child(bridge)
	bridge.button = app.header_button(toolbar, "Discover", "package", bridge.open, "Browse local model files and optional online listings")
	return bridge

func guard_reason() -> String:
	var app = owner_ref.get_ref() if owner_ref else null
	if not is_instance_valid(app) or not app.is_inside_tree(): return "The requesting Studio scene is no longer open."
	if app.source_import.bundle_active: return "Finish or cancel the character-parts queue before importing a discovered file."
	if app.import_actions.busy(): return "Finish the current import, project operation or dialog first."
	if app.sequence_editor and (app.sequence_editor.installing or app.sequence_editor.preview_busy): return "Finish changing the current sequence first."
	if app.home and app.home.visible: return "Choose New scene or Return to scene before importing a discovered file."
	return ""

func context() -> Dictionary:
	var app = owner_ref.get_ref()
	return {"session":app.recovery_session, "revision":app.recovery_revision, "owner":app.sequence_editor.active_owner, "generation":app.sequence_editor.generation, "world_selection":app.world_selection.selected, "joint_selection":app.pose_editor.selected}

func open() -> void:
	var app = owner_ref.get_ref()
	if not is_instance_valid(app): return
	var reason := guard_reason()
	if not reason.is_empty(): app.message(reason); return
	if is_instance_valid(window): window.popup_centered(); return
	app.stop(); app.finish_stroke(); app.pose_editor.finish_drag(); app.release_mouse()
	var requesting := context()
	window = DiscoveryWindow.open(app, func(path: String): accept_local(path, requesting), {"preferences_path":preferences_path})

func accept_local(path: String, requesting: Dictionary) -> void:
	var app = owner_ref.get_ref()
	if not is_instance_valid(app): return
	var reason := guard_reason()
	if not reason.is_empty(): app.message(reason); return
	if context() != requesting:
		app.message("The scene or selection changed while browsing. Reopen Discover before adding this file."); return
	if not path.is_absolute_path() or path.begins_with("res://") or path.begins_with("user://") or not FileAccess.file_exists(path):
		app.message("The selected local file is missing. Choose its directory again."); return
	if path.get_extension().to_lower() not in ["glb", "gltf", "fbx", "obj", "pmd", "pmx", "vrm", "mdl"]:
		app.message("This browser lists filenames. Export a supported GLB before adding this file."); return
	# The wrapper has closed before this deferred callback. ImportActions checks
	# busy state again and owns placement, conversion, errors and project lifetime.
	app.import_actions.add(path, true, 0)

func _exit_tree() -> void:
	if is_instance_valid(window): window.queue_free()

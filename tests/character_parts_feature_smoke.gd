extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Parts=preload("res://src/character_parts.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Parts smoke timeout");quit(2));call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/parts-checks/flow-"+str(Time.get_ticks_usec()))
	DirAccess.make_dir_recursive_absolute(folder)
	var body:=folder.path_join("body.glb");var hair:=folder.path_join("hair.glb")
	check(SceneIO.make_pose_fixture(body)==OK and SceneIO.make_pose_fixture(hair)==OK,"two real independent rig GLBs created")
	var original_inputs: Dictionary={body:FileAccess.get_sha256(body),hair:FileAccess.get_sha256(hair)}
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json")
	root.gui_embed_subwindows=true;root.size=Vector2i(1400,900);root.add_child(app);await settle()
	app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("cache")
	check(app.new_project(),"ordinary New")
	var before: Dictionary=app.current_world().duplicate(true);var history: int=app.history.size()
	app.source_import.start_bundle([{"path":body,"role":"body"},{"path":hair,"role":"hair"}],{"name":"Test character","fit_height":true,"reference_index":0,"start_frame":0})
	for i in range(16):await process_frame
	check(not app.source_import.bundle_active and app.source_import.pid<=0,"prepared GLB queue completed")
	var runtime: RefCounted=app.renderer.world_runtime
	check(runtime.instances.size()==3,"one character and two model parts installed")
	if runtime.instances.size()!=3:print("STATUS "+app.status.text);app.free();quit(1);return
	var world: Dictionary=app.current_world().duplicate(true);var group_id:="";var part_ids: Array=[]
	for row in world.objects:
		if row.kind=="group":group_id=row.id
		else:part_ids.append(row.id)
	var group: RefCounted=runtime.instance(group_id)
	check(group.data.scale==1. and group.base_root.basis.get_scale().y!=1.,"Scale1 applies one shared six-foot intrinsic reference")
	check(group.bones.is_empty() and runtime.instance(part_ids[0]).bones.size()==2 and runtime.instance(part_ids[1]).bones.size()==2,"parent does not absorb independent part rigs")
	check(runtime.instance(part_ids[0]).root.global_transform==runtime.instance(part_ids[1]).root.global_transform,"prepared sibling origins stay aligned")
	check(app.history.size()==history+1 and app.history[-1].type=="world","bundle installation is one Undo transaction")
	app.undo();check(app.current_world()==before,"Undo removes complete character")
	app.redo();check(app.current_world()==world,"Redo restores exact character and metadata")
	var editor: Node=app.character_parts_editor
	var cheap:=true
	for i in range(1000):cheap=editor.can_manage(group_id) and cheap
	check(cheap,"per-frame availability handles repeated calls without world snapshots")
	editor.open(group_id);await settle()
	check(editor.dialog.visible and editor.switches.size()==2,"Manage parts exposes both parts")
	editor.switches[part_ids[1]].button_pressed=false;editor.apply_visibility();await settle()
	check(not app.renderer.world_runtime.instance(part_ids[1]).root.visible,"part visibility changes actual scene")
	app.undo();check(app.renderer.world_runtime.instance(part_ids[1]).data.visible,"visibility Undo restores source visibility")
	# Project serialization must retain one common reference, separate rows and keys.
	var saved: Dictionary=app.current_world().duplicate(true)
	var restored: String=app.restore_world(saved)
	check(restored.is_empty() and app.current_world()==saved,"world rebuild preserves bundle metadata and independent visibility")
	check(Parts.describe(saved,group_id,int(app.video.duration_frames)).parts.size()==2,"serialized membership resolves after rebuild")
	var snapshot: String=folder.path_join("snapshot")
	var save_error: String=Storage.save_project(snapshot,app.video,app.keys,[],"",0,{}, {},{},true,saved)
	check(save_error.is_empty(),"ordinary project save accepts bundled assets and metadata")
	var loaded: Dictionary=Storage.load_project(snapshot)
	check(not loaded.has("error") and loaded.has("world") and Parts.describe(loaded.world,group_id,int(app.video.duration_frames)).parts.size()==2,"portable project reload retains character membership")
	check(FileAccess.get_sha256(body)==original_inputs[body] and FileAccess.get_sha256(hair)==original_inputs[hair],"original prepared inputs remain unchanged")
	# An actual Python child writes each generated GLB completion. This checks the
	# ordinary MDL queue lifecycle without claiming SourceIO/native conversion.
	var old_import: Node=app.source_import;old_import.queue_free()
	var queued=preload("res://tests/character_parts_import_relay.gd").new();queued.app=app;app.source_import=queued;app.add_child(queued)
	var fake_body:=folder.path_join("body.mdl");var fake_hair:=folder.path_join("hair.mdl")
	var file:=FileAccess.open(fake_body,FileAccess.WRITE);file.store_string(body);file.close()
	file=FileAccess.open(fake_hair,FileAccess.WRITE);file.store_string(hair);file.close()
	var before_queue: int=app.history.size()
	queued.start_bundle([{"path":fake_body,"role":"body"},{"path":fake_hair,"role":"hair"}],{"name":"Queued character","fit_height":false,"start_frame":0})
	for i in range(400):
		if not queued.bundle_active:break
		await create_timer(.025).timeout
	check(not queued.bundle_active and queued.pid<=0 and app.renderer.world_runtime.instances.size()==6,"real sequential preparer completions install both parts together")
	check(app.history.size()==before_queue+1,"sequential preparation still installs one Undo transaction")
	check(not queued._preparation_map_reserved,"finished Windows preparer entries are released")
	app.free();await settle()
	print("CHARACTER_PARTS_FEATURE "+JSON.stringify({"checks":checks,"failures":failures}));quit(1 if failures else 0)

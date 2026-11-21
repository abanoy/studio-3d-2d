extends SceneTree
# Actual ordinary SourceIO conversions on owned copies; no native fidelity claim.
const Parts=preload("res://src/character_parts.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var app
func _initialize() -> void:
	create_timer(900).timeout.connect(func():push_error("Native parts timeout");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:quit(2);return
	var input: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[0]));var folder: String=input.folder
	var pins:={}
	for item in input.requests:pins[item.path]=FileAccess.get_sha256(item.path)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json")
	root.gui_embed_subwindows=true;root.size=Vector2i(1400,900);root.add_child(app)
	for i in range(4):await process_frame
	app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("cache");app.new_project()
	app.source_import.gmod_root=folder.path_join("AbsentGame");app.source_import.workshop_root=folder.path_join("AbsentWorkshop")
	var before: Dictionary=app.current_world().duplicate(true);var history: int=app.history.size()
	app.source_import.start_bundle(input.requests,{"name":"Junko — SFM parts","fit_height":true,"reference_index":0,"start_frame":0,"unit_scale":.01905,"content":input.native_root})
	for i in range(17000):
		if not app.source_import.bundle_active:break
		await create_timer(.05).timeout
	var runtime: RefCounted=app.renderer.world_runtime
	check(not app.source_import.bundle_active and app.source_import.pid<=0,"six ordinary native preparations finished")
	check(runtime.instances.size()==7,"actual six native parts installed under one character")
	if runtime.instances.size()!=7:print("STATUS "+app.status.text);app.free();quit(1);return
	var world: Dictionary=app.current_world().duplicate(true);var root_id:="";var bones:={};var aligned:=true;var skeletons:={}
	for row in world.objects:
		if row.kind=="group":root_id=row.id
	for row in world.objects:
		var actor: RefCounted=runtime.instance(row.id)
		if row.kind=="group":check(actor.data.scale==1. and actor.bones.is_empty(),"empty character root keeps Scale1 and no merged bones");continue
		var role: String=row.metadata.character_part.role;bones[role]=actor.bones.size()
		aligned=aligned and actor.root.global_transform==runtime.instance(root_id).root.global_transform*actor.base_root and actor.data.scale==1.
		for joint in actor.bones.values():skeletons[joint.skeleton.get_instance_id()]=true
	check(bones=={"body":145,"hair":69,"dress":112,"skirt":136,"miniskirt":136,"mask":19},"all native bone inventories stay complete and independent")
	check(skeletons.size()==6 and aligned,"six separate skeletons retain the shared prepared origin")
	check(runtime.instance(root_id).data.metadata.character_parts.height_factor>0.,"one common body height reference recorded")
	check(app.history.size()==history+1,"all six native preparations install one Undo transaction")
	app.undo();check(app.current_world()==before,"native bundle Undo removes all seven rows")
	app.redo();check(app.current_world()==world,"native bundle Redo restores exact source metadata")
	var bundle:=Parts.describe(app.current_world(),root_id,int(app.video.duration_frames))
	check(bundle.parts.size()==6,"native membership available to Manage parts")
	var why: String=Storage.save_project(folder.path_join("snapshot"),app.video,app.keys,[],"",0,{}, {},{},true,world)
	check(why.is_empty(),"ordinary project writer retains all six native GLBs")
	var loaded:=Storage.load_project(folder.path_join("snapshot"))
	check(not loaded.has("error") and Parts.describe(loaded.world,root_id,int(app.video.duration_frames)).parts.size()==6,"native bundle membership reloads")
	var unchanged:=true
	for path in pins:unchanged=unchanged and FileAccess.get_sha256(path)==pins[path]
	check(unchanged,"all owned native MDLs remain unchanged")
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"bones":bones,"root_id":root_id,"world":app.current_world()},"\t"));file.close()
	app.free()
	for i in range(4):await process_frame
	print("CHARACTER_PARTS_NATIVE "+JSON.stringify({"checks":checks,"failures":failures,"parts":6,"bone_inventory":bones,"native_fidelity_qualified":false}));quit(1 if failures else 0)

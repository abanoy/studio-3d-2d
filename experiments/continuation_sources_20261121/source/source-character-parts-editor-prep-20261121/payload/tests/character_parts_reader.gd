extends SceneTree
# Fresh-process reader of only copied synthetic snapshot + expected-world.json.
const Parts=preload("res://src/character_parts.gd")
const World=preload("res://src/world_document.gd")
const Runtime=preload("res://src/world_runtime.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(60).timeout.connect(func():push_error("Character parts reader watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=2 or DisplayServer.get_name()!="headless":push_error("Expected headless reader folder and isolated profile name");quit(2);return
	if args[1].is_empty() or not OS.get_user_data_dir().replace("\\","/").ends_with("/"+args[1]):push_error("Expected exact independent reader profile");quit(2);return
	var folder: String=ProjectSettings.globalize_path(args[0]).simplify_path()
	var output: String=ProjectSettings.globalize_path("res://output").simplify_path()
	if not folder.begins_with(output+"/") or FileAccess.file_exists(folder.path_join("reader-result.json")):push_error("Use a fresh reader result under owned output");quit(2);return
	var expected=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected-world.json")))
	if not expected is Dictionary:push_error("Synthetic expected-world manifest is missing");quit(2);return
	var loaded: Dictionary=Storage.load_project(folder.path_join("snapshot"))
	check(not loaded.has("error"),"fresh process loads the packed synthetic assembly snapshot")
	if loaded.has("error"):quit(1);return
	check(World.portable(loaded.world)==expected,"all saved static World/member/native/visibility fields match expected wire")
	var bundle: Dictionary=Parts.describe(loaded.world,"hair",int(loaded.video.duration_frames))
	check(not bundle.has("error") and bundle.parts.size()==6 and bundle.root_id=="junko","fresh process recovers exact six-member bundle from member selection")
	var managed:=true
	for row in loaded.world.objects:managed=managed and str(row.source).simplify_path().begins_with(folder.path_join("snapshot/assets").simplify_path()+"/")
	check(managed,"all source paths resolve inside copied snapshot assets, not writer sources")
	var prepared: Dictionary=Runtime.prepare(loaded.world,int(loaded.video.duration_frames),loaded.video)
	check(not prepared.has("error"),"fresh runtime independently prepares all seven saved records")
	if prepared.has("error"):quit(1);return
	var live: RefCounted=prepared.runtime;root.add_child(live.root);live.evaluate(12,false,"",loaded.video)
	check(live.instances.size()==7 and live.instance("junko").bones.is_empty(),"saved group owns no member bone inventory")
	var owners:={};var parents:=true
	for role in Parts.ROLES:
		var actor: RefCounted=live.instance(role)
		parents=parents and actor.root.get_parent()==live.instance("junko").root and actor.bones.size()==2
		for bone in actor.bones.values():owners[bone.skeleton.get_instance_id()]=true
	check(parents and owners.size()==6,"fresh source loading keeps six distinct rigs despite repeated bone names")
	check(not Parts.Visibility.target(live.instance("hair").data,12) and Parts.Visibility.target(live.instance("mask").data,12) and Parts.Visibility.target(live.instance("dress").data,12),"fresh reader retains keyed per-part/outfit visibility")
	check(live.instance("junko").data.scale==2. and live.instance("hair").data.scale==1.,"fresh reader preserves one root scale without per-part normalization")
	live.dispose()
	var report: Dictionary={"checks":checks,"failures":failures,"synthetic_only":true,"actual_six_MDL_alignment_qualified":false,"bone_following_qualified":false}
	var file:=FileAccess.open(folder.path_join("reader-result.json"),FileAccess.WRITE)
	if file==null:quit(2);return
	file.store_string(JSON.stringify(report,"\t",true,true));file.flush()
	if file.get_error()!=OK:quit(2);return
	file.close();print("CHARACTER_PARTS_READER "+JSON.stringify(report));quit(1 if failures else 0)

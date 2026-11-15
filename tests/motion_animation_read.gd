extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Motion read watchdog");quit(2));call_deferred("run")
func run() -> void:
	var folder:=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("result.json")));var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery");root.add_child(app)
	for i in range(4):await process_frame
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache");app.has_project.open_file(expected.project)
	while app.has_project.pid>0:await process_frame
	for i in range(4):await process_frame
	check(World.portable(app.current_world())==expected.expected_world,"cold normal Open retains exact portable model8 world/settings/controls")
	var actor: RefCounted=app.renderer.world_runtime.instance("actor");var exact: bool=actor!=null and actor.motion_enabled()
	if actor:
		for half in range(96,-1,-1):exact=exact and JSON.stringify(actor.sample(float(half)/2),"",true,true).sha256_text()==expected.pose_hashes[half]
	check(exact,"cold reader retains all97 assisted solved native poses exactly in reverse")
	check(preload("res://src/drawing.gd").image(app.layers[1].cels[0]).get_data().hex_encode().sha256_text()==expected.layer_sha,"cold reader retains independent editable drawing bytes")
	app.set_frame(10);app.world_selection.clear();var image: Image=await app.renderer.capture(app.keys,app.layers,10,true);image.save_png(folder.path_join("reader-frame.png"));var reference:=Image.load_from_file(folder.path_join("saved-frame.png"));var a:=image.get_data();var b:=reference.get_data();var changed:=0;var total:=0.
	for i in range(a.size()):
		if a[i]!=b[i]:changed+=1;total+=absf(float(a[i])-float(b[i]))
	var mean:=total/float(a.size());check(changed<=384 and mean<.002,"cold native skin rebuild keeps final image within the existing mesh-edge bound")
	var file:=FileAccess.open(folder.path_join("reader.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks,"failures":failures,"changed_channels":changed,"mean_error":mean}));file.close();app.free();await process_frame;print("MOTION_ANIMATION_READ "+str(checks)+"/"+str(failures));quit(0 if failures==0 else 1)

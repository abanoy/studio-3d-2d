extends SceneTree
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(240).timeout.connect(func():push_error("Native backend watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var native: String=args[1] if args.size()>1 else "/workspace/has-private-native-new"
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var importer=app.source_import;importer.gmod_root="";importer.workshop_root="";importer.extra_roots=[];importer.mount_overrides={}
	var jobs:=[]
	var plans: Array=[{"file":"touhou_reimu_bikini.gma","member":"models/player/reimu_hakurei_bikini.mdl","actor":true,"scale":0.01905},{"file":"Miku_Hatsune.pmd","member":"","actor":true,"scale":0.08},{"file":"street01_android.pmx","member":"","actor":false,"scale":0.08}]
	if args.size()>2:plans=JSON.parse_string(FileAccess.get_file_as_string(args[2]))
	for row in plans:
		var previous: int=app.current_world().objects.size()
		importer.launch(native.path_join(row.file),row.member,row.actor,row.scale)
		check(importer.pid>0,"native importer launches "+row.file)
		while importer.pid>0:await process_frame
		await settle()
		check(app.current_world().objects.size()==previous+1,row.file+" is adopted through actual native importer")
		if app.current_world().objects.size()!=previous+1:print(app.status.text);app.free();quit(1);return
		jobs.append({"file":row.file,"folder":importer.folder})
		for child in app.get_children():
			if child is AcceptDialog and child.title in ["Source import warnings","Imported with limitations"]:child.confirmed.emit();child.hide()
	check(app.current_world().objects.size()==plans.size(),"all native import plans coexist without changing renderer settings")
	var result:={"checks":checks,"failures":failures,"jobs":jobs};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("NATIVE_BACKENDS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)

extends SceneTree
const Library=preload("res://src/pose_library.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Native body-pose watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plan.json")))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var reports:=[];var editor=app.pose_editor;var library=editor.pose_library
	for plan in plans:
		app.new_project();var sha:=FileAccess.get_sha256(plan.source)
		check(editor.add_model(plan.source).is_empty(),plan.label+" retained native preparation loads through shared GLB")
		app.physics_editor.freeze_all();app.physics_editor.clear_previews();app.mode.select(2);app.change_mode(2);await settle()
		var rig=editor.active_rig();check(rig!=null and rig.order.size()>20,plan.label+" retains actual native skeleton")
		var id: String=rig.order[-1]
		for candidate in rig.order:
			var name: String=rig.bones[candidate].name.to_lower()
			if "upperarm" in name or "upper_arm" in name or "腕" in name:id=candidate;break
		editor.selected=id;editor.operation.select(0);editor.fields[2].value=25;editor.apply_numeric();editor.frame_model();await settle()
		var pose: Dictionary=rig.sample_body(0,true);var place: Dictionary=rig.sample_authored_transform(0,true);library.open();library.name_edit.text=plan.label+" arm pose";await library.capture();await settle()
		var values:=Library.get_library(rig);check(values.entries.size()==1 and Library.compatible(values,rig).is_empty(),plan.label+" saves body pose/thumbnail against exact source and bone bindings")
		if values.entries.is_empty():print(app.status.text);app.free();quit(1);return
		Library.thumbnail(values.entries[0].thumbnail_png).image.save_png(folder.path_join(plan.label+"-pose.png"))
		app.set_frame(24);editor.selected=id;editor.reset_selected();app.set_frame(12);library.selected=values.entries[0].id;var before: Dictionary=rig.data.duplicate(true);library.apply_pose()
		check(Library.equivalent(rig.sample_body(12),pose) and rig.sample_authored_transform(12)==place,plan.label+" reuses authored FK pose without moving model")
		app.undo();check(Library.equivalent(rig.data,before),plan.label+" Undo restores exact independent animation state")
		check(FileAccess.get_sha256(plan.source)==sha,plan.label+" original preparation bytes stay unchanged")
		reports.append({"label":plan.label,"bones":rig.order.size(),"selected":id,"source_sha256":sha,"library_bytes":JSON.stringify(values,"",true,true).to_utf8_buffer().size()})
	print("POSE_LIBRARY_NATIVE ",JSON.stringify({"checks":checks,"failures":failures,"cases":reports}));app.free();quit(0 if failures==0 else 1)

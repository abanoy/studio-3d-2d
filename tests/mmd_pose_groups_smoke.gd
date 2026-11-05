extends SceneTree
const Model=preload("res://src/model.gd")
const Presets=preload("res://src/expression_presets.gd")
func _initialize() -> void:
	create_timer(90).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var app=load("res://main.tscn").instantiate()
	var folder:=ProjectSettings.globalize_path("res://output/mmd-pose-groups/%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	app.recovery_root=folder.path_join("recovery");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false
	var prepared: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/mmd-groups-verification.json"))
	var source: String=prepared.results[0].bundle.path_join("scene.glb")
	assert(app.pose_editor.add_model(source).is_empty())
	var rig: RefCounted=app.renderer.active_model()
	var original: Dictionary=rig.data.duplicate(true)
	var body: Dictionary=rig.sample_body(12)
	var catalogue: Dictionary=rig.root.get_meta(Presets.META)
	assert(catalogue.entries.size()==4)
	app.set_frame(12);app.pose_editor.frame_model();await settle()
	var camera: Array=app.keys.duplicate(true)
	var neutral: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var before_history: int=app.history.size()
	var importer=app.mmd_pose_importer
	for index in [0,1,2]:
		var entry: Dictionary=catalogue.entries[index]
		var unsupported: Dictionary=catalogue.entries[3]
		var text:="\ufeffVocaloid Pose Data file\nOriginal groups.pmx;\n0;\nMorph0{%s\n0.6;\n}\nMorph1{%s\n1;\n}\n" % [entry.native_name,unsupported.native_name]
		var path:=folder.path_join("group-%d.vpd" % index)
		var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(text);file.close()
		importer.begin(path)
		while importer.busy():await process_frame
		await settle()
		assert(is_instance_valid(importer.review) and importer.review.visible,app.status.text)
		assert(importer.proposed.matched_morphs==[entry.native_name] and importer.proposed.skipped_morphs.size()==1)
		assert(importer.proposed.skipped_morphs[0].name==unsupported.native_name and "unsupported" in importer.proposed.skipped_morphs[0].reason.to_lower())
		importer.review.confirmed.emit();await settle()
		assert(rig.authored_keys().is_empty() and rig.sample_body(12)==body and rig.data.metadata==original.metadata and app.keys==camera)
		for bind in entry.binds:assert(is_equal_approx(rig.sample_shapes(12)[bind.node][bind.index],.6*bind.weight))
		assert(app.history.size()==before_history+1)
		app.undo();assert(rig.data==original)
		app.redo()
		var changed: Image=await app.renderer.capture(app.keys,app.layers,12,true)
		assert(changed.get_data()!=neutral.get_data())
		app.undo();assert(rig.data==original)
		# The next independent group uses the same clean source and undo baseline.
		before_history=app.history.size()
	print("MMD_POSE_GROUPS failures=0 compound/nested/signed native PMX groups; unsupported UV refused; body/native/camera and Undo preserved")
	app.free();quit(0)

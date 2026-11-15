extends SceneTree
const Presets=preload("res://src/expression_presets.gd")
const Runner=preload("res://src/secondary_spring.gd")
const T=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(240).timeout.connect(func():quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.display_prefs_path=folder.path_join("prefs.cfg");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var observations:=[]
	for plan in plans:
		app.new_project();check(app.pose_editor.add_model(plan.glb).is_empty(),plan.name+" native feature setup")
		await settle();var actor=app.renderer.active_model();var id: String=actor.data.id
		app.pose_editor.frame_model();await settle();app.keys=[T.from_camera(0,app.renderer.camera,"linear")]
		var catalogue: Dictionary=actor.root.get_meta(Presets.META)
		var secondary: Dictionary=actor.root.get_meta("has_secondary_rig")
		print("VRM_FEATURES "+JSON.stringify({"name":plan.name,"expression_error":catalogue.error,"expression_count":catalogue.entries.size(),"spring_error":secondary.error,"chains":secondary.chains.size(),"colliders":secondary.colliders.size()}))
		check(catalogue.error.is_empty() and not catalogue.entries.is_empty(),plan.name+" native expressions bind")
		var selected:=-1
		for i in range(catalogue.entries.size()):
			var row: Dictionary=catalogue.entries[i]
			if row.error.is_empty() and not row.binds.is_empty():
				selected=i
				if "blink" in str(row.native_name).to_lower():break
		if selected>=0:
			var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
			app.pose_editor.open_shapes();await settle();var ui=app.pose_editor.animated_shapes.presets;ui.choices.select(selected);ui.choices.item_selected.emit(selected);ui.amount.value=1;ui.apply_button.pressed.emit();await settle();actor=app.renderer.world_runtime.instance(id)
			var after: Dictionary=actor.data.duplicate(true);var expressive: Image=await app.renderer.capture(app.keys,[],0,true)
			check(after!=before and app.history.size()==history+1 and expressive.get_data()!=neutral.get_data(),plan.name+" actual expression UI authors visible deformation")
			app.undo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==before,plan.name+" expression Undo exact")
			app.redo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==after,plan.name+" expression Redo exact")
		else:check(false,plan.name+" has a supported visible expression")
		for chain in secondary.chains:
			for index in range(chain.joints.size()):
				if chain.joints[index].binding.kind!="bone":print("NONBONE ",plan.name," ",chain.name," ",index,"/",chain.joints.size()," ",chain.joints[index].binding)
		if secondary.error.is_empty() and not secondary.chains.is_empty():
			var created: Dictionary=await Runner.create(actor);print("SPRING_CREATE ",plan.name," ",created.get("error","ok"));check(not created.has("error"),plan.name+" native spring runner starts")
			if not created.has("error"):
				var before: Dictionary=actor.data.duplicate(true);var sampled:={};var finite:=true
				for i in range(60):
					actor.live_pose=null;actor.apply(0);sampled=created.runner.step(1.0/120,Vector3(.2,0,0))
					finite=finite and not sampled.has("error")
				check(finite and actor.data==before,plan.name+" native springs run without modifying authored data")
				created.runner.dispose();actor.live_pose=null
		else:check(not secondary.error.is_empty(),plan.name+" unsupported spring structure has explicit diagnostics")
		observations.append({"name":plan.name,"expressions":catalogue.entries.size(),"spring_error":secondary.error,"chains":secondary.chains.size()})
	var result:={"checks":checks,"failures":failures,"models":observations};FileAccess.open(folder.path_join("features.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("VRM_FEATURE_RESULT "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)

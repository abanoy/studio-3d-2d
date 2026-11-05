extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Labels=preload("res://src/bone_labels.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Channels=preload("res://src/animated_channels.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(40).timeout.connect(func():push_error("Bone label watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()

func query(editor, text: String) -> void:
	editor.search.text=text
	# Setting LineEdit.text alone does not emit the user's text_changed event.
	editor.search.text_changed.emit(text)

func run() -> void:
	check(Labels.estimate("左腕")=="Left upper arm" and Labels.estimate("右ひじ")=="Right elbow","dictionary estimates common left/right humanoid parts")
	check(Labels.estimate("右親指２")=="Right thumb 2" and Labels.estimate("左人差指1")=="Left index finger 1","numbered finger segments preserve source numbering")
	check(Labels.estimate("左腕捩3")=="Left upper arm twist 3" and Labels.estimate("右足ＩＫ")=="Right leg IK","known twist and full-width IK conventions retain their meaning")
	check(Labels.estimate("上半身2")=="Upper body 2" and Labels.estimate("全ての親")=="Root control","common center/root/body controls have conservative estimates")
	check(Labels.display("mystery_joint")=="Other part" and Labels.display("左未知部品")=="Other part" and "mystery_joint" in Labels.display("mystery_joint",true),"unknown parts stay neutral in Simple and reveal their exact name in Advanced")
	check(Labels.matches("左腕","UPPER ARM") and Labels.matches("左腕","左腕") and not Labels.matches("左腕","ankle"),"search matches English or native names without unrelated matches")
	check(Labels.display("左腕1")!=Labels.display("左腕2") and Labels.display("leftUpperArm")=="Left upper arm","repeated parts retain numbers and known English conventions use body names")
	check(Labels.display("左手首")=="Left hand" and Labels.display("右足首")=="Right foot" and Labels.display("下半身")=="Pelvis" and Labels.display("口")=="Mouth","Simple generalizes hands, feet, pelvis and mouth")
	check(Labels.display("ValveBiped.Bip01_L_Hand")=="Left hand" and Labels.display("ValveBiped.Bip01_R_Finger11")=="Right index finger 2" and Labels.display("bip_hip_L")=="Left thigh","Source and SFM exact aliases share the standard vocabulary")
	check(Labels.display("opaqueJoint",false,"leftHand")=="Left hand" and Labels.display("opaqueJoint",true,"leftHand")=="Left hand · opaqueJoint","declared VRM humanoid roles label opaque internal names")
	check(Labels.role({"metadata":{"native_parameters":"opaque"}},"a")=="" and Labels.role({"metadata":{"native_parameters":{"humanoid":{"leftHand":{"node_name":"a"}}}}},"a")=="leftHand","role labels tolerate opaque native metadata and use explicit node mapping")
	var folder:=ProjectSettings.globalize_path("res://output/bone-labels/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("日本語.glb");SceneIO.make_pose_fixture(asset,["センター","左腕"]);var original:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.pose_editor.add_model(asset)
	var rig: RefCounted=app.renderer.active_model();var id: String=rig.data.id;var arm: String=rig.order[1];var editor=app.pose_editor
	check(rig.bones[arm].name=="左腕" and "左腕" in arm and editor.tree_items[arm].get_metadata(0)==arm,"native bone name and binding identity remain Japanese")
	check(editor.tree_items[arm].get_text(0)=="Left upper arm" and not "左腕" in editor.tree_items[arm].get_tooltip_text(0) and not arm in editor.tree_items[arm].get_tooltip_text(0),"Simple tree and tooltip use body names without internal names or IDs")
	var before: Dictionary=rig.data.duplicate(true)
	query(editor,"upper arm")
	check(editor.tree_items.has(arm) and editor.tree_items.size()==2 and editor.tree_items[arm].get_text(0)=="Left upper arm" and rig.data==before,"English search finds the original rig without editing it")
	query(editor,"左腕")
	check(editor.tree_items.has(arm) and editor.tree_items[arm].get_metadata(0)==arm,"native search resolves the same original bone")
	query(editor,"");editor.tree_items[arm].select(0);editor.record_key();editor.frame_model()
	var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
	app.set_frame(8);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=40;editor.apply_numeric()
	var posed: Image=await app.renderer.capture(app.keys,[],8,true)
	check(neutral.get_data()!=posed.get_data() and rig.authored_keys()[-1].pose.has(arm) and not rig.authored_keys()[-1].pose.has("Left upper arm"),"English-labelled control visibly poses and keys the original Japanese binding")
	var state: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var camera: Transform3D=app.renderer.camera.transform
	app.timeline.toggle_expanded(0);editor.search.text="upper arm";editor.search.text_changed.emit("upper arm")
	app.set_advanced(true);await settled()
	check(editor.selected==arm and editor.tree_items[arm].get_text(0)=="Left upper arm · 左腕" and arm in editor.tree_items[arm].get_tooltip_text(0),"Advanced reveals exact internal names and IDs while retaining selected bone and filter")
	var channel: Dictionary=app.timeline.channel_cache[id].channels[-1]
	check("左腕" in channel.label and arm in channel.tooltip,"expanded timeline reveals internal names in Advanced too")
	root.get_texture().get_image().save_png(folder.path_join("advanced-names.png"))
	app.set_advanced(false);await settled();channel=app.timeline.channel_cache[id].channels[-1]
	check(editor.tree_items[arm].get_text(0)=="Left upper arm" and channel.label=="Left upper arm" and not arm in channel.tooltip,"returning to Simple refreshes tree and cached timeline labels immediately")
	check(rig.data==state and app.history.size()==history and app.renderer.camera.transform==camera and app.frame==8 and editor.selected==arm,"mode switches preserve pose keys, selection, frame, camera and Undo")
	var relabelled: Image=await app.renderer.capture(app.keys,[],8,true)
	check(relabelled.get_data()==posed.get_data(),"label presentation changes leave final render pixels identical")
	root.get_texture().get_image().save_png(folder.path_join("simple-names.png"))
	var project:=folder.path_join("labels.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);app.world_selection.select_entity(id);rig=app.renderer.active_model()
	check(rig.bones[arm].name=="左腕" and rig.authored_keys()[-1].pose.has(arm) and editor.tree_items[arm].get_text(0)=="Left upper arm","packed HAS reopens native Japanese bindings and reapplies Simple labels")
	check(FileAccess.get_sha256(asset)==original,"dictionary labels never rewrite source model bytes")
	var native_tested:=false
	var miku:=ProjectSettings.globalize_path("res://output/pose-smoke/miku-project")
	if FileAccess.file_exists(miku.path_join("project.json")):
		var source: Dictionary=Storage.load_project(miku);var row: Dictionary=World.from_project(source).objects[-1]
		var single:=World.empty();single.objects.append(row);app.restore_world(single);app.world_selection.select_entity(row.id)
		rig=app.renderer.active_model();editor=app.pose_editor;arm=""
		for bone in rig.order:
			if rig.bones[bone].name=="左腕":arm=bone
		check(not arm.is_empty() and editor.tree_items[arm].get_text(0)=="Left upper arm","actual Miku PMD tree displays its common body-part name")
		before=rig.data.duplicate(true);query(editor,"left upper arm")
		check(editor.tree_items.has(arm) and editor.tree_items.size()<rig.order.size()/2 and not editor.tree_items.has(rig.order[0]) and editor.tree_items[arm].get_metadata(0)==arm and rig.data==before,"actual Miku supports English search with identical native data")
		editor.frame_model();await settled();root.get_texture().get_image().save_png(folder.path_join("miku-english.png"));native_tested=true
	var result:={"checks":checks,"failures":failures,"folder":folder,"native_tested":native_tested}
	var file:=FileAccess.open("res://output/bone-labels-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("BONE_LABELS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)

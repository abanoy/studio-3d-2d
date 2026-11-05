extends "res://tests/motion_assist_native.gd"
const Motion=preload("res://src/motion_animation.gd")
func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func native_case(plan: Dictionary) -> Dictionary:
	var start:=checks;var first:=failures;var actor:=setup(plan);var id:=arm(actor);var original: Dictionary=actor.data.duplicate(true)
	app.mode.select(2);app.change_mode(2);app.set_advanced(false);app.world_selection.select_entity("actor");app.set_frame(10);app.pose_editor.frame_model();app.keys=[T.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)];var shots: Array=app.keys.duplicate(true);var history: int=app.history.size();var paint: PackedByteArray=app.layers[1].cels[0].image.get_data()
	var baseline:=[];var roots:=[]
	for half in range(97):baseline.append(actor.sample(float(half)/2));roots.append(actor.sample_transform(float(half)/2))
	var ui=app.pose_editor.motion;check(ui.button.is_visible_in_tree() and not ui.button.disabled,"motion control is available in Simple: "+plan.name)
	ui.button.pressed.emit();check(ui.window.visible,"actual motion dialog opens: "+plan.name);ui.enabled.button_pressed=true;ui.apply();await settled()
	check(actor.data.format==Model.MOTION_FORMAT and actor.motion_enabled() and not ui.window.visible and app.history.size()==history+1,"Apply saves model8 settings with one Undo: "+plan.name+" "+ui.note.text)
	if actor.data.format!=Model.MOTION_FORMAT:return {"name":plan.name,"checks":checks-start,"failures":failures-first}
	var enabled_data: Dictionary=actor.data.duplicate(true);check(actor.data.animation_clips==original.animation_clips,"enabling adds intent without rewriting native main controls: "+plan.name)
	ui.open();check(not ui.helpers.visible,"Simple keeps generated helper keys hidden: "+plan.name);ui.window.hide();app.set_advanced(true);ui.open();check(ui.helpers.visible and ui.helpers.get_root()!=null and ui.helpers.get_root().get_child_count()>0,"Advanced reveals generated helper frames and native part names: "+plan.name)
	if plan.id=="native-4":
		await settled();root.get_viewport().get_texture().get_image().save_png(folder.path_join("advanced-motion-ui.png"))
	ui.window.hide();app.set_advanced(false)
	check(actor.sample(10)!=baseline[20],"ordinary native sampler now includes motion feeling: "+plan.name)
	app.undo();check(actor.data==original and actor.sample(10)==baseline[20],"Undo restores exact original model and motion: "+plan.name);app.redo();check(actor.data==enabled_data,"Redo restores exact assisted settings: "+plan.name)
	var poses:=[];var read_only:=true;var state:=snapshot(actor);var peak:=0.;var reachable:=true
	for half in range(97):poses.append(actor.sample(float(half)/2));reachable=reachable and actor.evaluation_error.is_empty();read_only=read_only and snapshot(actor)==state
	var reversible:=true
	for half in range(96,-1,-1):reversible=reversible and actor.sample(float(half)/2)==poses[half]
	check(read_only and reversible and reachable,"native shared sampler is read-only, reachable and reverse exact: "+plan.name)
	for at in range(49):
		app.set_frame(at)
		for foot in Contacts.active(actor.data.animation_clips,at).get("feet",[]):peak=maxf(peak,actor.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	check(peak<.0002,"ordinary native display keeps planted feet with assistance: "+plan.name)
	# Actual pose editing at an assisted intermediate frame creates only its own
	# authoritative part key; it must not bake the generated root motion.
	app.set_frame(10);var root_before:=[]
	for half in range(97):root_before.append(actor.sample_transform(float(half)/2))
	var old_keys: Array=actor.data.animation_clips[0].keys.duplicate(true);var editor=app.pose_editor;editor.selected=id;editor.operation.select(1);editor.refresh_values();history=app.history.size();editor.fields[0].value+=.01;editor.apply_numeric();await settled()
	check(actor.data.format==Model.MOTION_FORMAT and app.history.size()==history+1 and 10 in Motion.Body.B.frames(Motion.Body.view(actor.data),id),"actual bone edit auto-keys one main control on model8: "+plan.name+" "+app.status.text)
	var peers:=true
	for half in range(97):peers=peers and actor.sample_transform(float(half)/2)==root_before[half]
	check(peers and actor.data.animation_clips[0].keys==old_keys and Motion.Body.B.frames(Motion.Body.view(actor.data),"@root")==[0,12,24],"native bone edit never bakes helper root or legacy snapshots: "+plan.name)
	app.undo();check(actor.data==enabled_data,"bone edit Undo restores complete assisted model: "+plan.name)
	app.set_frame(10);ui.open();ui.enabled.button_pressed=false;ui.apply();await settled();var off_exact:=true
	for half in range(97):off_exact=off_exact and actor.sample(float(half)/2)==baseline[half] and actor.sample_transform(float(half)/2)==roots[half]
	check(not actor.motion_enabled() and off_exact,"saved Off restores original native pose and root motion exactly: "+plan.name)
	app.undo();check(actor.data==enabled_data and actor.motion_enabled(),"Undo Off restores the assisted model: "+plan.name)
	check(app.keys==shots and app.layers[1].cels[0].image.get_data()==paint,"native motion editing preserves explicit shots and independent paint: "+plan.name)
	return {"name":plan.name,"bones":actor.order.size(),"checks":checks-start,"failures":failures-first,"foot_error":peak}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1]);await wait_job();var plans:=[];var hashes:={}
	for row in app.current_world().objects:
		if row.get("format")==Model.CONTACT_FORMAT:plans.append(row);hashes[row.source]=FileAccess.get_sha256(row.source)
	check(plans.size()==5,"five native rigs available for normal model8 acceptance")
	var reports:=[]
	for plan in plans:reports.append(await native_case(plan))
	var actor: RefCounted=app.renderer.active_model();var path:=folder.path_join("motion-feeling.has");app.set_frame(10);app.world_selection.clear();app.has_project.save_file(path,"packed");await wait_job()
	check(FileAccess.file_exists(path),"normal packed HAS saves assistance intent and editable controls")
	var poses:=[]
	for half in range(97):poses.append(JSON.stringify(actor.sample(float(half)/2),"",true,true).sha256_text())
	var expected: Dictionary=World.portable(app.current_world());var layer_sha: String=app.layers[1].cels[0].image.get_data().hex_encode().sha256_text()
	var reference: Image=await app.renderer.capture(app.keys,app.layers,10,true);reference.save_png(folder.path_join("saved-frame.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000011.png")).get_data(),"normal final-render assistance and editable cyan paint match the exported MP4 frame exactly")
	var unchanged:=true
	for source in hashes:unchanged=unchanged and FileAccess.get_sha256(source)==hashes[source]
	check(unchanged,"all original native assets stay byte-identical")
	var result:={"checks":checks,"failures":failures,"native_reports":reports,"project":path,"expected_world":expected,"pose_hashes":poses,"layer_sha":layer_sha,"movie":app.last_export_folder.path_join("movie.mp4")};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close();app.free();await settled();print("MOTION_ANIMATION "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder}));quit(0 if failures==0 else 1)

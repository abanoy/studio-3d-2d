extends "res://tests/foot_hold_smoke.gd"
const IK=preload("res://src/limb_ik.gd")
func numbers(value):
	if value is int:return float(value)
	if value is Array:
		var result: Array=[]
		for item in value:result.append(numbers(item))
		return result
	if value is Dictionary:
		var result: Dictionary={}
		for key in value:result[key]=numbers(value[key])
		return result
	return value
func stamp(value) -> String:return JSON.stringify(numbers(value),"",true,true)
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var direct:="--direct" in OS.get_cmdline_user_args()
	var asset:=folder.path_join("helper-figure.glb");check((preload("res://src/tutorial_assets.gd").figure(asset) if direct else preload("res://tests/helper_rig_fixture.gd").create(asset))==OK,"original helper-joint fixture exports real skinned GLB")
	if not FileAccess.file_exists(asset):quit(1);return
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");editor=app.pose_editor
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false;check(editor.add_model(asset,0,placement).is_empty(),"ordinary import preserves helper skeleton")
	var rig: RefCounted=editor.active_rig()
	if rig==null:await app.quit_studio();quit(1);return
	var actor: String=rig.data.id;var helpers: Dictionary={};var tips: Array=[]
	for id in rig.order:
		if rig.bones[id].name.begins_with("AuthoredHelper"):helpers[id]=rig.bones[id].skeleton.get_bone_pose(rig.bones[id].index)
		if IK.normalized(rig.bones[id].name) in ["handl","handr","footl","footr"]:tips.append(id)
	check(helpers.size()==(0 if direct else 8) and tips.size()==4,"all8rotated helper joints and four semantic limb tips survive import")
	editor.selected="@root";editor.operation.select(1);editor.refresh_values()
	for field in editor.fields:field.value=0
	editor.apply_numeric();app.mode.select(2);app.change_mode(2);editor.frame_model();app.keys=[Timeline.key(0,Vector3(0,1,4),Quaternion.IDENTITY,60)];editor.record_key();app.set_frame(12);var shots: Array=app.keys.duplicate(true);var neutral: Image=await app.renderer.capture(app.keys,[],0,true)
	for tip in tips:
		var limb:=IK.chain(rig,tip);check(not limb.is_empty() and (rig.parent_id(tip)==limb.ids[1] if direct else rig.parent_id(tip)!=limb.ids[1]),"semantic chain accepts actual intervening helper for "+tip)
		editor.begin_draft();var original: Dictionary=rig.data.duplicate(true);var start: Transform3D=rig.bone_transform(tip);var target:=start.origin+Vector3(-.035 if "left" in limb.role.to_lower() else .035,.045,.025)
		var solved:=IK.solve(rig,limb,target);check(not solved.has("error") and not solved.get("clamped",true),"helper limb produces reachable authored target for "+tip)
		if solved.has("error"):continue
		rig.data.pose=solved.pose;editor.apply_frame()
		print("HELPER_TARGET_ERROR ",rig.bone_transform(tip).origin.distance_to(target));check(rig.bone_transform(tip).origin.distance_to(target)<.0002 and absf(rig.bone_transform(tip).basis.get_rotation_quaternion().dot(start.basis.get_rotation_quaternion()))>.99999,"helper limb reaches exact target and preserves endpoint orientation")
		var untouched:=true
		for id in helpers:untouched=untouched and rig.bones[id].skeleton.get_bone_pose(rig.bones[id].index)==helpers[id] and not solved.pose.has(id)
		check(untouched,"solver preserves all authored helper transforms without adding helper keys")
		rig.data=original;editor.apply_frame()
	var no_mutation: Dictionary=rig.data.duplicate(true);var first_limb:=IK.chain(rig,tips[0]);var far:=IK.solve(rig,first_limb,Vector3(10000,10000,10000))
	check(not far.has("error") and far.clamped and rig.data==no_mutation,"unreachable limb target clamps without changing the live rig")
	var invalid:=IK.solve(rig,first_limb,Vector3(NAN,0,0));check(invalid.has("error") and rig.data==no_mutation,"nonfinite target refuses without pose mutation")
	var hand_before: Dictionary=rig.data.duplicate(true);var hand_at: Vector3=rig.bone_transform(tips[0]).origin;var hand_history: int=app.history.size()
	editor.tree_items[tips[0]].select(0);editor.selected=tips[0];editor.operation.select(1);editor.space.select(1);editor.refresh_values();await settled();await move(0,-.03)
	check(rig.bone_transform(tips[0]).origin.distance_to(hand_at+Vector3(-.03,0,0))<.0002 and app.history.size()==hand_history+1,"actual hand gizmo uses helper-aware IK and creates one Undo")
	var hand_after: Dictionary=rig.data.duplicate(true);app.undo();check(rig.data==hand_before,"hand gizmo Undo restores exact helper pose");app.redo();check(rig.data==hand_after,"hand gizmo Redo restores exact authored limb keys")
	editor.selected="@root";editor.operation.select(1);editor.space.select(1);editor.hold_feet.button_pressed=true;editor.refresh_values();var pinned:=Hold.capture(rig,"@root");check(not pinned.has("error"),"Hold feet resolves both helper-bearing leg chains")
	var before: Dictionary=rig.data.duplicate(true);var count: int=app.history.size();numeric(1,-.12);await settled()
	check(error_of(rig,pinned)<.0002 and app.history.size()==count+1,"ordinary numeric crouch plants both helper feet in one Undo")
	var crouched: Dictionary=rig.data.duplicate(true);app.undo();check(rig.data==before,"Undo restores exact pre-crouch helper rig");app.redo();check(rig.data==crouched and error_of(rig,pinned)<.0002,"Redo replays authored FK with both planted feet")
	var picture: Image=await app.renderer.capture(app.keys,[],12,true);check(picture.get_data()!=neutral.get_data(),"authored IK and crouch visibly deform the rendered skin");picture.save_png(folder.path_join("expected.png"));var expected_pose:=stamp(rig.sample(12));var expected_keys:=stamp(rig.authored_keys())
	app.has_project.save_file(folder.path_join("Helper.has"),"packed");await wait_job();DirAccess.rename_absolute(asset,asset+".offline");app.has_project.open_file(folder.path_join("Helper.has"));await wait_job();rig=app.renderer.world_runtime.instances.get(actor)
	check(rig!=null and stamp(rig.sample(12))==expected_pose and stamp(rig.authored_keys())==expected_keys,"packed Open restores exact semantic FK and helper keys")
	picture=await app.renderer.capture(app.keys,[],12,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected.png")).get_data(),"reopened helper skin final render matches authored pose exactly")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session));var recovered_pose:=false
	if not recovered.has("error"):
		for row in recovered.world.objects:
			if row.id==actor:recovered_pose=stamp(Support.keys(row))==expected_keys
	check(recovered_pose,"background checkpoint preserves authored helper-bearing semantic keys")
	var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==picture.get_data(),"actual exported frame equals reopened helper skin exactly")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(stamp(app.keys)==stamp(shots),"helper IK and crouch never change camera keys")
	DirAccess.rename_absolute(asset+".offline",asset);print("HELPER_LIMB "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"direct":direct}));await app.quit_studio();quit(0 if failures==0 else 1)

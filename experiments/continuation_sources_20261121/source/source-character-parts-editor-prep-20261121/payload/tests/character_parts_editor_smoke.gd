extends SceneTree
# Strict headless synthetic app/control test. No pixels or native input approval.
const F=preload("res://tests/character_parts_fixture.gd")
const Parts=preload("res://src/character_parts.gd")
const World=preload("res://src/world_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var app
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Character parts editor watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
func empty_variant(path: String,field: String,value: Array) -> Error:
	var error: Error=SceneIO.make_empty(path)
	if error!=OK:return error
	var bytes: PackedByteArray=FileAccess.get_file_as_bytes(path)
	var length: int=bytes.decode_u32(12)
	var data: Dictionary=JSON.parse_string(bytes.slice(20,20+length).get_string_from_utf8())
	data.nodes[0][field]=value
	var encoded: PackedByteArray=JSON.stringify(data).to_utf8_buffer()
	while encoded.size()%4!=0:encoded.append(32)
	var tail: PackedByteArray=bytes.slice(20+length)
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file==null:return FileAccess.get_open_error()
	for number in [0x46546c67,2,20+encoded.size()+tail.size(),encoded.size(),0x4e4f534a]:file.store_32(number)
	file.store_buffer(encoded);file.store_buffer(tail);file.flush();error=file.get_error();file.close();return error
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=2 or DisplayServer.get_name()!="headless":push_error("Expected headless mode, one owned output folder and one isolated profile name");quit(2);return
	if args[1].is_empty() or not OS.get_user_data_dir().replace("\\","/").ends_with("/"+args[1]):push_error("Expected the exact isolated character-parts profile");quit(2);return
	var folder: String=ProjectSettings.globalize_path(args[0]).simplify_path()
	var output: String=ProjectSettings.globalize_path("res://output").simplify_path()
	if not folder.begins_with(output+"/") or DirAccess.dir_exists_absolute(folder):push_error("Use a fresh descendant of this runtime's output");quit(2);return
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:quit(2);return
	var group_path: String=folder.path_join("group.glb");var rig_path: String=folder.path_join("rig.glb")
	check(SceneIO.make_empty(group_path)==OK and SceneIO.make_pose_fixture(rig_path)==OK,"real inert root and independent synthetic rig asset are created")
	var sources: Dictionary={group_path:FileAccess.get_sha256(group_path),rig_path:FileAccess.get_sha256(rig_path)}
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json")
	root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	root.add_child(app);await settle();app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("project-cache")
	check(app.new_project(),"ordinary New establishes an empty isolated app before assembly")
	var editor: Node=app.character_parts_editor
	var group: Dictionary=World.object(group_path,"group","Junko parts");group.id="junko"
	var incoming: Dictionary=F.inputs(rig_path,sources[rig_path])
	var old_world: Dictionary=app.current_world().duplicate(true);var old_keys: Array=app.keys.duplicate(true)
	var history: int=app.history.size()
	check(editor.inert_group_error(group_path).is_empty() and not editor.inert_group_error(rig_path).is_empty() and not editor.inert_group_error(group_path,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb").is_empty(),"real root admission refuses nonempty assets and wrong checksums")
	for field in ["translation","scale"]:
		var path: String=folder.path_join(field+"-empty.glb")
		var value: Array=[1,0,0] if field=="translation" else [2,2,2]
		var made: Error=empty_variant(path,field,value)
		var decoded: Dictionary=SceneIO.load_glb(path) if made==OK else {"error":"fixture write failed"}
		check(not decoded.has("error") and not editor.inert_group_error(path).is_empty(),"valid nonidentity empty group refuses: "+field)
		if not decoded.has("error"):decoded.scene.free()
		sources[path]=FileAccess.get_sha256(path)
	check(editor.install_bundle(group,incoming,F.policy(),2.).is_empty(),"actual app installs seven rows through its ordinary atomic world path")
	check(app.history.size()==history+1 and app.history[-1].type=="world","whole assembly is one real Undo transaction")
	var runtime: RefCounted=app.renderer.world_runtime
	if runtime==null:app.free();quit(1);return
	var assembled: Dictionary=app.current_world().duplicate(true)
	check(runtime.instances.size()==7 and runtime.instance("junko").bones.is_empty(),"inert parent owns no child rig inventory")
	var skeletons:={};var bound:=true;var ownership:=true
	for role in Parts.ROLES:
		var actor: RefCounted=runtime.instance(role)
		bound=bound and actor.root.get_parent()==runtime.instance("junko").root and actor.bones.size()==2
		for bone in actor.bones.values():skeletons[bone.skeleton.get_instance_id()]=true
		ownership=ownership and actor.data.metadata.fixture_owner==role
	check(bound and skeletons.size()==6 and ownership,"same bone labels remain six separately inventoried skeletons")
	var body: RefCounted=runtime.instance("body");var hair: RefCounted=runtime.instance("hair")
	var body_arm:="";var hair_arm:=""
	for id in body.order:
		if body.bones[id].name=="arm":body_arm=id
	for id in hair.order:
		if hair.bones[id].name=="arm":hair_arm=id
	var independent:=false
	if not body_arm.is_empty() and not hair_arm.is_empty():
		runtime.evaluate(0,false,"",app.video)
		var body_before: Transform3D=body.bone_transform(body_arm);var hair_before: Transform3D=hair.bone_transform(hair_arm)
		var saved_hair: Dictionary=hair.data.duplicate(true);var posed_hair: Dictionary=saved_hair.duplicate(true)
		var q:=Quaternion(Vector3.RIGHT,0.4)
		posed_hair.pose={hair_arm:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}}
		var applied: String=runtime.restore_instance("hair",posed_hair);runtime.evaluate(0,false,"hair",app.video)
		independent=applied.is_empty() and body.bone_transform(body_arm)==body_before and hair.bone_transform(hair_arm)!=hair_before
		independent=runtime.restore_instance("hair",saved_hair).is_empty() and independent;runtime.evaluate(0,false,"",app.video)
	check(independent,"posing one hair rig cannot overwrite the body's identically named bone")
	check(app.keys==old_keys and not app.physics_editor.is_running(),"assembly authors no camera keys or automatic physics")
	app.undo();check(app.current_world()==old_world,"actual Undo removes the entire newly installed bundle")
	app.redo();check(app.current_world()==assembled,"actual Redo restores exact assembled world")
	runtime=app.renderer.world_runtime
	var root_before: Dictionary=runtime.instance("junko").data.duplicate(true)
	var moved: Dictionary=root_before.duplicate(true);moved.position=[3,2,-1]
	check(runtime.restore_instance("junko",moved).is_empty(),"ordinary root transform edit is admitted")
	runtime.evaluate(0,false,"",app.video)
	var aligned:=true
	for role in Parts.ROLES:
		var actor: RefCounted=runtime.instance(role)
		aligned=aligned and actor.root.global_transform==runtime.instance("junko").root.global_transform*actor.base_root and actor.data.scale==1
	check(aligned and runtime.instance("junko").data.scale==2.,"one group move/scale preserves each prepared origin without double normalization")
	check(runtime.restore_instance("junko",root_before).is_empty(),"temporary alignment probe restores authored root")
	app.set_frame(12);await settle();history=app.history.size()
	app.world_selection.select_entity("hair",false);app.world_selection.context_action(4);await settle()
	check(editor.dialog.visible and editor.switches.size()==6,"Manage parts opens six controls from a child selection")
	var first_dialog: Window=editor.dialog
	editor.open("junko")
	check(editor.dialog!=first_dialog and editor.dialog.visible and not first_dialog.visible,"reopening hides the old exclusive dialog before replacement")
	editor.dialog.hide()
	var other_dialog:=AcceptDialog.new();other_dialog.exclusive=true;app.add_child(other_dialog);other_dialog.popup_centered(Vector2i(240,120))
	var held_dialog: Window=editor.dialog;editor.open("junko")
	check(editor.dialog==held_dialog and not editor.dialog.visible,"a foreign exclusive dialog blocks opening without replacing its own hidden Parts window")
	other_dialog.hide();other_dialog.queue_free();editor.open("hair");await settle()
	for role in Parts.OUTFITS:
		editor.preset_buttons[role].pressed.emit()
		var correct:=true
		for other in Parts.OUTFITS:correct=correct and editor.switches[other].button_pressed==(other==role)
		check(correct,"single-part clothes button signal chooses its own part: "+role)
	editor.switches.hair.button_pressed=false;editor.switches.mask.button_pressed=true
	editor.preset_buttons.dress.pressed.emit();editor.apply_visibility();await settle()
	check(app.history.size()==history+1 and app.history[-1].type=="world_objects" and app.history[-1].after.size()==3,"hair/mask/outfit apply creates one existing multi-object Undo")
	var after: Dictionary=app.current_world().duplicate(true);var rows: Dictionary=Parts.indexed(after)
	check(not Parts.Visibility.target(rows.hair,12) and Parts.Visibility.target(rows.mask,12) and Parts.Visibility.target(rows.dress,12) and not Parts.Visibility.target(rows.skirt,12),"requested per-part and outfit states are keyed at current frame")
	check(Parts.Visibility.target(rows.hair,11) and not Parts.Visibility.target(rows.mask,11),"preceding frame visibility is preserved")
	check(rows.junko==Parts.indexed(assembled).junko and rows.body==Parts.indexed(assembled).body and app.keys==old_keys,"part changes leave body/root/camera and independent source state untouched")
	app.undo();check(app.current_world()==assembled,"one actual Undo restores all three visibility changes")
	app.redo();check(app.current_world()==after,"one actual Redo restores the exact part states")
	editor.open("junko");await settle();history=app.history.size();app.set_frame(13)
	editor.switches.hair.button_pressed=true;editor.apply_visibility()
	check(app.history.size()==history and app.current_world()==after,"stale frame refuses without partial visibility/history mutation")
	editor.dialog.hide();app.set_frame(12);editor.open("junko");await settle();history=app.history.size()
	app.begin_recovery_session();editor.switches.hair.button_pressed=true;editor.apply_visibility()
	check(app.history.size()==history and app.current_world()==after and app.frame==12,"new session with equal World and frame refuses the old pending dialog")
	editor.dialog.hide();editor.open("junko");await settle()
	var owner_before: String=app.sequence_editor.active_owner
	app.sequence_editor.active_owner="synthetic-other-owner";editor.switches.hair.button_pressed=true;editor.apply_visibility();app.sequence_editor.active_owner=owner_before
	check(app.history.size()==history and app.current_world()==after,"same-data synthetic sequence-owner change refuses before committing")
	var duration_before: int=app.video.duration_frames
	app.video.duration_frames=duration_before-1;editor.apply_visibility();app.video.duration_frames=duration_before
	check(app.history.size()==history and app.current_world()==after,"same-data synthetic video change refuses before committing")
	editor.dialog.hide();editor.open("junko");await settle()
	for control in editor.switches.values():control.button_pressed=false
	editor.apply_visibility();editor.dialog.hide();app.world_selection.select_entity("junko",false)
	var parts_action: Button
	for action in app.world_selection.actions:
		if action.text=="Manage parts…":parts_action=action
	if parts_action:parts_action.pressed.emit();await settle()
	check(parts_action!=null and editor.dialog.visible,"World action reopens Parts even when all member geometry is hidden")
	editor.dialog.hide();app.undo();check(app.current_world()==after,"hide-all recovery probe leaves exact authored part states restored")
	var snapshot: String=folder.path_join("snapshot")
	var expected_file:=FileAccess.open(folder.path_join("expected-world.json"),FileAccess.WRITE)
	if expected_file==null:app.free();quit(2);return
	expected_file.store_string(JSON.stringify(World.portable(after),"\t",true,true));expected_file.flush()
	if expected_file.get_error()!=OK:app.free();quit(2);return
	expected_file.close()
	var why: String=Storage.save_project(snapshot,app.video,app.keys,[],"",12,{}, {},{},true,app.current_world())
	check(why.is_empty(),"ordinary portable project writer retains root and all hidden parts")
	var loaded: Dictionary=Storage.load_project(snapshot)
	check(not loaded.has("error") and World.portable(loaded.world)==JSON.parse_string(JSON.stringify(World.portable(after),"",true,true)),"same-process portable reload preserves all static memberships and visibility fields")
	if not loaded.has("error"):
		var prepared: Dictionary=preload("res://src/world_runtime.gd").prepare(loaded.world,int(app.video.duration_frames),app.video)
		check(not prepared.has("error"),"separate runtime can load portable managed group/rig assets")
		if not prepared.has("error"):prepared.runtime.dispose()
	var unchanged:=true
	for source in sources:unchanged=unchanged and FileAccess.get_sha256(source)==sources[source]
	check(unchanged,"all generated source assets remain byte-identical")
	app.free();await process_frame
	var report: Dictionary={"checks":checks,"failures":failures,"synthetic_only":true,"headless_controls":true,"native_pixels_or_input_qualified":false,"same_process_portable_reload":true,"fresh_process_cold_read_qualified":false,"actual_six_MDL_conversion_or_alignment_qualified":false,"bone_following_qualified":false}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	if file==null:push_error("Cannot retain character parts result");quit(2);return
	file.store_string(JSON.stringify(report,"\t",true,true));file.flush()
	if file.get_error()!=OK:quit(2);return
	file.close();print("CHARACTER_PARTS_EDITOR "+JSON.stringify(report));quit(1 if failures else 0)

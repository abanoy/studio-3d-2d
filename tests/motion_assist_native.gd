extends SceneTree

# Project JSON has one number type. Compare exact values after the same numeric
# conversion for live and reopened transforms (identity may begin as integers).
static func sampled_motion_hash(actor: RefCounted,at: float) -> String:
	var raw:=JSON.stringify({"pose":actor.sample(at),"root":actor.sample_transform(at)},"",true,true)
	return JSON.stringify(JSON.parse_string(raw),"",true,true).sha256_text()
const Model=preload("res://src/model.gd")
const Preview=preload("res://src/motion_assist_preview.gd")
const World=preload("res://src/world_document.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
const T=Model.Timeline
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Motion assist native watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func snapshot(actor: RefCounted) -> Array:
	var result: Array=[actor.root.transform]
	for id in actor.order:
		var info: Dictionary=actor.bones[id];result.append([info.skeleton.get_bone_pose_position(info.index),info.skeleton.get_bone_pose_rotation(info.index),info.skeleton.get_bone_pose_scale(info.index)])
	return result
func arm(actor: RefCounted) -> String:
	var humanoid: Dictionary=actor.data.metadata.get("humanoid",{})
	if humanoid.get("leftUpperArm","") in actor.order:return humanoid.leftUpperArm
	for suffix in ["::左腕","::ValveBiped.Bip01_L_UpperArm","::bip_upperArm_L","::J_Bip_L_UpperArm"]:
		for id in actor.order:
			if id.ends_with(suffix):return id
	return ""
func setup(plan: Dictionary) -> RefCounted:
	app.new_project();var row:=World.object(plan.source,"model",plan.name);row.id="actor";row.metadata=plan.metadata.duplicate(true)
	var base: Dictionary=plan.get("body_base_transform",plan);row.rotation_xyzw=base.rotation_xyzw.duplicate();row.scale=base.scale
	var world:=World.empty();world.objects=[row];check(app.restore_world(world).is_empty(),"native standard model installs: "+plan.name)
	app.set_frame(0);var actor: RefCounted=app.renderer.world_runtime.instance(row.id);var legs: Array=actor.contact_legs();var pin:=Contacts.capture(actor,0,49,"motion-pin")
	var hip: Vector3=actor.bone_transform(legs[0].ids[0]).origin;var foot: Vector3=actor.bone_transform(legs[0].ids[2]).origin;var down: Vector3=(foot-hip)*.12;var id:=arm(actor)
	check(not id.is_empty() and not pin.has("error"),"native arm and two supported foot bindings resolve: "+plan.name)
	if id.is_empty() or pin.has("error"):return actor
	for at in [0,12,24]:
		var transform:=Model.Clips.transform(actor.data);var p: Vector3=down*(2. if at==12 else 1.);transform.position=[p.x,p.y,p.z]
		var pose: Dictionary={};var value:=Model.identity();var q:=Quaternion(Vector3.FORWARD,.8 if at==12 else 0.);value.rotation_xyzw=[q.x,q.y,q.z,q.w];pose[id]=value
		check(actor.put_pose_key({"frame":at,"pose":pose,"transform":transform,"authored_channels":["@root",id],"interpolation":"ease"},48,false,actor.data.duplicate(true)).is_empty(),"author native root and arm main key "+str(at)+": "+plan.name)
	var planted:=Ranges.edit(actor.data,0,49,pin.segments[0],48)
	check(not planted.has("error") and app.renderer.world_runtime.restore_instance(row.id,planted.data).is_empty(),"continuous contacts wrap the original three keys: "+plan.name)
	app.create_cel(false);preload("res://src/drawing.gd").stroke(preload("res://src/drawing.gd").edit_image(app.layers[1].cels[0]).image,Vector2(40,40),Vector2(140,40),8,Color.CYAN,false)
	app.set_frame(0);return app.renderer.world_runtime.instance(row.id)
func make_preview(actor: RefCounted) -> RefCounted:
	var id:=arm(actor);var tracks:={"@root":[],id:[]}
	for at in [0,12,24]:
		tracks["@root"].append({"frame":at,"value":actor.sample_transform(at),"interpolation":"ease"})
		tracks[id].append({"frame":at,"value":actor.sample_body(at).get(id,Model.identity()),"interpolation":"ease"})
	var preview:=Preview.new();check(preview.configure(actor,tracks,app.video,{"strength":.65,"distance_scale":actor.data.scale,"position_limit":.02}).is_empty(),"derive assistance from native authored controls: "+actor.data.name)
	var expected: Dictionary=preview.helper_keys();var wrong: Dictionary=tracks.duplicate(true);wrong[id][0].interpolation="hold"
	check(not preview.configure(actor,wrong,app.video).is_empty() and preview.helper_keys()==expected,"wrong easing refuses transactionally instead of replacing the authored curve: "+actor.data.name)
	wrong=tracks.duplicate(true);wrong[id].remove_at(1)
	check(not preview.configure(actor,wrong,app.video).is_empty() and preview.helper_keys()==expected,"omitted middle main control refuses without replacing a valid preview: "+actor.data.name)
	return preview
func visible_preview(actor: RefCounted,preview: RefCounted,at: int) -> void:
	app.set_frame(at);var evaluated: Dictionary=preview.evaluate_preview(at)
	if evaluated.has("error"):check(false,evaluated.error);return
	actor.preview_frame=at;actor.preview_pose=evaluated.pose;actor.preview_transform=evaluated.transform;actor.apply(at,false,false,app.video)
func clear_preview(actor: RefCounted) -> void:
	actor.preview_frame=-1;actor.preview_pose={};actor.preview_transform={};actor.apply(app.frame,false,false,app.video)
func case_for(plan: Dictionary) -> Dictionary:
	var start:=checks;var first:=failures;var actor:=setup(plan);var id:=arm(actor)
	if id.is_empty():return {"name":plan.name,"checks":checks-start,"failures":failures-first}
	var supplied:=make_preview(actor);var preview:=Preview.new();check(preview.configure_document(actor,["@root",id],app.video,{"strength":.65,"distance_scale":actor.data.scale,"position_limit":.02}).is_empty(),"derive complete native part curves directly from timeline records: "+plan.name)
	var equivalent:=true
	for half in range(97):
		var at:=float(half)/2;equivalent=equivalent and Preview.matching(preview.sample_transform(at),supplied.sample_transform(at)) and Preview.matching(preview.sample_body(at).get(id,Model.identity()),supplied.sample_body(at).get(id,Model.identity()))
	check(equivalent,"source-time compiler retains the established native three-key acting: "+plan.name)
	var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var state:=snapshot(actor);var paint: PackedByteArray=preload("res://src/drawing.gd").image(app.layers[1].cels[0]).get_data()
	app.world_selection.select_entity("actor");app.pose_editor.frame_model();app.world_selection.clear()
	app.keys=[T.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var shots: Array=app.keys.duplicate(true)
	var all_exact:=true;var reachable:=true;var read_only:=true;var values:=[]
	for half in range(97):
		var at:=float(half)/2;values.append(preview.sample(at));reachable=reachable and preview.evaluation_error.is_empty();read_only=read_only and snapshot(actor)==state
	for half in range(96,-1,-1):all_exact=all_exact and preview.sample(float(half)/2)==values[half]
	check(reachable,"derived native motion remains reachable at all97 half frames: "+plan.name)
	check(read_only and snapshot(actor)==state,"contact sampling restores the exact displayed native root/bones: "+plan.name)
	check(all_exact,"derived native poses are identical when seeking backwards: "+plan.name)
	all_exact=true
	for at in [0,12,24]:all_exact=all_exact and preview.sample(at)==actor.sample(at) and preview.sample_transform(at)==actor.sample_transform(at)
	check(all_exact,"all three main native poses and root transforms stay exact: "+plan.name)
	check(preview.evaluate_preview(-1).has("error") and preview.evaluate_preview(NAN).has("error") and preview.evaluate_preview(49).has("error"),"invalid native preview queries refuse explicitly: "+plan.name)
	preview.gain=NAN;check(preview.evaluate_preview(10).has("error"),"nonfinite native strength refuses explicitly: "+plan.name);preview.gain=1.
	actor.data.name+=" changed";check(preview.evaluate_preview(10).has("error"),"stale helpers refuse after main-data changes: "+plan.name);actor.data.name=before.name
	preview.gain=0.;all_exact=true
	for half in range(97):all_exact=all_exact and preview.sample(float(half)/2)==actor.sample(float(half)/2) and preview.sample_transform(float(half)/2)==actor.sample_transform(float(half)/2)
	check(all_exact,"turning assistance off restores exact native contact animation: "+plan.name);preview.gain=1.
	var peak:=0.;var peers_exact:=true;var changed:=false
	for at in range(49):
		visible_preview(actor,preview,at)
		for foot in Contacts.active(actor.data.animation_clips,at).get("feet",[]):peak=maxf(peak,actor.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
		var body: Dictionary=preview.sample_body(at);var original: Dictionary=actor.sample_body(at)
		for part in original:
			if part!=id:peers_exact=peers_exact and body.get(part)==original[part]
		changed=changed or body.get(id)!=original.get(id)
	check(peak<.0002,"actual displayed feet stay pinned during generated root/arm motion: "+plan.name)
	check(peers_exact and changed,"only selected arm receives acting before standard leg solving: "+plan.name)
	clear_preview(actor);app.set_frame(10);await settled()
	var original: Image=await app.renderer.capture(app.keys,app.layers,10,false);visible_preview(actor,preview,10);var assisted: Image=await app.renderer.capture(app.keys,app.layers,10,false)
	original.save_png(folder.path_join("%s-before.png" % plan.id));assisted.save_png(folder.path_join("%s-assisted.png" % plan.id))
	check(original.get_data()!=assisted.get_data(),"actual GPU skin changes with derived acting: "+plan.name)
	preview.gain=0.;visible_preview(actor,preview,10);var off: Image=await app.renderer.capture(app.keys,app.layers,10,false)
	check(original.get_data()==off.get_data(),"assistance Off restores the exact original GPU picture: "+plan.name);preview.gain=1.
	clear_preview(actor);var final_before: Image=await app.renderer.capture(app.keys,app.layers,10,true);visible_preview(actor,preview,10);var final_during: Image=await app.renderer.capture(app.keys,app.layers,10,true)
	check(final_before.get_data()==final_during.get_data(),"normal final rendering remains isolated from experimental preview helpers: "+plan.name)
	# A generated diagnostic, not native HAS persistence or normal Export support.
	if plan.id=="native-4":
		var movie_folder:=folder.path_join("preview-movie");DirAccess.make_dir_recursive_absolute(movie_folder)
		for at in range(48):
			visible_preview(actor,preview,at);var image: Image=await app.renderer.capture(app.keys,app.layers,at,false);image.save_png(movie_folder.path_join("frame_%06d.png" % (at+1)))
		var encoder:=preload("res://src/encoder.gd").new();check((await encoder.encode(self,"C:/Program Files/ffmpeg/bin/ffmpeg.exe",movie_folder,app.video)).is_empty(),"experimental derived poses render to a48frame diagnostic MP4")
	clear_preview(actor);check(actor.data==before and app.keys==shots and app.history.size()==history and preload("res://src/drawing.gd").image(app.layers[1].cels[0]).get_data()==paint,"preview preserves authored data/history/camera and independent editable paint: "+plan.name)
	# Real native source slices: trim the recorded take to its three main keys,
	# split BETWEEN controls, then move its right slice while retaining foot pins.
	var trimmed: Dictionary=before.duplicate(true);trimmed.animation_clips=[trimmed.animation_clips[0]];trimmed.animation_clips[0].length=25
	check(app.renderer.world_runtime.restore_instance("actor",trimmed).is_empty(),"native source take trims without flattening its controls: "+plan.name)
	app.set_frame(0);var complete:=Preview.new();complete.configure_document(actor,["@root",id],app.video,{"distance_scale":actor.data.scale,"position_limit":.02});var originals:=[]
	for half in range(97):originals.append(complete.sample(float(half)/2))
	var split:=Model.Clips.split(trimmed,8);var split_preview:=Preview.new();check(not split.has("error") and app.renderer.world_runtime.restore_instance("actor",split.data).is_empty() and split_preview.configure_document(actor,["@root",id],app.video,{"distance_scale":actor.data.scale,"position_limit":.02}).is_empty(),"native timeline split compiles retained source controls: "+plan.name)
	var split_exact:=true
	for half in range(97):split_exact=split_exact and split_preview.sample(float(half)/2)==originals[half]
	check(split_exact,"native split preserves exact assisted solved poses at all97 half frames: "+plan.name)
	var moved:=Model.Clips.move(split.data,split.right_id,20,48);var moved_preview:=Preview.new()
	if moved.has("error"):
		check(false,"native moved fixture: "+str(moved.error));return {"name":plan.name,"checks":checks-start,"failures":failures-first}
	var install_error: String=app.renderer.world_runtime.restore_instance("actor",moved.data)
	var preview_error: String=moved_preview.configure_document(actor,["@root",id],app.video,{"distance_scale":actor.data.scale,"position_limit":.02}) if install_error.is_empty() else install_error
	check(preview_error.is_empty(),"native moved slice and recorded gap compile together: "+plan.name+" "+preview_error)
	if not preview_error.is_empty():return {"name":plan.name,"checks":checks-start,"failures":failures-first}
	var relative_exact:=true
	for half in range(33):relative_exact=relative_exact and moved_preview.sample(20.+float(half)/2)==originals[16+half]
	check(relative_exact,"native moved slice retains exact relative solved helper poses: "+plan.name)
	var moved_samples:=[];var moved_ok:=true;var gap_peak:=0.
	for half in range(97):
		var evaluated: Dictionary=moved_preview.evaluate_preview(float(half)/2);moved_ok=moved_ok and not evaluated.has("error");moved_samples.append(evaluated)
	for half in range(96,-1,-1):moved_ok=moved_ok and moved_preview.evaluate_preview(float(half)/2)==moved_samples[half]
	for at in range(49):
		visible_preview(actor,moved_preview,at)
		for foot in Contacts.active(actor.data.animation_clips,at).get("feet",[]):gap_peak=maxf(gap_peak,actor.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	check(moved_ok and gap_peak<.0002,"native gap/trimmed tail stay reachable, reversible and visibly planted: "+plan.name)
	clear_preview(actor);check(actor.data==moved.data and app.keys==shots and app.history.size()==history and preload("res://src/drawing.gd").image(app.layers[1].cels[0]).get_data()==paint,"native slice preview leaves records, explicit shots, history and paint untouched: "+plan.name)
	app.renderer.world_runtime.restore_instance("actor",before);app.set_frame(0)
	return {"name":plan.name,"bones":actor.order.size(),"checks":checks-start,"failures":failures-first,"foot_error":peak,"gap_foot_error":gap_peak,"helpers":preview.helper_keys()}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1])
	while app.has_project.pid>0:await process_frame
	await settled();var plans:=[];var hashes:={}
	for row in app.current_world().objects:
		if row.get("format")==Model.CONTACT_FORMAT:plans.append(row);hashes[row.source]=FileAccess.get_sha256(row.source)
	check(plans.size()==5,"five representative native MMD/GMod/SFM/VRM rigs available")
	var reports:=[]
	for plan in plans:reports.append(await case_for(plan))
	var unchanged:=true
	for source in hashes:unchanged=unchanged and FileAccess.get_sha256(source)==hashes[source]
	check(unchanged,"all original native source bytes unchanged")
	var result:={"checks":checks,"failures":failures,"native_reports":reports,"normal_editor_integrated":false};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("MOTION_ASSIST_NATIVE "+JSON.stringify(result));quit(0 if failures==0 else 1)

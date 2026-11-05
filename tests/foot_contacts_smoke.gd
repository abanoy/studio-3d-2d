extends SceneTree
const Contacts=preload("res://src/foot_contacts.gd")
const Hold=preload("res://src/foot_hold.gd")
const T=preload("res://src/timeline.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Support=preload("res://tests/world_test_support.gd")
var checks:=0
var failures:=0
var app
var folder: String

func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Contact experiment watchdog");quit(2))
	call_deferred("run")
func check(value: bool, message: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+message)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func maximum_error(rig, segment: Dictionary) -> float:
	var error:=0.
	for foot in segment.feet:error=maxf(error,rig.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	return error
func experiment(rig, label: String) -> Dictionary:
	rig.apply(0,false,false,app.video)
	var track:=Contacts.capture(rig,0,25,"contact-"+label)
	check(not track.has("error") and Contacts.check_bindings(rig,track).is_empty(),"capture both native leg bindings and world targets: "+label)
	if track.has("error"):return {}
	var parser:=JSON.new();parser.parse(JSON.stringify(track,"",true,true));var decoded: Dictionary=parser.data
	var exact:=Contacts.check_bindings(rig,decoded).is_empty();var raw_error:=0.
	for i in range(2):
		var a: Dictionary=track.segments[0].feet[i];var b: Dictionary=decoded.segments[0].feet[i]
		exact=exact and a.ids==b.ids and T.vector(a.position)==T.vector(b.position) and T.quaternion(a.rotation_xyzw)==T.quaternion(b.rotation_xyzw)
		for axis in range(3):raw_error=maxf(raw_error,absf(float(a.position[axis])-float(b.position[axis])))
	check(exact,"decoded contact retains exact engine vectors/quaternions and bindings: "+label)
	print("RAW_JSON_POSITION_DELTA ",label," ",raw_error)
	track=decoded
	var original: Dictionary=rig.data.duplicate(true);var pose: Dictionary=rig.sample(0)
	var legs:=Hold.chains(rig);var upper: Vector3=rig.bone_transform(legs[0].ids[0]).origin
	var down: Vector3=(T.vector(track.segments[0].feet[0].position)-upper).normalized()
	var height: float=upper.distance_to(T.vector(track.segments[0].feet[0].position))
	var initial: Transform3D=rig.root.global_transform
	var peak:=0.;var repeats:=[];var outputs:=[];var errors:=0
	# Every half-frame, deliberately nonmonotonic on the second pass. Reset input each time.
	for pass_index in range(2):
		var frames:=range(49)
		if pass_index==1:frames.reverse()
		for value in frames:
			var t:=float(value)/48.;var weight:=t*t*(3.-2.*t)
			rig.root.global_transform=initial;rig.root.global_position+=down*height*.2*weight
			var solved:=Contacts.resolve(rig,pose,Contacts.at(track,t*24.))
			if solved.has("error"):errors+=1;print("CONTACT_ERROR ",label," ",value," ",solved.error);continue
			peak=maxf(peak,maximum_error(rig,track.segments[0]))
			if pass_index==0:outputs.append(solved.pose)
			else:repeats.append(solved.pose==outputs[value])
	check(errors==0 and peak<.0002,"continuous half-frame planted endpoints stay fixed: "+label)
	check(repeats.size()==49 and repeats.all(func(value):return value),"reverse-order seeks reproduce exact solved FK: "+label)
	check(rig.data==original,"continuous solve never authors model data or keys: "+label)
	var bad:=track.duplicate(true);bad.segments[0].feet[1].ids[0]="missing"
	check(not Contacts.check_bindings(rig,bad).is_empty(),"native binding mismatch refuses before evaluation: "+label)
	# An impossible second foot must restore the entire original skeleton, not half a solve.
	rig.root.global_transform=initial;Contacts.apply_pose(rig,pose)
	var baseline:=[]
	for id in rig.order:baseline.append(rig.bone_transform(id))
	bad=track.duplicate(true);bad.segments[0].feet[1].position=[99999,99999,99999]
	var failed:=Contacts.resolve(rig,pose,bad.segments[0]);var restored:=true
	for i in range(rig.order.size()):restored=restored and rig.bone_transform(rig.order[i]).is_equal_approx(baseline[i])
	check(failed.has("error") and restored and rig.data==original,"late right-foot reach failure restores whole input skeleton: "+label)
	# Root twist changes foot local rotations while the authored world orientation stays fixed.
	rig.root.global_transform=initial;rig.root.global_position+=down*height*.2
	rig.root.global_basis=Basis(Quaternion(down,.04))*rig.root.global_basis
	var twisted:=Contacts.resolve(rig,pose,track.segments[0])
	check(not twisted.has("error") and maximum_error(rig,track.segments[0])<.0002,"world orientation survives a body twist: "+label)
	rig.root.global_transform=initial;var released:=Contacts.resolve(rig,pose,{})
	var cleared: bool=released.pose==pose
	for i in range(rig.order.size()):cleared=cleared and rig.bone_transform(rig.order[i]).is_equal_approx(baseline[i])
	check(cleared,"releasing a contact clears the previous solved skeleton without history dependence: "+label)
	return {"track":track,"peak_error":peak,"samples":98,"raw_json_position_delta":raw_error}

func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	app.pose_editor.add_model(asset);var rig: RefCounted=app.renderer.active_model();app.pose_editor.frame_model();var authored:=experiment(rig,"original")
	if authored.is_empty():app.free();quit(1);return
	var track: Dictionary=authored.track
	var json:=JSON.stringify(track,"",true,true);var parser:=JSON.new();parser.parse(json)
	check(Contacts.validate(parser.data).is_empty() and int(parser.data.segments[0].from)==track.segments[0].from and int(parser.data.segments[0].to)==track.segments[0].to and parser.data.segments[0].id==track.segments[0].id,"full-precision contact JSON retains IDs and numeric source ranges")
	var bad:=track.duplicate(true);bad.segments[0].to=0;check(not Contacts.validate(bad).is_empty(),"empty range rejects")
	bad=track.duplicate(true);bad.segments.append(bad.segments[0].duplicate(true));check(not Contacts.validate(bad).is_empty(),"duplicate/overlapping contacts reject")
	bad=track.duplicate(true);bad.segments[0].feet[0].position[0]=NAN;check(not Contacts.validate(bad).is_empty(),"nonfinite targets reject")
	bad=track.duplicate(true);bad.segments[0].feet[0].rotation_xyzw=[0,0,0,2];check(not Contacts.validate(bad).is_empty(),"nonunit rotations reject")
	bad=track.duplicate(true);bad.segments[0].feet[1].ids[0]=bad.segments[0].feet[0].ids[0];check(not Contacts.validate(bad).is_empty(),"shared leg joints reject")
	var piece:={"id":"source","start":10,"length":25,"source_in":0,"foot_contacts":track}
	check(Contacts.active([piece],9).is_empty() and not Contacts.active([piece],10).is_empty() and not Contacts.active([piece],60).is_empty(),"presence-before-introduction and held final contact are distinct")
	var copy:=Contacts.active([piece],12);copy.feet[0].position[0]+=8
	check(piece.foot_contacts==track,"returned active contact cannot mutate saved source targets")
	var left:=piece.duplicate(true);left.length=8
	var right:=piece.duplicate(true);right.id="split";right.start=18;right.source_in=8;right.length=17
	check(Contacts.active([left,right],17.5)==Contacts.active([piece],17.5),"source-time split retains exact continuous contact")
	right.start=25
	check(Contacts.active([left,right],22)==track.segments[0],"moving split pieces apart bridges their identical declared contact")
	right.foot_contacts.segments[0].id="different-contact"
	check(Contacts.active([left,right],22).is_empty(),"different contacts do not invent a gap pin")
	right.erase("foot_contacts");check(Contacts.active([left,right],25).is_empty(),"an explicit unplanted piece releases the contact")
	# Render an actual midpoint with the same scene/world, no project or camera mutation.
	rig.apply(0,false,false,app.video);var before: Dictionary=rig.data.duplicate(true);var pose: Dictionary=rig.sample(0);rig.root.position.y-=.1
	Contacts.apply_pose(rig,pose);await settled();var free: Image=app.renderer.viewport.get_texture().get_image();free.save_png(folder.path_join("free-midpoint.png"))
	Contacts.resolve(rig,pose,track.segments[0]);await settled();var planted: Image=app.renderer.viewport.get_texture().get_image();planted.save_png(folder.path_join("planted-midpoint.png"))
	var visible:=0;var changed:=0
	for y in range(0,1080,3):
		for x in range(0,1920,3):
			var color:=planted.get_pixel(x,y)
			if color.r+color.g+color.b>.1:visible+=1
			if color!=free.get_pixel(x,y):changed+=1
	check(visible>1000 and changed>100 and maximum_error(rig,track.segments[0])<.0002,"actual lit-independent GPU skin changes at midpoint while planted endpoints remain fixed")
	check(rig.data==before and FileAccess.get_sha256(asset)==sha,"midpoint GPU render preserves original model and source bytes")
	var reports:={"original":authored}
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private "+sample);continue
		var loaded:=Storage.load_project(path);var row:=Support.legacy_model(World.from_project(loaded).objects[-1]);row.id="contact-native";row.parent_id="";row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0
		var original_sha:=FileAccess.get_sha256(row.source);app.new_project();var world:=World.empty();world.objects=[row];app.restore_world(world);app.world_selection.select_entity(row.id);rig=app.renderer.active_model()
		reports[sample]=experiment(rig,sample.replace("/","-"));check(FileAccess.get_sha256(row.source)==original_sha,"native binary remains unchanged: "+sample)
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private "+name);continue
		var original_sha:=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		await settled();rig=app.renderer.active_model()
		if not rig:check(false,"VRM worker completed");continue
		reports[name]=experiment(rig,name);check(FileAccess.get_sha256(path)==original_sha,"VRM input remains unchanged: "+name)
	var result:={"checks":checks,"failures":failures,"reports":reports,"folder":folder,"normal_editor_integration":false}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close()
	app.free();await settled();print("FOOT_CONTACTS_EXPERIMENT "+JSON.stringify(result));quit(0 if failures==0 else 1)

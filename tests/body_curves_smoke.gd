extends SceneTree
const B=preload("res://src/body_curves.gd")
const Model=B.Model
const Timeline=B.Timeline
const Fixture=preload("res://tests/body_curve_fixture.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Body curves GPU watchdog");quit(2));call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func find_bone(actor,suffix: String) -> String:
	for id in actor.order:
		if str(actor.bones[id].name).ends_with(suffix):return id
	return ""
func rotate(angle: float) -> Dictionary:
	var result:=Model.identity();var q:=Quaternion(Vector3.FORWARD,angle)
	result.rotation_xyzw=[q.x,q.y,q.z,q.w];return result
func preview(actor,data: Dictionary,frame: int) -> void:
	var state:=B.sample(data,frame);actor.preview_frame=frame;actor.preview_pose=state.pose;actor.preview_transform=state.transform
func equal(a,b) -> bool:return JSON.stringify(a)==JSON.stringify(b)
func canonical_equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func colors(image: Image) -> Dictionary:
	var bytes:=image.get_data();var blue:=0;var orange:=0
	for i in range(0,bytes.size(),32):
		if bytes[i+3]<250:continue
		if bytes[i+2]>bytes[i]*1.2 and bytes[i+2]>bytes[i+1]:blue+=1
		if bytes[i]>bytes[i+2]*1.2 and bytes[i]>bytes[i+1]:orange+=1
	return {"blue":blue,"orange":orange}
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var asset:=folder.path_join("branches.glb")
	check(Fixture.create(asset)==OK,"authored independent skin branches export a real test GLB")
	var plans: Array=[{"label":"Authored","source":asset,"metadata":{},"left":"left","right":"right"}]
	plans.append_array(JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json"))))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var metrics:={};var movie:=""
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);var actor: RefCounted=app.renderer.active_model()
		for field in plan.metadata:
			if field!="source_shape":actor.data.metadata[field]=plan.metadata[field]
		var left:=find_bone(actor,plan.left);var right:=find_bone(actor,plan.right)
		check(not left.is_empty() and not right.is_empty(),"native left/right identities resolve: "+plan.label)
		if left.is_empty() or right.is_empty():continue
		var source_hash:=FileAccess.get_sha256(actor.data.source);var native_ids: Array=actor.order.duplicate();var metadata: Dictionary=actor.data.metadata.duplicate(true)
		var original: Dictionary=actor.data.duplicate(true)
		for frame in [0,24]:
			var transform:=Model.Clips.transform(original);transform.position[0]+=0. if frame==0 else .4
			original.pose_keys.append({"frame":frame,"pose":{left:rotate(0. if frame==0 else .6)},"transform":transform,"interpolation":"ease"})
		check(app.pose_editor.restore_state(original).is_empty(),"normal editor accepts the baseline eased pose fixture: "+plan.label)
		app.set_frame(6);app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)];app.world_selection.select_entity("")
		var before: Image=await app.renderer.capture(app.keys,[],6,false);var root_before: Transform3D=actor.root.global_transform;var left_before: Transform3D=actor.bone_transform(left)
		var data:=B.extract(original);var updated:=B.put(data,12,{right:rotate(-.9)},"ease",48)
		check(not updated.has("error") and B.check_bindings(updated.data,native_ids).is_empty(),"independent controls bind to the existing standard rig: "+plan.label)
		if updated.has("error"):continue
		data=updated.data
		var body_exact:=true
		for half in range(97):
			var frame:=float(half)/2
			body_exact=body_exact and equal(B.sample_channel(data,frame,left),actor.sample(frame).get(left,Model.identity())) and equal(B.sample_channel(data,frame,"@root"),actor.sample_transform(frame))
		preview(actor,data,6);actor.apply(6);await settled();var after: Image=await app.renderer.capture(app.keys,[],6,false)
		check(body_exact and actor.root.global_transform==root_before and actor.bone_transform(left)==left_before,"rendered root and untouched native arm remain exact: "+plan.label)
		check(before.get_data()!=after.get_data(),"independent opposite arm visibly deforms actual GPU skin: "+plan.label)
		if plan.label=="Authored":
			before.save_png(folder.path_join("before.png"));after.save_png(folder.path_join("independent-preview.png"))
			print("AUTHORED_COLORS "+JSON.stringify({"before":colors(before),"after":colors(after)}))
			check(colors(before).blue>1000 and colors(before).orange>1000 and colors(after).blue>1000 and colors(after).orange>1000,"both skin branches remain positively visible after independent motion")
			var right_mesh: MeshInstance3D=actor.root.find_child("RightMesh",true,false)
			check(right_mesh!=null,"authored opposite branch can be isolated for pixel comparison")
			if right_mesh:
				right_mesh.visible=false;actor.preview_frame=-1;actor.apply(6);await settled();var isolated_before: Image=await app.renderer.capture(app.keys,[],6,false)
				preview(actor,data,6);actor.apply(6);await settled();var isolated_after: Image=await app.renderer.capture(app.keys,[],6,false)
				isolated_before.save_png(folder.path_join("isolated-before.png"));isolated_after.save_png(folder.path_join("isolated-after.png"))
				print("ISOLATED_COLORS "+JSON.stringify({"before":colors(isolated_before),"after":colors(isolated_after),"mesh":str(right_mesh.get_path())}))
				check(colors(isolated_before).blue>1000 and colors(isolated_after).blue>1000 and isolated_before.get_data()==isolated_after.get_data(),"positively visible untouched skin remains pixel-exact when the opposite branch changes")
				right_mesh.visible=true
		var began:=Time.get_ticks_usec()
		for frame in range(50):B.sample(data,float(frame%25))
		var average:=float(Time.get_ticks_usec()-began)/50.
		var json_path:=folder.path_join(plan.label+"-body-curves.json");var file:=FileAccess.open(json_path,FileAccess.WRITE);file.store_string(JSON.stringify(data));file.close()
		var reopened: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(json_path));var roundtrip_exact:=B.validate(reopened,48).is_empty()
		for half in range(97):roundtrip_exact=roundtrip_exact and equal(B.sample(data,float(half)/2),B.sample(reopened,float(half)/2))
		check(roundtrip_exact,"experimental internal contract survives JSON with exact sampled motion: "+plan.label)
		check(actor.data.metadata==metadata and actor.order==native_ids and FileAccess.get_sha256(actor.data.source)==source_hash,"experiment preserves native metadata, identities and original geometry: "+plan.label)
		# Diagnostic only: sample once into existing ordinary pose keys to verify
		# pixels/HAS/movie. This is not editable independent-track integration.
		var sampled: Dictionary=original.duplicate(true);sampled.pose_keys=[]
		for frame in range(49):
			var state:=B.sample(data,frame);sampled.pose_keys.append({"frame":frame,"pose":state.pose,"transform":state.transform,"interpolation":"linear"})
		var sampled_actor:=Model.new();sampled_actor.data=sampled;var conversion_difference:=0.
		for frame in range(49):
			var source:=B.sample(data,frame);var ordinary:=sampled_actor.sample(frame)
			for bone in source.pose:
				for field in ["position","rotation_xyzw"]:
					for i in range(source.pose[bone][field].size()):conversion_difference=maxf(conversion_difference,absf(float(source.pose[bone][field][i])-float(ordinary[bone][field][i])))
		actor.preview_frame=-1;actor.preview_pose={};actor.preview_transform={}
		app.world_selection.select_entity(actor.data.id);check(app.pose_editor.restore_state(sampled).is_empty(),"ordinary pose samples install for diagnostic portability: "+plan.label)
		app.set_frame(6);var expected: Image=await app.renderer.capture(app.keys,[],6,true)
		var id: String=actor.data.id;var path:=folder.path_join(plan.label+"-sampled.has");app.has_project.save_file(path,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(path);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id);app.set_frame(6);await settled()
		var replay_exact:=actor!=null and canonical_equal(actor.authored_keys(),sampled.pose_keys)
		if actor:
			for frame in range(49):
				replay_exact=replay_exact and equal(actor.sample(frame),sampled_actor.sample(frame)) and equal(actor.sample_transform(frame),sampled_actor.sample_transform(frame))
		check(replay_exact,"diagnostic HAS preserves sampled key payloads and exact pre-save ordinary evaluation: "+plan.label)
		if plan.label=="Authored":
			var reopened_pixels: Image=await app.renderer.capture(app.keys,[],6,true)
			check(reopened_pixels.get_data()==expected.get_data(),"authored diagnostic HAS preserves exact rendered body-motion pixels")
			Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
			var expected_overlay: Image=await app.renderer.capture(app.keys,app.layers,6,true)
			var error: String=await app.export_movie(folder);movie=app.last_export_folder.path_join("movie.mp4")
			check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000007.png")).get_data()==expected_overlay.get_data(),"diagnostic motion exports with independent drawing and exact preview pixels")
		metrics[plan.label]={"left":left,"right":right,"warm_sample_usec":average,"source_sha256":source_hash,"contract":json_path,"sampled_project":path,"ordinary_conversion_component_difference":conversion_difference}
	var result:={"checks":checks,"failures":failures,"metrics":metrics,"movie":movie,"normal_editor_integration":false}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("BODY_CURVES "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)

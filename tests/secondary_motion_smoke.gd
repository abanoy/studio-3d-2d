extends SceneTree
const Fixture=preload("res://tests/secondary_fixture.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Runner=preload("res://src/secondary_spring.gd")
const Model=preload("res://src/model.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Capture=preload("res://src/physics_recording.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
var folder: String
var metrics:={}
var movies: Array=[]
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Secondary watchdog expired");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func pose_distance(a: Dictionary,b: Dictionary) -> float:
	var result:=0.0
	for id in a:result=maxf(result,Timeline.quaternion(a[id].rotation_xyzw).angle_to(Timeline.quaternion(b.get(id,Model.identity()).rotation_xyzw)))
	return result
func pose_difference(a: Dictionary,b: Dictionary) -> float:
	var result:=0.0
	for id in a:
		var q:=Timeline.quaternion(a[id].rotation_xyzw);var r:=Timeline.quaternion(b.get(id,Model.identity()).rotation_xyzw)
		result=maxf(result,minf((Vector4(q.x,q.y,q.z,q.w)-Vector4(r.x,r.y,r.z,r.w)).length(),(Vector4(q.x,q.y,q.z,q.w)+Vector4(r.x,r.y,r.z,r.w)).length()))
	return result
func tick(actor,runner,wind: Vector3,t: float) -> Dictionary:
	actor.live_pose=null;actor.apply(0)
	# Sinusoidal body/anchor movement is explicit authored input, separate from
	# spring output; feed no previous simulation result back into the rest pose.
	actor.root.position.x=0.1*sin(t*2)
	return runner.step(1.0/120,wind)
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func baked(app,actor,label: String) -> void:
	actor.live_pose=null;actor.apply(0);var created: Dictionary=await Runner.create(actor)
	if created.has("error"):check(false,"bake runner starts: "+label);return
	var runner: RefCounted=created.runner;var keys: Array=[]
	for i in range(241):
		var result:=tick(actor,runner,Vector3(0.15,0,0) if i>=120 else Vector3.ZERO,float(i)/120)
		if i%5:continue
		var transform: Dictionary=actor.sample_transform(0);var pos: Vector3=actor.root.position;transform.position=[pos.x,pos.y,pos.z]
		keys.append(Capture.key({"pose":result.pose,"transform":transform},i/5))
	runner.dispose();actor.live_pose=null
	var previous: Dictionary=actor.data.duplicate(true);var id: String=actor.data.id
	var take:=Capture.replace_range(previous,keys,0,48,48)
	check(not take.has("error") and keys.size()==49,"secondary output uses the ordinary editable FK take format: "+label)
	if take.has("error"):return
	var error: String=app.renderer.world_runtime.restore_instances({id:take.data})
	check(error.is_empty(),"secondary take binds to the existing standard model: "+label)
	app.push_history({"type":"world_objects","before":{id:previous},"after":{id:take.data.duplicate(true)}});app.changed()
	app.undo();check(actor.data==previous,"Undo restores all pre-experiment motion: "+label);app.redo()
	app.renderer.camera.position=Vector3(1,1.5,3);app.renderer.camera.look_at(Vector3(0,1,0))
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(100,100,Color.RED)
	var pixels: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data();var shots: Array=app.keys.duplicate(true)
	app.set_frame(24);var saved_pose: Dictionary=actor.sample(24)
	var project:=folder.path_join(label+"-secondary.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	actor=app.renderer.world_runtime.instance(id)
	var def: Dictionary=actor.root.get_meta("has_secondary_rig")
	check(FileAccess.file_exists(project) and JSON.stringify(actor.sample(24))==JSON.stringify(saved_pose) and actor.data.metadata==previous.metadata and def.error.is_empty() and not def.chains.is_empty(),"packed reopen retains native rig/provenance and baked motion without live springs: "+label)
	app.set_frame(24);app.set_frame(0);app.set_frame(47);app.set_frame(24)
	check(JSON.stringify(actor.sample(24))==JSON.stringify(saved_pose) and JSON.stringify(app.keys)==JSON.stringify(JSON.parse_string(JSON.stringify(shots,"",true,true))) and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_data()==pixels,"arbitrary seek preserves recorded motion, explicit camera and independent paint: "+label)
	var image: Image=await app.renderer.capture(app.keys,app.layers,24,true);image.save_png(folder.path_join(label+"-reopened.png"))
	if label=="authored":
		error=await app.export_movie(folder)
		check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==image.get_data(),"baked spring output exports with exact reopened preview pixels")
		movies.append(app.last_export_folder.path_join("movie.mp4"))
func sample(app,path: String,label: String,expected_chains: int,expected_colliders: int) -> void:
	app.new_project();var data:=Model.definition(path)
	var report:=path.get_base_dir().path_join("parameters.json")
	if FileAccess.file_exists(report):data.metadata.native_parameters=JSON.parse_string(FileAccess.get_file_as_string(report))
	app.append_object(data,"model");var actor: RefCounted=app.renderer.active_model()
	await process_frame;await RenderingServer.frame_post_draw
	var def: Dictionary=actor.root.get_meta("has_secondary_rig");print("RIG ",label," ",def.get("error")," ",def.chains.size())
	check(def.error.is_empty() and def.chains.size()==expected_chains and def.colliders.size()==expected_colliders,"source springs and colliders adapt without silent truncation: "+label)
	if not def.error.is_empty():return
	var before: Dictionary=actor.data.duplicate(true);var sha:=FileAccess.get_sha256(path);var original_order: Array=actor.order.duplicate()
	var created: Dictionary=await Runner.create(actor);check(not created.has("error"),"unit-world spring runner accepts the declared rig: "+label)
	if created.has("error"):print(created);return
	var runner: RefCounted=created.runner;var neutral: Dictionary={};var blown: Dictionary={};var final: Dictionary={};var last: Dictionary={};var jerk:=0.0
	for i in range(600):
		var wind:=Vector3(0.15,0,0) if i>=120 and i<360 else Vector3.ZERO
		var result:=tick(actor,runner,wind,float(i)/120 if label!="authored" else 0)
		if result.has("error"):check(false,"spring runner produces every step: "+str(result));runner.dispose();return
		var pose: Dictionary=result.pose
		if not Model.pose_valid(pose):check(false,"spring pose finite and valid: "+label);runner.dispose();return
		if not last.is_empty():jerk=maxf(jerk,pose_distance(pose,last))
		last=pose
		if i==119:neutral=pose
		if i==359:
			blown=pose;actor.live_pose=pose;actor.apply(0)
			app.renderer.camera.position=Vector3(1,1.5,3);app.renderer.camera.look_at(Vector3(0,1,0))
			await process_frame;await RenderingServer.frame_post_draw
			app.renderer.viewport.get_texture().get_image().save_png(folder.path_join(label+"-wind.png"))
		if i==599:final=pose
	var sway:=pose_distance(neutral,blown);var recovery:=pose_distance(final,neutral)
	metrics[label]={"wind_angle":sway,"recovery_angle":recovery,"maximum_step_angle":jerk,"chains":def.chains.size(),"colliders":def.colliders.size(),"rotating_bones":blown.size()}
	check(sway>0.01,"standing character's declared loose parts respond to wind: "+label)
	if label=="authored":check(pose_distance(neutral,{})<0.00001,"no-wind authored strip preserves its intended rest pose")
	check(jerk<0.35,"fixed-step response avoids single-step angular jumps above20degrees: "+label)
	if label=="authored":check(recovery<sway*0.1,"authored hair/skirt settle after the wind stops")
	check(actor.data==before and actor.order==original_order and FileAccess.get_sha256(path)==sha,"secondary experiment preserves native geometry, bone IDs and all authored data: "+label)
	check(runner.step(0,Vector3.ZERO).has("error") and runner.step(1,Vector3.ZERO).has("error") and runner.step(NAN,Vector3.ZERO).has("error") and runner.step(1.0/120,Vector3(INF,0,0)).has("error"),"invalid solver steps reject safely: "+label)
	runner.dispose();actor.live_pose=null;actor.apply(0)
	# Repeat the same fixed ticks with different render yields: authoritative
	# spring stepping must not advance itself with the UI/render wall clock.
	created=await Runner.create(actor);runner=created.runner;var repeated: Dictionary={}
	for i in range(360):
		repeated=tick(actor,runner,Vector3(0.15,0,0) if i>=120 else Vector3.ZERO,float(i)/120 if label!="authored" else 0).pose
		if i%90==0:await process_frame
	var difference:=pose_difference(blown,repeated)
	check(difference<0.00001,"same fixed steps reproduce spring poses across different render pacing: "+label)
	metrics[label].repeat_quaternion_difference=difference
	runner.dispose();actor.live_pose=null;actor.apply(0)
	created=await Runner.create(actor);runner=created.runner;var control: Dictionary={}
	for i in range(360):control=tick(actor,runner,Vector3.ZERO,float(i)/120 if label!="authored" else 0).pose
	var wind_only:=pose_difference(blown,control);metrics[label].wind_control_difference=wind_only
	check(wind_only>0.005,"matching moving-anchor no-wind control proves airflow causes the change: "+label)
	runner.dispose();actor.live_pose=null;actor.apply(0)
	await baked(app,actor,label)
func corruption(path: String) -> void:
	var raw:=FileAccess.get_file_as_bytes(path);var size:=raw.decode_u32(12);var json: Dictionary=JSON.parse_string(raw.slice(20,20+size).get_string_from_utf8())
	var doc:=GLTFDocument.new();var state:=GLTFState.new();doc.append_from_buffer(raw,"",state);var scene:=doc.generate_scene(state)
	for kind in ["fractional","missing","duplicate","radius","center","shape","vector"]:
		var data:=json.duplicate(true);var native: Dictionary=data.extensions.VRMC_springBone
		match kind:
			"fractional":native.springs[0].joints[0].node=1.5
			"missing":native.springs[0].joints[0].node=999999
			"duplicate":native.springs.append(native.springs[0].duplicate(true))
			"radius":native.colliders[0].shape.sphere.radius=-1
			"center":native.springs[0].center=native.springs[1].joints[0].node
			"shape":native.colliders[0].shape={"plane":{}}
			"vector":native.springs[0].joints[0].gravityDir="bad"
		var result:=Definition.from_gltf(data,state,scene)
		check(not result.error.is_empty() and result.chains.is_empty() and result.colliders.is_empty(),"malformed secondary data disables the complete rig with an explicit reason: "+kind)
	scene.free()
	# Resolve live non-bone centers/colliders by exact source IDs, even when
	# distinct source nodes share the same display name. Stress repeated disposal.
	var tagged:=json.duplicate(true);var scene_root: int=tagged.scenes[int(tagged.get("scene",0))].nodes[0]
	tagged.extensions.VRMC_springBone.springs[0].center=scene_root
	var first_node: int=tagged.nodes.size()
	for x in [2,-2]:tagged.nodes.append({"name":"Duplicate anchor","translation":[x,0,0]})
	if not tagged.nodes[scene_root].has("children"):tagged.nodes[scene_root].children=[]
	tagged.nodes[scene_root].children.append_array([first_node,first_node+1])
	tagged.extensions.VRMC_springBone.colliders[0].node=first_node
	tagged.extensions.VRMC_springBone.colliders[1].node=first_node+1
	var tagged_path:=folder.path_join("live-node-identities.glb");Fixture.write_glb(tagged_path,tagged,raw.slice(28+size))
	var live_ok:=true
	for repeat in range(20):
		var loaded:=SceneIO.load_glb(tagged_path);var descriptor: Dictionary=loaded.scene.get_meta("has_secondary_rig")
		live_ok=live_ok and descriptor.error.is_empty()
		if descriptor.error.is_empty():
			var c: Dictionary=descriptor.chains[0].center;var ca: Dictionary=descriptor.colliders[0].binding;var cb: Dictionary=descriptor.colliders[1].binding
			live_ok=live_ok and c.kind=="node" and c.source_node==scene_root and ca.path!=cb.path and loaded.scene.get_node(ca.path).position.x==2 and loaded.scene.get_node(cb.path).position.x==-2
		loaded.scene.free()
	check(live_ok,"repeated imports bind live non-bone centers and duplicate-name colliders by exact source identity")
	var duplicate:=json.duplicate(true);var joints: Array=duplicate.extensions.VRMC_springBone.springs[0].joints
	duplicate.nodes[int(joints[0].node)].name="Same.髪";duplicate.nodes[int(joints[1].node)].name="Same.髪"
	var duplicate_path:=folder.path_join("duplicate-names.glb");Fixture.write_glb(duplicate_path,duplicate,raw.slice(28+size))
	var decoded:=SceneIO.load_glb(duplicate_path);var rig:=Model.new();rig.root=decoded.scene;rig.data=Model.definition(duplicate_path);rig.inventory(rig.root)
	var definition: Dictionary=rig.root.get_meta("has_secondary_rig");var a: String=definition.chains[0].joints[0].binding.id;var b: String=definition.chains[0].joints[1].binding.id
	check(definition.error.is_empty() and a!=b and rig.bones.has(a) and rig.bones.has(b) and rig.parent_id(b)==a,"duplicate Japanese/dotted source names bind to distinct correct engine-generated bones")
	rig.root.free()
	var legacy:=json.duplicate(true);var first: int=json.extensions.VRMC_springBone.springs[0].joints[0].node;var body: int=json.extensions.VRMC_springBone.colliders[0].node
	legacy.extensions={"VRM":{"secondaryAnimation":{"boneGroups":[{"bones":[first],"center":body,"stiffiness":0.8,"colliderGroups":[0]}],"colliderGroups":[{"node":body,"colliders":[{"offset":{"x":0.1,"y":0.2,"z":0.3},"radius":0.1}]}]}}}
	doc=GLTFDocument.new();state=GLTFState.new();doc.append_from_buffer(raw,"",state);scene=doc.generate_scene(state)
	var adapted:=Definition.from_gltf(legacy,state,scene)
	check(adapted.error.is_empty() and adapted.chains.size()==1 and adapted.chains[0].end_extension==0.07 and adapted.colliders[0].offset==[0.1,0.2,-0.3],"legacy root traversal, seven-centimeter virtual tail and collider Z conversion are explicit")
	legacy.extensions.VRM.secondaryAnimation.boneGroups[0].bones=[body]
	adapted=Definition.from_gltf(legacy,state,scene)
	check(not adapted.error.is_empty() and adapted.chains.is_empty(),"branched legacy chains refuse with a review reason instead of dropping branches")
	scene.free()
func contact_control(app,path: String) -> void:
	app.new_project();app.append_object(Model.definition(path),"model");var actor: RefCounted=app.renderer.active_model()
	await process_frame;await RenderingServer.frame_post_draw
	var poses: Array=[]
	for enabled in [true,false]:
		actor.apply(0);var created: Dictionary=await Runner.create(actor);var runner: RefCounted=created.runner
		if not enabled:
			for chain in runner.chains:chain.spring.set_enable_all_child_collisions(0,false);chain.spring.clear_collisions(0)
		var pose: Dictionary={}
		for i in range(360):pose=tick(actor,runner,Vector3(-0.6,0,0),0).pose
		poses.append(pose);runner.dispose()
	check(pose_difference(poses[0],poses[1])>0.005,"declared spring colliders change actual obstructed hair motion versus disabled collision control")
func scale_controls(app,path: String) -> void:
	app.new_project();var data:=Model.definition(path);data.scale=2;app.append_object(data,"model");var actor: RefCounted=app.renderer.active_model()
	await process_frame;await RenderingServer.frame_post_draw
	var def: Dictionary=actor.root.get_meta("has_secondary_rig").duplicate(true)
	# Legal VRM1 ancestor link with an unlisted intermediate bone.
	def.chains[0].joints.remove_at(1);actor.root.set_meta("has_secondary_rig",def)
	var created: Dictionary=await Runner.create(actor)
	check(not created.has("error"),"scaled model with a skipped source intermediate uses unit-world scratch chains")
	if created.has("error"):return
	var runner: RefCounted=created.runner;var pose: Dictionary={};var solved: Array[Transform3D]=[]
	for i in range(120):
		if i==119:
			var sk: Skeleton3D=runner.chains[0].scratch
			runner.chains[0].spring.modification_processed.connect(func():solved.append(sk.get_bone_global_pose(2)),CONNECT_ONE_SHOT)
		pose=tick(actor,runner,Vector3(0.15,0,0),0).pose
	actor.live_pose=pose;actor.apply(0)
	var target: String=def.chains[0].joints[1].binding.id;var actual: Transform3D=actor.bone_transform(target)
	check(solved.size()==1 and actual.origin.distance_to(solved[0].origin)<0.0001 and absf(actual.basis.get_rotation_quaternion().dot(solved[0].basis.get_rotation_quaternion()))>0.99999,"FK reconstruction preserves skipped intermediate geometry under scale")
	check(runner.chains[0].scratch.global_basis.get_scale().is_equal_approx(Vector3.ONE) and is_equal_approx(runner.chains[0].colliders[0].node.radius,0.16),"scratch bones stay unit scale while collider sizes follow actual model units")
	runner.dispose();check(runner.step(1.0/120,Vector3.ZERO).has("error"),"disposed secondary runner rejects further stepping")
	actor.live_pose=null;actor.apply(0);actor.root.scale=Vector3(1,2,1)
	created=await Runner.create(actor);check(created.has("error"),"nonuniform secondary rigs reject before running malformed physics")
	actor.apply(0);def=actor.root.get_meta("has_secondary_rig").duplicate(true)
	def.colliders[1].binding=def.chains[0].joints[0].binding.duplicate(true);actor.root.set_meta("has_secondary_rig",def)
	var info: Dictionary=actor.bones[def.colliders[1].binding.id];info.skeleton.set_bone_pose_scale(info.index,Vector3(1,2,1))
	created=await Runner.create(actor);check(created.has("error"),"late invalid collider cleans already allocated temporary shapes")
func run() -> void:
	folder=ProjectSettings.globalize_path("res://output/secondary-motion/run_"+str(Time.get_ticks_usec()));DirAccess.make_dir_recursive_absolute(folder)
	var path:=folder.path_join("hair-skirt.glb");check(Fixture.create(path)==OK,"original skinned hair and skirt fixture created")
	var app=load("res://src/app.gd").new();root.add_child(app);await process_frame
	await sample(app,path,"authored",2,2);corruption(path)
	await contact_control(app,path)
	await scale_controls(app,path)
	for item in OS.get_cmdline_user_args():
		if item.ends_with("scene.glb"):await sample(app,item,"vrm0" if "vrm0" in item else "vrm1",12,22)
	app.free()
	var result:={"checks":checks,"failures":failures,"folder":folder,"metrics":metrics,"movies":movies}
	var file:=FileAccess.open("res://output/secondary-motion-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("SECONDARY_MOTION "+JSON.stringify(result));quit(0 if failures==0 else 1)

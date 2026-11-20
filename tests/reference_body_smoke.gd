extends SceneTree
# Actual editor/renderer lifecycle; mechanics are independently checked by the
# reference_body_physics_unit oracle. This test never opens an original art asset.
const Fixture=preload("res://tests/reference_body_workflow_fixture.gd")
const Model=preload("res://src/model.gd")
const Height=preload("res://src/character_height.gd")
const PhysicsRig=preload("res://src/physics_rig.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var folder: String
var checks:=0
var failures:=0
var labels: Array[String]=[]
var normalized: Dictionary={}
var projects: Array=[]
var metrics: Dictionary={}
var movie:=""

func _initialize() -> void:
	create_timer(240).timeout.connect(func():push_error("Reference body workflow watchdog expired");quit(2))
	call_deferred("run")

func check(value: bool,label: String) -> void:
	checks+=1;labels.append(label);print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()

func wait_hair(id: String) -> void:
	while app.physics_editor.pending.has(id):await process_frame
	await settled()

func actor():return app.renderer.active_model()

func canonical(value) -> String:return JSON.stringify(value,"",true,true)

func exact_keys(a: Dictionary,b: Dictionary) -> bool:
	var aa:=a.keys();var bb:=b.keys();aa.sort();bb.sort();return aa==bb

func native_pose_bytes(pose: Dictionary) -> PackedByteArray:
	var ids:=pose.keys();ids.sort();var values:=PackedFloat32Array()
	for id in ids:
		values.append_array(PackedFloat32Array(pose[id].position));values.append_array(PackedFloat32Array(pose[id].rotation_xyzw))
	return values.to_byte_array()

func native_root_bytes(value: Dictionary) -> PackedByteArray:
	var values:=PackedFloat32Array(value.position);values.append_array(PackedFloat32Array(value.rotation_xyzw));return values.to_byte_array()

func source_state(rig) -> Dictionary:
	var bases:={};var rests:={}
	for id in rig.order:
		bases[id]=rig.bones[id].base;rests[id]=rig.bones[id].skeleton.get_bone_rest(rig.bones[id].index)
	return {"basis":rig.data.asset_basis.duplicate(true),"lineage":rig.data.metadata.get("import_basis_lineage",{}).duplicate(true),"source":rig.data.source,"sha256":rig.data.sha256,"raw":rig.raw_import_root,"base_root":rig.base_root,"order":rig.order.duplicate(),"bases":bases,"rests":rests}

func source_same(rig,state: Dictionary) -> bool:return source_state(rig)==state and FileAccess.get_sha256(rig.data.source)==state.sha256

func root_scale(rig) -> float:return float(rig.sample_transform(app.frame,true).scale)

func capture_error(simulation) -> Dictionary:
	var rig=simulation.rig;var pose: Dictionary=simulation.capture_pose();var globals:={};var position:=0.;var basis:=0.
	for id in rig.order:
		var delta: Dictionary=pose.get(id,Model.identity());var base: Transform3D=rig.bones[id].base
		var local:=Transform3D(Basis(base.basis.get_rotation_quaternion()*Timeline.quaternion(delta.rotation_xyzw)).scaled(base.basis.get_scale()),base.origin+Timeline.vector(delta.position))
		var parent: String=rig.parent_id(id);globals[id]=globals[parent]*local if globals.has(parent) else local
	for id in simulation.bodies:
		var expected: Transform3D=simulation.bodies[id].global_transform*simulation.bodies[id].body_offset.affine_inverse()
		var actual: Transform3D=rig.bones[id].skeleton.global_transform*globals[id]
		position=maxf(position,actual.origin.distance_to(expected.origin))
		for axis in range(3):basis=maxf(basis,actual.basis[axis].distance_to(expected.basis[axis]))
	return {"position":position,"basis":basis,"valid":Model.pose_valid(pose)}

func geometry_error(simulation,raw_bounds: Dictionary,worlds: Dictionary) -> Dictionary:
	var sk: Skeleton3D=simulation.skeleton;var frame:=Transform3D(sk.global_basis.orthonormalized(),sk.global_position).affine_inverse()
	var minimum:=Vector3(INF,INF,INF);var maximum:=-minimum
	for id in simulation.bodies:
		var point: Vector3=frame*worlds[id].origin;minimum=minimum.min(point);maximum=maximum.max(point)
	var span:=maxf((maximum-minimum).length(),.01);var size_error:=0.;var center_error:=0.;var unit_error:=0.;var boxes:=true
	for id in simulation.bodies:
		var body: PhysicalBone3D=simulation.bodies[id];var shape=body.get_child(0).shape;var world: Transform3D=worlds[id]
		boxes=boxes and shape is BoxShape3D and raw_bounds.has(id)
		if not shape is BoxShape3D or not raw_bounds.has(id):continue
		var expected: Vector3=raw_bounds[id].size*world.basis.get_scale().x+Vector3.ONE*span*.003
		size_error=maxf(size_error,shape.size.distance_to(expected))
		center_error=maxf(center_error,body.global_position.distance_to(world*raw_bounds[id].get_center()))
		unit_error=maxf(unit_error,body.global_basis.get_scale().distance_to(Vector3.ONE))
	return {"boxes":boxes,"size":size_error,"center":center_error,"unit":unit_error,"span":span}

func collision_floor(simulation) -> float:
	var result:=INF
	for body in simulation.bodies.values():
		var collision: CollisionShape3D=body.get_child(0);var shape=collision.shape;var t:=collision.global_transform
		if shape is BoxShape3D:
			for x in [-.5,.5]:
				for y in [-.5,.5]:
					for z in [-.5,.5]:result=minf(result,(t*(shape.size*Vector3(x,y,z))).y)
		elif shape is SphereShape3D:result=minf(result,t.origin.y-shape.radius)
		elif shape is CapsuleShape3D:
			var half: float=shape.height*.5-shape.radius;result=minf(result,minf((t*Vector3(0,half,0)).y,(t*Vector3(0,-half,0)).y)-shape.radius)
	return result

func bounds_error(a: AABB,b: AABB) -> float:return maxf(a.position.distance_to(b.position),a.end.distance_to(b.end))

func grab_case(simulation,state: Dictionary,before: Dictionary,history: int,scale: float) -> Dictionary:
	var rig=simulation.rig;var physics=app.physics_editor;var id: String=rig.data.id
	var target: PhysicalBone3D=simulation.bodies.values()[0]
	var center:=Vector3.ZERO
	for body in simulation.bodies.values():center+=body.global_position
	center/=simulation.bodies.size()
	app.renderer.camera.position=center+Vector3(2.,1.3,3.)*scale;app.renderer.camera.look_at(center)
	var point: Vector2=app.renderer.camera.unproject_position(target.global_position)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true
	app.canvas_input(press,point)
	var started: bool=physics.grabbing() and physics.grabbed in simulation.bodies.values() and app.world_selection.selected==id
	check(started,"scale "+str(scale)+": actual viewport left-click grabs the original reference body's collider")
	var lift:=0.;var velocity:=Vector3.ZERO;var retained:=false
	if started:
		var held: PhysicalBone3D=physics.grabbed;var origin: Vector3=held.global_position
		var motion:=InputEventMouseMotion.new();app.canvas_input(motion,point+Vector2(0,-220))
		for i in range(120):await physics_frame
		lift=held.global_position.y-origin.y
		app.canvas_input(motion,point+Vector2(120,-260))
		for i in range(12):await physics_frame
		velocity=held.linear_velocity
		var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-30,-30)
		app._input(release)
		retained=held.linear_velocity.is_equal_approx(velocity)
	check(started and lift>.15*scale,"scale "+str(scale)+": viewport dragging lifts the articulated reference against gravity")
	check(started and not physics.grabbing() and physics.active(id) and retained and velocity.length()>.1 and rig.data==before and app.history.size()==history and source_same(rig,state),"scale "+str(scale)+": outside release retains throwing velocity without authoring or replacing the source")
	return {"started":started,"lift":lift,"release_speed":velocity.length(),"velocity_retained":retained}

func setup_scene(scale: float,peer:=false) -> String:
	app.new_project();app.load_demo_room();app.mode.select(1);app.change_mode(1)
	var data:=normalized.duplicate(true);data.id="reference-body-main";data.scale=scale;data.position=[0,3.5,0];app.append_object(data,"model")
	var id: String=app.last_import_id
	if peer:
		data=normalized.duplicate(true);data.id="reference-body-peer";data.scale=.5;data.position=[2,3.5,0];app.append_object(data,"model");app.world_selection.select_entity(id)
	app.renderer.camera.position=Vector3(5,3,8);app.renderer.camera.look_at(Vector3(0,1.5,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)]
	return id

func save_case(name: String,id: String,frame: int) -> void:
	app.set_frame(frame);app.world_selection.select_entity(id);var rig=actor();var query:=Bounds.query(rig.root)
	var expected:={"name":name,"id":id,"frame":frame,"scale":root_scale(rig),"basis":rig.data.asset_basis.duplicate(true),"pose":rig.sample(frame,true),"transform":rig.sample_transform(frame,true),"minimum":[query.bounds.position.x,query.bounds.position.y,query.bounds.position.z],"maximum":[query.bounds.end.x,query.bounds.end.y,query.bounds.end.z]}
	# Preserve the writer's exact decimal strings. Parsing numeric JSON solely
	# for the oracle can itself move a double by one ULP before comparison.
	expected["pose_canonical"]=canonical(expected.pose);expected["transform_canonical"]=canonical(expected.transform)
	expected["definition"]=rig.data.duplicate(true)
	var path:=folder.path_join(name+".has");app.has_project.save_file(path,"packed");await wait_job()
	check(FileAccess.file_exists(path) and app.has_project.pid<0 and not app.physics_editor.is_running(),name+": packed save leaves no live solver")
	projects.append(expected)

func factor_case(scale: float) -> void:
	var id:=setup_scene(scale);await settled();var rig=actor();var physics=app.physics_editor
	var state:=source_state(rig);var before: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();var worlds:={}
	for bone in rig.order:worlds[bone]=rig.bone_transform(bone)
	var sk: Skeleton3D=rig.bones[rig.order[0]].skeleton
	var raw:=PhysicsRig.weighted_bounds(rig,sk,rig.order)
	physics.change(true)
	check(physics.body_active(id) and physics.collider_triangles>0,"scale "+str(scale)+": Simple body toggle starts against real map colliders")
	if not physics.body_active(id):return
	var simulation=physics.simulations[id];var geometry:=geometry_error(simulation,raw,worlds)
	check(geometry.boxes and geometry.size<.0001 and geometry.center<.0001 and geometry.unit<.0001,"scale "+str(scale)+": actual boxes match source skin in world metres with unit body frames")
	var capture:=capture_error(simulation)
	check(capture.valid and capture.position<.0002 and capture.basis<.0002,"scale "+str(scale)+": tick-zero body capture reconstructs source FK including scale")
	for i in range(480):await physics_frame
	await settled()
	var low:=collision_floor(simulation);var speed:=0.;var high:=-INF
	for body in simulation.bodies.values():speed=maxf(speed,body.linear_velocity.length());high=maxf(high,body.global_position.y)
	capture=capture_error(simulation)
	check(is_finite(low) and low>-.025 and high<3. and speed<2.,"scale "+str(scale)+": real contacts keep settled finite collision surfaces above the floor")
	check(capture.valid and capture.position<.001 and capture.basis<.001,"scale "+str(scale)+": moving-body capture remains canonical and preserves local scale")
	check(rig.data==before and app.history.size()==history and source_same(rig,state),"scale "+str(scale)+": live body motion leaves source, intrinsic basis and authored data unchanged")
	var grab: Dictionary=await grab_case(simulation,state,before,history,scale)
	var live_bounds:=Bounds.query(rig.root);var expected_pose: Dictionary=simulation.pose();physics.change(false)
	var frozen: Dictionary=rig.data.duplicate(true);var frozen_bounds:=Bounds.query(rig.root)
	check(not physics.is_running() and rig.data.pose==expected_pose and app.history.size()==history+1 and rig.data.pose_keys.is_empty(),"scale "+str(scale)+": Freeze is one Undo with no simulation keys")
	check(live_bounds.error.is_empty() and frozen_bounds.error.is_empty() and bounds_error(live_bounds.bounds,frozen_bounds.bounds)<.0002,"scale "+str(scale)+": frozen source FK and live final skin bounds agree")
	check(is_equal_approx(root_scale(rig),scale) and source_same(rig,state) and not sk.has_meta(Bounds.FINAL_META),"scale "+str(scale)+": Freeze keeps relative scale and clears owned bounds metadata")
	app.undo();check(rig.data==before and not physics.is_running(),"scale "+str(scale)+": Undo restores the exact authored reference with solver off")
	app.redo();check(rig.data==frozen and source_same(rig,state),"scale "+str(scale)+": Redo restores canonical frozen data and intrinsic identity")
	metrics[str(scale)]={"geometry":geometry,"capture":capture,"collision_floor":low,"speed":speed,"highest_body":high,"grab":grab}
	await settled();root.get_texture().get_image().save_png(folder.path_join("scale-"+str(scale)+"-editor.png"))
	await save_case("frozen-"+str(scale),id,0)

func hair_cases() -> void:
	for first in [true,false]:
		var label:="hair-first" if first else "body-first";var id:=setup_scene(1.);await settled();var rig=actor();var physics=app.physics_editor
		var state:=source_state(rig);var authored: Dictionary=rig.data.duplicate(true)
		if first:physics.change_hair(true);await wait_hair(id)
		physics.change(true)
		if not first:physics.change_hair(true);await wait_hair(id)
		check(physics.active(id) and physics.simulations[id] is Secondary and physics.simulations[id].primary!=null,label+": generic hair and reference body share the original actor")
		if not physics.active(id) or not physics.simulations[id] is Secondary or physics.simulations[id].primary==null:return
		var wrapper=physics.simulations[id];var primary=wrapper.primary;var ids: Array=wrapper.runner.chains[0].ids.duplicate();var disjoint:=true
		for bone in ids:disjoint=disjoint and not primary.bodies.has(bone)
		for i in range(90):await physics_frame
		check(disjoint and wrapper.running and primary.running and source_same(rig,state) and rig.data==authored,label+": both solvers keep disjoint canonical joints without authoring")
		physics.change_hair(false);await settled();var restored:=true
		for bone in ids:
			var info: Dictionary=rig.bones[bone];var local: Transform3D=info.skeleton.get_bone_pose(info.index);restored=restored and local.is_equal_approx(info.base)
		check(physics.simulations.get(id)==primary and primary.running and is_instance_valid(primary.simulator) and restored,label+": Hair Off restores authored local hair and keeps the same body alive")
		physics.change_hair(true);await wait_hair(id);physics.change(false);await settled()
		check(not physics.is_running() and not rig.bones[rig.order[0]].skeleton.has_meta(Bounds.FINAL_META) and source_same(rig,state),label+": Body Off disposes combined simulation and owned metadata")
	# Cancel during the actual awaited generic spring setup, preserving its borrowed body.
	var id:=setup_scene(1.);await settled();var physics=app.physics_editor;physics.change(true);var primary=physics.simulations.get(id)
	physics.change_hair(true);var pending: bool=physics.pending.has(id);physics.change_hair(false);await settled();await settled()
	check(pending and physics.simulations.get(id)==primary and primary.running and physics.pending.is_empty(),"pending hair cancellation preserves its borrowed reference body")
	physics.clear();check(not physics.is_running() and not is_instance_valid(primary.simulator),"clear disposes the retained body without late secondary installation")

func recording_cases() -> void:
	var id:=setup_scene(1.,true);await settled();var physics=app.physics_editor;var record=physics.recording
	app.video.fps_num=25;app.video.fps_den=2;app.video.duration_frames=12
	var before: Dictionary=app.renderer.world_state();var peer: Dictionary=app.renderer.world_runtime.instance("reference-body-peer").data.duplicate(true);var history: int=app.history.size()
	for target in ["reference-body-peer",id]:app.world_selection.select_entity(target);physics.change(true)
	app.world_selection.select_entity(id);record.scope.select(0)
	check(record.start() and record.targets.keys()==[id],"rational Local Record locks capture to the reference actor")
	while record.active:await process_frame
	var rig=app.renderer.world_runtime.instance(id)
	check(record.last_error.is_empty() and record.ticks==116 and record.last_frame==12 and rig.authored_keys().size()==13,"rational Local capture stores all13 boundaries with integer fixed-tick phase")
	check(app.renderer.world_runtime.instance("reference-body-peer").data==peer and app.history.size()==history+1 and not physics.is_running(),"Local capture leaves its peer authored state intact and commits one Undo")
	check(is_equal_approx(rig.sample_transform(6).scale,1.) and rig.data.asset_basis==normalized.asset_basis,"Local take stores artist scale rather than the intrinsic factor")
	app.undo();check(app.renderer.world_state()==before,"Local Undo restores the complete pre-take world")
	# World captures both normalized characters, at different actual body sizes.
	app.set_frame(0)
	for target in ["reference-body-peer",id]:app.world_selection.select_entity(target);physics.change(true)
	record.scope.select(1);history=app.history.size()
	check(record.start() and record.targets.size()==2,"World Record includes both independently sized reference bodies")
	while record.active:await process_frame
	var complete: bool=record.last_error.is_empty() and record.ticks==116 and app.history.size()==history+1 and not physics.is_running()
	for target in [id,"reference-body-peer"]:complete=complete and app.renderer.world_runtime.instance(target).authored_keys().size()==13
	check(complete,"World capture commits both canonical takes atomically and disposes solvers")
	var samples:={}
	for target in [id,"reference-body-peer"]:samples[target]={"pose":app.renderer.world_runtime.instance(target).sample(6),"root":app.renderer.world_runtime.instance(target).sample_transform(6)}
	app.set_frame(0);app.set_frame(11);app.set_frame(6);var repeated:=true
	for target in samples:
		var current=app.renderer.world_runtime.instance(target);repeated=repeated and canonical(current.sample(6))==canonical(samples[target].pose) and canonical(current.sample_transform(6))==canonical(samples[target].root)
	check(repeated and not physics.is_running(),"arbitrary seek replays stored body motion without restarting physics")
	Drawing.insert(app.layers[1],0,12,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(80,80,Color.CYAN)
	await save_case("reference-body-recorded",id,6)
	var preview: Image=await app.renderer.capture(app.keys,app.layers,6,true);preview.save_png(folder.path_join("recorded-preview.png"))
	var error: String=await app.export_movie(folder);var rendered:=Image.load_from_file(app.last_export_folder.path_join("frame_000007.png"))
	check(error.is_empty() and rendered!=null and rendered.get_data()==preview.get_data(),"1080p rational MP4 input frame equals the saved canonical preview and independent paint")
	movie=app.last_export_folder.path_join("movie.mp4")
	# A real Escape discards only this unfinished take.
	id=setup_scene(.5);await settled();physics=app.physics_editor;record=physics.recording;before=app.renderer.world_state();history=app.history.size();physics.change(true);record.scope.select(0)
	check(record.start(),"reference body can begin a new cancellable Local take")
	while record.active and record.last_frame<3:await process_frame
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	check(not record.active and not physics.is_running() and app.renderer.world_state()==before and app.history.size()==history,"Escape cancels reference capture without changing authored data or history")

func reader() -> void:
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	for item in expected.projects:
		app.has_project.open_file(folder.path_join(item.name+".has"));await wait_job();app.world_selection.select_entity(item.id);app.set_frame(int(item.frame));await settled()
		var rig=actor();var label: String=item.name
		check(rig!=null and not app.physics_editor.is_running() and app.physics_editor.import_starts.is_empty(),label+": independent cold reader restores without live activation")
		if not rig:continue
		check(canonical(rig.data.asset_basis)==canonical(item.basis) and is_equal_approx(root_scale(rig),float(item.scale)),label+": cold reader retains intrinsic basis and artist scale")
		var actual_pose: Dictionary=rig.sample(item.frame,true);var actual_transform: Dictionary=rig.sample_transform(item.frame,true)
		var pose_equal: bool=exact_keys(actual_pose,item.pose) and native_pose_bytes(actual_pose)==native_pose_bytes(item.pose)
		for id in actual_pose:pose_equal=pose_equal and item.pose.has(id) and exact_keys(actual_pose[id],item.pose.get(id,{}))
		var root_equal: bool=exact_keys(actual_transform,item.transform) and native_root_bytes(actual_transform)==native_root_bytes(item.transform) and actual_transform.scale==item.transform.scale
		FileAccess.open(folder.path_join(label+"-cold-sample-diagnostic.json"),FileAccess.WRITE).store_string(canonical({"expected_pose":item.pose,"actual_pose":actual_pose,"expected_transform":item.transform,"actual_transform":actual_transform,"expected_pose_canonical":canonical(item.pose),"writer_pose_canonical":item.pose_canonical,"actual_pose_canonical":canonical(actual_pose),"expected_transform_canonical":canonical(item.transform),"writer_transform_canonical":item.transform_canonical,"actual_transform_canonical":canonical(actual_transform),"writer_pose_string_exact":canonical(actual_pose)==item.pose_canonical,"writer_root_string_exact":canonical(actual_transform)==item.transform_canonical,"native_pose_bytes_exact":pose_equal,"native_root_bytes_and_scale_exact":root_equal}))
		check(pose_equal and root_equal,label+": cold reader retains exact canonical IDs, native float32 pose/root bits and root scale")
		var query:=Bounds.query(rig.root);var bounds:=AABB(Timeline.vector(item.minimum),Timeline.vector(item.maximum)-Timeline.vector(item.minimum))
		check(query.error.is_empty() and bounds_error(query.bounds,bounds)<.0002 and not rig.bones[rig.order[0]].skeleton.has_meta(Bounds.FINAL_META),label+": cold FK source bounds agree without stale solver metadata")
		check(Height.queries==0 and not app.height_review.pending,label+": cold reader never remeasures or offers import review")
		if label=="reference-body-recorded":
			var image: Image=await app.renderer.capture(app.keys,app.layers,int(item.frame),true);var preview:=Image.load_from_file(folder.path_join("recorded-preview.png"))
			check(image.get_data()==preview.get_data() and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,"cold recorded preview and independent drawing match writer pixels exactly")

func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("display.cfg");root.add_child(app);await settled()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if args.size()>1:await reader();finish(true);return
	var source:=folder.path_join("public-reference-body.glb");check(Fixture.create(source)==OK,"original public humanoid and separate spring fixture exports")
	app.import_actions.offer_height=true;var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	var error: String=app.pose_editor.add_model(source,0,context)
	while app.height_review.pending and not app.height_review.prepared:await process_frame
	check(error.is_empty() and app.height_review.pending and not app.height_review.reference.disabled,"actual import review offers the six-foot reference for the public complete figure")
	if not app.height_review.pending or app.height_review.reference.disabled:finish(false);return
	app.height_review.reference.button_pressed=true;app.height_review.apply();await settled()
	check(actor()!=null and actor().data.has("asset_basis") and is_equal_approx(actor().data.scale,1.) and absf(Height.query(actor()).height-Height.SIX_FEET)<.00002,"actual reference import applies six feet once with artist Scale1")
	if not actor():finish(false);return
	normalized=actor().data.duplicate(true)
	check(actor().root.get_meta("has_secondary_rig",{}).get("chains",[]).size()==1,"public GLB retains its separately declared generic hair strand")
	for scale in [.5,1.,2.]:await factor_case(scale)
	await hair_cases();await recording_cases()
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(canonical({"projects":projects}))
	check(FileAccess.get_sha256(source)==normalized.sha256,"all body, hair, recording and packaging operations preserve original source bytes")
	finish(false)

func finish(cold: bool) -> void:
	var result:={"checks":checks,"failures":failures,"labels":labels,"metrics":metrics,"projects":projects.size(),"movie":movie}
	FileAccess.open(folder.path_join("result-reader.json" if cold else "result.json"),FileAccess.WRITE).store_string(canonical(result))
	print("REFERENCE_BODY_WORKFLOW "+canonical(result));app.free();quit(0 if failures==0 else 1)

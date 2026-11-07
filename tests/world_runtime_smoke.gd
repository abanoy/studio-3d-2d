extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Renderer = preload("res://src/renderer.gd")
const World = preload("res://src/world_document.gd")
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Storage = preload("res://src/storage.gd")
const Timeline = preload("res://src/timeline.gd")
const Encoder = preload("res://src/encoder.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(75).timeout.connect(func():push_error("World runtime watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func pose_key(frame: int, position: Array, angle: float, bone: String) -> Dictionary:
	var q:=Quaternion(Vector3.BACK,deg_to_rad(angle))
	return {"frame":frame,"interpolation":"ease","transform":{"position":position,"rotation_xyzw":[0,0,0,1],"scale":1},"pose":{bone:{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}}}

func changed(a: Image,b: Image) -> int:
	var aa:=a.get_data();var bb:=b.get_data();var count:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:count+=1
	return count

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/world-runtime/run_%d" % Time.get_ticks_usec())
	var inputs:=folder.path_join("inputs");DirAccess.make_dir_recursive_absolute(inputs)
	var map:=inputs.path_join("map.glb");var rig:=inputs.path_join("rig.glb");var group:=inputs.path_join("group.glb")
	var authored:=Node3D.new();authored.name="OriginalSmallSet"
	SceneIO.box(authored,"Floor",Vector3(0,-0.1,-0.8),Vector3(4,0.2,4),Color("49576c"))
	SceneIO.box(authored,"Backdrop",Vector3(0,1,-2.7),Vector3(4,2,0.2),Color("506882"))
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(authored,state)
	if error==OK:error=doc.write_to_filesystem(state,map)
	authored.free()
	check(error==OK and SceneIO.make_pose_fixture(rig)==OK and SceneIO.make_empty(group)==OK,"authored two-set world assets")
	var originals:={map:FileAccess.get_sha256(map),rig:FileAccess.get_sha256(rig),group:FileAccess.get_sha256(group)}
	var read:=SceneIO.load_glb(rig);var prototype:=Model.new();prototype.root=read.scene;prototype.inventory(prototype.root)
	var bone:=""
	for id in prototype.order:
		if prototype.bones[id].name=="arm":bone=id
	prototype.root.free()
	var world:=World.empty()
	var parent:=World.object(group,"group","Both sets");parent.id="sets"
	# Child-before-parent serialization deliberately exercises graph preparation.
	for i in range(2):
		var actor:=World.object(rig,"model","Actor %d" % i);actor.id="actor-%d" % i;actor.parent_id="map-%d" % i;actor.start_frame=24 if i==1 else 0
		actor.pose_keys=[pose_key(0,[0,0,0],0,bone),pose_key(24,[0.4,0,0],-65 if i==0 else 45,bone)]
		var set_map:=World.object(map,"environment","Map %d" % i);set_map.id="map-%d" % i;set_map.parent_id="sets";set_map.position=[-3 if i==0 else 3,0,0]
		world.objects.append(actor);world.objects.append(set_map)
	world.objects.append(parent)
	var renderer:=Renderer.new();root.add_child(renderer);renderer.setup();renderer.set_background("black")
	check(renderer.import_scene(map).is_empty(),"legacy environment remains usable before world installation")
	var old_scene: Node3D=renderer.environment_scene
	var bad:=world.duplicate(true);bad.objects[2].pose_keys[0].pose={"absent bone":Model.identity()}
	var rejected:=renderer.prepare_world(bad,48)
	check(rejected.has("error") and renderer.environment_scene==old_scene and old_scene.is_inside_tree(),"one invalid rig leaves the complete installed legacy scene intact")
	var notifications:=[0];renderer.assets_changed.connect(func():notifications[0]+=1)
	var prepared:=renderer.prepare_world(world,48)
	check(not prepared.has("error") and renderer.install_world(prepared),"atomic install of two maps, two actors and group")
	if not renderer.world_runtime:quit(1);return
	var runtime: RefCounted=renderer.world_runtime
	check(not renderer.environment_scene and not renderer.model and notifications[0]==1,"world replaces legacy slots with one assets notification")
	check(not renderer.install_world(prepared) and renderer.world_runtime==runtime,"already attached prepared world cannot be installed twice")
	check(runtime.instances.size()==5 and runtime.instance("actor-0").root.get_parent()==runtime.instance("map-0").root and runtime.instance("map-0").root.get_parent()==runtime.instance("sets").root,"all stable IDs and parent links exist in the actual 3D tree")
	check(runtime.instance("actor-0").bones.size()==2 and runtime.instance("actor-1").bones.size()==2 and runtime.instance("map-0").bones.is_empty(),"bone inventories exclude independently parented child rigs")
	check(runtime.instance("actor-0").root!=runtime.instance("actor-1").root and runtime.instance("actor-0").data!=runtime.instance("actor-1").data,"shared asset creates independent live rig and pose instances")
	renderer.camera.position=Vector3(0,3.2,10);renderer.camera.look_at(Vector3(0,0.9,0),Vector3.UP)
	var keys:=[Timeline.key(0,renderer.camera.position,renderer.camera.quaternion,60),Timeline.key(48,Vector3(0.5,2.8,9.5),renderer.camera.quaternion,60)]
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48,"world_background":"black"}
	renderer.evaluate(keys,23)
	check(not runtime.instance("actor-1").root.is_visible_in_tree() and runtime.instance("actor-0").root.is_visible_in_tree(),"second actor is absent immediately before first presence")
	var first:=await renderer.capture(keys,[],0,true)
	var both:=await renderer.capture(keys,[],24,true)
	both.save_png(folder.path_join("combined-world.png"))
	check(runtime.instance("actor-1").root.is_visible_in_tree() and first.get_data()!=both.get_data(),"presence, root movement, two independent arm poses and camera sample on same frame")
	var left: RefCounted=runtime.instance("actor-0");var right: RefCounted=runtime.instance("actor-1")
	check(left.root.global_position.distance_to(Vector3(-2.6,0,0))<0.001 and right.root.global_position.distance_to(Vector3(3.4,0,0))<0.001,"map-local actor transforms evaluate through both map roots")
	var arm_before: Transform3D=left.bone_transform(bone)
	parent=runtime.instance("sets").data;parent.position=[0,1,0];runtime.evaluate(24)
	check(left.bone_transform(bone).origin.distance_to(arm_before.origin+Vector3.UP)<0.001,"group translation moves child model and skinned bone together")
	parent.position=[0,0,0];runtime.evaluate(24)
	var turn:=Quaternion(Vector3.UP,PI/2)
	parent.rotation_xyzw=[turn.x,turn.y,turn.z,turn.w];parent.scale=1.5;runtime.evaluate(24)
	check(left.root.global_position.distance_to((Basis(turn)*Vector3(-2.6,0,0))*1.5)<0.001 and right.root.global_position.distance_to((Basis(turn)*Vector3(3.4,0,0))*1.5)<0.001,"parent rotation and scale transform both complete sets without merging their rigs")
	parent.rotation_xyzw=[0,0,0,1];parent.scale=1;runtime.evaluate(24)
	var untouched: Dictionary=left.data.duplicate(true);var peer_before: Transform3D=left.bone_transform(bone)
	right.data.pose_keys[1].pose[bone].rotation_xyzw=[0,0,0,1];runtime.evaluate(24)
	check(left.data==untouched and left.bone_transform(bone).is_equal_approx(peer_before),"editing one instance never changes the other instance sharing its GLB")
	right.data.pose_keys[1].pose=world.objects[2].pose_keys[1].pose.duplicate(true)
	for id in ["actor-0","actor-1","map-0","map-1"]:
		var baseline:=both
		if id.begins_with("map-"):
			left.data.visible=false;right.data.visible=false
			baseline=await renderer.capture(keys,[],24,true)
		var instance: RefCounted=runtime.instance(id);instance.data.visible=false
		var hidden:=await renderer.capture(keys,[],24,true)
		check(changed(baseline,hidden)>500,"each loaded map/actor contributes actual visible pixels: "+id)
		instance.data.visible=true
		left.data.visible=true;right.data.visible=true
	runtime.instance("map-1").data.visible=false;runtime.evaluate(24)
	check(not right.root.is_visible_in_tree() and left.root.is_visible_in_tree(),"hidden parent suppresses its actor without changing sibling or child visibility data")
	runtime.instance("map-1").data.visible=true
	right.data.reference_only=true
	var preview:=await renderer.capture(keys,[],24,false)
	var final:=await renderer.capture(keys,[],24,true)
	check(changed(preview,final)>500 and right.root.is_visible_in_tree(),"reference-only instance excluded from final but restored for editing after capture")
	right.data.reference_only=false
	var image:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);image.fill(Color.TRANSPARENT)
	image.fill_rect(Rect2i(80,80,100,40),Color.RED)
	var layers:=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"cel","start":0,"duration":48,"image":image}]}]
	var composite:=await renderer.capture(keys,layers,24,true)
	check(composite.get_pixel(100,100).r>0.99 and FileAccess.get_sha256(rig)==originals[rig],"independent RGBA drawing overlays combined world without editing source geometry")
	var snapshot:=folder.path_join("snapshot")
	var save_error:=Storage.save_project(snapshot,video,keys,layers,"",24,{}, {},{},true,renderer.world_state())
	var loaded:=Storage.load_project(snapshot)
	check(save_error.is_empty() and not loaded.has("error"),"all runtime instances save through schema4 storage")
	var replacement:=renderer.prepare_world(loaded.world,48)
	check(not replacement.has("error") and renderer.install_world(replacement,24),"saved world reopens atomically with all instances")
	var reopened:=await renderer.capture(loaded.camera_keys,loaded.layers,24,true)
	var aa:=composite.get_data();var bb:=reopened.get_data();var error_sum:=0.0
	for i in range(aa.size()):error_sum+=absf(float(aa[i])-float(bb[i]))
	var rebuild_changes:=changed(composite,reopened);var rebuild_mean:=error_sum/aa.size()
	check(rebuild_changes<=384 and rebuild_mean<0.002,"combined preview survives full GLB rebuild within existing GPU edge tolerance")
	reopened.save_png(folder.path_join("package-reference.png"))
	var live: RefCounted=renderer.world_runtime;var previous_state:=renderer.world_state()
	bad=loaded.world.duplicate(true);bad.objects[-1].parent_id="missing"
	check(renderer.prepare_world(bad,48).has("error") and renderer.world_runtime==live and renderer.world_state()==previous_state,"bad parent graph preserves all live instances and their edits")
	var changed_source: Dictionary=loaded.world.duplicate(true);changed_source.objects[-1].sha256="0".repeat(64)
	check(renderer.prepare_world(changed_source,48).has("error") and renderer.world_runtime==live,"changed world asset rejects before replacing current world")
	check(not renderer.import_scene(map).is_empty() and not renderer.install_model({"model":null}) and renderer.world_runtime==live,"legacy single-slot calls cannot partially overwrite an installed world")
	var movie_folder:=folder.path_join("render");DirAccess.make_dir_recursive_absolute(movie_folder)
	for frame in range(48):
		var rendered:=await renderer.capture(keys,layers,frame,true)
		if rendered.save_png(movie_folder.path_join("frame_%06d.png" % (frame+1)))!=OK:check(false,"write combined-world PNG");break
	var encoder:=Encoder.new();var encode_error: String=await encoder.encode(self,OS.get_environment("HYBRID_FFMPEG") if OS.has_environment("HYBRID_FFMPEG") else ("C:/Program Files/ffmpeg/bin/ffmpeg.exe" if OS.get_name()=="Windows" else "ffmpeg"),movie_folder,video)
	check(encode_error.is_empty() and Image.load_from_file(movie_folder.path_join("frame_000025.png")).get_data()==reopened.get_data(),"actual camera/two-map/two-actor/drawing MP4 uses same frame24 evaluation")
	var native:=[];var native_world:=World.empty()
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private runtime fixture absent: "+sample);continue
		var original:=Storage.load_project(path)
		var row: Dictionary=World.from_project(original).objects[-1];row=Support.legacy_model(row);row.id="native-%d" % native.size();row.parent_id="";row.pose_keys=[]
		originals[row.source]=row.sha256
		row.position=[native.size()*3-3,0,0];native_world.objects.append(row);native.append(sample)
	if native.size()==3:
		prepared=renderer.prepare_world(native_world,48)
		check(not prepared.has("error") and renderer.install_world(prepared),"MMD, GMod and SFM actual rigs coexist in same runtime")
		var active: RefCounted=renderer.world_runtime
		for id in active.order:
			var instance: RefCounted=active.instance(id);var bounds:=renderer.scene_bounds(instance.root)
			instance.data.scale*=2.0/maxf(0.001,bounds.size.y);instance.data.position=[int(id.trim_prefix("native-"))*3-3,0,0]
		active.evaluate(0)
		var combined:=await renderer.capture(keys,[],0,true);combined.save_png(folder.path_join("native-combined.png"))
		for id in active.order:
			var instance: RefCounted=active.instance(id);instance.data.visible=false
			var hidden:=await renderer.capture(keys,[],0,true)
			check(instance.order.size()>50 and changed(combined,hidden)>500,"native rig visible independently in combined world: "+id)
			instance.data.visible=true
			var before_pose: Dictionary=instance.data.pose.duplicate(true)
			var arm:="";var index:=int(id.trim_prefix("native-"))
			for candidate in instance.order:
				if str(instance.bones[candidate].name).ends_with(["左腕","L_UpperArm","bip_upperArm_L"][index]):arm=candidate
			var peer_states:={}
			for peer in active.order:
				if peer!=id:peer_states[peer]=active.instance(peer).data.duplicate(true)
			instance.data.pose[arm]=Model.identity()
			var rotated:=Quaternion(Vector3.BACK,0.7);instance.data.pose[arm].rotation_xyzw=[rotated.x,rotated.y,rotated.z,rotated.w]
			var deformed:=await renderer.capture(keys,[],0,true)
			var independent:=true
			for peer in peer_states:
				if active.instance(peer).data!=peer_states[peer]:independent=false
			check(not arm.is_empty() and changed(combined,deformed)>100 and independent,"native bone deforms independently beside other ecosystems: "+id)
			instance.data.pose=before_pose
	var empty:=renderer.prepare_world(World.empty(),48)
	check(renderer.install_world(empty) and renderer.world_runtime.instances.is_empty() and renderer.empty_environment,"atomic empty-world replacement releases previous hierarchy")
	for path in originals:check(FileAccess.get_sha256(path)==originals[path],"original asset unchanged: "+path.get_file())
	var report:={"checks":checks,"failures":failures,"folder":folder,"snapshot":snapshot,"movie":movie_folder.path_join("movie.mp4"),"native_projects":native,"originals":originals,"rebuild_changed_channels":rebuild_changes,"rebuild_mean_error":rebuild_mean}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/world-runtime-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("WORLD_RUNTIME_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)

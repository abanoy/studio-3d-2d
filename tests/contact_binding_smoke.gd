extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Contacts=preload("res://src/foot_contacts.gd")
const Hold=preload("res://src/foot_hold.gd")
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Contact binding watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func json_file(path: String) -> Dictionary:return JSON.parse_string(FileAccess.get_file_as_string(path))
func run() -> void:
	var args:=OS.get_cmdline_user_args();var input: String=args[0];folder=args[1];DirAccess.make_dir_recursive_absolute(folder);var expected:=json_file(input.path_join("expected.json"));var writer:=json_file(input.path_join("writer-result.json"))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(writer.packed);await job()
	var metrics:={};var exact:=true;var unchanged:=true
	for id in expected.ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id);var before: Dictionary=actor.data.duplicate(true);var legs: Array=actor.contact_legs();var builds: int=actor.contact_binding_builds
		var began:=Time.get_ticks_usec()
		for i in range(200):actor.contact_legs()
		var cached_ms:=float(Time.get_ticks_usec()-began)/1000.;began=Time.get_ticks_usec()
		for i in range(200):Hold.chains(actor)
		var uncached_ms:=float(Time.get_ticks_usec()-began)/1000.
		check(actor.contact_binding_builds==builds and actor.contact_legs()==Hold.chains(actor),"warm compiled chain bindings match exact uncached resolution without rebuilding: "+id)
		for half in range(97):exact=exact and JSON.stringify(actor.sample(float(half)/2),"",true,true).sha256_text()==expected.samples[id][half]
		began=Time.get_ticks_usec()
		for at in range(49):actor.sample(at)
		var sample_ms:=float(Time.get_ticks_usec()-began)/1000.
		var track:=Contacts.track([Contacts.active(actor.data.animation_clips,12)]);var invalid:=track.duplicate(true);invalid.segments[0].feet[0].ids[2]=legs[0].ids[0]
		check(not Contacts.check_bindings(actor,invalid).is_empty() and actor.contact_binding_builds==builds,"compiled bindings still reject a foreign/shared requested chain: "+id)
		var order: Array[String]=actor.order.duplicate();actor.order.erase(legs[0].ids[2]);var rejected_order: bool=not Contacts.check_bindings(actor,track).is_empty();actor.order.assign(order)
		check(rejected_order and Contacts.check_bindings(actor,track).is_empty(),"order changes invalidate bindings and a restored order recompiles correctly: "+id)
		var meta: Dictionary=actor.data.metadata.duplicate(true);var params: Dictionary=meta.get("native_parameters",{}).duplicate(true);var humanoid: Dictionary=params.get("humanoid",{}).duplicate(true);humanoid["leftFoot"]={"node_name":"missing-foot-for-cache-test"};params["humanoid"]=humanoid;actor.data.metadata["native_parameters"]=params
		var rejected_meta: bool=not Contacts.check_bindings(actor,track).is_empty();actor.data.metadata=meta
		check(rejected_meta and Contacts.check_bindings(actor,track).is_empty(),"in-place humanoid metadata changes cannot reuse a stale binding: "+id)
		var middle: Dictionary=actor.bones[legs[0].ids[1]];var parent: int=middle.skeleton.get_bone_parent(middle.index);middle.skeleton.set_bone_parent(middle.index,-1)
		var rejected_parent: bool=not Contacts.check_bindings(actor,track).is_empty();middle.skeleton.set_bone_parent(middle.index,parent)
		check(rejected_parent and Contacts.check_bindings(actor,track).is_empty(),"live hierarchy changes invalidate bindings and restore without sticky failure: "+id)
		unchanged=unchanged and actor.data==before and actor.order==order
		metrics[id]={"bones":actor.order.size(),"cached_binding_200_ms":cached_ms,"uncached_binding_200_ms":uncached_ms,"sample_49_ms":sample_ms,"binding_builds":actor.contact_binding_builds}
	check(exact and unchanged,"compiled bindings retain all485 pre-optimization native poses and restore authored state exactly")
	# A bounded dense world: five native instances, each with exactly32 source blocks.
	var dense_values:={};var dense_expected:={};app.video.duration_frames=240;app.renderer.world_runtime.duration=240
	for id in expected.ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id);var data: Dictionary=actor.data.duplicate(true)
		for at in range(1,49):
			if data.animation_clips.size()>=32:break
			var index:=Model.Clips.index_at(data,at)
			if index>=0 and data.animation_clips[index].start!=at:data=Model.Clips.split(data,at).data
		var tail: Dictionary=data.animation_clips[-1];tail.length=241-int(tail.start)
		if tail.has("foot_contacts") and not tail.foot_contacts.segments.is_empty():tail.foot_contacts.segments[-1].to=int(tail.source_in)+int(tail.length)
		check(data.animation_clips.size()==32 and Model.validate(data,240).is_empty(),"dense native32-piece document validates at240frames: "+id);dense_values[id]=data
	check(app.renderer.world_runtime.restore_instances(dense_values).is_empty(),"real runtime installs the complete bounded dense world")
	var bytes: int=app.pose_editor.contacts.metadata_bytes(app.current_world());check(bytes<=1024*1024,"the dense five-native world stays within the complete project metadata budget")
	var dense_ms:={};var dense_errors:=0
	for id in expected.ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id);dense_expected[id]={};var began:=Time.get_ticks_usec()
		for at in range(241):actor.sample(at);dense_errors+=0 if actor.evaluation_error.is_empty() else 1
		dense_ms[id]=float(Time.get_ticks_usec()-began)/1000.
		for at in [0,12,48,120,240]:dense_expected[id][str(at)]=JSON.stringify(actor.sample(at),"",true,true).sha256_text()
	check(dense_errors==0,"all1205 samples of the dense contact world are reachable")
	app.set_frame(120);var path:=folder.path_join("dense-native.has");app.has_project.save_file(path,"packed");await job();check(FileAccess.file_exists(path),"dense five-native32-block world saves through the ordinary HAS worker")
	app.new_project();app.has_project.open_file(path);await job();var reopened:=true
	for id in dense_expected:
		var actor: RefCounted=app.renderer.world_runtime.instance(id)
		for at in dense_expected[id]:reopened=reopened and JSON.stringify(actor.sample(float(at)),"",true,true).sha256_text()==dense_expected[id][at]
	check(reopened and int(app.video.duration_frames)==240,"dense native world reopens with exact resolved sample poses")
	var result:={"checks":checks,"failures":failures,"folder":folder,"reference_folder":input,"reference_expected_sha256":FileAccess.get_sha256(input.path_join("expected.json")),"metrics":metrics,"dense_241_ms":dense_ms,"dense_metadata_bytes":bytes,"dense_project":path};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close();app.free();await settled();print("CONTACT_BINDINGS "+JSON.stringify(result));quit(0 if failures==0 else 1)

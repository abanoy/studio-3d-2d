extends SceneTree
const World = preload("res://src/world_document.gd")
const Model = preload("res://src/model.gd")
const Storage = preload("res://src/storage.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Audio = preload("res://src/audio_track.gd")
const Timeline = preload("res://src/timeline.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(45).timeout.connect(func():push_error("World document watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/world-document/run_%d" % Time.get_ticks_usec())
	var inputs:=folder.path_join("inputs");DirAccess.make_dir_recursive_absolute(inputs)
	var room:=inputs.path_join("map.glb");var rig:=inputs.path_join("actor.glb");var group:=inputs.path_join("group.glb")
	check(SceneIO.make_fixture(room)==OK and SceneIO.make_pose_fixture(rig)==OK and SceneIO.make_empty(group)==OK,"authored real map, rig and empty group assets")
	var originals:={}
	var arm_id:=""
	for path in [room,rig,group]:
		originals[path]=FileAccess.get_sha256(path)
		var decoded:=SceneIO.load_glb(path)
		check(not decoded.has("error"),"standard asset actually decodes: "+path.get_file())
		if decoded.has("scene"):
			if path==rig:
				var prototype:=Model.new();prototype.root=decoded.scene;prototype.inventory(prototype.root)
				for id in prototype.order:
					if prototype.bones[id].name=="arm":arm_id=id
			decoded.scene.free()
	check(not arm_id.is_empty(),"pose fixture uses actual imported bone identity rather than a guessed path")
	var world:=World.empty()
	var grouping:=World.object(group,"group","Set group");grouping.id="set"
	world.objects.append(grouping)
	for i in range(2):
		var map:=World.object(room,"environment","Map %d" % i);map.id="map-%d" % i;map.parent_id="set";map.position=[i*20,0,0]
		var actor:=World.object(rig,"model","Actor %d" % i);actor.id="actor-%d" % i;actor.parent_id=map.id;actor.start_frame=i*24
		actor.metadata={"unrecognized_native_field":{"retain":i},"source_family":"data fixture"}
		actor.pose={arm_id:{"position":[0,0,0],"rotation_xyzw":[0,0,0,1]}}
		actor.pose_keys=[{"frame":0,"pose":actor.pose.duplicate(true),"transform":{"position":[i,0,0],"rotation_xyzw":[0,0,0,1],"scale":1},"interpolation":"ease"}]
		world.objects.append(map);world.objects.append(actor)
	check(World.validate(world,48).is_empty(),"five independent map/model/group records share one model contract")
	var portable:=World.portable(world)
	check(World.validate(portable,48,true).is_empty() and not portable.objects[0].has("source"),"portable world uses only canonical managed asset references")
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48,"world_background":"black"}
	var keys:=[Timeline.key(0,Vector3(6,5,8),Quaternion.IDENTITY,60)]
	var image:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);image.set_pixel(100,100,Color.RED)
	var layers:=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"cel","start":0,"duration":48,"image":image}]}]
	var audio:={}
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	if FileAccess.file_exists(wav):
		var data:=Audio.read_wav(wav)
		if not data.has("error"):audio=Audio.make_clip(data);audio.start_frame=24
	var snapshot:=folder.path_join("snapshot")
	var error:=Storage.save_project(snapshot,video,keys,layers,"",24,audio,{}, {},true,world)
	check(error.is_empty(),"schema4 saves complete multi-object snapshot with editable cel/audio")
	var manifest_path:=snapshot.path_join("project.json")
	var wire: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	check(wire.schema_version==4 and wire.world.objects.size()==5 and not wire.has("scene") and not wire.has("model"),"schema4 has one canonical object list and no ambiguous old slots")
	var glbs:=0
	for file in DirAccess.get_files_at(snapshot.path_join("assets")):
		if file.get_extension()=="glb":glbs+=1
	check(glbs==3,"shared geometry is stored once for five instances")
	var loaded:=Storage.load_project(snapshot)
	check(not loaded.has("error") and World.portable(loaded.world)==JSON.parse_string(JSON.stringify(portable,"",true,true)),"world IDs, hierarchy, root transforms and pose keys round-trip losslessly")
	check(loaded.world.objects[4].start_frame==24 and loaded.world.objects[4].metadata==JSON.parse_string(JSON.stringify(world.objects[4].metadata,"",true,true)),"first presence and unknown native metadata remain independent per object")
	check(loaded.layers[0].cels[0].image.get_data()==image.get_data() and loaded.editor.frame==24,"independent drawing and saved master frame remain intact")
	check(loaded.audio.is_empty()==audio.is_empty() and (audio.is_empty() or loaded.audio.start_frame==24),"audio remains on same master timeline in schema4")
	check(World.from_project(loaded)==loaded.world and World.from_legacy(loaded).has("error"),"project normalizer preserves existing multi-object data instead of treating it as an empty legacy scene")
	var complete_hash:=FileAccess.get_sha256(manifest_path)
	for kind in ["duplicate","cycle","missing","fractional","scale"]:
		var bad:=world.duplicate(true)
		if kind=="duplicate":bad.objects[1].id=bad.objects[0].id
		if kind=="cycle":bad.objects[0].parent_id="actor-0"
		if kind=="missing":bad.objects[0].parent_id="missing"
		if kind=="fractional":bad.objects[4].start_frame=1.5
		if kind=="scale":bad.objects[4].scale=0
		var failed:=Storage.save_project(snapshot,video,keys,layers,"",0,audio,{}, {},true,bad)
		check(not failed.is_empty() and FileAccess.get_sha256(manifest_path)==complete_hash,"invalid world rejected before replacing valid snapshot: "+kind)
	var owned_asset: String=snapshot.path_join(portable.objects[1].path)
	var original_bytes:=FileAccess.get_file_as_bytes(owned_asset)
	var file:=FileAccess.open(owned_asset,FileAccess.WRITE);file.store_string("changed");file.close()
	check(Storage.load_project(snapshot).has("error"),"changed shared managed asset is rejected for all instances")
	file=FileAccess.open(owned_asset,FileAccess.WRITE);file.store_buffer(original_bytes);file.close()
	var manifest_bytes:=FileAccess.get_file_as_bytes(manifest_path)
	var unsafe:=wire.duplicate(true);unsafe.world.objects[1].path="../outside.glb"
	file=FileAccess.open(manifest_path,FileAccess.WRITE);file.store_string(JSON.stringify(unsafe));file.close()
	check(Storage.load_project(snapshot).has("error"),"unsafe world asset path rejects before file lookup")
	file=FileAccess.open(manifest_path,FileAccess.WRITE);file.store_buffer(manifest_bytes);file.close()
	Storage.save_project(snapshot,video,keys,layers,"",24,audio,{}, {},true,world)
	var backup_path:=snapshot.path_join("project.backup.json")
	var good_backup:=FileAccess.get_sha256(backup_path)
	var corrupt_graph:=wire.duplicate(true);corrupt_graph.world.objects[0].parent_id="missing"
	file=FileAccess.open(manifest_path,FileAccess.WRITE);file.store_string(JSON.stringify(corrupt_graph));file.close()
	var repaired:=Storage.save_project(snapshot,video,keys,layers,"",24,audio,{}, {},true,world)
	check(repaired.is_empty() and FileAccess.get_sha256(backup_path)==good_backup,"corrupt current world graph never replaces prior good manifest backup")
	var empty_folder:=folder.path_join("empty")
	check(Storage.save_project(empty_folder,video,keys,[],"",0,{}, {},{},true,World.empty()).is_empty(),"empty schema4 writer has no fabricated asset requirement")
	check(not Storage.load_project(empty_folder).has("error"),"schema4 also reads a genuinely empty 3D-only project")
	var empty_layers:=[{"id":"ink","name":"Ink","visible":true,"cels":[]}]
	var empty_layered:=folder.path_join("empty-layered")
	Storage.save_project(empty_layered,video,keys,empty_layers,"",0,{}, {},{},true,World.empty())
	check(not Storage.load_project(empty_layered).has("error"),"empty schema4 project reads with zero objects and optional drawing layer")
	var legacy:=folder.path_join("legacy")
	var old_model:=Model.definition(rig)
	Storage.save_project(legacy,video,keys,layers,room,24,{}, {},old_model)
	var old_wire: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(legacy.path_join("project.json")))
	for schema in [1,2,3]:
		var old:=old_wire.duplicate(true);old.schema_version=schema
		if schema<3:old.model={}
		file=FileAccess.open(legacy.path_join("project.json"),FileAccess.WRITE);file.store_string(JSON.stringify(old));file.close()
		var read:=Storage.load_project(legacy)
		check(not read.has("error") and World.validate(World.from_project(read),48).is_empty(),"schema%d remains readable and normalizes into world data" % schema)
	var unusual:=Storage.load_project(legacy)
	unusual.model.id="old/path"
	var normalized:=World.from_legacy(unusual)
	check(World.validate(normalized,48).is_empty() and normalized.objects[1].metadata.legacy_instance_id=="old/path" and unusual.model.id=="old/path","legacy unusual IDs normalize without losing their original value or mutating source data")
	unusual.model.id="legacy-scene-"+unusual.scene.sha256
	check(World.validate(World.from_legacy(unusual),48).is_empty(),"legacy scene/model ID collision normalizes to distinct instances")
	var native_world:=World.empty();var native:=[]
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private world fixture absent: "+sample);continue
		var read:=Storage.load_project(path)
		if read.has("error"):check(false,"native fixture readable: "+sample);continue
		var migrated:=World.from_project(read)
		for i in range(migrated.objects.size()):
			migrated.objects[i].id="native-%d-%d" % [native.size(),i]
			native_world.objects.append(migrated.objects[i])
		native.append(sample)
	var native_snapshot:=folder.path_join("native-snapshot")
	if not native.is_empty():
		error=Storage.save_project(native_snapshot,video,keys,empty_layers,"",0,{}, {},{},true,native_world)
		var read:=Storage.load_project(native_snapshot)
		check(error.is_empty() and not read.has("error") and World.portable(read.world)==JSON.parse_string(JSON.stringify(World.portable(native_world),"",true,true)),"actual MMD/GMod/SFM native poses/metadata coexist in one persisted world")
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await process_frame
	check(app.open_project(snapshot) and app.renderer.world_runtime.instances.size()==5 and app.world_selection.selected.is_empty(),"normal Open installs every schema4 object with no default selection")
	for path in originals:check(FileAccess.get_sha256(path)==originals[path],"world persistence preserves authored source bytes: "+str(path).get_file())
	var references:={}
	for row in world.objects:references[World.asset_path(row.sha256)]=row.source
	if not audio.is_empty():references["assets/"+audio.source.sha256+".wav"]=audio.source.path
	var report:={"checks":checks,"failures":failures,"folder":folder,"snapshot":snapshot,"empty_snapshot":empty_folder,"native_snapshot":native_snapshot if not native.is_empty() else "","native_projects":native,"references":references,"originals":originals}
	file=FileAccess.open(ProjectSettings.globalize_path("res://output/world-document-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("WORLD_DOCUMENT_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)

extends SceneTree
# Storage-only synthetic assets; never instantiate or render an imported model.
const ImportBasis=preload("res://src/import_basis.gd")
const Boundary=preload("res://src/import_basis_project.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Extended=preload("res://src/extended_timing.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
class TrapGuard:
	extends "res://src/project_payload_guard.gd"
	var visits:=0
	func asset(_folder: String,_row,_path_key: String="path",_hash_key: String="sha256",_limit: int=128*1024*1024) -> bool:
		visits+=1
		return false
func check(ok: bool,label: String) -> void:
	checks+=1
	print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func manifest(folder: String) -> Dictionary:
	var data=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("project.json")))
	return data if data is Dictionary else {}
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(folder)
	var source:=folder.path_join("synthetic.glb")
	var file:=FileAccess.open(source,FileAccess.WRITE)
	file.store_string("Synthetic storage-only asset, not a native model.");file.close()
	var row:=World.object(source,"model","Six-foot storage fixture")
	row.id="human"
	row["asset_basis"]=ImportBasis.create_record(row.sha256,"2").record
	var world:=World.empty();world.objects=[row]
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var keys: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)]
	var layers: Array=[]
	var target:=folder.path_join("active")
	var why:=Storage.save_project(target,video,keys,layers,"",0,{},{},{},true,world)
	check(why.is_empty(),"active size basis saves: "+why)
	if not why.is_empty():quit(1);return
	var saved:=manifest(target)
	check(saved.get("schema_version")==9 and saved.get("basis_content_schema_version")==4,"outer schema9 protects legacy world4")
	check(Storage.readable_manifest(target.path_join("project.json")) and Storage.readable_payloads(target,target.path_join("project.json")),"current reader and payload guard admit supported basis")
	var loaded:=Storage.load_project(target)
	check(not loaded.has("error"),"active scene reopens: "+str(loaded.get("error","")))
	if not loaded.has("error"):
		check(loaded.schema_version==9 and loaded.world.objects[0].asset_basis==saved.world.objects[0].asset_basis,"loaded result retains original scene-local capability and facts")
		check(not ImportBasis.inspect_capability(loaded).has("error"),"loaded runtime metadata remains capability-inspectable")
		check(Boundary.decoded_content_schema(loaded)==4 and World.from_project(loaded)==loaded.world,"schema9 world normalizer retains all model and basis data")
		check(World.from_legacy(loaded).has("error"),"legacy normalizer cannot silently drop a wrapped world")
		check(World.from_legacy({"schema_version":9.0}).has("error"),"JSON-decoded numeric9 cannot bypass legacy normalizer guard")
	var legacy_scene:={"schema_version":3,"model":row.duplicate(true),"scene":{},"source":source,"video":video,"layers":layers,"camera_keys":keys,"audio":{}}
	var legacy_wrapped: Dictionary=ImportBasis.encode_capability(legacy_scene).document
	var normalized_legacy:=World.from_project(legacy_wrapped)
	check(Boundary.decoded_content_schema(legacy_wrapped)==3 and not normalized_legacy.has("error") and normalized_legacy.objects[-1].asset_basis==row.asset_basis,"schema9 legacy-model content uses legacy route and retains basis")
	for invalid_version in [0,10,3.5,true,"4",null]:
		var malformed:=saved.duplicate(true);malformed.basis_content_schema_version=invalid_version
		check(Boundary.decoded_content_schema(malformed)==-1 and World.from_project(malformed).has("error"),"invalid wrapped content version refuses "+str(invalid_version))
	var before:=FileAccess.get_file_as_bytes(target.path_join("project.json"))
	var invalid:=world.duplicate(true);invalid.objects[0].asset_basis.factor="1"
	why=Storage.save_project(target,video,keys,layers,"",0,{},{},{},true,invalid)
	check(not why.is_empty() and FileAccess.get_file_as_bytes(target.path_join("project.json"))==before,"invalid size record cannot replace previous save")
	var absent_target:=folder.path_join("must-not-create")
	why=Storage.save_project(absent_target,video,keys,layers,"",0,{},{},{},true,invalid)
	check(not why.is_empty() and not DirAccess.dir_exists_absolute(absent_target),"invalid basis rejected before creating assets or project folder")
	for field in ["basis_content_schema_version","import_basis_capability"]:
		var bad:=saved.duplicate(true);bad.erase(field)
		var trap:=TrapGuard.new()
		check(not trap.valid(target,bad) and trap.visits==0,"missing "+field+" refuses before payload reads")
		check(Storage.decode_project(bad,"missing-folder").has("error"),"missing capability refuses project decode")
	var info:=World.object(source,"model","Legacy informational height")
	info.metadata["import_height"]={"factor":"0.1","target_metres":"1.8288"}
	var info_world:=World.empty();info_world.objects=[info]
	var old_target:=folder.path_join("legacy")
	why=Storage.save_project(old_target,video,keys,layers,"",0,{},{},{},true,info_world)
	check(why.is_empty() and manifest(old_target).get("schema_version")==4,"old informational import_height remains legacy identity")
	for version in [1,2]:
		var old:={"schema_version":version,"model":{},"scene":{}}
		check(not Boundary.validation_view(old).has("error"),"historical schema"+str(version)+" without basis retains legacy route")
		var decoded_old: Dictionary=JSON.parse_string(JSON.stringify(old))
		check(not Boundary.validation_view(decoded_old).has("error") and Boundary.decoded_content_schema(decoded_old)==version,"JSON numeric legacy schema retains its actual reader route")
		old.model={"asset_basis":row.asset_basis}
		check(Boundary.validation_view(old).has("error"),"historical schema cannot carry active basis")
	var child:={"schema_version":4,"video":video.duplicate(),"camera_keys":keys.duplicate(true),"layers":[],"world":world.duplicate(true),"audio":{}}
	var graph:={"format":Graph.FORMAT,"clips":[],"assets":[{"id":"child","name":"Active child","scene":child,"clips":[]}]}
	var nested:=folder.path_join("nested")
	why=Storage.save_project(nested,video,keys,layers,"",0,{},{},{},true,World.empty(),{},[],graph)
	check(why.is_empty(),"active child saves with independent capability: "+why)
	if why.is_empty():
		var data:=manifest(nested)
		check(data.schema_version==9 and data.sequence_graph.assets[0].scene.schema_version==9,"parent and child each declare capability")
		check(not Storage.load_project(nested).has("error"),"nested active scene reopens")
		var child_data: Dictionary=data.sequence_graph.assets[0].scene
		child_data.schema_version=child_data.basis_content_schema_version;child_data.erase("basis_content_schema_version");child_data.erase("import_basis_capability")
		check(Storage.decode_project(data,nested).has("error"),"parent permission cannot rescue downgraded active child")
	var long_video:=video.duplicate();long_video.duration_frames=480
	var reference_path:=folder.path_join("reference.png")
	var image:=Image.create(8,8,false,Image.FORMAT_RGBA8);image.fill(Color(.2,.4,.6,.5));image.save_png(reference_path)
	var reference:={"format":"studio_reference_sheet_1","name":"reference.png","source":reference_path,"sha256":FileAccess.get_sha256(reference_path)}
	var wrapped:=folder.path_join("reference-timing")
	why=Storage.save_project(wrapped,long_video,keys,layers,"",0,{},{},{},true,world,{},[],{},null,reference)
	check(why.is_empty(),"size basis composes around timing and reference: "+why)
	if why.is_empty():
		var data:=manifest(wrapped)
		check(data.schema_version==9 and data.basis_content_schema_version==8 and data.timing_content_schema_version==7 and data.content_schema_version==4,"wrapper order is basis9 then timing8 then reference7 then world4")
		var result:=Storage.load_project(wrapped)
		check(not result.has("error") and result.get("schema_version")==9 and not ImportBasis.inspect_capability(result).has("error"),"reference/timing runtime keeps size capability and wrapper facts")
		check(not result.has("error") and Boundary.decoded_content_schema(result)==4 and World.from_project(result)==result.world,"schema9 timing/reference stack normalizes to world4 without losing bases")
		check(not result.has("error") and result.reference_sheet.get("source")==wrapped.path_join(data.reference_sheet.path),"reference still resolves through existing checked payload route")
	var wrapped_child: Dictionary=ImportBasis.encode_capability(child).document
	check(Extended.child_schema(wrapped_child)==4,"sequence child recognises supported own basis wrapper")
	wrapped_child.import_basis_capability="unsupported"
	check(Extended.child_schema(wrapped_child)==-1,"sequence child rejects unsupported own capability")
	print("IMPORT_BASIS_STORAGE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)

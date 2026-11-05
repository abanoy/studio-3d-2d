extends SceneTree
const Extended=preload("res://src/extended_timing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Timeline=preload("res://src/timeline.gd")
const Origin=preload("res://src/drawing_origin.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":1440}
	for pair in [[24,1,1440],[120,1,7200],[24000,1001,1438],[30000,1001,1798],[1,1001,240]]:
		var timing:=video.duplicate();timing.fps_num=pair[0];timing.fps_den=pair[1];timing.duration_frames=pair[2]
		check(Extended.video_error(timing).is_empty() and Extended.max_frames(timing)==pair[2],"exact rational timing limit "+str(pair))
		if pair[2]>240:timing.duration_frames+=1;check(not Extended.video_error(timing).is_empty(),"one frame over timing envelope refuses")
	for value in [0,1441,7201,12.5,true,NAN]:
		var timing:=video.duplicate();timing.duration_frames=value;check(not Extended.video_error(timing).is_empty(),"invalid length refuses "+str(value))
	var keys: Array=[Timeline.key(0,Vector3(0,2,5),Quaternion.IDENTITY,60),Timeline.key(1440,Vector3(1,2,5),Quaternion.IDENTITY,60)]
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[]}]
	for kind in [3,4,5,6,7]:
		var world: Dictionary={} if kind==3 else World.empty()
		if kind==5:world.format=World.EFFECT_FORMAT;world["effects"]=[]
		var graph:={};var reference:={}
		if kind==6:
			var child_video:=video.duplicate();child_video.duration_frames=48
			var child:={"schema_version":4,"video":child_video,"camera_keys":[keys[0]],"layers":layers,"world":World.empty(),"audio":{}}
			graph={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Short child","scene":child,"clips":[]}],"clips":[{"id":"loop","asset_id":"child","start":1200,"duration":240,"source_in":0,"time_in":0,"key_in":0,"loop":true,"visible":true,"muted":false,"gain_db":0,"keys":[Graph.key()]}]}
		if kind==7:
			var png:=folder.path_join("reference.png");var image:=Image.create(8,8,false,Image.FORMAT_RGBA8);image.fill(Color(.25,.5,.75,.5));image.save_png(png)
			reference={"format":"studio_reference_sheet_1","name":"reference.png","source":png,"sha256":FileAccess.get_sha256(png)}
		var target:=folder.path_join(str(kind));var why:=Storage.save_project(target,video,keys,layers,"res://examples/room.glb" if kind==3 else "",1300,{},{},{},true,world,{},[],graph,null,reference)
		check(why.is_empty(),"long content saves "+str(kind)+": "+why)
		if not why.is_empty():continue
		var saved: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(target.path_join("project.json")))
		check(saved.schema_version==8 and saved.timing_content_schema_version==kind,"explicit schema8 wraps content "+str(kind))
		var loaded:=Storage.load_project(target)
		check(not loaded.has("error") and loaded.schema_version==(4 if kind==7 else kind) and loaded.video.duration_frames==1440,"cold reader unwraps correct runtime dispatch "+str(kind)+": "+str(loaded.get("error","")))
		check(Storage.readable_manifest(target.path_join("project.json")),"recovery catalog recognizes longer content "+str(kind))
		var downgrade:=saved.duplicate(true);downgrade.schema_version=kind;downgrade.erase("timing_content_schema_version")
		check(Storage.decode_project(downgrade,target).has("error"),"downgraded extended content refuses "+str(kind))
	var fast:=video.duplicate();fast.fps_num=120;fast.duration_frames=7200
	var target:=folder.path_join("maximum");var why:=Storage.save_project(target,fast,[keys[0]],layers,"",7199,{},{},{},true,World.empty())
	check(why.is_empty() and not Storage.load_project(target).has("error"),"7200-frame project round-trips without old1920bound")
	var before:=FileAccess.get_file_as_bytes(target.path_join("project.json"));fast.duration_frames=7201
	check(not Storage.save_project(target,fast,[keys[0]],layers,"",0,{},{},{},true,World.empty()).is_empty() and FileAccess.get_file_as_bytes(target.path_join("project.json"))==before,"invalid save preserves previous manifest bytes")
	var ancestry:={"format":"studio_drawing_origin_3","kind":"krita","name":"original.kra","sha256":"a".repeat(64),"width":32,"height":32,"fps":24,"range":[],"visibility":{},"fit":[32,32,0,0],"rate":[24,1],"at":1300,"duration":24}
	check(Origin.error(ancestry).is_empty(),"late drawing ancestry keeps original identity")
	var old:=ancestry.duplicate();old.format="studio_drawing_origin_1";check(not Origin.error(old).is_empty(),"old ancestry format cannot claim late placement")
	var too_long:=ancestry.duplicate();too_long.duration=241;check(not Origin.error(too_long).is_empty(),"late ancestry still caps each original import at240frames")
	var video_origin:=ancestry.duplicate(true);video_origin.format="studio_drawing_origin_4";video_origin.kind="video"
	for field in ["fps","range","visibility"]:video_origin.erase(field)
	video_origin["source_rate"]=[24,1];video_origin["source_duration"]=[1,1];video_origin["chroma"]={"enabled":false,"color":"00ff00","similarity":.1,"blend":.05}
	check(Origin.error(video_origin).is_empty(),"late video ancestry retains strict original decode choices")
	video_origin.format="studio_drawing_origin_2";check(not Origin.error(video_origin).is_empty(),"old video ancestry rejects late placement")
	var short_video:=video.duplicate();short_video.duration_frames=48
	var child:={"schema_version":4,"video":short_video,"camera_keys":[keys[0]],"layers":[{"id":"child-ink","name":"Retained ancestry","visible":true,"cels":[],"origin":ancestry}],"world":World.empty(),"audio":{}}
	var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Short retained ancestry","scene":child,"clips":[]}],"clips":[]}
	var retained:=folder.path_join("retained");why=Storage.save_project(retained,short_video,[keys[0]],layers,"",0,{},{},{},true,World.empty(),{},[],graph)
	check(why.is_empty() and not Storage.load_project(retained).has("error"),"short parent retains extended child ancestry with nested schema8")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(retained.path_join("project.json")))
	check(manifest.schema_version==8 and manifest.sequence_graph.assets[0].scene.schema_version==8,"short enclosing project explicitly declares extended child content")
	print("EXTENDED_TIMING_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

extends SceneTree
const Preset=preload("res://src/movement_path_preset.gd")
const PathData=Preset.PathData
const Model=Preset.Model
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func document(offset: float) -> Dictionary:
	var result:=Model.definition("res://project.godot")
	for at in [0,48]:
		var transform:=Model.identity();transform.scale=1.+float(at)/48;transform.position=[offset+float(at)/24,0,-3]
		transform.rotation_xyzw=[0,sin(float(at)/96),0,cos(float(at)/96)]
		var bone:=Model.identity();bone.position=[float(at)/48,0,0]
		result.pose_keys.append({"frame":at,"pose":{"different-joint":bone},"transform":transform,"interpolation":"ease"})
	return result
func _initialize() -> void:
	var video:={"fps_num":24,"fps_den":1,"duration_frames":48}
	var source:=document(1);var edited:=PathData.change(source,24,Vector3(3,1,-3),48)
	check(not edited.has("error"),"source waypoint edit creates independent position curve")
	var captured:=Preset.capture(edited.data,video,"Reusable route")
	check(not captured.has("error") and Preset.error(captured.get("preset",{})).is_empty(),"ordinary eased source path captures as strict relative data")
	if captured.has("error"):print(captured);quit(1);return
	var value: Dictionary=captured.preset
	check(value.keys.size()==3 and value.length==48 and Model.Timeline.vector(value.keys[0].offset)==Vector3.ZERO,"preset stores authored points with zero-relative introduction")
	var target:=document(10);var old:=target.duplicate(true);var assigned:=Preset.assign(target,video,value,24)
	check(not assigned.has("error"),"same-rate path assigns to a different model's position channel")
	if assigned.has("error"):print(assigned);quit(1);return
	var before:=Model.new();before.data=target;before.motion_video=video
	var after:=Model.new();after.data=assigned.data;after.motion_video=video
	var exact:=true
	for half in range(97):
		var at:=float(half)/2;var a:=before.sample_authored_transform(at);var b:=after.sample_authored_transform(at)
		exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale and before.sample_body(at)==after.sample_body(at) and before.sample_shapes(at)==after.sample_shapes(at)
	check(exact and target==old,"all97 half-frame pose/turn/size/expression peers and original document remain exact")
	check(after.sample_authored_transform(0).position==[10.,0.,-3.] and after.sample_authored_transform(24).position==[12.,1.,-3.] and after.sample_authored_transform(48).position==[12.,0.,-3.],"reused curve anchors at target introduction rather than source coordinates")
	check(not Preset.assign(target,{"fps_num":30,"fps_den":1,"duration_frames":48},value,0).get("error","").is_empty(),"rate mismatch refuses without silent retiming")
	check(not Preset.assign(target,{"fps_num":24,"fps_den":1,"duration_frames":24},value,0).get("error","").is_empty(),"oversize path refuses without truncation")
	check(not Preset.assign(target,video,{"format":"unknown"},0).get("error","").is_empty(),"unsupported data refuses before touching target")
	check(not Preset.assign({},video,value,0).get("error","").is_empty(),"malformed target refuses before field evaluation")
	check(not Preset.assign(target,{"fps_num":true,"fps_den":1,"duration_frames":48},value,0).get("error","").is_empty(),"malformed project timing refuses")
	check(not Preset.assign(target,{"fps_num":48,"fps_den":2,"duration_frames":48},value,0).has("error"),"equivalent rational rates preserve exact frame timing")
	var malformed: Array=[]
	for spec in [["format","other"],["name","bad\nname"],["name",""],["length",0],["fps_num",true],["coordinate_space","world_absolute"],["keys",[]]]:
		var bad:=value.duplicate(true);bad[spec[0]]=spec[1];malformed.append(bad)
	for spec in [["frame",true],["frame",1],["offset",[1,0,0]],["offset",[false,0,0]],["offset",[0,NAN,0]],["interpolation","other"]]:
		var bad:=value.duplicate(true);bad.keys[0][spec[0]]=spec[1];malformed.append(bad)
	var extra:=value.duplicate(true);extra["source"]="../../external.glb";malformed.append(extra)
	check(malformed.all(func(v):return not Preset.error(v).is_empty()),"malformed timing/offset/name/unknown-path payloads all reject")
	var plain:=Model.definition("res://project.godot");check(Preset.capture(plain,video,"No route").has("error"),"single static placement does not pretend to be an exchanged path")
	var static_target:=Model.definition("res://project.godot");var static_copy:=static_target.duplicate(true)
	var static_route:=Preset.assign(static_target,video,value,24)
	check(not static_route.has("error") and static_target==static_copy,"fresh static target receives one continuous route without changing original")
	static_target["start_frame"]=12
	var later:=Preset.assign(static_target,{"fps_num":24,"fps_den":1,"duration_frames":96},value,24)
	var later_ok:=not later.has("error")
	if later_ok:
		var probe:=Model.new();probe.data=later.data;probe.motion_video={"fps_num":24,"fps_den":1,"duration_frames":96}
		later_ok=int(later.data.start_frame)==12 and Model.Timeline.vector(probe.sample_authored_transform(36).position)==Vector3(2,1,0)
	check(later_ok,"later introduction keeps its frame and offsets route from that introduction")
	check(Preset.assign(static_target,video,value,0).has("error"),"route beyond remaining duration refuses on a valid later-introduced target")
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var file:=folder.path_join("Route.haspaths.json")
	check(Preset.write_file(file,value).is_empty(),"data-only preset writes and commits atomically")
	var loaded:=Preset.read_file(file);var same:=not loaded.has("error")
	if same:
		for half in range(97):same=same and Preset.sample(loaded.preset,float(half)/2)==Preset.sample(value,float(half)/2)
	check(same,"cold JSON numbers retain all97 half-frame path samples exactly")
	var saved:=FileAccess.get_sha256(file);check(not Preset.write_file(file,malformed[0]).is_empty() and FileAccess.get_sha256(file)==saved,"invalid export preserves previous preset file")
	var protected:=folder.path_join("parameters.json");FileAccess.open(protected,FileAccess.WRITE).store_string("original parameters")
	check(not Preset.write_file(protected,value,[protected]).is_empty() and FileAccess.get_file_as_string(protected)=="original parameters","known original native parameter file is protected from preset export")
	var large:=folder.path_join("large.json");var writer:=FileAccess.open(large,FileAccess.WRITE);writer.store_string("x".repeat(Preset.MAX_BYTES+1));writer.close()
	check(Preset.read_file(large).has("error"),"oversized file refuses before parsing")
	var unavailable:=folder.path_join("unavailable/missing.json");check(not Preset.write_file(unavailable,value).is_empty(),"unavailable destination reports failure without a partial preset")
	print("MOVEMENT_PATH_PRESET_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

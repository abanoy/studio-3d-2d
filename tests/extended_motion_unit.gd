extends "res://tests/movement_path_preset_unit.gd"
const Assist=preload("res://src/motion_assist.gd")
func _initialize() -> void:
	var video:={"fps_num":24,"fps_den":1,"duration_frames":1440}
	var source:=document(1);source["start_frame"]=1300
	for key in source.pose_keys:key.frame+=1300
	var captured:=Preset.capture(source,video,"Late short route")
	check(not captured.has("error"),"short movement route captures after frame1300: "+str(captured.get("error","")))
	if captured.has("error"):quit(1);return
	check(captured.preset.length==48,"late route keeps48frame local length")
	var target:=document(10);target["start_frame"]=1300
	for key in target.pose_keys:key.frame+=1300
	var assigned:=Preset.assign(target,video,captured.preset,1300)
	check(not assigned.has("error"),"late target accepts reusable route: "+str(assigned.get("error","")))
	if assigned.has("error"):quit(1);return
	var result:=Preset.capture(assigned.data,video,"Round trip")
	check(not result.has("error") and result.preset.keys==captured.preset.keys,"late Model9 route recaptures exact relative controls")
	var main: Array=[]
	for key in source.pose_keys:main.append({"frame":key.frame,"value":key.transform,"interpolation":key.interpolation})
	var assist:=Assist.new();var why:=assist.build(main,video)
	check(why.is_empty(),"derived motion preview accepts longer project: "+why)
	check(assist._main==main and not assist._helpers.is_empty(),"derived preview preserves late authored keys and produces helpers")
	print("EXTENDED_MOTION_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

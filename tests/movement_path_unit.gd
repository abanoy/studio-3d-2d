extends SceneTree
const PathData=preload("res://src/movement_path.gd")
const Model=PathData.Model
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS "if ok else"FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var original:=Model.definition("res://project.godot")
	for at in [0,48]:
		var transform:=Model.identity();transform["scale"]=1.;transform.position=[float(at)/24.,0,0]
		var bone:=Model.identity();bone.position=[float(at)/48.,0,0]
		original.pose_keys.append({"frame":at,"pose":{"left":bone},"transform":transform,"interpolation":"ease"})
	var source:=Model.new();source.data=original
	var changed:=PathData.change(original,24,Vector3(3,4,5),48)
	check(not changed.has("error")and Model.validate(changed.get("data",{}),48).is_empty(),"path point creates a valid independent root control")
	if changed.has("error"):print(changed);quit(1);return
	var edited:=Model.new();edited.data=changed.data;var exact:=true
	for half in range(97):
		var at:=float(half)/2.;exact=exact and source.sample_body(at)==edited.sample_body(at) and source.sample_authored_transform(at).rotation_xyzw==edited.sample_authored_transform(at).rotation_xyzw and source.sample_authored_transform(at).scale==edited.sample_authored_transform(at).scale
	check(exact and edited.sample_authored_transform(24).position==[3.,4.,5.],"all peer pose/rotation/scale samples remain exact while position changes")
	check(original.pose_keys.size()==2 and PathData.controls(changed.data).map(func(p):return p.frame)==[0,24,48],"path editing retains original source and exposes exact keyed frames")
	var removed:=PathData.remove(changed.data,24,48);edited.data=removed.data;exact=true
	for half in range(97):exact=exact and source.sample_authored_transform(float(half)/2.)==edited.sample_authored_transform(float(half)/2.)
	check(exact,"deleting the inserted point restores original sampled movement")
	for view in range(3):
		var prior:=Vector3(2,4,6);var point:=PathData.unprojected(Vector2(7,9),prior,view)
		check(PathData.projected(point,view)==Vector2(7,9)and (point.y==prior.y if view==0 else point.z==prior.z if view==1 else point.x==prior.x),"orthographic edit preserves hidden depth in view "+str(view))
	var turn:=original.duplicate(true);turn.pose_keys[1].transform.rotation_xyzw=[0,sin(.5),0,cos(.5)]
	turn.pose_keys[1].transform.scale=2.
	var turned:=PathData.change(turn,24,Vector3.ONE,48);source.data=turn;edited.data=turned.get("data",{});exact=not turned.has("error")
	for half in range(97):
		var a:=source.sample_authored_transform(float(half)/2.);var b:=edited.sample_authored_transform(float(half)/2.)
		exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
	check(exact and edited.data.format==PathData.Components.FORMAT,"older models upgrade without re-easing their turns or scale")
	var at_zero:=PathData.change(turn,0,Vector3(7,8,9),48);edited.data=at_zero.data
	check(edited.sample_authored_transform(0,true)==edited.sample_authored_transform(0,false) and edited.sample_authored_transform(0,true).position==[7.,8.,9.],"same-frame path edit refreshes displayed draft")
	var removed_zero:=PathData.remove(at_zero.data,0,48);edited.data=removed_zero.data
	check(edited.sample_authored_transform(0,true)==edited.sample_authored_transform(0,false),"same-frame deletion refreshes displayed draft")
	check(not PathData.change(turn,48,Vector3.ONE,48).has("error"),"existing movement points remain editable during turns")
	var hold:=original.duplicate(true);hold.pose_keys[0].interpolation="hold"
	var line:=PathData.preview(hold,{"fps_num":24,"fps_den":1,"duration_frames":48})
	check(line.any(func(p):return p.frame==48 and not p.join),"preview does not draw travel across an explicit hold jump")
	check(PathData.change(original,12,Vector3(NAN,0,0),48).has("error")and PathData.change(original,-1,Vector3.ZERO,48).has("error"),"invalid path coordinates and frames refuse")
	print("MOVEMENT_PATH_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

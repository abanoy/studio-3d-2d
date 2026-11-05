extends SceneTree
const Model=preload("res://src/model.gd")
const Body=preload("res://src/body_animation.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func transform(x: float,root:=false) -> Dictionary:
	var result:=Model.identity();result.position=[x,0,0]
	if root:result["scale"]=1.
	return result
func _initialize() -> void:
	create_timer(20).timeout.connect(func():push_error("Body model unit watchdog");quit(2))
	var old:=Model.definition("res://project.godot")
	for frame in [0,24]:old.pose_keys.append({"frame":frame,"pose":{"left":transform(0 if frame==0 else 10)},"transform":transform(0 if frame==0 else 10,true),"interpolation":"ease"})
	var before:=Model.new();before.data=old.duplicate(true);var actor:=Model.new();actor.data=old.duplicate(true)
	var edit:={"frame":12,"pose":actor.sample(12),"transform":actor.sample_transform(12),"authored_channels":["right"],"interpolation":"ease"};edit.pose.right=transform(1.)
	var error:=actor.put_pose_key(edit,48,false,old)
	check(error.is_empty() and actor.data.format==Model.BODY_FORMAT and Model.validate(actor.data,48).is_empty(),"authored body edit promotes to valid model6")
	var exact:=true
	for half in range(97):
		var frame:=float(half)/2;exact=exact and actor.sample(frame).left==before.sample(frame).left and actor.sample_transform(frame)==before.sample_transform(frame)
	check(exact and actor.sample(6).left.position[0]==1.5625,"model6 preserves untouched limb and root easing at every half-frame")
	check(absf(actor.sample(6).right.position[0]-.5)<.000001 and actor.sample(30).right.position[0]==1.,"model6 samples the new independent limb")
	check(actor.data.animation_clips[0].keys==old.pose_keys and actor.authored_keys().size()==3,"source snapshots stay intact while public authored frames include sparse controls")
	var recovered:=Model.new();recovered.data=JSON.parse_string(JSON.stringify(actor.data,"",true,true))
	check(Model.validate(recovered.data,48).is_empty() and recovered.sample(6)==actor.sample(6),"native model6 data validates and samples after JSON reopen")
	error=actor.remove_pose_key(12,48,"right")
	check(error.is_empty() and actor.sample(6).get("right",Model.identity()).position[0]==0 and actor.sample(6).left==before.sample(6).left,"selected-part removal preserves peer animation")
	var shaped:=Model.new();shaped.data=Body.promote(old,48)
	shaped.data.shape_base={"3":{"0":0.}};shaped.data.shape_pose={"3":{"0":0.}};shaped.data.shape_starts={"3":{"0":0}}
	shaped.data=Model.ShapeAnimation.put_key(shaped.data,{"frame":36,"shapes":{"3":{"0":1.}},"interpolation":"ease"},48)
	check(Model.validate(shaped.data,48).is_empty() and shaped.sample_transform(30)==before.sample_transform(30),"expression-only model6 blocks leave body motion unchanged")
	var bad:=shaped.data.duplicate(true);bad.animation_clips[0].body_controls={"left":[{"frame":12,"value":transform(NAN),"interpolation":"ease"}]}
	check(not Model.validate(bad,48).is_empty(),"invalid body controls refuse before evaluation")
	bad=shaped.data.duplicate(true);bad.format="studio_model_5"
	check(not Model.validate(bad,48).is_empty(),"old model versions cannot silently accept independent body fields")
	var recorded:=Model.new();recorded.data=Model.definition("res://project.godot");var base:=recorded.data.duplicate(true)
	error=recorded.put_pose_key({"frame":0,"pose":{},"transform":transform(0,true),"authored_channels":["@root"],"interpolation":"hold"},48,true,base)
	base=recorded.data.duplicate(true)
	error=recorded.put_pose_key({"frame":24,"pose":{"new_limb":transform(1.)},"transform":transform(0,true),"authored_channels":["new_limb"],"interpolation":"linear"},48,false,base)
	check(error.is_empty() and recorded.sample(12).new_limb.position[0]==0. and recorded.sample(24).new_limb.position[0]==1.,"explicit Record retains the rest-pose interpolation of subsequently animated parts")
	check(Body.B.frames(Body.view(recorded.data),"new_limb")==[0,24],"shared recorded rest exposes real per-part authored frame0")
	var later:=Model.new();later.data=Model.definition("res://project.godot");later.data["start_frame"]=24;base=later.data.duplicate(true)
	error=later.put_pose_key({"frame":4,"pose":{},"transform":transform(1.,true),"authored_channels":["@root"],"interpolation":"ease"},48,false,base)
	check(error.is_empty() and later.data.start_frame==4 and later.sample_transform(48).position[0]==1.,"earlier manual key corrects introduction without a phantom later return to rest")
	var growing:=Model.new();growing.data=Model.definition("res://project.godot");growing.data["start_frame"]=14
	for frame in [14,18,22]:
		base=growing.data.duplicate(true);error=growing.put_pose_key({"frame":frame,"pose":{},"transform":transform(float(frame-10)/4,true),"authored_channels":["@root"],"interpolation":"ease"},48,false,base)
	check(error.is_empty() and growing.data.animation_clips.size()==1 and growing.data.animation_clips[0].length==9,"a new authored take grows within one source block rather than keeping empty import placeholders")
	var legacy_delete:=Model.new();legacy_delete.data=old.duplicate(true)
	error=legacy_delete.remove_pose_key(24,48,"left")
	check(error.is_empty() and legacy_delete.data.format==Model.BODY_FORMAT and legacy_delete.sample(24).left.position[0]==0. and legacy_delete.sample_transform(24).position[0]==10.,"selected-part deletion in an older project upgrades only that operation and preserves root motion")
	var mixed:=Model.new();mixed.data=Model.definition("res://project.godot")
	for entry in [[0,"@root",0.],[14,"arm",1.],[24,"@root",10.]]:
		base=mixed.data.duplicate(true)
		var key:={"frame":entry[0],"pose":{},"transform":transform(entry[2],true),"authored_channels":[entry[1]],"interpolation":"ease"}
		if entry[1]!="@root":key.pose[entry[1]]=transform(entry[2])
		error=mixed.put_pose_key(key,48,false,base)
	check(error.is_empty() and mixed.data.animation_clips.size()==1 and mixed.sample_transform(6).position[0]==1.5625,"growing another part never moves the root's own interpolation endpoint")
	var compiled_exact:=true
	for half in range(97):
		var at:=float(half)/2;var reference:=Body.sample(mixed.data,at)
		compiled_exact=compiled_exact and mixed.sample(at)==reference.pose and mixed.sample_transform(at)==reference.transform
	check(compiled_exact,"compiled per-part ranges exactly match source evaluation at every half-frame")
	var previous:=Model.new();previous.data=mixed.data.duplicate(true)
	mixed.data=Model.Clips.split(mixed.data,8).data
	var split_exact:=true
	for half in range(97):
		var at:=float(half)/2;split_exact=split_exact and mixed.sample(at)==previous.sample(at) and mixed.sample_transform(at)==previous.sample_transform(at)
	check(split_exact,"explicit source split retains mixed-part motion throughout both ranges")
	var shifted: Dictionary=Model.Clips.move(previous.data,previous.data.animation_clips[0].id,20,48).data
	var shifted_actor:=Model.new();shifted_actor.data=shifted
	var shifted_arm:=[]
	for half in range(97):shifted_arm.append(shifted_actor.sample(float(half)/2).arm)
	base=shifted_actor.data.duplicate(true)
	error=shifted_actor.put_pose_key({"frame":4,"pose":{"third":transform(2.)},"transform":transform(0.,true),"authored_channels":["third"],"interpolation":"ease"},48,false,base)
	var backward_exact:=true
	for half in range(97):backward_exact=backward_exact and shifted_actor.sample(float(half)/2).arm==shifted_arm[half]
	check(error.is_empty() and backward_exact,"backward block growth preserves another part's original source addresses and introduction")
	bad=previous.data.duplicate(true)
	for i in range(9):
		bad.animation_clips[0].body_controls["budget-%d" % i]=[]
		for frame in range(241):bad.animation_clips[0].body_controls["budget-%d" % i].append({"frame":frame,"value":transform(0.),"interpolation":"ease"})
	check("2048" in Model.validate(bad,240),"combined independent controls retain the existing project key budget")
	var precise:=Model.new();precise.data=previous.data.duplicate(true);base=precise.data.duplicate(true)
	var tiny:=Model.identity();tiny.rotation_xyzw=[0.000342570594511926,-7.56021148462516e-11,0.00000376461503037717,1.]
	error=precise.put_pose_key({"frame":12,"pose":{"tiny":tiny},"transform":precise.sample_transform(12),"authored_channels":["tiny"],"interpolation":"ease"},48,false,base)
	var precise_read:=Model.new();precise_read.data=JSON.parse_string(JSON.stringify(precise.data,"",true,true))
	check(error.is_empty() and precise_read.data.animation_clips[0].body_controls.tiny[0].value.rotation_xyzw[1]==tiny.rotation_xyzw[1],"full-precision project encoding retains very small authored rotation values exactly")
	var precise_samples:=true
	for half in range(97):
		var at:=float(half)/2;precise_samples=precise_samples and precise_read.sample(at)==precise.sample(at) and precise_read.sample_transform(at)==precise.sample_transform(at)
	check(precise_samples,"full-precision reopen retains independent tiny-rotation samples at every half-frame")
	var args:=OS.get_cmdline_user_args()
	if not args.is_empty() and FileAccess.file_exists(args[0].path_join("recorded-models.json")):
		var takes: Array=JSON.parse_string(FileAccess.get_file_as_string(args[0].path_join("recorded-models.json")))
		for take in takes:
			var legacy:=Model.new();legacy.data=take;var integrated:=Model.new();integrated.data=Body.promote(take,48)
			var capture_exact:=not integrated.data.has("error") and Model.validate(integrated.data,48).is_empty()
			if capture_exact:
				for half in range(97):
					var at:=float(half)/2;var actual:=integrated.sample(at);var expected:=legacy.sample(at)
					capture_exact=capture_exact and integrated.sample_transform(at)==legacy.sample_transform(at)
					for id in actual:capture_exact=capture_exact and actual[id]==expected.get(id,Model.identity())
			check(capture_exact,"normal compiled model6 retains every native recorded part at97half-frames: "+str(take.name))
	print("BODY_ANIMATION_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

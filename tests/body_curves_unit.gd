extends SceneTree
const B=preload("res://src/body_curves.gd")
const Model=B.Model
const C=Model.Clips
var checks:=0
var failures:=0
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func transform(x: float,root:=false) -> Dictionary:
	var result:=Model.identity();result.position=[x,0,0]
	if root:result["scale"]=1.
	return result
func key(frame: int,x: float,mode: String="ease") -> Dictionary:
	return {"frame":frame,"pose":{"left":transform(x)},"transform":transform(x,true),"interpolation":mode}
func equal(a,b) -> bool:
	return JSON.stringify(a)==JSON.stringify(b)
func effective_equal(a: Dictionary,b: Dictionary) -> bool:
	for field in ["position","rotation_xyzw"]:
		for i in range(a[field].size()):
			if float(a[field][i])!=float(b[field][i]):return false
	return float(a.get("scale",1))==float(b.get("scale",1))
func same_part(data: Dictionary,id: String,expected: Array) -> bool:
	for half in range(expected.size()):
		if not equal(B.sample_channel(data,float(half)/2,id),expected[half]):return false
	return true
func samples(data: Dictionary,id: String) -> Array:
	var result:=[]
	for half in range(97):result.append(B.sample_channel(data,float(half)/2,id))
	return result
func _initialize() -> void:
	create_timer(20).timeout.connect(func():push_error("Body curves unit watchdog");quit(2))
	var old:=Model.definition("res://project.godot");old.pose_keys=[key(0,0.),key(24,10.)];var old_copy:=old.duplicate(true)
	var actor:=Model.new();actor.data=old
	var data:=B.extract(old);var original: Dictionary=data.duplicate(true)
	check(B.validate(data,48).is_empty(),"legacy snapshots extract into a valid independent body contract")
	var legacy_exact:=true
	for half in range(97):
		var frame:=float(half)/2
		legacy_exact=legacy_exact and equal(B.sample_channel(data,frame,"left"),actor.sample(frame).left) and equal(B.sample_channel(data,frame,"@root"),actor.sample_transform(frame))
	check(legacy_exact,"legacy body and root evaluation remain exact at every half-frame")
	var left:=samples(data,"left");var root_motion:=samples(data,"@root")
	var result:=B.put(data,12,{"right":transform(1.)},"ease",48);check(not result.has("error"),"new bone gets an independent control")
	data=result.data
	check(same_part(data,"left",left) and same_part(data,"@root",root_motion) and equal(original.pieces[0].keys,data.pieces[0].keys),"new bone preserves original snapshot values and all eased peer samples")
	check(absf(B.sample_channel(data,6,"left").position[0]-1.5625)<.000001,"untouched limb keeps its original1.5625 eased value")
	check(absf(B.sample_channel(data,6,"right").position[0]-.5)<.000001 and B.sample_channel(data,30,"right").position[0]==1.,"new bone interpolates from the prior base and holds after its last key")
	check(B.frames(data,"right")==[12] and B.frames(data,"left")==[0,24],"each body part exposes only its own authored frames")
	data=B.put(data,0,{"right":transform(0.)},"hold",48).data
	check(B.sample_channel(data,6,"right").position[0]==0. and same_part(data,"left",left),"same-frame interpolation choices do not alter another bone")
	var removed:=B.remove_key(data,0,"right",48)
	check(not removed.has("error") and B.frames(removed.data,"right")==[12] and same_part(removed.data,"left",left),"removing a new body-part key leaves peers exact")
	removed=B.remove_key(data,0,"left",48)
	check(not removed.has("error") and B.frames(removed.data,"left")==[24] and same_part(removed.data,"@root",root_motion),"removing a legacy bone key does not remove its root snapshot")
	data=B.put(removed.data,0,{"left":transform(0.)},"ease",48).data
	check(B.frames(data,"left")==[0,24] and same_part(data,"left",left),"re-keying a removed legacy control restores the original curve")
	var split:=B.split(data,12,48);check(not split.has("error"),"independent tracks split into owned source slices")
	var split_exact:=true
	for id in B.known_channels(data):split_exact=split_exact and same_part(split.data,id,samples(data,id))
	check(split_exact,"split preserves every body channel at every half-frame")
	var moved:=B.move(split.data,split.right_id,30,48);var relative_exact:=not moved.has("error")
	if relative_exact:
		for half in range(25):
			for id in B.known_channels(data):relative_exact=relative_exact and equal(B.sample_channel(moved.data,30.+float(half)/2,id),B.sample_channel(data,12.+float(half)/2,id))
	check(relative_exact,"moving a split carries every channel's original relative motion")
	check(B.sample_channel(moved.data,20,"left").position[0]>B.sample_channel(data,11,"left").position[0] and B.sample_channel(moved.data,20,"left").position[0]<B.sample_channel(data,12,"left").position[0],"body gaps connect recorded endpoints rather than freezing")
	var outside: Dictionary=B.put(original,30,{"right":transform(1.)},"linear",48).data
	check(same_part(outside,"left",left) and same_part(outside,"@root",root_motion),"a new body-part block after a take leaves existing curves exact")
	var right_before:=samples(outside,"right")
	outside=B.put(outside,27,{"third":transform(2.)},"ease",48).data
	check(same_part(outside,"right",right_before),"earlier block for another part preserves the first part's introduction")
	var bad:=data.duplicate(true);bad.pieces[0].controls.right[0].value.position[0]=NAN
	check(not B.validate(bad,48).is_empty(),"nonfinite part values reject")
	bad=data.duplicate(true);bad.pieces[0].controls.right.append(bad.pieces[0].controls.right[0].duplicate(true))
	check(not B.validate(bad,48).is_empty(),"duplicate or unsorted control addresses reject")
	check(not B.check_bindings(data,["left"]).is_empty() and B.check_bindings(data,["left","right"]).is_empty(),"native bone identities validate without renaming")
	check(B.put(data,49,{"left":transform(1.)},"ease",48).has("error") and B.put(data,12,{"left":transform(1.)},"bad",48).has("error"),"out-of-project frames and unknown interpolation refuse")
	check(equal(old,old_copy),"all edits leave the original source record untouched")
	bad=old.duplicate(true);bad.pose_keys[0].transform.rotation_xyzw=[0,0,0,0]
	check(B.extract(bad).has("error"),"malformed source records refuse before extraction")
	bad=data.duplicate(true);bad.pieces[0].removed={"left":[7]}
	check(not B.validate(bad,48).is_empty(),"phantom legacy-key suppression addresses reject")
	bad=data.duplicate(true);bad.base_pose["@root"]=Model.identity()
	check(not B.validate(bad,48).is_empty(),"root and bone identities cannot collide")
	var static_model:=old.duplicate(true);static_model.pose_keys=[];static_model.pose={"still":transform(2.)}
	var static_curves:=B.extract(static_model);var static_before:=static_curves.duplicate(true)
	var static_sample:=B.sample(static_curves,6);static_sample.pose.still.position[0]=99.;static_sample.transform.position[0]=99.
	check(equal(static_curves,static_before),"editing a returned static sample cannot mutate retained base curves")
	var shaped:=Model.ShapeAnimation.promote(old);shaped.shape_base={"3":{"0":0.}};shaped.shape_pose={"3":{"0":0.}};shaped.shape_starts={"3":{"0":0}}
	shaped=Model.ShapeAnimation.put_key(shaped,{"frame":36,"shapes":{"3":{"0":1.}},"interpolation":"ease"},48)
	var shaped_body:=B.extract(shaped)
	check(not shaped_body.has("error") and same_part(shaped_body,"left",left) and same_part(shaped_body,"@root",root_motion),"model5 expression-only pieces never become body anchors during extraction")
	var historical:=old.duplicate(true);var middle:=key(12,5.);middle.pose["right"]=transform(1.);middle["authored_channels"]=["right"]
	Model.Timeline.put_key(historical.pose_keys,middle);var historical_curves:=B.extract(historical)
	check(absf(B.sample_channel(historical_curves,6,"left").position[0]-2.5)<.000001,"historical coupled body motion is preserved rather than silently repaired")
	var args:=OS.get_cmdline_user_args()
	if not args.is_empty() and FileAccess.file_exists(args[0].path_join("recorded-models.json")):
		var recorded: Array=JSON.parse_string(FileAccess.get_file_as_string(args[0].path_join("recorded-models.json")))
		for model in recorded:
			actor=Model.new();actor.data=model;var curves:=B.extract(model);var all_exact:=not curves.has("error") and B.validate(curves,48).is_empty();var began:=Time.get_ticks_usec()
			if all_exact:
				for half in range(97):
					var frame:=float(half)/2;var state:=B.sample(curves,frame);var expected:=actor.sample(frame)
					all_exact=all_exact and effective_equal(state.transform,actor.sample_transform(frame))
					for id in state.pose:all_exact=all_exact and effective_equal(state.pose[id],expected.get(id,Model.identity()))
			print("RECORDED_BODY_CURVES "+JSON.stringify({"model":model.name,"channels":B.known_channels(curves).size(),"comparison_average_usec":float(Time.get_ticks_usec()-began)/97.}))
			check(all_exact,"actual native physics take preserves every effective body channel at every half-frame: "+str(model.name))
	print("BODY_CURVES_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

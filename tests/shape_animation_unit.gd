extends SceneTree
const Model=preload("res://src/model.gd")
const A=Model.ShapeAnimation
const C=Model.Clips
const Recording=preload("res://src/physics_recording.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func amount(data: Dictionary,frame: float) -> float:return float(A.sample(data,frame).get("3",{}).get("0",-999))
func key(frame: int,value: float,interpolation: String="linear") -> Dictionary:
	return {"frame":frame,"pose":{},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0},"shapes":{"3":{"0":value}},"interpolation":interpolation}
func _initialize() -> void:
	create_timer(10).timeout.connect(func():quit(2))
	var old:=Model.definition("res://project.godot");old["start_frame"]=0
	var data:=A.promote(old);data.shape_base={"3":{"0":.2}};data.shape_pose={"3":{"0":.8}};data.shape_starts={"3":{"0":0}}
	data=A.put_key(data,key(0,.2),48);data=A.put_key(data,key(24,.8),48)
	check(Model.validate(data,48).is_empty(),"version5 validates alongside old model versions")
	check(absf(amount(data,12)-.5)<.00001,"shape values interpolate in source time")
	check(absf(amount(data,48)-.8)<.00001,"last expression holds after its block")
	var split:=C.split(data,12)
	check(not split.has("error") and absf(amount(split.data,12)-.5)<.00001,"split preserves the exact source expression")
	var moved:=C.move(split.data,split.right_id,24,48)
	check(absf(amount(moved.data,30)-amount(data,18))<.00001,"moving a split carries relative expression time")
	check(amount(moved.data,18)>amount(data,11) and amount(moved.data,18)<.5,"gap connects expressions rather than freezing")
	var hold:=data.duplicate(true);hold.animation_clips[-1].shape_keys[0].interpolation="hold"
	check(absf(amount(hold,12)-.2)<.00001,"shape keys respect deliberate hold")
	var record_keys: Array=[]
	for frame in range(5,11):var sample:=key(frame,0);sample.erase("shapes");record_keys.append(sample)
	var recorded:=Recording.replace_range(data,record_keys,5,10,48)
	check(not recorded.has("error") and absf(amount(recorded.data,8)-amount(data,8))<.00001,"physics range replacement preserves authored expressions")
	check(absf(amount(recorded.data,20)-amount(data,20))<.00001,"physics recording preserves later expressions")
	var bad:=data.duplicate(true);bad.shape_pose={"03":{"0":1.}}
	check(not Model.validate(bad,48).is_empty(),"ambiguous shape identities reject")
	bad=data.duplicate(true);bad.animation_clips[-1].shape_keys[-1].shapes["3"]["0"]=NAN
	check(not Model.validate(bad,48).is_empty(),"nonfinite animated amounts reject")
	bad=data.duplicate(true);bad.format="studio_model_3"
	check(not Model.validate(bad,48).is_empty(),"old model versions cannot silently carry animated shapes")
	check(preload("res://src/shape_labels.gd").display("まばたき",false)=="Blink ≈" and preload("res://src/shape_labels.gd").display("まばたき",true)=="まばたき","Simple estimates preserve exact Advanced shape names")
	var body:=Model.new();body.data=old.duplicate(true)
	for frame in [0,24]:
		var body_key:=key(frame,0.,"ease");body_key.erase("shapes");body_key.transform.position=[0 if frame==0 else 10,0,0];body.data.pose_keys.append(body_key)
	var independent:=Model.new();independent.data=A.promote(body.data);independent.data.shape_base={"3":{"0":0.}};independent.data.shape_pose={"3":{"0":1.}};independent.data.shape_starts={"3":{"0":0}}
	independent.data=A.put_key(independent.data,key(12,1.,"ease"),48)
	check(Model.validate(independent.data,48).is_empty() and independent.data.animation_clips[0].keys==body.data.pose_keys,"expression insertion leaves existing body control bytes unchanged")
	var unchanged:=true
	for half in range(49):unchanged=unchanged and body.sample_transform(float(half)/2)==independent.sample_transform(float(half)/2)
	check(unchanged and absf(independent.sample_transform(6).position[0]-1.5625)<.000001,"eased body curve is exact at every half-frame after expression insertion")
	check(absf(amount(independent.data,6)-.5)<.000001 and absf(amount(independent.data,20)-1)<.000001,"unrelated body keys do not reset expressions")
	var before_a:=[]
	for frame in range(25):before_a.append(amount(independent.data,frame))
	independent.data.shape_base["3"]["1"]=0.;independent.data.shape_starts["3"]["1"]=0
	var other:=key(18,.7);other.shapes={"3":{"1":.7}};independent.data=A.put_key(independent.data,other,48)
	var separate:=true
	for frame in range(25):separate=separate and absf(amount(independent.data,frame)-float(before_a[frame]))<.000001
	check(separate,"another expression channel leaves the original curve unchanged")
	var legacy:=A.promote(old);legacy.format=A.LEGACY_FORMAT;legacy.erase("shape_starts");legacy.erase("shape_draft_frame");legacy.shape_base={"3":{"0":0.}};legacy.shape_pose={"3":{"0":1.}}
	legacy.animation_clips=[C.clip(old,0,25,0,[key(0,0.,"ease"),key(12,1.,"ease"),key(24,0.,"ease")])]
	legacy.animation_clips[0].keys[1].transform.position=[5,0,0];legacy.animation_clips[0].keys[2].transform.position=[10,0,0]
	var legacy_model:=Model.new();legacy_model.data=legacy;var upgraded:=Model.new();upgraded.data=A.promote(legacy)
	check(Model.validate(legacy,48).is_empty() and absf(legacy_model.sample_transform(6).position[0]-2.5)<.000001,"legacy model4 keeps its historical body evaluation")
	var legacy_exact:=true
	for half in range(49):
		var frame:=float(half)/2;legacy_exact=legacy_exact and legacy_model.sample_transform(frame)==upgraded.sample_transform(frame) and absf(amount(legacy,frame)-amount(upgraded.data,frame))<.000001
	check(legacy_exact and Model.validate(upgraded.data,48).is_empty(),"model4 promotion preserves old body and expression curves exactly")
	var removed:=A.remove_key(independent.data,12,"3","0")
	check(Model.validate(removed,48).is_empty() and not A.has_control(removed,12,"3","0") and removed.animation_clips[0].keys==independent.data.animation_clips[0].keys,"removing one expression leaves body controls exact")
	check(A.has_control(removed,18,"3","1") and absf(float(A.sample(removed,18)["3"]["1"])-.7)<.000001,"removing one expression leaves another expression intact")
	bad=data.duplicate(true);bad.shape_starts["3"]["0"]=49
	check(not Model.validate(bad,48).is_empty(),"out-of-project expression introductions reject")
	bad=data.duplicate(true);bad.shape_starts["999"]={"0":0}
	check(not Model.validate(bad,48).is_empty(),"unbound introduction identities reject")
	var gaps:=A.promote(old);gaps.shape_base={"3":{"0":0.}};gaps.shape_pose={"3":{"0":1.}};gaps.shape_starts={"3":{"0":0}}
	var left:=key(0,0.,"ease");left.erase("shapes");var right:=key(0,0.,"ease");right.erase("shapes");right.transform.position=[10,0,0]
	gaps.animation_clips=[C.clip(old,0,1,0,[left]),C.clip(old,24,1,0,[right])]
	var gap_model:=Model.new();gap_model.data=gaps;var expected_gap:=[]
	for half in range(49):expected_gap.append(gap_model.sample_transform(float(half)/2))
	gap_model.data=A.put_key(gaps,key(12,1.),48)
	var gap_exact:=true
	for half in range(49):gap_exact=gap_exact and gap_model.sample_transform(float(half)/2)==expected_gap[half]
	check(gap_exact and Model.validate(gap_model.data,48).is_empty(),"expression-only block inside body gap preserves every half-frame of body motion")
	var single:=A.promote(old);single.shape_base={"3":{"0":0.,"1":0.}};single.shape_pose=single.shape_base.duplicate(true);single.shape_starts={"3":{"0":0,"1":0}}
	single.animation_clips=[];single=A.put_key(single,key(12,1.,"ease"),48)
	var first_curve:=[]
	for half in range(97):first_curve.append(amount(single,float(half)/2))
	other=key(6,.8);other.shapes={"3":{"1":.8}};single=A.put_key(single,other,48)
	other.frame=18;single=A.put_key(single,other,48)
	var first_exact:=true
	for half in range(97):first_exact=first_exact and absf(amount(single,float(half)/2)-float(first_curve[half]))<.000001
	check(first_exact and Model.validate(single,48).is_empty(),"earlier and later edits of another expression preserve the original introduction and curve")
	var retimed:=preload("res://src/object_timing.gd").move(single,8,48)
	var retime_exact:=true
	for frame in range(33):retime_exact=retime_exact and absf(amount(single,frame)-amount(retimed,frame+8))<.000001
	check(retime_exact and retimed.shape_starts["3"]["0"]==8 and Model.validate(retimed,48).is_empty(),"whole-object retiming carries independent expression introductions")
	var modes:=A.promote(old);modes.shape_base={"3":{"0":0.,"1":0.}};modes.shape_pose=modes.shape_base.duplicate(true);modes.shape_starts={"3":{"0":0,"1":0}}
	modes=A.put_key(modes,key(0,0.),48)
	other=key(0,0.,"hold");other.shapes={"3":{"1":0.}};modes=A.put_key(modes,other,48)
	other=key(24,1.);other.shapes={"3":{"0":1.,"1":1.}};modes=A.put_key(modes,other,48)
	check(absf(amount(modes,12)-.5)<.000001 and float(A.sample(modes,12)["3"]["1"])==0. and Model.validate(modes,48).is_empty(),"different expressions at the same control frame keep their own interpolation choices")
	var before_body:=[]
	for frame in range(49):before_body.append(A.sample(single,frame))
	var body_only:=key(24,0.);body_only.erase("shapes");single=C.put_key(single,body_only,48)
	var expressions_exact:=true
	for frame in range(49):expressions_exact=expressions_exact and A.sample(single,frame)==before_body[frame]
	check(expressions_exact and Model.validate(single,48).is_empty(),"adding a body-only block leaves expression curves exact")
	print("SHAPE_ANIMATION_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

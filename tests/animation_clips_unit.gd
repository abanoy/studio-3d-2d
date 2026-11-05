extends SceneTree
const Clips=preload("res://src/animation_clips.gd")
const Model=preload("res://src/model.gd")
var checks:=0
var failures:=0

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func key(frame: int, x: float, angle: float, interpolation: String) -> Dictionary:
	var q:=Quaternion(Vector3.UP,angle)
	return {"frame":frame,"pose":{"joint":{"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}},"transform":{"position":[x,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0},"interpolation":interpolation}

func same_curve(a: Dictionary, b: Dictionary, a_start:=0, b_start:=0, count:=49) -> bool:
	var aa:=Model.new();aa.data=a;var bb:=Model.new();bb.data=b
	for i in range(count):
		if aa.sample(i+a_start)!=bb.sample(i+b_start) or aa.sample_transform(i+a_start)!=bb.sample_transform(i+b_start):return false
	return true

func _initialize() -> void:
	var original:=Model.definition("res://main.tscn");original["start_frame"]=0
	original.pose_keys=[key(0,0,0,"ease"),key(12,2,0.5,"linear"),key(36,8,1.0,"ease"),key(48,10,1.3,"hold")]
	original.metadata["unchanged"]={"unknown":"retained"}
	var prior:=original.duplicate(true);var promoted:=Clips.promote(original)
	check(Model.validate(promoted,96).is_empty() and promoted.format==Clips.FORMAT and promoted.pose_keys.is_empty(),"version2 owns source curves explicitly and validates")
	check(original==prior and promoted.metadata==prior.metadata,"promotion preserves the input record and unknown provenance")
	check(same_curve(original,promoted),"promotion preserves every root/bone sample including eased/linear segments")
	var divided:=Clips.split(original,24);var split: Dictionary=divided.data
	check(split.animation_clips.size()==2 and split.animation_clips[0].length==24 and split.animation_clips[1].start==24 and split.animation_clips[1].source_in==24,"split uses half-open pieces and source-time addresses")
	check(same_curve(original,split) and Model.validate(split,96).is_empty(),"splitting inside a curve preserves every original frame exactly")
	check(Clips.split(original,0).has("error") and Clips.split(original,49).has("error"),"split rejects boundary/outside requests without mutating source")
	var left: String=divided.left_id;var right: String=divided.right_id
	var shifted:=Clips.move(split,right,40,96)
	check(not shifted.has("error") and same_curve(original,shifted.data,24,40,25),"moving the right piece retains its original parametric motion")
	var rig:=Model.new();rig.data=shifted.data
	var a:=Model.new();a.data=original
	var x: float=rig.sample_transform(30).position[0]
	check(x>a.sample_transform(23).position[0] and x<a.sample_transform(24).position[0],"gap connects the surrounding endpoint states instead of freezing or hiding")
	check(rig.sample(90)==a.sample(48) and rig.sample_transform(90)==a.sample_transform(48),"after the final piece the complete last state holds")
	check(Clips.move(split,right,12,96).has("error") and Clips.move(split,right,80,96).has("error") and original==prior,"overlapping/out-of-project moves fail without changing the original")
	var held: Dictionary=shifted.data.duplicate(true);held.animation_clips[0].keys[1].interpolation="hold";rig.data=held
	check(rig.sample_transform(30)==a.sample_transform(12),"deliberately held source interpolation remains held across a gap")
	var removed:=Clips.remove(shifted.data,left,96)
	check(removed.data.start_frame==40 and removed.data.animation_clips.size()==1,"removing first piece updates introduction to the remaining piece")
	var pasted:=Clips.paste(removed.data,split.animation_clips[0],0,96)
	check(not pasted.has("error") and pasted.data.start_frame==0 and same_curve(original,pasted.data,0,0,24),"pasting a copied piece preserves its own source-time curve")
	check(Clips.paste(split,split.animation_clips[0],8,96).has("error"),"paste cannot overwrite another piece")
	var edited:=Clips.put_key(split,key(8,20,2,"ease"),96)
	check(edited.animation_clips[1]==split.animation_clips[1] and same_curve(original,edited,24,24,25),"editing a split piece cannot change its independently owned sibling")
	check(edited.animation_clips[0].keys.size()==5 and original==prior,"new key is stored in the edited piece while source input stays unchanged")
	var extended:=Clips.put_key(removed.data,key(8,20,2,"ease"),96)
	check(extended.start_frame==8 and Model.validate(extended,96).is_empty(),"manual earlier key introduces authored motion without changing the fixed piece")
	check(same_curve(original,extended,24,40,25),"earlier authored motion preserves every later fixed source sample")
	var near_before:=Clips.put_key(removed.data,key(32,20,2,"ease"),96)
	check(near_before.animation_clips.size()==2 and same_curve(original,near_before,24,40,25),"manual key before a clipped interior cannot alter the original slice's interpolation")
	var grown:=Clips.put_key(extended,key(12,22,2.2,"ease"),96);var backwards:=Clips.put_key(grown,key(4,18,1.8,"ease"),96)
	check(grown.animation_clips.size()==2 and backwards.animation_clips.size()==2 and same_curve(grown,backwards,8,8,5) and same_curve(original,backwards,24,40,25),"new authored take grows both directions while preserving existing motion and fixed neighbors")
	var empty:=Clips.remove(removed.data,right,96)
	check(empty.data.animation_clips.is_empty() and Model.validate(empty.data,96).is_empty(),"cutting last piece retains an empty, valid object record")
	var introduced:=Clips.put_key(empty.data,key(20,5,0.3,"linear"),96)
	check(introduced.animation_clips.size()==1 and introduced.start_frame==20 and Model.validate(introduced,96).is_empty(),"manual edit can introduce an object whose animation pieces were removed")
	var delayed:=original.duplicate(true);delayed.start_frame=16;var delay_split:=Clips.split(delayed,24)
	check(delay_split.data.start_frame==16 and delay_split.data.presence_offset==16,"split preserves an explicit late-introduction offset")
	var bad:=split.duplicate(true);bad.animation_clips[1].start=10
	check(not Model.validate(bad,96).is_empty(),"loader rejects overlapping serialized pieces")
	bad=split.duplicate(true);bad.animation_clips[1].id=bad.animation_clips[0].id
	check(not Model.validate(bad,96).is_empty(),"loader rejects duplicate piece identities")
	bad=split.duplicate(true);bad.animation_clips[0].source_in=-1
	check(not Model.validate(bad,96).is_empty(),"loader rejects invalid source ranges")
	bad=split.duplicate(true);bad.pose_keys=original.pose_keys.duplicate(true)
	check(not Model.validate(bad,96).is_empty(),"version2 rejects ambiguous unowned legacy keys")
	bad=split.duplicate(true);bad.format="studio_model_1"
	check(not Model.validate(bad,96).is_empty(),"piece ownership cannot be disguised as a legacy record")
	bad=promoted.duplicate(true);bad.animation_clips=[]
	var dense:=[]
	for frame in range(241):dense.append(key(frame,float(frame),0,"linear"))
	for i in range(9):
		var piece: Dictionary=promoted.animation_clips[0].duplicate(true);piece.id=str(i);piece.start=i;piece.length=1;piece.keys=dense.duplicate(true);bad.animation_clips.append(piece)
	check("2048" in Model.validate(bad,96),"loader bounds total independently owned source keys")
	bad=promoted.duplicate(true);bad.animation_clips=[]
	for i in range(33):
		var piece: Dictionary=promoted.animation_clips[0].duplicate(true);piece.id=str(i);piece.start=i;piece.length=1;bad.animation_clips.append(piece)
	check(not Model.validate(bad,96).is_empty(),"loader bounds the number of animation pieces")
	bad=promoted.duplicate(true);bad.erase("start_frame")
	check(not Model.validate(bad,96).is_empty(),"version2 requires an explicit introduction address even outside a world wrapper")
	rig.data=delay_split.data;rig.root=Node3D.new();rig.apply(15);var hidden: bool=not rig.root.visible;rig.apply(16)
	check(hidden and rig.root.visible,"standalone version2 application also honors first presence")
	rig.root.free();rig.root=null
	print("ANIMATION_CLIPS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)

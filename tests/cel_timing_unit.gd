extends SceneTree
const Timing=preload("res://src/cel_timing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var image:=Image.create(4,4,false,Image.FORMAT_RGBA8);image.fill(Color(.1,.4,.7,.5))
	var rows: Array=[{"id":"a","start":0,"duration":10,"image":image},{"id":"b","start":20,"duration":10,"image":image},{"id":"c","start":50,"duration":20,"image":image}]
	var before:=rows.duplicate(true);var pixels:=image.get_data()
	for start in [0,5,10,30,70,90]:
		var result:=Timing.proposal(rows,"a",start,100)
		check(not result.has("error") and result.before==0 and result.after==start and result.duration==10,"free same-layer move preserves length at "+str(start))
	for start in [-1,11,19,20,29,41,50,60,69,91,100,1.5,true,NAN]:check(Timing.proposal(rows,"a",start,100).has("error"),"overlap/out-of-range/nonwhole move refuses "+str(start))
	check(rows==before and image.get_data()==pixels and is_same(rows[0].image,image),"proposals mutate no metadata, allocate no new raster and preserve RGBA")
	check(not Timing.proposal(rows,"b",10,100).has("error") and not Timing.proposal(rows,"b",30,100).has("error"),"touching neighboring exposure boundaries is allowed")
	check(Timing.proposal(rows,"missing",10,100).has("error"),"missing stable cel identity refuses")
	for frames in [0,7201,12.5,true,NAN]:check(Timing.proposal(rows,"a",0,frames).has("error"),"invalid project duration refuses "+str(frames))
	var bad:=rows.duplicate(true);bad[1].id="a";check(Timing.proposal(bad,"a",30,100).has("error"),"duplicate cel identities refuse ambiguous edits")
	bad=rows.duplicate(true);bad.reverse();check(Timing.proposal(bad,"a",30,100).has("error"),"invalid unsorted source rows refuse")
	bad=rows.duplicate(true);bad[1].start=5;check(Timing.proposal(bad,"a",30,100).has("error"),"existing overlapping rows refuse without repair/data loss")
	var late: Array=[{"id":"late","start":3000,"duration":24,"image":image}]
	check(not Timing.proposal(late,"late",0,7200).has("error") and not Timing.proposal(late,"late",7176,7200).has("error"),"extended timeline moves preserve full exposure at both boundaries")
	print("CEL_TIMING_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

extends SceneTree
const Patch=preload("res://src/cel_patch.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var image:=Image.create(8,8,false,Image.FORMAT_RGBA8);image.fill(Color.CYAN)
	var source:={"id":"source","start":0,"duration":8,"image":image}
	var peer:={"id":"peer","start":8,"duration":2,"image":image.duplicate()}
	var before: Array=[source,peer];var after: Array=[source.duplicate(true),{"id":"right","start":4,"duration":4,"image":image.duplicate()},peer];after[0].duration=4
	var command:=Patch.create("layer","owner",before,after)
	check(command.before.size()==1 and command.after.size()==2 and not command.has("layer"),"delta drops unrelated peer and layer ownership")
	var undone:=Patch.apply(after,command,"before",48)
	check(not undone.has("error") and undone.cels.size()==2 and undone.cels[0].duration==8 and is_same(undone.cels[1],peer),"Undo restores target and preserves untouched peer dictionary")
	var redone:=Patch.apply(undone.cels,command,"after",48)
	check(not redone.has("error") and redone.cels.size()==3 and not is_same(redone.cels[0].image,redone.cels[1].image),"Redo reinstalls independent split halves")
	var normalized: Array=after.duplicate(true);normalized[0].start=0.0;normalized[0].duration=4.0;normalized[0].image=image.duplicate()
	check(not Patch.apply(normalized,command,"before",48).has("error"),"whole JSON numbers and rebuilt equal-pixel Images remain valid history targets")
	var stale: Array=after.duplicate(true);stale[0].duration=3;var saved:=stale.duplicate(true)
	check(Patch.apply(stale,command,"before",48).has("error") and stale==saved,"changed target refuses atomically")
	check(Patch.apply([after[0],peer],command,"before",48).has("error"),"missing target refuses")
	check(Patch.apply(after,command,"before",48,1).has("error"),"global budget allowance is enforced before restoring")
	check(Patch.apply(after,command,"invalid",48).has("error"),"invalid history direction refuses")
	var cut:=Patch.create("layer","owner",before,[peer]);var moved:=peer.duplicate(true);moved.start=2
	check(Patch.apply([moved],cut,"before",48).has("error") and moved.start==2,"new collision in restored slot refuses without overwriting unrelated peer")
	var solo:=Patch.create("layer","owner",[source],[]);var removed:=Patch.apply([source],solo,"after",48)
	check(not removed.has("error") and removed.cels.is_empty() and not Patch.apply([],solo,"before",48).has("error"),"empty-layer Cut/Undo remains supported")
	print("CEL_PATCH_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

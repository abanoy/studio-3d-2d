extends SceneTree
const Edits=preload("res://src/camera_key_edits.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var a:=Timeline.key(0,Vector3(1,2,3),Quaternion.IDENTITY,51.,"hold");a.near=.002;a.far=8000.;a["metadata"]={"notes":["original"]}
	var b:=Timeline.key(24,Vector3(4,5,6),Quaternion(Vector3.UP,.2),73.,"linear")
	var keys: Array=[a,b];var source: Array=keys.duplicate(true)
	check(Edits.error(keys,48).is_empty(),"ordinary authored camera range validates")
	var moved:=Edits.retime(keys,24,36,48)
	check(not moved.has("error") and moved.keys[1].frame==36,"retime changes the intended whole frame")
	var compare: Dictionary=moved.keys[1].duplicate(true);compare.frame=24
	check(compare==b and moved.keys[0]==a,"retime preserves every authored key property")
	check(keys==source,"pure planning never mutates the source")
	moved.keys[0].metadata.notes[0]="changed"
	check(keys[0].metadata.notes==["original"],"planned nested metadata is independent")
	check(Edits.retime(keys,24,24,48).changed==false,"same-frame release is a no-op")
	check(Edits.retime(keys,24,0,48).has("error"),"occupied target refuses without overwrite")
	check(Edits.retime(keys,9,12,48).has("error"),"missing source key refuses")
	check(Edits.retime(keys,24,12.5,48).has("error"),"fractional target refuses")
	check(Edits.retime(keys,24,-1,48).has("error") and Edits.retime(keys,24,49,48).has("error"),"target is inside the scene including end boundary")
	var legacy: Array=[a,Timeline.key(200,Vector3.ZERO,Quaternion.IDENTITY,60.)]
	check(Edits.error(legacy,48).is_empty() and Edits.retime(legacy,200,48,48).keys[-1].frame==48,"valid legacy off-scene keys remain editable")
	var captured:=Timeline.key(999,Vector3(6,7,8),Quaternion.IDENTITY,45.,"ease");captured.near=.04;captured.far=12000.
	var added:=Edits.toggle(keys,48,48,captured)
	check(added.keys.size()==3 and added.keys[-1].frame==48 and added.keys[-1].fov==45.,"double-click add accepts scene end boundary and current lens")
	check(added.keys[-1].near==.04 and added.keys[-1].far==12000. and captured.frame==999,"add preserves visibility range without mutating capture")
	var removed:=Edits.toggle(added.keys,24,48)
	check(removed.keys.size()==2 and removed.keys[0]==a and removed.keys[-1]==added.keys[-1],"remove changes only the selected key")
	check(Edits.toggle([a],0,48).error.contains("at least one"),"last camera key has a clear refusal")
	check(Edits.toggle(keys,12,48).has("error"),"adding without a valid capture refuses")
	var full: Array=[]
	for at in range(241):full.append(Timeline.key(at,Vector3.ZERO,Quaternion.IDENTITY,60.))
	check(Edits.toggle(full,241,300,Timeline.key(241,Vector3.ZERO,Quaternion.IDENTITY,60.)).has("error"),"241-key cap refuses growth")
	check(Edits.toggle(full,120,300).keys.size()==240,"full track still permits removal")
	var invalid: Array=source.duplicate(true);invalid[1].frame=0
	check(not Edits.error(invalid,48).is_empty(),"duplicate baseline frames refuse")
	invalid=source.duplicate(true);invalid.reverse()
	check(not Edits.error(invalid,48).is_empty(),"unsorted baseline frames refuse")
	invalid=source.duplicate(true);invalid[0].fov=NAN
	check(not Edits.error(invalid,48).is_empty(),"nonfinite lens refuses")
	invalid=source.duplicate(true);invalid[0].rotation_xyzw=[0,0,0,0]
	check(not Edits.error(invalid,48).is_empty(),"zero quaternion refuses")
	invalid=source.duplicate(true);invalid[0].far=.001
	check(not Edits.error(invalid,48).is_empty(),"invalid clipping range refuses")
	check(not Edits.error(keys,0).is_empty() and not Edits.error(keys,7201).is_empty(),"duration limits match the existing project limits")
	check(Edits.digest(keys)==Edits.digest(source) and Edits.digest(keys)!=Edits.digest(added.keys),"context digest binds exact key contents")
	check(keys==source and captured.frame==999,"all refused and successful plans preserve their inputs")
	print("CAMERA_KEY_EDITS_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

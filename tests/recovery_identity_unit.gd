extends SceneTree
const R=preload("res://src/recovery.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var pid:=OS.get_process_id();var key:=str(pid);var own:=R.owner_record()
	check(own.pid==pid and R.valid_creation(own.get("created_100ns")),"real Windows writer creation identity is available as an exact string")
	var observed:=R.process_info([pid]);check(observed.owners[key]=="alive" and observed.created_100ns[key]==own.created_100ns,"own process identity agrees with live inspection")
	var parent:=int(OS.get_cmdline_user_args()[1]);var foreign:=R.process_info([parent]);var other:={"pid":parent,"created_100ns":foreign.created_100ns.get(str(parent),"")}
	check(foreign.owners.get(str(parent))=="alive" and R.valid_creation(other.created_100ns) and other.created_100ns!=own.created_100ns,"separate real live parent has a distinct creation time")
	check(not R.owner_available(own,observed) and R.owner_available(own,observed,true),"exact current owner stays protected except explicit current-session history")
	check(not R.owner_available(other,foreign) and not R.owner_available(other,foreign,true),"matching unrelated live owner remains protected even with include-current")
	var reused:=own.duplicate();reused.created_100ns=other.created_100ns
	check(R.owner_available(reused,observed),"same PID with another actual process creation time is an expired incarnation")
	var legacy:={"pid":pid};check(not R.owner_available(legacy,observed) and R.owner_available(legacy,observed,true),"legacy current PID-only records retain old history behavior")
	var dead:={"owners":{key:"exited"},"created_100ns":{}}
	check(R.owner_available(own,dead) and R.owner_available(legacy,dead),"positive exited state permits identified and legacy records")
	var unknown:={"owners":{key:"unknown"},"created_100ns":{key:other.created_100ns}}
	R.discovery_warning="";check(not R.owner_available(own,unknown,true) and not R.discovery_warning.is_empty(),"unknown liveness cannot be bypassed by a mismatched identity")
	var no_identity:={"owners":{key:"alive"},"created_100ns":{}}
	R.discovery_warning="";check(not R.owner_available(own,no_identity,true) and not R.discovery_warning.is_empty(),"missing live creation query protects identified owners")
	for value in [null,0,"","0","01","+1","1.0","NaN","-1","18446744073709551616","1".repeat(21)]:check(not R.valid_creation(value),"invalid creation token refused: "+str(value))
	check(R.valid_creation("18446744073709551615") and R.valid_creation("1"),"unsigned64 creation tokens are preserved without floating conversion")
	var invalid:=own.duplicate();invalid.created_100ns=123
	check(not R.owner_available(invalid,dead),"malformed stored identity remains protected even with a stale PID")
	var base: String=OS.get_cmdline_user_args()[0];var scene:=base.path_join("room.glb");check(SceneIO.make_fixture(scene)==OK,"create original journal fixture")
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,55)]
	check(R.checkpoint(base,"owned",video,keys,[],scene,7,{},"original.has",1).is_empty(),"normal checkpoint writes identified owner without project schema changes")
	var folder:=base.path_join("owned");var before:=FileAccess.get_sha256(folder.path_join("project.json"));var saved:=R.read_json(folder.path_join("session.json"))
	check(int(saved.get("pid",0))==pid and saved.get("created_100ns")==own.created_100ns,"owner record contains the exact cached native creation string")
	check(R.candidates(base).is_empty() and not R.candidates(base,"",true).is_empty(),"real candidate discovery respects current ownership and explicit history")
	R.write_json(folder.path_join("session.json"),reused);check(not R.candidates(base).is_empty(),"normal candidate scan admits a simulated reused current PID with genuine different creation time")
	R.write_json(folder.path_join("session.json"),other);check(R.candidates(base).is_empty(),"normal scan protects exact identity of real live foreign parent")
	R.write_json(folder.path_join("session.json"),{"pid":parent});check(R.candidates(base).is_empty(),"legacy live foreign PID remains protected")
	R.write_json(folder.path_join("session.json"),invalid);R.discovery_warning="";check(R.candidates(base).is_empty() and not R.discovery_warning.is_empty(),"bad owner identity does not turn into an unowned recoverable session")
	R.write_json(folder.path_join("session.json"),{"pid":"bad"});check(R.candidates(base).is_empty(),"malformed PID stays protected")
	var broken:=FileAccess.open(folder.path_join("session.json"),FileAccess.WRITE);broken.store_string("{");broken.close();R.discovery_warning=""
	check(R.candidates(base).is_empty() and not R.discovery_warning.is_empty(),"present corrupt owner file is protected with a quiet warning")
	DirAccess.rename_absolute(folder.path_join("session.json"),folder.path_join("session.json.held"));check(not R.candidates(base).is_empty(),"missing sidecar preserves compatibility for older ownerless recovery folders");DirAccess.rename_absolute(folder.path_join("session.json.held"),folder.path_join("session.json"))
	check(FileAccess.get_sha256(folder.path_join("project.json"))==before,"ownership decisions never rewrite the saved scene")
	var snapshot:=R.owner_record();snapshot.created_100ns="1";check(R.owner_record()==own,"caller cannot poison cached own identity")
	print("RECOVERY_IDENTITY_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"owner":own}));quit(0 if failures==0 else 1)

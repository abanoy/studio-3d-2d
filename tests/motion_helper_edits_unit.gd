extends "res://tests/motion_assist_unit.gd"
func _initialize() -> void:
 var video:={"fps_num":24,"fps_den":1,"duration_frames":72};var main:=curve([0,12,24]);var saved:=main.duplicate(true);var base:=Assist.new();base.build(main,video);var edited:=Assist.new()
 var settings:={"helper_edits":{"segment-0-12-2":{"phase":.75,"amount":.5}}}
 check(edited.build(main,video,settings).is_empty(),"one helper accepts timing and amount adjustments")
 var target: Dictionary=edited.helper_keys()[1]
 check(target.id=="segment-0-12-2" and target.frame==9. and target.amount==.5 and target.editable,"edited helper exposes its regenerated phase and amount")
 check(edited.sample(9.)!=base.sample(9.),"helper adjustment changes evaluated motion")
 var exact:=true
 for key in main:exact=exact and edited.sample(key.frame)==key.value
 check(exact and main==saved and edited.main_keys()==saved,"adjustment never changes authored poses or controls")
 var peer_exact:=true;var forward:=[]
 for half in range(145):
  var frame:=float(half)/2.;forward.append(edited.sample(frame))
  if frame>=12:peer_exact=peer_exact and edited.sample(frame)==base.sample(frame)
 check(peer_exact,"other movement and settling spans remain exact")
 var reverse:=true;var bounded:=true;var off:=true
 for half in range(144,-1,-1):
  var frame:=float(half)/2.;reverse=reverse and edited.sample(frame)==forward[half]
  bounded=bounded and Assist.T.vector(edited.sample(frame).position).distance_to(Assist.T.vector(Assist.baseline(main,frame).position))<=.080001
  off=off and edited.sample(frame,0.)==Assist.baseline(main,frame)
 check(reverse and bounded and off,"edited motion remains bounded, seek-independent and reversible")
 var longer:=curve([0,12,24,36]);var reordered:=Assist.new();reordered.build(longer,video)
 check(reordered.helper_keys()[4].id==base.helper_keys()[4].id,"later additions keep existing segment identities")
 var shifted:=curve([12,24,36]);var previous:=Assist.new();previous.build(shifted,video)
 shifted.push_front({"frame":0,"value":value(-1.),"interpolation":"ease"})
 var extended:=Assist.new();extended.build(shifted,video)
 check(extended.helper_keys()[7]==previous.helper_keys()[4],"inserting an earlier pose preserves the untouched later helper identity and value")
 var old:=edited.fingerprint();var old_value:=edited.sample(9.)
 for bad in [{"segment-0-12-2":{"phase":.1,"amount":.5}},{"segment-0-12-2":{"phase":NAN,"amount":.5}},{"segment-0-12-2":{"phase":.75,"amount":1.1}},{"segment-0-12-2":{"phase":.75}},{"missing":{"phase":.5,"amount":.5}},{"settle-12-24-3":{"phase":.9,"amount":0.}}]:
  check(not edited.build(main,video,{"helper_edits":bad}).is_empty() and edited.fingerprint()==old and edited.sample(9.)==old_value,"invalid or stale adjustment refuses without replacing the plan")
 var simultaneous:={"helper_edits":{"segment-0-12-1":{"phase":.8,"amount":1.},"segment-0-12-2":{"phase":.9,"amount":1.}}}
 check(edited.build(main,video,simultaneous).is_empty(),"jointly moved helpers validate final ordering, not mutation order")
 var muted:=Assist.new();muted.build(main,video,{"helper_edits":{"segment-0-12-2":{"phase":.87,"amount":0.}}})
 check(muted.sample(10.44)==Assist.baseline(main,10.44),"zero amount removes this helper offset at its control")
 print("MOTION_HELPER_EDITS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

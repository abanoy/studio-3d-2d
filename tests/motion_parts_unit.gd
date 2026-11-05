extends SceneTree
const Motion=preload("res://src/motion_animation.gd")
const M=Motion.Body.Model
const D=preload("res://src/root_component_document.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1
 if not ok:failures+=1
 print(("PASS " if ok else "FAIL ")+label)
func value(x: float,root:=false) -> Dictionary:
 var v:=M.identity();v.position=[x,0,0]
 if root:v.scale=1.
 return v
func _initialize() -> void:
 var old:=M.definition("res://project.godot")
 for at in [0,12,24]:old.pose_keys.append({"frame":at,"pose":{"left":value(.3 if at==12 else 0.),"right":value(.2 if at==12 else 0.)},"transform":value(.1 if at==12 else 0.,true),"interpolation":"ease"})
 var base: Dictionary=Motion.configure(old,true,.65,48).data
 for source in [base,D.promote(base,48).data]:
  var before: Dictionary=source.duplicate(true);var original:=M.new();original.data=source
  var configured:=Motion.configure(source,true,.65,48,{"left":0.,"@root":0.});check(not configured.has("error") and configured.data.motion_assist.format==Motion.PART_SETTINGS,"versioned per-part settings accepted")
  var actor:=M.new();actor.data=configured.data;var exact:=true;var peers:=true
  for half in range(97):
   var at:=float(half)/2.;exact=exact and actor.sample(at).left==actor.sample_body(at).left and actor.sample_transform(at)==actor.sample_authored_transform(at)
   peers=peers and actor.sample(at).right==original.sample(at).right
  check(exact and peers,"disabled part and root exact; other part unchanged at97samples")
  check(source==before and actor.data.animation_clips==source.animation_clips,"authored data untouched")
  var adjusted:=Motion.configure(actor.data,true,.3,48);check(adjusted.data.motion_assist.part_strengths=={"left":0.,"@root":0.},"global changes preserve overrides")
  var cleared:=Motion.configure(actor.data,true,.65,48,{});check(cleared.data.motion_assist==base.motion_assist,"clearing overrides returns original version1 settings")
  var samples:=[]
  for half in range(97):samples.append(actor.sample(float(half)/2.))
  var reverse:=true
  for half in range(96,-1,-1):reverse=reverse and samples[half]==actor.sample(float(half)/2.)
  check(reverse,"reverse deterministic with per-part settings")
  var records: Dictionary=original.motion_plan().helper_keys()
  var edits := {}
  for part in ["left","@root"]:
   for helper in records[part]:
    if helper.kind=="overshoot":
     edits[part]={helper.id:{"phase":.75,"amount":.25}}
     break
  var tuned:=Motion.configure(source,true,.65,48,{},edits)
  check(edits.size()==2 and not tuned.has("error") and tuned.data.motion_assist.format==Motion.HELPER_SETTINGS,"combined root and bone adjustments promote to version3")
  if tuned.has("error"):continue
  var restored:=M.new();restored.data=JSON.parse_string(JSON.stringify(tuned.data,"",true,true))
  var plan: RefCounted=restored.motion_plan()
  check(plan!=null and restored.data.motion_assist.track_helper_edits==edits,"serialized settings recompile both edited tracks")
  if plan==null:continue
  check(restored.sample(9.).left!=original.sample(9.).left and restored.sample_transform(9.)!=original.sample_transform(9.) and restored.sample(9.).right==original.sample(9.).right,"restored edits affect only selected bone and root")
  var muted:=Motion.configure(tuned.data,true,.65,48,{"left":0.})
  restored.data=muted.data
  check(restored.motion_plan()!=null and restored.sample(9.).left==restored.sample_body(9.).left and restored.data.motion_assist.track_helper_edits==edits,"muting a part preserves its adjustments")
  check(Motion.configure(tuned.data,true,.65,48,{},{}).data.motion_assist==base.motion_assist,"removing last helper edit restores version1")
  var deletion:=M.new();deletion.data=tuned.data.duplicate(true)
  check(deletion.remove_pose_key(12,48,"left").is_empty() and deletion.motion_plan()!=null and deletion.data.motion_assist.track_helper_edits=={"@root":edits["@root"]},"removing a bone driver preserves the root adjustment")
  deletion.data=tuned.data.duplicate(true)
  check(deletion.remove_pose_key(24,48,"left").is_empty() and deletion.motion_plan()!=null and deletion.data.motion_assist.track_helper_edits==edits,"removing a different key preserves the tuned span")
  var split_tuned:=D.edit_clip(tuned.data,"split","",8,48) if source.format==D.FORMAT else M.Clips.split(tuned.data,8)
  var sliced:=M.new();sliced.data=split_tuned.data
  var whole:=M.new();whole.data=tuned.data
  var identical: bool=sliced.motion_plan()!=null
  for half in range(97):
   var at:=float(half)/2.
   identical=identical and sliced.sample(at)==whole.sample(at) and sliced.sample_transform(at)==whole.sample_transform(at)
  check(identical,"splitting through tuned bone and root movements preserves97 samples exactly")
  var only: String=tuned.data.animation_clips[0].id
  var empty:=D.edit_clip(tuned.data,"remove",only,0,48) if source.format==D.FORMAT else M.Clips.remove(tuned.data,only,48)
  check(not empty.has("error") and empty.data.motion_assist==base.motion_assist,"deleting the only tuned clip restores ordinary motion settings")
  if source.format==Motion.FORMAT:
   var prior: Dictionary=tuned.data.duplicate(true)
   var migrated:=D.promote(tuned.data,48)
   check(not migrated.has("error") and tuned.data==prior,"separating movement tracks preserves the original tuned model")
   if not migrated.has("error"):
    var moved:=M.new();moved.data=migrated.data
    var identity: String=edits["@root"].keys()[0]
    var preserved: bool=moved.motion_plan()!=null and migrated.data.motion_assist.track_helper_edits["@root"]=={"position/"+identity:edits["@root"][identity]}
    for half in range(97):
     var frame:=float(half)/2.
     var previous:=M.new();previous.data=prior
     preserved=preserved and moved.sample_transform(frame)==previous.sample_transform(frame)
    check(preserved,"position-only helper follows its component with exact motion at97 samples")
   var gap_data: Dictionary=prior.duplicate(true)
   gap_data.motion_assist.track_helper_edits["@root"]={"gap/unknown/segment-1-8-2":{"phase":.75,"amount":.25}}
   check(D.promote(gap_data,48).has("error"),"unresolved migration refuses before creating unusable root tracks")
   var split:=M.Clips.split(base,8)
   var moved_clip:=M.Clips.move(split.data,split.right_id,20,48)
   var gap_actor:=M.new();gap_actor.data=moved_clip.data
   var gap_id:=""
   for item in gap_actor.motion_plan().helper_keys()["@root"]:
    if item.get("connection",false) and item.kind=="overshoot":gap_id=item.id;break
   check(not gap_id.is_empty(),"split and moved root clip generates an addressable connecting overshoot")
   var tuned_gap:=Motion.configure(moved_clip.data,true,.65,48,{},{"@root":{gap_id:{"phase":.75,"amount":.25}}})
   gap_actor.data=tuned_gap.data
   var converted:=D.promote(tuned_gap.data,48)
   check(not converted.has("error"),"tuned gap promotes to independent tracks")
   if not converted.has("error"):
    var comparison:=M.new();comparison.data=converted.data
    var matches: bool=comparison.motion_plan()!=null and comparison.data.motion_assist.track_helper_edits["@root"].has("position/"+gap_id)
    for half in range(97):
     var frame:=float(half)/2.
     matches=matches and comparison.sample_transform(frame)==gap_actor.sample_transform(frame)
    check(matches,"tuned gap and neighboring source slices reproduce all97 samples after promotion")
 for invalid in [{"left":NAN},{"left":-1.},{"left":2.},{"":.5}]:check(Motion.configure(base,true,.65,48,invalid).has("error"),"invalid override refuses")
 print("MOTION_PARTS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

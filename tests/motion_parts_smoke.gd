extends "res://tests/motion_assist_native.gd"
const Motion=preload("res://src/motion_animation.gd")
const D=preload("res://src/root_component_document.gd")
var second_snapshot: Dictionary={}
func wait_job() -> void:
 while app.has_project.pid>0:await process_frame
 await settled()
func run() -> void:
 var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1]);await wait_job()
 var actor: RefCounted=app.renderer.world_runtime.instances.values()[0];var object_id: String=actor.data.id;app.world_selection.select_entity(object_id);var head:=""
 for id in actor.order:
  if actor.bones[id].name=="頭":head=id
 check(not head.is_empty(),"native head resolves")
 for components in [false,true]:
  if components:check(app.pose_editor.restore_state(D.promote(actor.data,48).data).is_empty(),"independent movement model installs")
  actor=app.renderer.world_runtime.instance(object_id);app.world_selection.select_entity(object_id);app.set_frame(18);app.set_advanced(true);var ui=app.pose_editor.motion;var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();ui.open()
  check(ui.part_panel.visible and head in ui.part_ids,"Advanced exposes native animated parts")
  ui.part_choice.select(ui.part_ids.find(head));ui.part_choice.item_selected.emit(ui.part_choice.selected);ui.part_override.button_pressed=true;ui.part_strength.value=0.;ui.apply();await settled()
  check(actor.data.motion_assist.get("part_strengths",{}).get(head,-1)==0. and app.history.size()==history+1,"one Apply stores separate amount with one Undo")
  check(actor.sample(18).get(head)==actor.sample_body(18).get(head) and actor.data.animation_clips==before.animation_clips,"head assistance disabled without changing main keys")
  var saved: Dictionary=actor.data.duplicate(true);app.undo();check(actor.data==before,"Undo restores exact model");app.redo();check(actor.data==saved,"Redo restores exact override")
  app.set_advanced(false);ui.open();check(not ui.part_panel.visible and not ui.helpers.visible,"Simple hides detailed controls")
  ui.strength.value=.45;ui.apply();check(actor.data.motion_assist.part_strengths[head]==0.,"Simple global adjustment retains advanced choice")
  ui.open();ui.enabled.button_pressed=false;ui.apply();check(not actor.motion_enabled(),"Off works for current model version");app.undo();check(actor.motion_enabled(),"Undo Off restores enabled assistance")
  # Return to inherited strength so next variant starts without a duplicate no-op.
  if not components:
   app.set_advanced(true);ui.open();ui.part_choice.select(ui.part_ids.find(head));ui.refresh_part();ui.part_override.button_pressed=false;ui.apply();check(not actor.data.motion_assist.has("part_strengths"),"clearing last override restores version1 settings")
 app.set_advanced(true)
 var editor=app.pose_editor.motion
 editor.open()
 var item: TreeItem=editor.helpers.get_root().get_first_child()
 while item:
  var record: Dictionary=item.get_metadata(0)
  if record.helper.kind=="overshoot" and record.helper.get("editable",false):break
  item=item.get_next()
 check(item!=null,"native model exposes an editable overshoot")
 if item:
  item.select(0);editor.refresh_helper()
  editor.helper_phase.value=.75;editor.helper_amount.value=.30
  var prior: Dictionary=actor.data.duplicate(true)
  editor.apply();await settled()
  check(actor.data.motion_assist.format==Motion.HELPER_SETTINGS and actor.data.animation_clips==prior.animation_clips,"Advanced helper Apply stores the adjustment and preserves authored poses")
  var tuned: Dictionary=actor.data.duplicate(true)
  app.undo();check(actor.data==prior,"Undo restores the automatic helper")
  app.redo();check(actor.data==tuned,"Redo restores the tuned helper")
  editor.open();editor.enabled.button_pressed=false;editor.apply()
  var dormant: Dictionary=actor.data.duplicate(true)
  editor.open()
  var inactive: TreeItem=editor.helpers.get_root().get_first_child()
  check(inactive!=null and inactive.get_metadata(0).get("saved_only",false),"Advanced lists saved adjustments while assistance is off")
  if inactive:
   inactive.select(0);editor.refresh_helper();editor.reset_helper()
   check(editor.draft_helpers.is_empty() and actor.data==dormant,"reset stages only the selected adjustment")
   editor.window.hide();editor.open();inactive=editor.helpers.get_root().get_first_child()
   check(inactive!=null and editor.draft_helpers==dormant.motion_assist.track_helper_edits,"cancel preserves the saved adjustment")
   inactive.select(0);editor.refresh_helper();editor.reset_helper();editor.apply()
   check(not actor.data.motion_assist.has("track_helper_edits"),"Apply removes the dormant adjustment")
   app.undo();check(actor.data==dormant,"Undo restores the dormant adjustment")
  app.undo();check(actor.data==tuned,"restoring assistance reactivates the exact tuned model")
  var part: String=tuned.motion_assist.track_helper_edits.keys()[0]
  app.set_frame(24);app.pose_editor.selected=part;app.pose_editor.delete_key()
  check(not actor.data.motion_assist.has("track_helper_edits") and actor.motion_plan()!=null and actor.data.animation_clips!=tuned.animation_clips,"deleting the driving arm key removes its adjustment and regenerates the remaining motion")
  app.undo();check(actor.data==tuned,"one Undo restores the driving pose and its helper adjustment")
  var original_samples: Array=[]
  for half in range(97):
   var at:=float(half)/2.
   original_samples.append([actor.sample(at),actor.sample_transform(at)])
  app.clip_editor.request("split",object_id,tuned.animation_clips[0].id,12)
  var split_state: Dictionary=actor.data.duplicate(true)
  var exact: bool=split_state.animation_clips.size()==tuned.animation_clips.size()+1
  for half in range(97):
   var at:=float(half)/2.
   exact=exact and [actor.sample(at),actor.sample_transform(at)]==original_samples[half]
  check(exact,"timeline split preserves the tuned performance at97 samples")
  app.undo();check(actor.data==tuned,"Undo reassembles the tuned clip")
  app.redo();check(actor.data==split_state,"Redo restores the independently owned tuned slices")
  var removed_id: String=split_state.animation_clips[1].id
  app.clip_editor.request("delete",object_id,removed_id,12)
  var kept: Dictionary=actor.data.motion_assist.track_helper_edits[part]
  check(actor.motion_plan()!=null and actor.data.animation_clips.size()==split_state.animation_clips.size()-1 and Motion.Body.Model.Clips.index_id(actor.data,removed_id)<0 and kept==tuned.motion_assist.track_helper_edits[part],"deleting the right slice preserves the left slice's tuned helper")
  app.undo();check(actor.data==split_state,"Undo restores the deleted slice and its adjustments")
  app.clip_editor.request("copy",object_id,removed_id,12)
  app.clip_editor.request("delete",object_id,removed_id,12)
  app.clip_editor.request("paste",object_id,"",12)
  var pasted_id: String=actor.data.animation_clips[Motion.Body.Model.Clips.index_at(actor.data,12)].id
  var pasted_state: Dictionary=actor.data.duplicate(true)
  var reproduced:=pasted_id!=removed_id and actor.motion_plan()!=null
  for half in range(97):
   var at:=float(half)/2.
   reproduced=reproduced and [actor.sample(at),actor.sample_transform(at)]==original_samples[half]
  check(reproduced,"pasted slice reproduces all97 samples with a new clip identity")
  app.clip_editor.request("delete",object_id,tuned.animation_clips[0].id,0)
  var independent: Dictionary=actor.data.motion_assist.get("track_helper_edits",{}).get(part,{})
  check(independent.size()==1 and independent.keys()[0].begins_with(pasted_id+"/") and actor.motion_plan()!=null,"pasted tuning survives removal of the original clip")
  app.undo();check(actor.data==pasted_state,"Undo restores the original beside the pasted clip")
  var source_before: Dictionary=actor.data.duplicate(true)
  var added: String=app.pose_editor.add_model(actor.data.source)
  var second: RefCounted=app.renderer.active_model()
  check(added.is_empty() and second!=null and second.data.id!=object_id,"a second instance of the same native character loads")
  if second and second.data.id!=object_id:
   var second_id: String=second.data.id
   app.physics_editor.freeze_all()
   app.clip_editor.request("paste",second_id,"",12)
   check(second.data.get("motion_assist",{}).get("format")==Motion.HELPER_SETTINGS and not second.motion_enabled(),"foreign paste stores tuning while preserving the new character's assistance-off state")
   check("Turn on Motion feeling" in app.status.text,"paste explains how to activate dormant adjustments")
   if second.data.has("motion_assist"):
    var second_settings:=Motion.configure(second.data,true,tuned.motion_assist.strength,48)
    var restored: String=app.pose_editor.restore_state(second_settings.data)
    var same:=restored.is_empty() and second.motion_plan()!=null
    var copied_length: int=app.clip_editor.clipboard.piece.length
    actor=app.renderer.world_runtime.instance(object_id)
    for half in range(copied_length*2):
     var at:=12.+float(half)/2.
     same=same and second.sample(at).get(part)==actor.sample(at).get(part)
    check(same and actor.data==source_before,"enabling the destination reproduces the tuned arm through the pasted slice and preserves the source model")
   var placement: Dictionary=D.put_component(second.data,18,"position",[1.2,0.,0.],"ease",48)
   check(not placement.has("error") and app.pose_editor.restore_state(placement.data).is_empty(),"second character has its own position on the shared stage")
   second_snapshot={"id":second_id,"settings":second.data.motion_assist.duplicate(true),"samples":[]}
   for half in range(97):
    var at:=float(half)/2.
    second_snapshot.samples.append(sampled_motion_hash(second,at))
   actor=app.renderer.world_runtime.instance(object_id);app.world_selection.select_entity(object_id)
 app.set_frame(18);var expected: Dictionary=actor.data.motion_assist.duplicate(true);var expected_poses:=[]
 var before_sound: int=app.history.size()
 app.choose_audio_at_playhead();await settled()
 var sound_picker: FileDialog
 for child in app.get_children():
  if child is FileDialog and child.visible:sound_picker=child
 check(sound_picker!=null and "frame 18" in sound_picker.title,"Add audio identifies the chosen playhead frame")
 app.set_frame(22)
 if sound_picker:sound_picker.file_selected.emit(folder.path_join("arm-cue.wav"))
 await settled();app.set_frame(18)
 check(app.audio_clips.size()==1 and app.audio_clip.start_frame==18 and app.history.size()==before_sound+1,"sound cue placed at the requested frame in a single edit even after seeking")
 second_snapshot["cue_pcm"]=app.audio_mix.pcm.hex_encode().sha256_text()
 second_snapshot["cue_source"]=app.audio_clip.source.sha256
 for half in range(97):expected_poses.append(JSON.stringify({"pose":actor.sample(float(half)/2.),"root":actor.sample_transform(float(half)/2.)},"",true,true).sha256_text())
 var image: Image=await app.renderer.capture(app.keys,app.layers,18,true);image.save_png(folder.path_join("before.png"));var path:=folder.path_join("part-motion.has");app.has_project.save_file(path,"packed");await wait_job();app.new_project();app.has_project.open_file(path);await wait_job();actor=app.renderer.world_runtime.instance(object_id)
 check(actor.data.motion_assist==expected,"packed Open retains per-part settings")
 var companion: RefCounted=app.renderer.world_runtime.instance(second_snapshot.id)
 check(companion!=null and companion!=actor and companion.data.motion_assist==second_snapshot.settings,"packed Open restores the second adjusted character independently")
 var evidence:=FileAccess.open(folder.path_join("second.json"),FileAccess.WRITE)
 evidence.store_string(JSON.stringify(second_snapshot,"",true,true));evidence.close()
 var after: Image=await app.renderer.capture(app.keys,app.layers,18,true);check(after.get_data()==image.get_data(),"reopened preview matches exactly")
 var error: String=await app.export_movie(folder);check(error.is_empty(),"ordinary movie export")
 if error.is_empty():check(Image.load_from_file(app.last_export_folder.path_join("frame_000019.png")).get_data()==image.get_data(),"movie source frame matches preview")
 var result:={"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"expected_settings":expected,"pose_hashes":expected_poses,"object_id":object_id,"head_id":head,"source_sha":FileAccess.get_sha256(actor.data.source)};var f:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();app.dirty=false;app.free();await settled();print("MOTION_PARTS_APP "+JSON.stringify(result));quit(0 if failures==0 else 1)

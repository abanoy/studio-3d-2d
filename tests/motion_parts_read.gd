extends "res://tests/motion_assist_native.gd"
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("result.json")));app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("cold-recovery");root.add_child(app);app.has_project.cache_root=folder.path_join("cold-cache");app.autosave_enabled.button_pressed=false;await settled()
 while app.has_project.pid>0:await process_frame
 await settled();var actor: RefCounted=app.renderer.world_runtime.instance(expected.object_id)
 check(actor!=null and actor.motion_enabled() and actor.data.motion_assist==expected.expected_settings,"cold Open restores exact source character settings")
 var reference: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("second.json")))
 check(app.audio_clips.size()==1 and app.audio_clips[0].start_frame==18 and app.audio_clips[0].source.sha256==reference.cue_source and app.audio_mix.pcm.hex_encode().sha256_text()==reference.cue_pcm,"packed sound restores at frame18 with identical preview audio")
 var second: RefCounted=app.renderer.world_runtime.instance(reference.id)
 check(second!=null and second!=actor and second.data.motion_assist==reference.settings,"cold Open restores separate identity and helper settings for the second character")
 if second:
  var matched:=true
  for half in range(96,-1,-1):
   var at:=float(half)/2.
   matched=matched and sampled_motion_hash(second,at)==reference.samples[half]
  check(matched,"second character reproduces all97 saved pose and movement samples")
 if actor:
  var exact:=true
  for half in range(96,-1,-1):exact=exact and JSON.stringify({"pose":actor.sample(float(half)/2.),"root":actor.sample_transform(float(half)/2.)},"",true,true).sha256_text()==expected.pose_hashes[half]
  check(exact,"cold regenerated motion matches97 reverse samples")
  check(FileAccess.get_sha256(actor.data.source)==expected.source_sha,"cold cache preserves exact native standard asset")
  app.world_selection.select_entity(expected.object_id);app.set_frame(18);app.set_advanced(true);var ui=app.pose_editor.motion;ui.open();ui.part_choice.select(ui.part_ids.find(expected.head_id));ui.refresh_part()
  check(ui.part_panel.visible and ui.part_override.button_pressed and ui.part_strength.value==0.,"cold Advanced controls display saved head override")
  ui.window.hide();var image: Image=await app.renderer.capture(app.keys,app.layers,18,true);image.save_png(folder.path_join("cold.png"));check(image.get_data()==Image.load_from_file(folder.path_join("before.png")).get_data(),"cold render exactly matches saved frame")
  check(preload("res://src/drawing.gd").cel_at(app.layers[1],18).image.get_pixel(80,70)==Color.CYAN,"cold Open retains editable independent ink")
 var result:={"checks":checks,"failures":failures};var file:=FileAccess.open(folder.path_join("reader.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.dirty=false;app.free();await settled();print("MOTION_PARTS_READ "+JSON.stringify(result));quit(0 if failures==0 else 1)

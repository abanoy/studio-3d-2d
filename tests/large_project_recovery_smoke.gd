extends "res://tests/large_project_smoke.gd"
func _initialize() -> void:
 create_timer(800).timeout.connect(func():push_error("Large project persistence watchdog");quit(2));call_deferred("run")
func run() -> void:
 var args:=OS.get_cmdline_user_args();folder=args[0];var reading: bool="--read" in args
 app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if reading else "recovery");app.recent_path=folder.path_join("reader-recents.json" if reading else "recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
 if reading:
  var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("large.has"));await wait_job()
  check(app.has_project.path==folder.path_join("large.has") and total()==400 and hashes()==expected.pixels,"fresh ordinary packed Open restores all400exact editable drawings")
  var ids:={}
  for layer in app.layers:
   for cel in layer.cels:ids[Drawing.raster_token(cel)[0]]=true
  check(ids.size()==400 and app.raster_budget.sample().accounted_bytes<=app.raster_budget.sample().owner_limit_bytes,"fresh400drawing identities remain independent within admitted storage")
  app.set_frame(37);await settled();check(app.canvas.overlay.get_image().get_data()==Image.load_from_file(folder.path_join("expected-overlay.png")).get_data(),"fresh dense GPU overlay equals original exact preview")
  var picture: Image=await app.renderer.capture(app.keys,app.layers,37,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-final.png")).get_data(),"fresh dense final picture equals original exact movie input")
  check(Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"fresh dense project keeps independently aligned audio PCM")
  print("LARGE_PROJECT_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
 var input_sha:=FileAccess.get_sha256(args[1]);app.has_project.open_file(args[1]);await wait_job();check(app.has_project.path==args[1] and total()==400,"ordinary packed400drawing project opens before media/crash workflow")
 if total()!=400:await app.quit_studio();quit(1);return
 check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"dense scene receives independent audio at frame24")
 app.mode.select(0);app.change_mode(0);app.set_frame(37);await settled();app.canvas.overlay.get_image().save_png(folder.path_join("expected-overlay.png"));var picture: Image=await app.renderer.capture(app.keys,app.layers,37,true);picture.save_png(folder.path_join("expected-final.png"));picture=null
 app.has_project.save_file(folder.path_join("large.has"),"packed");await wait_job();check(app.has_project.path==folder.path_join("large.has") and FileAccess.file_exists(folder.path_join("large.has")),"self-contained400drawing/audio HAS actually commits")
 var manual:=FileAccess.get_sha256(folder.path_join("large.has"));var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
 check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000038.png")).get_data()==Image.load_from_file(folder.path_join("expected-final.png")).get_data(),"101frame dense MP4 input matches exact original frame37")
 app.set_frame(37);app.changed();app.autosave_tick(true)
 while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
 var checkpoint: String=app.recovery_root.path_join(app.recovery_session);check(Storage.readable_manifest(checkpoint.path_join("project.json")),"ordinary dense recovery checkpoint commits a readable manifest")
 check(FileAccess.get_sha256(folder.path_join("large.has"))==manual and FileAccess.get_sha256(args[1])==input_sha,"dense checkpoint/export preserve both explicit HAS files")
 var expected:={"pixels":hashes(),"pcm":Storage.RasterReader.digest_bytes(app.audio_mix.pcm),"manual_sha":manual,"movie":movie,"checkpoint":checkpoint,"frame":37,"duration_frames":101,"memory":app.raster_budget.sample(),"checks":checks,"failures":failures}
 var serialized:=JSON.stringify(expected);var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(serialized);file.flush();file.close();check(FileAccess.get_file_as_string(folder.path_join("expected.json"))==serialized,"crash oracle is closed and readable before intentional termination")
 print("LARGE_PROJECT_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));OS.kill(OS.get_process_id());await create_timer(2).timeout;push_error("Large project kill returned");quit(3)

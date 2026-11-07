extends "res://tests/movement_path_smoke.gd"
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Track=preload("res://src/visibility_track.gd")
func _initialize() -> void:
 create_timer(360).timeout.connect(func():push_error("Scenario C watchdog");quit(2));call_deferred("run")
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func room(path: String,color: Color) -> Error:
 var node:=Node3D.new();node.name="OriginalScenarioRoom";SceneIO.box(node,"Floor",Vector3(0,-.15,-2),Vector3(12,.3,14),Color(.25,.25,.3));SceneIO.box(node,"ColoredBack",Vector3(0,2,-6),Vector3(12,4,.25),color)
 var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
 if error==OK:error=doc.write_to_filesystem(state,path)
 node.free();return error
func named_button(text: String) -> Button:
 for node in app.find_children("*","Button",true,false):
  if node.text==text:return node
 return null
func reveal(control: Control) -> void:
 await settled();app.inspector_scroll.ensure_control_visible(control);await settled()
func context(at: int,row: int) -> void:
 var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_RIGHT;event.pressed=true;event.position=Vector2(app.timeline.x(at),app.timeline.row_y(row)+12);app.timeline._gui_input(event);await settled()
func green(image: Image) -> int:
 var bytes:=image.get_data();var count:=0
 for i in range(0,bytes.size(),4):
  if bytes[i+1]>180 and bytes[i]<80 and bytes[i+2]<100:count+=1
 return count
func energy(a: Image,b: Image) -> int:
 var aa:=a.get_data();var bb:=b.get_data();var result:=0
 for i in range(0,aa.size(),4):
  for c in range(3):result+=absi(int(aa[i+c])-int(bb[i+c]))
 return result
func run() -> void:
 var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if "--read" in args else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
 if "--read" in args:
  var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("scenario-c.has"));await wait_job()
  check(app.has_project.path==folder.path_join("scenario-c.has") and canonical(World.portable(app.current_world()))==expected.world,"fresh packed Open restores exact complete scenario world and source-relative animation")
  check(canonical(app.keys)==expected.keys and app.video.visibility_fade_ms==0 and app.video.duration_frames==128,"fresh scenario retains camera cuts, zero fade and scene length")
  check(Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==expected.paint and Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"fresh scenario retains independent editable paint and timed sound")
  var rig: RefCounted=app.renderer.world_runtime.instance(expected.id);app.set_frame(100);check(not rig.root.visible and not rig.visible_at(100),"fresh later animation clip still cannot re-enable persistent OFF")
  for at in [120,121]:
   var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);check(picture.get_data()==Image.load_from_file(folder.path_join("cut-%d.png"%at)).get_data(),"fresh final camera cut reproduces exact pixels at"+str(at))
  print("SCENARIO_C_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
 var sources:={};var first:=folder.path_join("room-a.glb");var second:=folder.path_join("room-b.glb");var actor:=folder.path_join("actor.glb")
 check(room(first,Color(.8,.15,.12))==OK and room(second,Color(.12,.2,.8))==OK and SceneIO.make_pose_fixture(actor)==OK,"original two-set and articulated actor fixtures are generated locally")
 for path in [first,second,actor]:sources[path]=FileAccess.get_sha256(path)
 app.show_project_options();await settled();app.project_timing.duration.value=128
 var apply_length:=named_button("Apply scene length")
 for scroll in app.project_options.find_children("*","ScrollContainer",true,false):
  if scroll.is_ancestor_of(apply_length):scroll.ensure_control_visible(apply_length)
 await settled();await click(apply_length);app.project_options.hide()
 check(app.video.duration_frames==128 and app.video.visibility_fade_ms==300 and not app.advanced_mode,"Simple Options sets128frames while preserving default300ms fade")
 check(app.load_scene(first).is_empty() and app.load_scene(second).is_empty(),"two independent sets coexist in the same world")
 var second_id: String=app.last_import_id;var editor=app.pose_editor;app.world_selection.select_entity(second_id);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=30;editor.apply_numeric();app.keys=[Timeline.key(0,Vector3(0,1.6,5),Quaternion.IDENTITY,60)]
 await context(100,0);check(app.timeline.import_menu.visible and app.timeline.import_frame==100,"C1 timeline context captures exact import frame100")
 app.timeline.import_menu.id_pressed.emit(0);await settled();var picker: FileDialog
 for child in app.get_children():
  if child is FileDialog and child.visible:picker=child;break
 check(picker!=null and app.frame==100,"C1 timeline import opens actual picker at chosen playhead")
 if picker==null:await app.quit_studio();quit(1);return
 picker.file_selected.emit(actor);await settled();var id: String=app.last_import_id;var rig: RefCounted=app.renderer.world_runtime.instance(id)
 if app.physics_editor.is_running():app.physics_editor.toggle.button_pressed=false;await settled()
 var absent:=true
 for at in range(100):
  app.renderer.world_runtime.evaluate(at);absent=absent and not rig.root.visible
 app.set_frame(100);check(rig.data.start_frame==100 and absent and rig.root.visible,"C1 imported actor is absent at every frame0through99 and visible at100")
 app.mode.select(2);app.change_mode(2)
 for at in [100,112,124]:
  app.set_frame(at);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[0].value=float(at-112)/12;editor.apply_numeric()
 for at in [112,124]:
  app.set_frame(at);editor.selected=rig.order[1];editor.operation.select(0);editor.refresh_values();editor.fields[2].value=30 if at==112 else 60;editor.apply_numeric()
 var prior: Dictionary=rig.data.duplicate(true);var samples: Array=[]
 for at in range(25):samples.append({"root":rig.sample_transform(100+at),"body":rig.sample(100+at)})
 var row: int=app.timeline.object_rows.find_custom(func(item):return item.id==id);var history: int=app.history.size();await drag(app.timeline,Vector2(app.timeline.x(106),app.timeline.row_y(row)+12),Vector2(app.timeline.x(6)-app.timeline.x(106),0))
 var exact:=true
 for at in range(25):exact=exact and rig.sample_transform(at)==samples[at].root and rig.sample(at)==samples[at].body
 check(rig.data.start_frame==0 and rig.data.animation_clips[0].start==0 and exact and app.history.size()==history+1,"C2 real block drag carries all25relative root/bone samples from100to0 in one Undo")
 var moved: Dictionary=rig.data.duplicate(true);app.undo();check(rig.data==prior,"C2 Undo restores original late presence and motion");app.redo();check(rig.data==moved,"C2 Redo restores exact relative move")
 await context(12,row);app.timeline.import_menu.id_pressed.emit(10);await settled();check(rig.data.animation_clips.size()==2,"C3 actual context Split keeps two editable animation pieces")
 await drag(app.timeline,Vector2(app.timeline.x(16),app.timeline.row_y(row)+12),Vector2(app.timeline.x(104)-app.timeline.x(16),0))
 app.set_frame(50);var a:=Timeline.vector(rig.sample_transform(11).position);var b:=Timeline.vector(rig.sample_transform(100).position);var middle:=Timeline.vector(rig.sample_transform(50).position)
 check(rig.root.visible and rig.data.animation_clips[1].start==100 and middle.x>=minf(a.x,b.x)-.00001 and middle.x<=maxf(a.x,b.x)+.00001,"C3 separated pieces keep existing actor visible with a predictable bounded gap bridge")
 app.set_frame(10);app.world_selection.select_entity(id);await reveal(editor.visible_toggle);await click(editor.visible_toggle)
 app.set_frame(100);check(not rig.root.visible and not rig.visible_at(100) and rig.data.visibility_keys==[{"frame":10,"visible":false}],"C4 Simple visibility OFF at10 persists at100 despite later animation piece")
 app.world_selection.clear();await settled();var hidden: Image=await app.renderer.capture(app.keys,app.layers,100,true);var before_green:=green(root.get_texture().get_image());var data: Dictionary=rig.data.duplicate(true);app.world_selection.items[id].select(0);await settled();var after_green:=green(root.get_texture().get_image());var selected: Image=await app.renderer.capture(app.keys,app.layers,100,true)
 check(app.world_selection.selected==id and not rig.root.visible and rig.data==data and app.world_selection.outline_material.get_shader_parameter("ghost") and after_green>before_green+10 and selected.get_data()==hidden.get_data(),"C5 hidden tree selection shows actual editor green ghost without changing visibility or final pixels")
 root.get_texture().get_image().save_png(folder.path_join("hidden-selected.png"))
 var fade_visible: Image=await app.renderer.capture(app.keys,app.layers,9,true);var fade_partial: Image=await app.renderer.capture(app.keys,app.layers,14,true);var fade_hidden: Image=await app.renderer.capture(app.keys,app.layers,20,true)
 check(Track.opacity(rig.data,14,app.video)>0 and Track.opacity(rig.data,14,app.video)<1 and energy(fade_partial,fade_hidden)>0 and energy(fade_partial,fade_hidden)<energy(fade_visible,fade_hidden),"C6 default300ms transition has actual intermediate fade pixels")
 app.show_project_options();await settled();app.visibility_fade.value=0;app.project_options.hide();app.set_frame(10);var cut_hidden: Image=await app.renderer.capture(app.keys,app.layers,10,true)
 check(app.video.visibility_fade_ms==0 and not rig.root.visible and cut_hidden.get_data()==fade_hidden.get_data(),"C6 zero project fade makes visibility OFF instantaneous with no added VFX clip")
 app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.fill_rect(Rect2i(80,80,70,12),Color.CYAN);Drawing.touch(Drawing.image(app.layers[1].cels[0]));app.changed();await settled();check(app.canvas.overlay.get_image().get_pixel(80,80)==Color.CYAN,"actual GPU drawing overlay shows the independent source marker");check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"independent RGBA drawing and sound join the same scenario timeline")
 app.mode.select(1);app.change_mode(1)
 for at in [120,121]:
  app.set_frame(at);app.renderer.camera.position=Vector3(0 if at==120 else 30,2,7);app.renderer.camera.quaternion=Quaternion.IDENTITY;app.renderer.camera.fov=60;var save_key:=named_button("Save camera key [K]");await reveal(save_key)
  check(app.inspector_scroll.get_global_rect().encloses(save_key.get_global_rect()),"C7 camera key control is fully visible after mode layout settles")
  root.get_texture().get_image().save_png(folder.path_join("camera-before-%d.png"%at));await click(save_key)
  check(app.keys.any(func(key):return key.frame==at),"C7 actual button stores the exact camera key at"+str(at))
 var left: Image=await app.renderer.capture(app.keys,app.layers,120,true);var right: Image=await app.renderer.capture(app.keys,app.layers,121,true);left.save_png(folder.path_join("cut-120.png"));right.save_png(folder.path_join("cut-121.png"))
 app.mode.select(0);app.change_mode(0);app.set_frame(120);var p0: Vector3=app.renderer.camera.position;app.set_frame(121);var p1: Vector3=app.renderer.camera.position
 check(p0==Vector3(0,2,7) and p1==Vector3(30,2,7) and left.get_data()!=right.get_data() and left.get_pixel(80,80)==Color.CYAN and right.get_pixel(80,80)==Color.CYAN,"C7 one keyed camera cuts between distinct sets at adjacent frames120and121 while screen-space paint stays independent")
 var paint:=Storage.image_hash(Drawing.image(app.layers[1].cels[0]));var pcm:=Storage.RasterReader.digest_bytes(app.audio_mix.pcm);var world: Dictionary=canonical(World.portable(app.current_world()));var keys: Array=canonical(app.keys)
 app.has_project.save_file(folder.path_join("scenario-c.has"),"packed");await wait_job();check(app.has_project.path==folder.path_join("scenario-c.has"),"complete scenario saves as one editable packed HAS")
 var manual:=FileAccess.get_sha256(folder.path_join("scenario-c.has"));var error: String=await app.export_movie(folder)
 check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000121.png")).get_data()==left.get_data() and Image.load_from_file(app.last_export_folder.path_join("frame_000122.png")).get_data()==right.get_data(),"actual128frame movie inputs preserve exact adjacent camera cuts and paint")
 var preserved:=true
 for path in sources:preserved=preserved and FileAccess.get_sha256(path)==sources[path]
 check(preserved and FileAccess.get_sha256(folder.path_join("scenario-c.has"))==manual,"all original source models/maps and the explicit manual HAS remain unchanged")
 FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"world":world,"keys":keys,"id":id,"paint":paint,"pcm":pcm,"sources":sources,"manual_sha":manual,"movie":app.last_export_folder.path_join("movie.mp4")},"",true,true))
 print("SCENARIO_C_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"steps":7,"native_fixtures":0,"movie":app.last_export_folder.path_join("movie.mp4")}));await app.quit_studio();quit(0 if failures==0 else 1)

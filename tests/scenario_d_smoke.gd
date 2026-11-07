extends "res://tests/movement_path_smoke.gd"
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
 create_timer(300).timeout.connect(func():push_error("Scenario D watchdog");quit(2));call_deferred("run")
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func box_asset(path: String) -> Error:
 var node:=Node3D.new();node.name="OriginalScenarioBox";preload("res://src/scene3d.gd").box(node,"Box",Vector3.ZERO,Vector3.ONE*.8,Color("ed9275"));var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
 if error==OK:error=doc.write_to_filesystem(state,path)
 node.free();return error
func samples(ids: Array,at: int) -> Dictionary:
 var result:={}
 for id in ids:
  var actor: RefCounted=app.renderer.world_runtime.instance(id);result[id]={"root":actor.sample_transform(at),"body":actor.sample(at)}
 return result
func sample_stamp(ids: Array,at: int) -> String:
 # Keep the oracle as text: reparsing already-normalized tiny JSON floats can
 # introduce another decimal-roundtrip shift before comparison.
 return JSON.stringify(samples(ids,at),"",true,true)
func enable(id: String) -> void:
 app.world_selection.select_entity(id);await settled()
 if not app.physics_editor.body_active(id):await click(app.physics_editor.toggle)
func simulate(ids: Array,actor_id: String) -> void:
 app.set_frame(0)
 for id in ids:await enable(id)
 await enable(actor_id)
 for i in range(120):await physics_frame
func take(scope: int,actor_id: String,ids: Array) -> Dictionary:
 var physics=app.physics_editor;var recording=physics.recording;app.world_selection.select_entity(actor_id);recording.scope.select(scope);recording.scope.item_selected.emit(scope);await settled();var before: int=app.history.size();await click(recording.button)
 check(recording.active and (recording.targets.size()==1 and recording.targets.has(actor_id) if scope==0 else recording.targets.size()==ids.size()+1),"D recording control locks "+("Local actor only" if scope==0 else "World actor and props"))
 var frames:=0;var max_gap:=0;var previous:=Time.get_ticks_usec();var active: RefCounted=physics.simulations[actor_id]
 for body in active.bodies.values():body.apply_central_impulse(Vector3(8,1,0))
 while recording.active:
  frames+=1;var now:=Time.get_ticks_usec();max_gap=maxi(max_gap,now-previous);previous=now;await process_frame
 await settled()
 check(recording.last_error.is_empty() and app.frame==48 and app.history.size()==before+1 and not physics.is_running(),"D completed take reaches exact end in one Undo without leaving simulation live")
 return {"frames":frames,"max_frame_gap_ms":float(max_gap)/1000.,"max_sample_ms":recording.max_sample_ms,"bytes":recording.last_bytes}
func pick_point(id: String) -> Vector2:
 var selection=app.world_selection;selection.picking+=1;selection._process(0);await RenderingServer.frame_post_draw;var image: Image=selection.viewport.get_texture().get_image();selection.picking-=1;var color: Vector3=selection.color_for(id)
 for y in range(20,image.get_height()-20):
  for x in range(20,image.get_width()-20):
   var pixel:=image.get_pixel(x,y)
   if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<.001:return Vector2(x*2+1,y*2+1)
 return Vector2(-1,-1)
func run() -> void:
 var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if "--read" in args else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
 if "--read" in args:
  var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("scenario-d.has"));await wait_job()
  check(app.has_project.path==folder.path_join("scenario-d.has") and not app.physics_editor.is_running() and canonical(World.portable(app.current_world()))==expected.world,"fresh D packed Open restores recorded editable world with physics off")
  var exact:=true
  for at in range(48,-1,-1):exact=exact and sample_stamp(expected.ids,at)==expected.samples[str(at)]
  check(exact,"fresh D reverse seeks reproduce all49root/bone states for humanoid and three impacted props")
  check(Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==expected.paint and Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"fresh D retains exact independent drawing and timed PCM")
  var picture: Image=await app.renderer.capture(app.keys,app.layers,24,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-frame24.png")).get_data(),"fresh D final GPU frame equals original recorded preview exactly")
  print("SCENARIO_D_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
 var asset:=folder.path_join("figure.glb");var map:=folder.path_join("room.glb");var box:=folder.path_join("box.glb");var sources:={}
 for pair in [["Practice figure.glb",asset],["Practice room.glb",map]]:
  var original: String=ProjectSettings.globalize_path("res://examples/tutorials/"+pair[0]);sources[original]=FileAccess.get_sha256(original);var file:=FileAccess.open(pair[1],FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(original));file.close()
 check(box_asset(box)==OK,"original included humanoid/room and generated box fixtures are prepared")
 for path in [asset,map,box]:sources[path]=FileAccess.get_sha256(path)
 check(app.load_scene(map).is_empty(),"real included map geometry supplies ragdoll and prop collision")
 app.mode.select(1);app.change_mode(1);app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
 app.import_actions.add(asset,true,0);await settled();var id: String=app.last_import_id;var actor: RefCounted=app.renderer.world_runtime.instance(id);var physics=app.physics_editor;var recording=physics.recording
 check(actor.order.size()>=17 and physics.body_active(id) and not app.advanced_mode and physics.toggle.is_visible_in_tree() and recording.button.is_visible_in_tree(),"D1 original humanoid imports with compatible Physics ON and Record visible in Simple")
 if not physics.body_active(id):print(app.status.text);await app.quit_studio();quit(1);return
 var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var live: RefCounted=physics.simulations[id];var body: PhysicalBone3D=live.bodies.values()[0];var start:=body.global_position
 var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,app.renderer.camera.unproject_position(start));await settled()
 check(physics.grabbing(),"D1 actual viewport press grabs a humanoid physical body")
 var grabbed: PhysicsBody3D=physics.grabbed
 var motion:=InputEventMouseMotion.new();app.canvas_input(motion,physics.grab_point+Vector2(100,-150))
 for i in range(60):await physics_frame
 check(grabbed!=null and grabbed.global_position.distance_to(start)>.1 and actor.data==before and app.history.size()==history and actor.authored_keys().is_empty(),"D3 live humanoid manipulation moves physical bodies without authored keys/history")
 var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;app._input(release);check(not physics.grabbing() and physics.body_active(id),"D1 release drops the grab while unrecorded simulation continues")
 var pose: Dictionary=live.pose();physics.toggle.button_pressed=false;await settled();var frozen: Dictionary=actor.data.duplicate(true)
 check(not physics.is_running() and canonical(actor.data.pose)==canonical(pose) and actor.authored_keys().is_empty(),"D2 Physics OFF freezes the actual fallen pose without adding simulation keys")
 for i in range(20):await physics_frame
 check(actor.data==frozen,"D2 frozen humanoid stays in its current pose after physical proxies are removed")
 app.pose_editor.frame_model();await settled();var point: Vector2=await pick_point(id);check(point.x>=0,"D2 frozen humanoid remains pickable for a context action")
 if point.x>=0:
  var right:=InputEventMouseButton.new();right.button_index=MOUSE_BUTTON_RIGHT;right.pressed=true;app.canvas_input(right,point);right.pressed=false;app.canvas_input(right,point);await settled()
 check(app.world_selection.menu.visible,"D2 actual context menu opens on the frozen humanoid")
 app.world_selection.menu.id_pressed.emit(1);await settled();var neutral:=true
 for value in actor.sample(0,true).values():neutral=neutral and Timeline.vector(value.position).length()<.00001 and Timeline.quaternion(value.rotation_xyzw).get_angle()<.0001
 check(neutral,"D2 Reset pose context action restores the original neutral/T-pose controls")
 app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values()
 for axis in range(3):app.pose_editor.fields[axis].value=[-2.3,.2,0][axis]
 app.pose_editor.apply_numeric();app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,.7,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
 var ids: Array=[]
 for i in range(3):
  var data:=Model.definition(box);data.position=[0,.4+i*.8,0];check(app.append_object(data,"model").is_empty(),"D original dynamic prop "+str(i)+" joins the world");ids.append(app.last_import_id)
 app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.stroke(Drawing.image(app.layers[1].cels[0]),Vector2(80,80),Vector2(150,80),6,Color.CYAN,false);app.changed();check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"D independent drawing and sound are present before recording")
 var paint:=Storage.image_hash(Drawing.image(app.layers[1].cels[0]));var pcm:=Storage.RasterReader.digest_bytes(app.audio_mix.pcm);var keys: Array=app.keys.duplicate(true);var original: Dictionary=app.current_world().duplicate(true);app.mode.select(1);app.change_mode(1)
 await simulate(ids,id);var local_contacts: Array=[]
 for prop_id in ids:
  var prop: RigidBody3D=physics.simulations[prop_id].body;prop.contact_monitor=true;prop.max_contacts_reported=16;prop.body_entered.connect(func(other):if other is PhysicalBone3D:local_contacts.append(other.get_instance_id()))
 var local_metrics:=await take(0,id,ids);actor=app.renderer.world_runtime.instance(id);var peers:=true
 for row in original.objects:
  if row.id!=id:peers=peers and app.renderer.world_runtime.instance(row.id).data==row
 check(peers and not local_contacts.is_empty() and actor.authored_keys().size()==49,"D5 Local records all49humanoid samples while actually impacted unselected props remain unkeyed")
 var local: Dictionary=actor.data.duplicate(true);app.undo();check(app.current_world()==original,"D5 Local Undo restores all original authored state");app.redo();actor=app.renderer.world_runtime.instance(id);check(actor.data==local,"D5 Local Redo restores exact captured humanoid controls");app.undo()
 await simulate(ids,id);var contacts: Array=[];var starts:={}
 for prop_id in ids:
  var prop: RigidBody3D=physics.simulations[prop_id].body;prop.contact_monitor=true;prop.max_contacts_reported=16;prop.body_entered.connect(func(other):if other is PhysicalBone3D:contacts.append(other.get_instance_id()));starts[prop_id]=prop.global_position
 var world_metrics:=await take(1,id,ids);var displacement:=0.;var keyed:=true
 for prop_id in ids:
  var prop: RefCounted=app.renderer.world_runtime.instance(prop_id);keyed=keyed and prop.authored_keys().size()==49
  for key in prop.authored_keys():
   var delta: Vector3=Timeline.vector(key.transform.position)-starts[prop_id];displacement=maxf(displacement,Vector2(delta.x,delta.z).length())
 check(keyed and not contacts.is_empty() and displacement>.25,"D4 World captures real humanoid impacts and horizontal movement of all three recorded props")
 var all_ids: Array=ids.duplicate();all_ids.append(id);var expected_samples:={}
 for at in range(49):expected_samples[str(at)]=sample_stamp(all_ids,at)
 var replay:=true
 for at in [0,47,12,36,24]:app.set_frame(at);replay=replay and sample_stamp(all_ids,at)==expected_samples[str(at)]
 check(replay and not physics.is_running(),"D4 arbitrary seeks replay captured humanoid/prop motion without fresh simulation")
 check(world_metrics.frames>10 and world_metrics.bytes<1024*1024 and Storage.image_hash(Drawing.image(app.layers[1].cels[0]))==paint and Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==pcm and app.keys==keys,"D6 ordinary World take processes application frames, stays under metadata budget and preserves drawing/audio/camera")
 app.set_frame(24);var picture: Image=await app.renderer.capture(app.keys,app.layers,24,true);picture.save_png(folder.path_join("expected-frame24.png"));var world: Dictionary=canonical(World.portable(app.current_world()));app.has_project.save_file(folder.path_join("scenario-d.has"),"packed");await wait_job();check(app.has_project.path==folder.path_join("scenario-d.has"),"D recorded world saves as one editable packed HAS")
 var manual:=FileAccess.get_sha256(folder.path_join("scenario-d.has"));var error: String=await app.export_movie(folder)
 check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==picture.get_data(),"D actual movie uses exact recorded preview and independent drawing")
 var unchanged:=true
 for path in sources:unchanged=unchanged and FileAccess.get_sha256(path)==sources[path]
 check(unchanged and FileAccess.get_sha256(folder.path_join("scenario-d.has"))==manual,"D original included/copied sources and manual HAS remain unchanged")
 FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"world":world,"ids":all_ids,"samples":expected_samples,"paint":paint,"pcm":pcm,"sources":sources,"manual_sha":manual,"movie":app.last_export_folder.path_join("movie.mp4"),"local":local_metrics,"world_metrics":world_metrics,"local_contacts":local_contacts.size(),"contacts":contacts.size(),"horizontal_displacement":displacement},"",true,true))
 print("SCENARIO_D_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"local":local_metrics,"world":world_metrics,"local_contacts":local_contacts.size(),"contacts":contacts.size(),"displacement":displacement}));await app.quit_studio();quit(0 if failures==0 else 1)

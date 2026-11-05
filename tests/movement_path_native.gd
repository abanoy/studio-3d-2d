extends "res://tests/motion_assist_native.gd"
const PathData=preload("res://src/movement_path.gd")
const Validate=preload("res://src/contact_clipboard.gd")
func render_signature(node: Node, prefix: String, output: Dictionary) -> void:
 var path:=prefix+"/"+str(node.name)
 if node is Node3D:output[path+"/transform"]=var_to_bytes(node.transform).hex_encode();output[path+"/global"]=var_to_bytes(node.global_transform).hex_encode()
 if node is Skeleton3D:
  for bone in range(node.get_bone_count()):
   var key:=path+"/bone/"+str(bone)
   output[key]=var_to_bytes([node.get_bone_rest(bone),node.get_bone_pose(bone),node.get_bone_global_pose(bone)]).hex_encode()
 if node is MeshInstance3D:
  if node.skin:
   for bind in range(node.skin.get_bind_count()):output[path+"/bind/"+str(bind)]=var_to_bytes([node.skin.get_bind_bone(bind),node.skin.get_bind_name(bind),node.skin.get_bind_pose(bind)]).hex_encode()
  if node.mesh:
   for surface in range(node.mesh.get_surface_count()):output[path+"/surface/"+str(surface)]=var_to_bytes(node.mesh.surface_get_arrays(surface)).hex_encode().sha256_text()
  for shape in range(node.get_blend_shape_count()):output[path+"/shape/"+str(shape)]=var_to_bytes(node.get_blend_shape_value(shape)).hex_encode()
 for child in node.get_children():render_signature(child,path,output)
func save_signature(actor: RefCounted, label: String) -> void:
 var values: Dictionary={};render_signature(actor.root,"",values)
 values["camera"]=var_to_bytes([app.renderer.camera.transform,app.renderer.camera.get_camera_projection()]).hex_encode()
 var file:=FileAccess.open(folder.path_join(label+"-render-state.json"),FileAccess.WRITE);file.store_string(JSON.stringify(values));file.close()
func diagnostic_order(node: Node) -> void:
 if node is MeshInstance3D and node.mesh:
  for surface in range(node.mesh.get_surface_count()):
   var material: Material=node.get_active_material(surface)
   if material:
    var copy: Material=material.duplicate()
    if "--diagnostic-order" in OS.get_cmdline_user_args():copy.render_priority=clampi(surface-64,-128,127)
    node.set_surface_override_material(surface,copy)
 for child in node.get_children():diagnostic_order(child)
func click(control: Control) -> void:
 var viewport:=control.get_viewport();var point: Vector2=control.get_global_transform_with_canvas()*(control.size/2.)
 while viewport is Window and viewport.is_embedded():
  point+=Vector2(viewport.position);viewport=viewport.get_parent().get_viewport()
 for down in [true,false]:
  var e:=InputEventMouseButton.new();e.position=point;e.button_index=MOUSE_BUTTON_LEFT;e.pressed=down;viewport.push_input(e,true);await process_frame
 await settled()
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
 app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(OS.get_cmdline_user_args()[1])
 while app.has_project.pid>0:await process_frame
 await settled();var plans: Array=app.current_world().objects.filter(func(row):return Model.is_contact(row)).duplicate(true);var reports:=[]
 check(plans.size()==5,"all five prepared native character families loaded")
 for plan in plans:
  if not Model.is_contact(plan):continue
  var initial_checks:=checks;var initial_failures:=failures
  var actor:=setup(plan);var before: Dictionary=actor.data.duplicate(true);var state:=snapshot(actor)
  var original: Vector3=T.vector(actor.sample_authored_transform(6).position)
  var nearby:=PathData.change(before,6,original+Vector3(.001,0,0),48)
  check(not nearby.has("error") and Validate.validate_candidate(actor,nearby.get("data",before),48).is_empty(),"native small path adjustment remains reachable: "+plan.name)
  var distant:=PathData.change(before,6,original+Vector3(100,0,0),48)
  check(not distant.has("error") and not Validate.validate_candidate(actor,distant.get("data",before),48).is_empty(),"native unreachable path refuses planted feet: "+plan.name)
  check(actor.data==before and snapshot(actor)==state,"path validation preserves native state: "+plan.name)
  app.world_selection.select_entity("actor");app.set_frame(6);app.set_advanced(false);await settled()
  var editor=app.pose_editor.movement_path;app.inspector_scroll.ensure_control_visible(editor.button);await settled();await click(editor.button)
  check(is_instance_valid(editor.window) and editor.valid(),"native Simple path panel opens: "+plan.name)
  if not is_instance_valid(editor.window):continue
  editor.frame.value=6
  var history: int=app.history.size();var keys: Array=app.keys.duplicate(true);var ink: PackedByteArray=app.layers[1].cels[0].image.get_data()
  editor.move_point(6,original+Vector3(100,0,0));await click(editor.apply_button)
  check(editor.window.visible and actor.data==before and app.history.size()==history and not editor.note.text.is_empty(),"actual Apply refuses unreachable path without committing: "+plan.name)
  editor.move_point(6,original+Vector3(.001,0,0));var expected: Dictionary=editor.draft.duplicate(true);await click(editor.apply_button)
  check(not is_instance_valid(editor.window) and actor.data==expected and app.history.size()==history+1,"actual Apply commits reachable native movement once: "+plan.name)
  app.undo();await settled();check(actor.data==before,"native path Undo restores exact original: "+plan.name)
  app.redo();await settled();check(actor.data==expected and app.keys==keys and app.layers[1].cels[0].image.get_data()==ink,"native path Redo preserves camera and independent ink: "+plan.name)
  check(actor.data.format=="studio_model_9","ordinary native path edit upgrades the model: "+plan.name)
  var probe:=Model.new();probe.data=before;var exact:=true;var reachable:=true;var repeatable:=true;var poses:=[];var peak:=0.;var uncrossed:=true
  for half in range(97):
   var at:=float(half)/2.;var a:=probe.sample_authored_transform(at);var b: Dictionary=actor.sample_authored_transform(at)
   exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale and probe.sample_body(at)==actor.sample_body(at)
   poses.append(actor.sample(at));reachable=reachable and actor.evaluation_error.is_empty()
  check(exact and reachable,"new native point preserves peer body/turn/scale curves at97 samples: "+plan.name)
  for half in range(96,-1,-1):repeatable=repeatable and actor.sample(float(half)/2.)==poses[half]
  check(repeatable,"native path contact poses repeat on reverse seek: "+plan.name)
  for at in range(49):
   actor.apply(at,false,false,app.video)
   var legs: Array=actor.contact_legs();var left_hip: Vector3=actor.bone_transform(legs[0].ids[0]).origin;var right_hip: Vector3=actor.bone_transform(legs[1].ids[0]).origin
   var knees: Vector3=actor.bone_transform(legs[0].ids[1]).origin-actor.bone_transform(legs[1].ids[1]).origin
   uncrossed=uncrossed and knees.dot(left_hip-right_hip)>0.
   for foot in Contacts.active(actor.data.animation_clips,at).get("feet",[]):peak=maxf(peak,actor.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
  check(uncrossed,"new captured crouch keeps knees on their own sides: "+plan.name)
  check(peak<.0002,"displayed native feet remain planted along changed path: "+plan.name)
  app.set_frame(6);app.pose_editor.frame_model();app.keys=[T.from_camera(0,app.renderer.camera,"ease")];await settled()
  var before_pose: Dictionary=actor.sample(6);var before_root: Dictionary=actor.sample_transform(6)
  if "--diagnostic-order" in OS.get_cmdline_user_args() or "--diagnostic-copy" in OS.get_cmdline_user_args():diagnostic_order(actor.root)
  var picture: Image=await app.renderer.capture(app.keys,app.layers,6,true);picture.save_png(folder.path_join(plan.id+"-edited.png"));var rendered_state:=snapshot(actor);var camera_state: Transform3D=app.renderer.camera.transform
  if plan.id=="native-0":
   save_signature(actor,"before")
   for repeat in range(3):
    var repeated: Image=await app.renderer.capture(app.keys,app.layers,6,true);repeated.save_png(folder.path_join(plan.id+"-before-repeat-"+str(repeat)+".png"))
  var packed:=folder.path_join(plan.id+".has");app.has_project.save_file(packed,"packed")
  while app.has_project.pid>0:await process_frame
  check(app.has_project.path==packed,"native path saves packed HAS: "+plan.name)
  app.new_project();app.has_project.open_file(packed)
  while app.has_project.pid>0:await process_frame
  await settled();app.world_selection.select_entity("actor");actor=app.renderer.active_model()
  var actual: Dictionary=actor.data.duplicate(true);var wanted: Dictionary=expected.duplicate(true)
  actual.erase("path");wanted.erase("path")
  var same_asset:=FileAccess.get_sha256(actual.source)==FileAccess.get_sha256(wanted.source);actual.source=wanted.source
  var detail:=FileAccess.open(folder.path_join(plan.id+"-records.json"),FileAccess.WRITE);detail.store_string(JSON.stringify({"actual":actual,"expected":wanted},"",true,true));detail.close()
  check(actor!=null and same_asset and actual==JSON.parse_string(JSON.stringify(wanted,"",true,true)),"normal Open restores exact native path model: "+plan.name)
  var pose_file:=FileAccess.open(folder.path_join(plan.id+"-poses.json"),FileAccess.WRITE);pose_file.store_string(JSON.stringify({"before":before_pose,"after":actor.sample(6),"root_before":before_root,"root_after":actor.sample_transform(6)},"",true,true));pose_file.close()
  if "--diagnostic-order" in OS.get_cmdline_user_args() or "--diagnostic-copy" in OS.get_cmdline_user_args():diagnostic_order(actor.root)
  var reopened: Image=await app.renderer.capture(app.keys,app.layers,6,true)
  check(snapshot(actor)==rendered_state,"native renderer bone transforms survive reopen exactly: "+plan.name)
  check(app.renderer.camera.transform==camera_state,"native shot transform survives reopen exactly: "+plan.name)
  reopened.save_png(folder.path_join(plan.id+"-reopened.png"))
  if plan.id=="native-0":
   save_signature(actor,"after")
   for repeat in range(3):
    var repeated: Image=await app.renderer.capture(app.keys,app.layers,6,true);repeated.save_png(folder.path_join(plan.id+"-after-repeat-"+str(repeat)+".png"))
  check(reopened.get_data()==picture.get_data(),"native path and editable ink reopen to identical picture: "+plan.name)
  reports.append({"name":plan.name,"bones":actor.order.size(),"checks":checks-initial_checks,"failures":failures-initial_failures,"foot_error":peak})
 var result:={"checks":checks,"failures":failures,"native_reports":reports};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
 app.dirty=false;app.free();await settled();print("PATH_NATIVE "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

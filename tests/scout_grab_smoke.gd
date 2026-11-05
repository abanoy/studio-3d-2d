extends "res://tests/physics_smoke.gd"
# Repeat from fresh Scout instances, using the real grab anchor and pointer motion.
func run() -> void:
 var folder: String=OS.get_cmdline_user_args()[0]
 var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery")
 root.add_child(app);await settled();app.autosave_enabled.button_pressed=false
 var path:=ProjectSettings.globalize_path("res://output/sfm-smoke/project")
 var source: Dictionary=World.from_project(Storage.load_project(path)).objects[-1]
 var metrics:=[]
 for sign_value in [0.,-1.,1.]:
  var actor_data:=Model.definition(source.source)
  actor_data.metadata=source.metadata.duplicate(true);actor_data.position=[0,3,0]
  var original:=Model.new();original.data=source;var transform:=original.sample_transform(0)
  actor_data.rotation_xyzw=transform.rotation_xyzw;actor_data.scale=transform.scale
  app.new_project();app.load_demo_room();app.append_object(actor_data,"model")
  var rig: RefCounted=app.renderer.active_model()
  var before: Dictionary=rig.data.duplicate(true)
  var physics=app.physics_editor;physics.change(true)
  var sim: RefCounted=physics.simulations[rig.data.id]
  var arm: PhysicalBone3D=sim.bodies["scout_ARM/Skeleton3D::bip_lowerArm_L"]
  var upper: PhysicalBone3D=sim.bodies["scout_ARM/Skeleton3D::bip_upperArm_L"]
  var hand: PhysicalBone3D=sim.bodies["scout_ARM/Skeleton3D::bip_hand_L"]
  for body in sim.bodies.values():body.gravity_scale=0.
  PhysicsServer3D.body_set_mode(upper.get_rid(),PhysicsServer3D.BODY_MODE_STATIC)
  for tick in range(90):await physics_frame
  var joint:=arm.global_transform*arm.joint_offset
  var wrist: Vector3=(hand.global_transform*hand.joint_offset).origin
  var point:=joint.origin.lerp(wrist,.75)
  var axis:=joint.basis.z.normalized()
  var camera: Camera3D=app.renderer.camera
  camera.global_position=joint.origin+axis*2.
  camera.look_at(joint.origin,Vector3.UP if absf(axis.dot(Vector3.UP))<.9 else Vector3.RIGHT)
  var baseline:=upper.global_basis.inverse()*arm.global_basis
  var local_point:=arm.to_local(point)
  physics.grab_point=Vector2.ZERO;physics.grab_depth=99.
  check(physics.begin_grab(arm,point),"actual distal forearm pin attaches")
  check(physics.grab_point.distance_to(camera.unproject_position(point))<.001 and absf(physics.grab_depth-camera.project_ray_origin(physics.grab_point).distance_to(point))<.00001,"grab starts at the requested point without inheriting another grab's depth")
  var peak:=0.;var final_error:=0.;var final_angle:=0.;var span:=point.distance_to(joint.origin)
  var pointer_handled:=true
  for tick in range(90):
   var angle:=deg_to_rad(45.)*float(sign_value)*minf(1.,float(tick+1)/45.)
   var target:=joint.origin+(point-joint.origin).rotated(axis,angle)
   var drag:=InputEventMouseMotion.new()
   pointer_handled=physics.pointer(drag,camera.unproject_position(target)) and pointer_handled
   await physics_frame
   var relative:=upper.global_basis.inverse()*arm.global_basis
   final_angle=rad_to_deg(baseline.get_rotation_quaternion().angle_to(relative.get_rotation_quaternion()))
   peak=maxf(peak,final_angle)
   final_error=arm.to_global(local_point).distance_to(target)
  var motion: Dictionary={"direction":sign_value,"peak_degrees":peak,"final_degrees":final_angle,"lever_length":span,"final_target_error":final_error}
  print("SCOUT_GRAB_METRIC "+JSON.stringify(motion));metrics.append(motion)
  check(pointer_handled and is_finite(peak) and is_finite(final_error) and span>0 and rig.data==before,"controlled grab follows pointer input and leaves authored poses intact")
  if sign_value==0.:
   check(peak<1. and final_error<.001,"holding still causes no initial joint snap")
  else:
   check(final_angle>35. and final_angle<50. and peak<55. and final_error<.005,"forearm follows the 45-degree pull without a transient rotation spike")
  physics.release_grab();check(not physics.grabbing(),"release clears the real pin")
  physics.change(false);await settled()
 var result:={"checks":checks,"failures":failures,"metrics":metrics}
 FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
 app.free();print("SCOUT_GRAB "+JSON.stringify(result));quit(0 if failures==0 else 1)

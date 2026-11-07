extends SceneTree
const Walking=preload("res://src/walking_animation.gd")
const Walk=Walking.Evaluator
const Model=Walk.Model
const Motion=preload("res://src/motion_animation.gd")
const World=preload("res://src/world_document.gd")
const Runtime=preload("res://src/world_runtime.gd")
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(45).timeout.connect(func():push_error("Walking settings watchdog");quit(2));call_deferred("run")
func run() -> void:
	var source:="res://examples/tutorials/Practice figure.glb";var sha:=FileAccess.get_sha256(source);var original:=World.object(source,"model","Walker");var loaded:=SceneIO.load_glb(source);var node: Node3D=loaded.scene;root.add_child(node);var actor:=Model.new();actor.root=node;actor.base_root=node.transform;actor.data=original;actor.inventory(node);actor.motion_video={"fps_num":24,"fps_den":1,"duration_frames":48};actor.apply(0)
	var route: Dictionary=Walk.Paths.change(original,0,Vector3.ZERO,48).data;route=Walk.Paths.change(route,48,Vector3(0,0,.6),48).data;var before:=route.duplicate(true);var configured:=Walking.configure(route,true,{},48)
	check(not configured.has("error") and Model.validate(configured.get("data",{}),48).is_empty(),"walking intent uses validated component model and explicit settings version4")
	if configured.has("error"):print(configured);node.free();quit(1);return
	check(configured.data.format=="studio_model_9" and configured.data.motion_assist.format==Walking.ASSIST_FORMAT and Walking.active(configured.data) and configured.data.motion_assist.part_strengths.get("@root")==0 and route==before,"enabling walking does not modify source controls or enable prior root helpers")
	actor.data=configured.data;var document:=actor.data.duplicate(true);var state:=Walk.capture_state(actor);check(actor.check_bindings().is_empty() and Walk.capture_state(actor)==state,"live walking binding preflight restores installed root and bones exactly")
	var plain:=Model.new();plain.data=route;plain.motion_video=actor.motion_video;var exact:=true;var targets:=true
	for at in [0,9,17,24,37,47,48]:
		actor.apply(at,false,true,actor.motion_video);var first:=Walk.capture_state(actor);var plan: RefCounted=actor.motion_plan()
		if plan==null:print("WALK_CANONICAL_ERROR "+actor._motion_error);node.free();quit(1);return
		var generated: Dictionary=plan.walking.sample(at,plan.walking_amount)
		if generated.has("error"):print(generated);targets=false;continue
		for foot in generated.targets:targets=targets and actor.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position))<.0002
		actor.apply(at,false,false,actor.motion_video);exact=exact and Walk.capture_state(actor)==first and actor.data==document
	check(exact and targets,"ordinary final/preview model evaluation agrees with walking feet and never writes generated keys")
	var parsed: Dictionary=JSON.parse_string(JSON.stringify(document,"",true,true));check(Model.validate(parsed,48).is_empty() and parsed.motion_assist.walking==document.motion_assist.walking,"strict saved walking intent survives exact JSON roundtrip")
	check(actor.sample_transform(0)==plain.sample_authored_transform(0) and actor.sample(0)==plain.sample_body(0),"unkeyed starting pose stays exact while walking eases in")
	var corrected:=Walking.configure(document,true,{"lift":.11},48)
	check(Walking.configure(corrected.data,false,{},48).data.motion_assist.walking.lift==.11,"disabling without new corrections preserves saved walking intent")
	var disabled:=Walking.configure(document,false,{},48);actor.data=disabled.data;exact=true
	for at in [0.,12.,24.,47.,48.]:exact=exact and actor.sample_transform(at)==plain.sample_authored_transform(at) and actor.sample(at)==plain.sample_body(at)
	check(exact and not Walking.active(actor.data),"turning walking off restores exact preexisting authored motion")
	var off:=Motion.configure(document,false,.65,48);actor.data=off.data;check(not Walking.active(actor.data) and actor.sample_transform(12)==plain.sample_authored_transform(12) and actor.sample(12)==plain.sample_body(12),"ordinary master motion switch also disables walking exactly")
	var zero:=Motion.configure(document,true,0.,48);actor.data=zero.data;check(actor.sample_transform(12)==plain.sample_authored_transform(12) and actor.sample(12)==plain.sample_body(12),"master zero amount is exact authored motion")
	check(off.data.motion_assist.walking==document.motion_assist.walking and zero.data.motion_assist.walking==document.motion_assist.walking,"existing motion editor configuration preserves walking intent")
	for change in [{"amount":NAN},{"stride":.9},{"lift":-1},{"extra":1}]:check(Walking.configure(route,true,change,48).has("error"),"invalid walking correction refuses: "+str(change))
	for field in ["enabled","stride","amount","format"]:
		var bad:=document.duplicate(true);bad.motion_assist.walking[field]="bad";check(not Model.validate(bad,48).is_empty(),"mistyped saved walking field refuses: "+field)
	var extra:=document.duplicate(true);extra.motion_assist.walking.extra=1;check(not Model.validate(extra,48).is_empty(),"unknown saved walking fields refuse")
	var master_extra:=document.duplicate(true);master_extra.motion_assist.extra=1;check(not Model.validate(master_extra,48).is_empty(),"unknown version4 master fields refuse")
	actor.data=document.duplicate(true);actor.apply(24);var baseline: Dictionary=actor.sample_body(24);var arm: String="";var hip: String=""
	for id in actor.order:
		if Walk.Hold.IK.normalized(actor.bones[id].name)=="upperarml":arm=id
		if actor.bones[id].name=="hips":hip=id
	var pose:=baseline.duplicate(true);var value:=Model.identity();var q:=Quaternion(Vector3.FORWARD,.3);value.rotation_xyzw=[q.x,q.y,q.z,q.w];pose[arm]=value;actor.data.pose=pose;actor.data.draft_frame=24;var at: Dictionary=plain.sample_authored_transform(24)
	for field in ["position","rotation_xyzw","scale"]:actor.data[field]=at[field]
	var edited:=actor.sample(24,true);check(actor.evaluation_error.is_empty() and edited.get(arm)==value and edited.has(actor.contact_legs()[0].ids[0]),"unkeyed arm draft stays editable while walking continues on legs")
	pose[hip]=Model.identity();pose[hip].position=[0,.1,0];actor.data.pose=pose;edited=actor.sample(24,true)
	check(actor.evaluation_error.is_empty() and edited.get(hip)==pose[hip] and not edited.has(actor.contact_legs()[0].ids[0]) and actor.sample_transform(24,true)==at,"lower-body draft suspends walking for exact direct posing at that frame")
	actor.data=document.duplicate(true);actor.apply(0);var existing_camera:=Camera3D.new();root.add_child(existing_camera);existing_camera.current=true;var old_camera=root.get_camera_3d();state=Walk.capture_state(actor);var count:=root.get_child_count();var world:=World.empty();world.objects=[document]
	var prepared:=Runtime.prepare(world,48);check(not prepared.has("error") and prepared.runtime.root.get_parent()==null and root.get_child_count()==count and root.get_camera_3d()==old_camera and Walk.capture_state(actor)==state,"detached world preflight uses private viewport without changing old scene/camera")
	if not prepared.has("error"):prepared.runtime.dispose()
	var parent:=World.object(source,"group","Stationary parent");parent.id="walking-parent";parent.position=[.25,0,.125];parent.rotation_xyzw=[0,sin(.15),0,cos(.15)];parent.scale=1.1;parent.reference_only=true
	var outer:=World.object(source,"group","Outer parent");outer.id="walking-outer";outer.position=[-.125,0,.25];outer.rotation_xyzw=[0,sin(-.05),0,cos(-.05)];outer.scale=.9;outer.reference_only=true;parent.parent_id=outer.id
	var child:=document.duplicate(true);child.parent_id=parent.id;world.objects=[child,parent,outer]
	var grouped:=Runtime.prepare(world,48,actor.motion_video)
	check(not grouped.has("error"),"child-before-parent nested translated yawed uniformly scaled walking world preflights")
	if not grouped.has("error"):
		var runtime: RefCounted=grouped.runtime;root.add_child(runtime.root);var walker: RefCounted=runtime.instances[child.id];var all_feet:=true;var maximum:=0.
		for half in range(97):
			var group_frame:=float(half)/2.;runtime.evaluate(int(group_frame),true,"",actor.motion_video)
			var plan: RefCounted=walker.motion_plan();var generated: Dictionary=plan.walking.sample(group_frame,plan.walking_amount)
			if generated.has("error"):all_feet=false;continue
			var transform: Dictionary=generated.transform;walker.root.transform=Transform3D(Basis(Model.Timeline.quaternion(transform.rotation_xyzw)).scaled(Vector3.ONE*transform.scale),Model.Timeline.vector(transform.position))*walker.base_root;Walk.Feet.apply_pose(walker,generated.pose)
			for foot in generated.targets:
				var distance: float=walker.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position));maximum=maxf(maximum,distance);all_feet=all_feet and distance<.0002
		check(all_feet and runtime.evaluation_error.is_empty(),"all97nested-parent world-space foot samples remain within0.2mm: "+str(maximum))
		runtime.dispose()
	var moved: Dictionary=Walk.Paths.change(parent,0,Vector3(.25,0,.125),48).data;moved=Walk.Paths.change(moved,48,Vector3(.25,0,.225),48).data;world.objects=[child,moved,outer]
	var moving:=Runtime.prepare(world,48,actor.motion_video);check(moving.has("error") and "stationary" in str(moving.get("error","")),"animated parent root refuses during detached preparation")
	var assisted:=parent.duplicate(true);assisted=Motion.configure(assisted,true,.5,48).data;world.objects=[child,assisted,outer]
	var assisting:=Runtime.prepare(world,48,actor.motion_video);check(assisting.has("error") and "parent groups" in str(assisting.get("error","")),"ancestor procedural assistance refuses before child walking is installed")
	var tilted:=parent.duplicate(true);tilted.rotation_xyzw=[sin(.1),0,0,cos(.1)];world.objects=[child,tilted,outer]
	var sloped:=Runtime.prepare(world,48,actor.motion_video);check(sloped.has("error") and "upright" in str(sloped.get("error","")),"tilted static parent refuses unsupported ground inference")
	check(root.get_child_count()==count and root.get_camera_3d()==old_camera and actor.data==document,"grouped preflight success and refusals leave installed world/camera unchanged")
	var leg: String=actor.contact_legs()[0].ids[0];var keyed: Dictionary=Walk.Paths.Components.put_bones(document,24,{leg:Model.identity()},"ease",48).data;world.objects=[keyed];var rejected:=Runtime.prepare(world,48)
	check(rejected.has("error") and root.get_child_count()==count and root.get_camera_3d()==old_camera and actor.data==document,"unsupported saved walking rejects before old world replacement")
	check(FileAccess.get_sha256(source)==sha,"canonical walking validation/evaluation never changes original GLB")
	existing_camera.free();node.free();print("WALKING_ANIMATION_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)

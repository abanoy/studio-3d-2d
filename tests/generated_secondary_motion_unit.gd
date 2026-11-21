extends SceneTree
const Motion=preload("res://src/generated_secondary_motion.gd")
const Contact=preload("res://src/secondary_skin_contact.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	check(Motion.setting({}).mode=="keep_shape","old models retain Keep shape without a new saved value")
	var data:={"metadata":{Motion.KEY:{"format":Motion.FORMAT,"mode":"natural"}}}
	check(Motion.natural(data,{"source_family":"HAS"}),"explicit Natural applies to generated HAS helper profile")
	check(not Motion.natural(data,{"source_family":"VRM1"}) and not Motion.natural(data,{"source_family":"VRM0"}),"imported native springs retain their own physics")
	for bad in [true,{"mode":"natural"},{"format":Motion.FORMAT,"mode":"other"},{"format":Motion.FORMAT,"mode":"natural","strength":5}]:
		check(Motion.setting({"metadata":{Motion.KEY:bad}}).has("error"),"invalid optional setting is rejected")
	var config:={"stiffness":1.,"drag":.45,"gravity":0.,"gravity_direction":[0,-1,0],"radius":.005}
	var before: PackedByteArray=var_to_bytes(config)
	check(Motion.values(config,false,2)==config,"Keep shape retains every effective original parameter")
	check(Motion.values(config,true,0)==config,"attachment segment keeps its original tuning")
	var natural: Dictionary=Motion.values(config,true,1)
	check(natural.gravity==1. and natural.stiffness==.08 and natural.gravity_direction==[0.,-1.,0.],"hanging lengths gain explicit downward gravity and lower shape bias")
	check(natural.drag==config.drag and natural.radius==config.radius and var_to_bytes(config)==before,"gravity preset preserves drag,radius and original declaration")
	var point:=Vector3.RIGHT;var start:=Vector3(1,-.05,-.2);var finish:=Vector3(1,-.05,.2)
	var downward: Dictionary=Contact.downward_rotation(Vector3.ZERO,point,start,finish,.2)
	var moved: Vector3=downward.rotation*point if not downward.is_empty() else point
	check(not downward.is_empty() and moved.y<0. and Contact.point_distance(moved,start,finish)>=.2,"Natural surface escape moves downward and clears the unchanged capsule")
	check(is_equal_approx(moved.length(),point.length()),"Natural contact correction retains the exact weighted orbit and attachment")
	check(Contact.downward_rotation(Vector3.ZERO,point,Vector3(0,0,-.2),Vector3(0,0,.2),2.).is_empty(),"enclosed orbit refuses an impossible downward escape")
	check(Contact.downward_rotation(Vector3.ZERO,Vector3.DOWN,start,finish,.2).is_empty(),"already lowest orbit leaves contact to the ordinary bounded fallback")
	check(Motion.values(config,true,0,true).gravity==1.,"explicit loose first joint gains gravity without moving its attachment")
	check(Motion.flexible_first({},"longhair_1_0"),"existing long-hair root can relax instead of only its distant tip")
	check(not Motion.flexible_first({},"UnidentifiedJoint"),"ambiguous first joint retains original tuning")
	check(Motion.core({},"Head") and Motion.core({},"Neck") and Motion.core({},"ValveBiped.Bip01_Spine2") and not Motion.core({},"longhair_1_0"),"familiar core joints are conservatively excluded")
	check(Motion.core({"metadata":{"native_parameters":{"humanoid":{"head":{"node_name":"UnusualName"}}}}},"UnusualName"),"explicit humanoid declaration overrides loose-joint naming guesses")
	check(not Motion.flexible_first({"metadata":{"generated_helpers":{"format":"studio_generated_helpers_1","helper_nodes":9}}},"UnidentifiedJoint",1),"malformed legacy helper-node metadata cannot crash preset eligibility")
	check(Motion.core({},"ValveBiped.Bip01_L_UpperArm") and Motion.core({},"ValveBiped.Bip01_L_Forearm") and Motion.core({},"ValveBiped.Bip01_L_Hand") and Motion.core({},"ValveBiped.Bip01_R_Foot"),"known undeclared Source limb chains are excluded from loose-part tuning")
	print("GENERATED_SECONDARY_MOTION_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir()}));quit(0 if failures==0 else 1)

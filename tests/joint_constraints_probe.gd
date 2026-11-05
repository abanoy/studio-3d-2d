extends SceneTree
const Joints=preload("res://src/joint_constraints.gd")
const Model=preload("res://src/model.gd")
const T=preload("res://src/timeline.gd")
var app
func _initialize() -> void:
	create_timer(100).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func bone(rig,name: String) -> String:
	for id in rig.order:
		if rig.bones[id].name==name:return id
	return ""
func pose_record(rig,record: Dictionary) -> Dictionary:
	var id:=bone(rig,record.name);var p: Vector3=rig.bones[id].base.basis*T.vector(record.translation)
	return {"position":[p.x,p.y,p.z],"rotation_xyzw":record.rotation_xyzw}
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var cases: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("cases.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var reports: Array=[]
	for config in cases:
		assert(app.pose_editor.add_model(config.source).is_empty())
		var rig: RefCounted=app.renderer.active_model();var before: Dictionary=rig.data.duplicate(true)
		var controller:=bone(rig,config.controller);var effector:=bone(rig,config.effector)
		var plan:=Joints.plan(rig,controller);assert(not plan.has("error") and not plan.is_empty(),str(plan))
		var reference: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(config.reference)).converted
		var values:={}
		for record in reference.bones:
			if record.name==config.controller:values[controller]=pose_record(rig,record)
		assert(values.has(controller))
		var input:=values.duplicate(true);var began:=Time.get_ticks_usec()
		var result:=Joints.solve(rig,plan,values)
		var elapsed:=Time.get_ticks_usec()-began
		assert(not result.has("error"),str(result))
		assert(values==input and rig.data==before)
		var max_angle:=0.
		for record in reference.bones:
			var id:=bone(rig,record.name)
			if not result.pose.has(id):continue
			max_angle=maxf(max_angle,2*acos(clampf(absf(T.quaternion(result.pose[id].rotation_xyzw).dot(T.quaternion(record.rotation_xyzw))),0,1)))
		var original_lengths:={}
		for id in rig.order:
			if rig.parent_id(id)!="@root":original_lengths[id]=rig.bone_transform(id).origin.distance_to(rig.bone_transform(rig.parent_id(id)).origin)
		rig.data.pose=result.pose;rig.data.draft_frame=0;app.pose_editor.apply_frame();await settle()
		var distance: float=rig.bone_transform(effector).origin.distance_to(rig.bone_transform(controller).origin)
		print("JOINT_PROBE ",JSON.stringify({"case":config.controller,"reach":distance,"usec":elapsed,"reference_angle":max_angle,"chains":result.chains}))
		assert(distance<.001)
		for id in original_lengths:assert(absf(rig.bone_transform(id).origin.distance_to(rig.bone_transform(rig.parent_id(id)).origin)-original_lengths[id])<.00001)
		var limited_count:=0
		for chain in plan.chains:
			for link in chain.links:
				if not link.has("minimum"):continue
				limited_count+=1;var angles:=Basis(T.quaternion(result.pose[link.id].rotation_xyzw)).get_euler(EULER_ORDER_ZYX)
				for axis in range(3):assert(angles[axis]>=link.minimum[axis]-.00001 and angles[axis]<=link.maximum[axis]+.00001)
		assert(limited_count>0)
		var invalid: Dictionary=rig.root.get_meta(Joints.META).duplicate(true);var valid: Dictionary=invalid.duplicate(true)
		invalid.chains[0].iterations=10000;rig.root.set_meta(Joints.META,invalid)
		assert(Joints.plan(rig,controller).has("error"));rig.root.set_meta(Joints.META,valid)
		rig.data=before;app.pose_editor.apply_frame()
		reports.append({"source":config.source,"reach":distance,"usec":elapsed,"reference_angle":max_angle,"chains":result.chains,"lengths_unchanged":true,"limits_checked":true})
	var sample: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("euler.json")))
	var solver:=Joints.new();var clamped: Quaternion=solver.limited(T.quaternion(sample.input),{"minimum":T.vector(sample.minimum),"maximum":T.vector(sample.maximum)})
	assert(absf(clamped.dot(T.quaternion(sample.expected)))>1.-.000001)
	var report:={"cases":reports,"euler_reference_checked":true}
	FileAccess.open(folder.path_join("probe-result.json"),FileAccess.WRITE).store_string(JSON.stringify(report));print("JOINT_CONSTRAINTS_PROBE ",JSON.stringify(report));app.free();quit(0)

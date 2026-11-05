extends Node
const Candidate=preload("res://src/mmd_pose_candidate.gd")
const Motion=preload("res://src/mmd_motion_candidate.gd")
var app
var pid:=-1
var request:={}
var before:={}
var session:=""
var at:=0
var revision:=0
var target_id:=""
var review: ConfirmationDialog
var proposed:={}
var cancelled:=false
var progress: AcceptDialog
var import_button: Button
var motion_button: Button
var range_dialog: ConfirmationDialog
var source_time: SpinBox
var motion_count: SpinBox
var motion:=false
var candidate_job:={}
var converted_result:={}

func busy() -> bool:
	return pid>0 or not candidate_job.is_empty()

func base_bones(rig: RefCounted,frame: int) -> Array:
	var pose: Dictionary=rig.sample_body(frame,true);var rows: Array=[]
	for id in pose:
		if not rig.bones.has(id):continue
		var translation: Vector3=rig.bones[id].base.basis.inverse()*preload("res://src/timeline.gd").vector(pose[id].position)
		rows.append({"name":rig.bones[id].name,"translation":[translation.x,translation.y,translation.z],"rotation_xyzw":pose[id].rotation_xyzw})
	return rows

func setup(owner_app) -> void:
	app=owner_app
	import_button=app.button(app.pose_editor.panel,"Import MMD pose…",choose)
	motion_button=app.button(app.pose_editor.panel,"Import MMD motion…",choose_motion)

func choose_motion() -> void:
	if busy():return
	var rig: RefCounted=app.renderer.active_model()
	if not rig or rig.data.metadata.get("native_parameters",{}).get("kind")!="mmd_preparation":
		app.message("Select an imported MMD character first.");return
	app.choose_file("Import MMD motion",PackedStringArray(["*.vmd"]),motion_range)

func motion_range(path: String) -> void:
	if busy() or app.exporting or not app.renderer.active_model():return
	if app.frame>=int(app.video.duration_frames):app.message("Choose a frame inside the shot before importing motion.");return
	if is_instance_valid(range_dialog):range_dialog.queue_free()
	var rig: RefCounted=app.renderer.active_model()
	var id: String=rig.data.id;var first: int=app.frame
	var saved_session: String=app.recovery_session;var saved_revision: int=app.recovery_revision
	range_dialog=ConfirmationDialog.new();range_dialog.title="Import MMD motion";range_dialog.ok_button_text="Prepare motion";range_dialog.exclusive=false
	var box:=VBoxContainer.new();range_dialog.add_child(box)
	app.label(box,"Start at scene frame %d. Review before applying." % first)
	source_time=app.spin(box,"Start in source (seconds)",0,33333,0);source_time.step=.01
	motion_count=app.spin(box,"Length (scene frames)",1,mini(241,int(app.video.duration_frames)-first),mini(241,int(app.video.duration_frames)-first));motion_count.step=1
	app.label(box,"Matched bones and shapes use editable animation keys.\nCamera keys stay as you set them.")
	app.add_child(range_dialog)
	range_dialog.confirmed.connect(func():
		if app.frame!=first or app.recovery_session!=saved_session or app.recovery_revision!=saved_revision or not app.renderer.active_model() or app.renderer.active_model().data.id!=id:
			app.message("The scene changed. Choose the motion again at the intended frame.")
		else:begin(path,{"source_start":source_time.value*30,"count":int(motion_count.value)})
		if is_instance_valid(range_dialog):range_dialog.queue_free())
	range_dialog.canceled.connect(range_dialog.queue_free);range_dialog.popup_centered(Vector2i(520,260))

func choose() -> void:
	if busy():return
	var rig: RefCounted=app.renderer.active_model()
	if not rig or rig.data.metadata.get("native_parameters",{}).get("kind")!="mmd_preparation":
		app.message("Select an imported MMD character first.");return
	app.choose_file("Import MMD pose",PackedStringArray(["*.vpd"]),begin)

func begin(path: String,motion_settings: Dictionary={}) -> void:
	var rig: RefCounted=app.renderer.active_model()
	if busy() or not rig or app.exporting:return
	if OS.has_feature("web"):
		app.message("MMD pose preparation is available in the desktop Studio.");return
	var native: Dictionary=rig.data.get("metadata",{}).get("native_parameters",{})
	if native.get("kind")!="mmd_preparation" or not native.has("scale"):
		app.message("Select an imported MMD character first.");return
	if not app.physics_editor.freeze_all():return
	motion=not motion_settings.is_empty()
	if motion and (int(motion_settings.get("count",0))<1 or app.frame+int(motion_settings.get("count",0))>int(app.video.duration_frames)):
		app.message("Choose a motion length that fits inside the shot.");return
	if is_instance_valid(review):review.queue_free()
	proposed={}
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	rig=app.renderer.active_model()
	before=rig.data.duplicate(true);target_id=before.id;session=app.recovery_session;revision=app.recovery_revision;at=app.frame
	var folder:=ProjectSettings.globalize_path("res://output/mmd-poses/%d-%d-%d" % [int(Time.get_unix_time_from_system()),OS.get_process_id(),Time.get_ticks_usec()])
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:
		app.message("Cannot create the pose preparation folder.");return
	request={"source":before.source,"pose":path,"scale":before.metadata.native_parameters.scale,"blender":OS.get_environment("HYBRID_BLENDER"),"output":folder.path_join("converted.json"),"result":folder.path_join("result.json"),"cancel":folder.path_join("cancel")}
	if motion:request.merge({"kind":"motion","motion":path,"source_start":motion_settings.source_start,"count":motion_settings.count,"fps_num":int(app.video.fps_num),"fps_den":int(app.video.fps_den)})
	if not native.get("ik_constraints",{}).get("chains",[]).is_empty():
		if motion:
			request["base_frames"]=[]
			for offset in range(int(motion_settings.count)):request.base_frames.append(base_bones(rig,at+offset))
		else:request["base_bones"]=base_bones(rig,at)
	if request.blender.is_empty():request.blender="C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
	var request_path:=folder.path_join("request.json")
	var file:=FileAccess.open(request_path,FileAccess.WRITE)
	if not file:app.message("Cannot write the pose preparation request.");return
	file.store_string(JSON.stringify(request));file.close()
	cancelled=false
	pid=OS.create_process(app.source_import.python(),[ProjectSettings.globalize_path("res://tools/prepare_mmd_pose.py"),request_path],false)
	if pid<=0:app.message("Cannot start pose preparation. Check the desktop Python setting.");return
	import_button.disabled=true
	motion_button.disabled=true
	progress=AcceptDialog.new();progress.title="Preparing MMD motion" if motion else "Preparing MMD pose";progress.dialog_text="Reading animation for the selected character…";progress.ok_button_text="Cancel";progress.exclusive=false
	app.add_child(progress);progress.confirmed.connect(cancel);progress.close_requested.connect(cancel);progress.popup_centered(Vector2i(450,130))
	app.message("Preparing MMD motion…" if motion else "Preparing MMD pose…")

func cancel() -> void:
	if not busy():return
	if pid>0:
		var file:=FileAccess.open(request.cancel,FileAccess.WRITE)
		if not file:app.message("Cannot signal cancellation. Waiting for pose preparation to finish.");return
		file.store_string("cancel");file.close()
	cancelled=true
	if is_instance_valid(progress):progress.hide()
	app.message("Cancelling pose preparation…")

func valid_target() -> bool:
	var rig: RefCounted=app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else null
	if motion and (request.fps_num!=app.video.fps_num or request.fps_den!=app.video.fps_den):return false
	return rig!=null and session==app.recovery_session and at==app.frame and revision==app.recovery_revision and rig.data==before and not app.exporting and not app.playing

func finish_preparation() -> void:
	candidate_job.clear();converted_result.clear()
	import_button.disabled=false
	motion_button.disabled=false
	if is_instance_valid(progress):progress.queue_free()

func preparation_error(message: String) -> void:
	finish_preparation();app.message(message)

func _process(_delta: float) -> void:
	if not candidate_job.is_empty():
		if cancelled:preparation_error("Motion import cancelled. No animation was changed.");return
		if not valid_target():preparation_error("The scene changed during import. Import the motion again at the intended frame.");return
		var update:=Motion.step(candidate_job)
		if update.get("pending",false):
			if is_instance_valid(progress):progress.dialog_text="Preparing editable motion… %d / %d frames" % [update.completed,update.total]
			return
		var result: Dictionary=converted_result.duplicate(false)
		proposed=update;finish_preparation()
		if proposed.has("error"):app.message(proposed.error);return
		show_review(result);return
	if pid<=0 or OS.is_process_running(pid):return
	pid=-1
	if cancelled:preparation_error("Motion import cancelled. No animation was changed." if motion else "Pose import cancelled. No pose key was added.");return
	if not FileAccess.file_exists(request.result):preparation_error("Pose preparation ended without a result.");return
	var result_file:=FileAccess.open(request.result,FileAccess.READ)
	if not result_file or result_file.get_length()>(8 if motion else 4)*1024*1024:
		preparation_error("Pose preparation returned an unreadable or oversized result.");return
	var result=JSON.parse_string(FileAccess.get_file_as_string(request.result))
	if not result is Dictionary:preparation_error("Cannot read pose preparation result.");return
	if not result.get("ok",false):preparation_error(str(result.get("error","Cannot read pose result")));return
	if not result.get("converted") is Dictionary:preparation_error("Pose preparation returned no pose.");return
	if not valid_target():preparation_error("The scene changed during import. Import the pose again at the intended frame.");return
	var rig: RefCounted=app.renderer.world_runtime.instance(target_id)
	if motion:
		candidate_job=Motion.start(rig,result.converted,at,int(app.video.duration_frames),int(app.video.fps_num),int(app.video.fps_den))
		if candidate_job.has("error"):preparation_error(candidate_job.error);return
		converted_result=result
		return
	proposed=Candidate.candidate(rig,result.converted,at,int(app.video.duration_frames))
	finish_preparation()
	if proposed.has("error"):app.message(proposed.error);return
	show_review(result)

func show_review(result: Dictionary) -> void:
	if proposed.has("error"):app.message(proposed.error);return
	if motion:
		proposed["matched_morphs"]=proposed.summary.matched_morphs;proposed["skipped_morphs"]=proposed.summary.skipped_morphs
	var world: Dictionary=app.current_world()
	for i in range(world.objects.size()):
		if world.objects[i].id==proposed.data.id:world.objects[i]=proposed.data
	if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:
		app.message("This pose exceeds the project metadata limit. Use fewer controls.");return
	review=ConfirmationDialog.new();review.title="Review MMD pose";review.ok_button_text="Apply pose";review.exclusive=false
	var sample: Dictionary=result.converted.samples[0] if motion else result.converted
	var missing: Array=sample.get("unmatched_bones",[]) if sample.get("unmatched_bones") is Array else []
	var heading: String="Bone tracks matched: %d" % sample.bones.size() if motion else "Apply %d matched bones at frame %d?" % [sample.bones.size(),at]
	review.dialog_text=heading+"\nUnmatched bones: %d\nShape controls matched: %d\nShape controls skipped: %d\n\nFoot and hand targets may need adjustment.\n" % [missing.size(),proposed.matched_morphs.size(),proposed.skipped_morphs.size()]+("Undo restores the previous animation." if motion else "Undo restores the previous pose.")
	if motion:
		review.title="Review MMD motion"
		review.ok_button_text="Apply motion"
		review.dialog_text="Apply motion to frames %d–%d (%d frames)?\n\n" % [at,proposed.last_frame,result.converted.samples.size()]+review.dialog_text
		var source_end: float=result.converted.source_start+(result.converted.samples.size()-1)*30.*int(app.video.fps_den)/int(app.video.fps_num)
		if source_end>result.converted.source_last_frame:review.dialog_text+="\nThe selected range extends beyond the source motion; its final pose is held."
		if source_end<result.converted.source_last_frame:review.dialog_text+="\nLater source motion is outside the selected range."
		var extra: Dictionary=result.converted.other_sections
		if int(extra.get("camera",0))+int(extra.get("light",0))+int(extra.get("self_shadow",0))+int(extra.get("properties",0))>0:review.dialog_text+="\nSource camera, lights and visibility are not applied."
	var ik: Dictionary=sample.get("ik_report",{})
	if ik.get("available",false):
		var solved:=0;var limited:=false
		for chain in ik.get("chains",[]):
			if chain.get("enabled",true):solved+=1;limited=limited or float(chain.get("residual",0))>.001
		review.dialog_text+="\nJoint chains solved: %d" % solved
		if limited:review.dialog_text+="\nSome targets are not fully reached at these joint settings."
		if not ik.get("skipped",[]).is_empty():review.dialog_text+="\nUnsupported joint chains skipped: %d" % ik.skipped.size()
	elif motion and int(result.converted.other_sections.get("ik_switches",0))>0:review.dialog_text+="\nIK switches need retained joint declarations. Reimport the original MMD model to enable them."
	for skipped in proposed.skipped_morphs.slice(0,3):
		var caption: String=preload("res://src/shape_labels.gd").display(skipped.name,app.advanced_mode)
		review.dialog_text+="\n"+caption.left(40)+": "+str(skipped.reason).left(90)
	if proposed.skipped_morphs.size()>3:review.dialog_text+="\n… %d more skipped controls" % (proposed.skipped_morphs.size()-3)
	review.get_label().autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	review.get_label().custom_minimum_size.x=500
	app.add_child(review);review.confirmed.connect(apply);review.canceled.connect(review.queue_free);review.popup_centered(Vector2i(560,220))
	app.message("Motion ready. Review before applying." if motion else "Pose ready. Review before applying.")

func apply() -> void:
	if busy() or proposed.is_empty():return
	if not valid_target():
		app.message("The scene changed. Import the pose again before applying it.")
		if is_instance_valid(review):review.queue_free()
		return
	var error: String=app.pose_editor.restore_state(proposed.data)
	app.message(("MMD motion recorded at frames %d–%d. Undo restores the previous animation." % [at,proposed.last_frame] if motion else "MMD pose recorded at frame %d. Foot and hand targets may need adjustment. Undo restores the previous pose." % at) if error.is_empty() else error)
	if is_instance_valid(review):review.queue_free()
	if is_instance_valid(range_dialog):range_dialog.queue_free()

func _exit_tree() -> void:
	if pid>0:
		var file:=FileAccess.open(request.cancel,FileAccess.WRITE)
		if file:file.store_string("cancel");file.close()
	if is_instance_valid(progress):progress.queue_free()
	if is_instance_valid(review):review.queue_free()
	if is_instance_valid(range_dialog):range_dialog.queue_free()

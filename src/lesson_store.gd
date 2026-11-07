extends RefCounted
const Storage=preload("res://src/storage.gd")
const Recovery=preload("res://src/recovery.gd")
const Timeline=preload("res://src/timeline.gd")
const COURSES:={"first-movie-v1":11,"basic-pose":3,"advanced-camera":3,"advanced-lighting-v1":4,"advanced-interpolation-v1":5,"advanced-constraints-v1":5,"advanced-physics-v1":5}
var root: String
var error:=""
var restored_observations:={}

static func valid_observations(value) -> bool:
	if not value is Dictionary or value.size()>4:return false
	for name in value:
		if not name in ["physics_seen","preview_seen","export_done","local_record_seen"] or not value[name] is bool:return false
	return true

static func checkpoint_name(course: String,name: String) -> bool:
	if not course in COURSES:return false
	if name=="resume":return true
	for at in range(int(COURSES[course])+1):
		if name=="step_%02d" % at:return true
	return false

static func session_ok(value) -> bool:
	if not value is String or value.is_empty() or value.length()>96:return false
	for c in value:
		if not c in "0123456789_-":return false
	return true

func folder(course: String,session: String) -> String:
	return root.path_join(course).path_join(session) if course in COURSES and session_ok(session) else ""

func write_json(path: String,data: Dictionary) -> bool:
	error=preload("res://src/atomic_metadata.gd").write_bytes(path,JSON.stringify(data,"",true,true).to_utf8_buffer(),root)
	return error.is_empty()

func progress(course: String,session := "") -> Dictionary:
	if not course in COURSES:return {}
	if session.is_empty():
		var latest:=Recovery.read_json(root.path_join(course+".json"));session=str(latest.get("session",""))
	var directory:=folder(course,session)
	if directory.is_empty():return {}
	var value:=Recovery.read_json(directory.path_join("progress.json"))
	if value.get("format")!="studio_lesson_progress_1" or value.get("course")!=course or value.get("session")!=session or not Storage.integer(value.get("step"),0,int(COURSES[course])) or not value.get("done") is bool:return {}
	if value.done!=(int(value.step)==int(COURSES[course])):return {}
	if value.get("current")!="resume" and value.get("current")!="step_%02d" % int(value.step):return {}
	if not (value.get("updated_at") is int or value.get("updated_at") is float) or not is_finite(float(value.updated_at)):return {}
	return value

func sessions(course: String) -> Array:
	var rows: Array=[]
	if not course in COURSES:return rows
	if not DirAccess.dir_exists_absolute(root.path_join(course)):return rows
	for name in DirAccess.get_directories_at(root.path_join(course)):
		var item:=progress(course,name)
		if not item.is_empty():rows.append(item)
	rows.sort_custom(func(a,b):return a.updated_at>b.updated_at)
	return rows

static func ui(app) -> Dictionary:
	var view: Dictionary=app.renderer.view_state();var t: Transform3D=view.transform
	return {"basis":[t.basis.x.x,t.basis.x.y,t.basis.x.z,t.basis.y.x,t.basis.y.y,t.basis.y.z,t.basis.z.x,t.basis.z.y,t.basis.z.z],"origin":[t.origin.x,t.origin.y,t.origin.z],"fov":view.fov,"near":view.near,"far":view.far,"mode":app.mode.selected,"advanced":app.advanced_mode,"selected":app.world_selection.selected,"bone":app.pose_editor.selected,"layer":app.active_layer,"zoom":app.canvas.zoom,"pan":[app.canvas.pan.x,app.canvas.pan.y]}

static func valid_ui(value) -> bool:
	if not value is Dictionary or not value.get("advanced") is bool or not Storage.integer(value.get("mode"),0,2) or not Storage.integer(value.get("layer"),0,3):return false
	if value.has("observed") and not valid_observations(value.observed):return false
	for pair in [["basis",9],["origin",3],["pan",2]]:
		if not value.get(pair[0]) is Array or value[pair[0]].size()!=pair[1]:return false
		for number in value[pair[0]]:
			if not (number is int or number is float) or not is_finite(float(number)) or absf(float(number))>1e12:return false
	if not value.get("selected") is String or value.selected.length()>128 or not value.get("bone") is String or value.bone.length()>512:return false
	if not (value.get("zoom") is int or value.get("zoom") is float) or not is_finite(float(value.zoom)) or value.zoom<.25 or value.zoom>4:return false
	var b: Array=value.basis
	if absf(Basis(Vector3(b[0],b[1],b[2]),Vector3(b[3],b[4],b[5]),Vector3(b[6],b[7],b[8])).determinant())<.000001:return false
	return Timeline.range_error([value]).is_empty() and (value.get("fov") is int or value.get("fov") is float) and is_finite(float(value.fov)) and value.fov>=15 and value.fov<=120

static func valid_recovery(value) -> bool:
	# Recovery-only metadata. Never interpret imported project fields as a request
	# to start a lesson or use an unchecked session as a filesystem address.
	if not value is Dictionary or value.size()!=9 or JSON.stringify(value,"",true,true).to_utf8_buffer().size()>16384:return false
	if value.get("format")!="studio_lesson_recovery_1" or not value.get("course") is String or not value.course in COURSES or not session_ok(value.get("session")):return false
	if not Storage.integer(value.get("step"),0,int(COURSES[value.course])) or not value.get("done") is bool or value.done!=(int(value.step)==int(COURSES[value.course])):return false
	if not valid_ui(value.get("ui")) or not valid_ui(value.get("baseline")) or not value.get("collapsed") is bool:return false
	return (value.get("fov_baseline") is int or value.get("fov_baseline") is float) and is_finite(float(value.fov_baseline)) and value.fov_baseline>=15 and value.fov_baseline<=120

func save(app,course: String,session: String,step: int,done: bool,name: String,observations: Dictionary={}) -> bool:
	error="";var directory:=folder(course,session)
	if directory.is_empty() or step<0 or step>int(COURSES.get(course,0)) or done!=(step==int(COURSES.get(course,0))) or not name in ["resume","step_%02d" % step] or not valid_observations(observations):error="Invalid lesson checkpoint address.";return false
	error=preload("res://src/atomic_metadata.gd").path_error(directory.path_join(name).path_join("project.json"),root)
	if not error.is_empty():return false
	var state:=ui(app)
	if not observations.is_empty():state["observed"]=observations.duplicate()
	if not valid_ui(state):error="Invalid lesson view state.";return false
	var document: Dictionary=app.project_snapshot()
	error=Storage.save_project(directory.path_join(name),document.video,document.camera_keys,document.layers,str(document.get("source","")),int(document.editor.frame),document.audio,{},document.get("model",{}),true,document.world,{"lesson_ui":state},document.palette,document.sequence_graph,null,document.get("reference_sheet",{}))
	if not error.is_empty():return false
	var value:={"format":"studio_lesson_progress_1","course":course,"session":session,"step":step,"done":done,"current":name,"updated_at":Time.get_unix_time_from_system()}
	return write_json(directory.path_join("progress.json"),value) and write_json(root.path_join(course+".json"),{"session":session})

func load_snapshot(app,course: String,session: String,name: String) -> bool:
	error="";var directory:=folder(course,session)
	if directory.is_empty() or not checkpoint_name(course,name):error="Invalid lesson checkpoint.";return false
	# Inspect only bounded UI metadata here. Normal Open validates/decodes the
	# project once before installing anything, including all declared assets.
	var path:=directory.path_join(name);var data:=Recovery.read_json(path.path_join("project.json"))
	if not data.get("editor") is Dictionary:error="Lesson checkpoint has invalid editor state.";return false
	var value=data.editor.get("lesson_ui",{})
	if not valid_ui(value):error="Lesson checkpoint has invalid editor state.";return false
	if not app.open_project(path):error=app.open_project_error;return false
	app.has_project.clear_identity();app.project_folder=""
	restore_ui(app,value)
	restored_observations=value.get("observed",{}).duplicate()
	return true

static func restore_ui(app,value: Dictionary) -> void:
	# Call only after valid_ui and successful scene installation.
	app.set_advanced(value.advanced)
	if not value.selected.is_empty():app.world_selection.select_entity(value.selected)
	var actor: RefCounted=app.pose_editor.active_rig()
	app.pose_editor.selected=value.bone if actor and actor.bones.has(value.bone) else "@root";app.pose_editor.refresh_values();app.mode.select(value.mode);app.change_mode(value.mode)
	app.active_layer=mini(int(value.layer),app.layers.size()-1);app.layer_choice.select(app.active_layer);app.refresh_layer()
	var b: Array=value.basis
	app.renderer.restore_view({"transform":Transform3D(Basis(Vector3(b[0],b[1],b[2]),Vector3(b[3],b[4],b[5]),Vector3(b[6],b[7],b[8])),Timeline.vector(value.origin)),"fov":value.fov,"near":value.near,"far":value.far})
	app.canvas.zoom=value.zoom;app.canvas.pan=Vector2(value.pan[0],value.pan[1]);app.canvas.queue_redraw();app.changed()

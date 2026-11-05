extends Node
# Neutral observations only; adoption uses the existing manual catalogue/Undo.
const Catalog=preload("res://src/shape_catalog.gd")
var editor
var start_button: Button
var cancel_button: Button
var adopt_button: Button
var info: Label
var pid:=-1
var folder:=""
var job_id:=""
var revision:=-1
var root_id:=0
var source_sha:=""
var deadline:=0
var cancelled:=false
var observations:={}
var displayed:=""
var last_exit:=-1

func setup(owner_editor,parent: Node) -> void:
	editor=owner_editor
	start_button=editor.app.button(parent,"Study deform areas",start)
	start_button.tooltip_text="Compare neutral positional geometry locally. Suggestions remain unassigned until you choose to use them."
	cancel_button=editor.app.button(parent,"Cancel study",cancel)
	info=editor.app.label(parent,"");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	adopt_button=editor.app.button(parent,"Use suggested area",adopt)
	refresh()

func available() -> bool:
	return not OS.has_feature("web") and editor.actor()!=null and not editor.dirty and not editor.app.exporting and not editor.app.playing and not editor.app.pose_editor.contacts.live_busy() and editor.app.source_import.pid<=0 and editor.app.has_project.pid<=0

func context_valid() -> bool:
	var actor: RefCounted=editor.actor()
	return actor!=null and is_instance_valid(actor.root) and actor.root.get_instance_id()==root_id and actor.data.sha256==source_sha and editor.app.recovery_revision==revision and editor.panel.get_window().visible and not editor.app.home.visible and not editor.app.exporting and not editor.app.playing and not editor.app.pose_editor.contacts.live_busy()

func start() -> void:
	if pid>0:return
	if not available():editor.app.message("Apply pending amounts and pause live motion before studying controls. Local studies need Windows Studio.");return
	var actor: RefCounted=editor.actor();var controls:=[]
	for row in editor.rows():
		for target in range(row.names.size()):
			var entry:=Catalog.lookup(actor.data,int(row.node),target,str(row.names[target]))
			if entry.has("notice"):editor.app.message(str(entry.notice));return
			if entry.manual or entry.area!="Other":controls.append({"node":int(row.node),"target":target,"native_name":str(row.names[target]),"area":entry.area,"provenance":"Manual choice" if entry.manual else "Name estimate"})
	job_id=str(ResourceUID.create_id());folder=ProjectSettings.globalize_path("res://output/shape-studies/"+job_id)
	if DirAccess.dir_exists_absolute(folder):editor.app.message("Study folder already exists. Try again for a new study.");return
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:editor.app.message("Cannot create the study folder.");return
	var request:={"format":"studio_shape_study_request_1","job_id":job_id,"seeds":{"format":"studio_deform_seeds_1","source_sha256":actor.data.sha256,"controls":controls}}
	var file:=FileAccess.open(folder.path_join("request.json"),FileAccess.WRITE)
	if file==null:editor.app.message("Cannot write the study request.");return
	file.store_string(JSON.stringify(request));file.close()
	var python: String=editor.app.source_import.python()
	if python.is_absolute_path() and not FileAccess.file_exists(python):editor.app.message("Python was not found. Check the local Python setting.");return
	root_id=actor.root.get_instance_id();source_sha=actor.data.sha256;revision=editor.app.recovery_revision;cancelled=false;observations.clear();displayed=""
	pid=OS.create_process(python,[ProjectSettings.globalize_path("res://tools/shape_study_worker.py"),ProjectSettings.globalize_path(actor.data.source),folder],false)
	deadline=Time.get_ticks_msec()+125000
	info.text="Studying neutral geometry locally… Your scene is unchanged."
	if pid<0:info.text="Cannot start the study. Check that Python is installed."
	refresh()

func cancel() -> void:
	if pid>0:
		cancelled=true
		var file:=FileAccess.open(folder.path_join("cancel"),FileAccess.WRITE)
		if file:file.store_string("cancel");file.close()
		info.text="Cancelling study…"
	else:observations.clear();info.text="Study cleared. Saved choices are unchanged."
	displayed="";refresh()

func _process(_delta: float) -> void:
	if not is_instance_valid(editor):return
	if pid>0:
		if not context_valid() and not cancelled:cancel()
		if OS.is_process_running(pid):
			if Time.get_ticks_msec()>deadline:OS.kill(pid);cancelled=true
			refresh();return
		last_exit=OS.get_process_exit_code(pid);pid=-1
		if cancelled:observations.clear();info.text="Study cancelled. Your scene and saved choices are unchanged."
		elif last_exit!=0:observations.clear();info.text="Study worker did not finish successfully. Your scene is unchanged."
		else:
			var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.READ)
			var parser:=JSON.new();var result={}
			if file and file.get_length()<=8*1024*1024 and parser.parse(file.get_as_text())==OK and parser.data is Dictionary:result=parser.data
			if result.get("format")!="studio_shape_study_result_1" or result.get("job_id")!=job_id or not result.get("ok",false):info.text=str(result.get("error","Study ended without a usable result.")).left(400)
			else:
				var error:=install_report(result.get("value"))
				if not error.is_empty():info.text=error
		displayed=""
	elif not observations.is_empty() and not context_valid():observations.clear();displayed="";info.text="Scene or labels changed. Study again for fresh suggestions."
	refresh()

func install_report(value) -> String:
	if not context_valid() or not value is Dictionary or value.get("format")!="studio_deform_observations_1" or value.get("source_sha256")!=source_sha or not value.get("rows") is Array or value.rows.size()>4096:return "Study no longer matches the selected model."
	var expected:={};var candidate:={}
	for row in editor.rows():
		for target in range(row.names.size()):expected[str(int(row.node))+":"+str(target)]=str(row.names[target])
	for row in value.rows:
		if not row is Dictionary or not number_index(row.get("node"),100000) or not number_index(row.get("target"),2048):return "Study contains an invalid control identity."
		var key: String=str(int(row.node))+":"+str(int(row.target))
		if not expected.has(key) or expected[key]!=row.get("native_name") or candidate.has(key) or not row.get("region_estimate") is Dictionary or not row.region_estimate.get("area") in Catalog.AREAS or not number_index(row.get("changed_vertices"),500001):return "Study differs from the model's exact native controls."
		var estimate: Dictionary=row.region_estimate
		if not estimate.get("reason") is String or estimate.reason.length()>256 or not estimate.get("matches") is Array or estimate.matches.size()>8:return "Invalid study evidence."
		for match_row in estimate.matches:
			if not match_row is Dictionary or not number_index(match_row.get("seed_node"),100000) or not number_index(match_row.get("seed_target"),2048):return "Invalid study example identity."
			var seed_key: String=str(int(match_row.seed_node))+":"+str(int(match_row.seed_target))
			if not match_row.get("area") in Catalog.AREAS or match_row.area=="Other":return "Invalid study example area."
			if int(match_row.seed_node)!=int(row.node) or not expected.has(seed_key) or expected[seed_key]!=match_row.get("seed_name") or not match_row.get("seed_provenance") in ["Name estimate","Manual choice","Provisional observed annotation"] or not unit_number(match_row.get("similarity")) or not unit_number(match_row.get("query_coverage")):return "Study example no longer matches the model."
		candidate[key]=row
	if candidate.size()!=expected.size():return "Study is missing model controls."
	observations=candidate;return ""

static func number_index(value,limit: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=0 and value<limit

static func unit_number(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=0 and value<=1

func selected() -> Dictionary:return observations.get(str(editor.node_index)+":"+str(editor.shape_index),{})

func refresh() -> void:
	if not is_instance_valid(start_button):return
	start_button.disabled=pid>0 or not available();cancel_button.visible=pid>0;cancel_button.disabled=cancelled
	var row:=selected();adopt_button.disabled=pid>0 or not available() or row.is_empty() or row.region_estimate.area=="Other"
	if not row.is_empty():
		var key: String=str(editor.node_index)+":"+str(editor.shape_index)
		if displayed!=key:
			displayed=key;info.text="Neutral positional study: "+str(int(row.changed_vertices))+" moved vertices.\n"+("Suggested area: "+str(row.region_estimate.area)+" (tentative)." if row.region_estimate.area!="Other" else "No clear area match.")+"\n"+str(row.region_estimate.get("reason",""))+"\nNames and earlier manual choices provide the example labels. No animation changed."
			if not row.region_estimate.matches.is_empty():
				var example: Dictionary=row.region_estimate.matches[0]
				var coverage := roundi(float(example.query_coverage)*100)
				info.text+="\nClosest example: %s (%s).\n%s examples cover %d%% of the vertices this control moves." % [str(example.seed_name).left(100),example.seed_provenance,example.area,coverage]
				info.text+=" This percentage measures overlap, not a probability."
	elif not observations.is_empty():info.text="Select a control to review its neutral geometry.";displayed=""

func adopt() -> void:
	var row:=selected()
	if pid>0 or not available() or not context_valid() or row.is_empty() or row.region_estimate.area=="Other":return
	editor.assigned_area.select(Catalog.AREAS.find(row.region_estimate.area));editor.assign_control()
	if editor.app.recovery_revision!=revision:observations.clear();displayed="";info.text="Area saved with Undo. Study again to use this choice as a new example."

func _exit_tree() -> void:
	if pid>0 and OS.is_process_running(pid):OS.kill(pid)

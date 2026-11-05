extends Node
const Clip=preload("res://src/raster_clip.gd")
var app
var launch: Button
var pid:=-1
var phase:=""
var cancelled:=false
var session:=""
var revision:=0
var video:={}
var at:=0
var source:=""
var job:=""
var response:=""
var inventory:={}
var request:={}
var candidate:={}
var decoded: Array=[]
var choices: Dictionary={}
var review: ConfirmationDialog
var preview: ConfirmationDialog
var progress: AcceptDialog
var info: Label
var tools_label: Label
var still: SpinBox
var viewer: Control
var scrub: SpinBox
var last_stage:=""
var next_progress:=0

func setup(owner_app) -> void:
	app=owner_app
	launch=app.button(app.drawing_section,"Import Krita artwork…",choose)
	app.drawing_section.move_child(launch,app.layer_editor.launch.get_index()+1)
	launch.tooltip_text="Review a local KRA and add rendered artwork as one new editable drawing layer. Installed Krita is required."

func slots() -> int:
	var used:=0
	for layer in app.layers:used+=layer.cels.size()
	return 32-used
func available() -> bool:
	return not OS.has_feature("web") and not app.exporting and not app.playing and app.mode.selected==0 and app.layers.size()<4 and slots()>0 and app.frame<int(app.video.duration_frames)
func valid() -> bool:
	return session==app.recovery_session and revision==app.recovery_revision and video==app.video and at==app.frame and available()
func external_busy() -> bool:
	return app.source_import.pid>0 or app.has_project.pid>0 or app.audio_importer.pid>0
func close_dialogs() -> void:
	for dialog in [review,preview,progress]:
		if is_instance_valid(dialog):dialog.hide();dialog.queue_free()
	review=null;preview=null;progress=null;choices={};viewer=null;scrub=null
func fail(why: String) -> void:
	close_dialogs();phase="";candidate={};decoded=[];app.message(why)
func choose() -> void:
	if not phase.is_empty():app.message("Finish or cancel the current artwork import first.");return
	if not available():app.message("Choose Draw mode with room for another layer, drawing and frame. Krita import is desktop only.");return
	app.choose_file("Import Krita artwork",PackedStringArray(["*.kra ; Krita artwork"]),begin)
func begin(path: String) -> void:
	if not phase.is_empty() or not available() or external_busy():app.message("Finish other scene operations before importing artwork.");return
	if path.get_extension().to_lower()!="kra" or path.begins_with("\\\\") or path.begins_with("//") or path.contains("://"):app.message("Choose a local Krita .kra file.");return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.release_mouse()
	session=app.recovery_session;revision=app.recovery_revision;video=app.video.duplicate(true);at=app.frame;source=path
	job=ProjectSettings.globalize_path("res://output/krita-imports/%d-%d" % [OS.get_process_id(),Time.get_ticks_usec()])
	if DirAccess.make_dir_recursive_absolute(job)!=OK:fail("Cannot create the artwork preparation folder.");return
	cancelled=false;response=job.path_join("inspect.json");phase="inspect"
	start(["--inspect",source,"--result",response,"--cancel-file",job.path_join("cancel")],"Reading Krita layers…")
func start(args: Array,title: String) -> void:
	var arguments:=PackedStringArray([ProjectSettings.globalize_path("res://tools/prepare_krita.py")]);arguments.append_array(PackedStringArray(args))
	pid=OS.create_process(app.source_import.python(),arguments,false)
	if pid<=0:fail("Cannot start artwork preparation. Check the desktop Python setting.");return
	progress=AcceptDialog.new();progress.title="Import Krita artwork";progress.dialog_text=title+"\nYour original file stays unchanged.";progress.ok_button_text="Cancel";progress.exclusive=false;app.add_child(progress)
	progress.confirmed.connect(cancel);progress.close_requested.connect(cancel);progress.popup_centered(Vector2i(470,160))
func cancel() -> void:
	cancelled=true
	if pid>0:
		var flag:=FileAccess.open(job.path_join("cancel"),FileAccess.WRITE)
		if flag:flag.store_string("cancel");flag.close()
		if is_instance_valid(progress):progress.hide()
		app.message("Cancelling artwork preparation…")
	else:fail("Artwork import cancelled. No layer was added.")
func read_json(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>1024*1024:return {}
	var value=JSON.parse_string(file.get_as_text());file.close()
	return value if value is Dictionary else {}
func _process(_delta: float) -> void:
	launch.disabled=not phase.is_empty() or not available()
	if phase.is_empty():return
	if not cancelled and not valid():cancel();app.message("The scene, frame or working mode changed. Import artwork again.")
	if pid>0:
		if OS.is_process_running(pid):
			if phase=="prepare" and is_instance_valid(progress) and Time.get_ticks_msec()>=next_progress:
				next_progress=Time.get_ticks_msec()+250
				var update:=read_json(job.path_join("prepared/progress.json"));var stage: String=str(update.get("stage",""))
				if stage!=last_stage:last_stage=stage;progress.dialog_text="Preparing artwork: "+stage+"\nCancel keeps the scene unchanged."
			return
		pid=-1
		if is_instance_valid(progress):progress.queue_free();progress=null
		if cancelled:fail("Artwork import cancelled. No layer was added.");return
		var result:=read_json(response)
		if not result.get("ok",false):fail(str(result.get("error","Artwork preparation ended without a readable result.")));return
		if phase=="inspect":
			if not result.get("inventory") is Dictionary:fail("Cannot read the source layer inventory.");return
			inventory=result.inventory;show_layers();return
		if phase=="prepare":accept_packet(result);return
	if phase=="decode":
		var row: Dictionary=candidate.holds[decoded.size()]
		var image:=Image.load_from_file(row.path)
		if image==null or image.get_width()!=video.width or image.get_height()!=video.height:fail("Cannot decode this prepared drawing.");return
		image.convert(Image.FORMAT_RGBA8);decoded.append({"id":str(ResourceUID.create_id()),"start":at+row.start,"duration":row.duration,"image":image})
		if decoded.size()==candidate.holds.size():show_preview()
	if phase=="candidate" and is_instance_valid(preview):preview.get_ok_button().disabled=external_busy()

func krita() -> String:
	var prefs:=ConfigFile.new();prefs.load(app.display_prefs_path)
	for path in [OS.get_environment("HYBRID_KRITA"),str(prefs.get_value("tools","krita","")),"C:/Program Files/Krita (x64)/bin/krita.exe","C:/Program Files/Krita/bin/krita.exe"]:
		if FileAccess.file_exists(path) and path.get_file().to_lower()=="krita.exe":return path
	return ""
func locate() -> void:
	app.choose_file("Locate installed Krita",PackedStringArray(["krita.exe ; Krita executable"]),func(path):
		if path.get_file().to_lower()!="krita.exe" or not FileAccess.file_exists(path):app.message("Choose the installed krita.exe.");return
		var prefs:=ConfigFile.new();prefs.load(app.display_prefs_path);prefs.set_value("tools","krita",path)
		if prefs.save(app.display_prefs_path)!=OK:app.message("Cannot save the Krita location.");return
		if is_instance_valid(review):update_tools())
func update_tools() -> void:
	tools_label.text="Installed Krita found." if not krita().is_empty() else "Locate installed Krita to prepare this file."
	review.get_ok_button().disabled=not inventory.get("render_supported",false) or krita().is_empty()
func show_layers() -> void:
	phase="layers";review=ConfirmationDialog.new();review.title="Review Krita artwork";review.exclusive=false;review.unresizable=false;review.get_ok_button().text="Prepare preview";app.add_child(review)
	var box:=VBoxContainer.new();review.add_child(box)
	info=Label.new();info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;info.custom_minimum_size.x=500;box.add_child(info)
	info.text="%s · %s × %s\nRender the chosen layers together into one new drawing layer, starting at frame %d. Source audio and native layer editing stay in Krita." % [source.get_file(),inventory.get("width",0),inventory.get("height",0),at]
	if not inventory.get("render_supported",false):info.text+="\n"+str(inventory.get("limitations",[]))
	if not inventory.get("animated",false):still=app.spin(box,"Still exposure (frames)",1,int(video.duration_frames)-at,int(video.duration_frames)-at)
	else:still=null
	var reveal:=CheckButton.new();reveal.text="Choose source layers…";box.add_child(reveal)
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(500,220);box.add_child(scroll)
	var rows:=VBoxContainer.new();rows.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(rows);scroll.hide();reveal.toggled.connect(func(shown):scroll.visible=shown)
	if inventory.get("render_supported",false) and inventory.get("layers") is Array and inventory.layers.size()<=128:
		for row in inventory.layers:
			var id: String=str(row.get("uuid",""))
			if id.is_empty():continue
			var check:=CheckBox.new();check.text=str(row.get("name","Layer"));check.button_pressed=str(row.get("visible","1"))=="1";check.tooltip_text=id;rows.add_child(check);choices[id]={"check":check,"original":check.button_pressed}
	tools_label=Label.new();box.add_child(tools_label);app.button(box,"Locate Krita…",locate);update_tools()
	review.confirmed.connect(prepare);review.canceled.connect(cancel);review.close_requested.connect(cancel);review.popup_centered(Vector2i(540,320))
func prepare() -> void:
	if phase!="layers" or not valid() or external_busy():fail("The scene changed or another operation is running. Import artwork again.");return
	var overrides:={}
	for id in choices:
		if choices[id].check.button_pressed!=choices[id].original:overrides[id]=choices[id].check.button_pressed
	if still:still.apply()
	request={"source":source,"source_sha256":inventory.get("source_sha256"),"output":job.path_join("prepared"),"cancel":job.path_join("cancel"),"result":job.path_join("result.json"),"krita":krita(),"ffmpeg":app.encoder_path.text,"width":video.width,"height":video.height,"fps_num":video.fps_num,"fps_den":video.fps_den,"available_frames":int(video.duration_frames)-at,"max_cels":slots(),"still_duration_frames":int(still.value) if still else 1,"layer_visibility":overrides}
	var file:=FileAccess.open(job.path_join("request.json"),FileAccess.WRITE)
	if not file:fail("Cannot write artwork preparation request.");return
	file.store_string(JSON.stringify(request));file.close();review.hide();phase="prepare";response=request.result;last_stage="";start([job.path_join("request.json")],"Rendering selected layers…")
func accept_packet(result: Dictionary) -> void:
	var path:=job.path_join("prepared/clip.json")
	if result.get("clip") is not String or result.clip.replace("\\","/").simplify_path()!=path.replace("\\","/").simplify_path() or result.get("sha256")!=FileAccess.get_sha256(path):fail("Prepared artwork packet changed.");return
	candidate=Clip.validate(read_json(path),job.path_join("prepared"),video,at,slots(),str(inventory.get("source_sha256")))
	if candidate.has("error"):fail(candidate.error);return
	phase="decode";decoded=[]
func show_preview() -> void:
	phase="candidate";preview=ConfirmationDialog.new();preview.title="Add prepared artwork?";preview.exclusive=false;preview.unresizable=false;preview.get_ok_button().text="Add drawing layer";app.add_child(preview)
	var box:=VBoxContainer.new();preview.add_child(box)
	var caption:=Label.new();caption.text="Frame %d · %d frames · %d held drawings\nCheckerboard shows transparency. Original source stays unchanged." % [at,candidate.duration,decoded.size()];box.add_child(caption)
	viewer=preload("res://src/krita_preview.gd").new();viewer.custom_minimum_size=Vector2(480,270);viewer.size_flags_horizontal=Control.SIZE_EXPAND_FILL;box.add_child(viewer)
	scrub=app.spin(box,"Preview source-local frame",0,candidate.duration-1,0);scrub.value_changed.connect(show_frame);show_frame(0)
	preview.confirmed.connect(commit);preview.canceled.connect(cancel);preview.close_requested.connect(cancel);preview.popup_centered(Vector2i(520,400))
func show_frame(value: float) -> void:
	for cel in decoded:
		if at+int(value)>=cel.start and at+int(value)<cel.start+cel.duration:viewer.show_image(cel.image);return
func commit() -> void:
	if phase!="candidate" or not valid() or external_busy():fail("The scene changed. Review artwork again before adding it.");return
	var original:=FileAccess.open(source,FileAccess.READ)
	if original==null or original.get_length()>192*1024*1024:fail("Original artwork is missing or exceeds its limit.");return
	original.close()
	if FileAccess.get_sha256(source)!=inventory.get("source_sha256"):fail("Original artwork changed. Import it again.");return
	var bytes:=0
	for cel in decoded:bytes+=cel.image.get_data_size()
	if decoded.size()>slots() or bytes>256*1024*1024:fail("Prepared artwork exceeds available drawing resources.");return
	var before: Array=app.layers.duplicate();var selected: String=app.layers[app.active_layer].id
	var layer:={"id":str(ResourceUID.create_id()),"name":app.layer_editor.unique_name(source.get_file().get_basename().left(60)),"visible":true,"cels":decoded,"origin":candidate.origin.duplicate(true)}
	# Disarm stale guards before changed() advances the revision.
	phase="";decoded=[];candidate={};close_dialogs();app.layers.append(layer);app.active_layer=app.layers.size()-1
	app.layer_editor.structure(before,selected,bytes);app.message("Krita artwork added as an editable drawing layer. Undo removes this import.")
func _exit_tree() -> void:
	if pid>0:
		var flag:=FileAccess.open(job.path_join("cancel"),FileAccess.WRITE)
		if flag:flag.store_string("cancel");flag.close()

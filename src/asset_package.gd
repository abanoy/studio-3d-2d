extends RefCounted
# Existing .has container; one complete independent authored model/map record.
const FORMAT="studio_asset_package_1"
const World=preload("res://src/world_document.gd")
const Model=World.Model
static func snapshot(app) -> Dictionary:
	var rig=app.renderer.active_model()
	if rig==null or not app.renderer.world_runtime:return {"error":"Select a model or map in the World tree first."}
	var row: Dictionary=rig.data.duplicate(true)
	if row.get("kind") not in ["model","environment"] or not str(row.get("parent_id","")).is_empty():return {"error":"Asset packages need an independent model or map. Select an ungrouped asset."}
	if row.name.is_empty() or row.name.length()>200:return {"error":"Give the asset a name of1–200characters before packaging."}
	var world:=World.empty();world.objects=[row]
	var why:=World.validate(world,int(app.video.duration_frames))
	if not why.is_empty():return {"error":why}
	return {"header":{"format":FORMAT,"kind":row.kind,"name":row.name},"project":{"video":app.video.duplicate(true),"camera_keys":[Model.Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)],"layers":[],"world":world,"source":"","model":{},"audio":{},"palette":[],"sequence_graph":{},"sequence_context":{},"reference_sheet":{},"editor":{"frame":0}}}
static func import_into(app,data: Dictionary,header: Dictionary,expected_kind: String,package_path: String,at_frame: int) -> String:
	if header.get("format")!=FORMAT or header.get("kind")!=expected_kind:return "Choose a matching model/map asset package; ordinary scene HAS files open through Open project."
	if not data.get("world",{}).get("objects") is Array or data.world.objects.size()!=1 or not data.layers.is_empty() or not data.audio.is_empty() or not data.get("sequence_graph",{}).is_empty():return "Asset package contains unrelated scene data."
	var row: Dictionary=data.world.objects[0].duplicate(true)
	if row.get("kind")!=expected_kind or not row.get("parent_id","").is_empty():return "Asset package has an invalid model/map root."
	var static_asset: bool=row.get("format")=="studio_model_1" and row.pose_keys.is_empty()
	if at_frame!=0 and not static_asset:return "Move the playhead to frame0 before adding an animated package. Its authored frame timing will be preserved."
	if static_asset:row.start_frame=at_frame;row.draft_frame=at_frame
	if not static_asset and data.video.fps_num*app.video.fps_den!=app.video.fps_num*data.video.fps_den:return "Match this scene's frame rate to the asset package before importing its authored timing."
	row.id=str(ResourceUID.create_id())
	var original_metadata: Dictionary=row.metadata.duplicate(true)
	row.metadata["has_asset_package"]={"format":FORMAT,"file":package_path,"source_sha256":row.sha256,"original_import_source":str(original_metadata.get("import_source",""))}
	var why:=Model.validate(row,int(app.video.duration_frames))
	if not why.is_empty():return "Asset timing does not fit this scene. Extend its length before importing. "+why
	return app.append_object_data(row,expected_kind,int(row.start_frame))
static func export_dialog(app) -> void:
	if app.import_actions.busy():app.message("Finish the current operation first.");return
	var selected:=snapshot(app)
	if selected.has("error"):app.message(selected.error);return
	var dialog:=FileDialog.new();dialog.title="Save selected asset as .has";dialog.access=FileDialog.ACCESS_FILESYSTEM;dialog.file_mode=FileDialog.FILE_MODE_SAVE_FILE;dialog.filters=PackedStringArray(["*.has ; HAS model or map asset package"]);dialog.current_file="Asset.has"
	dialog.file_selected.connect(func(path):dialog.hide();dialog.queue_free();app.has_project.save_asset(path))
	dialog.canceled.connect(dialog.queue_free);app.add_child(dialog);dialog.popup_centered_ratio(.75)

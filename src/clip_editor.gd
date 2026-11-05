extends Node
const Clips=preload("res://src/animation_clips.gd")
const Shapes=preload("res://src/shape_animation.gd")
const Shape=preload("res://src/source_shape.gd")
const Contact=preload("res://src/contact_clipboard.gd")
const Components=preload("res://src/root_component_document.gd")
var app
var clipboard:={}

func commit(data: Dictionary, text: String) -> String:
	var view: Dictionary=app.renderer.view_state()
	var rig: RefCounted=app.renderer.world_runtime.instance(data.id)
	if Contact.Model.is_contact(data) or not app.pose_editor.contacts.affected(rig).is_empty():
		var validation:=Contact.validate_candidate(rig,data,int(app.video.duration_frames))
		if not validation.is_empty():app.message(validation);return validation
		var world: Dictionary=app.current_world()
		for i in range(world.objects.size()):
			if world.objects[i].id==data.id:world.objects[i]=data
		if app.pose_editor.contacts.metadata_bytes(world)>1024*1024:
			var message:="This edit exceeds the1MiB project metadata limit. Use fewer animation pieces.";app.message(message);return message
	var error: String=app.pose_editor.restore_state(data)
	if not error.is_empty():app.message(error);return error
	app.set_frame(app.frame);app.renderer.restore_view(view)
	app.message(text)
	return ""

func move_piece(id: String, piece_id: String, start: int, before: Dictionary) -> void:
	if app.exporting or not app.renderer.world_runtime:return
	var rig: RefCounted=app.renderer.world_runtime.instance(id)
	if not rig or JSON.stringify(rig.data)!=JSON.stringify(before):app.message("The object changed while dragging. Try moving the piece again.");return
	if not app.pose_editor.contacts.affected(rig).is_empty() and app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before moving planted animation.");return
	var result:=Components.edit_clip(rig.data,"move",piece_id,start,int(app.video.duration_frames)) if rig.data.get("format")==Components.FORMAT else Clips.move(rig.data,piece_id,start,int(app.video.duration_frames))
	if result.has("error"):app.message(result.error);return
	commit(result.data,"Animation piece moved with its original motion. Undo restores it.")

func request(action: String, id: String, piece_id: String, frame: int) -> void:
	if app.exporting or not app.renderer.world_runtime:return
	var rig: RefCounted=app.renderer.world_runtime.instance(id)
	if not rig:app.message("Choose an object's animation row first.");return
	if action!="copy" and (not app.pose_editor.contacts.affected(rig).is_empty() or action=="paste" and clipboard.get("piece",{}).has("foot_contacts")) and app.pose_editor.contacts.live_busy():app.message("Turn Physics and Hair & clothes off before editing planted animation.");return
	app.stop();app.pose_editor.finish_drag();app.finish_stroke();app.world_selection.select_entity(id)
	var data:=Clips.promote(rig.data)
	if piece_id.is_empty() and not Clips.has_pieces(rig.data):piece_id=data.animation_clips[0].id
	var result:={}
	if action=="split":result=Components.edit_clip(data,"split","",frame,int(app.video.duration_frames)) if data.get("format")==Components.FORMAT else Clips.split(data,frame)
	elif action=="paste":
		if clipboard.is_empty():app.message("Copy or cut an animation piece first.");return
		if clipboard.sha256!=rig.data.sha256:app.message("Paste onto an instance of the same model so its bones match.");return
		if int(clipboard.fps_num)*int(app.video.fps_den)!=int(app.video.fps_num)*int(clipboard.fps_den):app.message("Paste this animation into a project with the same frame rate.");return
		if clipboard.has("shape_base"):
			data=Shapes.promote(data)
			if not data.has("shape_names"):data["shape_names"]={}
			for row in rig.root.get_meta(Shape.META).rows:
				var node:=str(row.node)
				if not clipboard.shape_base.has(node):continue
				if not data.shape_base.has(node):data.shape_base[node]={}
				if not data.shape_starts.has(node):data.shape_starts[node]={}
				var inherited:=Shape.effective(row,Shape.setting(data))
				for index in clipboard.shape_base[node]:
					if not data.shape_base[node].has(index):data.shape_base[node][index]=inherited[int(index)]
					if not data.shape_starts[node].has(index):data.shape_starts[node][index]=int(data.start_frame)
					if not data.shape_names.has(node):data.shape_names[node]={}
					data.shape_names[node][index]=str(row.names[int(index)]).left(200)
		var piece: Dictionary=clipboard.piece.duplicate(true)
		if clipboard.has("root_components") and data.get("format")!=Components.FORMAT:
			var promoted:=Components.promote(data,int(app.video.duration_frames))
			if promoted.has("error"):app.message(promoted.error);return
			data=promoted.data
		if piece.has("body_controls") or Contact.Model.is_body(data):
			var body=load("res://src/body_animation.gd");data=body.promote(data,int(app.video.duration_frames))
			if data.has("error"):app.message(data.error);return
			var prior_parts: Array=body.B.known_channels(body.view(data))
			if not piece.has("body_controls"):body.prepare_take(data,piece)
			for part in piece.body_legacy_channels+piece.body_controls.keys():
				if not part in prior_parts:data.body_starts[part]=int(data.start_frame)
		if piece.has("foot_contacts"):
			data=Contact.Contact.promote(data,int(app.video.duration_frames))
			if data.has("error"):app.message(data.error);return
		result=Components.paste_clip(data,piece,clipboard.get("root_components",{}),frame,int(app.video.duration_frames)) if data.get("format")==Components.FORMAT else Clips.paste(data,piece,frame,int(app.video.duration_frames))
		if not result.has("error") and Contact.has_contacts(piece):
			if not clipboard.get("contact_anchor") is Transform3D:app.message("Copy this planted animation again to include its placement context.");return
			var validation:=Components.validate(result.data,int(app.video.duration_frames)) if result.data.get("format")==Components.FORMAT else Contact.Model.validate(result.data,int(app.video.duration_frames))
			if not validation.is_empty():app.message(validation);return
			var owner=clipboard.get("contact_owner")
			# Identity can move once, while the original cut block is still absent.
			# Undo can restore it without changing the clipboard; that is a copy.
			var preserve: bool=clipboard.get("contact_cut",false) and owner is WeakRef and owner.get_ref()==rig.root and Clips.index_id(data,str(piece.id))<0
			var mapped:=Contact.reanchor(piece,clipboard.contact_anchor,Contact.anchor(rig,result.data,frame),preserve)
			if mapped.has("error"):app.message(mapped.error);return
			result.data.animation_clips[Clips.index_id(result.data,result.clip_id)].foot_contacts=mapped.piece.foot_contacts
		if not result.has("error") and clipboard.has("helper_edits"):
			var pasted:=paste_helper_edits(result.data,result.clip_id,int(app.video.duration_frames))
			if pasted.has("error"):app.message(pasted.error);return
			result.data=pasted.data
	else:
		var index:=Clips.index_id(data,piece_id)
		if index<0:app.message("Right-click an animation block to choose its piece.");return
		var copied:={"sha256":rig.data.sha256,"fps_num":int(app.video.fps_num),"fps_den":int(app.video.fps_den),"piece":data.animation_clips[index].duplicate(true)}
		var settings: Dictionary=data.get("motion_assist",{})
		var owned:=remap_source_helpers(settings.get("track_helper_edits",{}),piece_id,piece_id)
		if not owned.is_empty():
			copied["helper_edits"]=owned
			copied["component_helpers"]=data.get("format")==Components.FORMAT
		if data.get("format")==Components.FORMAT:copied["root_components"]=data.root_components.get(piece_id,{}).duplicate(true)
		if Contact.has_contacts(copied.piece):
			copied["contact_anchor"]=Contact.anchor(rig,data,float(copied.piece.start));copied["contact_owner"]=weakref(rig.root);copied["contact_cut"]=action=="cut"
		if Shapes.has_data(data):
			var expression_data:=Shapes.promote(data)
			copied.piece=expression_data.animation_clips[index].duplicate(true)
			copied["shape_base"]=expression_data.shape_base.duplicate(true)
			copied.piece["base_shapes"]=Shapes.fill(copied.piece.get("base_shapes",{}),expression_data.shape_base)
		if Contact.Model.is_body(data):
			var body=load("res://src/body_animation.gd")
			for part in body.B.known_channels(body.view(data)):
				if part!="@root" and not copied.piece.base_pose.has(part):copied.piece.base_pose[part]=body.B.base_value(body.view(data),part).duplicate(true)
		if action=="copy":
			clipboard=copied;app.refresh_timeline();app.message("Animation piece copied. Right-click a free space on this model's row to paste.");return
		if action not in ["cut","delete"]:return
		result=Components.edit_clip(data,"remove",piece_id,0,int(app.video.duration_frames)) if data.get("format")==Components.FORMAT else Clips.remove(data,piece_id,int(app.video.duration_frames))
		if action=="cut" and not result.has("error"):
			if commit(result.data,"Animation piece cut. Paste it into a free space; Undo restores the cut.").is_empty():clipboard=copied;app.refresh_timeline()
			return
	if result.has("error"):app.message(result.error);return
	var error:=commit(result.data,"Animation piece "+("split without changing its motion." if action=="split" else "pasted with its source motion." if action=="paste" else "removed. Undo restores it."))
	if error.is_empty() and action=="paste" and clipboard.has("helper_edits") and not result.data.motion_assist.enabled:
		app.message("Clip pasted. Turn on Motion feeling for this model to use its saved helper adjustments.")
	# Clipboard content is reusable personal state, not part of project Undo.
	# Consume relocation only after a successful commit, including foreign Paste.
	if error.is_empty() and action=="paste" and clipboard.get("contact_cut",false):clipboard.contact_cut=false

# Gap tuning depends on neighboring clips. Transfer only source controls.
static func remap_source_helpers(edits: Dictionary,source: String,destination: String) -> Dictionary:
	var result:={}
	for part in edits:
		for address in edits[part]:
			var prefix: String=""
			if part=="@root":
				for component in ["position/","rotation_xyzw/"]:
					if address.begins_with(component):prefix=component;break
			var owner:=prefix+source+"/"
			if not address.begins_with(owner):continue
			if not result.has(part):result[part]={}
			result[part][prefix+destination+"/"+address.substr(owner.length())]=edits[part][address].duplicate(true)
	return result

func paste_helper_edits(data: Dictionary,id: String,duration: int) -> Dictionary:
	var copied:=remap_source_helpers(clipboard.helper_edits,clipboard.piece.id,id)
	if copied.has("@root") and data.format==Components.FORMAT and not clipboard.component_helpers:
		var migration:=data.duplicate()
		migration["motion_assist"]={"track_helper_edits":copied}
		var error:=Components.migrate_root_helpers(migration)
		if not error.is_empty():return {"error":error}
	var settings: Dictionary=data.get("motion_assist",{})
	var merged: Dictionary=settings.get("track_helper_edits",{}).duplicate(true)
	for part in copied:
		if not merged.has(part):merged[part]={}
		merged[part].merge(copied[part])
	return Contact.Model.motion_animation().configure(data,settings.get("enabled",false),settings.get("strength",.65),duration,null,merged)

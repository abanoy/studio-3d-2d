extends Node
const Graph=preload("res://src/sequence_graph.gd")
const Runtime=preload("res://src/sequence_runtime.gd")
const NestedAudio=preload("res://src/sequence_audio.gd")
const Audio=preload("res://src/audio_track.gd")
const World=preload("res://src/world_document.gd")
var app
var graph: Dictionary={}
var root_document: Dictionary={}
var active_owner:=""
var navigation: Array=[]
var editor_states: Dictionary={}
var runtime: Node
var installing:=false
var preview_busy:=false
var preview_stamp:=""
var generation:=0
var selected_clip:=""
var clipboard: Dictionary={}
var toolbar: HFlowContainer
var breadcrumb: Label
var back: Button
var strip: Control
var strip_scroll: ScrollContainer
var panel: AcceptDialog
var panel_context: Dictionary={}

func setup(owner_app) -> void:
	app=owner_app
	var column: Node=app.timeline.get_parent().get_parent()
	toolbar=HFlowContainer.new();column.add_child(toolbar);column.move_child(toolbar,app.timeline_ruler.get_parent().get_index())
	app.button(toolbar,"Sequences…",show_panel)
	back=app.button(toolbar,"Back to parent",return_to_parent)
	breadcrumb=app.label(toolbar,"Main scene")
	strip_scroll=ScrollContainer.new();strip_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;strip_scroll.custom_minimum_size.y=56
	column.add_child(strip_scroll);column.move_child(strip_scroll,toolbar.get_index()+1)
	strip=preload("res://src/sequence_timeline.gd").new();strip.editor=self;strip.size_flags_horizontal=Control.SIZE_EXPAND_FILL;strip_scroll.add_child(strip)
	refresh()

func scene_snapshot() -> Dictionary:
	var world: Dictionary=app.current_world()
	return {"schema_version":5 if world.format==World.EFFECT_FORMAT else 4,"video":app.video.duplicate(true),"camera_keys":app.keys.duplicate(true),"layers":app.layers.duplicate(true),"world":world,"audio":app.audio_document().duplicate(true),"palette":app.palette.duplicate(true),"editor":{"frame":app.frame}}
func asset(id: String) -> Dictionary:
	for item in graph.get("assets",[]):
		if item.id==id:return item
	return {}
func clips() -> Array:
	return graph.get("clips",[]) if active_owner.is_empty() else asset(active_owner).get("clips",[])
func find_clip(id: String) -> Dictionary:
	for clip in clips():
		if clip.id==id:return clip
	return {}
func sync_current() -> void:
	if installing:return
	var scene:=scene_snapshot()
	if active_owner.is_empty():root_document=scene
	else:
		var current:=asset(active_owner)
		if not current.is_empty():
			# Keep the scene dictionary's identity across layout Undo/Redo. Its
			# parametric edits belong to the asset, not an individual placement.
			current.scene.clear();current.scene.merge(scene)
func project_snapshot() -> Dictionary:
	if graph.is_empty():
		return {"video":app.video,"camera_keys":app.keys,"layers":app.layers,"source":app.source,"model":app.renderer.model_state(),"world":app.renderer.world_state(),"audio":app.audio_document(),"palette":app.palette,"editor":{"frame":app.frame},"sequence_graph":{}}
	sync_current();var result:=root_document.duplicate();result["sequence_graph"]=graph
	result["sequence_context"]={} if active_owner.is_empty() else {"format":"studio_sequence_editor_1","asset_id":active_owner,"frame":app.frame}
	return result
func clone_graph(value: Variant=null) -> Dictionary:
	if value==null:value=graph
	if value.is_empty():return {"format":Graph.FORMAT,"assets":[],"clips":[]}
	var result:={"format":value.format,"assets":[],"clips":value.clips.duplicate(true)}
	for item in value.assets:result.assets.append({"id":item.id,"name":item.name,"clips":item.clips.duplicate(true),"scene":item.scene})
	return result
func proposed(scene: Dictionary,candidate: Variant=null) -> Dictionary:
	if candidate==null:candidate=graph
	var copy:=clone_graph(candidate);var root: Dictionary=scene if active_owner.is_empty() else root_document
	if not active_owner.is_empty():
		for item in copy.assets:
			if item.id==active_owner:item.scene=scene
	return {"graph":copy,"root":root}
func scene_error(world: Dictionary) -> String:
	if installing or graph.is_empty():return ""
	var scene:=scene_snapshot();scene.world=world
	var proposal:=proposed(scene)
	return Graph.error(proposal.graph,proposal.root)
func used(kind: String) -> int:
	var scenes: Array=[]
	if graph.is_empty():scenes=[scene_snapshot()]
	else:
		scenes.append(scene_snapshot() if active_owner.is_empty() else root_document)
		for item in graph.assets:scenes.append(scene_snapshot() if item.id==active_owner else item.scene)
	var count:=0
	for scene in scenes:
		if kind=="cels":
			for layer in scene.layers:count+=layer.cels.size()
		elif kind=="audio":count+=Audio.clips(scene.get("audio",{})).size()
		elif kind=="objects":count+=scene.world.objects.size()
	return count
func mix(audio: Dictionary,video: Dictionary) -> Dictionary:
	if graph.is_empty():return {} if audio.is_empty() else Audio.mix_document(audio,video)
	var scene:=scene_snapshot();scene.audio=audio;scene.video=video
	var proposal:=timing_proposal(scene);var built:=NestedAudio.build(proposal.graph,proposal.root)
	return built if built.has("error") else built.mixes.get(active_owner,{})
func timing_proposal(scene: Dictionary) -> Dictionary:
	var proposal:=proposed(scene)
	proposal.root=proposal.root.duplicate();proposal.root.video=proposal.root.video.duplicate(true)
	proposal.root.video.fps_num=scene.video.fps_num;proposal.root.video.fps_den=scene.video.fps_den
	for item in proposal.graph.assets:
		item.scene=item.scene.duplicate();item.scene.video=item.scene.video.duplicate(true)
		item.scene.video.fps_num=scene.video.fps_num;item.scene.video.fps_den=scene.video.fps_den
	return proposal
func prepare_timing(video: Dictionary) -> Dictionary:
	var timing_error:=preload("res://src/extended_timing.gd").video_error(video)
	if not timing_error.is_empty():return {"error":timing_error}
	if graph.is_empty():
		var mixed: Dictionary={} if app.audio_document().is_empty() else Audio.mix_document(app.audio_document(),video)
		return mixed if mixed.has("error") else {"runtime":null,"mix":mixed}
	var scene:=scene_snapshot();scene.video=video
	var proposal:=timing_proposal(scene)
	var parent_timing:=preload("res://src/extended_timing.gd").video_error(proposal.root.video)
	if not parent_timing.is_empty():return {"error":parent_timing}
	var why:=Graph.error(proposal.graph,proposal.root)
	if not why.is_empty():return {"error":why}
	var prepared:=prepare_runtime(proposal.graph,proposal.root,active_owner)
	if prepared.has("error"):return prepared
	prepared["plan"]=proposal;prepared["mix"]=prepared.runtime.audio_mixes.get(active_owner,{})
	return prepared
func install_timing(prepared: Dictionary) -> void:
	if graph.is_empty():return
	var proposal: Dictionary=prepared.plan;root_document.video=proposal.root.video
	for item in proposal.graph.assets:
		var current:=asset(item.id)
		if not current.is_empty():current.scene.video=item.scene.video
	install_runtime(prepared.runtime)
func ready_for_edit() -> bool:
	if app.exporting or app.source_import.pid>0 or app.has_project.pid>0 or app.audio_importer.pid>0 or app.physics_editor.recording.active:return false
	for importer in [app.raster_importer,app.video_importer]:
		if importer and not importer.phase.is_empty():return false
	return not app.playing and not app.drawing and not app.pose_editor.dragging
func prepare_runtime(candidate: Dictionary,root: Dictionary,owner: String="") -> Dictionary:
	if candidate.is_empty():return {"runtime":null}
	var next:=Runtime.new();add_child(next)
	var error:=next.prepare(candidate,root,owner)
	if not error.is_empty():next.free();return {"error":error}
	return {"runtime":next}
func install_runtime(next: Node) -> void:
	var previous: Node=runtime;runtime=next
	app.renderer.sequence_runtime=runtime;app.renderer.sequence_owner=active_owner
	app.canvas.sequence_overlay=null;preview_stamp="";generation+=1
	if previous and previous!=runtime:previous.shutdown()
	if runtime:app.audio_mix=runtime.audio_mixes.get(active_owner,{})
	refresh()
func clear() -> void:
	graph={};root_document={};active_owner="";navigation=[];editor_states={};selected_clip=""
	install_runtime(null)
func finish() -> void:
	# Stop new preview jobs, then let every owned in-flight coroutine unwind while
	# the tree still supplies draw/process boundaries. Freeing it mid-await leaks
	# a GDScriptFunctionState even when its rendering nodes themselves are freed.
	set_process(false)
	for child in get_children():
		if child is Runtime:child.cancelled=true
	while true:
		var waiting:=preview_busy
		for child in get_children():
			if child is Runtime and child.requests>0:waiting=true
		if not waiting:return
		await get_tree().process_frame
func adopt(document: Dictionary,prepared: Node) -> void:
	clear();graph=document.get("sequence_graph",{});root_document=document
	install_runtime(prepared)
func commit(candidate: Dictionary,history:=true) -> String:
	if not ready_for_edit():return "Finish the current edit, import or recording first."
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();sync_current()
	var empty: bool=candidate.get("assets",[]).is_empty() and candidate.get("clips",[]).is_empty() and active_owner.is_empty()
	var why: String="" if empty else Graph.error(candidate,root_document)
	if not why.is_empty():return why
	var prepared: Dictionary={"runtime":null} if empty else prepare_runtime(candidate,root_document,active_owner)
	if prepared.has("error"):return prepared.error
	var before:=clone_graph();graph={} if empty else candidate
	install_runtime(prepared.runtime)
	if empty:app.rebuild_audio()
	if history:
		var bytes: int=(JSON.stringify(before).to_utf8_buffer().size()+JSON.stringify(candidate).to_utf8_buffer().size())*2
		app.push_history({"type":"sequence_graph","before":before,"after":clone_graph(),"bytes":bytes})
	app.changed();app.refresh_audio_controls();app.refresh_timeline();return ""
func restore(candidate: Dictionary) -> String:
	if candidate.get("assets",[]).is_empty():
		if not active_owner.is_empty():return "Return to the main scene before removing this asset."
		graph={};install_runtime(null);app.rebuild_audio();return ""
	return commit(clone_graph(candidate),false)
func default_clip(id: String,start: int,duration: int) -> Dictionary:
	var clip:={"id":str(ResourceUID.create_id()),"asset_id":id,"start":start,"duration":duration,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0.0,"keys":[Graph.key()]}
	if graph.get("format") in [Graph.SHADOW_FORMAT,Graph.MASK_FORMAT]:clip["shadow"]={}
	if graph.get("format")==Graph.MASK_FORMAT:clip["mask"]={}
	return clip
func promote_shadows(candidate: Dictionary) -> void:
	if candidate.format!=Graph.MASK_FORMAT:candidate.format=Graph.SHADOW_FORMAT
	var owners: Array=[{"clips":candidate.clips}];owners.append_array(candidate.assets)
	for owner in owners:
		for clip in owner.clips:
			if not clip.has("shadow"):clip["shadow"]={}
func promote_masks(candidate: Dictionary) -> void:
	promote_shadows(candidate);candidate.format=Graph.MASK_FORMAT
	var owners: Array=[{"clips":candidate.clips}];owners.append_array(candidate.assets)
	for owner in owners:
		for clip in owner.clips:
			if not clip.has("mask"):clip["mask"]={}
func change_mask(id: String,mask: Dictionary) -> String:
	var why:=Graph.mask_error(mask)
	if not why.is_empty():return why
	var current:=find_clip(id)
	if current.is_empty():return "This sequence clip is no longer available."
	var previous: Dictionary=current.get("mask",{})
	if previous.is_empty() and mask.is_empty():return ""
	if not previous.is_empty() and not mask.is_empty() and previous.invert==mask.invert:
		var a: Array=previous.rect;var b: Array=mask.rect
		if Rect2i(a[0],a[1],a[2],a[3])==Rect2i(b[0],b[1],b[2],b[3]):return ""
	var candidate:=clone_graph();promote_masks(candidate)
	for clip in owner_clips(candidate):
		if clip.id==id:clip.mask=mask.duplicate(true);return commit(candidate)
	return "This sequence clip is no longer available."
func change_shadow(id: String,style: Dictionary) -> String:
	var why:=Graph.shadow_error(style)
	if not why.is_empty():return why
	var current:=find_clip(id)
	if current.is_empty():return "This sequence clip is no longer available."
	if current.get("shadow",{})==style:return ""
	var candidate:=clone_graph();promote_shadows(candidate)
	for clip in owner_clips(candidate):
		if clip.id==id:clip.shadow=style.duplicate(true);return commit(candidate)
	return "This sequence clip is no longer available."
func owner_clips(candidate: Dictionary) -> Array:
	if active_owner.is_empty():return candidate.clips
	for item in candidate.assets:
		if item.id==active_owner:return item.clips
	return []
func new_sequence(name: String="Sequence") -> String:
	if not ready_for_edit() or app.frame>=app.video.duration_frames:app.message("Choose an available frame and finish current operations first.");return ""
	sync_current();var candidate:=clone_graph()
	if candidate.assets.size()>=4:app.message("This project already has four editable sequence assets.");return ""
	var id:=str(ResourceUID.create_id());var scene:=scene_snapshot();scene.world=World.empty();scene.schema_version=4;scene.audio={};scene.palette=app.palette.duplicate(true);scene.editor={"frame":0};scene.layers=[]
	if scene.video.duration_frames>240:
		scene.video.duration_frames=240
		scene.camera_keys=scene.camera_keys.filter(func(key):return key.frame<=240)
		if scene.camera_keys.is_empty():
			var initial: Dictionary=app.keys[0].duplicate(true);initial.frame=0;scene.camera_keys=[initial]
	for title in ["Rough","Ink"]:scene.layers.append({"id":str(ResourceUID.create_id()),"name":title,"visible":true,"cels":[]})
	var used_name:=name.strip_edges()
	if used_name.is_empty():used_name="Sequence"
	candidate.assets.append({"id":id,"name":used_name,"scene":scene,"clips":[]})
	var clip:=default_clip(id,app.frame,mini(240,int(app.video.duration_frames)-app.frame));owner_clips(candidate).append(clip)
	var error:=commit(candidate)
	if not error.is_empty():app.message(error);return ""
	selected_clip=clip.id;app.message("Editable sequence created. Open it to animate its own scene, drawings and sound.");return id
func add_instance(id: String) -> String:
	var item:=asset(id)
	if item.is_empty() or app.frame>=app.video.duration_frames:return "Choose an asset and an available frame."
	var candidate:=clone_graph();var clip:=default_clip(id,app.frame,mini(int(item.scene.video.duration_frames),int(app.video.duration_frames)-app.frame))
	owner_clips(candidate).append(clip);var error:=commit(candidate)
	if error.is_empty():selected_clip=clip.id
	return error
func change_clip(id: String,values: Dictionary) -> String:
	var candidate:=clone_graph();var found:=false
	for clip in owner_clips(candidate):
		if clip.id==id:clip.merge(values,true);found=true
	return commit(candidate) if found else "This sequence clip is no longer available."
func remove_clip(id: String) -> String:
	var candidate:=clone_graph();var rows:=owner_clips(candidate)
	for i in range(rows.size()):
		if rows[i].id==id:rows.remove_at(i);return commit(candidate)
	return "This sequence clip is no longer available."
func placement_key(id: String,key: Dictionary) -> String:
	var clip:=find_clip(id)
	if clip.is_empty():return "Select a sequence clip."
	var keys: Array=clip.keys.duplicate(true);var found:=false
	for i in range(keys.size()):
		if keys[i].frame==key.frame:keys[i]=key;found=true
	if not found:keys.append(key)
	keys.sort_custom(func(a,b):return a.frame<b.frame)
	return change_clip(id,{"keys":keys})
func split_clip(id: String,frame: int) -> String:
	var original:=find_clip(id)
	if original.is_empty():return "Select a sequence clip."
	var cut:=frame-int(original.start)
	if cut<1 or cut>=original.duration:return "Choose a split frame inside this clip."
	var candidate:=clone_graph();var rows:=owner_clips(candidate)
	for i in range(rows.size()):
		if rows[i].id!=id:continue
		var left: Dictionary=rows[i];var right:=left.duplicate(true)
		left.duration=cut;right.id=str(ResourceUID.create_id());right.start+=cut;right.duration-=cut;right.time_in+=cut;right.key_in+=cut
		# Both pieces retain the original curve and exact audio epoch. Cropping
		# a window does not resample an ease curve or restart fractional loops.
		rows.insert(i+1,right);var error:=commit(candidate)
		if error.is_empty():selected_clip=right.id
		return error
	return "This clip changed before it could be split."
func copy_clip(id: String) -> String:
	var clip:=find_clip(id)
	if clip.is_empty():return "Select a sequence clip."
	clipboard=clip.duplicate(true);return ""
func paste_clip() -> String:
	if clipboard.is_empty() or asset(str(clipboard.get("asset_id",""))).is_empty():return "Copy a sequence instance from this project first."
	var clip:=clipboard.duplicate(true);clip.id=str(ResourceUID.create_id());clip.start=app.frame
	var candidate:=clone_graph();owner_clips(candidate).append(clip)
	if clip.has("mask"):promote_masks(candidate)
	elif candidate.format==Graph.MASK_FORMAT:clip["mask"]={}
	if clip.has("shadow"):promote_shadows(candidate)
	elif candidate.format in [Graph.SHADOW_FORMAT,Graph.MASK_FORMAT]:clip["shadow"]={}
	var error:=commit(candidate)
	if error.is_empty():selected_clip=clip.id
	return error
func rename_asset(id: String,name: String) -> String:
	var candidate:=clone_graph()
	for item in candidate.assets:
		if item.id==id:item.name=name.strip_edges();return commit(candidate)
	return "This sequence asset is no longer available."
func remove_asset(id: String) -> String:
	if id==active_owner or id in navigation:return "Return to the main scene before removing an open sequence or ancestor."
	var candidate:=clone_graph();var owners: Array=[{"clips":candidate.clips}];owners.append_array(candidate.assets)
	for owner in owners:
		if owner.get("id","")==id:continue
		for clip in owner.clips:
			if clip.asset_id==id:return "Remove this asset's clip instances before removing its definition."
	for i in range(candidate.assets.size()):
		if candidate.assets[i].id==id:candidate.assets.remove_at(i);return commit(candidate)
	return "This sequence asset is no longer available."
func save_editor() -> void:
	editor_states[active_owner]={"history":app.history,"redo":app.redo_history,"bytes":app.history_bytes,"frame":app.frame,"mode":app.mode.selected,"layer":app.active_layer,"selection":app.world_selection.selected,"bone":app.pose_editor.selected,"view":app.renderer.view_state()}
func switch_to(id: String,route: Array) -> String:
	if not ready_for_edit():return "Finish the current edit, import or recording first."
	if not id.is_empty() and asset(id).is_empty():return "Sequence asset is missing."
	if not app.physics_editor.freeze_all():return "Finish recording before opening a sequence."
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();sync_current()
	var scene: Dictionary=root_document if id.is_empty() else asset(id).scene
	var prepared: Dictionary=app.renderer.prepare_world(scene.world,int(scene.video.duration_frames))
	if prepared.has("error"):return prepared.error
	var next:=prepare_runtime(graph,root_document,id)
	if next.has("error"):prepared.runtime.dispose();return next.error
	if app.tutorials:app.tutorials.document_changing()
	close_panel()
	save_editor();installing=true;app.physics_editor.clear();app.world_selection.clear()
	app.renderer.install_world(prepared);active_owner=id;navigation=route
	app.video=scene.video.duplicate(true);app.keys=scene.camera_keys.duplicate(true);app.layers=scene.layers.duplicate(true)
	if app.layers.is_empty():
		for title in ["Rough","Ink"]:app.layers.append({"id":str(ResourceUID.create_id()),"name":title,"visible":true,"cels":[]})
	app.audio_clip=scene.get("audio",{});app.palette=scene.get("palette",[]).duplicate(true);app.palette_editor.refresh(true)
	app.source="";app.renderer.set_background(str(app.video.get("world_background","black")))
	var state: Dictionary=editor_states.get(id,{})
	app.history=state.get("history",[]);app.redo_history=state.get("redo",[]);app.history_bytes=state.get("bytes",0)
	app.active_layer=clampi(int(state.get("layer",1)),0,app.layers.size()-1);app.refresh_layer_choices()
	app.pose_editor.rebuild_tree();app.world_selection.refresh()
	if not str(state.get("selection","")).is_empty():app.world_selection.select_entity(state.selection,false)
	var rig: RefCounted=app.renderer.active_model()
	app.pose_editor.selected=state.get("bone","@root") if rig and (state.get("bone","@root")=="@root" or rig.bones.has(state.get("bone","@root"))) else "@root"
	app.pose_editor.refresh_values()
	app.mode.select(int(state.get("mode",0)));app.refresh_workspace()
	app.recovery_revision+=1;app.set_frame(int(state.get("frame",scene.get("editor",{}).get("frame",0))))
	if state.has("view"):app.renderer.restore_view(state.view)
	installing=false;install_runtime(next.runtime);app.refresh_scene_name();app.refresh_audio_controls();return ""
func restore_context(value: Dictionary) -> String:
	if value.is_empty():return ""
	var error:=Graph.context_error(value,graph)
	if not error.is_empty():return error
	error=enter(value.asset_id)
	if error.is_empty():app.set_frame(int(value.frame))
	return error
func trim_history() -> void:
	if graph.is_empty() and editor_states.is_empty():return
	var contexts: Array=[]
	for id in editor_states:
		if id!=active_owner:contexts.append(editor_states[id])
	var current:={"history":app.history,"redo":app.redo_history,"bytes":app.history_bytes}
	contexts.append(current)
	var live:={};var live_pcm:={};var scenes: Array=[scene_snapshot() if active_owner.is_empty() else root_document]
	for item in graph.get("assets",[]):scenes.append(scene_snapshot() if item.id==active_owner else item.scene)
	for scene in scenes:
		for layer in scene.layers:
			for cel in layer.cels:live[cel.image.get_instance_id()]=true
		for clip in Audio.clips(scene.get("audio",{})):live_pcm[clip.source.sha256]=true
	for context in contexts:
		for command in context.history+context.redo:
			if command.type!="sequence_graph":continue
			if not command.has("sequence_metadata_bytes"):command["sequence_metadata_bytes"]=int(command.get("bytes",0))
			command.bytes=command.sequence_metadata_bytes;var seen:={};var seen_pcm:={}
			for side in ["before","after"]:
				for item in command[side].get("assets",[]):
					for layer in item.scene.layers:
						for cel in layer.cels:
							var id: int=cel.image.get_instance_id()
							if not live.has(id) and not seen.has(id):seen[id]=true;command.bytes+=cel.image.get_data_size()
					for clip in Audio.clips(item.scene.get("audio",{})):
						if not live_pcm.has(clip.source.sha256) and not seen_pcm.has(clip.source.sha256):seen_pcm[clip.source.sha256]=true;command.bytes+=clip.source.pcm.size()
	var total:=0;var count:=0
	for context in contexts:
		for command in context.history+context.redo:total+=int(command.get("bytes",0));count+=1
	while (total>64*1024*1024 or count>128) and count>1:
		var selected: Dictionary={};var selected_redo:=false;var oldest:=9223372036854775807
		for context in contexts:
			for side in ["history","redo"]:
				if context[side].is_empty():continue
				var command: Dictionary=context[side][0 if side=="history" else context[side].size()-1]
				var stamp: int=command.get("sequence_stamp",0)
				if stamp<oldest:oldest=stamp;selected=context;selected_redo=side=="redo"
		if selected.is_empty():break
		if selected_redo:
			for command in selected.redo:total-=int(command.get("bytes",0));count-=1
			selected.redo.clear()
		else:
			var command: Dictionary=selected.history.pop_front();total-=int(command.get("bytes",0));count-=1
	for context in contexts:
		context.bytes=0
		for command in context.history:context.bytes+=int(command.get("bytes",0))
	app.history_bytes=current.bytes
	# A retired editor is retained only while its asset can actually be restored.
	var retained:={}
	for item in graph.get("assets",[]):retained[item.id]=true
	for context in contexts:
		for command in context.history+context.redo:
			if command.type!="sequence_graph":continue
			for side in ["before","after"]:
				for item in command[side].get("assets",[]):retained[item.id]=true
	for id in editor_states.keys():
		if not id.is_empty() and id!=active_owner and not retained.has(id):editor_states.erase(id)
func enter(id: String) -> String:
	if id==active_owner:return ""
	if navigation.size()>=16:return "Return to a parent scene before opening more sequence editors."
	var route:=navigation.duplicate();route.append(active_owner)
	return switch_to(id,route)
func return_to_parent() -> void:
	if navigation.is_empty():return
	var route:=navigation.duplicate();var id: String=route.pop_back();var why:=switch_to(id,route)
	if not why.is_empty():app.message(why)
func refresh() -> void:
	if not is_instance_valid(toolbar):return
	back.visible=not active_owner.is_empty()
	breadcrumb.text="Main scene" if active_owner.is_empty() else "Editing sequence: "+str(asset(active_owner).get("name","Sequence"))
	strip_scroll.visible=not clips().is_empty();strip.custom_minimum_size.y=maxi(26,clips().size()*26);strip.queue_redraw()
func _process(_delta: float) -> void:
	if not is_instance_valid(toolbar):return
	back.disabled=not ready_for_edit();strip.queue_redraw()
	if not runtime or app.exporting or preview_busy:return
	var stamp:="%d:%s:%d" % [generation,active_owner,app.frame]
	if stamp==preview_stamp:return
	preview_stamp=stamp;preview_busy=true
	var context:=generation;var owner:=active_owner;var frame: int=app.frame;var current: Node=runtime
	var image: Image=await current.render(owner,frame,false)
	if context==generation and owner==active_owner and frame==app.frame and image:
		app.canvas.sequence_overlay=ImageTexture.create_from_image(image);app.canvas.queue_redraw()
	preview_busy=false

func panel_valid() -> bool:
	return panel_context.get("session")==app.recovery_session and panel_context.get("owner")==active_owner and panel_context.get("revision")==app.recovery_revision
func close_panel() -> void:
	if is_instance_valid(panel):panel.hide();panel.queue_free()
	panel=null
func show_panel() -> void:
	if not ready_for_edit():app.message("Finish current operations before editing sequences.");return
	close_panel();sync_current();panel_context={"session":app.recovery_session,"owner":active_owner,"revision":app.recovery_revision}
	panel=AcceptDialog.new();panel.title="Editable sequences";panel.exclusive=false;panel.ok_button_text="Close";app.add_child(panel)
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(580,490);panel.add_child(scroll)
	var box:=VBoxContainer.new();box.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(box)
	var note: Label=app.label(box,"Reuse an editable child scene. Its camera, poses, drawings and sound stay independent.\nChild backgrounds composite transparently; add a map or artwork for a visible background.")
	note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;note.custom_minimum_size.x=540
	var name:=LineEdit.new();name.placeholder_text="New sequence name";name.text="Sequence %d" % (graph.get("assets",[]).size()+1);box.add_child(name)
	app.button(box,"New sequence and edit…",func():
		if not panel_valid():app.message("The scene changed. Reopen Sequences to review it.");return
		var id:=new_sequence(name.text)
		if not id.is_empty():close_panel();var why:=enter(id);if not why.is_empty():app.message(why))
	var assets:=OptionButton.new();box.add_child(assets)
	for item in graph.get("assets",[]):assets.add_item(item.name);assets.set_item_metadata(assets.item_count-1,item.id)
	app.button(box,"Add selected sequence at playhead",func():
		if not panel_valid() or assets.selected<0:app.message("Choose an asset in the current scene.");return
		var why:=add_instance(str(assets.get_item_metadata(assets.selected)))
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	app.button(box,"Edit selected sequence…",func():
		if not panel_valid() or assets.selected<0:return
		var id:=str(assets.get_item_metadata(assets.selected));close_panel();var why:=enter(id);if not why.is_empty():app.message(why))
	app.button(box,"Rename selected sequence",func():
		if not panel_valid() or assets.selected<0:return
		var why:=rename_asset(str(assets.get_item_metadata(assets.selected)),name.text)
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	app.button(box,"Remove unused sequence definition",func():
		if not panel_valid() or assets.selected<0:return
		var why:=remove_asset(str(assets.get_item_metadata(assets.selected)))
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	var selection:=OptionButton.new();box.add_child(selection)
	for clip in clips():
		selection.add_item("%s · frames %d–%d" % [asset(clip.asset_id).name,clip.start,clip.start+clip.duration-1]);selection.set_item_metadata(selection.item_count-1,clip.id)
		if clip.id==selected_clip:selection.select(selection.item_count-1)
	if not clips().is_empty():
		selected_clip=str(selection.get_item_metadata(maxi(0,selection.selected)))
		selection.item_selected.connect(func(index):selected_clip=str(selection.get_item_metadata(index));close_panel();show_panel())
		add_clip_controls(box,find_clip(selected_clip))
	panel.confirmed.connect(close_panel);panel.close_requested.connect(close_panel);panel.popup_centered()
func add_clip_controls(box: VBoxContainer,clip: Dictionary) -> void:
	var id: String=clip.id
	app.button(box,"Split clip at playhead",func():
		if not panel_valid():return
		var why:=split_clip(id,app.frame)
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	app.button(box,"Copy sequence clip",func():var why:=copy_clip(id);app.message("Sequence clip copied." if why.is_empty() else why))
	app.button(box,"Paste copied clip at playhead",func():
		if not panel_valid():return
		var why:=paste_clip()
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	var start: SpinBox=app.spin(box,"Parent start frame",0,app.video.duration_frames-1,clip.start)
	var duration: SpinBox=app.spin(box,"Clip length (frames)",1,app.video.duration_frames,clip.duration)
	var source_in: SpinBox=app.spin(box,"Child in frame",0,asset(clip.asset_id).scene.video.duration_frames-1,(int(clip.source_in)+int(clip.time_in))%int(asset(clip.asset_id).scene.video.duration_frames))
	var loop:=CheckButton.new();loop.text="Loop child sequence";loop.button_pressed=clip.loop;box.add_child(loop)
	var visible:=CheckButton.new();visible.text="Show picture";visible.button_pressed=clip.visible;box.add_child(visible)
	var muted:=CheckButton.new();muted.text="Mute child sound";muted.button_pressed=clip.muted;box.add_child(muted)
	var gain: SpinBox=app.spin(box,"Child sound gain (dB)",-60,12,clip.gain_db);gain.step=.01;gain.value=clip.gain_db
	var displayed_gain:=gain.value
	app.button(box,"Apply clip timing and sound",func():
		if not panel_valid():app.message("The scene changed. Reopen Sequences.");return
		for field in [start,duration,source_in,gain]:field.apply()
		var why:=change_clip(id,{"start":int(start.value),"duration":int(duration.value),"source_in":int(source_in.value) if int(source_in.value)!=(int(clip.source_in)+int(clip.time_in))%int(asset(clip.asset_id).scene.video.duration_frames) else clip.source_in,"time_in":0 if int(source_in.value)!=(int(clip.source_in)+int(clip.time_in))%int(asset(clip.asset_id).scene.video.duration_frames) else clip.time_in,"loop":loop.button_pressed,"visible":visible.button_pressed,"muted":muted.button_pressed,"gain_db":gain.value if gain.value!=displayed_gain else clip.gain_db})
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	var at:=clampi(app.frame-int(clip.start),0,int(clip.duration));var p:=Graph.placement(clip,int(clip.start)+at)
	app.label(box,"Placement keys are local to this clip; repeated instances keep their own placement.")
	var time: SpinBox=app.spin(box,"Placement key frame",0,clip.duration,at)
	var x: SpinBox=app.spin(box,"Horizontal offset (pixels)",-19200,19200,p.offset.x);x.step=.01;x.value=p.offset.x
	var y: SpinBox=app.spin(box,"Vertical offset (pixels)",-19200,19200,p.offset.y);y.step=.01;y.value=p.offset.y
	var scale: SpinBox=app.spin(box,"Picture scale",.01,8,p.scale);scale.step=.001;scale.value=p.scale
	var rotation: SpinBox=app.spin(box,"Picture rotation (degrees)",-36000,36000,p.rotation);rotation.step=.01;rotation.value=p.rotation
	var opacity: SpinBox=app.spin(box,"Picture opacity (%)",0,100,p.opacity*100);opacity.step=.01;opacity.value=p.opacity*100
	var interpolation:=OptionButton.new();box.add_child(interpolation)
	for label in ["linear","hold","ease"]:interpolation.add_item(label)
	app.button(box,"Save placement key",func():
		if not panel_valid():app.message("The scene changed. Reopen Sequences.");return
		for field in [time,x,y,scale,rotation,opacity]:field.apply()
		var why:=placement_key(id,{"frame":int(time.value)+int(clip.key_in),"offset":[x.value,y.value],"scale":scale.value,"rotation":rotation.value,"opacity":opacity.value/100,"interpolation":interpolation.get_item_text(interpolation.selected)})
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	var style: Dictionary=clip.get("shadow",{})
	var shadow_enabled:=CheckButton.new();shadow_enabled.text="Drop shadow";shadow_enabled.button_pressed=not style.is_empty();box.add_child(shadow_enabled)
	var offset: Array=style.get("offset",[12,12])
	var shadow_x: SpinBox=app.spin(box,"Shadow horizontal offset (pixels)",-2048,2048,offset[0])
	var shadow_y: SpinBox=app.spin(box,"Shadow vertical offset (pixels)",-2048,2048,offset[1])
	shadow_x.step=.01;shadow_x.value=offset[0];shadow_y.step=.01;shadow_y.value=offset[1]
	var softness: SpinBox=app.spin(box,"Shadow softness (pixels)",0,32,style.get("softness",4));softness.step=.1;softness.value=style.get("softness",4)
	var tint:=ColorPickerButton.new();var rgba: Array=style.get("color",[0,0,0,.5]);tint.color=Color(rgba[0],rgba[1],rgba[2],rgba[3]);tint.tooltip_text="Shadow color and opacity";box.add_child(tint)
	var shown_x:=shadow_x.value;var shown_y:=shadow_y.value;var shown_softness:=softness.value;var shown_color:=tint.color
	app.button(box,"Apply shadow",func():
		if not panel_valid():app.message("The scene changed. Reopen Sequences.");return
		for field in [shadow_x,shadow_y,softness]:field.apply()
		var color:=tint.color
		var why:=change_shadow(id,{"offset":[shadow_x.value if shadow_x.value!=shown_x else offset[0],shadow_y.value if shadow_y.value!=shown_y else offset[1]],"color":[color.r,color.g,color.b,color.a] if color!=shown_color else rgba,"softness":softness.value if softness.value!=shown_softness else style.get("softness",4)} if shadow_enabled.button_pressed else {})
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	var mask: Dictionary=clip.get("mask",{})
	var mask_enabled:=CheckButton.new();mask_enabled.text="Picture mask";mask_enabled.button_pressed=not mask.is_empty();box.add_child(mask_enabled)
	app.label(box,"Mask coordinates follow the child canvas before placement. Child artwork stays editable.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var rect: Array=mask.get("rect",[0,0,1920,1080])
	var mask_x: SpinBox=app.spin(box,"Mask left (pixels)",0,1919,rect[0])
	var mask_y: SpinBox=app.spin(box,"Mask top (pixels)",0,1079,rect[1])
	var mask_width: SpinBox=app.spin(box,"Mask width (pixels)",1,1920,rect[2])
	var mask_height: SpinBox=app.spin(box,"Mask height (pixels)",1,1080,rect[3])
	var inverted:=CheckButton.new();inverted.text="Cut out this rectangle instead";inverted.button_pressed=mask.get("invert",false);box.add_child(inverted)
	app.button(box,"Apply mask",func():
		if not panel_valid():app.message("The scene changed. Reopen Sequences.");return
		for field in [mask_x,mask_y,mask_width,mask_height]:field.apply()
		var why:=change_mask(id,{"rect":[int(mask_x.value),int(mask_y.value),int(mask_width.value),int(mask_height.value)],"invert":inverted.button_pressed} if mask_enabled.button_pressed else {})
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))
	app.button(box,"Remove selected clip",func():
		if not panel_valid():return
		var why:=remove_clip(id)
		if why.is_empty():close_panel();show_panel()
		else:app.message(why))

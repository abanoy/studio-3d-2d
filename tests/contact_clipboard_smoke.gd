extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Contact=preload("res://src/contact_clipboard.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const T=Model.Timeline
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Contact clipboard watchdog");quit(2));call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func actor(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func root_value(y: float) -> Dictionary:return {"position":[0,y,0],"rotation_xyzw":[0,0,0,1],"scale":1.}
func action(id: String,frame: int,command: int) -> void:
	app.world_selection.select_entity(id);app.refresh_timeline()
	var row:=-1
	for i in range(app.timeline.object_rows.size()):
		if app.timeline.object_rows[i].id==id:row=i
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_RIGHT;event.pressed=true
	event.position=Vector2(app.timeline.x(frame),app.timeline.row_y(row)+12);app.timeline._gui_input(event);await settled();app.timeline.import_menu.id_pressed.emit(command);await settled()
func endpoint_error(rig,piece: Dictionary,frame: int) -> float:
	app.renderer.world_runtime.evaluate(frame,false,"",app.video)
	var segment:=Ranges.Contact.Contacts.active([piece],frame);var peak:=0.
	for foot in segment.feet:peak=maxf(peak,rig.bone_transform(foot.ids[2]).origin.distance_to(T.vector(foot.position)))
	return peak
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	var empty:=folder.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var source:=World.object(asset);source.id="sender"
	var parent:=World.object(empty,"group","Receiver parent");parent.id="parent";parent.position=[5,0,0];parent.scale=1.3;var q:=Quaternion(Vector3.UP,.2);parent.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var receiver:=World.object(asset);receiver.id="receiver";receiver.parent_id=parent.id;receiver.position=[10,0,0]
	var world:=World.empty();world.objects=[source,parent,receiver];check(app.restore_world(world).is_empty(),"two instances and transformed parent install")
	var rig:=actor(source.id)
	for frame in [0,24]:
		var before: Dictionary=rig.data.duplicate(true)
		rig.put_pose_key({"frame":frame,"pose":{},"transform":root_value(0. if frame==0 else -.15),"authored_channels":["@root"],"interpolation":"ease"},48,false,before)
	app.set_frame(0);var track:=Ranges.Contact.Contacts.capture(rig,0,1,"original-pin")
	var planted:=Ranges.edit(rig.data,0,25,track.segments[0],48)
	app.renderer.world_runtime.restore_instance(source.id,planted.data);app.set_frame(0)
	var sender: Dictionary=rig.data.duplicate(true);var target: Dictionary=actor(receiver.id).data.duplicate(true);var view: Dictionary=app.renderer.view_state();var shots: Array=app.keys.duplicate(true)
	await action(source.id,0,11)
	check(app.clip_editor.clipboard.has("contact_anchor") and rig.data==sender,"actual timeline Copy retains immutable placement context")
	var copied: Dictionary=app.clip_editor.clipboard.piece.duplicate(true);var old_anchor: Transform3D=app.clip_editor.clipboard.contact_anchor
	var history: int=app.history.size();await action(receiver.id,24,13)
	rig=actor(receiver.id)
	check(rig.data.format==Model.CONTACT_FORMAT and rig.data.animation_clips.size()==2 and app.history.size()==history+1,"actual timeline Paste promotes receiver and installs one editable contact piece")
	if rig.data.format!=Model.CONTACT_FORMAT:app.free();quit(1);return
	var pasted: Dictionary=rig.data.animation_clips[-1];var new_anchor:=Contact.anchor(rig,rig.data,24);var delta:=new_anchor*old_anchor.affine_inverse()
	var mapped:=true
	for i in range(2):
		var foot: Dictionary=pasted.foot_contacts.segments[0].feet[i];var old_foot: Dictionary=copied.foot_contacts.segments[0].feet[i]
		mapped=mapped and T.vector(foot.position).distance_to(delta*T.vector(old_foot.position))<.000001 and absf(T.quaternion(foot.rotation_xyzw).dot(delta.basis.orthonormalized().get_rotation_quaternion()*T.quaternion(old_foot.rotation_xyzw)))>.999999
	check(mapped and pasted.foot_contacts.segments[0].id!=copied.foot_contacts.segments[0].id,"copy reanchors world pins and gives its independent contact a new identity")
	var ordinary_data:=Contact.Contact.Body.promote(target,48);var ordinary_piece:=copied.duplicate(true);ordinary_piece.erase("foot_contacts")
	ordinary_data=Model.Clips.paste(ordinary_data,ordinary_piece,24,48).data;var ordinary:=Model.new();ordinary.data=ordinary_data
	check(rig.sample_transform(12)==ordinary.sample_transform(12) and rig.sample_transform(24)==ordinary.sample_transform(24) and rig.data.body_base_transform==ordinary_data.body_base_transform,"contact paste preserves ordinary absolute root curves, receiving baseline and connecting gap")
	var peak:=0.
	for frame in range(24,49):peak=maxf(peak,endpoint_error(rig,pasted,frame))
	check(peak<.0002 and actor(source.id).data==sender and app.keys==shots and app.renderer.view_state()==view,"pasted parented animation holds both feet without changing source, shot keys or view")
	var saved_paste: Dictionary=rig.data.duplicate(true);app.undo();check(actor(receiver.id).data==target,"Paste Undo restores exact receiver and model version")
	app.redo();check(actor(receiver.id).data==saved_paste,"Paste Redo restores exact reanchored native parameters")
	# A missing placement context must not publish foreign fixed world targets.
	app.undo();app.clip_editor.clipboard.erase("contact_anchor");history=app.history.size();app.clip_editor.request("paste",receiver.id,"",24)
	check(actor(receiver.id).data==target and app.history.size()==history and app.status.text.contains("again"),"old/missing anchor context refuses without partial paste or history")
	app.clip_editor.clipboard.contact_anchor=Transform3D(Basis.from_scale(Vector3(2,1,1)),Vector3.ZERO);app.clip_editor.request("paste",receiver.id,"",24)
	check(actor(receiver.id).data==target and app.history.size()==history and app.status.text.contains("uniform"),"unsupported anchor scale refuses before data and history change")
	app.clip_editor.clipboard.contact_anchor=old_anchor;app.clip_editor.clipboard.piece=copied.duplicate(true);app.clip_editor.clipboard.piece.foot_contacts.segments[0].feet[1].position=[9999,9999,9999]
	app.clip_editor.request("paste",receiver.id,"",24)
	check(actor(receiver.id).data==target and app.history.size()==history and app.status.text.contains("Frame"),"unreachable pasted pins cannot publish a half-installed clip")
	app.clip_editor.clipboard.piece=copied.duplicate(true);app.clip_editor.clipboard.piece.foot_contacts.segments[0].feet[0].ids[0]="foreign-bone"
	app.clip_editor.request("paste",receiver.id,"",24)
	check(actor(receiver.id).data==target and app.history.size()==history and app.status.text.contains("bones"),"foreign contact binding refuses despite a matching geometry hash")
	app.physics_editor.queue_import_start(receiver.id,true,false);app.clip_editor.clipboard.piece=copied.duplicate(true);app.clip_editor.request("paste",receiver.id,"",24)
	check(actor(receiver.id).data==target and app.history.size()==history and app.physics_editor.import_starts.has(receiver.id),"pending physics defers structural contact paste without consuming its ticket")
	app.physics_editor.clear()
	# Contact-only source pieces retain the receiver's own root, unlike a root-motion clip.
	app.new_project();source=World.object(asset);source.id="static-source";receiver=World.object(asset);receiver.id="static-receiver";receiver.position=[3,0,0]
	world=World.empty();world.objects=[source,receiver];app.restore_world(world);app.set_frame(0);rig=actor(source.id)
	track=Ranges.Contact.Contacts.capture(rig,0,1,"static-pin");planted=Ranges.edit(rig.data,0,13,track.segments[0],48);app.renderer.world_runtime.restore_instance(source.id,planted.data);app.set_frame(0)
	await action(source.id,2,11);await action(receiver.id,24,13);rig=actor(receiver.id);pasted=rig.data.animation_clips[-1]
	check(rig.sample_transform(24).position==[3,0,0] and endpoint_error(rig,pasted,28)<.0002,"contact-only paste anchors to the receiver root instead of teleporting it to the source")
	# Copy survives New/Open; the expired source Node must not be retained by the clipboard.
	var clipboard: Dictionary=app.clip_editor.clipboard.duplicate(true);app.new_project();receiver=World.object(asset);receiver.id="new-project-receiver";receiver.position=[-3,0,0];world=World.empty();world.objects=[receiver];app.restore_world(world)
	app.clip_editor.clipboard=clipboard;history=app.history.size();app.clip_editor.request("paste",receiver.id,"",24);rig=actor(receiver.id)
	check(clipboard.contact_owner.get_ref()==null and app.history.size()==history+1 and rig.data.format==Model.CONTACT_FORMAT and endpoint_error(rig,rig.data.animation_clips[-1],28)<.0002,"cross-project paste reanchors after the source root has been freed")
	# Real split -> cut -> paste within the same instance retains a continuous logical pin.
	app.new_project();world=World.empty();world.objects=[sender];app.restore_world(world);rig=actor(sender.id)
	# Remove the explicit frame25 release event before choosing24..36 as free space.
	app.clip_editor.request("delete",sender.id,rig.data.animation_clips[-1].id,25)
	app.clip_editor.request("split",sender.id,"",12);rig=actor(sender.id)
	var right: String=rig.data.animation_clips[1].id;app.clip_editor.request("cut",sender.id,right,12);app.clip_editor.request("paste",sender.id,"",24);rig=actor(sender.id)
	check(rig.data.animation_clips.size()==2 and not Ranges.Contact.Contacts.active(rig.data.animation_clips,18).is_empty() and endpoint_error(rig,rig.data.animation_clips[-1],30)<.0002,"cut/paste relocation preserves the same declared pin across the new gap")
	var before: Dictionary=rig.data.duplicate(true);history=app.history.size();app.clip_editor.move_piece(sender.id,rig.data.animation_clips[-1].id,28,before)
	check(app.history.size()==history+1 and rig.data.animation_clips[-1].start==28 and not Ranges.Contact.Contacts.active(rig.data.animation_clips,20).is_empty(),"normal piece movement retains source-time contacts and connecting gap")
	app.undo();check(rig.data==before,"piece movement Undo restores contact timing exactly")
	app.retime_object(sender.id,4,rig.data.duplicate(true));check(rig.data.start_frame==4 and not Ranges.Contact.Contacts.active(rig.data.animation_clips,28).is_empty(),"whole-object retime moves contact timing with presence and body motion")
	app.undo()
	var a: Dictionary=track.segments[0].duplicate(true);var b: Dictionary=JSON.parse_string(JSON.stringify(a,"",true,true));check(Ranges.Contact.Contacts.same_contact(a,b),"logical contact identity uses exact engine targets after JSON rounding")
	var introduced:=Model.new();introduced.data=before.duplicate(true);introduced.data.start_frame=8;introduced.data.presence_offset=8;introduced.root=rig.root;introduced.base_root=rig.base_root;introduced.bones=rig.bones;introduced.order=rig.order;introduced.world_context=rig.world_context
	introduced.data.animation_clips[0].foot_contacts.segments[0].feet[1].position=[99999,99999,99999];introduced.sample(0)
	check(introduced.evaluation_error.is_empty(),"contacts are inactive before explicit object presence, even when a source slice starts earlier")
	introduced.sample(8);check(not introduced.evaluation_error.is_empty(),"the same invalid contact becomes an explicit error when the object is introduced")
	# Independent visibility is authoritative while editing contact blocks.
	var hidden: Dictionary=rig.data.duplicate(true);hidden.visibility_keys=[{"frame":0,"visible":false}];app.renderer.world_runtime.restore_instance(sender.id,hidden);app.video.visibility_fade_ms=0;app.set_frame(30)
	check(not rig.root.visible and not rig.data.visible==false,"retimed contact motion cannot turn a persistent visibility key on")
	app.renderer.world_runtime.restore_instance(sender.id,before);app.set_frame(30);app.world_selection.select_entity(sender.id);app.pose_editor.frame_model();app.keys=[T.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var has_path:=folder.path_join("pasted-contacts.has");app.has_project.save_file(has_path,"packed")
	while app.has_project.pid>0:await process_frame
	app.new_project();app.has_project.open_file(has_path)
	while app.has_project.pid>0:await process_frame
	app.set_frame(30);var reference: Image=await app.renderer.capture(app.keys,app.layers,30,true);reference.save_png(folder.path_join("pasted-frame.png"));var export_error: String=await app.export_movie(folder)
	check(export_error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000031.png")).get_data(),"retimed/cut/pasted contacts reopen through real HAS and match actual MP4 frames")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	# Initially valid inverse parent/child curves must not become invalid after a retime.
	app.new_project();parent=World.object(empty,"group","Animated parent");parent.id="moving-parent";source=World.object(asset);source.id="moving-child";source.parent_id=parent.id
	var parent_model:=Model.new();parent_model.data=parent;var child_model:=Model.new();child_model.data=source
	for frame in [0,24]:
		var p:=root_value(0.);p.position[0]=0. if frame==0 else 10.;var parent_before: Dictionary=parent_model.data.duplicate(true)
		parent_model.put_pose_key({"frame":frame,"pose":{},"transform":p,"authored_channels":["@root"],"interpolation":"ease"},48,false,parent_before)
		p=root_value(0. if frame==0 else -.15);p.position[0]=0. if frame==0 else -10.;var child_before: Dictionary=child_model.data.duplicate(true)
		child_model.put_pose_key({"frame":frame,"pose":{},"transform":p,"authored_channels":["@root"],"interpolation":"ease"},48,false,child_before)
	world=World.empty();world.objects=[child_model.data,parent_model.data];app.restore_world(world);app.set_frame(0);rig=actor(source.id);track=Ranges.Contact.Contacts.capture(rig,0,1,"inverse-parent-pin");planted=Ranges.edit(rig.data,0,25,track.segments[0],48)
	app.renderer.world_runtime.restore_instance(source.id,planted.data);app.set_frame(0)
	check(Contact.validate_candidate(rig,rig.data,48).is_empty(),"inverse parent/child source motion is genuinely reachable before retiming")
	var retime_before: Dictionary=rig.data.duplicate(true);history=app.history.size();app.retime_object(source.id,4,retime_before)
	check(rig.data==retime_before and app.history.size()==history and app.status.text.contains("Frame"),"retime that breaks parent-relative reach refuses atomically with frame feedback")
	check(FileAccess.get_sha256(asset)==sha,"original model bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"peak_error":peak,"movie":movie};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_CLIPBOARD "+JSON.stringify(result));quit(0 if failures==0 else 1)

extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Contact=preload("res://src/contact_clipboard.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Contact identity watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func actor(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func pin(data: Dictionary,at: int) -> String:return str(Contacts.active(data.animation_clips,at).get("id",""))
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func pose_hashes() -> Dictionary:
	var hashes:={}
	for id in ["source","receiver"]:
		hashes[id]=[]
		for half in range(97):hashes[id].append(JSON.stringify(actor(id).sample(float(half)/2),"",true,true).sha256_text())
	return hashes
func reopen() -> void:
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected-world.json")))
	check(same(World.portable(app.current_world()),expected),"cold process retains exact portable pasted IDs, gaps and native metadata")
	var expected_poses: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected-poses.json")))
	check(pose_hashes()==expected_poses,"cold process retains all194 fractional native poses exactly")
	check(pin(actor("source").data,10).is_empty() and pin(actor("source").data,20)!=pin(actor("receiver").data,12),"cold process retains released gap and independent instance identities")
	app.set_frame(22);var actual: Image=await app.renderer.capture(app.keys,app.layers,22,true);var reference:=Image.load_from_file(folder.path_join("identity-frame.png"));reference.convert(Image.FORMAT_RGBA8)
	var a:=actual.get_data();var b:=reference.get_data();var changed:=0;var total:=0.
	for i in range(a.size()):
		if a[i]!=b[i]:changed+=1;total+=absf(float(a[i])-float(b[i]))
	actual.save_png(folder.path_join("cold-frame.png"));check(changed<=384 and total/a.size()<.002,"cold native scene/paint retains established mesh-edge pixel bound")
	var result:={"checks":checks,"failures":failures,"changed_channels":changed,"mean_error":total/a.size()};var file:=FileAccess.open(folder.path_join("cold-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_IDENTITY_REOPEN "+JSON.stringify(result));quit(0 if failures==0 else 1)
func setup(plan: Dictionary) -> Dictionary:
	app.new_project();var data:=World.object(plan.source);data.id="source";data.metadata=plan.metadata.duplicate(true)
	var other:=World.object(plan.source);other.id="receiver";other.position=[3,0,0];other.metadata=plan.metadata.duplicate(true)
	var world:=World.empty();world.objects=[data,other];app.restore_world(world);app.set_frame(0)
	var rig:=actor(data.id);var track:=Contacts.capture(rig,0,8,"pin-"+str(plan.label));var promoted:=Ranges.Contact.promote(rig.data,48)
	promoted.animation_clips=[Ranges.empty_piece(promoted,0,8)];promoted.animation_clips[0]["foot_contacts"]=track
	var split:=Model.Clips.split(promoted,4);app.renderer.world_runtime.restore_instance(data.id,split.data);app.set_frame(0)
	return actor(data.id).data.duplicate(true)
func cut_right() -> void:
	app.clip_editor.request("cut","source",actor("source").data.animation_clips[1].id,4)
func paste(id: String,at: int) -> void:app.clip_editor.request("paste",id,"",at)
func case_for(plan: Dictionary) -> Dictionary:
	var began:=checks;var before_failures:=failures;var original:=setup(plan);var original_pin:=pin(original,4)
	cut_right();var cut: Dictionary=actor("source").data.duplicate(true);var clipboard: Dictionary=app.clip_editor.clipboard.duplicate(true);var history: int=app.history.size()
	paste("source",0)
	check(actor("source").data==cut and app.history.size()==history and app.clip_editor.clipboard==clipboard,"overlap refusal retains pending cut and immutable clipboard: "+plan.label)
	app.clip_editor.clipboard.piece.foot_contacts.segments[0].feet[1].position=[9999,9999,9999];paste("source",12)
	check(actor("source").data==cut and app.history.size()==history and app.clip_editor.clipboard.get("contact_cut",false),"reach refusal does not consume cut relocation: "+plan.label)
	app.clip_editor.clipboard=clipboard.duplicate(true)
	if plan.label=="Miku_Hatsune.pmd":
		var padded:=cut.duplicate(true);var world: Dictionary=app.current_world();var limit:=1024*1024
		padded.metadata["budget_probe"]="x".repeat(limit-app.pose_editor.contacts.metadata_bytes(world)-256)
		app.renderer.world_runtime.restore_instance("source",padded);world=app.current_world();var fits: bool=app.pose_editor.contacts.metadata_bytes(world)<limit;paste("source",12)
		check(fits and actor("source").data==padded and app.history.size()==history and app.status.text.contains("metadata") and app.clip_editor.clipboard==clipboard,"full-world metadata refusal retains the exact pending Cut, clipboard and Undo")
		var dense:=cut.duplicate(true)
		for i in range(31):dense.animation_clips.append(Ranges.empty_piece(dense,4+i,1))
		app.renderer.world_runtime.restore_instance("source",dense);paste("source",44)
		check(actor("source").data==dense and app.history.size()==history and app.status.text.contains("32") and app.clip_editor.clipboard==clipboard,"32-piece refusal retains pending Cut without partial data or Undo")
		app.renderer.world_runtime.restore_instance("source",cut)
	paste("source",12)
	var first: Dictionary=actor("source").data.duplicate(true)
	check(pin(first,12)==original_pin and pin(first,8)==original_pin and app.history.size()==history+1,"first successful same-placement Cut/Paste retains logical continuity across its gap: "+plan.label)
	check(not app.clip_editor.clipboard.get("contact_cut",false) and app.clip_editor.clipboard.piece==clipboard.piece,"successful relocation consumes only its cut privilege, retaining reusable source motion: "+plan.label)
	paste("source",20);var second: Dictionary=actor("source").data.duplicate(true);var second_pin:=pin(second,20)
	check(not second_pin.is_empty() and second_pin!=original_pin and pin(second,18).is_empty(),"reusing Cut clipboard creates an independent pin and releases the gap: "+plan.label)
	app.undo();check(actor("source").data==first,"repeated Paste Undo restores exact first placement: "+plan.label)
	app.redo();check(actor("source").data==second,"repeated Paste Redo restores exact new identity: "+plan.label)
	paste("source",28);var third: Dictionary=actor("source").data.duplicate(true);var third_pin:=pin(third,28)
	check(not third_pin.is_empty() and not third_pin in [original_pin,second_pin] and pin(third,26).is_empty(),"third paste remains independent of both existing pins: "+plan.label)
	app.undo();app.undo();app.undo();app.undo()
	check(actor("source").data==original,"Undo through every paste and original Cut restores exact source: "+plan.label)
	paste("source",12);var restored: Dictionary=actor("source").data.duplicate(true)
	check(pin(restored,12)!=original_pin and pin(restored,10).is_empty(),"reusing consumed clipboard after Undo restores a copy, not a second original pin: "+plan.label)
	# Undoing the original Cut before ANY successful Paste also revokes identity
	# reuse: the original block exists again, although the clipboard remains full.
	original=setup(plan);original_pin=pin(original,4);cut_right();app.undo();paste("source",12)
	var undone: Dictionary=actor("source").data.duplicate(true)
	check(pin(undone,4)==original_pin and pin(undone,12)!=original_pin and pin(undone,10).is_empty(),"Undo Cut before first Paste cannot duplicate the restored source identity: "+plan.label)
	# A move into another instance becomes independently anchored there. Its later
	# reuse back on the sender is a copy even when that root has not changed.
	original=setup(plan);original_pin=pin(original,4);cut_right();paste("receiver",12)
	var receiver: Dictionary=actor("receiver").data.duplicate(true);var receiver_pin:=pin(receiver,12)
	check(not receiver_pin.is_empty() and receiver_pin!=original_pin and not app.clip_editor.clipboard.get("contact_cut",false),"foreign-instance successful paste consumes cut privilege and reanchors independently: "+plan.label)
	paste("source",20);var returned: Dictionary=actor("source").data.duplicate(true)
	check(not pin(returned,20).is_empty() and not pin(returned,20) in [original_pin,receiver_pin] and pin(returned,10).is_empty(),"foreign relocation followed by sender reuse cannot revive the old logical pin: "+plan.label)
	var stable:=true
	for id in ["source","receiver"]:
		var rig:=actor(id)
		for half in range(97):rig.sample(float(half)/2);stable=stable and rig.evaluation_error.is_empty()
	check(stable and actor("source").data==returned and actor("receiver").data==receiver,"all194 fractional samples stay reachable and authored state is unchanged: "+plan.label)
	return {"label":plan.label,"checks":checks-began,"failures":failures-before_failures,"bones":actor("source").order.size()}
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(args[1]);await job()
	if args.size()>2 and args[2]=="read":await reopen();return
	var plans:=[];var hashes:={}
	for object in app.current_world().objects:
		if object.kind!="model" or object.get("format")!=Model.CONTACT_FORMAT:continue
		plans.append({"label":object.name,"source":object.source,"metadata":object.metadata.duplicate(true)});hashes[object.source]=FileAccess.get_sha256(object.source)
	check(plans.size()==5,"five actual MMD/GMod/SFM/VRM0/VRM1 rigs available")
	if plans.size()!=5:app.free();quit(1);return
	var reports:=[]
	for plan in plans:reports.append(case_for(plan))
	app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(130,40),8,Color.CYAN,false);app.changed()
	app.set_frame(22);app.world_selection.select_entity("source");app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var before: Dictionary=World.portable(app.current_world());var path:=folder.path_join("independent-pastes.has");app.has_project.save_file(path,"packed");await job();app.new_project();app.has_project.open_file(path);await job()
	var expected_file:=FileAccess.open(folder.path_join("expected-world.json"),FileAccess.WRITE);expected_file.store_string(JSON.stringify(before,"",true,true));expected_file.close()
	var actual_file:=FileAccess.open(folder.path_join("reopened-world.json"),FileAccess.WRITE);actual_file.store_string(JSON.stringify(World.portable(app.current_world()),"",true,true));actual_file.close()
	check(same(World.portable(app.current_world()),before),"packed HAS retains every pasted identity, gap and native parameter")
	var poses_file:=FileAccess.open(folder.path_join("expected-poses.json"),FileAccess.WRITE);poses_file.store_string(JSON.stringify(pose_hashes()));poses_file.close()
	app.set_frame(22);var reference: Image=await app.renderer.capture(app.keys,app.layers,22,true);reference.save_png(folder.path_join("identity-frame.png"));var error: String=await app.export_movie(folder)
	check(error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000023.png")).get_data(),"independent Cut/Paste contacts and editable paint render exact reopened preview/movie pixels")
	var unchanged:=true
	for source in hashes:unchanged=unchanged and FileAccess.get_sha256(source)==hashes[source]
	check(unchanged,"all original prepared native model bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"native_reports":reports,"movie":app.last_export_folder.path_join("movie.mp4"),"project":path};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_IDENTITY "+JSON.stringify(result));quit(0 if failures==0 else 1)

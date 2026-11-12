extends "res://tests/contact_transform_smoke.gd"
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var reader: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("result.json")));app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("cold-recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cold-cache");app.has_project.open_file(reader.project);await job()
	check(JSON.parse_string(JSON.stringify(World.portable(app.current_world()),"",true,true))==reader.expected_world,"fresh process reopens exact portable viewport-authored scene")
	var exact:=true
	for half in range(96,-1,-1):exact=exact and JSON.stringify(actor("child").sample(float(half)/2),"",true,true).sha256_text()==reader.pose_hashes[half]
	check(exact,"all97 native solved poses match in reverse order after cold reopen")
	check(preload("res://src/drawing.gd").image(app.layers[1].cels[0]).get_data().hex_encode().sha256_text()==reader.layer_sha,"fresh process preserves the independent editable cyan drawing")
	check(not app.pose_editor.contacts.viewport.active and not app.pose_editor.contacts.viewport.dragging and actor("child").preview_frame==-1,"project has no transient target gesture or preview on cold Open")
	app.set_frame(12);var image: Image=await app.renderer.capture(app.keys,app.layers,12,true);var original:=Image.load_from_file(folder.path_join("saved-frame.png"));var a:=image.get_data();var b:=original.get_data();var changed:=0;var total:=0.
	for i in range(a.size()):
		if a[i]!=b[i]:changed+=1;total+=abs(int(a[i])-int(b[i]))
	check(changed<=384 and total/a.size()<.002,"cold packed scene retains preview pixels within established mesh-edge rebuild bound")
	var value:={"checks":checks,"failures":failures,"changed_channels":changed,"mean":total/a.size()};var file:=FileAccess.open(folder.path_join("reader.json"),FileAccess.WRITE);file.store_string(JSON.stringify(value));file.close();app.free();await settled();print("CONTACT_VIEWPORT_READ "+JSON.stringify(value));quit(0 if failures==0 else 1)

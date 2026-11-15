extends "res://tests/fan_motion_smoke.gd"

func run() -> void:
	folder=ProjectSettings.globalize_path("res://output/hair-disable/run_"+str(Time.get_ticks_usec()))
	DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("posed-hair.glb")
	check(Fixture.create(asset)==OK,"hair-disable fixture creates the actual skinned spring rig")
	var app=load("res://main.tscn").instantiate()
	app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false
	await hair_off(app,asset)
	var result:={"checks":checks,"failures":failures,"folder":folder}
	FileAccess.open("res://output/hair-disable-result.json",FileAccess.WRITE).store_string(JSON.stringify(result))
	print("HAIR_DISABLE "+JSON.stringify(result))
	await process_frame
	app.free();quit(0 if failures==0 else 1)

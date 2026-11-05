extends SceneTree
const Library=preload("res://src/pose_library.gd")
func _initialize() -> void:
	var rows=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]));var failures:=0
	for row in rows:
		var accepted:=Library.error(row.value).is_empty()
		if accepted!=row.valid:failures+=1;print("FAIL ",JSON.stringify(row))
	var unique:=Library.unique_name("Wave",[{"name":"Wave"},{"name":"Wave 2"}]);if unique!="Wave 3":failures+=1
	print("POSE_LIBRARY_UNIT ",JSON.stringify({"checks":rows.size()+1,"failures":failures}));quit(0 if failures==0 else 1)

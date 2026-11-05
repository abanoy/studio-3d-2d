extends SceneTree
const Origin=preload("res://src/drawing_origin.gd")
func _initialize() -> void:
	var rows=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]));var failures:=0
	for row in rows:
		var accepted:=Origin.error(row.value).is_empty()
		if accepted!=row.valid:failures+=1;print("FAIL ",JSON.stringify(row))
	print("DRAWING_ORIGIN_UNIT ",JSON.stringify({"checks":rows.size(),"failures":failures}));quit(0 if failures==0 else 1)

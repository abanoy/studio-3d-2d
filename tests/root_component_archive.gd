extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var path:=folder.path_join("project.json");var project: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path));var checks:=0;var failures:=0
	for index in range(project.world.objects.size()):
		var row: Dictionary=project.world.objects[index]
		if row.kind!="model":continue
		if OS.get_cmdline_user_args().size()==1:
			var promoted:=D.promote(row,int(project.video.duration_frames))
			if promoted.has("error"):print(promoted);quit(1);return
			project.world.objects[index]=promoted.data
		checks+=1
		if not D.validate(project.world.objects[index],int(project.video.duration_frames)).is_empty():failures+=1
		var unsupported: Dictionary=project.world.objects[index].duplicate(true);unsupported.format="studio_model_999";checks+=1
		if D.Model.validate(unsupported,int(project.video.duration_frames)).is_empty():failures+=1
	if OS.get_cmdline_user_args().size()==1:
		var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(project));file.close()
	checks+=1
	var loaded:=Storage.load_project(folder)
	if loaded.has("error"):failures+=1
	print("COMPONENT_ARCHIVE "+JSON.stringify({"checks":checks,"failures":failures,"normal_reader_error":loaded.get("error","")}));quit(0 if failures==0 else 1)

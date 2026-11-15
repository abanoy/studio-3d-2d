extends SceneTree
const Recovery=preload("res://src/recovery.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Storage=preload("res://src/storage.gd")
const GC=preload("res://src/recovery_blob_retention.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func write(path: String,bytes: PackedByteArray) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(bytes);file.flush();file.close()
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var base: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(base)
	var folder:=base.path_join("session");var video:={"width":960,"height":540,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[preload("res://src/timeline.gd").key(0,Vector3(0,1,4),Quaternion.IDENTITY,60)]
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[]}];var image:=Drawing.blank(960,540);Drawing.insert(layers[0],0,48,image)
	var paths: Array=[];var originals: Dictionary={}
	for i in range(25):
		image.fill(Color(float(i)/25.,.25,.5,1));Drawing.touch(image)
		var source:=base.path_join("original_%d.glb"%i);var root:=Node3D.new();root.name="Original_"+str(i);preload("res://src/scene3d.gd").box(root,"Panel",Vector3.ZERO,Vector3.ONE,Color(float(i)/25.,.5,.5));var doc:=GLTFDocument.new();var state:=GLTFState.new();var code:=doc.append_from_scene(root,state)
		if code==OK:code=doc.write_to_filesystem(state,source)
		root.free();originals[source]=FileAccess.get_sha256(source)
		var error:=Recovery.checkpoint(base,"session",video,keys,layers,source,i,{},"manual.has",i)
		check(code==OK and error.is_empty(),"commit changing image and geometry generation"+str(i))
		var manifest:=Journal.read_json(folder.path_join("project.json"));paths.append(manifest.layers[0].cels[0].path)
	var current:=GC.inventory(folder);check(not current.is_empty() and Journal.entries(folder).size()==12,"valid inventory retains current and rollback catalog roots")
	var count:=DirAccess.get_files_at(folder.path_join("cels/content")).size();var assets:=DirAccess.get_files_at(folder.path_join("assets")).size()
	check(count<=13 and assets<=13 and count>0,"25generations retain at most13drawing and13geometry blobs including rollback catalog")
	check(not FileAccess.file_exists(folder.path_join(paths[0])) and FileAccess.file_exists(folder.path_join(paths[-1])),"expired proven-owned pixels retire while current pixels stay")
	var all_valid:=true
	for name in current.stamps:
		if name in ["session.json","journal.json","journal.backup.json"]:continue
		if Storage.load_project(folder,name).has("error"):all_valid=false
	check(all_valid,"every retained current/backup/history manifest still opens with exact checked payloads")
	var unknown:=folder.path_join("cels/content/"+"a".repeat(64)+".png");write(unknown,"owner-owned unrelated bytes".to_utf8_buffer());var before:=GC.inventory(folder);var result:=GC.retire(folder,before)
	check(result.removed==0 and FileAccess.get_file_as_string(unknown)=="owner-owned unrelated bytes","unreferenced hash-shaped files are untouched unless proven formerly referenced")
	var catalog:=folder.path_join("journal.backup.json");var good:=FileAccess.get_file_as_bytes(catalog);write(catalog,"{".to_utf8_buffer());result=GC.retire(folder,before)
	check(result.skipped and FileAccess.file_exists(unknown),"corrupt rollback catalog stops all blob reclamation");write(catalog,good)
	var owner_path:=folder.path_join("session.json");good=FileAccess.get_file_as_bytes(owner_path);write(owner_path,JSON.stringify({"pid":OS.get_process_id()+1}).to_utf8_buffer());check(GC.inventory(folder).is_empty() and GC.retire(folder,before).skipped,"another process owner prevents reclamation");write(owner_path,good)
	var escaped:=before.duplicate(true);escaped.paths["../original_0.glb"]=true;escaped.paths["cels/content/notes.png"]=true;result=GC.retire(folder,escaped)
	check(result.removed==0 and FileAccess.file_exists(unknown),"path escapes and non-owned filename shapes cannot become deletion targets")
	if OS.get_name()=="Linux":
		var linked:=folder.path_join(paths[0]);var filesystem:=DirAccess.open(base)
		check(filesystem.create_link(base.path_join("original_0.glb"),linked)==OK,"create owned test symlink to an original outside recovery")
		escaped.paths[paths[0]]=true;result=GC.retire(folder,escaped)
		check(result.removed==0 and filesystem.is_link(linked) and FileAccess.get_sha256(base.path_join("original_0.glb"))==originals[base.path_join("original_0.glb")],"linked candidate is left untouched and original link target is preserved")
		DirAccess.remove_absolute(linked)
	var kept:=true
	for source in originals:kept=kept and FileAccess.get_sha256(source)==originals[source]
	check(kept,"all25original geometry assets remain byte-identical outside recovery")
	# Collect nested, audio, effect and reference dependencies independently.
	var keep: Dictionary={};var data: Dictionary=Journal.read_json(folder.path_join("project.json"));var child:=data.duplicate(true);child.layers[0].cels[0].path="cels/content/"+"b".repeat(64)+".png";data.sequence_graph={"assets":[{"scene":child}]};data.audio={"clips":[{"path":"assets/"+"c".repeat(64)+".wav"}]};data.reference_sheet={"path":"references/"+"d".repeat(64)+".png"};data.world={"objects":[],"effects":[{"path":"assets/"+"e".repeat(64)+".json","texture_path":"assets/"+"f".repeat(64)+".png"}]}
	check(GC.references(data,keep) and keep.has(child.layers[0].cels[0].path) and keep.has(data.audio.clips[0].path) and keep.has(data.reference_sheet.path) and keep.has(data.world.effects[0].texture_path),"nested drawings and audio/effect/reference dependencies all remain roots")
	print("RECOVERY_BLOB_RETENTION "+JSON.stringify({"checks":checks,"failures":failures,"retained_cels":count,"retained_assets":assets,"generations":25}));quit(0 if failures==0 else 1)

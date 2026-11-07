extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
var folder: String
var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func write(path: String,bytes: PackedByteArray) -> void:
 var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(bytes);file.close()
func save(project: String,layers: Array=[],frame:=0) -> String:return Storage.save_project(project,video,keys,layers,"",frame,{}, {},{},true,World.empty())
func fixture(name: String,layers: Array=[]) -> String:
 var project:=folder.path_join(name);var error:=save(project,layers)
 if not error.is_empty():push_error("Fixture "+name+": "+error);failures+=1
 return project
func link(source: String,target: String) -> bool:
 var code:=DirAccess.open(folder).create_link(source,target)
 if code!=OK:failures+=1;push_error("Cannot create owned symbolic-link fixture: "+target)
 return code==OK
func hardlink(source: String,target: String) -> bool:
 var code:=OS.execute("ln",PackedStringArray(["--",source,target]))
 if code!=0:failures+=1;push_error("Cannot create owned hard-link fixture: "+target)
 return code==0
func _initialize() -> void:
 folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 if OS.get_name()!="Linux":
  print("PROJECT_WRITE_PATHS_UNIT "+JSON.stringify({"checks":0,"failures":0,"skipped":"Linux symlink/hardlink/permission fixture; native Windows gate remains"}));quit();return
 var original:=folder.path_join("original.txt");var sentinel:="ORIGINAL SOURCE SENTINEL".to_utf8_buffer();write(original,sentinel)
 var project:=fixture("manifest-link");var manifest:=FileAccess.get_sha256(project.path_join("project.json"));var temp:=project.path_join("project.json.tmp")
 check(link(original,temp),"create owned symbolic-link fault fixture")
 check(not save(project,[],1).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and FileAccess.get_sha256(project.path_join("project.json"))==manifest,"manifest temporary link refuses without changing source or previous save")
 project=fixture("target-link");var source_manifest:=folder.path_join("source-manifest.json");write(source_manifest,FileAccess.get_file_as_bytes(project.path_join("project.json")));var source_sha:=FileAccess.get_sha256(source_manifest);DirAccess.remove_absolute(project.path_join("project.json"));link(source_manifest,project.path_join("project.json"))
 check(not save(project,[],1).is_empty() and FileAccess.get_sha256(source_manifest)==source_sha and DirAccess.open(project).is_link("project.json"),"linked manifest destination refuses while original and link remain intact")
 project=fixture("backup-link");manifest=FileAccess.get_sha256(project.path_join("project.json"));link(original,project.path_join("project.backup.json"))
 check(not save(project,[],1).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and FileAccess.get_sha256(project.path_join("project.json"))==manifest,"linked backup destination cannot overwrite original source")
 var external:=folder.path_join("outside-assets");DirAccess.make_dir_recursive_absolute(external);write(external.path_join("keep.txt"),sentinel);project=fixture("assets-link");DirAccess.remove_absolute(project.path_join("assets"));link(external,project.path_join("assets"));manifest=FileAccess.get_sha256(project.path_join("project.json"))
 check(not save(project).is_empty() and FileAccess.get_sha256(project.path_join("project.json"))==manifest and DirAccess.get_files_at(external).size()==1,"linked managed directory refuses before writing outside project")
 project=fixture("cels-link");DirAccess.remove_absolute(project.path_join("cels/content"));link(external,project.path_join("cels/content"))
 var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,20,20),Color.CYAN);var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"cel","start":0,"duration":48,"image":image}]}]
 check(not save(project,layers).is_empty() and DirAccess.get_files_at(external).size()==1,"nested cel directory link refuses without emitting external PNG")
 project=fixture("png-link",layers);var cel_path:=project.path_join("cels/content/"+Storage.image_hash(image)+".png");var source_png:=folder.path_join("source.png");write(source_png,FileAccess.get_file_as_bytes(cel_path));var source_png_sha:=FileAccess.get_sha256(source_png);DirAccess.remove_absolute(cel_path);link(source_png,cel_path);manifest=FileAccess.get_sha256(project.path_join("project.json"))
 check(not save(project,layers).is_empty() and FileAccess.get_sha256(source_png)==source_png_sha and FileAccess.get_sha256(project.path_join("project.json"))==manifest,"linked cel destination refuses without changing original PNG")
 var copied:=folder.path_join("managed.bin");link(original,copied)
 check(not Storage.managed_copy(source_png,copied,source_png_sha).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel,"managed copy refuses linked file destination")
 project=fixture("hard-temp");temp=project.path_join("project.json.tmp");check(hardlink(original,temp) and save(project,[],1).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and FileAccess.get_file_as_bytes(temp)==sentinel,"fresh manifest temporary preserves existing hard-linked source inode")
 project=fixture("hard-backup");var before:=FileAccess.get_file_as_bytes(project.path_join("project.json"));var backup_source:=folder.path_join("backup-source.json");write(backup_source,before);hardlink(backup_source,project.path_join("project.backup.json"))
 check(save(project,[],1).is_empty() and FileAccess.get_file_as_bytes(backup_source)==before and FileAccess.get_file_as_bytes(project.path_join("project.backup.json"))==before,"atomic verified backup replacement preserves external hard-linked source")
 copied=folder.path_join("managed-hard.bin");hardlink(original,copied+".import.tmp")
 check(Storage.managed_copy(source_png,copied,source_png_sha).is_empty() and FileAccess.get_sha256(copied)==source_png_sha and FileAccess.get_file_as_bytes(original)==sentinel,"fresh managed-copy temporary preserves legacy hard-linked temporary")
 project=fixture("hard-png");cel_path=project.path_join("cels/content/"+Storage.image_hash(image)+".png");hardlink(original,cel_path+".tmp.png")
 check(save(project,layers).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and Storage.image_hash(Drawing.image(Storage.load_project(project).layers[0].cels[0]))==Storage.image_hash(image),"fresh verified PNG temporary preserves hard-linked source and exact saved pixels")
 project=fixture("hard-png-final");cel_path=project.path_join("cels/content/"+Storage.image_hash(image)+".png");var wrong:=Drawing.blank(1920,1080);var wrong_source:=folder.path_join("wrong.png");wrong.save_png(wrong_source);var wrong_sha:=FileAccess.get_sha256(wrong_source);hardlink(wrong_source,cel_path)
 check(save(project,layers).is_empty() and FileAccess.get_sha256(wrong_source)==wrong_sha and Storage.image_hash(Drawing.image(Storage.load_project(project).layers[0].cels[0]))==Storage.image_hash(image),"atomic PNG replacement repairs wrong cache without changing hard-linked original")
 project=fixture("stale-temp");write(project.path_join("project.json.tmp"),"{interrupted".to_utf8_buffer());check(save(project,[],1).is_empty() and FileAccess.get_file_as_string(project.path_join("project.json.tmp"))=="{interrupted" and Storage.readable_manifest(project.path_join("project.json")),"legacy interrupted temporary remains untouched while new save succeeds")
 project=fixture("blocked-temp");manifest=FileAccess.get_sha256(project.path_join("project.json"));DirAccess.make_dir_recursive_absolute(project.path_join("project.json.tmp"));check(not save(project,[],1).is_empty() and FileAccess.get_sha256(project.path_join("project.json"))==manifest,"existing temporary-directory obstruction keeps prior failure-preservation contract")
 var actual:=fixture("chosen-root");var alias:=folder.path_join("chosen-root-link");check(link(actual,alias) and save(alias,[],1).is_empty() and int(Storage.load_project(actual).editor.frame)==1,"explicitly chosen linked project root remains usable with safe descendants")
 project=fixture("read-only");manifest=FileAccess.get_sha256(project.path_join("project.json"));var mode:=OS.execute("chmod",PackedStringArray(["555",project]));var error:=save(project,[],1);OS.execute("chmod",PackedStringArray(["755",project]));check(mode==0 and not error.is_empty() and FileAccess.get_sha256(project.path_join("project.json"))==manifest,"real owned read-only directory refuses safely with previous manifest intact")
 print("PROJECT_WRITE_PATHS_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"scope":"owned Linux links/hardlinks/read-only paths; no Windows or hostile concurrent filesystem race certification"}));quit(0 if failures==0 else 1)

extends SceneTree
const Recovery=preload("res://src/recovery.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Lesson=preload("res://src/lesson_store.gd")
const Atomic=preload("res://src/atomic_metadata.gd")
var checks:=0
var failures:=0
var folder: String
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func write(path: String,bytes: PackedByteArray) -> void:
 var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(bytes);file.close()
func link(source: String,target: String) -> void:
 if DirAccess.open(folder).create_link(source,target)!=OK:push_error("Cannot create owned link fixture");failures+=1
func put(kind: String,path: String) -> String:
 if kind=="recovery":return Recovery.write_json(path,{"saved":2})
 if kind=="journal":return Journal.write_bytes(path,"{\"saved\":2}".to_utf8_buffer())
 var store:=Lesson.new();store.root=folder;store.write_json(path,{"saved":2});return store.error
func _initialize() -> void:
 folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 if OS.get_name()!="Linux":print("PRIVATE_METADATA_UNIT "+JSON.stringify({"checks":0,"failures":0,"skipped":"Linux owned link/permission faults; Windows gate remains"}));quit();return
 var sentinel:="ORIGINAL SOURCE".to_utf8_buffer();var original:=folder.path_join("original.txt");write(original,sentinel)
 for kind in ["recovery","journal","lesson"]:
  var base:=folder.path_join(kind);DirAccess.make_dir_recursive_absolute(base)
  var target:=base.path_join("normal.json");check(put(kind,target).is_empty() and Recovery.read_json(target).get("saved")==2,"%s verifies and commits exact metadata" % kind)
  target=base.path_join("temp-link.json");write(target,"{\"old\":1}".to_utf8_buffer());var prior:=FileAccess.get_file_as_bytes(target);link(original,target+".tmp")
  check(not put(kind,target).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and FileAccess.get_file_as_bytes(target)==prior,"%s refuses linked legacy temporary before changing source/old state" % kind)
  target=base.path_join("target-link.json");link(original,target)
  check(not put(kind,target).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and DirAccess.open(base).is_link(target),"%s refuses linked primary destination" % kind)
  target=base.path_join("hard-temp.json");var code:=OS.execute("ln",PackedStringArray(["--",original,target+".tmp"]))
  check(code==0 and put(kind,target).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and FileAccess.get_file_as_bytes(target+".tmp")==sentinel,"%s fresh temporary preserves hard-linked source inode" % kind)
  target=base.path_join("hard-primary.json");code=OS.execute("ln",PackedStringArray(["--",original,target]))
  check(code==0 and put(kind,target).is_empty() and FileAccess.get_file_as_bytes(original)==sentinel and Recovery.read_json(target).get("saved")==2,"%s atomic primary replacement preserves external hard-linked source" % kind)
  target=base.path_join("stale.json");write(target+".tmp","interrupted".to_utf8_buffer())
  check(put(kind,target).is_empty() and FileAccess.get_file_as_string(target+".tmp")=="interrupted","%s leaves interrupted legacy temporary untouched" % kind)
  target=base.path_join("directory.json");write(target,"{\"old\":1}".to_utf8_buffer());prior=FileAccess.get_file_as_bytes(target);DirAccess.make_dir_recursive_absolute(target+".tmp")
  check(not put(kind,target).is_empty() and FileAccess.get_file_as_bytes(target)==prior,"%s obstructed temporary keeps prior state" % kind)
  var read_only:=base.path_join("read-only");DirAccess.make_dir_recursive_absolute(read_only);target=read_only.path_join("state.json");write(target,"{\"old\":1}".to_utf8_buffer());prior=FileAccess.get_file_as_bytes(target);OS.execute("chmod",PackedStringArray(["555",read_only]));var error:=put(kind,target);OS.execute("chmod",PackedStringArray(["755",read_only]))
  check(not error.is_empty() and FileAccess.get_file_as_bytes(target)==prior,"%s real permission failure keeps prior metadata" % kind)
 var outside:=folder.path_join("outside");DirAccess.make_dir_recursive_absolute(outside);var alias:=folder.path_join("linked-session");link(outside,alias)
 check(not Journal.write_bytes(alias.path_join("journal.json"),"{}".to_utf8_buffer()).is_empty() and DirAccess.get_files_at(outside).is_empty(),"journal rejects linked session directory before emitting external metadata")
 var store:=Lesson.new();store.root=folder
 check(not store.write_json(alias.path_join("progress.json"),{}) and DirAccess.get_files_at(outside).is_empty(),"lesson rejects linked managed directory before writing outside root")
 var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
 check(not Recovery.checkpoint(folder,"linked-session",video,[],[],"",0,{},"",1).is_empty() and DirAccess.get_files_at(outside).is_empty(),"checkpoint refuses linked session before session/project/history writes")
 check(not Atomic.path_error(folder.path_join("unset.json"),"").is_empty(),"unset metadata ownership root refuses")
 var too_large:=PackedByteArray();too_large.resize(Atomic.MAX_BYTES+1)
 check(not Atomic.write_bytes(folder.path_join("oversized.json"),too_large,folder).is_empty() and not FileAccess.file_exists(folder.path_join("oversized.json")),"oversized private metadata refuses before creating target")
 check(not Atomic.write_bytes(folder.get_base_dir().path_join("escaped.json"),"{}".to_utf8_buffer(),folder).is_empty(),"private metadata root escape refuses")
 var journal_folder:=folder.path_join("catalog");DirAccess.make_dir_recursive_absolute(journal_folder);var a:={"sha256":"a".repeat(64),"saved_at":1,"revision":1,"preview":""};var b:={"sha256":"b".repeat(64),"saved_at":2,"revision":2,"preview":""};Journal.commit(journal_folder,[a]);var catalog:=FileAccess.get_file_as_bytes(journal_folder.path_join("journal.json"));link(original,journal_folder.path_join("journal.backup.json"))
 check(not Journal.commit(journal_folder,[b]).is_empty() and FileAccess.get_file_as_bytes(journal_folder.path_join("journal.json"))==catalog and FileAccess.get_file_as_bytes(original)==sentinel,"linked history backup refuses before replacing valid primary catalog")
 check(FileAccess.get_file_as_bytes(original)==sentinel,"all private write failures preserve original source bytes")
 print("PRIVATE_METADATA_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"scope":"owned Linux metadata links/hardlinks/permissions; no Windows/power-loss/concurrent-writer certification"}));quit(0 if failures==0 else 1)

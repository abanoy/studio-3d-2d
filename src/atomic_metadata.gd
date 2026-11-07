extends RefCounted
# Small private metadata writes: verify a fresh inode before atomic replacement.
# The explicitly selected root may be linked; managed descendants may not.
const MAX_BYTES:=1024*1024
static func path_error(path: String,owned_root: String) -> String:
 if path.is_empty() or owned_root.is_empty():return "Metadata needs an owned folder. Previous state preserved."
 var base:=ProjectSettings.globalize_path(owned_root).simplify_path().trim_suffix("/")
 var target:=ProjectSettings.globalize_path(path).simplify_path()
 if not target.begins_with(base+"/"):return "Metadata write escapes its owned folder. Previous state preserved."
 var relative:=target.substr(base.length()+1)
 if relative.is_empty() or relative.contains(":") or relative.contains("\\"):return "Unsafe metadata write path. Previous state preserved."
 var filesystem:=DirAccess.open(ProjectSettings.globalize_path("res://"))
 if not filesystem:return "Cannot inspect metadata write path. Previous state preserved."
 var at:=base
 for part in relative.split("/"):
  if part in ["",".",".."]:return "Unsafe metadata write path. Previous state preserved."
  at=at.path_join(part)
  if filesystem.is_link(at):return "Metadata write path is a symbolic link. Previous state preserved."
 return ""
static func write_bytes(path: String,bytes: PackedByteArray,owned_root: String) -> String:
 var boundary:=preload("res://src/save_worker.gd").existing_boundary(owned_root)
 if bytes.size()>MAX_BYTES:return "Metadata exceeds1MiB. Previous state preserved."
 for candidate in [path,path+".tmp"]:
  var why:=path_error(candidate,owned_root)
  if not why.is_empty():return why
 if DirAccess.dir_exists_absolute(path) or DirAccess.dir_exists_absolute(path+".tmp"):return "Metadata destination is blocked by a directory. Previous state preserved."
 if DirAccess.make_dir_recursive_absolute(path.get_base_dir())!=OK:return "Cannot create metadata folder. Previous state preserved."
 # Never open a legacy temporary inode, even when it is a hard link.
 var temporary:=path+"."+str(ResourceUID.create_id())+".tmp"
 var filesystem:=DirAccess.open(path.get_base_dir())
 if not filesystem or filesystem.is_link(temporary) or FileAccess.file_exists(temporary) or DirAccess.dir_exists_absolute(temporary):return "Cannot create fresh metadata temporary. Previous state preserved."
 var file:=FileAccess.open(temporary,FileAccess.WRITE)
 if not file:return "Cannot write metadata temporary. Previous state preserved."
 file.store_buffer(bytes);file.flush();var code:=file.get_error();file.close()
 var expected:=HashingContext.new();expected.start(HashingContext.HASH_SHA256);expected.update(bytes);var digest:=expected.finish().hex_encode()
 var readback:=FileAccess.open(temporary,FileAccess.READ)
 var verified: bool=code==OK and readback!=null and readback.get_length()==bytes.size() and FileAccess.get_sha256(temporary)==digest
 if readback:readback.close()
 if not verified:
  DirAccess.remove_absolute(temporary);return "Cannot verify metadata temporary. Previous state preserved."
 var why:=path_error(path,owned_root)
 if not why.is_empty():DirAccess.remove_absolute(temporary);return why
 var arguments:=PackedStringArray([ProjectSettings.globalize_path(owned_root).simplify_path(),ProjectSettings.globalize_path(path).simplify_path(),ProjectSettings.globalize_path(temporary).simplify_path(),digest,boundary])
 var result:=preload("res://src/save_worker.gd").run("metadata_commit.py",arguments)
 return "" if result.get("ok",false)==true else str(result.error)

extends SceneTree
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Reader=preload("res://src/cel_raster_reader.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 var image:=Image.create(32,16,false,Image.FORMAT_RGBA8);image.fill(Color(.2,.7,.8,.5));var pixels:=image.get_data();var cache:=Cache.new(0,4096)
 var first:=Owner.from_image(image.duplicate(),cache);var second:=Owner.from_image(image.duplicate(),cache)
 check(not first.has("error") and not second.has("error") and cache.owned_bytes()==4096,"two admitted independent hot owners consume exact conservative bytes")
 var refused:=Owner.from_image(image.duplicate(),cache)
 check(refused.has("error") and cache.live_owners().size()==2 and cache.owned_bytes()==4096,"over-limit new owner refuses without registration or losing existing drawings")
 check(first.owner.read().image.get_data()==pixels and second.owner.read().image.get_data()==pixels and image.get_data()==pixels,"failed admission preserves existing and original source pixels")
 second={};var replacement:=Owner.from_image(image.duplicate(),cache)
 check(not replacement.has("error") and cache.owned_bytes()==4096 and cache.live_owners().size()==2,"discarded history/clipboard owner releases weak-registry admission capacity")
 var snap=Snapshot.capture(image).raster;var shared:=Cache.new(0,snap.storage_bytes());var a:=Owner.from_snapshot(snap,shared);var b:=Owner.from_snapshot(snap,shared)
 check(not a.has("error") and not b.has("error") and shared.owned_bytes()==snap.storage_bytes(),"independent cold owners sharing one immutable backing charge its payload once")
 shared.register(a.owner)
 check(shared.live_owners().size()==2 and shared.owned_bytes()==snap.storage_bytes(),"duplicate registry references cannot double-charge cold or hot ownership")
 var token: Array=a.owner.token();var pin: Dictionary=a.owner.pin()
 check(pin.has("error") and not a.owner.is_pinned() and a.owner.token()==token and a.owner._cold==snap,"edit hydration refuses before replacing cold authority when the hard limit has no room")
 check(a.owner.read().image.get_data()==pixels and shared.retained_bytes==0,"read/seek still materializes exact pixels without retaining an over-limit decoded cache")
 var borrowed: Image=a.owner.read().image;pin=a.owner.pin(token,borrowed)
 check(pin.has("error") and borrowed.get_data()==pixels and not a.owner.is_pinned(),"borrowed selection hydration also refuses atomically without losing its preview pixels")
 var roomy:=Cache.new(4096,4096);var cold:=Owner.from_snapshot(snap,roomy)
 var preview: Dictionary=cold.owner.read();check(roomy.retained_bytes==2048,"ordinary cold read caches a bounded decoded frame when capacity permits")
 preview={};var extra:=Owner.from_image(image.duplicate(),roomy)
 check(not extra.has("error") and roomy.retained_bytes==0 and roomy.owned_bytes()+roomy.retained_bytes<=roomy.owner_limit,"new authority evicts disposable decoded cache before admission")
 var editable: Dictionary=cold.owner.pin()
 check(editable.has("error") and not cold.owner.is_pinned() and extra.owner.is_pinned(),"hydration accounts other retained history/clipboard owners rather than only active cels")
 extra={};editable=cold.owner.pin()
 check(not editable.has("error") and cold.owner.is_pinned() and roomy.owned_bytes()+roomy.retained_bytes<=roomy.owner_limit,"released unrelated authority permits exact hydration within the hard bound")
 check(editable.image.get_data()==pixels and image.get_data()==pixels,"successful admission preserves exact independent source pixels")
 check(Cache.new(0,-1).owner_limit==0 and Cache.new(0,9999999999).owner_limit==Cache.DEFAULT_OWNER_LIMIT,"configuration cannot raise hard owner limit beyond320MiB")
 var full:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);full.fill(Color(.3,.5,.7,.5));var large:=Cache.new(0);var owners: Array=[];var rejected:=0
 for i in range(48):
  var result:=Owner.from_image(full.duplicate(),large)
  if result.has("error"):rejected+=1
  else:owners.append(result.owner)
 check(owners.size()==40 and rejected==8 and large.owned_bytes()==40*1920*1080*4 and large.owned_bytes()<=large.owner_limit,"default hard owner limit bounds48attempted full-HD retained authorities without raising the live cel cap")
 var path:=folder.path_join("source.png");full.save_png(path);var original:=FileAccess.get_sha256(path);var context:=Reader.new();context.cold_cels=true;context.adaptive_cache=Cache.new(0,0)
 var project:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[preload("res://src/timeline.gd").key(0,Vector3.ZERO,Quaternion.IDENTITY,60)],"world":preload("res://src/world_document.gd").empty(),"layers":[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"cel","start":0,"duration":48,"path":"source.png","pixel_sha256":Reader.digest_bytes(full.get_data())}]}],"audio":{},"editor":{"frame":0}}
 var decoded:=Storage.decode_project(project,folder,false,context)
 check(decoded.has("error") and context.adaptive_cache.live_owners().is_empty() and FileAccess.get_sha256(path)==original,"over-budget staged project decode returns an error without publishing partial owners or rewriting its source")
 print("RASTER_ADMISSION_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"default_owner_limit":Cache.DEFAULT_OWNER_LIMIT,"full_hd_accepted":owners.size(),"full_hd_rejected":rejected,"scope":"conservative owned+decoded bytes, not processRSS/GPU/tiles/temporary materializations"}));quit(0 if failures==0 else 1)
